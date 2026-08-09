"""WebRTC video frame callback for live Rubik's cube face scanning."""

from __future__ import annotations

import queue
import cv2
import av
import numpy as np
from solver.color_classifier import classify_hsv

# Queue carries (samples, colors): list of 9 HSV tuples + list of 9 color names.
result_queue: queue.Queue = queue.Queue(maxsize=1)

# BGR colors for in-frame cell overlay rectangles
_OVERLAY_BGR: dict[str, tuple[int, int, int]] = {
    "White":  (255, 255, 255),
    "Yellow": (0,   220, 255),
    "Red":    (0,   30,  220),
    "Orange": (0,   140, 255),
    "Green":  (0,   180, 30),
    "Blue":   (220, 100, 30),
}


def make_scan_callback():
    """Return a WebRTC video frame callback with real-time color classification.

    On every frame the callback:
    1. Samples a small HSV patch at each of the 9 grid-cell centers.
    2. Classifies each patch with :func:`~solver.color_classifier.classify_hsv`.
    3. Draws a filled colored square + initial-letter label in each cell.
    4. Pushes ``(samples, colors)`` into :data:`result_queue`.

    Returns:
        A ``video_frame_callback`` compatible with ``streamlit_webrtc``.
    """
    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        h_img, w_img, _ = img.shape
        size = min(h_img, w_img)
        y0, x0 = (h_img - size) // 2, (w_img - size) // 2
        y1, x1 = y0 + size, x0 + size
        cell = size // 3
        margin = max(1, min(10, cell // 5))

        hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        samples: list[tuple[float, float, float]] = []
        colors: list[str] = []
        centers: list[tuple[int, int]] = []

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

        # Dim everything outside the scan grid
        dimmed = (img * 0.35).astype(np.uint8)
        dimmed[y0:y1, x0:x1] = img[y0:y1, x0:x1]
        img = dimmed

        # Draw per-cell colored overlays + letter labels
        sq = max(14, cell // 4)
        for (cx, cy), color_name in zip(centers, colors):
            bgr = _OVERLAY_BGR.get(color_name, (120, 120, 120))
            cv2.rectangle(img, (cx - sq, cy - sq), (cx + sq, cy + sq), bgr, -1)
            cv2.rectangle(img, (cx - sq, cy - sq), (cx + sq, cy + sq), (30, 30, 30), 1)
            label = color_name[0]
            text_color = (30, 30, 30) if color_name in ("White", "Yellow") else (230, 230, 230)
            font_scale = max(0.3, sq / 28.0)
            cv2.putText(
                img, label,
                (cx - sq // 3, cy + sq // 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, text_color, 1, cv2.LINE_AA,
            )

        # Grid lines
        cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), 2)
        for i in range(1, 3):
            cv2.line(img, (x0 + i * cell, y0), (x0 + i * cell, y1), (200, 200, 200), 1)
            cv2.line(img, (x0, y0 + i * cell), (x1, y0 + i * cell), (200, 200, 200), 1)

        # Push latest results — drop stale frame if queue is full
        if not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                pass
        result_queue.put((samples, colors))

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    return video_frame_callback