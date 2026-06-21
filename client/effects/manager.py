class EffectManager:
    def __init__(self) -> None:
        self.active: list[tuple[str, dict]] = []

    def spawn(self, name: str, **payload) -> None:
        self.active.append((name, payload))

    def clear(self) -> None:
        self.active.clear()

