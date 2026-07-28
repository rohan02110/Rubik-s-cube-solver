import streamlit as st
import kociemba
from solver.face_scan import sample_face_hsv
from solver.cube_solver import cluster_faces, build_cubestring

SCAN_ORDER = ["F", "R", "B", "L", "U", "D"]

INSTRUCTIONS = {
    "F": "Hold the cube naturally in front of you. Whatever face points at you now is your reference Front (F) — you'll return to this exact pose twice more.",
    "R": "Without tilting up or down, spin the cube 90° to your right so the face that was on the right now points at you.",
    "B": "Spin another 90° in the same direction.",
    "L": "Spin another 90° in the same direction — last spin.",
    "U": "Return to the Front-facing pose from step 1. Tilt the cube backward (top rolls away from you) 90°, so the top face points at the camera.",
    "D": "From the Front-facing pose again, tilt the cube forward (top rolls toward you) 90°, so the bottom face points at the camera.",
}

st.title("Rubik's Solver")

with st.sidebar:
    st.markdown("### Notation reference")
    st.markdown("""
- Letter alone = clockwise quarter turn (e.g. `R`)
- Letter + `'` = counterclockwise quarter turn (e.g. `R'`)
- Letter + `2` = half turn (e.g. `R2`)
- U / D / L / R / F / B = Up / Down / Left / Right / Front / Back
""")

if "hsv" not in st.session_state:
    st.session_state.hsv = {}

for f in SCAN_ORDER:
    if f not in st.session_state.hsv:
        step = SCAN_ORDER.index(f) + 1
        st.subheader(f"Step {step} of 6 — {f} face")
        st.info(INSTRUCTIONS[f])
        img_file = st.camera_input("Capture", key=f)
        if img_file:
            samples, crop = sample_face_hsv(img_file)
            st.session_state.hsv[f] = samples
        break
    st.write(f"✅ {f} face captured")

if len(st.session_state.hsv) == 6:
    st.success("All 6 faces captured")
    if st.button("Detect Colors & Solve"):
        faces = cluster_faces(st.session_state.hsv)
        cubestring = build_cubestring(faces)
        st.code(cubestring)
        try:
            st.write(kociemba.solve(cubestring).split())
        except Exception:
            st.error("Invalid cube state — this usually means a face was misread. Try Rescan.")

    if st.button("Rescan"):
        st.session_state.hsv = {}
        st.rerun()