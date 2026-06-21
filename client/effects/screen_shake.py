class ScreenShake:
    def __init__(self) -> None:
        self.amount = 0.0

    def trigger(self, amount: float) -> None:
        self.amount = max(self.amount, amount)

