# ==============================================================================
# Project: Smart Chess
# Module: Path Utilities & Resource Resolution
# Author: Mohammad Sufiyan Aasim (@SufiyanAasim) - System Architecture
# License: MIT License
# ==============================================================================
__author__ = "Mohammad Sufiyan Aasim"

import os
import sys


def resource_path(*parts: str) -> str:
    """
    Returns an absolute path to resource file/folder (@author: Mohammad Sufiyan Aasim).
    Works cleanly across local dev and bundled PyInstaller standalone environments.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, *parts)


def get_data_path(*parts: str) -> str:
    """
    Returns an absolute path to persistent read/write data files (e.g., database, pgn exports).
    In PyInstaller builds, points alongside the executable (`data/`) instead of temporary `_MEIPASS`.
    In development, points to project root (`data/`).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, "data", *parts)

