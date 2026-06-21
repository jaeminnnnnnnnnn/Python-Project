from pathlib import Path

import pygame

from client.game.settings import Settings
from client.paths import asset_path


MUSIC_EXTENSIONS = (".ogg", ".mp3", ".wav")
SFX_EXTENSIONS = (".wav", ".ogg", ".mp3")


class AudioManager:
    def __init__(self) -> None:
        self.music_enabled = True
        self.sfx_enabled = True
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.available = False
        self.current_music: str | None = None
        self.sfx_cache: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.available = True
        except pygame.error:
            self.available = False

    def apply_settings(self, settings: Settings) -> None:
        self.music_enabled = settings.music_enabled
        self.sfx_enabled = settings.sfx_enabled
        self.music_volume = settings.music_volume
        self.sfx_volume = settings.sfx_volume
        if self.available:
            pygame.mixer.music.set_volume(self.music_volume)
            if not self.music_enabled:
                pygame.mixer.music.stop()

    def play_music(self, name: str) -> None:
        if not self.available or not self.music_enabled:
            return
        if self.current_music == name and pygame.mixer.music.get_busy():
            return
        path = self._find_asset(asset_path("music"), name, MUSIC_EXTENSIONS)
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_music = name
        except pygame.error:
            self.current_music = None

    def play_sfx(self, name: str) -> None:
        if not self.available or not self.sfx_enabled:
            return
        sound = self.sfx_cache.get(name)
        if sound is None:
            path = self._find_asset(asset_path("sfx"), name, SFX_EXTENSIONS)
            if not path:
                return
            try:
                sound = pygame.mixer.Sound(path)
                self.sfx_cache[name] = sound
            except pygame.error:
                return
        sound.set_volume(self.sfx_volume)
        sound.play()

    def _find_asset(self, directory: Path, name: str, extensions: tuple[str, ...]) -> Path | None:
        for extension in extensions:
            path = directory / f"{name}{extension}"
            if path.exists():
                return path
        return None
