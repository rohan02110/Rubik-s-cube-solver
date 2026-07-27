import streamlit as st

st.title("Rubik's Solver")
img = st.camera_input("Show a cube face")

if img is not None:
    with open("capture.jpg", "wb") as f:
        f.write(img.getbuffer())
    st.image(img)
    st.success("Saved!")