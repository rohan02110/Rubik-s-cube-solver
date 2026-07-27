import streamlit as st
import numpy as np
import cv2
from PIL import Image

st.title("HSV Calibration")
img_file = st.camera_input("Photo of one cube face")

if img_file:
    rgb = np.array(Image.open(img_file).convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    h_min, h_max = st.slider("Hue", 0, 179, (0, 179))
    s_min, s_max = st.slider("Saturation", 0, 255, (0, 255))
    v_min, v_max = st.slider("Value", 0, 255, (0, 255))

    mask = cv2.inRange(hsv, (h_min, s_min, v_min), (h_max, s_max, v_max))
    st.image(rgb, caption="Original")
    st.image(mask, caption="Mask")