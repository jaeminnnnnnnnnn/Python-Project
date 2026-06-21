from server.app.rooms import RoomStore


def test_room_starts_when_two_players_ready() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    room = store.set_ready(room.id, second.id, True)
    assert room.started

