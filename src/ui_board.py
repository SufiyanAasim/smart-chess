# ==============================================================================
# Project: Smart Chess
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim), Taha Siddiqui (@13eeCoder)
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import tkinter as tk
import chess

BOARD_THEMES = {
    "Classic Tan": {"light": "#E6E2D3", "dark": "#7A6A55"},
    "Classic Wood": {"light": "#E6C280", "dark": "#B37A42"},
    "Forest Green": {"light": "#E6E2D3", "dark": "#4E7A42"},
    "Ocean Blue": {"light": "#E2E8F0", "dark": "#4B9CD3"},
    "Midnight Dark": {"light": "#3A3F47", "dark": "#1F232B"}
}


class ChessBoardUI(tk.Canvas):
    """
    Tkinter Canvas chessboard:
    - Click piece -> shows legal target squares (green)
    - If target square has opponent piece -> highlight red
    - Last move highlighted
    - Premove highlight supported
    """
    def __init__(self, master, on_move_attempt, get_sprite_image_callback=None, is_game_running_callback=None):
        super().__init__(master, bg="#0F1115", highlightthickness=0)
        self.on_move_attempt = on_move_attempt
        self.get_sprite_image_callback = get_sprite_image_callback
        self.is_game_running_callback = is_game_running_callback

        self.board = chess.Board()
        self.theme_name = "Classic Tan"

        self.selected_sq = None
        self.legal_targets = set()

        self.last_move = None
        self.premove_visual = None  # (from,to)
        self.hint_move = None

        self._animating = False

        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda _e: self.redraw())

    def set_board(self, board: chess.Board):
        self.board = board
        self.selected_sq = None
        self.legal_targets.clear()
        self.hint_move = None
        self.redraw()

    def set_theme(self, theme_name: str):
        self.theme_name = theme_name
        self.redraw()

    def set_last_move(self, move: chess.Move | None):
        self.last_move = move
        self.redraw()

    def set_hint_move(self, move: chess.Move | None):
        self.hint_move = move
        self.redraw()

    def clear_hint(self):
        self.hint_move = None
        self.redraw()

    def set_premove_visual(self, from_sq: int, to_sq: int):
        self.premove_visual = (from_sq, to_sq)
        self.redraw()

    def clear_premove_visual(self):
        self.premove_visual = None
        self.redraw()

    def _square_px(self) -> int:
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        margin = 24
        return max(1, min(w - margin * 2, h - margin * 2) // 8)

    def _xy_to_square(self, x: int, y: int):
        sp = self._square_px()
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        board_w = sp * 8
        board_h = sp * 8
        ox = (w - board_w) // 2
        oy = (h - board_h) // 2

        file_ = (x - ox) // sp
        rank_from_top = (y - oy) // sp
        if not (0 <= file_ <= 7 and 0 <= rank_from_top <= 7):
            return None
        rank = 7 - rank_from_top
        return chess.square(file_, rank)


    def _square_to_xy(self, sq: int):
        sp = self._square_px()
        file_ = chess.square_file(sq)
        rank = chess.square_rank(sq)
        x = file_ * sp
        y = (7 - rank) * sp
        return x, y

    def _on_click(self, event):
        if self._animating:
            return

        # Do not allow any piece selection or target highlights if the game has not started (`running == False`).
        if self.is_game_running_callback and not self.is_game_running_callback():
            self.selected_sq = None
            self.legal_targets.clear()
            self.redraw()
            return

        self.hint_move = None

        sq = self._xy_to_square(event.x, event.y)
        if sq is None:
            return

        piece = self.board.piece_at(sq)

        # If a piece is selected and user clicked a legal target: attempt move.
        if self.selected_sq is not None and sq in self.legal_targets:
            self.on_move_attempt(self.selected_sq, sq)
            self.selected_sq = None
            self.legal_targets.clear()
            self.redraw()
            return

        # Otherwise, select if it's current side's piece.
        if piece and piece.color == self.board.turn:
            self.selected_sq = sq
            self._compute_legal_targets()
            self.redraw()
        else:
            self.selected_sq = None
            self.legal_targets.clear()
            self.redraw()

    def _compute_legal_targets(self):
        self.legal_targets.clear()
        if self.selected_sq is None or (self.is_game_running_callback and not self.is_game_running_callback()):
            return
        for mv in self.board.legal_moves:
            if mv.from_square == self.selected_sq:
                self.legal_targets.add(mv.to_square)

    def redraw(self):
        self.delete("all")
        sp = self._square_px()

        board_w = sp * 8
        board_h = sp * 8

        # Center board in canvas if canvas larger
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        ox = (w - board_w) // 2
        oy = (h - board_h) // 2

        # Draw Coordinates A-H and 1-8 in the margins
        for f in range(8):
            col_letter = chr(ord('A') + f)
            cx = ox + f * sp + sp // 2
            # Bottom label
            self.create_text(cx, oy + board_h + 12, text=col_letter, fill="#A9B0BC", font=("Segoe UI", 10, "bold"))
            # Top label
            self.create_text(cx, oy - 12, text=col_letter, fill="#A9B0BC", font=("Segoe UI", 10, "bold"))

        for r in range(8):
            row_number = str(8 - r)
            cy = oy + r * sp + sp // 2
            # Left label
            self.create_text(ox - 12, cy, text=row_number, fill="#A9B0BC", font=("Segoe UI", 10, "bold"))
            # Right label
            self.create_text(ox + board_w + 12, cy, text=row_number, fill="#A9B0BC", font=("Segoe UI", 10, "bold"))

        theme = BOARD_THEMES.get(self.theme_name, BOARD_THEMES["Classic Tan"])
        light = theme["light"]
        dark = theme["dark"]
        sel = "#4C8DFF"
        last = "#FFF59D"
        prem = "#9B59B6"
        hint_light = "#E8D0FF"
        hint_dark = "#9B59B6"

        game_running = True
        if self.is_game_running_callback and not self.is_game_running_callback():
            game_running = False

        # draw squares with width=0 and exact boundary coords to prevent clipping or outline box cutting
        for r in range(8):
            for f in range(8):
                x1 = ox + f * sp
                y1 = oy + r * sp
                x2 = ox + (f + 1) * sp
                y2 = oy + (r + 1) * sp
                is_dark = (r + f) % 2 == 1
                base = dark if is_dark else light

                sq = chess.square(f, 7 - r)

                # Only draw highlights when the game has started / is running
                if game_running:
                    # last move highlight
                    if self.last_move:
                        if sq == self.last_move.to_square:
                            base = "#FFF59D"
                        elif sq == self.last_move.from_square:
                            base = "#FFE082"

                    # hint move highlight
                    if self.hint_move and (sq == self.hint_move.from_square or sq == self.hint_move.to_square):
                        base = hint_dark if is_dark else hint_light

                    # premove highlight
                    if self.premove_visual and (sq == self.premove_visual[0] or sq == self.premove_visual[1]):
                        base = prem

                    # legal moves highlight
                    if sq in self.legal_targets:
                        px = self.board.piece_at(sq)
                        has_opponent = px and px.color != self.board.turn
                        if has_opponent:
                            base = "#A04040" if is_dark else "#ECA1A1"
                        else:
                            base = "#4D8066" if is_dark else "#B8E2C8"

                    # selection highlight
                    if self.selected_sq == sq:
                        base = sel

                self.create_rectangle(x1, y1, x2, y2, fill=base, width=0)

        # pieces
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue
            x, y = self._square_to_xy(sq)
            x += ox
            y += oy

            img = None
            if self.get_sprite_image_callback:
                img = self.get_sprite_image_callback(piece, sp)

            if img:
                self.create_image(x + sp // 2, y + sp // 2, image=img)
            else:
                # Unicode fallback
                glyph = piece.unicode_symbol()
                self.create_text(
                    x + sp // 2,
                    y + sp // 2,
                    text=glyph,
                    font=("Segoe UI Symbol", max(14, int(sp * 0.6))),
                )

    def animate_move(self, move: chess.Move, moving_piece: chess.Piece, on_done=None):
        # Minimal: do not animate deeply; just redraw and call done
        self._animating = True
        self.after(10, lambda: self._finish_anim(on_done))

    def _finish_anim(self, on_done):
        self._animating = False
        if on_done:
            on_done()
