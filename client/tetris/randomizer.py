import random
from collections import deque


class SevenBag:
    def __init__(self, seed: int | None = None) -> None:
        self.queue: deque[str] = deque()
        self.random = random.Random(seed)

    def next(self) -> str:
        if not self.queue:
            bag = list("IJLOSTZ")
            self.random.shuffle(bag)
            self.queue.extend(bag)
        return self.queue.popleft()

    def preview(self, count: int = 5) -> list[str]:
        while len(self.queue) < count:
            bag = list("IJLOSTZ")
            self.random.shuffle(bag)
            self.queue.extend(bag)
        return list(self.queue)[:count]
