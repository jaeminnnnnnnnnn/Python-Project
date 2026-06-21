import pygame

from client.constants import CYAN, GRAY, PIECE_COLORS, WHITE
from client.tetris.board import HEIGHT, WIDTH
from client.tetris.piece import SHAPES


CELL = 24
MINI_CELL = 12
PANEL_SIDE_WIDTH = 76
PANEL_GAP = 12
BOARD_PIXEL_WIDTH = WIDTH * CELL
BOARD_PIXEL_HEIGHT = HEIGHT * CELL
PANEL_WIDTH = PANEL_SIDE_WIDTH + PANEL_GAP + BOARD_PIXEL_WIDTH + PANEL_GAP + PANEL_SIDE_WIDTH
PANEL_HEIGHT = BOARD_PIXEL_HEIGHT


def draw_tetris_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    state: dict,
    x: int,
    y: int,
    title: str,
) -> None:
    hold_x = x
    board_x = x + PANEL_SIDE_WIDTH + PANEL_GAP
    next_x = board_x + BOARD_PIXEL_WIDTH + PANEL_GAP

    if title:
        title_rect = pygame.Rect(board_x, y - 34, BOARD_PIXEL_WIDTH, 26)
        pygame.draw.rect(screen, (28, 32, 40), title_rect, border_radius=6)
        pygame.draw.rect(screen, CYAN, title_rect, 1, border_radius=6)
        title_surface = small_font.render(title, True, WHITE)
        screen.blit(title_surface, title_surface.get_rect(center=title_rect.center))
    draw_hold_box(screen, small_font, state.get("hold"), hold_x, y)
    draw_board(screen, state.get("grid", empty_grid()), state.get("ghost", []), board_x, y)
    draw_next_box(screen, small_font, state.get("next", []), next_x, y)


def draw_board(screen: pygame.Surface, grid: list[list[str | None]], ghost: list, x: int, y: int) -> None:
    border = pygame.Rect(x - 4, y - 4, BOARD_PIXEL_WIDTH + 8, BOARD_PIXEL_HEIGHT + 8)
    pygame.draw.rect(screen, (12, 14, 18), border, border_radius=6)
    pygame.draw.rect(screen, CYAN, border, 2, border_radius=6)
    for row_index in range(HEIGHT):
        for col_index in range(WIDTH):
            kind = grid[row_index][col_index] if row_index < len(grid) and col_index < len(grid[row_index]) else None
            rect = pygame.Rect(x + col_index * CELL + 1, y + row_index * CELL + 1, CELL - 2, CELL - 2)
            color = PIECE_COLORS[kind] if kind else (20, 23, 29)
            pygame.draw.rect(screen, color, rect)
            if kind:
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)
    for ghost_x, ghost_y in ghost:
        if 0 <= ghost_x < WIDTH and 0 <= ghost_y < HEIGHT:
            rect = pygame.Rect(x + ghost_x * CELL + 4, y + ghost_y * CELL + 4, CELL - 8, CELL - 8)
            pygame.draw.rect(screen, (86, 92, 104), rect, 2)
    for col in range(WIDTH + 1):
        pygame.draw.line(screen, (35, 38, 45), (x + col * CELL, y), (x + col * CELL, y + BOARD_PIXEL_HEIGHT))
    for row in range(HEIGHT + 1):
        pygame.draw.line(screen, (35, 38, 45), (x, y + row * CELL), (x + BOARD_PIXEL_WIDTH, y + row * CELL))


def draw_hold_box(screen: pygame.Surface, font: pygame.font.Font, kind: str | None, x: int, y: int) -> None:
    draw_label(screen, font, "HOLD", x, y)
    pygame.draw.rect(screen, (28, 32, 40), (x, y + 28, PANEL_SIDE_WIDTH, 70), border_radius=6)
    pygame.draw.rect(screen, GRAY, (x, y + 28, PANEL_SIDE_WIDTH, 70), 1, border_radius=6)
    if kind:
        draw_piece_preview(screen, kind, x + 12, y + 43)


def draw_next_box(screen: pygame.Surface, font: pygame.font.Font, pieces: list[str], x: int, y: int) -> None:
    draw_label(screen, font, "NEXT", x, y)
    for index, kind in enumerate(pieces[:5]):
        box_y = y + 28 + index * 72
        pygame.draw.rect(screen, (28, 32, 40), (x, box_y, PANEL_SIDE_WIDTH, 64), border_radius=6)
        pygame.draw.rect(screen, GRAY, (x, box_y, PANEL_SIDE_WIDTH, 64), 1, border_radius=6)
        draw_piece_preview(screen, kind, x + 12, box_y + 12)


def draw_label(screen: pygame.Surface, font: pygame.font.Font, label: str, x: int, y: int) -> None:
    surface = font.render(label, True, WHITE)
    screen.blit(surface, surface.get_rect(center=(x + PANEL_SIDE_WIDTH // 2, y + 10)))


def draw_piece_preview(screen: pygame.Surface, kind: str, x: int, y: int) -> None:
    cells = SHAPES[kind][0]
    min_x = min(dx for dx, _ in cells)
    min_y = min(dy for _, dy in cells)
    color = PIECE_COLORS[kind]
    for dx, dy in cells:
        rect = pygame.Rect(
            x + (dx - min_x) * MINI_CELL,
            y + (dy - min_y) * MINI_CELL,
            MINI_CELL - 1,
            MINI_CELL - 1,
        )
        pygame.draw.rect(screen, color, rect)


def empty_grid() -> list[list[str | None]]:
    return [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
