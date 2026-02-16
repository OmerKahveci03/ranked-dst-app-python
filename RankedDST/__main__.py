import threading
import sys
import os

from argparse import ArgumentParser
from RankedDST.ui.window import create_window, get_window

from RankedDST.networking.proxy import start_proxy_server
from RankedDST.networking.socket import connect_websocket, disconnect_websocket

from RankedDST.dedicated_server.world_cleanup import clean_old_files

from RankedDST.tools.state import load_initial_state, set_developing
from RankedDST.tools.logger import logger
from RankedDST.tools.job_object import create_kill_on_close_job


def init():
    """
    Obtains initial state and attempts the first socket connection once the webview window is created
    """
    while True:
        window = get_window()
        if window: 
            break
    
    load_initial_state()
    clean_old_files()
    connect_websocket()

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        exe_name = os.path.basename(sys.executable).lower()

        if "dev" in exe_name:
            mode = "dev"
        elif "local" in exe_name:
            mode = "local"
        else:
            mode = "prod"
    else:
        # Running normally
        parser = ArgumentParser()
        parser.add_argument("--dev", action="store_true")
        parser.add_argument("--prod", action="store_true")
        args = parser.parse_args()

        if args.prod:
            mode = "prod"
        elif args.dev:
            mode = "dev"
        else:
            mode = "local"

    # None is local
    if mode == "prod":
        set_developing(developing=False)
    elif mode == "dev":
        set_developing(developing=True)

    create_kill_on_close_job()
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
