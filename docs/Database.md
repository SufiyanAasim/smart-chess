# SQLite & PGN Data Storage Specification
Maintainer: **Taha Siddiqui (@13eeCoder)**

Smart Chess stores local match history and tactical puzzles inside an embedded SQLite database (`DatabaseManager`) and exports full game histories in standard Portable Game Notation (PGN) format (`exports/`).

## Persistent Data Locations
All persistent user data is managed automatically across runtime sessions:
- **Database File**: `data/chess_games.db` (Consolidated containing all historical games played and tactical puzzles)
- **PGN Exports Folder**: `data/exports/*.pgn` (Generated when clicking `📥 Export PGN`)

### Path Resolution (`utils_paths.py`)
To prevent data loss in PyInstaller-built standalone executables (`SmartChess.exe`), the application uses `get_data_path(*parts)`:
- In development mode (`python main.py`), paths resolve inside `<project_root>/data/`.
- In PyInstaller packaged executable mode (`sys.frozen`), paths resolve inside `<executable_directory>/data/`, preventing the database or exported PGNs from being wiped when the temporary `_MEIPASS` folder is cleaned up upon exit.

## Schema Structure

### `games` Table (@author: Taha Siddiqui)
Records historical match results, total moves, selected mode, and exact SAN move notation strings.

| Field | Type | Attributes | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique record ID (chronologically ordered) |
| `game_date` | TEXT | NOT NULL | Date and time stamp of the match (`YYYY-MM-DD HH:MM:SS`) |
| `white_player` | TEXT | NOT NULL | Name of White player or Computer (`White`, `Solver`, etc.) |
| `black_player` | TEXT | NOT NULL | Name of Black player or Computer (`Black`, `Puzzle AI`, etc.) |
| `result` | TEXT | NOT NULL | Game outcome (e.g. `1-0`, `0-1`, `1/2-1/2`) |
| `total_moves` | INTEGER | NOT NULL | Total count of plies/moves |
| `mode` | TEXT | NOT NULL | Game mode selected (`Local 1v1`, `Tactical Puzzle Trainer`, `LAN Host`, etc.) |
| `san_moves` | TEXT | DEFAULT "" | Space-separated string of Standard Algebraic Notation moves (`e4 e5 Nf3 Nc6`) |

### `puzzles` Table (@author: Taha Siddiqui)
Stores curated endgame tactics and winning checkmate sequences for the `Tactical Puzzle Trainer` mode.

| Field | Type | Attributes | Description |
|---|---|---|---|
| `puzzle_id` | TEXT | PRIMARY KEY | Unique string identifier (`p001`, `p002`, `p003`) |
| `title` | TEXT | NOT NULL | Human-readable title of the puzzle (`Forking the Queen`) |
| `fen` | TEXT | NOT NULL | Starting board state in Forsyth-Edwards Notation |
| `moves` | TEXT | NOT NULL | Space-separated correct winning move sequence in UCI format (`e4f6 d7d5`) |
| `theme` | TEXT | DEFAULT "Tactics" | Theme classification badge (`Checkmate in 2`, `Knight Fork`, `Pin`) |
| `difficulty` | INTEGER | DEFAULT 1 | Numeric rating index (1=Easy, 2=Medium, 3=Hard) |

## Operations & Queries (`DatabaseManager`)
- **`record_game(...)`**: Inserts a completed game row with `san_moves`. Automatically alters legacy database schemas to append the `san_moves` column if upgrading from an older version.
- **`fetch_recent_games_with_id(limit=15)`**: Fetches match records ordered chronologically descending for the login screen and leaderboard dialogs.
- **`delete_game_by_id(game_id)` & `clear_all_games()`**: Deletes individual match records or purges the entire history (`🗑️ Delete Selected` & `🧹 Clear All`).
- **`export_game_to_pgn(game_id)`**: Formats a stored game row into a standard PGN string complete with `Event`, `Site`, `Date`, `White`, `Black`, `Result`, and numbered move pairs (`1. e4 e5 2. Nf3 Nc6...`).
