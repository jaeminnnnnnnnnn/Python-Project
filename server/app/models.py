from dataclasses import dataclass, field
import random
import time
from uuid import uuid4

from shared.schemas import Player, RoomPublic


@dataclass
class Room:
    title: str
    password: str | None
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    players: dict[str, Player] = field(default_factory=dict)
    last_seen: dict[str, float] = field(default_factory=dict)
    max_players: int = 2
    started: bool = False
    match_seed: int | None = None

    def touch(self, player_id: str, now: float | None = None) -> None:
        self.last_seen[player_id] = time.time() if now is None else now

    def start_match(self) -> None:
        self.started = True
        self.match_seed = random.randrange(1, 2**31)

    @property
    def has_password(self) -> bool:
        return bool(self.password)

    def public(self) -> RoomPublic:
        return RoomPublic(
            id=self.id,
            title=self.title,
            has_password=self.has_password,
            players=list(self.players.values()),
            max_players=self.max_players,
            started=self.started,
            match_seed=self.match_seed,
        )
