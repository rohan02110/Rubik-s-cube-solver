RANGES = {
    "white":  [((0, 0, 180), (179, 40, 255))],
    "yellow": [((20, 80, 80), (35, 255, 255))],
    "red":    [((0, 100, 80), (8, 255, 255)), ((170, 100, 80), (179, 255, 255))],
    "orange": [((9, 120, 120), (19, 255, 255))],
    "green":  [((40, 60, 60), (80, 255, 255))],
    "blue":   [((90, 60, 60), (130, 255, 255))],
}

def classify(h, s, v):
    for name, ranges in RANGES.items():
        for lo, hi in ranges:
            if lo[0] <= h <= hi[0] and lo[1] <= s <= hi[1] and lo[2] <= v <= hi[2]:
                return name
    return "unknown"