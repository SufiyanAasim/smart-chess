# ==============================================================================
# Project: Smart Chess
# Module: Unit Tests for Database Manager
# Author: Taha Siddiqui (@13eeCoder) - Security & Relational Storage Tests
# License: MIT License
# ==============================================================================
__author__ = "Taha Siddiqui"

import unittest
import os
import sys
import uuid

# Add src to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use a completely unique database filename to prevent file locks/residual data
        self.db_path = f"test_chess_db_{uuid.uuid4().hex}.sqlite"
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        # Force SQLite to release lock by garbage collecting the db manager
        import gc, time
        self.db = None
        gc.collect()
        if os.path.exists(self.db_path):
            for _ in range(5):
                try:
                    os.remove(self.db_path)
                    break
                except Exception:
                    time.sleep(0.05)
        if hasattr(self, "pgn_path") and os.path.exists(self.pgn_path):
            try:
                os.remove(self.pgn_path)
            except Exception:
                pass

    def test_record_and_fetch_game(self):
        # Assert database is initially empty
        games = self.db.fetch_recent_games()
        self.assertEqual(len(games), 0)

        # Record a match
        self.db.record_game("Alice", "Bob", "1-0", 42, "Local 1v1", san_moves="e4 e5 Nf3 Nc6")

        # Fetch recent games
        games = self.db.fetch_recent_games()
        self.assertEqual(len(games), 1)

        # Check values
        date, white, black, result, moves, mode = games[0]
        self.assertEqual(white, "Alice")
        self.assertEqual(black, "Bob")
        self.assertEqual(result, "1-0")
        self.assertEqual(moves, 42)
        self.assertEqual(mode, "Local 1v1")

    def test_fetch_limit(self):
        # Record 3 matches
        self.db.record_game("P1", "P2", "1/2-1/2", 10, "Local 1v1")
        self.db.record_game("P3", "P4", "0-1", 15, "Local 1v1")
        self.db.record_game("P5", "P6", "1-0", 20, "Local 1v1")

        # Fetch with limit=2
        games = self.db.fetch_recent_games(limit=2)
        self.assertEqual(len(games), 2)
        
        # Verify ordering (LIFO - descending by ID)
        self.assertEqual(games[0][1], "P5")
        self.assertEqual(games[1][1], "P3")

    def test_delete_and_clear_games(self):
        self.db.record_game("Alice", "Bob", "1-0", 40, "Local 1v1")
        self.db.record_game("Charlie", "Dave", "0-1", 30, "Local 1v1")
        
        games = self.db.fetch_recent_games_with_id()
        self.assertEqual(len(games), 2)
        
        # Delete first game
        game_id = games[0][0]
        self.db.delete_game_by_id(game_id)
        
        remaining = self.db.fetch_recent_games()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0][1], "Alice")
        
        # Clear all
        self.db.clear_all_games()
        self.assertEqual(len(self.db.fetch_recent_games()), 0)

    def test_puzzles_and_pgn_export(self):
        # Check seed puzzles
        puzzle = self.db.fetch_random_puzzle()
        self.assertIsNotNone(puzzle)
        pid, fen, sol, theme, rating, solved = puzzle
        self.assertEqual(solved, 0)
        
        # Mark solved
        self.db.mark_puzzle_solved(pid)
        
        # Verify PGN export
        self.db.record_game("WhitePlayer", "BlackPlayer", "1-0", 5, "Local 1v1", san_moves="e4 e5 Qh5 Nc6 Bc4 Nf6 Qxf7#")
        games = self.db.fetch_recent_games_with_id()
        gid = games[0][0]
        self.pgn_path = f"test_export_{uuid.uuid4().hex}.pgn"
        success = self.db.export_game_to_pgn(gid, self.pgn_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.pgn_path))
        with open(self.pgn_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("WhitePlayer", content)
            self.assertIn("Qxf7#", content)


if __name__ == "__main__":
    unittest.main()
