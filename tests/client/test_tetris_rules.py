from client.tetris.board import Board, WIDTH
from client.tetris.piece import Piece
from client.tetris.rules import TetrisGame
from client.tetris.garbage import garbage_for_lines


def test_piece_cannot_move_past_left_wall() -> None:
    game = TetrisGame()
    for _ in range(WIDTH):
        game.move(-1, 0)
    assert not game.move(-1, 0)


def test_clear_full_line() -> None:
    board = Board()
    board.grid[-1] = ["I" for _ in range(WIDTH)]
    assert board.clear_lines() == 1
    assert all(cell is None for cell in board.grid[0])


def test_hard_drop_locks_piece() -> None:
    game = TetrisGame()
    result = game.hard_drop()
    assert result.locked
    assert any(cell is not None for row in game.board.grid for cell in row)


def test_rotation_returns_piece() -> None:
    piece = Piece("T")
    assert piece.rotated(1).rotated(-1).rotation == piece.rotation


def test_add_garbage_lines() -> None:
    game = TetrisGame()
    game.add_garbage(2, hole=3)
    assert game.board.grid[-1][3] is None
    assert game.board.grid[-2][3] is None
    assert sum(cell == "G" for cell in game.board.grid[-1]) == WIDTH - 1


def test_garbage_for_lines() -> None:
    assert garbage_for_lines(1) == 0
    assert garbage_for_lines(2) == 1
    assert garbage_for_lines(3) == 2
    assert garbage_for_lines(4) == 4
    assert garbage_for_lines(4, combo=0, back_to_back=True) == 5
    assert garbage_for_lines(2, combo=3) == 3


def test_ghost_piece_lands_on_floor() -> None:
    game = TetrisGame()
    ghost = game.ghost_piece()
    assert game.board.collides(ghost.moved(0, 1))
    assert not game.board.collides(ghost)


def test_srs_rotation_kicks_near_wall() -> None:
    game = TetrisGame()
    game.current = Piece("T", x=0, y=2)
    assert game.rotate(1)
    assert not game.board.collides(game.current)


def test_combo_increases_attack_after_consecutive_clears() -> None:
    game = TetrisGame()
    game.combo = 2
    game.back_to_back = False
    assert garbage_for_lines(2, combo=game.combo) == 2


def test_seeded_games_have_same_piece_sequence() -> None:
    first = TetrisGame(seed=1234)
    second = TetrisGame(seed=1234)
    first_sequence = [first.current.kind] + [first.randomizer.next() for _ in range(10)]
    second_sequence = [second.current.kind] + [second.randomizer.next() for _ in range(10)]
    assert first_sequence == second_sequence
