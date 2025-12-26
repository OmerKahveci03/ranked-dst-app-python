import webview
import os
import sys

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
    webview.create_window(
        title=title,
        url=resource("RankedDST/ui/resources/window.html"),
        resizable=False,
        height=620,
        width=420,
        # frameless=True,
    )
    webview.start()