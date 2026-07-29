import numpy as np
import cv2
import av
import queue

result_queue = queue.Queue(maxsize=1)

def make_callback():
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape
        size = min(h, w)
        y0, x0 = (h - size) // 2, (w - size) // 2
        y1, x1 = y0 + size, x0 + size
        cell = size // 3

        hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        samples = []
        centers = []
        for row in range(3):
            for col in range(3):
                cy = y0 + row * cell + cell // 2
                cx = x0 + col * cell + cell // 2
                patch = hsv_full[cy-10:cy+10, cx-10:cx+10].reshape(-1, 3)
                hh, ss, vv = patch.mean(axis=0)
                samples.append((hh, ss, vv))
                centers.append((cx, cy))

        # dim everything outside the grid square
        dimmed = (img * 0.3).astype(np.uint8)
        dimmed[y0:y1, x0:x1] = img[y0:y1, x0:x1]
        img = dimmed

        # live color swatches
        for (cx, cy), (hh, ss, vv) in zip(centers, samples):
            swatch_bgr = cv2.cvtColor(np.uint8([[[hh, ss, vv]]]), cv2.COLOR_HSV2BGR)[0][0]
            cv2.rectangle(img, (cx-15, cy-15), (cx+15, cy+15),
                          tuple(int(c) for c in swatch_bgr), -1)

        # grid lines
        cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), 2)
        for i in range(1, 3):
            cv2.line(img, (x0 + i*cell, y0), (x0 + i*cell, y1), (255, 255, 255), 1)
            cv2.line(img, (x0, y0 + i*cell), (x1, y0 + i*cell), (255, 255, 255), 1)

        if not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                pass
        result_queue.put(samples)

        return av.VideoFrame.from_ndarray(img, format="bgr24")
    return video_frame_callback

legend_queue = queue.Queue(maxsize=1)

def make_legend_callback():
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape
        box = min(h, w) // 3
        cy, cx = h // 2, w // 2

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        patch = hsv[cy-15:cy+15, cx-15:cx+15].reshape(-1, 3)
        sample = tuple(patch.mean(axis=0))

        cv2.rectangle(img, (cx-box//2, cy-box//2), (cx+box//2, cy+box//2), (255, 255, 255), 2)

        if not legend_queue.empty():
            try:
                legend_queue.get_nowait()
            except queue.Empty:
                pass
        legend_queue.put(sample)

        return av.VideoFrame.from_ndarray(img, format="bgr24")
    return video_frame_callback