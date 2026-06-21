from dataclasses import asdict, dataclass, field

from client.game.input import DEFAULT_KEY_BINDINGS


@dataclass
class Settings:
    music_enabled: bool = True
    sfx_enabled: bool = True
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    key_bindings: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_KEY_BINDINGS))

    def to_dict(self) -> dict:
        return asdict(self)
