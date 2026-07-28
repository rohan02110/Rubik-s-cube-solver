import numpy as np
from sklearn.cluster import KMeans

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
    color_to_face = {faces[f][4]: f for f in STRING_ORDER}
    return "".join(color_to_face[c] for f in STRING_ORDER for c in faces[f])