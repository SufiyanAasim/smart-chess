# Changelog

All notable changes to the Smart Chess desktop application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
- Ongoing performance tuning and Stockfish 18 engine parameter refinements.

---

## [5.0.0] - 2026-07-15 ("Grandmaster")

📖 Detailed release notes are available in [v5.0.0.md](file:///d:/Completed%20Github%20Projects%20%28Fully%20Tested%20&%20Deployed%29/Smart%20Chess/docs/releases/v5.0.0.md).

### Added
- **🏆 Tactical Puzzle Trainer (`@author: Taha Siddiqui`)**: Interactive training mode with seeded FEN puzzles in SQLite (`DatabaseManager`), real-time move sequence verification, and theme badges.
- **📊 Post-Match Analysis Bar & Blunder Graph (`@author: Mohammad Sufiyan Aasim`)**: Background Stockfish evaluation thread computing centipawn curves, move classifications (`🔥 Best Move`, `🤔 Inaccuracy`, `😧 Mistake`, `😱 Blunder`), and detailed summary table modal.
- **⏱️ Custom Time Controls & Fischer Increment (`@author: Taha Siddiqui`)**: Preset clocks (`5+0 Bullet`, `3+2 Blitz`, `10+5 Rapid`, `15+10 Classical`) plus custom dialog with per-turn Fischer increment (`apply_turn_increment`) applied across local and LAN games.
- **◀ Game Replay Viewer (`@author: Mohammad Sufiyan Aasim & Taha Siddiqui`)**: Interactive step-by-step match replay modal (`ReplayViewerModal`) with navigation controls and auto-play (`▶ Auto`).
- **📥 PGN Export (`@author: Taha Siddiqui`)**: One-click export of any completed or stored game history directly to standard `.pgn` files inside `data/pgn/`.
- **🗑️ Match Deletion & Management (`@author: Taha Siddiqui`)**: Delete individual selected matches or clear entire game history with confirmation dialogs directly from the login screen or leaderboard modal.
- **💬 LAN Chat & Floating Emotes (`@author: Taha Siddiqui`)**: Real-time LAN chat messaging and floating board emote overlays (`LAN_CHAT`, `LAN_EMOTE`).
- **♟️ Checkmate Verification (`@author: Mohammad Sufiyan Aasim`)**: Verified rule precision checking `board.is_game_over()` on every move attempt, triggering custom checkmate trophies and sounds.

---

## [1.0.0] - 2026-07-14 ("Patzer")

📖 Detailed release notes are available in [v1.0.0.md](file:///d:/Completed%20Github%20Projects%20%28Fully%20Tested%20&%20Deployed%29/Smart%20Chess/docs/releases/v1.0.0.md).

### Added
- **Modern Rebranding**: Renamed application to "Smart Chess" with custom flat layout profiles, matching dark theme panels, and updated brand iconography.
- **💡 Asynchronous AI Move Hints**: On-demand Stockfish analysis generating neon-purple chess board overlay indicators without blocking main UI execution.
- **🏆 Styled GameOver Dialog**: Formatted post-game modal handling resignation, checks, draws, stalemates, timeouts, and rematch options.
- **🎮 Local Network (LAN) Multiplayer**: UDP room broadcast discovery on port 5000 and TCP socket game state synchronization for hosting/joining local matches.
- **Recent Match History UI Buttons**: Themed scroll indicators for the sidebar match history list.
- **Contributors Credits**: Premium credit card layout inside the setup credits screen.
- **Coordinates Tooltips**: Precise coordinates popup shown on board dock hover with 15px offset safety to prevent mouse-hover flickering.
- **Pawn Promotion Dialog**: Multi-choice selection popup for piece promotions.
- **IP Address Helper**: Informational panel displaying local IP addresses for LAN multiplayer hosting.
- **Database Engine**: SQL-injection-resistant SQLite database manager (`DatabaseManager`) to securely log history records inside `data/chess_games.db` (`11` matches consolidated) and export PGN game files to `data/pgn/`.

### Changed
- **Modular Directory & Path Organization**: Consolidated all core source files into a clean `src/` directory and implemented dual-mode path resolution (`utils_paths.py`) using `get_data_path` to ensure persistent database and PGN storage alongside packaged PyInstaller executables (`data/`).
- **Audio Output Threading**: Threaded Pygame mixer playback to prevent main thread blocking during chess move events.
- **UTF-8 Output Encoding**: Configured Python output encoding explicitly to UTF-8 to prevent terminal errors.
