import hashlib

def hash_string(raw_string: str) -> str:
    """
    Hash a string using SHA-256 and return a hex-encoded string.

    Parameters
    ----------
    raw_string: str
        The raw string to be hashed
    
    Returns
    -------
    hashed_string: str
        The result of the hashing algorithm
    """
    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()