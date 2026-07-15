# ==============================================================================
# Project: Smart Chess
# Module: Game State Tracking (Board State & Rules)
# Author: Mohammad Sufiyan Aasim (@SufiyanAasim) - System Architect
# License: MIT License
# ==============================================================================
__author__ = "Mohammad Sufiyan Aasim"

import chess


class GameState:
    """
    Central state container tracking board rules, active timers, captures, and player modes (@author: Mohammad Sufiyan Aasim).
    """
    def __init__(self):
        self.board = chess.Board()

        self.running = False
        self.paused = False
        self.result_recorded = False

        self.mode = "Local 1v1"
        self.white_name = "White"
        self.black_name = "Black"

        # ai_controller.py/ chess_engine.py
        self.ai_side = None  # chess.WHITE/ chess.BLACK
        self.ai_thinking = False

        # LAN
        self.lan_enabled = False
        self.lan_role = None  # chess.WHITE/ chess.BLACK/ None(spectator Option)
        self.lan_started = False
        self.lan_connected_count = 0

        # move history
        self.san_moves = []

        # timers (@author: Taha Siddiqui - Time Controls & Increment)
        self.initial_time = 5 * 60
        self.increment_seconds = 0
        self.time_control_label = "5+0 min (Bullet)"
        self.white_time_left = self.initial_time
        self.black_time_left = self.initial_time
        self.ten_sec_white_played = False
        self.ten_sec_black_played = False

        # captures counters
        self.captured_by_white = {"Q": 0, "R": 0, "B": 0, "N": 0, "P": 0}
        self.captured_by_black = {"Q": 0, "R": 0, "B": 0, "N": 0, "P": 0}

        # premove (offline AI-offline Mode)
        self.premove = None  # (from_sq, to_sq, promo)/ None

    def reset_board(self, board: chess.Board | None = None):
        self.board = board if board is not None else chess.Board()

        self.running = False
        self.paused = False
        self.result_recorded = False
        self.san_moves.clear()

        self.white_time_left = self.initial_time
        self.black_time_left = self.initial_time
        self.ten_sec_white_played = False
        self.ten_sec_black_played = False

        self.captured_by_white = {"Q": 0, "R": 0, "B": 0, "N": 0, "P": 0}
        self.captured_by_black = {"Q": 0, "R": 0, "B": 0, "N": 0, "P": 0}

        self.premove = None
