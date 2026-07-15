# ==============================================================================
# Project: Smart Chess
# Test Module: LAN Controller Integration Tests
# Author: Taha Siddiqui (@13eeCoder) - Security & Networking
# License: MIT License
# ==============================================================================

import time
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from lan_controller import LANController


class TestLANController(unittest.TestCase):
    def setUp(self):
        self.host = LANController()
        self.client = LANController()

    def tearDown(self):
        self.client.stop()
        self.host.stop()
        time.sleep(0.2)

    def test_lan_host_join_and_sync(self):
        # 1. Start Host (Plays White)
        board = self.host.start_host_plays_white()
        self.assertIsNotNone(board)
        time.sleep(0.2)

        # 2. Client joins on localhost loopback
        self.client.start_join("127.0.0.1")
        time.sleep(0.5)

        # Verify Client received ROLE BLACK and FEN
        received_role = None
        deadline = time.time() + 2.0
        while time.time() < deadline and received_role is None:
            while not self.client.events.empty():
                ev, payload = self.client.events.get()
                if ev == "LAN_ROLE":
                    received_role = payload
            time.sleep(0.05)

        self.assertEqual(received_role, "BLACK", "Client should be assigned role BLACK when host plays white.")

        # 3. Test Chat broadcasting
        self.host.send_chat("White", "Welcome to LAN Match")
        
        chat_msg = None
        deadline = time.time() + 2.0
        while time.time() < deadline and chat_msg is None:
            while not self.client.events.empty():
                ev, payload = self.client.events.get()
                if ev == "LAN_CHAT":
                    chat_msg = payload
            time.sleep(0.05)

        self.assertEqual(chat_msg, "White: Welcome to LAN Match", "Client should receive chat broadcast from host.")

        # 4. Test Emote broadcasting
        self.client.send_emote("Black", "🔥")
        
        emote_msg = None
        deadline = time.time() + 2.0
        while time.time() < deadline and emote_msg is None:
            while not self.host.events.empty():
                ev, payload = self.host.events.get()
                if ev == "LAN_EMOTE":
                    emote_msg = payload
            time.sleep(0.05)

        self.assertEqual(emote_msg, "Black|🔥", "Host should receive emote broadcast from client.")


if __name__ == "__main__":
    unittest.main()
