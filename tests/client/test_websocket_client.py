from client.net.websocket import RoomSocketClient


def test_visual_sync_send_drops_stale_visual_messages() -> None:
    client = RoomSocketClient("room-1")

    client.send({"type": "match.state", "state": {"score": 1}})
    client.send({"type": "match.garbage", "lines": 2})
    client.send({"type": "match.input", "action": "move_left", "state": {"score": 2}})

    queued = []
    while not client.outgoing.empty():
        queued.append(client.outgoing.get_nowait())

    assert queued == [
        {"type": "match.garbage", "lines": 2},
        {"type": "match.input", "action": "move_left", "state": {"score": 2}},
    ]


def test_put_back_preserves_messages_before_existing_queue() -> None:
    client = RoomSocketClient("room-1")
    client.messages.put({"type": "room.state"})

    client.put_back([{"type": "match.state", "state": {"score": 10}}])

    assert client.drain() == [
        {"type": "match.state", "state": {"score": 10}},
        {"type": "room.state"},
    ]


def test_drain_drops_stale_visual_messages_per_player() -> None:
    client = RoomSocketClient("room-1")
    client.messages.put({"type": "match.state", "player_id": "p1", "state": {"score": 1}})
    client.messages.put({"type": "match.garbage", "target_id": "p2", "lines": 2})
    client.messages.put({"type": "match.input", "player_id": "p1", "state": {"score": 2}})
    client.messages.put({"type": "match.state", "player_id": "p1", "state": {"score": 3}})
    client.messages.put({"type": "match.state", "player_id": "p2", "state": {"score": 4}})

    assert client.drain() == [
        {"type": "match.garbage", "target_id": "p2", "lines": 2},
        {"type": "match.input", "player_id": "p1", "state": {"score": 2}},
        {"type": "match.state", "player_id": "p1", "state": {"score": 3}},
        {"type": "match.state", "player_id": "p2", "state": {"score": 4}},
    ]
