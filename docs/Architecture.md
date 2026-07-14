# System Architecture

## Overview
Smart Chess is a modular desktop application structured with a clean separation between state management, local database transactions, networking, sound rendering, and UI modules.

```
┌─────────────────────────────────────────────────────────┐
│                    Entry Point                          │
│                     main.py                             │
└──────────────────────────┬──────────────────────────────┘
                           │
             ┌─────────────▼─────────────┐
             │       Application         │
             │     src/chess_app.py      │
             └──────┬──────────────┬─────┘
                    │              │
      ┌─────────────▼─────┐  ┌─────▼─────────────┐
      │   ChessBoardUI    │  │    UISidebar      │
      │  src/ui_board.py  │  │ src/ui_sidebar.py │
      └───────────────────┘  └───────────────────┘
```

  src/lan_controller.py ──► UDP broadcast (port 5000) — LAN lobby discovery

## Key Components

### 1. `main.py`
The entrypoint bootstrap module that adds `src/` to python's import search path, constructs the main app class, and launches the Tkinter event loop.

### 2. `src/chess_app.py`
The orchestrator controller module containing the primary application lifecycle, setups (`_build_login_screen`), matches setups, dialog handlers, and window configuration states.

### 3. `src/ui_board.py`
The graphics rendering canvas class (`ChessBoardUI`) responsible for drawing checkered boards, rendering piece sprites, displaying selection borders, mapping clicks to chess coordinates, and drawing last move/hint overlays.

### 4. `src/ui_sidebar.py`
The match details sidebar controller (`UISidebar`) containing match clocks, statistics trackers (captured balance), action triggers (Draw, Resign), and the SAN move history log.

### 5. `src/chess_engine.py`
Interface wrapper for Stockfish binary interactions. Launches subprocesses asynchronously using stdin/stdout streams for skill adjustments and move generation.

### 6. `src/lan_controller.py`
Network controller running socket host servers, UDP broadcast signals (on port 5000) for network discoverability, and TCP connection loops.

### 7. `src/database_manager.py`
SQLite manager executing parameterized queries for registering game histories and stats inside `data/chess_games.db`. All historical records up to date (`11` matches) are consolidated in this database.

### 8. `src/sound_manager.py`
Synthesizes and renders move, capture, check, and countdown sound effects utilizing pygame's audio mixer thread.

### 9. `src/utils_paths.py`
Path resolution utility managing dual-mode execution across development and PyInstaller builds:
- **`resource_path(*parts)`**: Resolves read-only bundled assets from `src/resources/` (or temporary `_MEIPASS` when frozen).
- **`get_data_path(*parts)`**: Resolves persistent read/write user files (`data/chess_games.db` and PGN exports under `data/pgn/`) relative to the root (`data/`) or alongside the executable when frozen (`<exe_dir>/data/`).
