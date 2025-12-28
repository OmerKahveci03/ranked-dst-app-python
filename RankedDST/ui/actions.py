"""
RankedDST/ui/actions.py

This module contains the UIActions class; an instance of which is passed into the window object.

The methods of this class are called by the javascript functions under resources/ui_actions.js
"""

import RankedDST.ui.handlers as handlers

from RankedDST.dedicated_server.world_launcher import debug_start, stop_dedicated_server

from RankedDST.tools.state import get_user_data, set_user_data, DEVELOPING
from RankedDST.tools.config import save_data

class UIActions:
    """
    A class to bridge the gap between the javascript of the ui and the python app
    """

    def test_button(self) -> None:
        handlers.test_button()

    def save_klei_secret(self, new_secret: str) -> None:
        """
        Triggered when the `klei-secret-button` is clicked on the UI.
        """
        set_user_data({"klei_secret" : new_secret})
        secret_key = "klei_secret_dev" if DEVELOPING else "klei_secret"
        save_data({secret_key: new_secret})

        # connect_websocket()

    def start_server_button(self) -> None:
        debug_start()

    def stop_server_button(self) -> None:
        stop_dedicated_server()
