from __future__ import annotations

import random

from client.tetris.piece import Piece


WIDTH = 10
HEIGHT = 20


class Board:
    def __init__(self) -> None:
        self.grid: list[list[str | None]] = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]

    def collides(self, piece: Piece) -> bool:
        for x, y in piece.cells:
            if x < 0 or x >= WIDTH or y >= HEIGHT:
                return True
            if y >= 0 and self.grid[y][x] is not None:
                return True
        return False

    def lock(self, piece: Piece) -> None:
        for x, y in piece.cells:
            if 0 <= y < HEIGHT:
                self.grid[y][x] = piece.kind

    def clear_lines(self) -> int:
        remaining = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = HEIGHT - len(remaining)
        self.grid = [[None for _ in range(WIDTH)] for _ in range(cleared)] + remaining
        return cleared

    def is_blocked(self, piece: Piece) -> bool:
        return self.collides(piece)

    def add_garbage_lines(self, count: int, hole: int | None = None) -> None:
        for _ in range(max(count, 0)):
            garbage_hole = random.randrange(WIDTH) if hole is None else hole % WIDTH
            row = ["G" for _ in range(WIDTH)]
            row[garbage_hole] = None
            self.grid.pop(0)
            self.grid.append(row)
