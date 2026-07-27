import streamlit as st
from solver.face_scan import scan_face

st.title("Rubik's Solver")
img_file = st.camera_input("Show a cube face")

if img_file:
    labels, crop = scan_face(img_file)
    st.image(crop, width=200)
    st.write(labels)