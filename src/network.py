# ==============================================================================
# Project: Smart Chess
# Module: Networking Helpers & Protocol Definitions
# Author: Taha Siddiqui (@13eeCoder) - Security & Networking
# License: MIT License
# ==============================================================================
__author__ = "Taha Siddiqui"

import socket


def get_local_ip() -> str:
    """
    Best-effort local LAN IP detection without external calls (@author: Taha Siddiqui).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
