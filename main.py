# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import sys
import os

# Add src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chess_app import ChessApp

if __name__ == "__main__":
    app = ChessApp()
    app.mainloop()
