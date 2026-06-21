import pytest

from server.app.rooms import RoomStore
from shared.errors import InvalidPasswordError, RoomFullError


def test_create_and_join_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    assert first.id != second.id
    assert len(room.players) == 2


def test_password_room_rejects_wrong_password() -> None:
    store = RoomStore()
    room, _ = store.create_room("Room", "pw", "A")
    with pytest.raises(InvalidPasswordError):
        store.join_room(room.id, "B", "bad")


def test_room_full() -> None:
    store = RoomStore()
    room, _ = store.create_room("Room", None, "A")
    store.join_room(room.id, "B", None)
    with pytest.raises(RoomFullError):
        store.join_room(room.id, "C", None)


def test_reset_match_clears_ready_and_started() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    store.set_ready(room.id, second.id, True)
    assert room.started
    assert room.match_seed is not None

    room = store.reset_match(room.id, first.id)
    assert not room.started
    assert room.match_seed is None
    assert all(not player.ready for player in room.players.values())


def test_match_seed_is_created_once_per_started_match() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    room = store.set_ready(room.id, second.id, True)
    seed = room.match_seed

    room = store.set_ready(room.id, first.id, True)

    assert room.match_seed == seed


def test_heartbeat_keeps_player_in_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    store.heartbeat(room.id, first.id)
    assert first.id in room.players
    assert first.id in room.last_seen


def test_room_survives_short_listing_gap() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")

    removed = store.cleanup_stale_players(now=room.last_seen[first.id] + 30.0)

    assert removed == []
    assert store.list_rooms()[0].id == room.id


def test_cleanup_removes_stale_player_and_resets_match() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    store.set_ready(room.id, second.id, True)
    room.last_seen[second.id] = 0.0

    store.cleanup_stale_players(now=RoomStore.stale_timeout_seconds + 1)

    assert second.id not in room.players
    assert not room.started
    assert all(not player.ready for player in room.players.values())


def test_cleanup_removes_empty_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    room.last_seen[first.id] = 0.0

    store.cleanup_stale_players(now=RoomStore.stale_timeout_seconds + 1)

    assert room.id not in store.rooms
