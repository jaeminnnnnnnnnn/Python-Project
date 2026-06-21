from dataclasses import dataclass


@dataclass(frozen=True)
class RepeatTiming:
    delay: float
    interval: float


class RepeatController:
    def __init__(self, timings: dict[str, RepeatTiming]) -> None:
        self.timings = timings
        self.remaining: dict[str, float] = {}

    def press(self, action: str) -> None:
        timing = self.timings.get(action)
        if timing and action not in self.remaining:
            self.remaining[action] = timing.delay

    def release(self, action: str) -> None:
        self.remaining.pop(action, None)

    def reset(self) -> None:
        self.remaining.clear()

    def update(self, dt: float) -> list[str]:
        actions: list[str] = []
        for action in list(self.remaining):
            timing = self.timings[action]
            self.remaining[action] -= dt
            while self.remaining[action] <= 0.0:
                actions.append(action)
                self.remaining[action] += timing.interval
        return actions


GAME_REPEAT = {
    "move_left": RepeatTiming(delay=0.14, interval=0.045),
    "move_right": RepeatTiming(delay=0.14, interval=0.045),
    "soft_drop": RepeatTiming(delay=0.06, interval=0.035),
}
