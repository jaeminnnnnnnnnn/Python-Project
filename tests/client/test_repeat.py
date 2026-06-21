from client.game.repeat import RepeatController, RepeatTiming


def test_repeat_controller_waits_for_initial_delay() -> None:
    repeat = RepeatController({"move_left": RepeatTiming(delay=0.2, interval=0.05)})

    repeat.press("move_left")

    assert repeat.update(0.1) == []
    assert repeat.update(0.1) == ["move_left"]


def test_repeat_controller_emits_multiple_actions_for_large_delta() -> None:
    repeat = RepeatController({"soft_drop": RepeatTiming(delay=0.1, interval=0.05)})

    repeat.press("soft_drop")

    assert repeat.update(0.21) == ["soft_drop", "soft_drop", "soft_drop"]


def test_repeat_controller_release_stops_repeating() -> None:
    repeat = RepeatController({"move_right": RepeatTiming(delay=0.1, interval=0.05)})

    repeat.press("move_right")
    repeat.release("move_right")

    assert repeat.update(1.0) == []
