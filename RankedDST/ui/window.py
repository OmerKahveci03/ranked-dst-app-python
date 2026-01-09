import webview
import os
import sys

from RankedDST.tools.logger import logger
from RankedDST.ui.actions import UIActions

window_object: webview.Window | None = None

def get_window() -> webview.Window | None:
    return window_object

def resource(path: str) -> str:
    """
    If bundled into an executable: appends the path to the
    system's MEIPASS location.

    Otherwise simply returns the path.
    """
    logger.info(f"Resource got path: {path}")
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(path)

def create_window(title: str, socket_connect_func: callable, socket_disconnect_func: callable) -> None:
    """
    Creates and starts a **webview** window.

    Parameters
    ----------
    title: str
        The name of the window created
    socket_connect_func: callable
        A function that attempts to establish a socketio connection when run. Has no parameters
        in the function signature. Required to avoid circular imports.
    """
    global window_object
    window_object = webview.create_window(
        title=title,
        url=resource("RankedDST/ui/resources/window.html"),
        resizable=False,
        height=620,
        width=420,
        js_api=UIActions(
            window_getter=get_window,
            socket_connect_func=socket_connect_func, 
            socket_disconnect_func=socket_disconnect_func
        ),
        # frameless=True,
    )
    webview.start() # to do: make this its own function lol
    