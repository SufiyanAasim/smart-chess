# Development Guidelines

## Setting Up Workspace
1. Initialize a Python virtual environment (v3.11+):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run in developer mode:
   ```bash
   python main.py
   ```

## Folder Layout Structure
- `src/`: Core Python modules (board canvas, sidebar menus, engine controls, AI, sound, LAN, and path utilities).
- `data/`: Persistent read/write user data directory:
  - `data/chess_games.db`: Consolidated SQLite match history database.
  - `data/pgn/`: Exported PGN game files (`*.pgn`).
- `docs/`: Technical specifications, architectural blueprints, and release documentation (`releases/`).
- `tests/`: Module unit tests (`test_database.py`).
- `src/resources/`: Bundled static read-only assets (piece sprites in PNG, audio sound clips, app icon, and start background).

## Path Resolution Best Practices (`utils_paths.py`)
When contributing code that reads or writes files, follow these strict path conventions:
- **`resource_path(*parts)`**: Use ONLY for read-only static resources bundled into PyInstaller (`_MEIPASS`), such as images, icons, and sound files inside `src/resources/`.
- **`get_data_path(*parts)`**: Use ALWAYS for read-write user data files (`chess_games.db`, PGN files). This guarantees that user files are stored persistently in `data/` alongside the executable when packaged, instead of temporary extraction folders.
