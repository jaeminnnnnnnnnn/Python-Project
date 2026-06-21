from client.player_labels import player_label


def test_player_label_uses_room_order() -> None:
    room = {"players": [{"id": "a"}, {"id": "b"}]}
    assert player_label(room, "a") == "P1"
    assert player_label(room, "b") == "P2"
    assert player_label(room, "missing") == "P?"

