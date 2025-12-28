"""
RankedDST/dedicated_server/manager.py

This module creates the DedicatedServerManager class which is used for controlling the dedicated server created by the app.

The object contains a master and caves subprocess that can be set/cleared
"""
import subprocess
import threading
from typing import Optional

class DedicatedServerManager:
    def __init__(self):
        self.master: Optional[subprocess.Popen] = None
        self.caves: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()

    def is_running(self) -> bool:
        return (
            self.master is not None
            and self.master.poll() is None
            and self.caves is not None
            and self.caves.poll() is None
        )

    def set(self, master: subprocess.Popen, caves: subprocess.Popen):
        with self.lock:
            self.master = master
            self.caves = caves

    def clear(self):
        with self.lock:
            self.master = None
            self.caves = None

SERVER_MANAGER = DedicatedServerManager()
