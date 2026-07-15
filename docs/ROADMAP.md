# Smart Chess Roadmap

This document outlines feature implementations, architectural milestones, and ongoing development phases:

## Phase 5 (v5.0.0 - Grandmaster): Training, Replays & Clock Management (Completed)
- [x] **Tactical Puzzle Trainer**: Interactive training mode with seeded FEN puzzles in SQLite (`DatabaseManager`) and real-time move sequence verification (`@author: Taha Siddiqui`).
- [x] **Post-Match Analysis Bar & Blunder Graph**: Stockfish evaluation curve (+2.5 to -4.0) and move breakdown modal (`@author: Mohammad Sufiyan Aasim`).
- [x] **Custom Time Controls & Fischer Increment**: Preset clocks (`5+0 Bullet`, `3+2 Blitz`, `10+5 Rapid`, `15+10 Classical`) plus custom dialog with turn increment applied (`@author: Taha Siddiqui`).
- [x] **Game Replay Viewer & PGN Export**: Interactive step-by-step match replay modal (`ReplayViewerModal`) and one-click export to `exports/` (`@author: Mohammad Sufiyan Aasim & Taha Siddiqui`).
- [x] **Match Management & Deletion**: Selective match deletion and full history purge dialogs (`@author: Taha Siddiqui`).
- [x] **LAN Chat & Floating Emotes**: Live LAN chat messaging and floating board emote overlays (`@author: Taha Siddiqui`).

## Phase 4 (v4.0.0 - Zugzwang): Achievements & Trophy Cabinet (Integrated)
- [x] Checkmate trophies (`🏆 Checkmate`) and audio feedback milestones (`@author: Mohammad Sufiyan Aasim`).
- [x] SQLite database schema migrations and SAN move notation archiving (`@author: Taha Siddiqui`).

## Phase 3 (v3.0.0 - Fianchetto): Sound Themes & Custom Profiles (Completed / Integrated)
- [x] Audio mixer threading and customizable sound volume/enable toggles (`SoundManager`) (`@author: Mohammad Sufiyan Aasim`).
- [x] Custom player naming across Local 1v1, Player vs Computer, and LAN modes (`@author: Mohammad Sufiyan Aasim & Taha Siddiqui`).

## Phase 2 (v2.0.0 - Gambit): Game Move Analysis & Graph (Completed in v5.0.0)
- [x] Post-match analysis graph displaying centipawn evaluation bar history (`@author: Mohammad Sufiyan Aasim`).
- [x] Classification of moves (`🔥 Best Move`, `🤔 Inaccuracy`, `😧 Mistake`, `😱 Blunder`) (`@author: Mohammad Sufiyan Aasim`).
- [x] Timeline navigation on match logs supporting retrospective board jumps (`ReplayViewerModal`) (`@author: Mohammad Sufiyan Aasim & Taha Siddiqui`).

## Phase 1 (v1.0.0 - Patzer): Core Restructure & Styling (Completed)
- [x] Flat modernized dark styling with borderless text frames (`@author: Mohammad Sufiyan Aasim`).
- [x] Relocate files to standard `src/` template (`@author: Mohammad Sufiyan Aasim`).
- [x] Interactive best-move suggestions using Stockfish integration (`@author: Mohammad Sufiyan Aasim`).
- [x] Custom rematch modals for game over terminations (`@author: Mohammad Sufiyan Aasim`).
- [x] Local Network (LAN) multiplayer over UDP discovery (`@author: Taha Siddiqui`).

## Future Directions
- [ ] Multi-engine support (e.g. Komodo, Leela Chess Zero).
- [ ] Opening book explorer auto-tagging Sicilian Defense, Ruy Lopez, Queen's Gambit.
- [ ] Online matchmaking server lobby beyond local area networks.
