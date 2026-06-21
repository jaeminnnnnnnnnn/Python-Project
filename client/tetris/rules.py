from __future__ import annotations

from dataclasses import dataclass

from client.tetris.board import Board
from client.tetris.piece import Piece
from client.tetris.randomizer import SevenBag
from client.tetris.scoring import score_for_lines
from client.tetris.srs import kicks_for
from client.tetris.garbage import garbage_for_lines, is_back_to_back_clear


@dataclass
class StepResult:
    locked: bool = False
    lines_cleared: int = 0
    game_over: bool = False
    attack: int = 0


class TetrisGame:
    def __init__(self, seed: int | None = None) -> None:
        self.board = Board()
        self.randomizer = SevenBag(seed)
        self.current = Piece(self.randomizer.next())
        self.hold_piece: str | None = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.combo = -1
        self.back_to_back = False

    @property
    def next_pieces(self) -> list[str]:
        return self.randomizer.preview()

    def move(self, dx: int, dy: int) -> bool:
        candidate = self.current.moved(dx, dy)
        if self.board.collides(candidate):
            return False
        self.current = candidate
        return True

    def rotate(self, amount: int) -> bool:
        from_rotation = self.current.rotation % 4
        candidate = self.current.rotated(amount)
        to_rotation = candidate.rotation % 4
        for kick_x, kick_y in kicks_for(self.current.kind, from_rotation, to_rotation):
            kicked = candidate.moved(kick_x, -kick_y)
            if not self.board.collides(kicked):
                self.current = kicked
                return True
        return False

    def ghost_piece(self) -> Piece:
        ghost = self.current
        while not self.board.collides(ghost.moved(0, 1)):
            ghost = ghost.moved(0, 1)
        return ghost

    def hard_drop(self) -> StepResult:
        while self.move(0, 1):
            self.score += 2
        return self.lock_piece()

    def soft_drop(self) -> StepResult:
        if self.move(0, 1):
            self.score += 1
            return StepResult()
        return self.lock_piece()

    def tick(self) -> StepResult:
        if self.game_over:
            return StepResult(game_over=True)
        if self.move(0, 1):
            return StepResult()
        return self.lock_piece()

    def hold(self) -> None:
        if not self.can_hold:
            return
        current_kind = self.current.kind
        if self.hold_piece is None:
            self.hold_piece = current_kind
            self.current = Piece(self.randomizer.next())
        else:
            self.current = Piece(self.hold_piece)
            self.hold_piece = current_kind
        self.can_hold = False
        if self.board.collides(self.current):
            self.game_over = True

    def lock_piece(self) -> StepResult:
        self.board.lock(self.current)
        cleared = self.board.clear_lines()
        if cleared:
            self.combo += 1
        else:
            self.combo = -1
        qualifies_b2b = is_back_to_back_clear(cleared)
        attack = garbage_for_lines(cleared, self.combo, self.back_to_back and qualifies_b2b)
        if cleared:
            self.back_to_back = qualifies_b2b
        self.lines += cleared
        self.level = self.lines // 10 + 1
        self.score += score_for_lines(cleared, self.level)
        self.current = Piece(self.randomizer.next())
        self.can_hold = True
        self.game_over = self.board.is_blocked(self.current)
        return StepResult(locked=True, lines_cleared=cleared, game_over=self.game_over, attack=attack)

    def add_garbage(self, count: int, hole: int | None = None) -> None:
        if count <= 0 or self.game_over:
            return
        self.board.add_garbage_lines(count, hole)
        if self.board.collides(self.current):
            self.game_over = True
