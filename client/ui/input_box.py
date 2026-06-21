class InputBox:
    def __init__(self, text: str = "") -> None:
        self.text = text

    def append(self, value: str) -> None:
        self.text += value

    def backspace(self) -> None:
        self.text = self.text[:-1]

