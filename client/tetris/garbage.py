BASE_LINE_ATTACK = {0: 0, 1: 0, 2: 1, 3: 2, 4: 4}


def combo_bonus(combo: int) -> int:
    if combo < 1:
        return 0
    if combo <= 2:
        return 1
    if combo <= 4:
        return 2
    if combo <= 6:
        return 3
    return 4


def garbage_for_lines(lines: int, combo: int = -1, back_to_back: bool = False) -> int:
    attack = BASE_LINE_ATTACK.get(lines, 0)
    if back_to_back and lines == 4:
        attack += 1
    attack += combo_bonus(combo)
    return attack


def is_back_to_back_clear(lines: int) -> bool:
    return lines == 4
