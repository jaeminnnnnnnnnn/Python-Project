LINE_SCORES = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


def score_for_lines(lines: int, level: int) -> int:
    return LINE_SCORES.get(lines, 0) * max(level, 1)

