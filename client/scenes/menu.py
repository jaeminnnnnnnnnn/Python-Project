import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.scenes.base import Scene
from client.ui.surface import draw_header, draw_panel, draw_status_bar


class MenuScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.items = [("Single", "single"), ("Online", "online_lobby"), ("Options", "options")]
        self.selected = 0

    def on_enter(self) -> None:
        self.app.audio.play_music("menu_theme")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.select_at(event.pos)
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.select_at(event.pos):
                    self.activate_selected()
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (self.app.key("menu_next"), pygame.K_TAB, pygame.K_DOWN, pygame.K_RIGHT):
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key in (pygame.K_UP, pygame.K_LEFT):
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key in (self.app.key("confirm"), pygame.K_RETURN):
                self.activate_selected()
            elif event.key in (self.app.key("back"), pygame.K_ESCAPE):
                self.app.quit()

    def item_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(110, 165 + index * 68, 300, 50)

    def select_at(self, pos: tuple[int, int]) -> bool:
        for index in range(len(self.items)):
            if self.item_rect(index).collidepoint(pos):
                self.selected = index
                return True
        return False

    def activate_selected(self) -> None:
        target = self.items[self.selected][1]
        self.app.change_scene(target)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        draw_header(screen, self.font, "GTRIS", "Online Tetris")
        for index, (label, _) in enumerate(self.items):
            rect = self.item_rect(index)
            color = CYAN if index == self.selected else WHITE
            draw_panel(screen, rect, border_color=color if index == self.selected else GRAY)
            surface = self.font.render(label, True, color)
            screen.blit(surface, surface.get_rect(midleft=(rect.x + 28, rect.centery)))
        draw_status_bar(screen, self.small_font, "Click or use arrows   Enter Select   Esc Quit")
