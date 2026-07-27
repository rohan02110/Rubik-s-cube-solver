import streamlit as st
from solver.face_scan import scan_face

FACES = ["U", "R", "F", "D", "L", "B"]

if "faces" not in st.session_state:
    st.session_state.faces = {}

st.title("Rubik's Solver")

for f in FACES:
    st.subheader(f"{f} face")
    img_file = st.camera_input(f"Show the {f} face", key=f)
    if img_file:
        labels, crop = scan_face(img_file)
        st.image(crop, width=150)
        st.write(labels)
        st.session_state.faces[f] = labels

if len(st.session_state.faces) == 6:
    st.success("All 6 faces scanned")

from solver.cube_solver import build_cubestring

if len(st.session_state.faces) == 6:
    cubestring = build_cubestring(st.session_state.faces)
    st.code(cubestring)

    import kociemba

if len(st.session_state.faces) == 6:
    cubestring = build_cubestring(st.session_state.faces)
    st.code(cubestring)

    if st.button("Solve"):
        try:
            moves = kociemba.solve(cubestring)
            st.write(moves.split())
        except Exception:
            st.error("Invalid cube state — rescan a face and try again.")

    if st.button("Rescan"):
        st.session_state.faces = {}
        st.rerun()