"""
RankedDST/ui/actions.py

This module contains the UIActions class; an instance of which is passed into the window object.

The methods of this class are called by the javascript functions under resources/ui_actions.js
"""
import webbrowser
from RankedDST.dedicated_server.world_launcher import stop_dedicated_server

from RankedDST.tools.logger import logger
import RankedDST.tools.state as state
from RankedDST.tools.config import save_data
from RankedDST.tools.path_checker import required_files_exist, open_file_explorer
from RankedDST.ui.updates import show_popup

class UIActions:
    """
    A class to bridge the gap between the javascript of the ui and the python app
    """

    def __init__(self, window_getter: callable, socket_connect_func: callable, socket_disconnect_func: callable):
        self._window_getter = window_getter
        self._connect_socket = socket_connect_func
        self._disconnect_socket = socket_disconnect_func


    def save_proxy_secret(self, new_secret: str) -> None:
        """
        Triggered when the `proxy-secret-button` is clicked on the UI.
        """
        state.set_user_data({"proxy_secret" : new_secret})
        secret_key = "proxy_secret_dev" if state.DEVELOPING else "proxy_secret"
        save_data({secret_key: new_secret})

        self._connect_socket()

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

    def open_file_explorer_ui(self) -> None:
        """
        Opens the file explorer and checks if the provided path contains necessary files. If it does,
        then the path is saved, stored in memory, and connect_socket is run.
        """

        path = open_file_explorer()

        if not path:
            logger.info("No path provided")
            return
        
        files_exist = required_files_exist(dedi_path=path)
        if not files_exist:
            logger.info(f"Incorrect path. Files do not exist at '{path}'")
            return
        
        logger.info("User provided the correct path!")
        save_data({'dedi_path' : path})
        state.set_user_data(new_values={'dedi_path' : path})
        state.set_connection_state(state.ConnectionConnecting)

        self._connect_socket()

    def submit_dedi_path(self, path: str) -> None:
        if not isinstance(path, str):
            logger.info("User did not provide a string")
            show_popup(window=self._window_getter(), popup_msg="Invalid Input")
            return
        
        files_exist = required_files_exist(dedi_path=path)
        if not files_exist:
            logger.info(f"Incorrect path. Files do not exist at '{path}'")
            show_popup(window=self._window_getter(), popup_msg="Incorrect Path")
            return
        
        logger.info("User provided the correct path!")
        save_data({'dedi_path' : path})
        state.set_user_data(new_values={'dedi_path' : path})
        state.set_connection_state(state.ConnectionConnecting)

        self._connect_socket() # to do: deal with duplicated code
