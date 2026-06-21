from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayInput:
    frame: int
    action: str

