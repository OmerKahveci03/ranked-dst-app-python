# RankedDST/tools/job_object.py
import win32job
import win32api
import win32con
import subprocess

_job = None

def create_kill_on_close_job():
    """
    Initializes the global _job object. Must be called before `assign_process`.
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
    Assigns the subprocess to the windows job object; causing it to be killed
    if the parent dies.
    """
    if proc is None:
        return
    handle = win32api.OpenProcess(
        win32con.PROCESS_ALL_ACCESS,
        False,
        proc.pid
    )
    win32job.AssignProcessToJobObject(_job, handle)
