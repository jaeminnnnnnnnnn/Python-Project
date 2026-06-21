import pytest

from server.app.rooms import RoomStore
from shared.errors import InvalidPasswordError, RoomFullError


def test_create_and_join_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    assert first.id != second.id
    assert room.owner_id == first.id
    assert len(room.players) == 2


def test_owner_leave_keeps_room_when_other_player_remains() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)

    result = store.leave_room(room.id, first.id)

    assert result is room
    assert first.id not in room.players
    assert second.id in room.players
    assert room.id in store.rooms


def test_non_owner_leave_keeps_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)

    result = store.leave_room(room.id, second.id)

    assert result is room
    assert first.id in room.players
    assert second.id not in room.players
    assert room.id in store.rooms


def test_room_is_removed_when_last_player_leaves() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")

    result = store.leave_room(room.id, first.id)

    assert result is None
    assert room.id not in store.rooms


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


def test_ready_recovers_missing_player_when_room_has_space() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    room.players.pop(first.id)
    room.last_seen.pop(first.id)

    room = store.set_ready(room.id, first.id, True)

    assert first.id in room.players
    assert room.players[first.id].ready


def test_room_survives_without_heartbeat() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")

    removed = store.cleanup_stale_players(now=999999.0)

    assert removed == []
    assert store.list_rooms()[0].id == room.id


def test_cleanup_does_not_remove_stale_player_or_reset_match() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    _, second = store.join_room(room.id, "B", None)
    store.set_ready(room.id, first.id, True)
    store.set_ready(room.id, second.id, True)
    room.last_seen[second.id] = 0.0

    store.cleanup_stale_players(now=999999.0)

    assert second.id in room.players
    assert room.started
    assert all(player.ready for player in room.players.values())


def test_cleanup_does_not_remove_empty_room() -> None:
    store = RoomStore()
    room, first = store.create_room("Room", None, "A")
    room.last_seen[first.id] = 0.0

    store.cleanup_stale_players(now=999999.0)

    assert room.id in store.rooms
