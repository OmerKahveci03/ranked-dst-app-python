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

        self.master_status = 'down'
        self.caves_status = 'down'
    
    def set_shard_status(self, shard: str, status: str):
        """
        Update the current status of the shard.
        
        shard: str
            The shard the status is updated for. Must be either `'Master' or 'Caves'`
        status: str
            The status to be updated. Must be either `'down', 'launching', or 'launched'`
        """
        assert shard in ['Master', 'Caves'], f"Shard must be either 'Caves' or 'Master'. Was given: {shard}"
        assert status in ['down', 'launching', 'launched'], f"Status must be either 'down', 'launching', or 'launched'. Was given: {status}"

        if shard == 'Master':
            self.master_status = status
        elif shard == 'Caves':
            self.caves_status = status

    def get_shard_status(self) -> tuple[str, str]:
        """
        Obtains the status of the master and caves shards.

        Status will only be one of: `'down', 'launching', or 'launched'`

        Returns
        -------
        master_status: str
            The status of the master shard.
        caves_status: str
            The status of the caves shard.
        """
        return self.master_status, self.caves_status

    def is_running(self) -> bool:
        return (
            self.master is not None
            and self.master.poll() is None
            and self.caves is not None
            and self.caves.poll() is None
        )

    def set_subprocesses(self, master: subprocess.Popen, caves: subprocess.Popen) -> None:
        """
        Stores the subprocesses for the master and caves shard
        """
        with self.lock:
            self.master = master
            self.caves = caves

    def clear_subprocesses(self) -> None:
        """
        Clears out the master and caves subprocesses and sets their statuses to 'down'
        """
        with self.lock:
            self.master = None
            self.caves = None
        
        self.set_shard_status(shard="Master", status="down")
        self.set_shard_status(shard="Caves", status="down")

SERVER_MANAGER = DedicatedServerManager()
