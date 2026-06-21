from client.game.input import CONTROL_GROUPS


def test_control_groups_only_include_gameplay_bindings() -> None:
    actions = [action for _, group_actions in CONTROL_GROUPS for action in group_actions]

    assert "back" not in actions
    assert "confirm" not in actions
    assert "menu_next" not in actions
    assert actions == [
        "move_left",
        "move_right",
        "rotate_cw",
        "rotate_ccw",
        "rotate_180",
        "soft_drop",
        "hard_drop",
        "hold",
    ]
