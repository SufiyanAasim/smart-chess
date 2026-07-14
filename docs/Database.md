# SQLite & PGN Data Storage Specification

Smart Chess stores local match history inside an embedded SQLite database and exports full game histories in standard Portable Game Notation (PGN) format.

## Persistent Data Locations
All persistent user data is managed under the `data/` directory:
- **Database File**: `data/chess_games.db` (Consolidated containing all historical games played to date)
- **PGN Exports Folder**: `data/pgn/*.pgn`

### Path Resolution (`utils_paths.py`)
To prevent data loss in PyInstaller-built standalone executables (`SmartChess.exe`), the application uses `get_data_path(*parts)`:
- In development mode (`python main.py`), paths resolve inside `<project_root>/data/`.
- In PyInstaller packaged executable mode (`sys.frozen`), paths resolve inside `<executable_directory>/data/`, preventing the database or exported PGNs from being wiped when the temporary `_MEIPASS` folder is cleaned up upon exit.

## Schema Structure

### `games` Table
Records historical match results and statistics.

| Field | Type | Attributes | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique record ID (chronologically ordered) |
| `game_date` | TEXT | NOT NULL | Date and time stamp of the match (`YYYY-MM-DD HH:MM:SS`) |
| `white_player` | TEXT | NOT NULL | Name of White player or Computer |
| `black_player` | TEXT | NOT NULL | Name of Black player or Computer |
| `result` | TEXT | NOT NULL | Game outcome (e.g. `1-0`, `0-1`, `1/2-1/2`) |
| `total_moves` | INTEGER | NOT NULL | Total count of plies/moves |
| `mode` | TEXT | NOT NULL | Game mode selected (`Local 1v1`, `LAN Host`, `Player vs Computer`, etc.) |

