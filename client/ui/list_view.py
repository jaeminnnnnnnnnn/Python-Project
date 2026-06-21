class ListView:
    def __init__(self, items: list[str] | None = None) -> None:
        self.items = items or []
        self.selected = 0

    def move(self, delta: int) -> None:
        if self.items:
            self.selected = (self.selected + delta) % len(self.items)

