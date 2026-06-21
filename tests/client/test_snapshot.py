from client.tetris.piece import Piece
from client.tetris.rules import TetrisGame
from client.tetris.snapshot import game_snapshot


def test_game_snapshot_includes_active_piece_inside_visible_board() -> None:
    game = TetrisGame()
    game.current = Piece("T", x=4, y=0)

    snapshot = game_snapshot(game)

    assert any(cell == "T" for row in snapshot["grid"] for cell in row)
    assert all(y >= 0 for _, y in snapshot["ghost"])


def test_game_snapshot_excludes_cells_above_board() -> None:
    game = TetrisGame()
    game.current = Piece("I", x=4, y=0, rotation=1)

    snapshot = game_snapshot(game)

    assert all(len(row) == 10 for row in snapshot["grid"])
