import numpy as np
import cv2
from PIL import Image

def sample_face_hsv(img_file):
    rgb = np.array(Image.open(img_file).convert("RGB"))
    h, w, _ = rgb.shape
    size = min(h, w)
    y0, x0 = (h - size) // 2, (w - size) // 2
    crop = cv2.resize(rgb[y0:y0+size, x0:x0+size], (300, 300))
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    samples = []
    for row in range(3):
        for col in range(3):
            cy, cx = row * 100 + 50, col * 100 + 50
            patch = hsv[cy-10:cy+10, cx-10:cx+10].reshape(-1, 3)
            samples.append(tuple(patch.mean(axis=0)))
    return samples, crop