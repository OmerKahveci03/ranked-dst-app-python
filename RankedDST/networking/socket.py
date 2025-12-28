"""
RankedDST/networking/socket.py

This module establishes a webscocket connection using flask's socketio

The connection is to either http://localhost:5000/proxy or https://dontgetlosttogether.com/proxy
"""

import webview
import socketio
import time
import RankedDST.tools.state as state

from RankedDST.tools.secret import hash_string
from RankedDST.tools.config import save_data
from RankedDST.tools.logger import logger

from RankedDST.dedicated_server.world_launcher import start_dedicated_server, stop_dedicated_server

from RankedDST.ui.window import get_window

# Global socket client
client_socket: socketio.Client | None = None


def _backend_url() -> str:
    if state.DEVELOPING:
        return "http://localhost:5000"
    return "https://dontgetlosttogether.com"


def connect_websocket() -> socketio.Client | None:
    """
    Attempts to establish a socketio websocket connection. The user_data's klei secret
    is obtained, hashed, then used for authentication.
    """
    logger.info("Connecting websocket...")
    reached_backend = False

    global client_socket
    window_object = get_window()
    if not isinstance(window_object, webview.Window):
        return client_socket
    
    if isinstance(client_socket, socketio.Client) and client_socket.connected:
        logger.info(" Socket is already connected")
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

    logger.info("🔌 Connecting Socket.IO client...")

    client_socket = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,  # infinite
        reconnection_delay=2,
        logger=False,
        engineio_logger=False,
    )

    @client_socket.on("connect", namespace="/proxy")
    def connect_proxy():
        nonlocal reached_backend
        reached_backend = True
        logger.info("✅ Socket.IO connected to /proxy")
        state.set_connection_state(state.ConnectionConnected, window_object)

        match_id = state.get_user_data("match_id")
        if not match_id:
            print("Not in a match")
            state.set_match_state(state.MatchNone, window_object)
            return
        
        print("In a match! Requesting world files!")
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
        if not reached_backend:
            logger.info("❌ Never reached backend — server likely down")
            state.set_connection_state(state.ConnectionServerDown, window_object)
        else:
            logger.info("⚠️ Disconnected from server")
            state.set_connection_state(state.ConnectionNotConnected, window_object)
        state.set_match_state(state.MatchNone, window_object)

    @client_socket.on("connect_error", namespace="/proxy")
    def on_connect_error(data):
        nonlocal reached_backend
        reached_backend = True
        logger.info(f"❌ Connect error (server reachable): {data}")
        state.set_connection_state(state.ConnectionNotConnected, window_object)

    @client_socket.on("connection_accepted", namespace="/proxy")
    def on_connection_accepted(data):
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
        logger.info("❌ Auth failed. Resetting secret + state.")
        state.set_user_data(
            new_values={"klei_secret": ""}, 
            window=window_object,
            overwrite=True
        )
        secret_key = "klei_secret_dev" if state.DEVELOPING else "klei_secret"
        #save_data({secret_key : ""})
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        client_socket.disconnect()


    @client_socket.on("generate_world", namespace="/proxy")
    def on_generate_world(data):
        logger.info("🎉 Received generate_world from backend")
        state.set_match_state(new_state=state.MatchWorldGenerating, window=window_object)
        
        try:
            start_dedicated_server(server_configs=data)
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
        client_socket.connect(
            _backend_url(),
            namespaces=["/proxy"],
            auth={"klei_secret_hash": hashed},
            transports=["websocket"],
        )
        logger.info("Socket connection!")
    except Exception as e:
        logger.info(f"❌ Socket connect failed: {e}")
        # state.set_connection_state(state.ConnectionServerDown, window_object)
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

def start_socket_loop() -> None:
    """
    Creates a permanent blocking loop that tries to establish a websocket connection
    if a klei secret is provided and the connection does not already exist.

    Shouldn't be run on the main thread
    """
    last_secret = None

    while True:
        logger.debug("Start Socket Loop")
        time.sleep(0.5)

        if isinstance(client_socket, socketio.Client) and client_socket.connected:
            logger.debug(" Socket is already connected...")
            time.sleep(30)
            continue

        secret = state.get_user_data("klei_secret")
        connection_state = state.get_connection_state()

        if not secret or secret == last_secret:
            logger.debug(f"This klei secret won't work: {secret}")
            time.sleep(1)
            continue
        
        logger.debug(f"Secret okay. Continuing with connection state: {connection_state}")
        last_secret = secret

        if connection_state == state.ConnectionServerDown:
            logger.debug("Server is down. Will wait five seconds")
            time.sleep(5)

        connect_websocket()

