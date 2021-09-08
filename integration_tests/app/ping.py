""" integration tests - ping - Function for checking if an endpoint is active"""
from urllib.request import urlopen
import socket


def ping(host: str) -> bool:
    """
    Returns True if host (str) responds to a ping request.
    """
    socket.setdefaulttimeout(20)  # timeout in seconds
    try:
        urlopen(host)
    except Exception:
        print(">>> Server did not respond")
        return False
    else:
        return True
