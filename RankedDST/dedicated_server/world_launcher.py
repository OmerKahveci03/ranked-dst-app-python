"""
This is a standalone module built to allow easy dedicated server testing. 

Production is implemented in the GoLang app.
"""

import os
import re
import subprocess
import time
import threading
import webview
import socketio

import RankedDST.tools.state as state
from RankedDST.tools.secret import hash_string
from RankedDST.tools.job_object import assign_process

from pathlib import Path
from RankedDST.tools.logger import logger, server_logger
from RankedDST.dedicated_server.server_manager import SERVER_MANAGER
from RankedDST.dedicated_server.world_cleanup import clean_old_files

CREATE_NO_WINDOW = 0x08000000


def create_cluster(
    cluster_dir: str,
    server_configs: dict[str, str],
) -> None:
    """
    Writes the cluster files to disk if not already present

    Parameters
    ----------
    cluster_dir: str
        The full file path to the cluster file
    server_configs: dict[str, str]
        A dictionary containing all files to be written. The key is the file type and the value is the
        entire contents of the file.

        Expected keys: 
        ```
        "ClusterIni", "MasterServerIni", "CavesServerIni",  # .ini files
        "MasterWorldGenOverride", "CavesWorldGenOverride", "ModOverrides" # .lua files
        ```
    """
    if os.path.exists(cluster_dir):
        logger.info("Cluster directory already exists!")
        return

    logger.info(f"Creating cluster directory at: '{cluster_dir}'")
    os.makedirs(cluster_dir, exist_ok=True)
    os.makedirs(os.path.join(cluster_dir, "Master"), exist_ok=True)
    os.makedirs(os.path.join(cluster_dir, "Caves"), exist_ok=True)

    required_keys = ["ClusterIni", "MasterServerIni", "CavesServerIni", "MasterWorldGenOverride", "CavesWorldGenOverride", "ModOverrides"]
    if any(required_key not in server_configs.keys() for required_key in required_keys):
        logger.error("Missing required file")
        raise ValueError("Missing required file")
    
    # Location at cluster_dir
    key_to_path = {
        "ClusterIni": "cluster.ini",
        "MasterServerIni" : os.path.join("Master", "server.ini"),
        "CavesServerIni" : os.path.join("Caves", "server.ini"),
        "MasterWorldGenOverride" : os.path.join("Master", "worldgenoverride.lua"),
        "CavesWorldGenOverride" : os.path.join("Caves", "worldgenoverride.lua"),
    }

    for key, path in key_to_path.items():
        write_fp = os.path.join(cluster_dir, path)
        write_text = server_configs.get(key)
        with open(write_fp, mode="w", encoding="utf-8") as file:
            file.write(write_text)

    for shard in ["Master", "Caves"]:
        write_fp = os.path.join(cluster_dir, shard, "modoverrides.lua")
        write_text = server_configs.get("ModOverrides")
        with open(write_fp, mode="w", encoding="utf-8") as file:
            file.write(write_text)

def ensure_mods(
    mod_ids: list[str],
    steam_mods_path: str,
) -> None:
    """
    Ensures that the `dedicated_server_mods_setup.lua` file at the **steam_mods_path** contains all the
    mod ids provided. If not, then they will be added to the file.

    Each mod id must have a corresponding `ServerModSetup("<id>")` line in the file.

    Parameters
    ----------
    mod_ids: list[str]
        A list of workshop ids for the mods that must exist at the `dedicated_server_mods_setup.lua` file.
    steam_mods_path: str
        The directory that must contain the `dedicated_server_mods_setup.lua` file.
    """

    mod_setup_file = Path(steam_mods_path) / "dedicated_server_mods_setup.lua"
    valid_id = re.compile(r"^[0-9]{6,12}$")

    cleaned_ids: list[str] = []
    for mod_id in mod_ids:
        mod_id = mod_id.strip()
        if not valid_id.match(mod_id):
            raise ValueError(
                f"Invalid workshop ID: {mod_id!r} (must be 6-12 digits)"
            )
        cleaned_ids.append(mod_id)

    existing = ""
    if mod_setup_file.exists():
        existing = mod_setup_file.read_text(encoding="utf-8")

    missing_lines: list[str] = []
    for mod_id in cleaned_ids:
        line = f'ServerModSetup("{mod_id}")'
        if line not in existing:
            missing_lines.append(line)
    
    if not missing_lines:
        logger.info(f" All {len(cleaned_ids)} mods already present in {mod_setup_file}")
        return

    mod_setup_file.parent.mkdir(parents=True, exist_ok=True)

    with mod_setup_file.open("a", encoding="utf-8") as f:
        for line in missing_lines:
            f.write(line + "\n")

    logger.info(f"🧩 Added {len(missing_lines)} new mod(s) to {mod_setup_file}")


def launch_shard(
    nullrender_fp: str,
    shard: str,
    cluster_name: str,
    window: webview.Window | None,
    client_socket: socketio.Client | None
) -> subprocess.Popen:
    """
    Uses the nullrenderer binary to launch a server; either the master or caves. The cluster_name folder
    is expected to exist and the shard must be either 'Master' or 'Caves'

    Parameters
    ----------
    nullrender_fp: str
        The full path to the executable that launches and hosts the DST world.
    shard: str
        Determines the type of server to be launched. Must be either `'Master' or 'Caves'`
    cluster_name: str
        The folder name containing valid world files, such as cluster.ini, server.ini... etc.
    window: webview.Window | None
        The webview window object. Needed to update the UI when world state changes.
    client_socket: socketio.Client | None
        The global socketio object. Needed to emit events to the server when certain events take place.
    """

    assert shard in ["Master", "Caves"], "Shard must be 'Master' or 'Caves'"
    logger.info(f" Launching {shard} Shard!")
    cmd = [
        nullrender_fp,
        "-cluster", cluster_name,
        "-shard", shard,
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(nullrender_fp),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=CREATE_NO_WINDOW,
    )
    assign_process(proc)
    SERVER_MANAGER.set_shard_status(shard=shard, status='launching')

    def stream_output():
        launched: bool = False
        for line in proc.stdout:
            server_logger.info("[%s] %s", shard, line.rstrip())

            if not launched and "Sim paused" in line:
                logger.info(f"The {shard} shard is launched!")
                SERVER_MANAGER.set_shard_status(shard=shard, status='launched')
                launched = True

                master_status, caves_status = SERVER_MANAGER.get_shard_status()
                if master_status == caves_status and master_status == 'launched':
                    logger.info("Both shards are launched!")
                    state.set_match_state(new_state=state.MatchWorldReady, window=window)
                    raw_secret = state.get_user_data("proxy_secret")
                    hashed = hash_string(raw_secret)

                    logger.info("Player has generated the world")
                    client_socket.emit(
                        "world_generated",
                        {"proxy_secret_hash": hashed},
                        namespace="/proxy"
                    )
            elif "Leave Announcement" in line:
                if isinstance(client_socket, socketio.Client) and client_socket.connected and shard == 'Master': # Master shard to avoid duplicate emissions
                    raw_secret = state.get_user_data("proxy_secret")
                    hashed = hash_string(raw_secret)

                    logger.info("Player has left the world")
                    client_socket.emit(
                        "world_left",
                        {"proxy_secret_hash": hashed},
                        namespace="/proxy"
                    )

    threading.Thread(target=stream_output, daemon=True).start()

    return proc


def start_dedicated_server(
    server_configs: dict[str, str],
    window: webview.Window | None = None,
    client_socket: socketio.Client | None = None,
) -> None:
    """
    Parameters
    ----------
    server_configs: dict[str, str]
        A dictionary containing all files to be written. The key is the file type and the value is the
        entire contents of the file. The 'MatchId' and 'ModIds' are also provided.

        Expected keys: 
        ```
        "MatchId", "ModIds"
        "ClusterIni", "MasterServerIni", "CavesServerIni",  # .ini files
        "MasterWorldGenOverride", "CavesWorldGenOverride", "ModOverrides", # .lua files
        ```
    window: webview.Window (default None)
        The webview window object. Needed to update the UI when world state changes.
    client_socket: socketio.Client (default None)
        The global socketio object. Needed to emit events to the server when certain events take place.
    """
    base_cluster_dir = Path.home() / "Documents" / "Klei" / "DoNotStarveTogether"

    dedi_path = state.get_user_data(get_key='dedi_path')
    logger.info(f"dedi path is: {dedi_path}")
    nullrender_fp = os.path.join(dedi_path, 'bin64', 'dontstarve_dedicated_server_nullrenderer_x64.exe')

    steam_mods_path = os.path.join(dedi_path, "mods")

    logger.debug(f"Starting Dedicated Server!\n\tdedi_path: {dedi_path}\n\tnullrender_fp: {nullrender_fp}")

    assert os.path.exists(nullrender_fp), "Nullrender binary must exist"
    assert os.path.exists(base_cluster_dir), f"Base cluster directory must exist at {base_cluster_dir}"

    if SERVER_MANAGER.is_running():
        logger.info("⚠️ Dedicated server already running ⚠️")
        return

    match_id = server_configs.pop("MatchId")
    mod_ids = server_configs.pop("ModIds")

    cluster_name = f"Ranked DST Match {match_id}"
    cluster_dir = os.path.join(base_cluster_dir, cluster_name)
    create_cluster(cluster_dir=cluster_dir, server_configs=server_configs)

    ensure_mods(mod_ids=mod_ids, steam_mods_path=steam_mods_path)

    raw_secret = state.get_user_data("proxy_secret")
    hashed = hash_string(raw_secret)

    logger.info("Generating World")
    client_socket.emit(
        "generating_world",
        {"proxy_secret_hash": hashed},
        namespace="/proxy"
    )

    state.set_match_state(new_state=state.MatchWorldGenerating, window=window)
    master_process = launch_shard(
        nullrender_fp=nullrender_fp,
        shard="Master",
        cluster_name=cluster_name,
        window=window,
        client_socket=client_socket
    )

    caves_process = launch_shard(
        nullrender_fp=nullrender_fp,
        shard="Caves",
        cluster_name=cluster_name,
        window=window,
        client_socket=client_socket
    )

    SERVER_MANAGER.set_subprocesses(master_process, caves_process)
    logger.info("Launched both master and caves!")

def stop_dedicated_server(timeout: float = 1.0) -> None:
    """
    Shuts down the dedicated server if up and updates match state.

    Parameters
    ----------
    timeout: flaot (default 1.0)
        The time in seconds to wait before force killing the processes.
    """
    if not SERVER_MANAGER.is_running():
        logger.info("Dedicated server was not running. Nothing to shutdown.")
        return
    
    logger.info("🛑 STOPPING DEDICATED SERVER 🛑")

    with SERVER_MANAGER.lock:
        processes = {
            "Master" : SERVER_MANAGER.master, 
            "Caves" : SERVER_MANAGER.caves
        }

    # Gracefully terminate
    for shard, proc in processes.items():
        if proc and proc.poll() is None:
            logger.info(f"Gracefully terminating {shard} process")
            proc.terminate()
    
    start = time.time()
    while time.time() - start < timeout:
        if all(proc.poll() is not None for proc in processes.values() if proc):
            break
        time.sleep(0.1)

    # Force kill if needed
    for shard, proc in processes.items():
        if proc and proc.poll() is None:
            logger.info(f"💀 Force killing {shard} shard 💀")
            proc.kill()

    SERVER_MANAGER.clear_subprocesses()
    logger.info("✅ Dedicated server stopped ✅")
