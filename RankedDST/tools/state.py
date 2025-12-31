"""
RankedDST/state.py

The source of truth for the project's state.
"""
import webview
import json
import os

from RankedDST.tools.logger import logger
from RankedDST.tools.config import get_config_path, save_data
from RankedDST.tools.path_checker import try_find_dedi_path

from RankedDST.ui.updates import update_match_state, update_connection_state, update_user_data

DEVELOPING = False

# -------------------- NETWORKING STATE -------------------- #
def route_url() -> str:
    """
    Returns the base url the backend exposes for all http requests.

    Returns
    -------
    route_url: str 
        The URL exposed by the backend for http requests.
    """

    if DEVELOPING:
        return "http://localhost:5000"
    return "https://dontgetlosttogether.com/api"

def socket_url() -> str:
    """
    Returns the base url the backend exposes for the websocket connection

    Returns
    -------
    socket_url: str 
        The URL exposed by the backend for websocket connections.
    """

    if DEVELOPING:
        return "http://localhost:5000"
    return "https://dontgetlosttogether.com"

def site_url() -> str:
    """
    Returns the base url for the website

    Returns
    -------
    site_url: str 
        The URL exposed by the frontend
    """

    if DEVELOPING:
        return "http://localhost:5173"
    return "https://dontgetlosttogether.com"

# -------------------- MATCH STATE -------------------- #
MatchNone = "no_match" # You are not in a live match
MatchWorldGenerating = "world_generating"
MatchWorldReady = "world_ready"
MatchInProgress = "in_progress" # You are in the world while the match is live
MatchCompleted = "completed" # Your run is over but the match is still live so you are waiting for the others to finish

valid_match_states = [MatchNone, MatchWorldGenerating, MatchWorldReady, MatchInProgress, MatchCompleted]
match_state = MatchNone

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
ConnectionServerDown = "no_server"
ConnectionNoPath = "no_path" # if prerequisite file paths do not exist we cannot continue

valid_connection_states = [ConnectionNoPath, ConnectionNotConnected, ConnectionServerDown, ConnectionConnecting, ConnectionConnected]
connection_state = ConnectionNotConnected

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
        return
    
    logger.info( f"Changing connection state to {new_state}")
    update_connection_state(new_state=new_state, window=window)
    connection_state = new_state


# -------------------- USER DATA -------------------- #
global_user_data = {
    "user_id" : None,
    "username" : None,
    "match_id" : None,
    "klei_secret" : None,
    "dedi_path" : None,
}
valid_user_data_keys = ['user_id', 'username', 'match_id', 'klei_secret', 'dedi_path']

def get_user_data(get_key: str | None = None) -> dict[str, str | None] | str | None:
    """
    Returns a dictionary containing the user's data. If get_key is provided, then only the value stored
    for that key is returned.

    Valid keys are `'user_id', 'username', 'match_id', 'klei_secret', 'dedi_path'`
    """
    if not get_key:
        return global_user_data

    return global_user_data.get(get_key, None)

def set_user_data(new_values: dict[str, str | None], window: webview.Window | None = None, overwrite: bool = False) -> None:
    """
    Set the user data to be equal to the new values. If overwrite is false, then only modify the
    keys provided.

    Valid keys are `'user_id', 'username', 'match_id', 'klei_secret', 'dedi_path'`

    Parameters
    ----------
    new_values: dict[str, str | None]
        The values to update the global user_data object with.

        Example:
        ```
        {"user_id" : "1", "username" : "INeedANames"}
        ```
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


def load_initial_state(window: webview.Window) -> None:
    """
    Loads the ~/home/.ranked_dst/config.json file and reads the data found.
    """

    logger.info("Loading initial state...")
    config_fp = get_config_path()
    if not os.path.exists(config_fp):
        with open(config_fp, "w", encoding="utf-8") as file:
            file.write("{}")

    with open(config_fp, "r+", encoding="utf-8") as file:
        try:
            config_data: dict[str, str] = json.load(file)
            logger.info(f"Read {config_data} into config data!")
        except Exception:
            logger.warning(f"Failed to read '{file}'. Replacing it with an empty json")
            file.write("{}")
            config_data: dict[str, str] = {}

    secret_key = "klei_secret_dev" if DEVELOPING else "klei_secret"

    klei_secret = config_data.get(secret_key, None)
    if klei_secret:
        logger.info(f"Klei secret was stored as {klei_secret}")
        set_user_data({"klei_secret" : klei_secret})
    else:
        logger.info("No klei secret was stored.")
    
    saved_dedi_path = config_data.get('dedi_path', None)
    valid_path = try_find_dedi_path(candidate_path=saved_dedi_path)

    if not valid_path:
        logger.info("A path was not found. Will be required to proceed.")
        set_connection_state(new_state=ConnectionNoPath, window=window)
    else:
        logger.info("Dedicated server tools are ready to go!")
        set_user_data({"dedi_path" : valid_path})

        set_connection_state(ConnectionNotConnected, window=window)  # might want to remove this actually

        if saved_dedi_path != valid_path:
            save_data({'dedi_path': valid_path})

    logger.info(f"User data state is now: {get_user_data()}")
    set_match_state(MatchNone, window=window) # likely not needed either
