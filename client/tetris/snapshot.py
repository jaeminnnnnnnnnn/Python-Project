from client.tetris.board import HEIGHT, WIDTH
from client.tetris.rules import TetrisGame


def game_snapshot(game: TetrisGame) -> dict:
    grid = [row[:] for row in game.board.grid]
    ghost_cells = [
        (x, y)
        for x, y in game.ghost_piece().cells
        if 0 <= x < WIDTH and 0 <= y < HEIGHT
    ]
    for x, y in game.current.cells:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            grid[y][x] = game.current.kind
    return {
        "grid": grid,
        "ghost": ghost_cells,
        "score": game.score,
        "lines": game.lines,
        "level": game.level,
        "hold": game.hold_piece,
        "next": game.next_pieces,
        "game_over": game.game_over,
        "combo": game.combo,
        "back_to_back": game.back_to_back,
    }
