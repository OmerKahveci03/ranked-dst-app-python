"""
This is a standalone module built to allow easy dedicated server testing. 

Production is implemented in the GoLang app.
"""

import os
import subprocess
import shutil
import threading

def launch_shard(
    nullrender_fp: str,
    shard: str,
    cluster_name: str
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
    """
    assert shard in ["Master", "Caves"], "Shard must be 'Master' or 'Caves'"
    print(f" Launching {shard} Shard!")
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
    )

    def stream_output():
        for line in proc.stdout:
            print(f"[{shard}] {line}", end="")

    threading.Thread(target=stream_output, daemon=True).start()

    return proc

def start_dedicated_server(
    static_dir: str,
    cluster_dir: str,
    nullrender_fp: str,
) -> None:
    """
    Copies the cluster.ini, server.ini, worldgenoverride.lua, and modoverrides.lua
    files into the cluster dir. Then launches the master and caves shards using the
    nullrender executable

    Parameters
    ----------
    static_dir: str
        The static folder containing the world files to be copied into the cluster directory
    cluster_dir: str
        The cluster folder to be created. Used to generate the world.
    nullrender_fp: str
        The full path to the executable that launches and hosts the DST world.
    """
    
    assert os.path.exists(nullrender_fp), "Nullrender binary must exist"
    
    os.makedirs(cluster_dir, exist_ok=True)

    cluster_ini_src = os.path.join(static_dir, "cluster.ini")
    assert os.path.exists(cluster_ini_src), "Missing cluster.ini"
    shutil.copy2(cluster_ini_src, os.path.join(cluster_dir, "cluster.ini"))

    for shard in ["Master", "Caves"]:

        shard_cluster = os.path.join(cluster_dir, shard)
        os.makedirs(shard_cluster, exist_ok=True)

        for file_name in "server.ini", "worldgenoverride.lua", "modoverrides.lua":
            static_fp = os.path.join(static_dir, shard, file_name)
            assert os.path.exists(static_fp), f"Missing static file: {static_fp}"

            write_fp = os.path.join(shard_cluster, file_name)
            shutil.copy2(static_fp, write_fp)
    
    print(f"Created cluster directory at:\n\t'{cluster_dir}'!")
    cluster_name = os.path.basename(cluster_dir)

    master_process = launch_shard(
        nullrender_fp=nullrender_fp,
        shard="Master",
        cluster_name=cluster_name
    )

    caves_process = launch_shard(
        nullrender_fp=nullrender_fp,
        shard="Caves",
        cluster_name=cluster_name
    )

    print("Launched both master and caves!")

    try:
        # Block until either process exits
        master_process.wait()
        caves_process.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        master_process.terminate()
        caves_process.terminate()

def stop_dedicated_server():
    pass
