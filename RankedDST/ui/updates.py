"""
RankedDST/ui/updates.py

This module contains all functions that invoke javascript functions to update the UI
"""

import webview
import json
from RankedDST.tools.logger import logger

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
    """
    Evaluates the `setUserData` function for the UI.

    Parameters
    ----------
    username: str
        The username of the user to display
    window: webview.Window | None
        The webview window object containing the javascript code to be invoked.
    """
        
    if window and isinstance(window, webview.Window):
        window.evaluate_js(f"setUserData({json.dumps(username)})")

def show_popup(window: webview.Window | None, popup_msg: str, button_msg: str = "Okay") -> None:
    """
    Reveal a popup on the UI by running the `showPopup` javascript function.

    Fills in the popup and button text with the provided message.

    Parameters
    ----------
    window: webview.Window | None
        The webview window object containing the javascript code to be invoked.
    popup_msg: str
        The text content of the main message of the popup.
    button_msg: str (default "Okay")
        The text content of the button that closes the popup.
    """
    
    if window and isinstance(window, webview.Window):
        window.evaluate_js(f"showPopup({json.dumps(popup_msg)}, {json.dumps(button_msg)})")
