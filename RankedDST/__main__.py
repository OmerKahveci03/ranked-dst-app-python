import threading

from RankedDST.dedicated_server.world_launcher import start_dedicated_server
from RankedDST.ui.window import create_window

from RankedDST.networking.proxy import start_proxy_server
from RankedDST.networking.socket import connect_websocket

if __name__ == "__main__":
    cluster_dir = r"C:\Users\ofsys\Documents\Klei\DoNotStarveTogether\TestWorld"
    nullrender_fp = r"C:\Program Files (x86)\Steam\steamapps\common\Don't Starve Together Dedicated Server\bin64\dontstarve_dedicated_server_nullrenderer_x64.exe"
    static_dir = r"C:\Users\ofsys\Documents\Code\FullStack\ranked-dst\backend\static"

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
        target=connect_websocket,
        daemon=True
    )
    websocket_thread.start()

    print("Creating User Interface")
    create_window(title="Ranked DST")

    print("Starting Dedicated Server")
    start_dedicated_server(
        static_dir=static_dir,
        cluster_dir=cluster_dir,
        nullrender_fp=nullrender_fp,
    )
