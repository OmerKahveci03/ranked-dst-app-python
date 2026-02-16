"""
RankedDST/tools/path_checker.py

This module is tasked with ensuring that prerequisite file paths exist. Otherwise, no socket connection should take place
"""

from pathlib import Path

# Using tkinter only for opening file explorer
import tkinter as tk
from tkinter import filedialog

from RankedDST.tools.logger import logger

def required_files_exist(search_path: str | Path, mute_logs: bool = False, dedi_path: bool = True) -> bool:
    """
    The dedicated server path must contain the following files:

    `mods/dedicated_server_mods_setup.lua`,
    `bin64/dontstarve_dedicated_server_nullrenderer_x64.exe`

    The cluster directory should contain at least the following:

    `client_log.txt`,
    `master_server_log.txt`

    Parameters
    ----------
    search_path: str | Path
        The full file path to the file being searched for. If looking for the steam dedicated server tools 
        folder, then usually found under `steam/steamapps/common`. Otherwise we are looking for the cluster foldrer
    mute_logs: bool (default False)
        An optional config to mute logs. Used during polling
    dedi_path: bool (default True)
        An optional config. If true, then the searched path is for the dedicated server tools. Otherwise it is
        for the base cluster directory under `klei/DoNotStarveTogether`
    
    Returns
    -------
    files_exist: bool
        Is false if either the `mods_setup` or `nullrenderer` files are missing where they are expected.
    """
    search_path = Path(search_path)
    
    if dedi_path:
        mods_setup_fp = Path(search_path) / "mods" / "dedicated_server_mods_setup.lua"
        nullrender_fp = Path(search_path) / "bin64" / "dontstarve_dedicated_server_nullrenderer_x64.exe"
        search_files = [mods_setup_fp, nullrender_fp]

        expected_folder_name = "Don't Starve Together Dedicated Server"
    else:
        client_log_fp = Path(search_path) / "client_log.txt"
        master_log_fp = Path(search_path) / "master_server_log.txt"
        search_files = [client_log_fp, master_log_fp]

        expected_folder_name = "DoNotStarveTogether"

    if search_path.name != expected_folder_name:
        logger.info(f"Expected the folder name to be {expected_folder_name}, not {search_path.name}")
        return False
    for fp in search_files:
        if not fp.exists():
            if not mute_logs:
                logger.info(f"Missing '{fp.name}' under '{search_path}'")
            return False
        if not mute_logs:
            logger.info(f"Found '{fp.name}' under '{search_path}'")
    return True

def try_find_prerequisite_path(candidate_path: str | None = None, mute_logs: bool = False, dedi_path: bool = True) -> str | None:
    """
    Attempts to find the prerequisite path by checking common locations. An additional candidate path
    can be provided as well. Supports searching for dedicated server tools and the base cluster directory.

    Parameters
    ----------
    candidate_path: str (default None)
        An optional path to be added as a candidate
    mute_logs: bool (default False)
        An optional config to mute logs. Used during polling
    dedi_path: bool (default True)
        An optional config. If true, then the searched path is for the dedicated server tools. Otherwise it is
        for the base cluster directory under `klei/DoNotStarveTogether`

    Returns
    -------
    found_path: str | None
        Returns the path if found. Otherwise just returns None
    """

    if dedi_path:
        candidates = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Don't Starve Together Dedicated Server",
            r"C:\Program Files\Steam\steamapps\common\Don't Starve Together Dedicated Server",
        ]
    else:
        candidates = [
            Path.home() / "Documents" / "Klei" / "DoNotStarveTogether",
            Path.home() / "OneDrive" / "Documents" / "Klei" / "DoNotStarveTogether",
        ]
    #candidates = [] # for testing

    if isinstance(candidate_path, str):
        candidates.append(Path(candidate_path))

    for path in candidates:
        if required_files_exist(search_path=path, mute_logs=mute_logs, dedi_path=dedi_path):
            return str(path)

    if not mute_logs:
        logger.info("Could not auto-detect DST Dedicated Server path")
    return None

def open_file_explorer() -> str:
    """
    Open file explorer using an API and allow the user to find the path themselves. Returns
    the path selected.

    Returns
    -------
    path: str | None
        The path the user selected in the file explorer
    """
    logger.info("Opening file explorer...")
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.askdirectory(
        title="Select Don't Starve Together Dedicated Server Folder"
    )

    root.destroy()

    if path:
        logger.info(f"User selected DST path: {path}")
        return path

    logger.info("User cancelled DST path selection")
    return None

def check_dst_versions(dedi_fp: str, raise_error: bool = False) -> bool:
    """
    Checks if the dedicated server tools match the same version as the dst game. Returns true if they match. False
    otherwise.

    Raises an error if the files are not found.

    Parameters
    ----------
    dedi_fp: str
        The valid full file path to the directory containing the dedicated server tools. Should contain the version.txt file,
        and a level below there should be a 'Don't Stave Together' folder that also contains version.txt.
    raise_error: bool (default False)
        If true, errors will be raised.

    Returns
    -------
    versions_match: bool
        Whether the two versions match. If either file is not found then an exception is raised.
    """

    # return False

    expected_dedi_tool_basename = "Don't Starve Together Dedicated Server"
    expected_dst_basename = "Don't Starve Together"

    dedi_path = Path(dedi_fp)
    if dedi_path.name != expected_dedi_tool_basename:
        err_msg = f"Dedicated server tools path has an unexpected name: {dedi_path.name}"
        logger.error(err_msg)
        if raise_error:
            raise ValueError()
        return False

    steamapps_path = dedi_path.parent
    dst_path = steamapps_path / expected_dst_basename

    if not dst_path.exists():
        err_msg = "Don't Starve Together not found. Is it installed on your computer?"
        logger.error(err_msg)
        if raise_error:
            raise ValueError(err_msg)
        return False
    if not dst_path.is_dir():
        err_msg = "DST path should be a directory, not a file"
        logger.error(err_msg)
        if raise_error:
            raise ValueError(err_msg)
        return False
    
    versions: list[int] = []
    for path in [dst_path, dedi_path]:
        version_file_path = path / "version.txt"

        if not version_file_path.exists() or not version_file_path.is_file():
            err_msg = f"Version file not found for {path.name}"
            logger.error(err_msg)
            if raise_error:
                raise ValueError()
            return False
        
        # read it and append to versions
        version = version_file_path.read_text().strip()
        versions.append(version)

    return versions[0] == versions[1]
    

    
