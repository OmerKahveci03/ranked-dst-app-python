"""
RankedDST/ui/actions.py

This module contains the UIActions class; an instance of which is passed into the window object.

The methods of this class are called by the javascript functions under resources/ui_actions.js
"""
import webbrowser

import requests
from RankedDST.dedicated_server.world_launcher import stop_dedicated_server

from RankedDST.tools.secret import hash_string
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


    def login_clicked(self, username: str, password: str) -> None:
        """
        Triggered when the `login-button` is clicked on the UI.
        """
        logger.debug("Login button clicked")
        hashed_password = hash_string(password)

        try:
            response = requests.post(
                url=f"{state.route_url()}/login",
                json={
                    "username" : username, 
                    "hashed_password" : hashed_password,
                    "proxy": True
                }
            )
        except Exception as e:
            show_popup(window=self._window_getter(), popup_msg=f"Error logging in: {e}", button_msg="Dang")
            return

        data: dict = response.json()
        if not data.get("success", False):
            message = data.get("message", None)
            if not message:
                show_popup(window=self._window_getter(), popup_msg="Critical Error", button_msg="That's not good...")
                return
            
            show_popup(window=self._window_getter(), popup_msg=message, button_msg="Okay")
            return
        

        proxy_secret = data.get('auth_token')
        state.set_user_data({"proxy_secret" : proxy_secret})
        secret_key = state.get_secret_key()
        save_data({secret_key: proxy_secret})

        self._connect_socket()

    def stop_server_button(self) -> None:
        stop_dedicated_server()

    def logout_button(self) -> None:
        """
        Triggered when the `logout-button` is clicked on the UI's header.

        Disconnects the websocket connection and changes state to not connected.
        """
        window = self._window_getter()
        state.set_connection_state(new_state=state.ConnectionNotConnected, window=window)
        state.set_match_state(new_state=state.MatchNone, window=window)
        state.set_user_data(new_values={'proxy_secret' : ""})

        secret_key = state.get_secret_key()
        save_data(save_values={secret_key: ""})
        
        stop_dedicated_server()
        self._disconnect_socket()

    def open_website(self, page: str = "") -> None:
        """
        Opens the website for the given page.

        Valid pages are `'stats', 'leaderboard', 'queue', 'history', 'profile', 'setup' and ''`
        """
        assert page in ["", "stats", "leaderboard", "queue", "history", "profile", "setup?tab=no-dedi", "setup?tab=no-cluster"], f"Invalid page: {page}"
        
        url = f"{state.site_url()}/{page}"
        
        webbrowser.open(url, new=2)

    def open_file_explorer_ui(self, dedi_path: bool) -> None:
        """
        Opens the file explorer and checks if the provided path contains necessary files. If it does,
        then the path is saved, stored in memory, and connect_socket is run.

        If dedi_path is true, then the dedicated server tools are being searched for. Otherwise the
        cluster folder is searched for.
        """

        path = open_file_explorer()

        if not path:
            logger.info("No path provided")
            show_popup(window=self._window_getter(), popup_msg="No Path Provided")
            return
        
        files_exist = required_files_exist(search_path=path, dedi_path=dedi_path)
        if not files_exist:
            logger.info(f"Incorrect path. Files do not exist at '{path}'")
            show_popup(window=self._window_getter(), popup_msg="Incorrect Path")
            return
        
        write_key = 'dedi_path' if dedi_path else 'cluster_path'
        
        logger.info("User provided the correct path!")
        save_data({write_key : path})
        state.set_user_data(new_values={write_key : path})
        state.set_connection_state(state.ConnectionConnecting)

        # if dedi_path:
        #     self._connect_socket()

    def submit_path(self, path: str, dedi_path: bool) -> None:
        if not isinstance(path, str):
            logger.info("User did not provide a string")
            show_popup(window=self._window_getter(), popup_msg="Invalid Input")
            return
        
        files_exist = required_files_exist(search_path=path, dedi_path=dedi_path)
        if not files_exist:
            logger.info(f"Incorrect path. Files do not exist at '{path}'")
            show_popup(window=self._window_getter(), popup_msg="Incorrect Path")
            return
        
        logger.info("User provided the correct path!")
        write_key = 'dedi_path' if dedi_path else 'cluster_path'
        save_data({write_key : path})
        state.set_user_data(new_values={write_key : path})
        state.set_connection_state(state.ConnectionConnecting)

        # if dedi_path:
        #     self._connect_socket()
