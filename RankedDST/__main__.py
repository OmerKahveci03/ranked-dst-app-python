import threading

from RankedDST.ui.window import create_window, get_window

from RankedDST.networking.proxy import start_proxy_server
from RankedDST.networking.socket import start_socket_loop, connect_websocket, disconnect_websocket

from RankedDST.tools.config import load_initial_state
from RankedDST.tools.logger import logger

def init():
    """
    Obtains initial state and attempts the first socket connection once the webview window is created
    """
    while True:
        window = get_window()
        if window: 
            break
    
    load_initial_state(window=window)
    connect_websocket()

if __name__ == "__main__":
    # First: determine initial state
    #   Either we have a secret or we don't
    #   Then either we have dedicated server tools installed or we don't
    # load_initial_state()
    
    proxy_thread = threading.Thread(
        target=start_proxy_server,
        kwargs={
            "host": "127.0.0.1",
            "port": 3035,
        },
        daemon=True,
    )
    proxy_thread.start()

    init_thread = threading.Thread(
        target=init,
        daemon=True
    )
    init_thread.start()

    logger.info("Creating User Interface")
    create_window(
        title="Ranked DST", 
        socket_connect_func=connect_websocket, 
        socket_disconnect_func=disconnect_websocket
    )
