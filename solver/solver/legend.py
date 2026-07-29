import numpy as np

def feat(h, s, v):
    rad = np.deg2rad(float(h) * 2)
    return np.array([np.cos(rad), np.sin(rad), float(s) / 255])

def classify_to_legend(h, s, v, legend):
    target = feat(h, s, v)
    best_name, best_dist = None, None
    for name, (lh, ls, lv) in legend.items():
        dist = np.linalg.norm(target - feat(lh, ls, lv))
        if best_dist is None or dist < best_dist:
            best_name, best_dist = name, dist
    return best_name