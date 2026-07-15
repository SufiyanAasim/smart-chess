# ==============================================================================
# Project: Smart Chess
# Module: AI Controller (Stockfish & Minimax Evaluation Engine)
# Author: Mohammad Sufiyan Aasim (@SufiyanAasim) - AI/MLOps & System Architecture
# License: MIT License
# ==============================================================================
__author__ = "Mohammad Sufiyan Aasim"

import queue
import threading
import chess

from chess_engine import PIECE_VALUES


class AIController:
    """
    Orchestrates AI evaluation loops across Stockfish and Minimax (@author: Mohammad Sufiyan Aasim).
    Runs AI-offline calculation in a background worker thread so the UI never freezes.
    Emits events into self.events:

      ("AI_MOVE", "<uci>")
      ("AI_ERROR", "<message>")
    """

    def __init__(self, engine):
        self.engine = engine
        self.events = queue.Queue()
        self.thinking = False
        self._stop = threading.Event()
        self._thread = None

    def stop(self):
        self._stop.set()

    def start_think(self, fen: str, minimax_depth: int = 2, stockfish_time: float = 0.25, stockfish_skill: int = 20):
        if self.thinking:
            return
        self.thinking = True
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._think_worker,
            args=(fen, minimax_depth, stockfish_time, stockfish_skill),
            daemon=True,
        )
        self._thread.start()

    def _think_worker(self, fen: str, minimax_depth: int, stockfish_time: float, stockfish_skill: int):
        try:
            if self.engine.has_stockfish():
                uci = self.engine.stockfish_bestmove(fen, move_time=stockfish_time, skill_level=stockfish_skill)
                self.events.put(("AI_MOVE", uci))
            else:
                board = chess.Board(fen)
                mv = self._minimax_root(board, depth=max(1, minimax_depth))
                if mv is None:
                    raise RuntimeError("No legal move found")
                self.events.put(("AI_MOVE", mv.uci()))
        except Exception as e:
            self.events.put(("AI_ERROR", str(e)))
        finally:
            self.thinking = False

    def start_analysis(self, san_moves: list):
        """
        Multithreaded post-match calculation loop (@author: Mohammad Sufiyan Aasim).
        Emits ("AI_ANALYSIS", {"evals": [...], "classifications": [...]}) to self.events.
        """
        if self.thinking:
            return
        self.thinking = True
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._analyze_worker,
            args=(san_moves,),
            daemon=True,
        )
        self._thread.start()

    def _analyze_worker(self, san_moves: list):
        try:
            board = chess.Board()
            evals = [0]
            move_classifications = []

            for idx, san in enumerate(san_moves):
                if self._stop.is_set():
                    break
                try:
                    mv = board.parse_san(san)
                    board.push(mv)
                except Exception:
                    break

                if self.engine.has_stockfish():
                    try:
                        sc = self.engine.stockfish_eval(board.fen(), depth=8)
                    except Exception:
                        sc = self._evaluate(board) * 100
                else:
                    sc = self._evaluate(board) * 100

                evals.append(sc)

                prev_sc = evals[-2]
                if idx % 2 == 0:
                    delta = sc - prev_sc
                else:
                    delta = prev_sc - sc

                if delta <= -300:
                    cls_name, emoji = "Blunder", "😱"
                elif delta <= -150:
                    cls_name, emoji = "Mistake", "😧"
                elif delta <= -75:
                    cls_name, emoji = "Inaccuracy", "🤔"
                else:
                    cls_name, emoji = "Best Move", "🔥"

                move_classifications.append({
                    "move_num": idx + 1,
                    "san": san,
                    "color": "White" if idx % 2 == 0 else "Black",
                    "eval": sc / 100.0,
                    "classification": cls_name,
                    "emoji": emoji
                })

            self.events.put(("AI_ANALYSIS", {"evals": evals, "classifications": move_classifications}))
        except Exception as e:
            self.events.put(("AI_ERROR", f"Analysis failed: {str(e)}"))
        finally:
            self.thinking = False

    # ---------- Minimax Algorithm ----------
    def _minimax_root(self, board: chess.Board, depth: int):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = legal_moves[0]
        best_score = -10**9 if board.turn == chess.WHITE else 10**9
        alpha = -10**9
        beta = 10**9

        for mv in legal_moves:
            board.push(mv)
            score = self._minimax(board, depth - 1, alpha, beta)
            board.pop()

            if board.turn == chess.WHITE:
                # white tries to maximize
                if score > best_score:
                    best_score = score
                    best_move = mv
                alpha = max(alpha, score)
            else:
                # black tries to minimize
                if score < best_score:
                    best_score = score
                    best_move = mv
                beta = min(beta, score)

        return best_move

    def _minimax(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        if board.is_game_over():
            if board.is_checkmate():
                return -10**6 if board.turn == chess.WHITE else 10**6
            return 0

        if depth <= 0:
            return self._evaluate(board)

        if board.turn == chess.WHITE:
            value = -10**9
            for mv in board.legal_moves:
                board.push(mv)
                value = max(value, self._minimax(board, depth - 1, alpha, beta))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 10**9
            for mv in board.legal_moves:
                board.push(mv)
                value = min(value, self._minimax(board, depth - 1, alpha, beta))
                board.pop()
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _evaluate(self, board: chess.Board) -> int:
        # material evaluation only simple & stable
        score = 0
        for pt, val in PIECE_VALUES.items():
            score += len(board.pieces(pt, chess.WHITE)) * val
            score -= len(board.pieces(pt, chess.BLACK)) * val
        return score
