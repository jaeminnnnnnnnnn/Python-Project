from dataclasses import dataclass

import pygame


DEFAULT_KEY_BINDINGS = {
    "menu_next": pygame.K_TAB,
    "confirm": pygame.K_RETURN,
    "back": pygame.K_ESCAPE,
    "retry_ready": pygame.K_r,
    "move_left": pygame.K_LEFT,
    "move_right": pygame.K_RIGHT,
    "rotate_cw": pygame.K_x,
    "rotate_ccw": pygame.K_z,
    "rotate_180": pygame.K_LSHIFT,
    "soft_drop": pygame.K_DOWN,
    "hard_drop": pygame.K_SPACE,
    "hold": pygame.K_c,
}

ACTION_LABELS = {
    "menu_next": "Menu Move",
    "confirm": "Confirm",
    "back": "Back",
    "retry_ready": "Retry / Ready",
    "move_left": "Move Left",
    "move_right": "Move Right",
    "rotate_cw": "Rotate Right",
    "rotate_ccw": "Rotate Left",
    "rotate_180": "Rotate 180",
    "soft_drop": "Soft Drop",
    "hard_drop": "Hard Drop",
    "hold": "Hold Piece",
}

CONTROL_GROUPS = [
    ("Common", ["menu_next", "confirm", "back", "retry_ready"]),
    ("Game", ["move_left", "move_right", "rotate_cw", "rotate_ccw", "rotate_180", "soft_drop", "hard_drop", "hold"]),
]


@dataclass(frozen=True)
class KeyBindings:
    menu_next: int = pygame.K_TAB
    confirm: int = pygame.K_RETURN
    back: int = pygame.K_ESCAPE
    retry_ready: int = pygame.K_r
    move_left: int = pygame.K_LEFT
    move_right: int = pygame.K_RIGHT
    rotate_cw: int = pygame.K_x
    rotate_ccw: int = pygame.K_z
    rotate_180: int = pygame.K_LSHIFT
    soft_drop: int = pygame.K_DOWN
    hard_drop: int = pygame.K_SPACE
    hold: int = pygame.K_c
