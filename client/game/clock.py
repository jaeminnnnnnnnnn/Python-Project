class StepTimer:
    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.elapsed = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        if self.elapsed >= self.interval:
            self.elapsed -= self.interval
            return True
        return False

    def reset(self) -> None:
        self.elapsed = 0.0

