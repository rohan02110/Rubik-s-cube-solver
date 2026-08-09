"""Stateless HSV-range classifier for standard Rubik's cube sticker colors.

Eliminates the need for user calibration. Color ranges are tuned for the six
standard Rubik's cube sticker colors under typical indoor lighting.

OpenCV HSV space: H in [0, 179], S in [0, 255], V in [0, 255].
"""

from __future__ import annotations

# Representative HSV centers used by the fallback nearest-center metric.
_CENTERS: list[tuple[str, float, float, float]] = [
    ("White",   0.0,  15.0, 220.0),
    ("Yellow", 27.0, 210.0, 220.0),
    ("Red",     0.0, 200.0, 200.0),
    ("Orange", 13.0, 220.0, 220.0),
    ("Green",  58.0, 185.0, 175.0),
    ("Blue",  112.0, 200.0, 185.0),
]


def classify_hsv(h: float, s: float, v: float) -> str:
    """Classify an HSV pixel into one of 6 standard Rubik's cube color names.

    Priority order prevents overlap: White first (catches any low-saturation
    pixel regardless of hue noise), then Yellow, Red, Orange, Green, Blue.
    Falls back to nearest-center distance for edge cases.

    Args:
        h: Hue in [0, 179].
        s: Saturation in [0, 255].
        v: Value (brightness) in [0, 255].

    Returns:
        One of: "White", "Yellow", "Red", "Orange", "Green", "Blue".
    """
    # 1. White — very low saturation, high brightness (hue is irrelevant)
    if s < 70 and v > 130:
        return "White"

    # 2. Red — hue near 0° or near 180° (circular wrap-around, checked early)
    if (h <= 8.0 or h >= 168.0) and s > 100 and v > 80:
        return "Red"

    # 3. Orange — hue 8–22°, clearly saturated (checked before Yellow to avoid overlap)
    if 8.0 < h <= 22.0 and s > 100 and v > 80:
        return "Orange"

    # 4. Yellow — hue 22–40°, well saturated
    if 22.0 < h <= 40.0 and s > 80 and v > 100:
        return "Yellow"

    # 5. Green — hue 40–85°
    if 40.0 <= h <= 85.0 and s > 60 and v > 60:
        return "Green"

    # 6. Blue — hue 85–140°
    if 85.0 <= h <= 140.0 and s > 60 and v > 60:
        return "Blue"

    # Fallback: weighted nearest-center in HSV space
    return _nearest_center(h, s, v)


def _nearest_center(h: float, s: float, v: float) -> str:
    """Return the color name whose HSV center is closest to (h, s, v)."""
    best_name, best_dist = "White", float("inf")
    for name, ch, cs, cv in _CENTERS:
        dh = min(abs(h - ch), 180.0 - abs(h - ch)) / 90.0   # normalized, circular
        ds = abs(s - cs) / 255.0
        dv = abs(v - cv) / 255.0
        dist = dh * 2.0 + ds * 1.5 + dv
        if dist < best_dist:
            best_name, best_dist = name, dist
    return best_name
