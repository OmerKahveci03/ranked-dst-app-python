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


def connect_websocket() -> None:
    """
    Attempts to establish a socketio websocket connection. The user_data's klei secret
    is obtained, hashed, then used for authentication.
    """
    logger.info("Connecting websocket...")

    global client_socket
    window_object = get_window()
    if not isinstance(window_object, webview.Window):
        return

    state.set_connection_state(state.ConnectionConnecting, window_object)

    raw_secret = state.get_user_data("klei_secret")
    if not raw_secret:
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        state.set_match_state(state.MatchNone)
        stop_dedicated_server()
        logger.info("🕹️ No Klei secret stored — skipping connection.")
        return

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
        logger.info("✅ Socket.IO connected to /proxy")
        state.set_connection_state(state.ConnectionConnected, window_object)

    @client_socket.on("disconnect", namespace="/proxy")
    def on_proxy_disconnect():
        logger.info("⚠️ Lost connection to server")
        state.set_connection_state(state.ConnectionServerDown, window_object)
        state.set_match_state(state.MatchNone)

    @client_socket.on("connection_accepted", namespace="/proxy")
    def on_connection_accepted(data):
        logger.info("✅ Auth successful")

        user_id = data.get("user_id")
        username = data.get("username")
        match_id = data.get("match_id", None)

        state.set_user_data({"user_id" : user_id, "username" : username, "match_id" : match_id})

        if match_id is not None:
            client_socket.emit(
                "request_world_files",
                {
                    "match_id": match_id,
                    "klei_secret_hash": hashed,
                },
                namespace="/proxy",
            )
        else:
            state.set_match_state(state.MatchNone)

    @client_socket.on("connection_denied", namespace="/proxy")
    def on_connection_denied(_):
        logger.info("❌ Auth failed. Resetting secret + state.")
        state.set_user_data({"klei_secret": ""}, overwrite=True)
        # save_data({"klei_secret" : ""})
        state.set_connection_state(state.ConnectionNotConnected, window_object)
        client_socket.disconnect()

    @client_socket.on("generate_world", namespace="/proxy")
    def on_generate_world(data):
        logger.info("🎉 Received generate_world from backend")

        try:
            start_dedicated_server(data)
        except Exception as e:
            logger.info(f"❌ Failed to launch dedicated server: {e}")

    @client_socket.on("run_complete", namespace="/proxy")
    def on_run_complete(_):
        logger.info("Player's run is complete! Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchCompleted)

    @client_socket.on("match_complete", namespace="/proxy")
    def on_match_complete(_):
        logger.info("Match complete. Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchNone)

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
        state.set_connection_state(state.ConnectionServerDown, window_object)

def start_socket_loop() -> None:
    """
    Creates a permanent blocking loop that tries to establish a websocket connection
    if a klei secret is provided and the connection does not already exist.

    Shouldn't be run on the main thread
    """
    last_secret = None

    while True:
        logger.info("Start Socket Loop")
        time.sleep(0.5)

        if isinstance(client_socket, socketio.Client) and client_socket.connected:
            logger.info(" Socket is already connected...")
            time.sleep(30)
            continue

        secret = state.get_user_data("klei_secret")
        connection_state = state.get_connection_state()

        if connection_state == state.ConnectionServerDown:
            logger.info("Server is down. Trying again in five seconds")
            time.sleep(5)

        if secret and secret != last_secret:
            logger.info(f"Secret okay. Continuing with connection state: {connection_state}")
            connect_websocket()

            last_secret = secret
