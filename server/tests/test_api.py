from fastapi.testclient import TestClient
import asyncio

import server.app.websocket as websocket_module
from server.app.state import room_store
from server.main import app


client = TestClient(app)


def setup_function() -> None:
    room_store.rooms.clear()


def test_room_api_flow() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]

    rooms = client.get("/rooms").json()
    assert len(rooms) == 1
    assert rooms[0]["id"] == room_id
    assert rooms[0]["owner_id"] == first_id

    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]

    room = client.post(f"/rooms/{room_id}/ready", json={"player_id": first_id, "ready": True}).json()
    assert not room["started"]

    room = client.post(f"/rooms/{room_id}/ready", json={"player_id": second_id, "ready": True}).json()
    assert room["started"]
    assert room["match_seed"] is not None

    room = client.get(f"/rooms/{room_id}").json()
    assert len(room["players"]) == 2

    room = client.post(f"/rooms/{room_id}/leave", json={"player_id": second_id}).json()
    assert len(room["players"]) == 1
    assert not room["started"]


def test_owner_leave_api_keeps_room_when_other_player_remains() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]
    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]

    response = client.post(f"/rooms/{room_id}/leave", json={"player_id": first_id})

    assert response.status_code == 200
    room = response.json()
    assert [player["id"] for player in room["players"]] == [second_id]
    assert client.get("/rooms").json()[0]["id"] == room_id


def test_last_player_leave_api_removes_room() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]

    response = client.post(f"/rooms/{room_id}/leave", json={"player_id": first_id})

    assert response.status_code == 200
    assert response.json() is None
    assert client.get("/rooms").json() == []


def test_room_reset_api_clears_match_state() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]
    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]
    client.post(f"/rooms/{room_id}/ready", json={"player_id": first_id, "ready": True})
    room = client.post(f"/rooms/{room_id}/ready", json={"player_id": second_id, "ready": True}).json()
    assert room["started"]

    room = client.post(f"/rooms/{room_id}/reset", json={"player_id": first_id}).json()
    assert not room["started"]
    assert all(not player["ready"] for player in room["players"])


def test_room_heartbeat_api() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    player_id = created["player"]["id"]

    response = client.post(f"/rooms/{room_id}/heartbeat", json={"player_id": player_id})

    assert response.status_code == 200
    assert response.json()["id"] == room_id


def test_room_heartbeat_missing_player_returns_404() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]

    response = client.post(f"/rooms/{room_id}/heartbeat", json={"player_id": "missing"})

    assert response.status_code == 404


def test_join_missing_room_returns_404() -> None:
    response = client.post("/rooms/missing/join", json={"player_name": "B"})
    assert response.status_code == 404


def test_room_websocket_receives_state_updates() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    player_id = created["player"]["id"]

    with client.websocket_connect(f"/ws/rooms/{room_id}") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "room.state"
        assert initial["room"]["id"] == room_id

        client.post(f"/rooms/{room_id}/ready", json={"player_id": player_id, "ready": True})
        updated = websocket.receive_json()
        assert updated["type"] == "room.state"
        assert updated["room"]["players"][0]["ready"]


def test_room_websocket_broadcasts_match_state() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    player_id = created["player"]["id"]

    with client.websocket_connect(f"/ws/rooms/{room_id}") as sender:
        with client.websocket_connect(f"/ws/rooms/{room_id}") as receiver:
            sender.receive_json()
            receiver.receive_json()
            sender.send_json({"type": "match.state", "player_id": player_id, "state": {"score": 10}})
            message = receiver.receive_json()
            assert message["type"] == "match.state"
            assert message["player_id"] == player_id
            assert message["state"]["score"] == 10


def test_room_websocket_broadcasts_garbage_and_result() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]
    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]

    with client.websocket_connect(f"/ws/rooms/{room_id}") as sender:
        with client.websocket_connect(f"/ws/rooms/{room_id}") as receiver:
            sender.receive_json()
            receiver.receive_json()
            sender.send_json({"type": "match.garbage", "player_id": first_id, "target_id": second_id, "lines": 2, "hole": 4})
            garbage = receiver.receive_json()
            assert garbage["type"] == "match.garbage"
            assert garbage["target_id"] == second_id
            assert garbage["lines"] == 2

            sender.send_json({"type": "match.result", "winner_id": first_id, "loser_id": second_id})
            result = receiver.receive_json()
            assert result["type"] == "match.result"
            assert result["winner_id"] == first_id
            assert result["loser_id"] == second_id


def test_room_websocket_disconnect_before_match_keeps_player() -> None:
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]
    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]

    with client.websocket_connect(f"/ws/rooms/{room_id}?player_id={first_id}") as survivor:
        survivor.receive_json()
        with client.websocket_connect(f"/ws/rooms/{room_id}?player_id={second_id}") as leaving:
            leaving.receive_json()

        room = client.get(f"/rooms/{room_id}").json()
        assert {player["id"] for player in room["players"]} == {first_id, second_id}


def test_disconnect_cleanup_during_match_removes_player(monkeypatch) -> None:
    monkeypatch.setattr(websocket_module, "DISCONNECT_GRACE_SECONDS", 0.01)
    created = client.post("/rooms", json={"title": "Room", "player_name": "A"}).json()
    room_id = created["room"]["id"]
    first_id = created["player"]["id"]
    joined = client.post(f"/rooms/{room_id}/join", json={"player_name": "B"}).json()
    second_id = joined["player"]["id"]
    client.post(f"/rooms/{room_id}/ready", json={"player_id": first_id, "ready": True})
    client.post(f"/rooms/{room_id}/ready", json={"player_id": second_id, "ready": True})

    asyncio.run(websocket_module.remove_disconnected_player_after_grace(room_id, second_id))

    room = client.get(f"/rooms/{room_id}").json()
    assert [player["id"] for player in room["players"]] == [first_id]
