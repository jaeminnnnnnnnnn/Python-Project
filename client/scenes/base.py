from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from client.constants import WHITE

if TYPE_CHECKING:
    from client.game.app import GameApp


class Scene:
    def __init__(self, app: GameApp) -> None:
        self.app = app
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 28)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pass

    def draw_text(self, screen: pygame.Surface, text: str, pos: tuple[int, int], small: bool = False) -> None:
        font = self.small_font if small else self.font
        surface = font.render(text, True, WHITE)
        screen.blit(surface, pos)
