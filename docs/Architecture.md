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

```
src/lan_controller.py ──► UDP broadcast (port 5000) & TCP sync — LAN room discovery & chat
src/ai_controller.py  ──► Background thread eval queues — Stockfish analysis & blunder graph
src/database_manager.py ─► SQLite schema & PGN engine — match logs, puzzles & file exports
```

## Architectural Ownership & Division of Responsibilities
To ensure strict code clarity and balanced division across all subsystems, the application is divided according to domain responsibilities between the two maintainers:

| Component / Module | Primary Maintainer | Domain & Responsibilities |
| :--- | :--- | :--- |
| `src/chess_app.py` | **Mohammad Sufiyan Aasim** | Application orchestration, login/setup loop, window events, modal controllers (`ReplayViewerModal`, `PostMatchAnalysisModal`, `GameOverDialog`), checkmate verification, and event polling loops. |
| `src/ui_board.py` | **Mohammad Sufiyan Aasim** | Canvas board rendering, piece sprite caching, dynamic evaluation bar (`set_evaluation_bar`), floating emote overlays, coordinates tooltips, and micro-animations. |
| `src/ui_sidebar.py` | **Mohammad Sufiyan Aasim** & **Taha Siddiqui** | Sidebar layout, chat box, and match action buttons (`Sufiyan`); Fischer increment clock updates (`apply_turn_increment`) and preset time display (`Taha`). |
| `src/ai_controller.py` | **Mohammad Sufiyan Aasim** | Asynchronous Stockfish worker threads, centipawn evaluation curves, and move classifications (`🔥 Best Move`, `🤔 Inaccuracy`, `😧 Mistake`, `😱 Blunder`). |
| `src/chess_engine.py` | **Mohammad Sufiyan Aasim** | Stockfish engine subprocess lifecycle, skill parameter adjustments, and FEN evaluation queries. |
| `src/database_manager.py` | **Taha Siddiqui** | SQLite schema migrations, SAN move archiving (`san_moves`), `Tactical Puzzle Trainer` puzzle seeding/fetching, match deletion, and `.pgn` file exports. |
| `src/lan_controller.py` | **Taha Siddiqui** | Network protocols, UDP server discovery, TCP sockets, `LAN_CHAT` messaging, and `LAN_EMOTE` overlays. |
| `src/game_state.py` | **Mohammad Sufiyan Aasim** & **Taha Siddiqui** | Central state variables (`running`, `board`, `ai_side`) (`Sufiyan`); time control tracking (`initial_time`, `increment_seconds`) and puzzle state trackers (`Taha`). |
| `src/sound_manager.py` | **Taha Siddiqui** | Pygame mixer threading, audio volume controls, and sound effect playback for moves, captures, and checkmates (`@author: Taha Siddiqui`). |
| `src/utils_paths.py` | **Mohammad Sufiyan Aasim** & **Taha Siddiqui** | Path resolution utility (`resource_path` and `get_data_path`) managing persistent storage alongside bundled assets. |

## Key Subsystems (v5.0.0 Grandmaster)

### 1. Tactical Puzzle Trainer (`@author: Taha Siddiqui`)
Leverages an SQLite puzzle table seeded automatically inside `DatabaseManager.ensure_puzzles_seed()`. When a user enters `Tactical Puzzle Trainer` mode, the app loads an FEN puzzle and verifies moves against the stored solution sequence step-by-step, animating the opponent's replies.

### 2. Post-Match Analysis Bar & Blunder Graph (`@author: Mohammad Sufiyan Aasim`)
Executes asynchronously inside `AIController.start_analysis`. By processing all SAN moves recorded in `GameState.san_moves` in a background daemon thread, it calculates exact centipawn diffs and renders both a live evaluation bar on the board (`ChessBoardUI`) and a post-match breakdown modal (`PostMatchAnalysisModal`).

### 3. Custom Time Controls & Fischer Increment (`@author: Taha Siddiqui`)
Plugs directly into the game timer loop (`_tick_timer`) and move execution callbacks (`_apply_offline_move`, `LAN_LASTMOVE`). Every time a player completes a legal move, `apply_turn_increment` credits `increment_seconds` to their active clock. Presets include `5+0 Bullet`, `3+2 Blitz`, `10+5 Rapid`, and `15+10 Classical`.

### 4. Game Replay Viewer & PGN Export (`@author: Mohammad Sufiyan Aasim` & `@author: Taha Siddiqui`)
Allows players to review past matches from the `Recent Match History` tables or post-game popup. The `ReplayViewerModal` (`Sufiyan`) provides step navigation (`◀◀`, `◀`, `▶`, `▶▶`) and auto-play (`▶ Auto`), while the `DatabaseManager.export_game_to_pgn` (`Taha`) saves matches to `.pgn` files under `data/pgn/`.
