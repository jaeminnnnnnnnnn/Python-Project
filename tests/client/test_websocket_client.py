from client.net.websocket import RoomSocketClient


def test_match_state_send_drops_stale_state_messages() -> None:
    client = RoomSocketClient("room-1")

    client.send({"type": "match.state", "state": {"score": 1}})
    client.send({"type": "match.garbage", "lines": 2})
    client.send({"type": "match.state", "state": {"score": 2}})

    queued = []
    while not client.outgoing.empty():
        queued.append(client.outgoing.get_nowait())

    assert queued == [
        {"type": "match.garbage", "lines": 2},
        {"type": "match.state", "state": {"score": 2}},
    ]
