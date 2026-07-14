# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

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

    def test_record_and_fetch_game(self):
        # Assert database is initially empty
        games = self.db.fetch_recent_games()
        self.assertEqual(len(games), 0)

        # Record a match
        self.db.record_game("Alice", "Bob", "1-0", 42, "Local 1v1")

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


if __name__ == "__main__":
    unittest.main()
