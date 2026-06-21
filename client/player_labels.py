def player_label(room: dict, player_id: str) -> str:
    for index, player in enumerate(room.get("players", []), start=1):
        if player.get("id") == player_id:
            return f"P{index}"
    return "P?"

