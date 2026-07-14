# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import chess


class GameState:
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

        # timers
        self.initial_time = 5 * 60
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
