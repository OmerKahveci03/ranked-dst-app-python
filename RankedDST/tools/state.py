"""
RankedDST/state.py

The source of truth for the project's state.
"""
import webview

from RankedDST.tools.logger import logger
from RankedDST.ui.updates import update_match_state, update_connection_state, update_user_data

DEVELOPING = True

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

valid_connection_states = [ConnectionNotConnected, ConnectionServerDown, ConnectionConnecting, ConnectionConnected]
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


# -------------------- DEDICATED SERVER TOOLS STATE -------------------- #
DediPathNotFound = "no_path"     # The base path does not exist, or it does not contain the "bin64/dontstarve_dedicated_server_nullrenderer_x64.exe" or the "mods/dedicated_server_mods_setup.lua"
DediToolsNotUpdated = "not_updated" # Path exists but the steam tools has an update available
DediPathFound = "path_found"  # Path exists and the tool is up to date

valid_dedi_path_states = [ DediPathNotFound, DediToolsNotUpdated, DediPathFound]
dedi_path_state = DediPathFound

def get_dedi_path_state() -> str:
    """
    Returns the app's dedi_path state.
    """
    return dedi_path_state

def set_dedi_path_state(new_state: str) -> None:
    """
    Mutates the global dedi_path variable
    """
    if new_state not in valid_dedi_path_states:
        raise ValueError(f"Dedicated server tools path state invalid. Recieved: {dedi_path_state}\n\tMust be in {valid_dedi_path_states}")
    global dedi_path
    dedi_path = new_state

# -------------------- USER DATA -------------------- #
global_user_data = {
    "user_id" : None,
    "username" : None,
    "match_id" : None,
    "klei_secret" : None,
}
valid_user_data_keys = ['user_id', 'username', 'match_id', 'klei_secret']

def get_user_data(get_key: str | None = None) -> dict[str, str | None] | str | None:
    """
    Returns a dictionary containing the user's data. If get_key is provided, then only the value stored
    for that key is returned.

    Valid keys are `'user_id', 'username', 'match_id', 'klei_secret'`
    """
    if not get_key:
        return global_user_data

    return global_user_data.get(get_key, None)

def set_user_data(new_values: dict[str, str | None], window: webview.Window | None = None, overwrite: bool = False) -> None:
    """
    Set the user data to be equal to the new values. If overwrite is false, then only modify the
    keys provided.

    Valid keys are `'user_id', 'username', 'match_id', 'klei_secret'`

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
