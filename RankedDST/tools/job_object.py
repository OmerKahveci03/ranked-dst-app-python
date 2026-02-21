import sys
import os
import signal
import subprocess
import atexit

_job = None
_children: list[subprocess.Popen] = []

# -------------------------------------------------------
# WINDOWS IMPLEMENTATION
# -------------------------------------------------------
if sys.platform == "win32":
    import win32job
    import win32api
    import win32con

    def create_kill_on_close_job():
        """
        Creates a Windows Job Object that kills all assigned
        processes if this parent process exits.
        """
        global _job
        if _job is not None:
            return _job

        job = win32job.CreateJobObject(None, "")
        info = win32job.QueryInformationJobObject(
            job,
            win32job.JobObjectExtendedLimitInformation
        )

        info["BasicLimitInformation"]["LimitFlags"] |= (
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )

        win32job.SetInformationJobObject(
            job,
            win32job.JobObjectExtendedLimitInformation,
            info
        )

        _job = job
        return job

    def assign_process(proc: subprocess.Popen) -> None:
        """
        Assigns subprocess to the Windows job object.
        """
        if proc is None or _job is None:
            return

        handle = win32api.OpenProcess(
            win32con.PROCESS_ALL_ACCESS,
            False,
            proc.pid
        )

        win32job.AssignProcessToJobObject(_job, handle)


# -------------------------------------------------------
# UNIX IMPLEMENTATION (macOS + Linux)
# -------------------------------------------------------
else:

    def create_kill_on_close_job():
        """
        No-op on Unix.
        We use process groups + atexit cleanup instead.
        """
        return None

    def assign_process(proc: subprocess.Popen) -> None:
        """
        Register subprocess for cleanup on exit.
        Assumes it was started with os.setsid.
        """
        if proc is None:
            return

        _children.append(proc)

    def _cleanup():
        """
        Kill all registered child process groups on parent exit.
        """
        for proc in _children:
            try:
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                pass

    atexit.register(_cleanup)
