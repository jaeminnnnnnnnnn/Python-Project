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
    "menu_next": "메뉴 이동",
    "confirm": "선택",
    "back": "뒤로",
    "retry_ready": "재시작 / 준비",
    "move_left": "왼쪽 이동",
    "move_right": "오른쪽 이동",
    "rotate_cw": "오른쪽 회전",
    "rotate_ccw": "왼쪽 회전",
    "rotate_180": "180도 회전",
    "soft_drop": "소프트 드롭",
    "hard_drop": "하드 드롭",
    "hold": "홀드",
}

CONTROL_GROUPS = [
    ("게임 조작", ["move_left", "move_right", "rotate_cw", "rotate_ccw", "rotate_180", "soft_drop", "hard_drop", "hold"]),
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
