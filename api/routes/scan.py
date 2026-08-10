import base64
import cv2
import numpy as np
from flask import Blueprint, request, jsonify

from solver.color_classifier import classify_hsv

scan_bp = Blueprint('scan', __name__)

# BGR colors for in-frame cell overlay rectangles
_OVERLAY_BGR = {
    "White":  (255, 255, 255),
    "Yellow": (0,   220, 255),
    "Red":    (0,   30,  220),
    "Orange": (0,   140, 255),
    "Green":  (0,   180, 30),
    "Blue":   (220, 100, 30),
}

@scan_bp.route('/scan-frame', methods=['POST'])
def scan_frame():
    if 'frame' not in request.files:
        return jsonify({"error": "No frame file provided"}), 400

    file = request.files['frame']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Failed to decode image"}), 400

    h_img, w_img, _ = img.shape
    size = min(h_img, w_img)
    y0, x0 = (h_img - size) // 2, (w_img - size) // 2
    y1, x1 = y0 + size, x0 + size
    cell = size // 3
    margin = max(1, min(10, cell // 5))

    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    samples = []
    colors = []
    centers = []

    for row in range(3):
        for col in range(3):
            cy = y0 + row * cell + cell // 2
            cx = x0 + col * cell + cell // 2
            patch = hsv_full[
                max(0, cy - margin):min(h_img, cy + margin),
                max(0, cx - margin):min(w_img, cx + margin),
            ].reshape(-1, 3)
            hh, ss, vv = float(patch[:, 0].mean()), float(patch[:, 1].mean()), float(patch[:, 2].mean())
            samples.append((hh, ss, vv))
            colors.append(classify_hsv(hh, ss, vv))
            centers.append((cx, cy))

    return jsonify({
        "colors": colors
    }), 200
