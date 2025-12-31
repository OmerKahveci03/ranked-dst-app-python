"""
RankedDST/networking/socket.py

This module establishes a webscocket connection using flask's socketio

The connection is to either http://localhost:5000/proxy or https://dontgetlosttogether.com/proxy
"""

import webview
import socketio
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
    Attempts to establish a socketio websocket connection. The user_data's klei secret
    is obtained, hashed, then used for authentication.

    Returns
    -------
    client_socket: socketio.Client
        The global socketio client object.
    """
    logger.info("Connecting websocket...")
    auth_fail: bool = False

    global client_socket
    window_object = get_window()
    if not isinstance(window_object, webview.Window):
        return client_socket
    
    if isinstance(client_socket, socketio.Client) and client_socket.connected:
        logger.info(" Socket is already connected")
        return client_socket

    if state.get_connection_state() == state.ConnectionNoPath:
        logger.info(" Can't connect websocket without dedicated server tools")
        return client_socket

    state.set_connection_state(state.ConnectionConnecting, window_object)

    raw_secret = state.get_user_data("klei_secret")
    if not raw_secret or raw_secret == "":
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        state.set_match_state(state.MatchNone, window_object)
        stop_dedicated_server()
        logger.info("🕹️ No Klei secret stored — skipping connection.")
        return client_socket

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
        """

        logger.info("On connect proxy")
        nonlocal auth_fail
        if auth_fail:
            logger.info("⚠️ Auth Failed so Disconnecting ⚠️")
            return
        logger.info("✅ Socket.IO connected to /proxy")
        state.set_connection_state(state.ConnectionConnected, window_object)

        match_id = state.get_user_data("match_id")
        if not match_id:
            logger.info("Not in a match")
            state.set_match_state(state.MatchNone, window_object)
            return
        
        logger.info("In a match! Requesting world files!")
        client_socket.emit(
            "request_world_files",
            {
                "match_id": match_id,
                "klei_secret_hash": hashed,
            },
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
        state.set_user_data(new_values={"user_id" : None, "username" : None, "match_id" : None, "klei_secret" : None})
        state.set_connection_state(new_state=state.ConnectionNotConnected, window=window_object)
        state.set_match_state(new_state=state.MatchNone, window=window_object)

    @client_socket.on("connect_error", namespace="/proxy")
    def on_connect_error(data):
        """
        Built in socketio event. Raises an error when something goes wrong on the transport level.

        Sets the connection state to `state.ConnectionServerDown`.
        """

        logger.info(f"❌ Connect error: {type(data)} - {data}")
        state.set_connection_state(new_state=state.ConnectionServerDown, window=window_object)

    @client_socket.on("connection_accepted", namespace="/proxy")
    def on_connection_accepted(data):
        """
        Defined by us. Emitted by the backend if the hashed klei secret is approved on connection.

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

        state.set_user_data(
            new_values={"user_id" : user_id, "username" : username, "match_id" : match_id},
            window=window_object
        )

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
            new_values={"klei_secret": ""}, 
            window=window_object,
        )
        show_popup(window=window_object, popup_msg="Invalid Klei Secret")
        # Our saved secret doesn't work, so we will delete it
        secret_key = "klei_secret_dev" if state.DEVELOPING else "klei_secret"
        save_data({secret_key : ""})
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        client_socket.disconnect()


    @client_socket.on("generate_world", namespace="/proxy")
    def on_generate_world(data):
        logger.info("🎉 Received generate_world from backend")
        
        try:
            start_dedicated_server(server_configs=data, window=window_object, client_socket=client_socket)
        except Exception as e:
            logger.info(f"❌ Failed to launch dedicated server: {e}")

    @client_socket.on("run_complete", namespace="/proxy")
    def on_run_complete(_):
        logger.info("Player's run is complete! Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchCompleted, window_object)

    @client_socket.on("match_complete", namespace="/proxy")
    def on_match_complete(_):
        logger.info("Match complete. Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchNone, window_object)

    try:
        logger.info("🔌 Connecting Socket.IO client 🔌")
        client_socket.connect(
            state.socket_url(),
            namespaces=["/proxy"],
            auth={"klei_secret_hash": hashed},
            transports=["websocket"],
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
