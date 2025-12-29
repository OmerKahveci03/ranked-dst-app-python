"""
RankedDST/ui/updates.py

This module contains all functions that invoke javascript functions to update the UI
"""

import webview
import json

def update_match_state(new_state: str, window: webview.Window | None) -> None:
    """
    Evaluates the `matchStateChanged` function for the UI.

    Parameters
    ----------
    new_state: str
        The state that was changed
    window: webview.Window | None
        The webview window object containing the javascript code to be invoked.
    """

    if window and isinstance(window, webview.Window):
        window.evaluate_js(f"matchStateChanged({json.dumps(new_state)})")

def update_connection_state(new_state: str, window: webview.Window | None) -> None:
    """
    Evaluates the `connectionStateChanged` function for the UI.

    Parameters
    ----------
    new_state: str
        The state that was changed
    window: webview.Window | None
        The webview window object containing the javascript code to be invoked.
    """

    if window and isinstance(window, webview.Window):
        window.evaluate_js(f"connectionStateChanged({json.dumps(new_state)})")

def update_user_data(username: str, window: webview.Window | None) -> None:
    if window and isinstance(window, webview.Window):
        window.evaluate_js(f"setUserData({json.dumps(username)})")