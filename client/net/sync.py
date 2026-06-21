class SyncBuffer:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def push(self, message: dict) -> None:
        self.messages.append(message)

    def drain(self) -> list[dict]:
        messages = self.messages
        self.messages = []
        return messages

