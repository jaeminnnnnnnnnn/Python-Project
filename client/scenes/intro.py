import pygame

from client.constants import BLACK, CYAN
from client.scenes.base import Scene
from client.ui.fonts import game_font


class IntroScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.elapsed = 0.0

    def on_enter(self) -> None:
        self.elapsed = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == self.app.key("confirm"):
                self.app.change_scene("menu")

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= 1.2:
            self.app.change_scene("menu")

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        title_font = game_font(78)
        title = title_font.render("GTRIS", True, CYAN)
        screen.blit(title, title.get_rect(center=(480, 360)))
