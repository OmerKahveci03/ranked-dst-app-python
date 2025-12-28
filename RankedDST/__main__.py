import threading

from RankedDST.ui.window import create_window

from RankedDST.networking.proxy import start_proxy_server
from RankedDST.networking.socket import start_socket_loop

from RankedDST.tools.config import load_initial_state
from RankedDST.tools.logger import logger

if __name__ == "__main__":
    cluster_dir = r"C:\Users\ofsys\Documents\Klei\DoNotStarveTogether\TestWorld"
    nullrender_fp = r"C:\Program Files (x86)\Steam\steamapps\common\Don't Starve Together Dedicated Server\bin64\dontstarve_dedicated_server_nullrenderer_x64.exe"
    static_dir = r"C:\Users\ofsys\Documents\Code\FullStack\ranked-dst\backend\static"

    # First: determine initial state
    #   Either we have a secret or we don't
    #   Then either we have dedicated server tools installed or we don't
    load_initial_state()
    
    proxy_thread = threading.Thread(
        target=start_proxy_server,
        kwargs={
            "host": "127.0.0.1",
            "port": 3035,
        },
        daemon=True,
    )
    proxy_thread.start()

    websocket_thread = threading.Thread(
        target=start_socket_loop,
        daemon=True
    )
    websocket_thread.start()

    logger.info("Creating User Interface")
    create_window(title="Ranked DST")
