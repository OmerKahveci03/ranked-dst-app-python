"""
RankedDST/state.py

The source of truth for the project's state
"""

Developing = True

MatchNone = "no_match"
MatchWorldGenerating = "world_generating"
MatchWorldReady = "world_ready"
MatchInProgress = "in_progress"
MatchCompleted = "completed"

valid_match_states = [MatchNone, MatchWorldGenerating, MatchWorldReady, MatchInProgress, MatchCompleted]
match_state = MatchNone

def get_match_state() -> str:
    """
    Returns the match state.
    """
    return match_state

def set_match_state(new_state: str) -> None:
    """
    Mutates the global match_state variable.
    """
    if new_state not in valid_match_states:
        raise ValueError(f"Match state invalid. Recieved: {new_state}\n\tMust be in {valid_match_states}")
    global match_state
    match_state = new_state


ConnectionConnected = "connected"
ConnectionConnecting = "connecting"
ConnectionNotConnected = "not_connected"
ConnectionServerDown = "no_server"

valid_connection_states = [ConnectionNotConnected, ConnectionServerDown, ConnectionConnecting, ConnectionConnected]
connection_state = ConnectionNotConnected

def get_connection_state() -> str:
    """
    Returns the app's connection state.
    """
    return connection_state

def set_connection_state(new_state: str) -> None:
    """
    Mutates the global match_state variable
    """
    if new_state not in valid_connection_states:
        raise ValueError(f"Connection state invalid. Recieved: {new_state}\n\tMust be in {valid_connection_states}")
    global connection_state
    connection_state = new_state


def GetKleiSecret() -> str:
    return "123"
    raise NotImplementedError("Not implemented")

def HashString(string: str) -> str:
    return string
    raise NotImplementedError("Not implemented")

def SetUserData() -> None:
    return
    raise NotImplementedError("Not implemented")

def SetKleiSecret(new_secret: str) -> None:
    return
    raise NotImplementedError("Not implemented")