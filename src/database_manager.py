# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import os
import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_date TEXT NOT NULL,
                    white_player TEXT NOT NULL,
                    black_player TEXT NOT NULL,
                    result TEXT NOT NULL,
                    total_moves INTEGER NOT NULL,
                    mode TEXT NOT NULL
                )
                """
            )
            con.commit()

    def record_game(self, white_player: str, black_player: str, result: str, total_moves: int, mode: str):
        game_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO games (game_date, white_player, black_player, result, total_moves, mode)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (game_date, white_player, black_player, result, int(total_moves), mode),
            )
            con.commit()

    def fetch_recent_games(self, limit: int = 200):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT game_date, white_player, black_player, result, total_moves, mode
                FROM games
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            return cur.fetchall()
