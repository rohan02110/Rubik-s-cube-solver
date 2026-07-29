import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict

STRING_ORDER = ["U", "R", "F", "D", "L", "B"]

def cluster_faces(face_hsv):
    all_samples = [s for f in STRING_ORDER for s in face_hsv[f]]
    feats = []
    for h, s, v in all_samples:
        rad = np.deg2rad(float(h) * 2)
        feats.append([np.cos(rad), np.sin(rad), float(s) / 255])
    labels = KMeans(n_clusters=6, n_init=10, random_state=0).fit_predict(np.array(feats))
    result, i = {}, 0
    for f in STRING_ORDER:
        result[f] = list(labels[i:i+9])
        i += 9
    return result

def build_cubestring(faces):
    centers = [faces[f][4] for f in STRING_ORDER]
    if len(set(centers)) != 6:
        raise ValueError("two faces were detected as the same color — a center sticker was likely misread")
    color_to_face = dict(zip(centers, STRING_ORDER))
    return "".join(color_to_face[c] for f in STRING_ORDER for c in faces[f])

def compute_cluster_colors(face_hsv, faces):
    groups = defaultdict(list)
    for f in STRING_ORDER:
        for hsv, c in zip(face_hsv[f], faces[f]):
            groups[c].append(hsv)
    colors = {}
    for c, samples in groups.items():
        h, s, v = np.mean(samples, axis=0)
        rgb = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2RGB)[0][0]
        colors[c] = tuple(int(x) for x in rgb)
    return colors

def guess_name(h, s, v):
    if s < 50:
        return "White"
    if h < 10 or h > 170:
        return "Red"
    if h < 20:
        return "Orange"
    if h < 35:
        return "Yellow"
    if h < 85:
        return "Green"
    return "Blue"

def cluster_names(face_hsv, faces):
    groups = defaultdict(list)
    for f in STRING_ORDER:
        for hsv, c in zip(face_hsv[f], faces[f]):
            groups[c].append(hsv)
    return {c: guess_name(*np.mean(samples, axis=0)) for c, samples in groups.items()}