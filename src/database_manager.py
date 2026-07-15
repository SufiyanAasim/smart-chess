# ==============================================================================
# Project: Smart Chess
# Module: Database Manager (Parameterized SQLite & Query Security Isolation)
# Author: Taha Siddiqui (@13eeCoder) - Security & Relational Storage
# License: MIT License
# ==============================================================================
__author__ = "Taha Siddiqui"

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages SQLite relational database storage and query execution for match logs.
    
    Responsibilities & Security Rules (@author: Taha Siddiqui):
    - Uses fully parameterized queries to ensure isolation from SQL injection attacks.
    - Handles automatic table schema creation and migration.
    - Provides historical game queries, targeted ID deletions, and bulk wipe actions.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db_path)
        try:
            with con:
                yield con
        finally:
            con.close()

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
                    mode TEXT NOT NULL,
                    san_moves TEXT DEFAULT ''
                )
                """
            )
            # Schema migration for existing databases missing san_moves
            try:
                cur.execute("ALTER TABLE games ADD COLUMN san_moves TEXT DEFAULT ''")
            except Exception:
                pass

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS puzzles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fen TEXT NOT NULL,
                    solution_uci TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    solved INTEGER DEFAULT 0
                )
                """
            )
            con.commit()
        self.ensure_puzzles_seed()

    def ensure_puzzles_seed(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM puzzles")
            count = cur.fetchone()[0]
            if count == 0:
                seed_puzzles = [
                    ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7", "Scholar's Mate in 1", 800),
                    ("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR b KQkq - 1 2", "h4e1", "Fool's Mate in 1", 600),
                    ("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1", "e1e8", "Back Rank Checkmate in 1", 900),
                    ("r2q1rk1/ppp2ppp/2n1bn2/2b1p3/4P3/2NB1N2/PPPB1PPP/R2Q1RK1 b - - 0 8", "c6d4", "Central Outpost Knight", 1100),
                    ("2kr3r/ppp2ppp/2n5/3q4/3P4/2B5/PP3PPP/R2Q1RK1 w - - 1 13", "d1g4,c8b8,g4g7", "Double Attack & Capture", 1300),
                    ("r1bqk2r/pp1n1ppp/2n1p3/2bpP3/5B2/2NB1N2/PPP2PPP/R2Q1RK1 w kq - 2 9", "d3h7,g8h7,f3g5", "Classic Greek Gift Sacrifice", 1600),
                    ("4r1k1/5ppp/8/8/3Q4/8/5PPP/4R1K1 w - - 0 1", "e1e8", "Back Rank Mate with Queen Guard", 1000),
                    ("r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 b kq - 3 4", "g8f6", "Two Knights Defense Opening", 950),
                    ("r3k2r/ppp2ppp/2n2q2/3P4/2B1p1b1/2P2N2/P1P2PPP/R2QK2R w KQkq - 0 11", "d5c6,e4f3,d1e2", "Tactical Counter-Attack", 1450),
                    ("6k1/pp3ppp/8/3Q4/8/8/PP3PPP/4q1K1 w - - 0 1", "g1f1", "King Escape Check", 850),
                    ("3r2k1/p4ppp/1p6/8/8/1P1R4/P4PPP/6K1 w - - 0 1", "d3d8", "Rook Capture Checkmate", 900),
                    ("r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2PP1N2/PP3PPP/RNBQ1RK1 w - - 0 7", "d3d4,e5d4,c3d4", "Center Pawn Break", 1200),
                ]
                cur.executemany(
                    "INSERT INTO puzzles (fen, solution_uci, theme, rating, solved) VALUES (?, ?, ?, ?, 0)",
                    seed_puzzles
                )
                con.commit()

    def record_game(self, white_player: str, black_player: str, result: str, total_moves: int, mode: str, san_moves: str = ""):
        game_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO games (game_date, white_player, black_player, result, total_moves, mode, san_moves)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (game_date, white_player, black_player, result, int(total_moves), mode, san_moves),
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

    def fetch_recent_games_with_id(self, limit: int = 200):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT id, game_date, white_player, black_player, result, total_moves, mode
                FROM games
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            return cur.fetchall()

    def fetch_game_by_id(self, game_id: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, game_date, white_player, black_player, result, total_moves, mode, san_moves FROM games WHERE id = ?", (int(game_id),))
            return cur.fetchone()

    def fetch_all_games_with_san(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, game_date, white_player, black_player, result, total_moves, mode, san_moves FROM games ORDER BY id ASC")
            return cur.fetchall()

    def delete_game_by_id(self, game_id: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM games WHERE id = ?", (int(game_id),))
            con.commit()

    def clear_all_games(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM games")
            con.commit()

    def fetch_random_puzzle(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, fen, solution_uci, theme, rating, solved FROM puzzles WHERE solved = 0 ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id, fen, solution_uci, theme, rating, solved FROM puzzles ORDER BY RANDOM() LIMIT 1")
                row = cur.fetchone()
            return row

    def mark_puzzle_solved(self, puzzle_id: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE puzzles SET solved = 1 WHERE id = ?", (int(puzzle_id),))
            con.commit()

    def export_game_to_pgn(self, game_id: int, filepath: str) -> bool:
        row = self.fetch_game_by_id(game_id)
        if not row:
            return False
        import chess.pgn
        game = self._row_to_pgn_game(row)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(game) + "\n\n")
        return True

    def export_all_to_pgn(self, filepath: str) -> int:
        rows = self.fetch_all_games_with_san()
        if not rows:
            return 0
        import chess.pgn
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        count = 0
        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows:
                game = self._row_to_pgn_game(row)
                f.write(str(game) + "\n\n")
                count += 1
        return count

    def _row_to_pgn_game(self, row):
        import chess
        import chess.pgn
        gid, game_date, wp, bp, result, total_moves, mode, san_moves = row
        game = chess.pgn.Game()
        game.headers["Event"] = f"Smart Chess ({mode})"
        game.headers["Date"] = game_date.split(" ")[0] if " " in game_date else game_date
        game.headers["White"] = wp
        game.headers["Black"] = bp
        game.headers["Result"] = result
        game.headers["PlyCount"] = str(total_moves)

        node = game
        if san_moves and san_moves.strip():
            board = chess.Board()
            moves_list = [m.strip() for m in san_moves.split(" ") if m.strip()]
            for san in moves_list:
                try:
                    mv = board.parse_san(san)
                    node = node.add_variation(mv)
                    board.push(mv)
                except Exception:
                    break
        return game
