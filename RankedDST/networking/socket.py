"""
RankedDST/networking/socket.py

This module establishes a webscocket connection using flask's socketio

The connection is to either http://localhost:5000/proxy or https://dontgetlosttogether.com/proxy
"""

import webview
import socketio
from threading import Event

import RankedDST.tools.state as state

from RankedDST.tools.secret import hash_string
from RankedDST.tools.config import save_data
from RankedDST.tools.logger import logger
from RankedDST.ui.updates import show_popup

from RankedDST.dedicated_server.world_launcher import start_dedicated_server, stop_dedicated_server

from RankedDST.ui.window import get_window

# Global socket client
client_socket: socketio.Client | None = None


def connect_websocket() -> socketio.Client | None:
    """
    Attempts to establish a socketio websocket connection. The user_data's proxy secret
    is obtained, hashed, then used for authentication.

    Returns
    -------
    client_socket: socketio.Client
        The global socketio client object.
    """
    logger.info("Connecting websocket...")
    auth_fail: bool = False

    auth_ready = Event()

    global client_socket
    window_object = get_window()
    if not isinstance(window_object, webview.Window):
        return client_socket
    
    if isinstance(client_socket, socketio.Client) and client_socket.connected:
        logger.info(" Socket is already connected")
        return client_socket
    
    state.ensure_prerequisites(window=window_object)

    raw_secret = state.get_user_data("proxy_secret")
    if not raw_secret or raw_secret == "":
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        state.set_match_state(state.MatchNone, window_object)
        stop_dedicated_server()
        logger.info("🕹️ No Proxy secret stored — skipping connection.")
        return client_socket
    
    state.set_connection_state(state.ConnectionConnecting, window_object)

    hashed = hash_string(raw_secret)

    client_socket = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,  # infinite
        reconnection_delay=2,
        logger=False,
        engineio_logger=False,
    )

    @client_socket.on("connect", namespace="/proxy")
    def connect_proxy():
        """
        Built in socketio event. Triggers after the initial connection succeeds, which means that
        connection_accepted has already triggered. Therefore the in-memory user_data state is now
        populated.

        If match_id is not none in state.user_data, then the `request_world_files` event is emitted.

        Emits an 'app_version' event to the backend as well.
        """
        auth_ready.wait(timeout=2)
        logger.info("On connect proxy")
        print(f"Connect proxy starting with match state {state.get_match_state()}")
        nonlocal auth_fail
        if auth_fail:
            logger.info("⚠️ Auth Failed so Disconnecting ⚠️")
            return
        logger.info("✅ Socket.IO connected to /proxy")
        state.set_connection_state(state.ConnectionConnected, window_object)

        client_socket.emit(
            "app_version",
            {"version" : state.VERSION},
            namespace="/proxy"
        )

        match_id = state.get_user_data("match_id")
        if not match_id:
            logger.info("Not in a match")
            state.set_match_state(state.MatchNone, window_object)
            return
        
        current_match_state = state.get_match_state()
        if current_match_state != state.MatchCompleted:
            logger.info(f"In a match with state {current_match_state}! Requesting world files!")
            client_socket.emit(
                "request_world_files", 
                {"match_id": match_id, "proxy_secret_hash": hashed}, 
                namespace="/proxy"
            )

    @client_socket.on("disconnect", namespace="/proxy")
    def on_proxy_disconnect():
        """
        Built in socketio event. Called when the `disconnect()` method for the socketio Client object
        is invoked. No error is raised.

        Will reset all user/connection/match state to the default.
        """

        logger.info(f"🛜 Proxy disconnect 🛜")
        state.set_user_data(new_values={"user_id" : None, "username" : None, "match_id" : None})
        state.set_connection_state(new_state=state.ConnectionNotConnected, window=window_object)
        state.set_match_state(new_state=state.MatchNone, window=window_object)

    @client_socket.on("connect_error", namespace="/proxy")
    def on_connect_error(data):
        """
        Built in socketio event. Raises an error when something goes wrong on the transport level.

        Sets the connection state to `state.ConnectionServerDown`.
        """

        logger.error(f"❌ Connect error: {type(data)} - {data} - {state.socket_url()}")
        state.set_connection_state(new_state=state.ConnectionServerDown, window=window_object)

    @client_socket.on("connection_accepted", namespace="/proxy")
    def on_connection_accepted(data):
        """
        Defined by us. Emitted by the backend if the hashed proxy secret is approved on connection.

        Provides user data.

        Payload
        -------
        user_id: str
            The user id of the user.
        username: str
            The username for the user. Will be displayed on the UI
        match_id : int | None
            The match id of the live match the user is in. If the user in not in a live match, then None
            is provided.
        """

        logger.info("On connection accepted")
        logger.info("✅ Auth successful")

        user_id = data.get("user_id")
        username = data.get("username")
        match_id = data.get("match_id", None)
        match_status = data.get("match_status", None)

        print(f"Connection accepted returned: {data}")

        state.set_user_data(
            new_values={"user_id" : user_id, "username" : username, "match_id" : match_id},
            window=window_object
        )
        if match_status == "completed":
            state.set_match_state(state.MatchCompleted, window=window_object)

        print(f"Connection accepted ending with match state {state.get_match_state()}")
        auth_ready.set()

    # Auth rejection
    @client_socket.on("connection_denied", namespace="/proxy")
    def on_connection_denied(_):
        """
        Defined by us. Emitted by the backend during initial connection if the provided hashed secret did
        not exist in the database. Raises an error?
        """

        logger.info("On connection denied")
        nonlocal auth_fail
        auth_fail = True
        logger.info("❌ Auth failed. Resetting secret + state.")
        state.set_user_data(
            new_values={"proxy_secret": ""}, 
            window=window_object,
        )
        show_popup(window=window_object, popup_msg="Invalid Proxy Secret")
        # Our saved secret doesn't work, so we will delete it
        secret_key = state.get_secret_key()
        save_data({secret_key : ""})
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        client_socket.disconnect()


    @client_socket.on("generate_world", namespace="/proxy")
    def on_generate_world(data):
        logger.info("🎉 Received generate_world from backend")
        
        try:
            start_dedicated_server(server_configs=data, window=window_object, client_socket=client_socket)
        except Exception as e:
            show_popup(window=window_object, popup_msg=f"Failed to launch dedicated server: {e}", button_msg="Oh no...")
            logger.info(f"❌ Failed to launch dedicated server: {e}")

    @client_socket.on("run_complete", namespace="/proxy")
    def on_run_complete(_):
        logger.info("Player's run is complete! Shutting down server")
        stop_dedicated_server()

        if state.get_match_state() != state.MatchNone:
            state.set_match_state(state.MatchCompleted, window_object)

    @client_socket.on("match_complete", namespace="/proxy")
    def on_match_complete(_):
        logger.info("Match complete. Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchNone, window_object)
    
    @client_socket.on("show_popup", namespace="/proxy")
    def on_show_popup(data):
        show_message = data.get('message', None)
        button_message = data.get('button_message', None)

        if show_message is None or not isinstance(show_message, str):
            logger.warning(f"Show popup was given with an incorrect show_message; {type(show_message)}\n\tdata: {type(data)}")
            return
        
        if isinstance(button_message, str):
            show_popup(window=window_object, popup_msg=show_message, button_msg=button_message)
        else:
            show_popup(window=window_object, popup_msg=show_message)

    try:
        logger.info("🔌 Connecting Socket.IO client 🔌")
        client_socket.connect(
            state.socket_url(),
            namespaces=["/proxy"],
            auth={"proxy_secret_hash": hashed},
            #transports=["websocket"],
            retry=True
        )
    except Exception as e:
        # Exceptions are raised for issues at the transport level
        logger.info(f"❌ Socket connect failed: {type(e)} - {e}")
    return client_socket

def disconnect_websocket() -> socketio.Client | None:
    """
    Shuts down the websocket connection in the global client_socket object.

    Returns
    -------
    client_socket: socketio.Client | None
        The client socketio object
    """
    global client_socket

    if not isinstance(client_socket, socketio.Client):
        logger.warning(f"Cannot disconnect an object of type '{type(client_socket)}'")
    if client_socket.connected:
        logger.info("Disconnecting socket connection")
        client_socket.disconnect()
    else:
        logger.warning("Can't disconnect a connection that doesn't exist")

    return client_socket
