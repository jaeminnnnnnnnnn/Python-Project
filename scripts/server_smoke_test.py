import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client.net.api import ApiClient, ApiError


def main() -> None:
    api = ApiClient()
    created = api.create_room("Server Smoke", "Smoke")
    room = created["room"]
    player = created["player"]
    room_id = room["id"]
    player_id = player["id"]
    print(f"created room={room_id} player={player_id}")

    try:
        for index in range(10):
            fetched = api.get_room(room_id)
            print(f"get[{index}] players={len(fetched['players'])}")

        ready = api.set_ready(room_id, player_id, True)
        ready_player = next(player for player in ready["players"] if player["id"] == player_id)
        print(f"ready={ready_player['ready']}")

        fetched = api.get_room(room_id)
        print(f"final get players={len(fetched['players'])}")
    finally:
        try:
            api.leave_room(room_id, player_id)
            print("left")
        except ApiError as exc:
            print(f"leave failed: {exc}")


if __name__ == "__main__":
    main()
