"""
RankedDST/tools/path_checker.py

This module is tasked with ensuring that prerequisite file paths exist. Otherwise, no socket connection should take place
"""

import os

# Using tkinter only for opening file explorer
import tkinter as tk
from tkinter import filedialog

from RankedDST.tools.logger import logger

def required_files_exist(dedi_path: str, mute_logs: bool = False) -> bool:
    """
    The dedicated server path must contain the following files:

    mods/dedicated_server_mods_setup.lua
    bin64/dontstarve_dedicated_server_nullrenderer_x64.exe

    Parameters
    ----------
    dedi_path: str
        The full file path to the steam dedicated server tools folder. Usually found
        under `steam/steamapps/common`.
    mute_logs: bool (default False)
        An optional config to mute logs. Used during polling
    
    Returns
    -------
    files_exist: bool
        Is false if either the `mods_setup` or `nullrenderer` files are missing where they are expected.
    """

    mods_setup_fp = os.path.join(dedi_path, "mods", "dedicated_server_mods_setup.lua")
    nullrender_fp = os.path.join(dedi_path, "bin64", "dontstarve_dedicated_server_nullrenderer_x64.exe")

    for fp in [mods_setup_fp, nullrender_fp]:
        if not os.path.exists(fp):
            if not mute_logs:
                logger.info(f"Missing '{os.path.basename(fp)}' under '{dedi_path}'")
            return False
        if not mute_logs:
            logger.info(f"Found '{os.path.basename(fp)}' under '{dedi_path}'")
    return True

def try_find_dedi_path(candidate_path: str | None = None, mute_logs: bool = False) -> str | None:
    """
    Attempts to find the dedicated server path by checking common locations

    Parameters
    ----------
    candidate_path: str (default None)
        An optional path to be added as a candidate
    mute_logs: bool (default False)
        An optional config to mute logs. Used during polling

    Returns
    -------
    found_path: str | None
        Returns the path if found. Otherwise just returns None
    """

    candidates = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Don't Starve Together Dedicated Server",
        r"C:\Program Files\Steam\steamapps\common\Don't Starve Together Dedicated Server",
    ]
    # candidates = [] # for testing

    if isinstance(candidate_path, str):
        candidates.append(candidate_path)

    for path in candidates:
        if required_files_exist(path, mute_logs=mute_logs):
            return path

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
