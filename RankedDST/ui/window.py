import webview
import os
import sys

from RankedDST.ui.actions import UIActions

window_object: webview.Window | None = None

def get_window() -> webview.Window:
    return window_object

def resource(path: str) -> str:
    """
    If bundled into an executable: appends the path to the
    system's MEIPASS location.

    Otherwise simply returns the path.
    """
    print(f"Resource got path: {path}")
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(path)

def create_window(title: str) -> None:
    """
    Creates and starts a **webview** window.
    """
    global window_object
    window_object = webview.create_window(
        title=title,
        url=resource("RankedDST/ui/resources/window.html"),
        resizable=False,
        height=620,
        width=420,
        js_api=UIActions(),
        # frameless=True,
    )
    webview.start()