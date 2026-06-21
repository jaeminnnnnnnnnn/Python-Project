import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client.tetris.rules import TetrisGame
from server.app.rooms import RoomStore


def main() -> None:
    game = TetrisGame()
    game.move(-1, 0)
    game.rotate(1)
    game.hard_drop()

    store = RoomStore()
    room, first = store.create_room("Test Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    store.set_ready(room.id, second.id, True)
    store.leave_room(room.id, second.id)

    print("smoke ok")


if __name__ == "__main__":
    main()
