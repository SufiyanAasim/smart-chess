# Troubleshooting Guide

Common issues and their solutions:

## 1. Stockfish Engine Offline
- **Symptoms**: AI moves instantly or reports "Engine offline".
- **Fix**: Place `stockfish.exe` in the root folder of the project. Ensure the executable matches your architecture (e.g. x64).

## 2. Audio Playback Failures
- **Symptoms**: Warnings in output or no sound clicks on moves.
- **Fix**: Pygame audio relies on initialized sound mixers. Ensure correct audio output devices are active and volume settings in the settings panel are configured.

## 3. Tkinter PIL / Pillow Failures
- **Symptoms**: Piece sprites fail to render, fallback glyphs are shown instead.
- **Fix**: Reinstall Pillow in your virtual environment:
  ```bash
  pip install --force-reinstall Pillow
  ```

## 4. Database & PGN Data Persistence
- **Symptoms**: Match records missing after restarting standalone executable (`SmartChess.exe`) or PGN export directory errors.
- **Fix**: Smart Chess utilizes `get_data_path` to persist all database logs and exported PGN files inside `data/chess_games.db` and `data/pgn/`. When running as a packaged executable, the `data/` directory is automatically created inside the directory containing `SmartChess.exe` (not inside temporary extraction folder `_MEIPASS`). Ensure that the folder where `SmartChess.exe` resides has write permissions. When running from source (`python main.py`), check that `<project_root>/data/` exists and is writable.
