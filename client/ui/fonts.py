from __future__ import annotations

from functools import lru_cache

import pygame

from client.paths import asset_path


KOREAN_FONT_NAMES = (
    "notosanskr",
    "noto sans kr",
    "noto sans cjk kr",
    "nanumgothic",
    "malgungothicsemilight",
    "malgungothic",
    "malgun gothic semilight",
    "malgun gothic",
    "applesdgothicneo",
    "applegothic",
    "gulim",
    "dotum",
    "unbatang",
)

BUNDLED_FONT_FILES = (
    "NotoSansKR-Regular.ttf",
    "NanumGothic.ttf",
    "MalgunGothic.ttf",
)


@lru_cache(maxsize=1)
def korean_font_path() -> str | None:
    for filename in BUNDLED_FONT_FILES:
        path = asset_path("fonts", filename)
        if path.exists():
            return str(path)
    return pygame.font.match_font(KOREAN_FONT_NAMES)


def game_font(size: int) -> pygame.font.Font:
    return pygame.font.Font(korean_font_path(), size)
