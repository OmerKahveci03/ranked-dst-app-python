"""
RankedDST/ui/actions.py

This module contains the UIActions class; an instance of which is passed into the window object.

The methods of this class are called by the javascript functions under resources/ui_actions.js
"""
import webbrowser

from RankedDST.dedicated_server.world_launcher import debug_start, stop_dedicated_server

from RankedDST.tools.logger import logger
import RankedDST.tools.state as state
from RankedDST.tools.config import save_data

class UIActions:
    """
    A class to bridge the gap between the javascript of the ui and the python app
    """

    def __init__(self, socket_connect_func: callable, socket_disconnect_func: callable):
        self._connect_socket = socket_connect_func
        self._disconnect_socket = socket_disconnect_func

    def save_klei_secret(self, new_secret: str) -> None:
        """
        Triggered when the `klei-secret-button` is clicked on the UI.
        """
        state.set_user_data({"klei_secret" : new_secret})
        secret_key = "klei_secret_dev" if state.DEVELOPING else "klei_secret"
        save_data({secret_key: new_secret})

        self._connect_socket()

    def start_server_button(self) -> None:
        debug_start()

    def stop_server_button(self) -> None:
        stop_dedicated_server()

    def logout_button(self) -> None:
        """
        Triggered when the `logout-button` is clicked on the UI's header.

        Disconnects the websocket connection and changes state to not connected.
        """
        stop_dedicated_server()
        self._disconnect_socket()

    def open_website(self, page: str = "") -> None:
        """
        Opens the website for the given page.

        Valid pages are `'stats', 'leaderboard', 'queue', 'history', 'profile', and ''`
        """
        assert page in ["", "stats", "leaderboard", "queue", "history", "profile"], f"Invalid page: {page}"
        
        url = f"{state.site_url()}/{page}"
        
        webbrowser.open(url, new=2)
