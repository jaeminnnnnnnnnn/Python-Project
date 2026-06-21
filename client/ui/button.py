from dataclasses import dataclass


@dataclass
class Button:
    label: str
    action: str
    selected: bool = False

