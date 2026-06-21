from dataclasses import dataclass
import math


@dataclass
class Countdown:
    duration: float = 3.0
    remaining: float | None = None

    def __post_init__(self) -> None:
        if self.remaining is None:
            self.remaining = self.duration

    def reset(self) -> None:
        self.remaining = self.duration

    def update(self, dt: float) -> None:
        self.remaining = max(0.0, self.remaining - dt)

    @property
    def active(self) -> bool:
        return self.remaining > 0.0

    @property
    def label(self) -> str:
        if not self.active:
            return ""
        return str(max(1, math.ceil(self.remaining)))
