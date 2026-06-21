import pygame

from client.audio import sfx
from client.constants import BLACK, CYAN, GRAY, RED, WHITE
from client.game.repeat import GAME_REPEAT, RepeatController
from client.scenes.base import Scene
from client.tetris.rules import TetrisGame
from client.tetris.snapshot import game_snapshot
from client.ui.tetris_panel import draw_tetris_panel


PANEL_X = 280
PANEL_Y = 95


class SingleScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.game = TetrisGame()
        self.fall_elapsed = 0.0
        self.repeat = RepeatController(GAME_REPEAT)

    def on_enter(self) -> None:
        self.game = TetrisGame()
        self.fall_elapsed = 0.0
        self.repeat.reset()
        self.app.audio.play_music("game_theme")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.game.game_over:
                if self.retry_rect().collidepoint(event.pos):
                    self.on_enter()
                elif self.menu_rect().collidepoint(event.pos):
                    self.app.change_scene("menu")
                continue
            if event.type == pygame.KEYUP:
                self.release_repeat(event.key)
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == self.app.key("back"):
                self.app.change_scene("menu")
            elif event.key == self.app.key("retry_ready") and self.game.game_over:
                self.on_enter()
            elif self.game.game_over:
                continue
            elif event.key == self.app.key("move_left"):
                self.repeat.press("move_left")
                self.apply_action("move_left")
            elif event.key == self.app.key("move_right"):
                self.repeat.press("move_right")
                self.apply_action("move_right")
            elif event.key == self.app.key("soft_drop"):
                self.repeat.press("soft_drop")
                self.apply_action("soft_drop")
            elif event.key == self.app.key("rotate_cw"):
                if self.game.rotate(1):
                    self.app.audio.play_sfx(sfx.ROTATE)
            elif event.key == self.app.key("rotate_ccw"):
                if self.game.rotate(-1):
                    self.app.audio.play_sfx(sfx.ROTATE)
            elif event.key == self.app.key("rotate_180"):
                if self.game.rotate(2):
                    self.app.audio.play_sfx(sfx.ROTATE)
            elif event.key == self.app.key("hard_drop"):
                self.after_step(self.game.hard_drop())
                self.app.audio.play_sfx(sfx.HARD_DROP)
            elif event.key == self.app.key("hold"):
                self.game.hold()
                self.app.audio.play_sfx(sfx.HOLD)

    def update(self, dt: float) -> None:
        if self.game.game_over:
            return
        for action in self.repeat.update(dt):
            self.apply_action(action)
        self.fall_elapsed += dt
        interval = max(0.12, 0.8 - (self.game.level - 1) * 0.06)
        if self.fall_elapsed >= interval:
            self.fall_elapsed = 0.0
            self.after_step(self.game.tick())

    def release_repeat(self, key: int) -> None:
        for action in GAME_REPEAT:
            if key == self.app.key(action):
                self.repeat.release(action)

    def apply_action(self, action: str) -> None:
        if action == "move_left":
            if self.game.move(-1, 0):
                self.app.audio.play_sfx(sfx.MOVE)
        elif action == "move_right":
            if self.game.move(1, 0):
                self.app.audio.play_sfx(sfx.MOVE)
        elif action == "soft_drop":
            self.after_step(self.game.soft_drop())

    def after_step(self, result) -> None:
        if result.lines_cleared:
            self.app.audio.play_sfx(sfx.LINE_CLEAR)
        if result.game_over:
            self.app.audio.play_sfx(sfx.GAME_OVER)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        self.draw_text(screen, "Single", (70, 50))
        draw_tetris_panel(screen, self.font, self.small_font, self.snapshot(), PANEL_X, PANEL_Y, "")
        self.draw_sidebar(screen)
        if self.game.game_over:
            self.draw_game_over(screen)

    def draw_game_over(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 172))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(250, 205, 460, 245)
        pygame.draw.rect(screen, (28, 32, 40), panel, border_radius=8)
        pygame.draw.rect(screen, RED, panel, width=3, border_radius=8)

        title_surface = self.font.render("GAME OVER", True, RED)
        screen.blit(title_surface, title_surface.get_rect(center=(panel.centerx, panel.y + 66)))

        score_surface = self.small_font.render(f"Score {self.game.score}   Lines {self.game.lines}", True, WHITE)
        screen.blit(score_surface, score_surface.get_rect(center=(panel.centerx, panel.y + 122)))

        retry_surface = self.small_font.render("R Retry", True, CYAN)
        screen.blit(retry_surface, retry_surface.get_rect(center=(panel.centerx, panel.y + 176)))

        back_surface = self.small_font.render("Esc Menu", True, GRAY)
        screen.blit(back_surface, back_surface.get_rect(center=(panel.centerx, panel.y + 210)))

    def retry_rect(self) -> pygame.Rect:
        return pygame.Rect(370, 360, 220, 40)

    def menu_rect(self) -> pygame.Rect:
        return pygame.Rect(370, 400, 220, 40)

    def snapshot(self) -> dict:
        return game_snapshot(self.game)

    def draw_sidebar(self, screen: pygame.Surface) -> None:
        self.draw_text(screen, f"Score {self.game.score}", (70, 130), small=True)
        self.draw_text(screen, f"Lines {self.game.lines}", (70, 165), small=True)
        self.draw_text(screen, f"Level {self.game.level}", (70, 200), small=True)
