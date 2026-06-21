from dataclasses import dataclass


@dataclass
class MatchState:
    room_id: str
    started: bool = False

