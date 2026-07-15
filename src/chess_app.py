# ==============================================================================
# Project: Smart Chess
# Module: Core Application Controller & System Orchestrator
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim) - System Architecture & UI Transitions
#          Taha Siddiqui (@13eeCoder) - Multi-threaded Loops, Networking & Security Handlers
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import os
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import chess

from utils_paths import resource_path, get_data_path
from database_manager import DatabaseManager
from chess_engine import ChessEngine, PIECE_VALUES
from sound_manager import SoundManager
from ui_board import ChessBoardUI
from game_state import GameState
from lan_controller import LANController
from ui_sidebar import UISidebar
from ai_controller import AIController

# Optional background image support
try:
    from PIL import Image, ImageTk  # pip install pillow
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class HoverTooltip:
    """
    Floating tooltip controller (@author: Mohammad Sufiyan Aasim).
    """
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.widget:
            return
        
        text = self.text_func()
        if not text:
            return
            
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg="#171A21")
        
        f = tk.Frame(tw, bg="#171A21", highlightthickness=1, highlightbackground="#4C8DFF", bd=0)
        f.pack(fill="both", expand=True)
        
        lbl = tk.Label(f, text=text, justify="left", font=("Segoe UI", 10), bg="#171A21", fg="#E7EAF0", padx=12, pady=10)
        lbl.pack()

        # Update geometry to get correct winfo values
        tw.update_idletasks()
        tw_w = tw.winfo_width()
        tw_h = tw.winfo_height()
        
        # Position to the RIGHT of the widget with 15px gap (prevents cursor overlap & glitching)
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 15
        y = self.widget.winfo_rooty() + (self.widget.winfo_height() - tw_h) // 2
        
        tw.geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class CustomMessageBox(tk.Toplevel):
    def __init__(self, parent, title, message, box_type="info", yes_text="Yes", no_text="No", is_danger=False):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Center on parent window
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = 400
        h = 170
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        self.result = None

        # Content frame
        content = ttk.Frame(self, style="Card.TFrame", padding=18)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # Message Label with modern icon prefix when danger
        icon_prefix = "⚠️  " if is_danger else ("❌  " if box_type == "error" else "")
        lbl_msg = ttk.Label(
            content, 
            text=icon_prefix + message, 
            background="#171A21", 
            foreground="#FF6B6B" if is_danger else "#E7EAF0",
            font=("Segoe UI", 11, "bold" if is_danger else "normal"), 
            wraplength=350, 
            justify="center",
            anchor="center"
        )
        lbl_msg.grid(row=0, column=0, sticky="nsew", pady=(0, 16))

        # Button Frame
        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.grid(row=1, column=0, sticky="ew")

        if box_type in ("info", "error"):
            btn_frame.columnconfigure(0, weight=1)
            btn = ttk.Button(btn_frame, text="OK", style="Accent.TButton", command=self.on_ok)
            btn.grid(row=0, column=0, ipady=2, ipadx=10)
        elif box_type == "yesno":
            btn_frame.columnconfigure((0, 1), weight=1)
            yes_style = "Danger.TButton" if is_danger else "Accent.TButton"
            btn_yes = ttk.Button(btn_frame, text=yes_text, style=yes_style, command=self.on_yes)
            btn_yes.grid(row=0, column=0, padx=(0, 8), sticky="ew")
            btn_no = ttk.Button(btn_frame, text=no_text, style="Ghost.TButton", command=self.on_no)
            btn_no.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.bind("<Return>", lambda e: self.on_ok() if box_type in ("info", "error") else self.on_yes())
        self.bind("<Escape>", lambda e: self.on_no() if box_type == "yesno" else self.on_ok())
        self.wait_window(self)

    def on_ok(self):
        self.result = True
        self.destroy()

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_theme, sound_enabled, sound_volume, current_difficulty, on_save):
        super().__init__(parent)
        self.title("Game Settings")
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Center on parent window
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = 400
        h = 320
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        self.on_save = on_save

        content = ttk.Frame(self, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)

        # Title
        ttk.Label(content, text="Game Settings", font=("Segoe UI", 14, "bold"), background="#171A21", foreground="#E7EAF0").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Board Theme
        ttk.Label(content, text="Board Theme", background="#171A21", foreground="#E7EAF0").grid(row=1, column=0, sticky="w", pady=8)
        self.theme_var = tk.StringVar(value=current_theme)
        self.theme_combo = ttk.Combobox(
            content,
            textvariable=self.theme_var,
            values=["Classic Tan", "Classic Wood", "Forest Green", "Ocean Blue", "Midnight Dark"],
            state="readonly",
            width=20
        )
        self.theme_combo.grid(row=1, column=1, sticky="e", pady=8)

        # Sound Enable (Styled Flat Button Toggle)
        ttk.Label(content, text="Sound Effects", background="#171A21", foreground="#E7EAF0").grid(row=2, column=0, sticky="w", pady=8)
        self.sound_enabled_var = tk.BooleanVar(value=sound_enabled)
        
        self.sound_toggle_btn = ttk.Button(content, text="", command=self.on_sound_toggle_click)
        self.sound_toggle_btn.grid(row=2, column=1, sticky="e", pady=8)

        # Sound Volume
        ttk.Label(content, text="Sound Volume", background="#171A21", foreground="#E7EAF0").grid(row=3, column=0, sticky="w", pady=8)
        self.sound_volume_var = tk.DoubleVar(value=sound_volume * 100.0)
        self.sound_scale = ttk.Scale(content, from_=0.0, to=100.0, variable=self.sound_volume_var, orient="horizontal")
        self.sound_scale.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=8)

        # AI Difficulty
        ttk.Label(content, text="AI Difficulty", background="#171A21", foreground="#E7EAF0").grid(row=4, column=0, sticky="w", pady=8)
        self.diff_var = tk.StringVar(value=current_difficulty)
        self.diff_combo = ttk.Combobox(
            content,
            textvariable=self.diff_var,
            values=["Easy", "Medium", "Hard"],
            state="readonly",
            width=20
        )
        self.diff_combo.grid(row=4, column=1, sticky="e", pady=8)

        # Buttons
        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure((0, 1), weight=1)

        ttk.Button(btn_frame, text="Save Settings", style="Accent.TButton", command=self.save).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ttk.Button(btn_frame, text="Cancel", style="Ghost.TButton", command=self.destroy).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Initial call to set toggle styling & slider state
        self.update_sound_toggle_btn()
        self.toggle_sound_slider()

    def update_sound_toggle_btn(self):
        if self.sound_enabled_var.get():
            self.sound_toggle_btn.configure(text="🔊 ON", style="Accent.TButton")
        else:
            self.sound_toggle_btn.configure(text="🔇 OFF", style="Ghost.TButton")

    def on_sound_toggle_click(self):
        self.sound_enabled_var.set(not self.sound_enabled_var.get())
        self.update_sound_toggle_btn()
        self.toggle_sound_slider()

    def toggle_sound_slider(self):
        if self.sound_enabled_var.get():
            self.sound_scale.configure(state="normal")
        else:
            self.sound_scale.configure(state="disabled")

    def save(self):
        self.on_save({
            "theme": self.theme_var.get(),
            "sound_enabled": self.sound_enabled_var.get(),
            "sound_volume": self.sound_volume_var.get() / 100.0,
            "difficulty": self.diff_var.get()
        })
        self.destroy()


class CreditsDialog(tk.Toplevel):
    """
    Credits and contributor recognition modal (@author: Mohammad Sufiyan Aasim).
    Displays contributor responsibilities and external GitHub repository links.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Smart Chess - Credits")
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Center on parent window
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = 500
        h = 485
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(self, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        # Logo branding
        logo_path = resource_path("src", "resources", "app_logo", "logo.png")
        if os.path.exists(logo_path) and PIL_AVAILABLE:
            try:
                pil_logo = Image.open(logo_path)
                pil_logo = pil_logo.resize((80, 80), Image.Resampling.LANCZOS)
                self.credits_logo_imgtk = ImageTk.PhotoImage(pil_logo)
                
                logo_lbl = tk.Label(content, image=self.credits_logo_imgtk, bg="#171A21")
                logo_lbl.pack(pady=(0, 8))
            except Exception:
                pass

        # Game Title
        ttk.Label(content, text="Smart Chess Client", font=("Segoe UI", 16, "bold"), background="#171A21", foreground="#E7EAF0").pack(pady=(0, 5))
        ttk.Label(content, text="Professional Desktop Chess Platform • v5.0.0 (Grandmaster)", font=("Segoe UI", 10, "bold"), background="#171A21", foreground="#4C8DFF").pack(pady=(0, 10))

        # Divider line
        divider = tk.Frame(content, height=2, bg="#4C8DFF", bd=0)
        divider.pack(fill="x", pady=(0, 15))

        # Grid for Contributors
        grid = ttk.Frame(content, style="Card.TFrame")
        grid.pack(fill="both", expand=True, pady=(0, 15))
        grid.columnconfigure((0, 1), weight=1)
        grid.rowconfigure(0, weight=1)

        import webbrowser

        # Contributor 1
        c1_frame = tk.Frame(grid, bg="#1E2330", highlightthickness=1, highlightbackground="#2A3040", bd=0, padx=10, pady=12)
        c1_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ttk.Label(c1_frame, text="Mohammad Sufiyan Aasim", font=("Segoe UI", 10, "bold"), background="#1E2330", foreground="#E7EAF0").pack(anchor="w")
        ttk.Label(c1_frame, text="System Architect & AI/MLOps", font=("Segoe UI", 8), background="#1E2330", foreground="#A9B0BC").pack(anchor="w", pady=(2, 6))
        
        btn_c1 = ttk.Button(
            c1_frame, text="GitHub ↗", style="Accent.TButton",
            command=lambda: webbrowser.open_new_tab("https://github.com/SufiyanAasim")
        )
        btn_c1.pack(anchor="w")

        # Contributor 2
        c2_frame = tk.Frame(grid, bg="#1E2330", highlightthickness=1, highlightbackground="#2A3040", bd=0, padx=10, pady=12)
        c2_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        ttk.Label(c2_frame, text="Taha Siddiqui", font=("Segoe UI", 10, "bold"), background="#1E2330", foreground="#E7EAF0").pack(anchor="w")
        ttk.Label(c2_frame, text="Security & Networking", font=("Segoe UI", 8), background="#1E2330", foreground="#A9B0BC").pack(anchor="w", pady=(2, 6))
        
        btn_c2 = ttk.Button(
            c2_frame, text="GitHub ↗", style="Accent.TButton",
            command=lambda: webbrowser.open_new_tab("https://github.com/13eeCoder")
        )
        btn_c2.pack(anchor="w")

        # Project Details Footer
        details = (
            "App Version: v5.0.0 (Grandmaster)\n"
            "Built with: Python, Tkinter, Pygame Audio, Pillow, python-chess,\n"
            "Stockfish 18, SQLite (Match History)"
        )
        ttk.Label(content, text=details, font=("Segoe UI", 8), justify="center", background="#171A21", foreground="#A9B0BC").pack(pady=(5, 10))

        # Close button
        ttk.Button(content, text="Close", style="Ghost.TButton", command=self.destroy).pack(side="bottom", ipady=2, ipadx=15)


class CustomTimeDialog(tk.Toplevel):
    """
    Dialog for configuring custom clock durations and Fischer increments (@author: Taha Siddiqui).
    """
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Custom Time Control")
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        parent.update_idletasks()
        px, py, pw, ph = parent.winfo_rootx(), parent.winfo_rooty(), parent.winfo_width(), parent.winfo_height()
        w, h = 360, 240
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(self, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)

        ttk.Label(content, text="⏱️ Custom Time Settings", font=("Segoe UI", 14, "bold"), background="#171A21", foreground="#4C8DFF").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        ttk.Label(content, text="Initial Minutes:", font=("Segoe UI", 10), background="#171A21", foreground="#E7EAF0").grid(row=1, column=0, sticky="w", pady=6)
        self.min_var = tk.IntVar(value=10)
        ttk.Entry(content, textvariable=self.min_var, width=10).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(content, text="Increment (Sec):", font=("Segoe UI", 10), background="#171A21", foreground="#E7EAF0").grid(row=2, column=0, sticky="w", pady=6)
        self.inc_var = tk.IntVar(value=5)
        ttk.Entry(content, textvariable=self.inc_var, width=10).grid(row=2, column=1, sticky="w", pady=6)

        btn_row = ttk.Frame(content, style="Card.TFrame")
        btn_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_row.columnconfigure((0, 1), weight=1)

        def save_click():
            try:
                m = max(1, self.min_var.get())
                i = max(0, self.inc_var.get())
                on_save(m, i)
                self.destroy()
            except Exception:
                pass

        ttk.Button(btn_row, text="Apply", style="Accent.TButton", command=save_click).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="Cancel", style="Ghost.TButton", command=self.destroy).grid(row=0, column=1, sticky="ew", padx=(6, 0))


class PostMatchAnalysisModal(tk.Toplevel):
    """
    Dynamic evaluation bar & blunder graph displayed post-match (@author: Mohammad Sufiyan Aasim).
    Shows evaluation curves from +2.5 to -4.0 and move classification breakdown.
    """
    def __init__(self, parent, analysis_data):
        super().__init__(parent)
        self.title("📊 Post-Match Evaluation & Analysis")
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        px, py, pw, ph = parent.winfo_rootx(), parent.winfo_rooty(), parent.winfo_width(), parent.winfo_height()
        w, h = 820, 560
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(self, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        ttk.Label(content, text="Post-Match Evaluation & Blunder Graph", font=("Segoe UI", 16, "bold"), background="#171A21", foreground="#E7EAF0").grid(row=0, column=0, sticky="w", pady=(0, 5))

        classifications = analysis_data.get("classifications", [])
        best_c = sum(1 for c in classifications if c["classification"] == "Best Move")
        inacc_c = sum(1 for c in classifications if c["classification"] == "Inaccuracy")
        mist_c = sum(1 for c in classifications if c["classification"] == "Mistake")
        blun_c = sum(1 for c in classifications if c["classification"] == "Blunder")

        stats_str = f"🔥 Best Moves: {best_c}  |  🤔 Inaccuracies: {inacc_c}  |  😧 Mistakes: {mist_c}  |  😱 Blunders: {blun_c}"
        ttk.Label(content, text=stats_str, font=("Segoe UI", 11, "bold"), background="#171A21", foreground="#4C8DFF").grid(row=1, column=0, sticky="w", pady=(0, 15))

        cols = ("move_num", "color", "san", "eval", "class", "icon")
        tree = ttk.Treeview(content, columns=cols, show="headings", style="Custom.Treeview")
        tree.grid(row=2, column=0, sticky="nsew")

        headers = {"move_num": "#", "color": "Side", "san": "Move (SAN)", "eval": "Eval (CP)", "class": "Classification", "icon": "Icon"}
        for c in cols:
            tree.heading(c, text=headers[c])
            tree.column(c, width=120 if c in ("class", "eval") else (60 if c in ("move_num", "icon") else 100), anchor="center")

        sb = ttk.Scrollbar(content, orient="vertical", command=tree.yview)
        sb.grid(row=2, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        for item in classifications:
            ev_str = f"{item['eval']:+.2f}"
            tree.insert("", tk.END, values=(item["move_num"], item["color"], item["san"], ev_str, item["classification"], item["emoji"]))

        ttk.Button(content, text="Close Analysis", style="Accent.TButton", command=self.destroy).grid(row=3, column=0, columnspan=2, sticky="e", pady=(15, 0))


class ReplayViewerModal(tk.Toplevel):
    """
    Step-by-step game replay viewer with PGN move controls (@author: Mohammad Sufiyan Aasim & Taha Siddiqui).
    Supports: ◀◀ First | ◀ Prev | ▶ Next | ▶▶ Last | ▶ Auto-Play
    """
    def __init__(self, parent, san_moves: list, white_name: str, black_name: str, get_sprite_callback=None):
        super().__init__(parent)
        self.title("◀ Game Replay Viewer")
        self.configure(bg="#0F1115")
        self.transient(parent)
        self.grab_set()

        parent.update_idletasks()
        px, py, pw, ph = parent.winfo_rootx(), parent.winfo_rooty(), parent.winfo_width(), parent.winfo_height()
        w, h = 900, 640
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        self.san_moves = san_moves
        self.current_idx = 0
        self._autoplay_job = None
        self.board = chess.Board()

        layout = ttk.Frame(self, padding=16)
        layout.pack(fill="both", expand=True)
        layout.columnconfigure(0, weight=3)
        layout.columnconfigure(1, weight=2)
        layout.rowconfigure(0, weight=1)

        board_card = ttk.Frame(layout, style="Card.TFrame", padding=12)
        board_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        board_card.columnconfigure(0, weight=1)
        board_card.rowconfigure(0, weight=1)

        self.board_ui = ChessBoardUI(
            board_card,
            on_move_attempt=lambda _f, _t: None,
            get_sprite_image_callback=get_sprite_callback,
            is_game_running_callback=lambda: True
        )
        self.board_ui.grid(row=0, column=0, sticky="nsew")
        self.board_ui.set_board(self.board)

        sidebar = ttk.Frame(layout, style="Card.TFrame", padding=16)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(2, weight=1)

        ttk.Label(sidebar, text=f"{white_name} vs {black_name}", font=("Segoe UI", 13, "bold"), background="#171A21", foreground="#E7EAF0").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.status_lbl = ttk.Label(sidebar, text=f"Move 0 / {len(self.san_moves)}", font=("Segoe UI", 10), background="#171A21", foreground="#4C8DFF")
        self.status_lbl.grid(row=1, column=0, sticky="w", pady=(0, 12))

        self.history_list = tk.Listbox(sidebar, bg="#12151C", fg="#E7EAF0", font=("Consolas", 11), borderwidth=0, highlightthickness=0, selectbackground="#4C8DFF")
        self.history_list.grid(row=2, column=0, sticky="nsew")

        sb = ttk.Scrollbar(sidebar, orient="vertical", command=self.history_list.yview)
        sb.grid(row=2, column=1, sticky="ns")
        self.history_list.config(yscrollcommand=sb.set)

        for idx, san in enumerate(self.san_moves):
            self.history_list.insert(tk.END, f"{idx+1}. {san}")

        ctrl_frame = ttk.Frame(sidebar, style="Card.TFrame")
        ctrl_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        for c in range(5):
            ctrl_frame.columnconfigure(c, weight=1)

        ttk.Button(ctrl_frame, text="◀◀", style="Ghost.TButton", command=self.go_first).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(ctrl_frame, text="◀", style="Ghost.TButton", command=self.go_prev).grid(row=0, column=1, padx=2, sticky="ew")
        self.btn_auto = ttk.Button(ctrl_frame, text="▶ Auto", style="Accent.TButton", command=self.toggle_autoplay)
        self.btn_auto.grid(row=0, column=2, padx=2, sticky="ew")
        ttk.Button(ctrl_frame, text="▶", style="Ghost.TButton", command=self.go_next).grid(row=0, column=3, padx=2, sticky="ew")
        ttk.Button(ctrl_frame, text="▶▶", style="Ghost.TButton", command=self.go_last).grid(row=0, column=4, padx=2, sticky="ew")

        ttk.Button(sidebar, text="Close Replay", style="Ghost.TButton", command=self.destroy).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _sync_board(self):
        self.board.reset()
        last_mv = None
        for i in range(self.current_idx):
            try:
                last_mv = self.board.push_san(self.san_moves[i])
            except Exception:
                break
        self.board_ui.set_board(self.board)
        self.board_ui.set_last_move(last_mv)
        self.status_lbl.config(text=f"Move {self.current_idx} / {len(self.san_moves)}")
        self.history_list.selection_clear(0, tk.END)
        if self.current_idx > 0:
            self.history_list.selection_set(self.current_idx - 1)
            self.history_list.see(self.current_idx - 1)

    def go_first(self):
        self._stop_auto()
        self.current_idx = 0
        self._sync_board()

    def go_prev(self):
        self._stop_auto()
        if self.current_idx > 0:
            self.current_idx -= 1
            self._sync_board()

    def go_next(self):
        self._stop_auto()
        if self.current_idx < len(self.san_moves):
            self.current_idx += 1
            self._sync_board()

    def go_last(self):
        self._stop_auto()
        self.current_idx = len(self.san_moves)
        self._sync_board()

    def toggle_autoplay(self):
        if self._autoplay_job is not None:
            self._stop_auto()
        else:
            self.btn_auto.config(text="⏸ Stop")
            self._tick_auto()

    def _tick_auto(self):
        if self.current_idx < len(self.san_moves):
            self.current_idx += 1
            self._sync_board()
            self._autoplay_job = self.after(800, self._tick_auto)
        else:
            self._stop_auto()

    def _stop_auto(self):
        if self._autoplay_job is not None:
            try:
                self.after_cancel(self._autoplay_job)
            except Exception:
                pass
        self._autoplay_job = None
        self.btn_auto.config(text="▶ Auto")

    def _on_close(self):
        self._stop_auto()
        self.destroy()


class GameOverDialog(tk.Toplevel):
    """
    Match termination modal and rematch selector (@author: Mohammad Sufiyan Aasim).
    Displays victory/draw reasons, match score summaries, and rematch options.
    """
    def __init__(self, parent, title, result_text, details_text, on_rematch, on_close, on_analysis=None, on_replay=None):
        super().__init__(parent)
        self.title("Game Over")
        self.configure(bg="#171A21")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Center on parent window
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w, h = 540, 310
        self.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(self, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        # Header Title
        ttk.Label(content, text=title, font=("Segoe UI", 16, "bold"), background="#171A21", foreground="#4C8DFF").pack(pady=(0, 10))

        # Result Text
        ttk.Label(content, text=result_text, font=("Segoe UI", 12, "bold"), background="#171A21", foreground="#E7EAF0").pack(pady=5)

        # Details Text
        ttk.Label(content, text=details_text, font=("Segoe UI", 10), background="#171A21", foreground="#A9B0BC", justify="center").pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.pack(fill="x", side="bottom", pady=(15, 0))
        for c in range(4):
            btn_frame.columnconfigure(c, weight=1)

        def rematch_click():
            self.destroy()
            on_rematch()

        def close_click():
            self.destroy()
            on_close()

        def analysis_click():
            if on_analysis:
                on_analysis()

        def replay_click():
            if on_replay:
                on_replay()

        ttk.Button(btn_frame, text="📊 Analysis", style="Accent.TButton", command=analysis_click).grid(row=0, column=0, padx=3, sticky="ew")
        ttk.Button(btn_frame, text="◀ Replay", style="Ghost.TButton", command=replay_click).grid(row=0, column=1, padx=3, sticky="ew")
        ttk.Button(btn_frame, text="🔄 Rematch", style="Ghost.TButton", command=rematch_click).grid(row=0, column=2, padx=3, sticky="ew")
        ttk.Button(btn_frame, text="🚪 Setup", style="Ghost.TButton", command=close_click).grid(row=0, column=3, padx=3, sticky="ew")


def piece_asset_key(piece: chess.Piece) -> str:
    color = "w" if piece.color == chess.WHITE else "b"
    pt = {
        chess.PAWN: "P",
        chess.KNIGHT: "N",
        chess.BISHOP: "B",
        chess.ROOK: "R",
        chess.QUEEN: "Q",
        chess.KING: "K",
    }[piece.piece_type]
    return f"{color}{pt}"


class ChessApp(tk.Tk):
    """
    Main application orchestrator and lifecycle window manager.
    
    Architectural & Statement Division of Responsibilities:
    - @author: Mohammad Sufiyan Aasim -> System Architecture, UI Screens, Game Loops, Board Canvas Transitions & Dialogs.
    - @author: Taha Siddiqui -> Multi-threaded Network Polling, Timer Threads, Database Match Records & Audio/Security Polling.
    """
    def __init__(self):
        super().__init__()

        self.title("Smart Chess")
        self.configure(bg="#0F1115")

        # Exact structure you specified
        self.sounds_dir = resource_path("src", "resources", "sounds")
        self.sprite_dir = resource_path("src", "resources", "assets", "pieces in png")
        self.start_bg_path = resource_path("src", "resources", "assets", "start_bg.png")
        self.db_path = get_data_path("chess_games.db")

        self.db = DatabaseManager(db_path=self.db_path)
        self.engine = ChessEngine()
        self.ai = AIController(self.engine)
        self.lan = LANController()
        
        self.difficulty_var = tk.StringVar(value="Select Difficulty...")
        self.sound_enabled_var = tk.BooleanVar(value=True)
        self.sound_volume_var = tk.DoubleVar(value=1.0)
        
        self.sounds = SoundManager(self, sounds_dir=self.sounds_dir, enabled=self.sound_enabled_var.get())
        self.sounds.set_volume(self.sound_volume_var.get())

        self.state_obj = GameState()

        # Fullscreen keys MUST work even when focus is inside Entry/Listbox:
        self._is_fullscreen = False
        self.bind_all("<F11>", self._toggle_fullscreen, add="+")
        self.bind_all("<Escape>", self._exit_fullscreen, add="+")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.state("zoomed")
        except Exception:
            pass
        self.minsize(1120, 700)

        self.sprite_cache = {}
        self._timer_job = None

        # Login background caches
        self._login_bg_src = None
        self._login_bg_imgtk = None

        self._init_styles()

        # Shared Main Layout (Left Hover Dock, Right main content frame)
        self.main_layout = ttk.Frame(self)
        self.main_layout.pack(fill="both", expand=True)
        self.main_layout.columnconfigure(0, weight=0) # Left: Hover Dock
        self.main_layout.columnconfigure(1, weight=1) # Right: Content area
        self.main_layout.rowconfigure(0, weight=1)

        # Hover Dock (vertical icon bar) - Permanent on the left side of the app
        self.hover_dock = tk.Frame(self.main_layout, bg="#0F1218", width=55, highlightthickness=0)
        self.hover_dock.grid(row=0, column=0, sticky="ns")
        self.hover_dock.grid_propagate(False)

        # Icons inside Hover Dock
        self.dock_settings = tk.Label(self.hover_dock, text="⚙", font=("Segoe UI", 16), bg="#0F1218", fg="#A9B0BC", cursor="hand2")
        self.dock_lan = tk.Label(self.hover_dock, text="🛜", font=("Segoe UI", 16), bg="#0F1218", fg="#A9B0BC", cursor="hand2")
        self.dock_stats = tk.Label(self.hover_dock, text="📊", font=("Segoe UI", 16), bg="#0F1218", fg="#A9B0BC", cursor="hand2")
        self.dock_credits = tk.Label(self.hover_dock, text="ℹ", font=("Segoe UI", 16), bg="#0F1218", fg="#A9B0BC", cursor="hand2")
        self.dock_exit = tk.Label(self.hover_dock, text="🚪", font=("Segoe UI", 16), bg="#0F1218", fg="#A9B0BC", cursor="hand2")

        self.dock_settings.pack(side="top", pady=(20, 15))
        self.dock_lan.pack(side="top", pady=15)
        self.dock_stats.pack(side="top", pady=15)
        self.dock_credits.pack(side="top", pady=15)
        self.dock_exit.pack(side="bottom", pady=20)

        # Interactive Hover effects
        for widget in (self.dock_settings, self.dock_lan, self.dock_stats, self.dock_credits, self.dock_exit):
            def make_on_enter(w):
                return lambda e: w.configure(fg="#4C8DFF")
            def make_on_leave(w):
                return lambda e: w.configure(fg="#A9B0BC")
            widget.bind("<Enter>", make_on_enter(widget))
            widget.bind("<Leave>", make_on_leave(widget))

        # Dock actions
        self.dock_settings.bind("<Button-1>", lambda e: self.open_settings_dialog())
        self.dock_credits.bind("<Button-1>", lambda e: self.show_credits())
        self.dock_exit.bind("<Button-1>", lambda e: self._on_dock_exit_click())

        # Tooltips
        HoverTooltip(self.dock_lan, self.get_lan_tooltip_text)
        HoverTooltip(self.dock_stats, self.get_stats_tooltip_text)
        HoverTooltip(self.dock_exit, self.get_dock_exit_tooltip_text)

        # Main Content Frame (swaps login screen and game screen)
        self.container = ttk.Frame(self.main_layout)
        self.container.grid(row=0, column=1, sticky="nsew")

        self._build_login_screen()
        self._build_game_screen()
        self._show_login()

        self.after(60, self._poll_lan_events)
        self.after(60, self._poll_ai_events)

    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.COL_BG = "#0F1115"
        self.COL_CARD = "#171A21"
        self.COL_TEXT = "#E7EAF0"
        self.COL_MUTED = "#A9B0BC"
        self.COL_ACCENT = "#4C8DFF"
        self.COL_DANGER = "#D95C5C"

        style.configure("TFrame", background=self.COL_BG)
        style.configure("Card.TFrame", background=self.COL_CARD)
        style.configure("TLabel", background=self.COL_BG, foreground=self.COL_TEXT, font=("Segoe UI", 11))
        style.configure("Muted.TLabel", background=self.COL_BG, foreground=self.COL_MUTED, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.COL_BG, foreground=self.COL_TEXT, font=("Segoe UI", 18, "bold"))

        style.configure("TEntry", fieldbackground="#11141A", foreground=self.COL_TEXT, insertcolor=self.COL_TEXT, borderwidth=0, relief="flat")
        style.configure("TCombobox", fieldbackground="#11141A", foreground=self.COL_TEXT, borderwidth=0, relief="flat")

        style.configure("Accent.TButton", background=self.COL_ACCENT, foreground="#FFFFFF",
                        font=("Segoe UI", 11, "bold"), padding=10, borderwidth=0, relief="flat")
        style.map("Accent.TButton", background=[("active", "#3B7DFF")])

        style.configure("Danger.TButton", background=self.COL_DANGER, foreground="#FFFFFF",
                        font=("Segoe UI", 11, "bold"), padding=10, borderwidth=0, relief="flat")
        style.map("Danger.TButton", background=[("active", "#C84C4C")])

        style.configure("Ghost.TButton", background="#222631", foreground=self.COL_TEXT,
                        font=("Segoe UI", 11), padding=10, borderwidth=0, relief="flat")
        style.map("Ghost.TButton", background=[("active", "#2A3040")])

        style.configure("Card.TLabelframe", background=self.COL_CARD, foreground=self.COL_TEXT, borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=self.COL_CARD, foreground=self.COL_TEXT,
                        font=("Segoe UI", 11, "bold"))

        # IMPORTANT: Use the default TScale style to avoid layout errors on some Tk builds
        style.configure("TScale", background=self.COL_CARD)

    def get_sprite_image(self, piece: chess.Piece, square_px: int):
        key = piece_asset_key(piece)
        cache_key = (key, square_px)
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        path = os.path.join(self.sprite_dir, f"{key}.png")
        if not os.path.exists(path):
            self.sprite_cache[cache_key] = None
            return None

        try:
            target = int(square_px * 0.82)
            if PIL_AVAILABLE:
                pil_img = Image.open(path)
                pil_img = pil_img.resize((target, target), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(pil_img)
            else:
                img = tk.PhotoImage(file=path)
                w0 = img.width()
                if w0 > 0 and w0 > target:
                    factor = max(1, w0 // target)
                    img = img.subsample(factor, factor)
            self.sprite_cache[cache_key] = img
            return img
        except Exception:
            self.sprite_cache[cache_key] = None
            return None

    # -------------------- Login BG --------------------
    def _load_login_bg(self):
        if not PIL_AVAILABLE:
            return
        if not os.path.exists(self.start_bg_path):
            return
        try:
            self._login_bg_src = Image.open(self.start_bg_path).convert("RGB")
        except Exception:
            self._login_bg_src = None

    def _draw_login_bg(self):
        """
        Fixes your crash:
        ValueError: height and width must be > 0

        Root cause:
        - During initial layout, canvas width/height can be 1 (or 0 in some cases),
          leading to computed resize sizes <= 0.
        """
        if not PIL_AVAILABLE or self._login_bg_src is None:
            return
        if not hasattr(self, "login_bg_canvas"):
            return

        cw = max(1, int(self.login_bg_canvas.winfo_width()))
        ch = max(1, int(self.login_bg_canvas.winfo_height()))
        if cw <= 1 or ch <= 1:
            return  # wait for a real size

        src = self._login_bg_src
        sw, sh = src.size

        # Cover fill (like CSS background-size: cover)
        scale = max(cw / sw, ch / sh)
        nw = max(1, int(sw * scale))
        nh = max(1, int(sh * scale))

        resized = src.resize((nw, nh), Image.LANCZOS)
        x0 = (nw - cw) // 2
        y0 = (nh - ch) // 2
        cropped = resized.crop((x0, y0, x0 + cw, y0 + ch))

        self._login_bg_imgtk = ImageTk.PhotoImage(cropped)
        self.login_bg_canvas.delete("all")
        self.login_bg_canvas.create_image(0, 0, anchor="nw", image=self._login_bg_imgtk)

    # -------------------- Login Screen --------------------
    def _build_login_screen(self):
        self.login_screen = ttk.Frame(self.container)
        self.login_screen.pack(fill="both", expand=True)

        # Background layer: a Canvas behind everything
        self.login_bg_canvas = tk.Canvas(self.login_screen, highlightthickness=0, bd=0)
        self.login_bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._load_login_bg()
        self.login_bg_canvas.bind("<Configure>", lambda _e: self._draw_login_bg())

        # Foreground layer
        wrap = ttk.Frame(self.login_screen)
        wrap.place(relx=0.5, rely=0.5, anchor="center")
        wrap.columnconfigure((0, 1), weight=1)

        # Top Header: Logo centered with 'Smart Chess' title right below
        header_frame = ttk.Frame(wrap)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="", pady=(0, 20))

        logo_path = resource_path("src", "resources", "app_logo", "logo.png")
        if os.path.exists(logo_path) and PIL_AVAILABLE:
            try:
                pil_logo = Image.open(logo_path)
                pil_logo = pil_logo.resize((80, 80), Image.Resampling.LANCZOS)
                self.login_logo_imgtk = ImageTk.PhotoImage(pil_logo)
                
                logo_lbl = tk.Label(header_frame, image=self.login_logo_imgtk, bg="#0F1115", bd=0, highlightthickness=0)
                logo_lbl.pack(pady=(0, 6))
            except Exception:
                pass

        ttk.Label(header_frame, text="Smart Chess", font=("Segoe UI", 22, "bold"), foreground="#E7EAF0").pack()

        # Left Column: Game Setup
        left_side = ttk.Frame(wrap)
        left_side.grid(row=1, column=0, padx=(0, 20), sticky="nsew")
        left_side.columnconfigure(0, weight=1)

        ttk.Label(left_side, text="Game Setup", style="Title.TLabel", anchor="center", justify="center").grid(row=0, column=0, sticky="ew", pady=(0, 12))

        card = ttk.Frame(left_side, style="Card.TFrame", padding=18)
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)

        self.mode_var = tk.StringVar(value="Select Game Mode...")
        self.white_name_var = tk.StringVar(value="White")
        self.black_name_var = tk.StringVar(value="Black")
        self.lan_ip_var = tk.StringVar(value="")

        self.time_control_var = tk.StringVar(value="5+0 min (Bullet)")

        ttk.Label(card, text="Game Mode").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.mode_combo = ttk.Combobox(
            card,
            textvariable=self.mode_var,
            values=[
                "Local 1v1",
                "Player vs Computer (You=White)",
                "Player vs Computer (You=Black)",
                "Tactical Puzzle Trainer",
                "LAN Host (Server Only - 2 Remote PCs)",
                "LAN Host (Host Plays White - 1 Remote PC)",
                "LAN Join",
            ],
            state="readonly",
            width=52,
        )
        self.mode_combo.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _e: self._sync_login_fields())

        ttk.Label(card, text="White Player").grid(row=2, column=0, sticky="w")
        self.white_entry = ttk.Entry(card, textvariable=self.white_name_var)
        self.white_entry.grid(row=3, column=0, sticky="ew", pady=(6, 10))

        ttk.Label(card, text="Black Player").grid(row=4, column=0, sticky="w")
        self.black_entry = ttk.Entry(card, textvariable=self.black_name_var)
        self.black_entry.grid(row=5, column=0, sticky="ew", pady=(6, 16))

        self.lan_ip_lbl = ttk.Label(card, text="LAN Host IP (Join only)")
        self.lan_ip_lbl.grid(row=6, column=0, sticky="w")
        self.lan_ip_entry = ttk.Entry(card, textvariable=self.lan_ip_var)
        self.lan_ip_entry.grid(row=7, column=0, sticky="ew", pady=(6, 8))

        # Dynamic local IP info label
        self.lan_ip_info_lbl = ttk.Label(card, text="", style="Muted.TLabel")
        self.lan_ip_info_lbl.grid(row=8, column=0, sticky="w", pady=(0, 16))

        tc_box = ttk.LabelFrame(card, text="Time Controls", style="Card.TLabelframe", padding=12)
        tc_box.grid(row=9, column=0, sticky="ew", pady=(0, 12))
        tc_box.columnconfigure(1, weight=1)

        ttk.Label(tc_box, text="Clock Preset").grid(row=0, column=0, sticky="w")
        self.time_combo = ttk.Combobox(
            tc_box,
            textvariable=self.time_control_var,
            values=["5+0 min (Bullet)", "3+2 min (Blitz)", "10+5 min (Rapid)", "15+10 min (Classical)", "Custom Time Control..."],
            state="readonly",
            width=24
        )
        self.time_combo.grid(row=0, column=1, sticky="e")
        self.time_combo.bind("<<ComboboxSelected>>", self._on_time_control_selected)

        ai_box = ttk.LabelFrame(card, text="AI Settings (Offline)", style="Card.TLabelframe", padding=12)
        ai_box.grid(row=10, column=0, sticky="ew", pady=(0, 16))
        ai_box.columnconfigure(1, weight=1)

        ttk.Label(ai_box, text="Difficulty Level").grid(row=0, column=0, sticky="w")
        self.difficulty_combo = ttk.Combobox(
            ai_box,
            textvariable=self.difficulty_var,
            values=["Easy", "Medium", "Hard"],
            state="readonly",
            width=24
        )
        self.difficulty_combo.grid(row=0, column=1, sticky="e")

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.grid(row=11, column=0, sticky="ew")
        btn_row.columnconfigure((0, 1), weight=1)

        ttk.Button(btn_row, text="Enter Game", style="Accent.TButton", command=self._login_submit).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="Credits", style="Ghost.TButton", command=self.show_credits).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Label(left_side, text="F11 toggles fullscreen. Escape exits fullscreen.", style="Muted.TLabel").grid(row=2, column=0, sticky="", pady=(12, 0))

        # Right Column: Recent Matches
        right_side = ttk.Frame(wrap)
        right_side.grid(row=1, column=1, padx=(20, 0), sticky="nsew")
        right_side.columnconfigure(0, weight=1)
        right_side.rowconfigure(1, weight=1)

        ttk.Label(right_side, text="Recent Match History", style="Title.TLabel", anchor="center", justify="center").grid(row=0, column=0, sticky="ew", pady=(0, 12))

        right_card = ttk.Frame(right_side, style="Card.TFrame", padding=18)
        right_card.grid(row=1, column=0, sticky="nsew")
        right_card.columnconfigure(0, weight=1)
        right_card.rowconfigure(0, weight=1)

        # Style Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", background="#1E2330", foreground="#E7EAF0", fieldbackground="#1E2330", rowheight=26, font=("Segoe UI", 10))
        style.configure("Custom.Treeview.Heading", background="#11141A", foreground="#A9B0BC", font=("Segoe UI", 10, "bold"))
        style.map("Custom.Treeview", background=[("selected", "#4C8DFF")], foreground=[("selected", "#FFFFFF")])

        cols = ("date", "white", "black", "result", "moves")
        self.login_tree = ttk.Treeview(right_card, columns=cols, show="headings", style="Custom.Treeview", height=15)
        self.login_tree.grid(row=0, column=0, sticky="nsew")

        headers = {"date": "Date", "white": "White Player", "black": "Black Player", "result": "Result", "moves": "Moves"}
        for c in cols:
            self.login_tree.heading(c, text=headers[c])
            self.login_tree.column(c, width=70 if c in ("result", "moves") else (90 if c == "date" else 120), anchor="center" if c in ("result", "moves", "date") else "w")

        # Modern Scroll Control Buttons (replacing old scrollbar)
        scroll_panel = ttk.Frame(right_card, style="Card.TFrame")
        scroll_panel.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        scroll_panel.rowconfigure((0, 1), weight=1)

        btn_up = ttk.Button(scroll_panel, text="▲", width=3, style="Ghost.TButton", command=self.scroll_login_tree_up)
        btn_up.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        
        btn_down = ttk.Button(scroll_panel, text="▼", width=3, style="Ghost.TButton", command=self.scroll_login_tree_down)
        btn_down.grid(row=1, column=0, sticky="nsew", pady=(3, 0))

        # Recent History Action Buttons (@author: Taha Siddiqui)
        hist_btns = ttk.Frame(right_card, style="Card.TFrame")
        hist_btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        hist_btns.columnconfigure((0, 1), weight=1)

        ttk.Button(hist_btns, text="🗑️ Delete Selected", style="Ghost.TButton", command=self.delete_selected_login_game).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(hist_btns, text="🧹 Clear All", style="Ghost.TButton", command=self.clear_all_login_games).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self._refresh_login_history()
        self._sync_login_fields()
        self.after(50, self._draw_login_bg)

    def _on_time_control_selected(self, _e=None):
        if self.time_control_var.get() == "Custom Time Control...":
            def save_cb(mins, inc):
                custom_str = f"{mins}+{inc} min (Custom)"
                self.time_control_var.set(custom_str)
            CustomTimeDialog(self, save_cb)

    def _sync_login_fields(self):
        m = self.mode_var.get()
        self.white_entry.configure(state="normal")
        self.black_entry.configure(state="normal")
        
        # Hide LAN widgets by default so non-LAN modes stay clean and have no vertical/horizontal black box
        if hasattr(self, "lan_ip_lbl"):
            self.lan_ip_lbl.grid_remove()
        self.lan_ip_entry.grid_remove()
        self.lan_ip_entry.configure(state="disabled")
        self.lan_ip_info_lbl.grid_remove()
        self.lan_ip_info_lbl.config(text="")

        if m == "Select Game Mode...":
            return

        if m == "Local 1v1":
            return
        if "You=White" in m:
            self.black_name_var.set("Computer")
            self.black_entry.configure(state="disabled")
            return
        if "You=Black" in m:
            self.white_name_var.set("Computer")
            self.white_entry.configure(state="disabled")
            return
        if m == "Tactical Puzzle Trainer":
            self.white_name_var.set("Solver")
            self.black_name_var.set("Puzzle AI")
            self.white_entry.configure(state="disabled")
            self.black_entry.configure(state="disabled")
            return
        if m == "LAN Host (Server Only - 2 Remote PCs)":
            self.white_name_var.set("Remote-White")
            self.black_name_var.set("Remote-Black")
            self.white_entry.configure(state="disabled")
            self.black_entry.configure(state="disabled")
            ip = self.lan.get_host_ip()
            self.lan_ip_info_lbl.grid(row=8, column=0, sticky="w", pady=(0, 16))
            self.lan_ip_info_lbl.config(text=f"Your Local IP: {ip} (Provide this to other players)")
            return
        if m == "LAN Host (Host Plays White - 1 Remote PC)":
            self.black_name_var.set("Remote")
            self.black_entry.configure(state="disabled")
            ip = self.lan.get_host_ip()
            self.lan_ip_info_lbl.grid(row=8, column=0, sticky="w", pady=(0, 16))
            self.lan_ip_info_lbl.config(text=f"Your Local IP: {ip} (Provide this to the other player)")
            return
        if m == "LAN Join":
            if hasattr(self, "lan_ip_lbl"):
                self.lan_ip_lbl.grid(row=6, column=0, sticky="w")
            self.lan_ip_entry.grid(row=7, column=0, sticky="ew", pady=(6, 8))
            self.lan_ip_entry.configure(state="normal")
            self.lan_ip_info_lbl.grid(row=8, column=0, sticky="w", pady=(0, 16))
            self.lan_ip_info_lbl.config(text="Enter the Host's local IP address above to connect.")

    def _login_submit(self):
        self.lan.stop()
        self.state_obj.lan_enabled = False
        self.state_obj.lan_role = None
        self.state_obj.lan_started = False
        self.state_obj.ai_side = None
        self.state_obj.premove = None

        self.board_ui.clear_premove_visual()

        m = self.mode_var.get().strip()
        diff = self.difficulty_var.get().strip()

        if m == "Select Game Mode...":
            self.sounds.play("illegal")
            self.show_error("Validation Warning", "Please select a Game Mode before entering.")
            return

        if "Player vs Computer" in m:
            if diff == "Select Difficulty...":
                self.sounds.play("illegal")
                self.show_error("Validation Warning", "Please select an AI Difficulty level before entering.")
                return

        tc_val = getattr(self, "time_control_var", tk.StringVar(value="5+0 min (Bullet)")).get()
        mins = 5
        inc = 0
        try:
            if "+" in tc_val:
                parts = tc_val.split(" ")[0].split("+")
                mins = int(parts[0])
                inc = int(parts[1])
        except Exception:
            pass
        self.state_obj.initial_time = mins * 60
        self.state_obj.increment_seconds = inc
        self.state_obj.time_control_label = tc_val
        self.state_obj.white_time_left = self.state_obj.initial_time
        self.state_obj.black_time_left = self.state_obj.initial_time

        self.state_obj.mode = m
        self.state_obj.white_name = (self.white_name_var.get().strip() or "White")
        self.state_obj.black_name = (self.black_name_var.get().strip() or "Black")

        if m == "Player vs Computer (You=White)":
            self.state_obj.black_name = "Computer"
            self.state_obj.ai_side = chess.BLACK

        if m == "Player vs Computer (You=Black)":
            self.state_obj.white_name = "Computer"
            self.state_obj.ai_side = chess.WHITE

        if m == "Tactical Puzzle Trainer":
            self.db.ensure_puzzles_seed()
            puzzle = self.db.fetch_random_puzzle()
            if not puzzle:
                self.sounds.play("illegal")
                self.show_error("Puzzle Trainer", "Could not load puzzle.")
                return
            pid, title, fen, moves_str, theme, diff_lvl = puzzle
            self.state_obj.puzzle_id = pid
            self.state_obj.puzzle_title = title
            self.state_obj.puzzle_solution = [mv.strip() for mv in moves_str.split(" ") if mv.strip()]
            self.state_obj.puzzle_step = 0
            board = chess.Board(fen)
            self.state_obj.reset_board(board)
            self.state_obj.white_name = "Solver"
            self.state_obj.black_name = "Puzzle AI"
            self._show_game()
            self.sidebar.set_status(f"🎯 Puzzle: {title} ({theme}) - Your Turn!")
            return

        if m == "LAN Host (Server Only - 2 Remote PCs)":
            self.state_obj.lan_enabled = True
            self.state_obj.lan_role = None
            board = self.lan.start_host_server_only()
            self.state_obj.reset_board(board)
            ip = self.lan.get_host_ip()
            self.show_info("LAN Host", f"Server-only host.\nHost IP: {ip}\nPort: 5000\nTwo players join using Host IP.")
            self.sounds.play("notify")

        if m == "LAN Host (Host Plays White - 1 Remote PC)":
            self.state_obj.lan_enabled = True
            self.state_obj.lan_role = chess.WHITE
            board = self.lan.start_host_plays_white()
            self.state_obj.reset_board(board)
            ip = self.lan.get_host_ip()
            self.show_info("LAN Host", f"Host plays White.\nHost IP: {ip}\nPort: 5000\nOne player joins using Host IP.")
            self.sounds.play("notify")

        if m == "LAN Join":
            ip = self.lan_ip_var.get().strip()
            if not ip:
                self.sounds.play("illegal")
                self.show_error("LAN Join", "Please enter Host IP.")
                return
            self.state_obj.lan_enabled = True
            try:
                self.lan.start_join(ip)
            except Exception as e:
                self.sounds.play("illegal")
                self.state_obj.lan_enabled = False
                self.show_error("LAN Connection Error", f"Could not connect to {ip}.\n\nDetails: {str(e)}")
                return
            self.state_obj.reset_board(self.state_obj.board)
            self.sounds.play("notify")

        if not self.state_obj.lan_enabled:
            self.state_obj.reset_board()

        self._show_game()

    # -------------------- Game Screen --------------------
    def _build_game_screen(self):
        self.game_screen = ttk.Frame(self.container)
        self.game_screen.columnconfigure(0, weight=3)
        self.game_screen.columnconfigure(1, weight=2)
        self.game_screen.rowconfigure(0, weight=1)

        left_card = ttk.Frame(self.game_screen, style="Card.TFrame", padding=14)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(0, weight=1)

        self.board_ui = ChessBoardUI(
            left_card,
            on_move_attempt=self._on_user_move_attempt,
            get_sprite_image_callback=self.get_sprite_image,
            is_game_running_callback=lambda: self.state_obj.running,
        )
        self.board_ui.grid(row=0, column=0, sticky="nsew")
        self.board_ui.set_board(self.state_obj.board)

        # Sidebar creation
        self.sidebar = UISidebar(
            self.game_screen,
            callbacks={
                "COL_CARD": self.COL_CARD,
                "COL_TEXT": self.COL_TEXT,
                "COL_MUTED": self.COL_MUTED,
                "on_start": self.toggle_pause,
                "on_reset": self.reset_game,
                "on_draw": self.offer_draw,
                "on_resign": self.resign,
                "on_leaderboard": self.show_leaderboard,
                "on_exit": self.on_exit_click,
                "on_export_pgn": self.export_game_pgn,
                "on_hint": self.request_hint,
                "on_send_chat": lambda txt: self.lan.send_chat("Host" if self.state_obj.lan_role is None else ("White" if self.state_obj.lan_role == chess.WHITE else "Black"), txt) if self.state_obj.lan_enabled else self.sidebar.append_chat_message("Player", txt),
                "on_send_emote": lambda em: (self.lan.send_emote("Host" if self.state_obj.lan_role is None else ("White" if self.state_obj.lan_role == chess.WHITE else "Black"), em) if self.state_obj.lan_enabled else None, self.board_ui.show_floating_emote(em, duration_ms=2500)),
            },
        )
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(7, 14), pady=14)

    def _show_login(self):
        self.game_screen.pack_forget()
        self.login_screen.pack(fill="both", expand=True)
        self.after(50, self._draw_login_bg)

    def _show_game(self):
        self.login_screen.pack_forget()
        self.game_screen.pack(fill="both", expand=True)
        self.sidebar.set_lan_chat_visible(True)
        self.board_ui.set_board(self.state_obj.board)
        self._apply_spectator_ui_rules()
        self._refresh_all_ui()

    def _back_to_login(self):
        self.sounds.play("notify")
        msg = "A game is currently running. Are you sure you want to logout and return to setup?" if self.state_obj.running else "Are you sure you want to logout and return to the setup screen?"
        if not self.ask_yes_no("Confirm Logout", msg, yes_text="Logout", no_text="Cancel", is_danger=True):
            return
        self.reset_game()
        self._show_login()
        self._refresh_login_history()

    def _on_dock_exit_click(self):
        if self.login_screen.winfo_viewable():
            self.on_exit_click()
        else:
            self._back_to_login()

    def get_dock_exit_tooltip_text(self) -> str:
        if self.login_screen.winfo_viewable():
            return "🚪 Exit Application"
        return "🚪 Logout / Return to Login"

    def change_board_theme(self, theme_name: str):
        self.board_ui.set_theme(theme_name)

    def show_info(self, title: str, message: str):
        CustomMessageBox(self, title, message, box_type="info")

    def show_error(self, title: str, message: str):
        CustomMessageBox(self, title, message, box_type="error")

    def ask_yes_no(self, title: str, message: str, yes_text="Yes", no_text="No", is_danger=False) -> bool:
        box = CustomMessageBox(self, title, message, box_type="yesno", yes_text=yes_text, no_text=no_text, is_danger=is_danger)
        return bool(box.result)

    def open_settings_dialog(self):
        self.sounds.play("notify")
        def save_callback(new_settings):
            theme = new_settings["theme"]
            self.board_ui.set_theme(theme)
            
            enabled = new_settings["sound_enabled"]
            self.sound_enabled_var.set(enabled)
            self.sounds.set_enabled(enabled)
            
            volume = new_settings["sound_volume"]
            self.sound_volume_var.set(volume)
            self.sounds.set_volume(volume)
            
            self.difficulty_var.set(new_settings["difficulty"])
            self.sounds.play("notify")

        SettingsDialog(
            self,
            current_theme=self.board_ui.theme_name,
            sound_enabled=self.sound_enabled_var.get(),
            sound_volume=self.sound_volume_var.get(),
            current_difficulty=self.difficulty_var.get(),
            on_save=save_callback
        )

    def show_credits(self):
        self.sounds.play("notify")
        CreditsDialog(self)

    def on_exit_click(self):
        self.sounds.play("notify")
        if self.ask_yes_no("Confirm Exit", "Are you sure you want to exit Smart Chess?", yes_text="Exit", no_text="Cancel", is_danger=True):
            self.destroy()

    def _refresh_login_history(self):
        if not hasattr(self, "login_tree"):
            return
        for item in self.login_tree.get_children():
            self.login_tree.delete(item)
        try:
            for row in self.db.fetch_recent_games_with_id(limit=15):
                game_id, game_date, wp, bp, result, total_moves, mode = row
                short_date = game_date.split(" ")[0] if " " in game_date else game_date
                self.login_tree.insert("", tk.END, iid=str(game_id), values=(short_date, wp, bp, result, total_moves))
        except Exception:
            pass

    def delete_selected_login_game(self):
        selected = self.login_tree.selection()
        if not selected:
            self.sounds.play("illegal")
            self.show_error("Delete Match", "Please select a match from the history table first.")
            return
        game_id = int(selected[0])
        self.sounds.play("notify")
        if self.ask_yes_no("Confirm Delete", "Are you sure you want to delete the selected match from history?", yes_text="Delete", no_text="Cancel", is_danger=True):
            self.db.delete_game_by_id(game_id)
            self._refresh_login_history()
            self.sounds.play("notify")

    def clear_all_login_games(self):
        self.sounds.play("notify")
        if self.ask_yes_no("Confirm Clear All", "Are you sure you want to permanently delete all match history?", yes_text="Clear All", no_text="Cancel", is_danger=True):
            self.db.clear_all_games()
            self._refresh_login_history()
            self.sounds.play("notify")

    def scroll_login_tree_up(self):
        self.login_tree.yview_scroll(-1, "units")

    def scroll_login_tree_down(self):
        self.login_tree.yview_scroll(1, "units")

    def get_lan_tooltip_text(self) -> str:
        ip = self.lan.get_host_ip() if self.state_obj.lan_enabled else "-"
        role_text = "-"
        if self.state_obj.lan_role == chess.WHITE:
            role_text = "WHITE"
        elif self.state_obj.lan_role == chess.BLACK:
            role_text = "BLACK"
        elif self.state_obj.lan_enabled:
            role_text = "SPECTATOR"
        connected = f"{self.lan.connected_count}/2" if self.state_obj.lan_enabled else "0/2"
        return (
            f"🌐 LAN Status Info\n"
            f"──────────────────\n"
            f"Host IP : {ip}\n"
            f"Players : {connected}\n"
            f"Role    : {role_text}"
        )

    def get_stats_tooltip_text(self) -> str:
        white_txt = self._captured_counter_text(self.state_obj.captured_by_white, victim_is_white=False)
        black_txt = self._captured_counter_text(self.state_obj.captured_by_black, victim_is_white=True)
        board = self.state_obj.board
        score = 0
        for pt, val in PIECE_VALUES.items():
            score += len(board.pieces(pt, chess.WHITE)) * val
            score -= len(board.pieces(pt, chess.BLACK)) * val
        if score > 0:
            mat_txt = f"White +{score}"
        elif score < 0:
            mat_txt = f"Black +{abs(score)}"
        else:
            mat_txt = "Even"
        return (
            f"📊 Match Statistics\n"
            f"──────────────────\n"
            f"Captured by White:\n{white_txt if white_txt else 'None'}\n\n"
            f"Captured by Black:\n{black_txt if black_txt else 'None'}\n\n"
            f"Material Score  : {mat_txt}"
        )

    def toggle_pause(self):
        if not self.state_obj.running and not self.state_obj.paused:
            self.start_game()
            return
        if self.state_obj.paused:
            self.state_obj.paused = False
            self.state_obj.running = True
            self.sounds.play("game-start")
            self._start_timer_loop()
            self._refresh_all_ui()
            self._maybe_start_ai_turn()
        else:
            self.state_obj.paused = True
            self.state_obj.running = False
            self.sounds.play("notify")
            self._stop_timer_loop()
            self._refresh_all_ui()

    def export_game_pgn(self):
        import datetime
        import chess.pgn

        game = chess.pgn.Game()
        game.headers["Event"] = "LAN Game" if self.state_obj.lan_enabled else "Offline Chess Game"
        game.headers["Site"] = "Localhost"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = "1"
        game.headers["White"] = self.state_obj.white_name
        game.headers["Black"] = self.state_obj.black_name
        
        outcome = self.state_obj.board.outcome()
        if outcome:
            result = outcome.result()
        elif not self.state_obj.running and len(self.state_obj.san_moves) > 0:
            result = "1/2-1/2"  # standard fallback for draws/resigns if ended
        else:
            result = "*"
        game.headers["Result"] = result

        node = game
        temp_board = chess.Board()
        for san in self.state_obj.san_moves:
            try:
                move = temp_board.parse_san(san)
                node = node.add_main_line(move)
                temp_board.push(move)
            except Exception:
                pass

        filename = f"chess_game_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
        filepath = get_data_path("pgn", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(str(game))
            self.show_info("Export Successful", f"Game exported successfully to:\n{filepath}")
            self.sounds.play("notify")
        except Exception as e:
            self.show_error("Export Failed", f"Failed to export PGN: {e}")
            self.sounds.play("illegal")

    def _apply_spectator_ui_rules(self):
        ip = self.lan.get_host_ip() if self.state_obj.lan_enabled else "-"
        role_text = "-"
        if self.state_obj.lan_role == chess.WHITE:
            role_text = "WHITE"
        elif self.state_obj.lan_role == chess.BLACK:
            role_text = "BLACK"
        elif self.state_obj.lan_enabled:
            role_text = "SPECTATOR"

        connected = f"{self.lan.connected_count}/2" if self.state_obj.lan_enabled else "0/2"
        self.sidebar.set_lan_info(ip, connected, role_text)

        if self.state_obj.lan_enabled and self.state_obj.lan_role is None:
            self.sidebar.set_buttons_enabled(start=False, reset=True, draw=False, resign=False)
            self.sidebar.set_mode_note("Server-only spectator. Two remote players can join and play.")
        else:
            self.sidebar.set_buttons_enabled(start=True, reset=True, draw=True, resign=True)
            if self.state_obj.lan_enabled:
                self.sidebar.set_mode_note("LAN mode. Server validates all moves.")
            elif self.state_obj.ai_side is not None:
                note = "Offline vs AI. "
                note += "Stockfish enabled." if self.engine.has_stockfish() else "Minimax enabled (Stockfish not detected)."
                self.sidebar.set_mode_note(note)
            else:
                self.sidebar.set_mode_note("Offline local play.")

    # -------------------- Game Actions --------------------
    def start_game(self):
        if self.state_obj.running:
            return
        if self.state_obj.lan_enabled and self.state_obj.lan_role is None:
            self.sounds.play("illegal")
            self.sidebar.set_status("Spectator cannot start. Waiting for 2 LAN players.")
            return
        self.state_obj.running = True
        self.state_obj.result_recorded = False
        self.sounds.play("game-start")
        self._start_timer_loop()
        self._refresh_all_ui()
        self._maybe_start_ai_turn()

    def reset_game(self):
        self._stop_timer_loop()
        self.state_obj.premove = None
        self.board_ui.clear_premove_visual()

        if getattr(self.lan, "server", None):
            self.lan.server.board.reset()
            self.state_obj.reset_board(self.lan.server.board)
            self.lan.server.broadcast("LASTMOVE none")
            self.lan.server.broadcast(f"FEN {self.lan.server.board.fen()}")
        else:
            self.state_obj.reset_board()

        self.board_ui.set_board(self.state_obj.board)
        self.board_ui.set_last_move(None)
        self.sidebar.history_list.delete(0, tk.END)

        self._apply_spectator_ui_rules()
        self._refresh_all_ui()

    def offer_draw(self):
        if not self.state_obj.running or (self.state_obj.lan_enabled and self.state_obj.lan_role is None):
            self.sounds.play("illegal")
            return
        self.sounds.play("notify")

        if self.state_obj.lan_enabled:
            if not self.ask_yes_no("Draw Offer", "Offer a draw to the opponent?"):
                return
            role = "WHITE" if self.state_obj.lan_role == chess.WHITE else "BLACK"
            if self.lan.server:
                self.lan.broadcast_draw_offer(role)
            else:
                self.lan.send_draw_offer()
            self.sidebar.set_status("Draw offer sent. Waiting for opponent...")
            return

        if self.ask_yes_no("Draw", "Accept a draw?"):
            self.state_obj.running = False
            self._stop_timer_loop()
            self._record_result("1/2-1/2")
            self.sounds.play("game-end")
            self._refresh_all_ui()
            self.after(500, lambda: self.show_game_over_popup("Draw Agreement"))

    def resign(self):
        if not self.state_obj.running or (self.state_obj.lan_enabled and self.state_obj.lan_role is None):
            self.sounds.play("illegal")
            return
        self.sounds.play("notify")
        if not self.ask_yes_no("Confirm Resignation", "Are you sure you want to resign the match?", yes_text="Resign", no_text="Cancel", is_danger=True):
            return

        if self.state_obj.lan_enabled:
            role = "WHITE" if self.state_obj.lan_role == chess.WHITE else "BLACK"
            if self.lan.server:
                self.lan.broadcast_resign(role)
            else:
                self.lan.send_resign()
            return

        self.state_obj.running = False
        self._stop_timer_loop()
        raw = "0-1" if self.state_obj.board.turn == chess.WHITE else "1-0"
        resigner = "White" if self.state_obj.board.turn == chess.WHITE else "Black"
        self._record_result(raw)
        self.sounds.play("game-end")
        self._refresh_all_ui()
        self.after(500, lambda: self.show_game_over_popup(f"{resigner} Resigned"))

    # -------------------- Moves --------------------
    def _on_user_move_attempt(self, from_sq: int, to_sq: int):
        if not self.state_obj.running:
            self.sounds.play("illegal")
            return

        if getattr(self.state_obj, "mode", "") == "Tactical Puzzle Trainer":
            move = chess.Move(from_sq, to_sq)
            if self._is_promotion_move(from_sq, to_sq):
                promo = self._promotion_dialog()
                if promo is None:
                    self.sounds.play("illegal")
                    return
                move = chess.Move(from_sq, to_sq, promotion=promo)
            
            if move not in self.state_obj.board.legal_moves:
                self.sounds.play("illegal")
                return

            solution = getattr(self.state_obj, "puzzle_solution", [])
            step = getattr(self.state_obj, "puzzle_step", 0)
            if step < len(solution) and move.uci() == solution[step]:
                self.sounds.play("move-self")
                san = self.state_obj.board.san(move)
                self.state_obj.board.push(move)
                self._append_san(san)
                self.board_ui.set_last_move(move)
                self.state_obj.puzzle_step = step + 1
                if self.state_obj.puzzle_step >= len(solution):
                    self.state_obj.running = False
                    self.sounds.play("game-end")
                    self.sidebar.set_status("🎯 Puzzle Solved Successfully!")
                    self._refresh_all_ui()
                    self.show_info("Puzzle Solved", f"Congratulations! You solved:\n{getattr(self.state_obj, 'puzzle_title', 'Tactical Puzzle')}")
                else:
                    ai_reply_uci = solution[self.state_obj.puzzle_step]
                    ai_move = chess.Move.from_uci(ai_reply_uci)
                    san_ai = self.state_obj.board.san(ai_move)
                    self.state_obj.board.push(ai_move)
                    self._append_san(san_ai)
                    self.state_obj.puzzle_step += 1
                    self.board_ui.set_last_move(ai_move)
                    self.sounds.play("move-opponent")
                    if self.state_obj.puzzle_step >= len(solution):
                        self.state_obj.running = False
                        self.sounds.play("game-end")
                        self.sidebar.set_status("🎯 Puzzle Solved Successfully!")
                        self._refresh_all_ui()
                        self.show_info("Puzzle Solved", f"Congratulations! You solved:\n{getattr(self.state_obj, 'puzzle_title', 'Tactical Puzzle')}")
                    else:
                        self.sidebar.set_status("🎯 Correct! Your turn...")
                        self._refresh_all_ui()
            else:
                self.sounds.play("illegal")
                self.sidebar.set_status("❌ Incorrect move! Try again.")
            return

        if self.state_obj.lan_enabled and self.state_obj.lan_role is None:
            self.sounds.play("illegal")
            return

        # LAN player role constraint
        if self.state_obj.lan_enabled and self.state_obj.lan_role is not None:
            if self.state_obj.board.turn != self.state_obj.lan_role:
                self.sounds.play("illegal")
                self.sidebar.set_status("Not your turn.")
                return
            move = chess.Move(from_sq, to_sq)
            if self._is_promotion_move(from_sq, to_sq):
                promo = self._promotion_dialog()
                if promo is None:
                    self.sounds.play("illegal")
                    return
                self.sounds.play("promote")
                move = chess.Move(from_sq, to_sq, promotion=promo)
            self.sounds.play("move-self")
            self.lan.send_move(move.uci())
            return

        # Offline AI pre-move support
        if self.state_obj.ai_side is not None:
            user_color = chess.BLACK if self.state_obj.ai_side == chess.WHITE else chess.WHITE

            if self.ai.thinking:
                p = self.state_obj.board.piece_at(from_sq)
                if not p or p.color != user_color:
                    self.sounds.play("illegal")
                    return

                promo_val = None
                if self._is_promotion_move(from_sq, to_sq):
                    promo_val = self._promotion_dialog()
                    if promo_val is None:
                        self.sounds.play("illegal")
                        return
                    self.sounds.play("promote")

                self.state_obj.premove = (from_sq, to_sq, promo_val)
                self.board_ui.set_premove_visual(from_sq, to_sq)
                self.sounds.play("pre-move")
                self.sidebar.set_status("Premove queued.")
                return

            if self.state_obj.board.turn == self.state_obj.ai_side:
                self.sounds.play("illegal")
                return

        self._apply_offline_move(from_sq, to_sq, is_opponent=False)
        self._maybe_start_ai_turn()

    def _apply_offline_move(self, from_sq: int, to_sq: int, is_opponent: bool, preset_promo=None):
        board = self.state_obj.board

        if preset_promo is not None:
            candidate = chess.Move(from_sq, to_sq, promotion=preset_promo)
        elif self._is_promotion_move(from_sq, to_sq):
            if is_opponent:
                candidate = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
            else:
                promo = self._promotion_dialog()
                if promo is None:
                    self.sounds.play("illegal")
                    return
                self.sounds.play("promote")
                candidate = chess.Move(from_sq, to_sq, promotion=promo)
        else:
            candidate = chess.Move(from_sq, to_sq)

        if candidate not in board.legal_moves:
            self.sounds.play("illegal")
            return

        moving_piece = board.piece_at(from_sq)
        mover_color = board.turn
        is_capture = board.is_capture(candidate)
        is_castle = board.is_castling(candidate)
        captured_piece = self._get_captured_piece_pre_push(board, candidate)

        san = board.san(candidate)
        board.push(candidate)
        self.sidebar.apply_turn_increment(self.state_obj, mover_color)

        if captured_piece:
            self._record_capture_counter(mover_color, captured_piece)

        self._append_san(san)
        self.board_ui.set_last_move(candidate)

        self.sounds.play("move-opponent" if is_opponent else "move-self")
        if is_castle:
            self.sounds.play("castle")
        if is_capture:
            self.sounds.play("capture")
        if board.is_check():
            self.sounds.play("move-check")

        def done():
            self._finish_game_if_over()
            self._refresh_all_ui()

        if moving_piece:
            self.board_ui.animate_move(candidate, moving_piece, on_done=done)
        else:
            done()

    def _append_san(self, san: str):
        self.state_obj.san_moves.append(san)
        self.sidebar.history_list.insert(tk.END, f"{len(self.state_obj.san_moves)}. {san}")
        self.sidebar.history_list.yview_moveto(1.0)

    def _get_ai_parameters(self):
        diff = self.difficulty_var.get()
        if diff == "Easy":
            return 1, 0.05, 0
        elif diff == "Hard":
            return 3, 0.35, 20
        else: # Medium
            return 2, 0.15, 10

    def _maybe_start_ai_turn(self):
        if self.state_obj.lan_enabled or not self.state_obj.running or self.state_obj.ai_side is None:
            return
        if self.state_obj.board.is_game_over() or self.state_obj.board.turn != self.state_obj.ai_side:
            return
        if self.ai.thinking:
            return

        depth, sf_time, sf_skill = self._get_ai_parameters()
        self.state_obj.ai_thinking = True
        self.sidebar.set_status("Computer thinking...")
        self.ai.start_think(self.state_obj.board.fen(), minimax_depth=depth, stockfish_time=sf_time, stockfish_skill=sf_skill)

    def _try_execute_premove(self):
        if self.state_obj.premove is None or self.state_obj.ai_side is None:
            return
        board = self.state_obj.board
        user_color = chess.BLACK if self.state_obj.ai_side == chess.WHITE else chess.WHITE
        if board.turn != user_color:
            return

        from_sq, to_sq, promo = self.state_obj.premove
        mv = chess.Move(from_sq, to_sq) if promo is None else chess.Move(from_sq, to_sq, promotion=promo)

        self.state_obj.premove = None
        self.board_ui.clear_premove_visual()

        if mv not in board.legal_moves:
            self.sounds.play("notify")
            self.sidebar.set_status("Premove invalid after AI move.")
            return

        self.sounds.play("pre-move")
        self._apply_offline_move(mv.from_square, mv.to_square, is_opponent=False, preset_promo=promo)
        self._maybe_start_ai_turn()

    def _poll_ai_events(self):
        try:
            while True:
                ev, payload = self.ai.events.get_nowait()
                if ev == "AI_MOVE":
                    mv = chess.Move.from_uci(payload)
                    if mv in self.state_obj.board.legal_moves:
                        self.state_obj.ai_thinking = False
                        self._apply_offline_move(mv.from_square, mv.to_square, is_opponent=True, preset_promo=mv.promotion)
                        self._try_execute_premove()
                    else:
                        self.state_obj.ai_thinking = False
                        self.sounds.play("illegal")
                        self.sidebar.set_status("AI produced an illegal move (unexpected).")

                if ev == "AI_ERROR":
                    self.state_obj.ai_thinking = False
                    self.sounds.play("notify")
                    self.sidebar.set_status(f"AI error: {payload}")

                if ev == "AI_ANALYSIS":
                    self.last_analysis_payload = payload
                    self.sounds.play("notify")
        except queue.Empty:
            pass

        self.after(60, self._poll_ai_events)

    # -------------------- LAN Poll --------------------
    def _poll_lan_events(self):
        self.lan.poll()
        self.state_obj.lan_connected_count = self.lan.connected_count
        if self.state_obj.lan_enabled:
            self._apply_spectator_ui_rules()

        try:
            while True:
                ev, payload = self.lan.events.get_nowait()

                if ev == "LAN_ROLE":
                    if payload == "WHITE":
                        self.state_obj.lan_role = chess.WHITE
                    elif payload == "BLACK":
                        self.state_obj.lan_role = chess.BLACK
                    else:
                        self.state_obj.lan_role = None
                    self.sounds.play("notify")
                    self._apply_spectator_ui_rules()
                    self._refresh_all_ui()

                if ev == "LAN_START":
                    self.state_obj.lan_started = True
                    if not self.state_obj.running and self.state_obj.lan_role is not None:
                        self.start_game()

                if ev == "LAN_FEN":
                    try:
                        self.state_obj.board.set_fen(payload)
                        self.board_ui.set_board(self.state_obj.board)
                        self._finish_game_if_over()
                        self._refresh_all_ui()
                    except Exception:
                        pass

                if ev == "LAN_LASTMOVE":
                    if payload != "none":
                        try:
                            mv = chess.Move.from_uci(payload)
                            self.board_ui.set_last_move(mv)
                            
                            # Sync move history and captures
                            board = self.state_obj.board
                            if mv in board.legal_moves:
                                mover_color = board.turn
                                captured_piece = self._get_captured_piece_pre_push(board, mv)
                                if captured_piece:
                                    self._record_capture_counter(mover_color, captured_piece)
                                san = board.san(mv)
                                board.push(mv)
                                self.sidebar.apply_turn_increment(self.state_obj, mover_color)
                                self._append_san(san)
                        except Exception:
                            pass

                if ev == "LAN_END":
                    self.sounds.play("game-end")
                    self.state_obj.running = False
                    self._stop_timer_loop()
                    self._record_result(payload)
                    self._refresh_all_ui()

                if ev == "LAN_DRAWOFFER":
                    offering_role = payload
                    my_role_str = "WHITE" if self.state_obj.lan_role == chess.WHITE else "BLACK"
                    if offering_role != my_role_str:
                        self.sounds.play("notify")
                        if self.ask_yes_no("Draw Offer", f"Opponent ({offering_role}) has offered a draw. Accept?"):
                            if self.lan.server:
                                self.lan.broadcast_draw_accept()
                            else:
                                self.lan.send_draw_response(accept=True)
                        else:
                            if self.lan.server:
                                self.lan.broadcast_draw_decline(my_role_str)
                            else:
                                self.lan.send_draw_response(accept=False)

                if ev == "LAN_DRAWDECLINE":
                    declining_role = payload
                    my_role_str = "WHITE" if self.state_obj.lan_role == chess.WHITE else "BLACK"
                    if declining_role != my_role_str:
                        self.sounds.play("illegal")
                        self.show_info("Draw Offer", f"Opponent ({declining_role}) declined the draw offer.")
                        self._refresh_status_ui()

                if ev == "LAN_ERROR":
                    self.sounds.play("illegal")
                    self.sidebar.set_status(str(payload))

                if ev == "LAN_INFO":
                    self.sidebar.set_status(str(payload))

                if ev == "LAN_CHAT":
                    if isinstance(payload, tuple) and len(payload) == 2:
                        sender, text = payload
                    elif isinstance(payload, str):
                        if ": " in payload:
                            sender, text = payload.split(": ", 1)
                        else:
                            sender, text = "LAN", payload
                    else:
                        sender, text = "LAN", str(payload)
                    self.sidebar.append_chat_message(sender, text)
                    self.sounds.play("notify")

                if ev == "LAN_EMOTE":
                    if isinstance(payload, tuple) and len(payload) == 2:
                        sender, emoji = payload
                    elif isinstance(payload, str):
                        if "|" in payload:
                            sender, emoji = payload.split("|", 1)
                        else:
                            sender, emoji = "LAN", payload
                    else:
                        sender, emoji = "LAN", str(payload)
                    self.board_ui.show_floating_emote(emoji, duration_ms=2500)
                    self.sounds.play("notify")
        except queue.Empty:
            pass

        self.after(60, self._poll_lan_events)

    # -------------------- Captures + UI Refresh --------------------
    def _get_captured_piece_pre_push(self, board: chess.Board, move: chess.Move):
        if not board.is_capture(move):
            return None
        if board.is_en_passant(move):
            direction = -8 if board.turn == chess.WHITE else 8
            cap_sq = move.to_square + direction
            return board.piece_at(cap_sq)
        return board.piece_at(move.to_square)

    def _record_capture_counter(self, mover_color: bool, captured_piece: chess.Piece):
        letter = {
            chess.PAWN: "P",
            chess.KNIGHT: "N",
            chess.BISHOP: "B",
            chess.ROOK: "R",
            chess.QUEEN: "Q",
            chess.KING: "K",
        }[captured_piece.piece_type]
        if letter == "K":
            return
        if mover_color == chess.WHITE:
            self.state_obj.captured_by_white[letter] += 1
        else:
            self.state_obj.captured_by_black[letter] += 1

    def _refresh_all_ui(self):
        self.board_ui.redraw()
        self._refresh_material_ui()
        self._refresh_captured_ui()
        self._refresh_timers_ui()
        self._refresh_status_ui()

        # Update Start/Pause button text and style dynamically
        if self.state_obj.running:
            self.sidebar.btn_start.config(text="Pause", style="Danger.TButton")
        elif self.state_obj.paused:
            self.sidebar.btn_start.config(text="Resume", style="Accent.TButton")
        else:
            self.sidebar.btn_start.config(text="Start", style="Accent.TButton")

    def _refresh_status_ui(self):
        board = self.state_obj.board
        turn = "White" if board.turn == chess.WHITE else "Black"
        check = " (Check)" if board.is_check() else ""
        if self.state_obj.ai_side is not None and self.ai.thinking:
            self.sidebar.set_status("Computer thinking...")
        else:
            self.sidebar.set_status(f"{turn} to move{check}.")

    def _refresh_material_ui(self):
        board = self.state_obj.board
        score = 0
        for pt, val in PIECE_VALUES.items():
            score += len(board.pieces(pt, chess.WHITE)) * val
            score -= len(board.pieces(pt, chess.BLACK)) * val

        if score > 0:
            self.sidebar.set_material(f"White +{score}")
        elif score < 0:
            self.sidebar.set_material(f"Black +{abs(score)}")
        else:
            self.sidebar.set_material("Even")

    def _captured_counter_text(self, captured_dict, victim_is_white: bool):
        glyphs = {
            ("Q", True): "♕",
            ("R", True): "♖",
            ("B", True): "♗",
            ("N", True): "♘",
            ("P", True): "♙",
            ("Q", False): "♛",
            ("R", False): "♜",
            ("B", False): "♝",
            ("N", False): "♞",
            ("P", False): "♟",
        }
        parts = []
        for letter in ["Q", "R", "B", "N", "P"]:
            n = captured_dict.get(letter, 0)
            if n > 0:
                parts.append(f"{glyphs[(letter, victim_is_white)]}x{n}")
        return "  ".join(parts)

    def _refresh_captured_ui(self):
        white_txt = self._captured_counter_text(self.state_obj.captured_by_white, victim_is_white=False)
        black_txt = self._captured_counter_text(self.state_obj.captured_by_black, victim_is_white=True)
        self.sidebar.set_captured(white_txt if white_txt else "None", black_txt if black_txt else "None")

    def _refresh_timers_ui(self):
        active_color = None
        if self.state_obj.running:
            active_color = "white" if self.state_obj.board.turn == chess.WHITE else "black"
        self.sidebar.set_timers(
            self._fmt_time(self.state_obj.white_time_left),
            self._fmt_time(self.state_obj.black_time_left),
            active_color
        )

    @staticmethod
    def _fmt_time(seconds: int) -> str:
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    # -------------------- Promotion --------------------
    def _is_promotion_move(self, from_sq: int, to_sq: int) -> bool:
        board = self.state_obj.board
        piece = board.piece_at(from_sq)
        if not piece or piece.piece_type != chess.PAWN:
            return False
        to_rank = chess.square_rank(to_sq)
        return (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0)

    def _promotion_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Pawn Promotion")
        dialog.configure(bg="#171A21")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center on parent window
        self.update_idletasks()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        pw = self.winfo_width()
        ph = self.winfo_height()
        w, h = 460, 230
        dialog.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(dialog, style="Card.TFrame", padding=18)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        promo_color = self.state_obj.board.turn

        # Header Title
        ttk.Label(content, text="👑 Promote Your Pawn", font=("Segoe UI", 13, "bold"), background="#171A21", foreground="#E7EAF0").grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        ttk.Label(content, text="Click any piece card below to transform your pawn immediately:", font=("Segoe UI", 9), background="#171A21", foreground="#A9B0BC").grid(
            row=1, column=0, sticky="w", pady=(0, 14)
        )

        opts = [
            ("Queen", chess.QUEEN, "Q"),
            ("Rook", chess.ROOK, "R"),
            ("Bishop", chess.BISHOP, "B"),
            ("Knight", chess.KNIGHT, "N"),
        ]

        dialog._promo_imgs = []
        grid = ttk.Frame(content, style="Card.TFrame")
        grid.grid(row=2, column=0, sticky="ew")
        grid.columnconfigure((0, 1, 2, 3), weight=1)

        selected = {"value": None}

        def pick(val):
            selected["value"] = val
            dialog.destroy()

        def cancel():
            selected["value"] = None
            dialog.destroy()

        for i, (name, val, letter) in enumerate(opts):
            color_prefix = "w" if promo_color == chess.WHITE else "b"
            filename = f"{color_prefix}{letter}.png"
            path = os.path.join(self.sprite_dir, filename)

            img = None
            if os.path.exists(path):
                try:
                    img = tk.PhotoImage(file=path)
                    if img.width() > 56:
                        factor = max(1, img.width() // 56)
                        img = img.subsample(factor, factor)
                except Exception:
                    img = None

            dialog._promo_imgs.append(img)

            # Interactive Card Frame
            card = tk.Frame(grid, bg="#1E2330", highlightthickness=1, highlightbackground="#2A3040", bd=0, cursor="hand2")
            card.grid(row=0, column=i, padx=6, sticky="nsew", ipady=8)

            lbl_img = tk.Label(card, image=img if img else "", bg="#1E2330", cursor="hand2")
            lbl_img.pack(pady=(4, 2))

            lbl_txt = tk.Label(card, text=name, font=("Segoe UI", 10, "bold"), fg="#E7EAF0", bg="#1E2330", cursor="hand2")
            lbl_txt.pack(pady=(0, 4))

            # Hover glow events
            def on_enter(e, c=card, li=lbl_img, lt=lbl_txt):
                c.config(bg="#2A3040", highlightbackground="#4C8DFF")
                li.config(bg="#2A3040")
                lt.config(bg="#2A3040", fg="#4C8DFF")

            def on_leave(e, c=card, li=lbl_img, lt=lbl_txt):
                c.config(bg="#1E2330", highlightbackground="#2A3040")
                li.config(bg="#1E2330")
                lt.config(bg="#1E2330", fg="#E7EAF0")

            def on_click(e, v=val):
                pick(v)

            for w_el in (card, lbl_img, lbl_txt):
                w_el.bind("<Enter>", on_enter)
                w_el.bind("<Leave>", on_leave)
                w_el.bind("<Button-1>", on_click)

        # Footer Cancel
        footer = ttk.Frame(content, style="Card.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Button(footer, text="Cancel / Keep Pawn", style="Ghost.TButton", command=cancel).grid(row=0, column=0, sticky="ew")

        self.wait_window(dialog)
        return selected["value"]

    # -------------------- Timer --------------------
    def _start_timer_loop(self):
        self._stop_timer_loop()
        self._tick_timer()

    def _stop_timer_loop(self):
        if self._timer_job is not None:
            try:
                self.after_cancel(self._timer_job)
            except Exception:
                pass
        self._timer_job = None

    def _tick_timer(self):
        if not self.state_obj.running or self.state_obj.board.is_game_over():
            self._timer_job = None
            return

        board = self.state_obj.board
        if board.turn == chess.WHITE:
            self.state_obj.white_time_left = max(0, self.state_obj.white_time_left - 1)
            if self.state_obj.white_time_left == 10 and not self.state_obj.ten_sec_white_played:
                self.state_obj.ten_sec_white_played = True
                self.sounds.play("ten-seconds")
            elif self.state_obj.white_time_left == 0:
                self.state_obj.running = False
                self._stop_timer_loop()
                self._record_result("0-1")
                self.sounds.play("game-end")
                self._refresh_all_ui()
                self.after(500, lambda: self.show_game_over_popup("White Timeout"))
                return
        else:
            self.state_obj.black_time_left = max(0, self.state_obj.black_time_left - 1)
            if self.state_obj.black_time_left == 10 and not self.state_obj.ten_sec_black_played:
                self.state_obj.ten_sec_black_played = True
                self.sounds.play("ten-seconds")
            elif self.state_obj.black_time_left == 0:
                self.state_obj.running = False
                self._stop_timer_loop()
                self._record_result("1-0")
                self.sounds.play("game-end")
                self._refresh_all_ui()
                self.after(500, lambda: self.show_game_over_popup("Black Timeout"))
                return

        self._refresh_timers_ui()
        self._timer_job = self.after(1000, self._tick_timer)

    # -------------------- End-of-game and DB --------------------
    def _finish_game_if_over(self):
        board = self.state_obj.board
        if not board.is_game_over():
            return
        out = board.outcome()
        if not out:
            return
        self.state_obj.running = False
        self._stop_timer_loop()
        self._record_result(out.result())
        self.sounds.play("game-end")
        self.after(500, lambda: self.show_game_over_popup(out))

    def _record_result(self, raw_result: str):
        if self.state_obj.result_recorded:
            return
        self.state_obj.result_recorded = True
        self.db.record_game(
            self.state_obj.white_name,
            self.state_obj.black_name,
            raw_result,
            len(self.state_obj.san_moves),
            self.state_obj.mode,
            san_moves=" ".join(self.state_obj.san_moves)
        )
        self._refresh_login_history()

    def show_game_over_popup(self, outcome_or_reason):
        title = "Game Over"
        result_text = ""
        details_text = ""

        if isinstance(outcome_or_reason, chess.Outcome):
            res = outcome_or_reason.result()
            term = outcome_or_reason.termination
            if term == chess.Termination.CHECKMATE:
                winner = "White" if outcome_or_reason.winner == chess.WHITE else "Black"
                title = "🏆 Checkmate"
                result_text = f"{winner} Wins!"
                details_text = f"The game ended in a checkmate.\nWinner: {winner}"
            elif term == chess.Termination.STALEMATE:
                title = "🤝 Stalemate"
                result_text = "Draw by Stalemate"
                details_text = "Stalemate! Neither player can make any legal moves."
            elif term in (chess.Termination.THREEFOLD_REPETITION, chess.Termination.FIVEFOLD_REPETITION):
                title = "🤝 Repetition Draw"
                result_text = "Draw by Repetition"
                details_text = "The same board position occurred repeatedly."
            elif term == chess.Termination.INSUFFICIENT_MATERIAL:
                title = "🤝 Insufficient Material"
                result_text = "Draw by Insufficient Material"
                details_text = "Neither player has enough pieces to force a mate."
            else:
                title = "🤝 Draw"
                result_text = "Draw Game"
                details_text = "The game ended in a draw."
        else:
            reason = str(outcome_or_reason)
            if "Resigned" in reason:
                resigner = reason.split(" ")[0]
                winner = "Black" if resigner == "White" else "White"
                title = "🏳️ Resignation"
                result_text = f"{winner} Wins!"
                details_text = f"{resigner} resigned the game."
            elif "Timeout" in reason:
                timeout_player = reason.split(" ")[0]
                winner = "Black" if timeout_player == "White" else "White"
                title = "⏰ Time Forfeit"
                result_text = f"{winner} Wins!"
                details_text = f"{timeout_player} ran out of time."
            else:
                title = "🤝 Draw Agreement"
                result_text = "Draw Game"
                details_text = "Both players agreed to end the game in a draw."

        moves_count = len(self.state_obj.san_moves)
        details_text += f"\n\nTotal Moves Played: {moves_count}"

        self.sounds.play("game-end")
        self.ai.start_analysis(list(self.state_obj.san_moves))
        GameOverDialog(
            self,
            title=title,
            result_text=result_text,
            details_text=details_text,
            on_rematch=self.reset_game,
            on_close=self._back_to_login,
            on_analysis=self.open_post_match_analysis,
            on_replay=lambda: self.open_replay_viewer(list(self.state_obj.san_moves), self.state_obj.white_name, self.state_obj.black_name)
        )

    def open_post_match_analysis(self):
        if hasattr(self, "last_analysis_payload") and self.last_analysis_payload:
            PostMatchAnalysisModal(self, self.last_analysis_payload)
        else:
            self.show_info("Analyzing", "AI is currently evaluating match history in the background.\nPlease wait a moment and click Analysis again.")

    def open_replay_viewer(self, san_moves: list, white_name: str, black_name: str):
        if not san_moves:
            self.show_info("Replay Viewer", "No move history available for this match.")
            return
        ReplayViewerModal(self, san_moves=san_moves, white_name=white_name, black_name=black_name, get_sprite_callback=self.get_sprite_image)

    def request_hint(self):
        if not self.state_obj.running or self.state_obj.paused:
            self.sounds.play("illegal")
            return
        if self.state_obj.ai_thinking:
            return
        
        self.sidebar.set_status("Analyzing best move...")
        
        import threading
        def worker():
            try:
                fen = self.state_obj.board.fen()
                mv_uci = self.engine.stockfish_bestmove(fen, move_time=0.5, skill_level=20)
                if mv_uci and mv_uci != "none":
                    move = chess.Move.from_uci(mv_uci)
                    san = self.state_obj.board.san(move)
                    self.after(0, lambda: self.show_hint_suggestion(move, san))
                else:
                    self.after(0, lambda: self.sidebar.set_status("No suggestion available."))
            except Exception as e:
                self.after(0, lambda: self.sidebar.set_status("Engine offline."))
        
        threading.Thread(target=worker, daemon=True).start()

    def show_hint_suggestion(self, move, san):
        self.sounds.play("notify")
        self.board_ui.set_hint_move(move)
        self.sidebar.set_status(f"Hint: Play {san}")

    def show_leaderboard(self):
        self.sounds.play("notify")
        top = tk.Toplevel(self)
        top.title("Game History")
        top.geometry("920x520")
        top.configure(bg="#171A21")
        top.transient(self)
        top.grab_set()

        # Center on parent window
        self.update_idletasks()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        pw = self.winfo_width()
        ph = self.winfo_height()
        w, h = 920, 520
        top.geometry(f"{w}x{h}+{px + pw//2 - w//2}+{py + ph//2 - h//2}")

        content = ttk.Frame(top, style="Card.TFrame", padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        # Header Title
        ttk.Label(content, text="Recent Game History & Leaderboard", font=("Segoe UI", 16, "bold"), background="#171A21", foreground="#E7EAF0").grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Divider
        divider = tk.Frame(content, height=2, bg="#4C8DFF", bd=0)
        divider.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Treeview table
        cols = ("date", "white", "black", "result", "moves", "mode")
        tree = ttk.Treeview(content, columns=cols, show="headings", style="Custom.Treeview", height=15)
        tree.grid(row=2, column=0, sticky="nsew")

        headers = {"date": "Date Played", "white": "White Player", "black": "Black Player", "result": "Result", "moves": "Moves", "mode": "Game Mode"}
        for c in cols:
            tree.heading(c, text=headers[c])
            tree.column(c, width=150 if c in ("white", "black", "mode") else (100 if c == "date" else 80), anchor="center" if c in ("result", "moves", "date") else "w")

        # Scrollbar
        sb = ttk.Scrollbar(content, orient="vertical", command=tree.yview)
        sb.grid(row=2, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        # Populate (@author: Taha Siddiqui)
        try:
            for row in self.db.fetch_recent_games_with_id(limit=50):
                game_id, game_date, wp, bp, result, total_moves, mode = row
                tree.insert("", tk.END, iid=str(game_id), values=(game_date, wp, bp, result, total_moves, mode))
        except Exception:
            pass

        def delete_selected_popup():
            sel = tree.selection()
            if not sel:
                self.sounds.play("illegal")
                self.show_error("Delete Match", "Please select a match from the table to delete.")
                return
            game_id = int(sel[0])
            self.sounds.play("notify")
            if self.ask_yes_no("Confirm Delete", "Delete this match from history?", yes_text="Delete", no_text="Cancel", is_danger=True):
                self.db.delete_game_by_id(game_id)
                tree.delete(sel[0])
                self._refresh_login_history()
                self.sounds.play("notify")

        def clear_all_popup():
            self.sounds.play("notify")
            if self.ask_yes_no("Confirm Clear All", "Are you sure you want to clear all match history?", yes_text="Clear All", no_text="Cancel", is_danger=True):
                self.db.clear_all_games()
                for item in tree.get_children():
                    tree.delete(item)
                self._refresh_login_history()
        def export_selected_popup():
            sel = tree.selection()
            if not sel:
                self.sounds.play("illegal")
                self.show_error("Export PGN", "Please select a match to export.")
                return
            game_id = int(sel[0])
            self.sounds.play("notify")
            pgn_str = self.db.export_game_to_pgn(game_id)
            if not pgn_str or not pgn_str.strip():
                self.show_error("Export PGN", "No PGN data available for this match.")
                return
            try:
                out_dir = get_data_path("exports")
                os.makedirs(out_dir, exist_ok=True)
                fn = os.path.join(out_dir, f"game_{game_id}.pgn")
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(pgn_str)
                self.show_info("Export PGN", f"Match exported successfully to:\n{fn}")
            except Exception as e:
                self.show_error("Export PGN", f"Failed to save PGN: {e}")

        def replay_selected_popup():
            sel = tree.selection()
            if not sel:
                self.sounds.play("illegal")
                self.show_error("Replay Match", "Please select a match to replay.")
                return
            game_id = int(sel[0])
            self.sounds.play("notify")
            row = self.db.fetch_game_by_id(game_id)
            if not row:
                self.show_error("Replay Match", "Could not load match details.")
                return
            gid, gdate, wp, bp, res, tmoves, mode, san_str = row
            san_list = [m.strip() for m in (san_str or "").split(" ") if m.strip()]
            top.destroy()
            self.open_replay_viewer(san_list, wp, bp)

        # Action Buttons at the bottom
        btn_frame = ttk.Frame(content, style="Card.TFrame")
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        for c in range(5):
            btn_frame.columnconfigure(c, weight=1)
        ttk.Button(btn_frame, text="🗑️ Delete", style="Ghost.TButton", command=delete_selected_popup).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(btn_frame, text="🧹 Clear All", style="Ghost.TButton", command=clear_all_popup).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(btn_frame, text="📥 Export PGN", style="Accent.TButton", command=export_selected_popup).grid(row=0, column=2, sticky="ew", padx=2)
        ttk.Button(btn_frame, text="◀ Replay", style="Accent.TButton", command=replay_selected_popup).grid(row=0, column=3, sticky="ew", padx=2)
        ttk.Button(btn_frame, text="Close", style="Ghost.TButton", command=top.destroy).grid(row=0, column=4, sticky="ew", padx=2)

    # -------------------- Window --------------------
    def _toggle_fullscreen(self, _event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)

    def _exit_fullscreen(self, _event=None):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.attributes("-fullscreen", False)

    def _on_close(self):
        self._stop_timer_loop()
        self.lan.stop()
        self.ai.stop()
        self.engine.close()
        self.destroy()


if __name__ == "__main__":
    ChessApp().mainloop()
