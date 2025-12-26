"""
RankedDST/networking/socket.py

This module establishes a webscocket connection using flask's socketio

The connection is to either http://localhost:5000/proxy or https://dontgetlosttogether.com/proxy
"""


import socketio
import RankedDST.state as state
from RankedDST.dedicated_server.world_launcher import start_dedicated_server, stop_dedicated_server

# Global socket client
client_socket: socketio.Client | None = None


def _backend_url() -> str:
    if state.Developing:
        return "http://localhost:5000"
    return "https://dontgetlosttogether.com"


def connect_websocket():
    print("Connecting websocket...")

    global client_socket

    state.set_connection_state(state.ConnectionConnecting)

    raw_secret = state.GetKleiSecret()
    if not raw_secret:
        state.set_connection_state(state.ConnectionNotConnected)
        state.set_match_state(state.MatchNone)
        stop_dedicated_server()
        print("🕹️ No Klei secret stored — skipping connection.")
        return

    hashed = state.HashString(raw_secret)

    print("🔌 Connecting Socket.IO client...")

    client_socket = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,  # infinite
        reconnection_delay=2,
        logger=False,
        engineio_logger=False,
    )

    @client_socket.event
    def connect():
        print("✅ Socket.IO connected")
        state.set_connection_state(state.ConnectionConnected)

    @client_socket.event
    def disconnect():
        print("❌ Socket.IO disconnected")
        state.set_connection_state(state.ConnectionNotConnected)

    @client_socket.event
    def connect_error(data):
        print("❌ Connection error:", data)
        state.set_connection_state(state.ConnectionServerDown)


    @client_socket.on("connection_accepted", namespace="/proxy")
    def on_connection_accepted(data):
        print("✅ Auth successful")

        user_id = data.get("user_id")
        username = data.get("username")
        match_id = data.get("match_id")

        state.SetUserData(user_id, username)

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
        print("❌ Auth failed. Resetting secret + state.")
        state.SetKleiSecret("")
        state.set_connection_state(state.ConnectionNotConnected)
        client_socket.disconnect()

    @client_socket.on("generate_world", namespace="/proxy")
    def on_generate_world(data):
        print("🎉 Received generate_world from backend")

        try:
            start_dedicated_server(data)
        except Exception as e:
            print("❌ Failed to launch dedicated server:", e)

    @client_socket.on("run_complete", namespace="/proxy")
    def on_run_complete(_):
        print("Player's run is complete! Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchCompleted)

    @client_socket.on("match_complete", namespace="/proxy")
    def on_match_complete(_):
        print("Match complete. Shutting down server")
        stop_dedicated_server()
        state.set_match_state(state.MatchNone)

    try:
        client_socket.connect(
            _backend_url(),
            namespaces=["/proxy"],
            auth={"klei_secret_hash": hashed},
            transports=["websocket"],
        )
    except Exception as e:
        print("❌ Socket connect failed:", e)
        state.set_connection_state(state.ConnectionServerDown)
        return
