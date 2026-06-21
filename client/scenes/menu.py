import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.scenes.base import Scene


class MenuScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.items = [("Single", "single"), ("Online", "online_lobby"), ("Options", "options")]
        self.selected = 0

    def on_enter(self) -> None:
        self.app.audio.play_music("menu_theme")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (self.app.key("menu_next"), pygame.K_DOWN, pygame.K_RIGHT):
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key in (pygame.K_UP, pygame.K_LEFT):
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key == self.app.key("confirm"):
                target = self.items[self.selected][1]
                self.app.change_scene(target)
            elif event.key == self.app.key("back"):
                self.app.quit()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        self.draw_text(screen, "Menu", (80, 70))
        for index, (label, _) in enumerate(self.items):
            color = CYAN if index == self.selected else WHITE
            prefix = "> " if index == self.selected else "  "
            surface = self.font.render(prefix + label, True, color)
            screen.blit(surface, (110, 160 + index * 58))
        hint = self.small_font.render("Tab/Arrow: Move   Enter: Select   Esc: Exit", True, GRAY)
        screen.blit(hint, (80, 650))
