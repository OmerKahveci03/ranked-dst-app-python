"""
RankedDST/state.py

The source of truth for the project's state.
"""
import webview
import json
import os
import sys
import time

from RankedDST.tools.logger import logger
from RankedDST.tools.config import get_config_path, save_data
from RankedDST.tools.path_checker import try_find_prerequisite_path, check_dst_versions

from RankedDST.ui.updates import update_match_state, update_connection_state, update_user_data, show_popup

# False - prod
# True - dev
# None - local
DEVELOPING = None

def set_developing(developing: bool | None):
    global DEVELOPING
    DEVELOPING = developing

def get_secret_key():
    if DEVELOPING is None:
        return "proxy_secret_local"
    elif DEVELOPING:
        return "proxy_secret_dev"
    else:
        return "proxy_secret"

VERSION = 1.34

# -------------------- NETWORKING STATE -------------------- #
def route_url() -> str:
    """
    Returns the base url the backend exposes for all http requests.

    Returns
    -------
    route_url: str 
        The URL exposed by the backend for http requests.
    """

    if DEVELOPING is None:
        return "http://localhost:5000"
    elif DEVELOPING:
        return "https://dontgetlosttogether.com/api"
    else:
        return "https://rankeddst.com/api"
    

def socket_url() -> str:
    """
    Returns the base url the backend exposes for the websocket connection

    Returns
    -------
    socket_url: str 
        The URL exposed by the backend for websocket connections.
    """

    if DEVELOPING is None:
        return "http://localhost:5000"
    elif DEVELOPING:
        return "https://dontgetlosttogether.com"
    else:
        return "https://rankeddst.com"

def site_url() -> str:
    """
    Returns the base url for the website

    Returns
    -------
    site_url: str 
        The URL exposed by the frontend
    """

    if DEVELOPING is None:
        return "http://localhost:5173"
    elif DEVELOPING:
        return "https://dontgetlosttogether.com"
    else:
        return "https://rankeddst.com"

# -------------------- MATCH STATE -------------------- #
MatchNone = "no_match" # You are not in a live match
MatchWorldGenerating = "world_generating"
MatchWorldReady = "world_ready"
MatchInProgress = "in_progress" # You are in the world while the match is live
MatchCompleted = "completed" # Your run is over but the match is still live so you are waiting for the others to finish

valid_match_states = [MatchNone, MatchWorldGenerating, MatchWorldReady, MatchInProgress, MatchCompleted]
match_state = None

def get_match_state() -> str:
    """
    Returns the match state.
    """
    return match_state

def set_match_state(new_state: str, window: webview.Window | None = None) -> None:
    """
    Mutates the global match_state variable.

    Parameters
    ----------
    new_state: str
        The state to change the global match_state variable to
    window: webview.Window (default None)
        The webview window object to evaluate the javascript function for
    """

    if new_state not in valid_match_states:
        raise ValueError(f"Match state invalid. Recieved: {new_state}\n\tMust be in {valid_match_states}")
    
    global match_state
    if match_state == new_state:
        return
    
    logger.info( f"Changing match state to {new_state}")
    update_match_state(new_state=new_state, window=window)
    match_state = new_state


# -------------------- CONNECTION STATE -------------------- #
ConnectionConnected = "connected"
ConnectionConnecting = "connecting"
ConnectionNotConnected = "not_connected"
ConnectionNeedUpdate = "need_update" # dst and mod tools are not same version
ConnectionServerDown = "no_server"
ConnectionNoPath = "no_path" # if prerequisite file paths do not exist we cannot continue
ConnectionNoCluster = "no_cluster" # no cluster path (klei dst path)

valid_connection_states = [
    ConnectionNoCluster, ConnectionNoPath, ConnectionNeedUpdate, 
    ConnectionNotConnected, ConnectionServerDown, 
    ConnectionConnecting, ConnectionConnected
]

# connection_state = ConnectionNotConnected
connection_state = None

def get_connection_state() -> str:
    """
    Returns the app's connection state.
    """
    return connection_state

def set_connection_state(new_state: str, window: webview.Window | None = None) -> None:
    """
    Mutates the global connection_state variable. Calls the `connectionStateChanged` javascript function
    for the window object with the new_state as the parameter.

    Parameters
    ----------
    new_state: str
        The state to change the global connection_state variable to
    window: webview.Window (default None)
        The webview window object to evaluate the javascript function for. Can be omitted, but
        shouldn't unless another javascript function is modifying the UI.
    """
    if new_state not in valid_connection_states:
        raise ValueError(f"Connection state invalid. Recieved: {new_state}\n\tMust be in {valid_connection_states}")
    
    global connection_state
    if connection_state == new_state:
        logger.info(f"Connection state was already {new_state}. No updates to ui.")
        return
    
    logger.info( f"Changing connection state to {new_state}")
    update_connection_state(new_state=new_state, window=window)
    connection_state = new_state


# -------------------- USER DATA -------------------- #
global_user_data = {
    "user_id" : None,
    "username" : None,
    "match_id" : None,
    "proxy_secret" : None,
    "dedi_path" : None,
    "cluster_path" : None
}
valid_user_data_keys = ['user_id', 'username', 'match_id', 'proxy_secret', 'dedi_path', 'cluster_path']

def get_user_data(get_key: str | None = None) -> dict[str, str | None] | str | None:
    """
    Returns a dictionary containing the user's data. If get_key is provided, then only the value stored
    for that key is returned.

    Valid keys are `'user_id', 'username', 'match_id', 'proxy_secret', 'dedi_path', 'cluster_path'`
    """
    if not get_key:
        return global_user_data

    return global_user_data.get(get_key, None)

def set_user_data(new_values: dict[str, str | None], window: webview.Window | None = None, overwrite: bool = False) -> None:
    """
    Set the user data to be equal to the new values. If overwrite is false, then only modify the
    keys provided.

    Valid keys are `'user_id', 'username', 'match_id', 'proxy_secret', 'dedi_path', 'cluster_path'`

    Parameters
    ----------
    new_values: dict[str, str | None]
        The values to update the global user_data object with.

        Example:
        ```
        {"user_id" : "1", "username" : "INeedANames"}
        ```
    window: webview.Window (default None)
        If provided, then the data may update the UI as well. Only username is supported in this case.
    overwrite: bool (default False)
        If set to true, then all values are reset before writing
    """
    if any(key not in valid_user_data_keys for key in new_values):
        raise ValueError("Invalid key provided")
    
    global global_user_data

    if overwrite:
        # reset everything first
        global_user_data = {key: None for key in valid_user_data_keys}

    for key, value in new_values.items():
        global_user_data[key] = value

    # Update UI if possible
    if not window:
        return

    username = new_values.get('username', None)
    update_user_data(username=username, window=window)


def wait_required_folder(check_interval: float = 2.0, dedi_path: bool = True) -> None:
    """
    Should be run when dedicated server tools or cluster folder are not found. Repeatedly checks if the given folder 
    exists/ is installed.
    
    Exits if the `connection_state` is not longer equal to the corresponding state or if the searched paths find the tools.
    
    Is blocking until the exit condition
    """
    blocking_connection_state = ConnectionNoPath if dedi_path else ConnectionNoCluster
    search_folder = "dedicated tools" if dedi_path else "cluster folder"
    
    logger.info(f"Waiting for {search_folder}...")
    start = time.time()
    while True:
        time.sleep(check_interval)
        
        if get_connection_state() != blocking_connection_state:
            logger.info(f"No longer waiting for {search_folder}")
            return
        
        found_path = try_find_prerequisite_path(mute_logs=True, dedi_path=dedi_path)
        if not found_path:
            continue

        elapsed = time.time() - start
        logger.info(f"{search_folder} found in {int(elapsed)} seconds! No longer waiting.")
        return

def wait_matching_versions(window: webview.Window, check_interval: float = 2.0) -> bool:
    """
    Should be run when dedicated server tools do not match the same version as dst. Repeatedly checks if the versions match.

    Exits if the version.txt for both dst and dedi tools match. Is blocking until then.

    If check_dst_versions, the function exits but the message will popup.

    Returns
    -------
    version_check_failed: bool
        Returns True if the app is unable to determine if versions are matching
    """
    if sys.platform == "darwin":
        return True

    logger.info(f"Waiting for dst and dedi tools to have matching versions...")
    start = time.time()
    while True:
        time.sleep(check_interval)
        dedi_path = get_user_data(get_key="dedi_path")
        
        try:
            versions_match = check_dst_versions(dedi_fp=dedi_path, raise_error=True)
        except Exception as e:
            # push to ui
            show_popup(window=window, popup_msg=str(e), button_msg="Dang it")
            logger.error(f"An error occurred when checking dst versions: {e}")
            return True

        if not versions_match:
            continue

        elapsed = time.time() - start
        logger.info(f"DST versions match after {int(elapsed)} seconds! No longer waiting.")
        return False
    
    return True

def load_initial_state() -> None:
    """
    Loads the ~/home/ranked_dst/config.json file and reads the data found.
    """
    logger.info("Loading initial state...")
    config_fp = get_config_path()
    if not os.path.exists(config_fp):
        with open(config_fp, "w", encoding="utf-8") as file:
            file.write("{}")

    # 1. load config json file
    with open(config_fp, "r+", encoding="utf-8") as file:
        try:
            config_data: dict[str, str] = json.load(file)
            logger.info(f"Read {config_data} into config data!")
        except Exception:
            logger.warning(f"Failed to read '{file}'. Replacing it with an empty json")
            file.write("{}")
            config_data: dict[str, str] = {}
    
    dev_secret = config_data.pop('proxy_secret_dev', None)
    local_secret = config_data.pop('proxy_secret_local', None)
    if DEVELOPING:
        config_data['proxy_secret'] = dev_secret
    elif DEVELOPING is None:
        config_data['proxy_secret'] = local_secret
    set_user_data(new_values=config_data)

update_warning_shown = False

def ensure_prerequisites(window: webview.Window) -> None:
    """
    Ensures that the following three prerequisites are in place:
    1. The cluster path in memory maps to the actual folder for cluster files to be created in
    2. The dedicated server tools and prerequisite files exist on the user's computer
    3. DST and dedicated server tools have the same version
    4. A proxy secret is stored in memory

    If step 1, 2, or 3 fails, then the function waits until the condition is satisfied. If step 4 fails, then
    nothing happens
    """
    current_user_data = get_user_data()

    # 1. Check for cluster path
    saved_cluster_path = current_user_data.get('cluster_path', None)
    valid_cluster_path = try_find_prerequisite_path(candidate_path=saved_cluster_path, dedi_path=False)
    if not valid_cluster_path:
        logger.info("The cluster path was not found. Will be required to proceed.")
        set_connection_state(new_state=ConnectionNoCluster, window=window)

        wait_required_folder(dedi_path=False)
    else:
        logger.info("(1/4) Cluster path exists!")
        if saved_cluster_path != valid_cluster_path:
            set_user_data({"cluster_path" : valid_cluster_path})
            save_data({'cluster_path': valid_cluster_path})

    # 2. Check for dedicated server tools
    saved_dedi_path = current_user_data.get('dedi_path', None)
    valid_path = try_find_prerequisite_path(candidate_path=saved_dedi_path, dedi_path=True)

    if not valid_path:
        logger.info("A path was not found. Will be required to proceed.")
        set_connection_state(new_state=ConnectionNoPath, window=window)

        wait_required_folder(dedi_path=True)
    else:
        logger.info("2/4) Dedicated server tools are ready to go!")
        set_user_data({"dedi_path" : valid_path})

        if saved_dedi_path != valid_path:
            set_user_data({"dedi_path" : valid_path})
            save_data({'dedi_path': valid_path})

    # 3. Check for dedi tools and dst versions to be matching
    version_check_failed = False
    if sys.platform != "darwin":
        versions_match = check_dst_versions(dedi_fp=valid_path, raise_error=False)
        if not versions_match:
            logger.info("(3/4) DST version does not match dedicated tools")
            set_connection_state(new_state=ConnectionNeedUpdate, window=window)

            version_check_failed = wait_matching_versions(window=window)

        else:
            logger.info("(3/4) Dedicated server tools match the DST version!")
    else:
        logger.info("(3/4) Skipping version check on MacOS")
        version_check_failed = True

    global update_warning_shown
    if version_check_failed and not update_warning_shown:
        show_popup(window=window, popup_msg="Unable to confirm the version of your dedicated server tools. Make sure they are up to date before playing!")
        update_warning_shown = True

    # 4. Check for proxy secret
    proxy_secret = current_user_data.get('proxy_secret', None)
    if proxy_secret:
        logger.info(f"(4/4) Proxy secret was stored as {proxy_secret}")
        set_user_data({"proxy_secret" : proxy_secret})
    else:
        logger.info("No proxy secret was stored.")
        set_match_state(MatchNone, window=window) # likely not needed either

    logger.info(f"User data state is now: {get_user_data()}")
