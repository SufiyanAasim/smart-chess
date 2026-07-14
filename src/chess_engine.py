# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import os
import shutil
import subprocess
import chess


PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


class ChessEngine:
    """"
    Optional "Stockfish Algorithm" support if stockfish exists in PATH or in project folder
    Otherwise AI-offline mode uses minimax in "ai_controller.py"
    """

    def __init__(self):
        self._stockfish_path = self._detect_stockfish()

    def _detect_stockfish(self):
        # PATH
        p = shutil.which("stockfish")
        if p:
            return p
        # project folder "stockfish.exe"
        for candidate in ("stockfish.exe", "stockfish"):
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
            root_cand = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", candidate))
            if os.path.exists(root_cand):
                return root_cand
        return None

    def has_stockfish(self) -> bool:
        return self._stockfish_path is not None

    def stockfish_bestmove(self, fen: str, move_time: float = 0.25, skill_level: int = 20) -> str:
        """
        Very small UCI interaction: send position + go movetime.
        Returns a UCI move string like 'e2e4'.
        """
        if not self._stockfish_path:
            raise RuntimeError("Stockfish not available")

        # simple sub-process UCI session per request
        proc = subprocess.Popen(
            [self._stockfish_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        try:
            def send(cmd: str):
                proc.stdin.write(cmd + "\n")
                proc.stdin.flush()

            send("uci")
            send(f"setoption name Skill Level value {skill_level}")
            send("isready")
            send(f"position fen {fen}")
            ms = max(50, int(move_time * 1000))
            send(f"go movetime {ms}")

            best = None
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("bestmove"):
                    parts = line.split()
                    if len(parts) >= 2:
                        best = parts[1]
                    break

            if not best or best == "(none)":
                raise RuntimeError("Stockfish did not return a move")
            return best
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    def close(self):
        # nothing persistent to close in engine implementation
        pass
