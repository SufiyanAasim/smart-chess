# ==============================================================================
# Project: Smart Chess
# Module: Sidebar Controller (Match Clocks, Telemetry Graphs & Statistics Logs)
# Authors: Mohammad Sufiyan Aasim (@SufiyanAasim) - UI Layout, Timers & Notation Log
#          Taha Siddiqui (@13eeCoder) - Match Statistics & Database Action Triggers
# License: MIT License
# ==============================================================================
__authors__ = ["Mohammad Sufiyan Aasim", "Taha Siddiqui"]

import tkinter as tk
from tkinter import ttk


class UISidebar(ttk.Frame):
    """
    Sidebar UI Controller.
    
    Responsibility Division:
    - @author: Mohammad Sufiyan Aasim -> Cards, Clock Layouts, Dominance Bar Graph & SAN Log.
    - @author: Taha Siddiqui -> Match Statistics metrics, PGN Export & Database Action Triggers.
    """
    def __init__(self, master, callbacks: dict):
        super().__init__(master, style="Card.TFrame", padding=14)

        self.callbacks = callbacks
        self.COL_CARD = callbacks["COL_CARD"]
        self.COL_TEXT = callbacks["COL_TEXT"]
        self.COL_MUTED = callbacks["COL_MUTED"]

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)  # History list takes all extra space

        # Row 0: Title
        ttk.Label(self, text="Match Details", font=("Segoe UI", 14, "bold"),
                  background=self.COL_CARD, foreground=self.COL_TEXT).grid(row=0, column=0, sticky="w")

        # Row 1: Status Label
        self.status_label = ttk.Label(self, text="Ready", background=self.COL_CARD,
                                      foreground=self.COL_MUTED, wraplength=460)
        self.status_label.grid(row=1, column=0, sticky="ew", pady=(6, 12))

        # Row 2: Prominent Clocks
        timer_box = ttk.LabelFrame(self, text="Clocks", style="Card.TLabelframe", padding=10)
        timer_box.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        timer_box.columnconfigure((0, 1), weight=1)

        # White Clock Card
        self.white_clock_frame = tk.Frame(timer_box, bg="#1E2330", highlightthickness=1, highlightbackground="#2A3040", bd=0)
        self.white_clock_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        
        self.white_clock_lbl = ttk.Label(self.white_clock_frame, text="WHITE", font=("Segoe UI", 9, "bold"), foreground=self.COL_MUTED, background="#1E2330")
        self.white_clock_lbl.pack(pady=(6, 2))
        self.white_timer_label = tk.Label(self.white_clock_frame, text="05:00", font=("Consolas", 22, "bold"), fg="#E7EAF0", bg="#1E2330")
        self.white_timer_label.pack(pady=(0, 6))

        # Black Clock Card
        self.black_clock_frame = tk.Frame(timer_box, bg="#1E2330", highlightthickness=1, highlightbackground="#2A3040", bd=0)
        self.black_clock_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")

        self.black_clock_lbl = ttk.Label(self.black_clock_frame, text="BLACK", font=("Segoe UI", 9, "bold"), foreground=self.COL_MUTED, background="#1E2330")
        self.black_clock_lbl.pack(pady=(6, 2))
        self.black_timer_label = tk.Label(self.black_clock_frame, text="05:00", font=("Consolas", 22, "bold"), fg="#E7EAF0", bg="#1E2330")
        self.black_timer_label.pack(pady=(0, 6))

        # Row 3: Live Stats Box (Captured Pieces & Material Balance)
        self.stats_box = ttk.LabelFrame(self, text="Captured Pieces & Balance", style="Card.TLabelframe", padding=10)
        self.stats_box.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self.stats_box.columnconfigure((0, 1), weight=1)

        # White Captured (Black Pieces)
        self.white_captured_lbl = ttk.Label(self.stats_box, text="Captured by White:", font=("Segoe UI", 8, "bold"), background=self.COL_CARD, foreground=self.COL_MUTED)
        self.white_captured_lbl.grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        self.white_captured_val = ttk.Label(self.stats_box, text="None", font=("Segoe UI", 10), background=self.COL_CARD, foreground=self.COL_TEXT)
        self.white_captured_val.grid(row=1, column=0, sticky="w", pady=(0, 8))

        # Black Captured (White Pieces)
        self.black_captured_lbl = ttk.Label(self.stats_box, text="Captured by Black:", font=("Segoe UI", 8, "bold"), background=self.COL_CARD, foreground=self.COL_MUTED)
        self.black_captured_lbl.grid(row=0, column=1, sticky="w", pady=(0, 2))

        self.black_captured_val = ttk.Label(self.stats_box, text="None", font=("Segoe UI", 10), background=self.COL_CARD, foreground=self.COL_TEXT)
        self.black_captured_val.grid(row=1, column=1, sticky="w", pady=(0, 8))

        # Material Balance
        self.material_lbl = ttk.Label(self.stats_box, text="Material Balance:", font=("Segoe UI", 8, "bold"), background=self.COL_CARD, foreground=self.COL_MUTED)
        self.material_lbl.grid(row=2, column=0, sticky="w", pady=(2, 0))

        self.material_val = ttk.Label(self.stats_box, text="Even", font=("Segoe UI", 9, "bold"), background=self.COL_CARD, foreground="#4C8DFF")
        self.material_val.grid(row=2, column=1, sticky="e", pady=(2, 0))

        # Live Score Display
        self.score_lbl = ttk.Label(self.stats_box, text="Live Score: Even (50% vs 50%)", font=("Segoe UI", 9, "bold"), background=self.COL_CARD, foreground="#E7EAF0")
        self.score_lbl.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 4))

        # Visual Dominance & Evaluation Bar Graph
        self.graph_canvas = tk.Canvas(self.stats_box, height=18, bg="#11141A", highlightthickness=1, highlightbackground="#2A3040", bd=0)
        self.graph_canvas.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.graph_canvas.bind("<Configure>", lambda _e: self._draw_stats_graph())

        # Hint Button in stats_box
        self.btn_hint = ttk.Button(self.stats_box, text="💡 Get Move Hint", style="Ghost.TButton", command=callbacks["on_hint"])
        self.btn_hint.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        # Row 4: Action Buttons
        btns = ttk.Frame(self, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_start = ttk.Button(btns, text="Start", style="Accent.TButton", command=callbacks["on_start"])
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_reset = ttk.Button(btns, text="Reset", style="Ghost.TButton", command=callbacks["on_reset"])
        self.btn_reset.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self.btn_draw = ttk.Button(btns, text="Draw", style="Ghost.TButton", command=callbacks["on_draw"])
        self.btn_draw.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        self.btn_resign = ttk.Button(btns, text="Resign", style="Danger.TButton", command=callbacks["on_resign"])
        self.btn_resign.grid(row=0, column=3, sticky="ew")

        # Row 5: Move History (Takes all extra space!)
        hist = ttk.LabelFrame(self, text="Move History (SAN)", style="Card.TLabelframe", padding=12)
        hist.grid(row=5, column=0, sticky="nsew", pady=(0, 12))
        hist.columnconfigure(0, weight=1)
        hist.rowconfigure(0, weight=1)

        self.history_list = tk.Listbox(
            hist, bg="#11141A", fg=self.COL_TEXT, bd=0, highlightthickness=0,
            font=("Consolas", 11), activestyle="none"
        )
        self.history_list.grid(row=0, column=0, sticky="nsew")

        # Modern Scroll Control Buttons (replacing old scrollbar)
        scroll_panel = ttk.Frame(hist, style="Card.TFrame")
        scroll_panel.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        scroll_panel.rowconfigure((0, 1), weight=1)

        btn_up = ttk.Button(scroll_panel, text="▲", width=3, style="Ghost.TButton", command=self.scroll_up)
        btn_up.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        
        btn_down = ttk.Button(scroll_panel, text="▼", width=3, style="Ghost.TButton", command=self.scroll_down)
        btn_down.grid(row=1, column=0, sticky="nsew", pady=(3, 0))

        # Row 6: LAN Spectator Chat & Quick-Emotes Panel (@author: Taha Siddiqui)
        self.chat_panel = ttk.LabelFrame(self, text="LAN Chat & Quick-Emotes", style="Card.TLabelframe", padding=10)
        self.chat_panel.grid(row=6, column=0, sticky="nsew", pady=(0, 12))
        self.chat_panel.columnconfigure(0, weight=1)
        self.chat_panel.rowconfigure(1, weight=1)

        # Quick-Emotes Drawer
        emotes_frame = ttk.Frame(self.chat_panel, style="Card.TFrame")
        emotes_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        emotes_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        for idx, em in enumerate(["🏆", "⚡", "👏", "🔥", "🤔"]):
            btn_em = ttk.Button(emotes_frame, text=em, style="Ghost.TButton", width=3,
                                command=lambda e=em: callbacks.get("on_send_emote", lambda _x: None)(e))
            btn_em.grid(row=0, column=idx, sticky="ew", padx=1)

        # Chat display area
        self.chat_log = tk.Text(self.chat_panel, height=4, bg="#11141A", fg=self.COL_TEXT, bd=0, font=("Segoe UI", 9), state="disabled", wrap="word")
        self.chat_log.grid(row=1, column=0, sticky="nsew", pady=(0, 6))

        # Chat Entry & Send
        chat_inp_frame = ttk.Frame(self.chat_panel, style="Card.TFrame")
        chat_inp_frame.grid(row=2, column=0, sticky="ew")
        chat_inp_frame.columnconfigure(0, weight=1)
        self.chat_entry = ttk.Entry(chat_inp_frame, font=("Segoe UI", 9))
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.chat_entry.bind("<Return>", lambda _e: self._send_chat_click())
        ttk.Button(chat_inp_frame, text="Send", style="Accent.TButton", width=6, command=self._send_chat_click).grid(row=0, column=1)

        # Row 7: Footer Buttons
        footer = ttk.Frame(self, style="Card.TFrame")
        footer.grid(row=7, column=0, sticky="ew")
        footer.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(footer, text="Leaderboard", style="Ghost.TButton", command=callbacks["on_leaderboard"]).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.btn_export = ttk.Button(footer, text="Export PGN", style="Ghost.TButton", command=callbacks["on_export_pgn"])
        self.btn_export.grid(row=0, column=1, sticky="ew", padx=(4, 4))
        self.btn_exit = ttk.Button(footer, text="Exit Game", style="Danger.TButton", command=callbacks["on_exit"])
        self.btn_exit.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # Initially hide chat panel unless LAN is enabled
        self.chat_panel.grid_remove()

    def _send_chat_click(self):
        txt = self.chat_entry.get().strip()
        if txt:
            self.callbacks.get("on_send_chat", lambda _x: None)(txt)
            self.chat_entry.delete(0, tk.END)

    def set_lan_chat_visible(self, visible: bool):
        if visible:
            self.chat_panel.grid()
        else:
            self.chat_panel.grid_remove()

    def append_chat_message(self, sender: str, text: str):
        self.chat_log.configure(state="normal")
        self.chat_log.insert(tk.END, f"{sender}: {text}\n")
        self.chat_log.see(tk.END)
        self.chat_log.configure(state="disabled")

    def scroll_up(self):
        self.history_list.yview_scroll(-1, "units")

    def scroll_down(self):
        self.history_list.yview_scroll(1, "units")

    def set_status(self, text: str):
        self.status_label.config(text=text)

    def set_material(self, text: str):
        self.material_val.config(text=text)
        diff = 0
        if "White +" in text:
            self.material_val.config(foreground="#4C8DFF")
            try:
                diff = int(text.split("+")[-1].strip())
            except Exception:
                diff = 1
        elif "Black +" in text:
            self.material_val.config(foreground="#D95C5C")
            try:
                diff = -int(text.split("+")[-1].strip())
            except Exception:
                diff = -1
        else:
            self.material_val.config(foreground="#A9B0BC")
            diff = 0

        # Calculate dominance (clamped between 0.10 and 0.90 for visual appeal)
        perc = 0.5 + (diff * 0.05)
        perc = max(0.10, min(0.90, perc))
        self._dominance_perc = perc

        white_p = int(perc * 100)
        black_p = 100 - white_p
        if diff > 0:
            score_txt = f"Live Score: White +{diff} ({white_p}% Dominance)"
        elif diff < 0:
            score_txt = f"Live Score: Black +{abs(diff)} ({black_p}% Dominance)"
        else:
            score_txt = "Live Score: Even (50% vs 50%)"

        if hasattr(self, "score_lbl"):
            self.score_lbl.config(text=score_txt)
        self._draw_stats_graph()

    def _draw_stats_graph(self):
        if not hasattr(self, "graph_canvas"):
            return
        self.graph_canvas.delete("all")
        w = max(1, self.graph_canvas.winfo_width())
        h = max(1, self.graph_canvas.winfo_height())

        perc = getattr(self, "_dominance_perc", 0.5)
        split_x = int(w * perc)

        # Draw White Dominance bar (#4C8DFF) on left
        if split_x > 0:
            self.graph_canvas.create_rectangle(0, 0, split_x, h, fill="#4C8DFF", width=0)
        # Draw Black Dominance bar (#D95C5C) on right
        if split_x < w:
            self.graph_canvas.create_rectangle(split_x, 0, w, h, fill="#D95C5C", width=0)

        # Draw glowing center divider / notch
        self.graph_canvas.create_line(split_x, 0, split_x, h, fill="#FFFFFF", width=2)

        # Draw percentage labels inside bar if wide enough
        if w > 120:
            white_p = int(perc * 100)
            black_p = 100 - white_p
            if white_p >= 18 and split_x >= 30:
                self.graph_canvas.create_text(split_x // 2, h // 2, text=f"{white_p}%", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))
            if black_p >= 18 and (w - split_x) >= 30:
                self.graph_canvas.create_text(split_x + (w - split_x) // 2, h // 2, text=f"{black_p}%", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))

    def set_timers(self, white_txt: str, black_txt: str, active_color: str = None):
        self.white_timer_label.config(text=white_txt)
        self.black_timer_label.config(text=black_txt)

        # Reset highlights
        self.white_clock_frame.config(highlightbackground="#2A3040")
        self.black_clock_frame.config(highlightbackground="#2A3040")
        self.white_timer_label.config(fg="#E7EAF0")
        self.black_timer_label.config(fg="#E7EAF0")

        if active_color == "white":
            self.white_clock_frame.config(highlightbackground="#4C8DFF")
            self.white_timer_label.config(fg="#4C8DFF")
            self.black_timer_label.config(fg="#555B68")  # Dimmed
        elif active_color == "black":
            self.black_clock_frame.config(highlightbackground="#4C8DFF")
            self.black_timer_label.config(fg="#4C8DFF")
            self.white_timer_label.config(fg="#555B68")  # Dimmed

    def set_captured(self, by_white: str, by_black: str):
        self.white_captured_val.config(text=by_white)
        self.black_captured_val.config(text=by_black)

    def set_mode_note(self, text: str):
        pass

    def set_lan_info(self, host_ip: str, connected: str, role: str):
        pass

    def set_buttons_enabled(self, start: bool, reset: bool, draw: bool, resign: bool):
        self.btn_start.config(state=("normal" if start else "disabled"))
        self.btn_reset.config(state=("normal" if reset else "disabled"))
        self.btn_draw.config(state=("normal" if draw else "disabled"))
        self.btn_resign.config(state=("normal" if resign else "disabled"))

    def apply_turn_increment(self, state_obj, completed_turn):
        """
        Applies Fischer time increment to player upon move completion (@author: Taha Siddiqui).
        """
        import chess
        if state_obj.increment_seconds <= 0 or not state_obj.running or state_obj.paused:
            return
        if completed_turn == chess.WHITE:
            state_obj.white_time_left += state_obj.increment_seconds
        else:
            state_obj.black_time_left += state_obj.increment_seconds
