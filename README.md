<div align="center">

<img src="src/resources/app_logo/logo.png" alt="Smart Chess Logo" width="110" />

# Smart Chess

**A secure, feature-rich desktop chess client with Stockfish AI and serverless LAN multiplayer rooms**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-5.0.0%20Grandmaster-7c3aed?style=flat)](docs/releases/v5.0.0.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-64748b?style=flat)]()
[![Tests](https://img.shields.io/badge/tests-passing-22c55e?style=flat)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-0ea5e9?style=flat)](.github/CONTRIBUTING.md)

Play offline matches against Stockfish 18, host LAN lobbies for local multiplayer games and spectators, and utilize real-time move hints — all within a custom flat dark desktop application. Built with Python, Tkinter, Pygame, and SQLite. No cloud connections, no subscriptions, and zero data leaving your machine.

[**Download Release**](docs/releases/v5.0.0.md) · [**Changelog**](docs/CHANGELOG.md) · [**Roadmap**](docs/ROADMAP.md) · [**Report a Bug**](.github/ISSUE_TEMPLATE/bug.yml)

</div>

---

## 📖 Overview
Smart Chess delivers a modern desktop workspace for chess players, blending standard board rules with visual engine telemetry and serverless multiplayer games. Built using Python's robust standard GUI system (Tkinter) and enhanced with a custom flat dark visual theme, the client bypasses typical legacy styling to provide clean panels, glowing active timers, and smooth coordinate overlays.

By incorporating Stockfish 18 as an asynchronous local process and combining it with UDP broadcast discovery for local network matches, Smart Chess serves as a complete offline study companion and multiplayer client.

---

## ✨ Key Features

### ⚔️ Game Modes
* **Local 1v1**: Classic pass-and-play desktop match with automated validation.
* **Player vs Computer**: Configurable offline matches against a local Stockfish 18 engine.
* **LAN Host & Join**: Host rooms on your local network (discovered via UDP broadcasting on port 5000) or join as a player or spectator with instant move synchronization.

### 💡 Interactive Telemetry & Hints
* **Stockfish Hints**: Request background AI evaluations dynamically using the "💡 Get Move Hint" control, rendering path suggestions on the board in neon purple.
* **Move Highlights**: Visual gold overlays (`#FFF59D`) indicating start and end coordinates of the last move.
* **Pawn Promotion Overlay**: Custom dialog that halts the clock to let players select Queen, Rook, Bishop, or Knight promotions.

### ⏱️ Responsive Clocks
* **Turn Glows**: Glowing neon-blue frame highlighting the clock of the active player.
* **Time Alerts**: Low-time audio reminders and visual warnings for players during high-stakes endgames.

### 🔐 Security & Local Relational Storage
* **SQLite Backend**: Logs matches, moves, timings, and outcomes to local file `data/chess_games.db` (`11` historical matches consolidated).
* **PGN Exports**: Exports match histories in Portable Game Notation directly to `data/pgn/`.
* **PyInstaller Data Persistence**: Uses `get_data_path` so user databases and PGN exports persist alongside standalone executables (`SmartChess.exe`) without getting wiped by temporary build folders (`_MEIPASS`).
* **Query Isolation**: All database interaction utilizes fully parameterized SQL queries, guaranteeing complete isolation from injection attacks.

---

## 🏗️ System Architecture
Smart Chess enforces a strict modular architecture to separate UI elements, socket networking, background calculation threads, and data management layers.

```
┌─────────────────────────────────────────────────────────┐
│                    Entry Point                          │
│                     main.py                             │
│       (Appends src/ path & boots ChessApp UI)           │
└──────────────────────────┬──────────────────────────────┘
                           │
             ┌─────────────▼─────────────┐
             │       Application         │
             │     src/chess_app.py      │
             │   (Controls App States)   │
             └──────┬──────────────┬─────┘
                    │              │
       ┌─────────────▼─────┐  I─────▼─────────────┐
       │   ChessBoardUI    │  │    UISidebar      │
       │  src/ui_board.py  │  │ src/ui_sidebar.py │
       │ (Draws board/hint)│  │ (Clocks & Logs)   │
       └───────────────────┘  └───────────────────┘
```

* **`main.py`**: Entry-point module setting path variables and launching the Tkinter main loop.
* **`src/chess_app.py`**: Core application orchestrator managing panel transitions, lobby selections, sound settings, and match timers.
* **`src/ui_board.py`**: Interactive board viewport handling piece draws, moves validation highlights, and hover coordinate tooltips.
* **`src/ui_sidebar.py`**: Panel controller containing the active match statistics, captures ratio list, and the match notation log.
* **`src/chess_engine.py`**: Manages subprocess loops communicating directly with the Stockfish 18 binary via stdin/stdout streams.
* **`src/lan_controller.py`**: Manages socket listening loops, TCP connection synchronizations, and UDP host discovery broadcasting.
* **`src/database_manager.py`**: Handles local SQLite operations to insert and query historical game logs inside `data/chess_games.db`.
* **`src/utils_paths.py`**: Dual-mode path resolver separating read-only bundled assets (`resource_path`) from persistent read-write user storage (`get_data_path` for `data/chess_games.db` and `data/pgn/`).

---

## 🛠️ Technology Stack

### Third-Party Dependencies
* **[Pillow](https://python-pillow.org/)**: Advanced image handling and sprite rendering support.
* **[Pygame](https://www.pygame.org/)**: Threaded audio mixer powering ambient move clicks and capture cues.
* **[python-chess](https://github.com/niklasf/python-chess)**: Chess rules compliance engine, move generator, and SAN/PGN parsing framework.

### Standard Libraries Utilized
* **`tkinter` / `ttk`**: Application GUI layouts, styles, and card views.
* **`sqlite3`**: Relational database storage.
* **`socket` & `threading`**: Local network host broadcasting and asynchronous game loops.
* **`subprocess`**: Managing independent Stockfish engine calculations.

---

## 🚀 Getting Started

### Prerequisites
* Python **3.11** or newer.
* Stockfish 18 binary located in the project root directory (named `stockfish.exe` on Windows).

### Installation & Run
1. Clone the repository:
   ```bash
   git clone https://github.com/SufiyanAasim/smart-chess.git
   cd smart-chess
   ```
2. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### 🐳 Docker & Container Deployment
Run Smart Chess inside an isolated containerized environment with X11 display forwarding and volume persistence:
```bash
# Build and run with Docker Compose (recommended)
docker compose up --build

# Or run manually with Docker CLI
docker build -t smart-chess .
docker run --rm -it --net=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v $(pwd)/data:/app/data smart-chess
```

---

## 🗂️ Project Structure

```text
smart-chess/
├── .github/                    # Community files, templates, and CI workflows
│   ├── ISSUE_TEMPLATE/         # Bug, feature, and question forms
│   └── workflows/              # Build, lint, and test automation
├── data/                       # Local application data
│   ├── chess_games.db          # SQLite match database
│   └── pgn/                    # Exported PGN game files
├── docs/                       # Architecture, development, and release docs
│   ├── releases/               # Per-version release notes (v1–v5)
│   ├── Architecture.md          # System architecture details
│   ├── Database.md              # Database schema and persistence notes
│   ├── Development.md           # Developer setup and contribution guide
│   ├── CHANGELOG.md             # Version history
│   ├── RELEASE.md               # Release process and milestones
│   ├── ROADMAP.md               # Planned features
│   └── Troubleshooting.md       # Common issues and fixes
├── src/                        # Application source code
│   ├── resources/               # Logos, piece artwork, backgrounds, and sounds
│   ├── ai_controller.py         # AI move and hint orchestration
│   ├── chess_app.py             # Main application coordinator
│   ├── chess_engine.py          # Stockfish process integration
│   ├── database_manager.py      # SQLite match persistence
│   ├── game_state.py            # Board and match state management
│   ├── lan_controller.py        # LAN lobby and synchronization logic
│   ├── network.py               # Network transport helpers
│   ├── sound_manager.py         # Pygame audio playback
│   ├── ui_board.py              # Chessboard rendering and interaction
│   ├── ui_sidebar.py            # Clocks, controls, and move log UI
│   └── utils_paths.py           # Bundled and persistent path resolution
├── tests/                      # Unit and integration tests
│   ├── test_database.py         # Database behavior tests
│   └── test_lan.py              # LAN networking tests
├── .env.example                # Optional environment configuration template
├── build_exe.ps1               # Windows executable build script
├── docker-compose.yml           # Container orchestration configuration
├── Dockerfile                   # Application container image
├── main.py                      # Desktop application entry point
├── Makefile                     # Common development commands
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT license
└── README.md                    # Project overview and setup guide
```

---

## 🗺️ Project Roadmap & Releases

We follow Semantic Versioning (`MAJOR.MINOR.PATCH`) to organize releases. Detailed specifications for all version milestones can be accessed in [docs/RELEASE.md](docs/RELEASE.md).

| Version | Codename | Status | Highlights |
|---|---|---|---|
| [v5.0.0](docs/releases/v5.0.0.md) | **Grandmaster** | ✅ Released | Tactical Puzzle Trainer, Post-Match Blunder Graph, Fischer Increments, PGN Replay Viewer, Dynamic Emotes, LAN Chat & Spectator verification. |
| [v4.0.0](docs/releases/v4.0.0.md) | **Zugzwang** | ✅ Released | Tactical checkmate trophies, schema migrations, SAN archiving. |
| [v3.0.0](docs/releases/v3.0.0.md) | **Fianchetto** | ✅ Released | Immersive sound themes, threaded audio controller, custom player profiles. |
| [v2.0.0](docs/releases/v2.0.0.md) | **Gambit** | ✅ Released | Post-match analysis graph, move classification overlays (blunders, mistakes). |
| [v1.0.0](docs/releases/v1.0.0.md) | **Patzer** | 🟢 Pre-Release | Flat Dark UI, Stockfish 18, Move Hints, SQLite Logging, LAN Multiplayer lobbies. |

---

## 🧪 Running Unit & Integration Tests
Validate database queries, schema migrations, and local network socket synchronizations by running the automated test suite:
```bash
python -m unittest discover -s tests
```

---

## 👥 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/SufiyanAasim">
        <img src="https://github.com/SufiyanAasim.png" width="80" alt="Mohammad Sufiyan Aasim"/><br/>
        <sub><b>Mohammad Sufiyan Aasim</b></sub>
      </a><br/>
      <sub>System Architect · AI/MLOps · Docs</sub>
    </td>
    <td align="center">
      <a href="https://github.com/13eeCoder">
        <img src="https://github.com/13eeCoder.png" width="80" alt="Taha Siddiqui"/><br/>
        <sub><b>Taha Siddiqui</b></sub>
      </a><br/>
      <sub>Security & Networking · Multi-threading</sub>
    </td>
  </tr>
</table>

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
