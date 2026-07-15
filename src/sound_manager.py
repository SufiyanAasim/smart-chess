# ==============================================================================
# Project: Smart Chess
# Module: Threaded Sound Manager (Audio & Multi-threading)
# Author: Taha Siddiqui (@13eeCoder) - Multi-threading & Audio
# License: MIT License
# ==============================================================================
__author__ = "Taha Siddiqui"

import os
import ctypes

try:
    import pygame  # pip install pygame or pygame-ce
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class WinMCIPlayer:
    """
    Native Windows MP3 playback engine using winmm.dll (mciSendStringW) (@author: Taha Siddiqui).
    Plays custom MP3 sound effects with zero external dependencies when pygame is not installed.
    """
    def __init__(self, sounds_dir: str):
        self.sounds_dir = sounds_dir
        self._alias_counter = 0

    def play(self, name: str, volume: float = 1.0) -> bool:
        if os.name != "nt":
            return False
        try:
            path = os.path.join(self.sounds_dir, f"{name}.mp3")
            if not os.path.exists(path):
                return False

            self._alias_counter = (self._alias_counter + 1) % 25
            alias = f"snd_{self._alias_counter}"

            # Close any previous instance of this alias
            ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)

            # Open MP3 file
            err = ctypes.windll.winmm.mciSendStringW(f'open "{path}" type mpegvideo alias {alias}', None, 0, None)
            if err != 0:
                err = ctypes.windll.winmm.mciSendStringW(f'open {path} type mpegvideo alias {alias}', None, 0, None)
            if err == 0:
                # Set volume (0 to 1000 scale in MCI)
                vol_int = int(max(0.0, min(1.0, volume)) * 1000)
                ctypes.windll.winmm.mciSendStringW(f"setaudio {alias} volume to {vol_int}", None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f"play {alias} from 0", None, 0, None)
                return True
        except Exception:
            pass
        return False


class SoundManager:
    """
    Threaded sound controller for MP3 effects (@author: Taha Siddiqui).
    Plays MP3 sounds from ./resources/sounds using exact filenames:
    game-start, game-end, castle, capture, pre-move, ten-seconds,
    illegal, notify, promote, move-check, move-opponent, move-self

    Dual-Engine Architecture:
    1. Pygame / Pygame-CE (if installed and available)
    2. Windows Native MCI Player (ctypes winmm.dll, 100% dependency-free on Windows)
    """

    def __init__(self, tk_root, sounds_dir: str, enabled: bool = True):
        self.tk_root = tk_root
        self.sounds_dir = sounds_dir
        self.enabled = enabled

        self._ready = False
        self._loaded = {}
        self.volume = 1.0
        self.mci_player = WinMCIPlayer(sounds_dir) if os.name == "nt" else None

        if self.enabled and PYGAME_AVAILABLE:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.set_num_channels(32)
                self._ready = True
            except Exception:
                self._ready = False

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        for snd in self._loaded.values():
            if snd:
                try:
                    snd.set_volume(self.volume)
                except Exception:
                    pass

    def _path(self, name: str) -> str:
        return os.path.join(self.sounds_dir, f"{name}.mp3")

    def play(self, name: str):
        if not self.enabled:
            return

        path = self._path(name)
        if not os.path.exists(path):
            self._fallback_beep()
            return

        # Attempt Pygame engine first if ready
        if self._ready:
            try:
                snd = self._loaded.get(name)
                if snd is None:
                    snd = pygame.mixer.Sound(path)
                    try:
                        snd.set_volume(self.volume)
                    except Exception:
                        pass
                    self._loaded[name] = snd
                ch = snd.play()
                if ch is not None:
                    return
            except Exception:
                pass

        # Attempt Native Windows MCI engine if on Windows or Pygame failed/not installed
        if self.mci_player and self.mci_player.play(name, volume=self.volume):
            return

        # Only if both audio engines fail do we fall back to system bell
        self._fallback_beep()

    def _fallback_beep(self):
        try:
            self.tk_root.bell()
        except Exception:
            pass
