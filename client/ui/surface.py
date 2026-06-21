import pygame

from client.constants import CYAN, GRAY, WHITE
from client.ui.fonts import game_font


PANEL_BG = (28, 32, 40)
PANEL_DARK = (20, 23, 29)


def draw_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    border_color: tuple[int, int, int] = GRAY,
    fill_color: tuple[int, int, int] = PANEL_BG,
) -> None:
    pygame.draw.rect(screen, fill_color, rect, border_radius=8)
    pygame.draw.rect(screen, border_color, rect, 1, border_radius=8)


def draw_header(screen: pygame.Surface, font: pygame.font.Font, title: str, subtitle: str | None = None) -> None:
    title_surface = font.render(title, True, WHITE)
    screen.blit(title_surface, (80, 58))
    pygame.draw.line(screen, CYAN, (80, 106), (880, 106), 2)
    if subtitle:
        subtitle_surface = game_font(24).render(subtitle, True, GRAY)
        screen.blit(subtitle_surface, (82, 116))


def draw_status_bar(screen: pygame.Surface, font: pygame.font.Font, text: str) -> None:
    rect = pygame.Rect(70, 632, 820, 40)
    draw_panel(screen, rect, border_color=(48, 54, 66), fill_color=PANEL_DARK)
    surface = font.render(text, True, GRAY)
    screen.blit(surface, (88, 642))
