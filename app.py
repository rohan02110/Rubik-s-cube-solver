import streamlit as st
import queue
import numpy as np
import cv2
import kociemba
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from solver.live_scan import result_queue, make_callback, legend_queue, make_legend_callback
from solver.legend import classify_to_legend
from solver.cube_solver import build_cubestring, STRING_ORDER
from streamlit_webrtc import RTCConfiguration
from solver.cube3d import render_cube

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

SCAN_ORDER = ["F", "R", "B", "L", "U", "D"]
COLOR_NAMES = ["White", "Yellow", "Red", "Orange", "Green", "Blue"]

INSTRUCTIONS = {
    "F": "Hold the cube naturally in front of you. Whatever face points at you now is your reference Front (F) — you'll return to this exact pose twice more.",
    "R": "Without tilting up or down, spin the cube 90° to your right so the face that was on the right now points at you.",
    "B": "Spin another 90° in the same direction.",
    "L": "Spin another 90° in the same direction — last spin.",
    "U": "Return to the Front-facing pose from step 1. Tilt the cube backward (top rolls away from you) 90°, so the top face points at the camera.",
    "D": "From the Front-facing pose again, tilt the cube forward (top rolls toward you) 90°, so the bottom face points at the camera.",
}

def swatch(rgb, size=36):
    r, g, b = rgb
    st.markdown(
        f'<div style="width:{size}px;height:{size}px;background:rgb({r},{g},{b});'
        f'border:1px solid #888;border-radius:4px;"></div>',
        unsafe_allow_html=True,
    )

def hsv_to_rgb(hsv):
    h, s, v = hsv
    rgb = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2RGB)[0][0]
    return tuple(int(x) for x in rgb)

st.title("Rubik's Solver")

with st.sidebar:
    st.markdown("### Notation reference")
    st.markdown("""
- Letter alone = clockwise quarter turn (e.g. `R`)
- Letter + `'` = counterclockwise quarter turn (e.g. `R'`)
- Letter + `2` = half turn (e.g. `R2`)
- U / D / L / R / F / B = Up / Down / Left / Right / Front / Back
""")

if "legend" not in st.session_state:
    st.session_state.legend = {}
if "faces" not in st.session_state:
    st.session_state.faces = {}
if "stage" not in st.session_state:
    st.session_state.stage = "legend"

# ---------------- LEGEND ----------------
if st.session_state.stage == "legend":
    remaining = [c for c in COLOR_NAMES if c not in st.session_state.legend]

    if remaining:
        current = remaining[0]
        st.subheader(f"Define legend — {current} ({len(st.session_state.legend)+1} of 6)")
        st.info(f"Hold your {current} sticker centered in the box, then capture.")

        ctx = webrtc_streamer(
            key="legend_cam",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=make_legend_callback(),
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration=RTC_CONFIGURATION,
        )

        if ctx.state.playing:
            if st.button(f"Capture {current}"):
                try:
                    st.session_state.legend[current] = legend_queue.get(timeout=1)
                    st.rerun()
                except queue.Empty:
                    st.warning("No frame yet — wait a second and try again.")
    else:
        st.session_state.stage = "scan"
        st.rerun()

# ---------------- SCAN ----------------
elif st.session_state.stage == "scan":
    remaining = [f for f in SCAN_ORDER if f not in st.session_state.faces]

    if remaining:
        current = remaining[0]
        step = SCAN_ORDER.index(current) + 1
        st.subheader(f"Step {step} of 6 — {current} face")
        st.info(INSTRUCTIONS[current])

        ctx = webrtc_streamer(
            key="scanner",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=make_callback(),
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration=RTC_CONFIGURATION,
        )

        if ctx.state.playing:
            if st.button(f"Lock in {current} face"):
                try:
                    samples = result_queue.get(timeout=1)
                    st.session_state.faces[current] = [
                        classify_to_legend(h, s, v, st.session_state.legend) for h, s, v in samples
                    ]
                    st.rerun()
                except queue.Empty:
                    st.warning("No frame yet — wait a second and try again.")
    else:
        st.session_state.stage = "verify"
        st.rerun()

# ---------------- VERIFY ----------------
elif st.session_state.stage == "verify":
    st.success("All 6 faces captured — check each sticker and fix any misreads")

    st.markdown("**Legend**")
    legend_cols = st.columns(6)
    for col, name in zip(legend_cols, COLOR_NAMES):
        with col:
            swatch(hsv_to_rgb(st.session_state.legend[name]))
            st.caption(name)

    for f in STRING_ORDER:
        with st.expander(f"{f} face", expanded=True):
            for row in range(3):
                cols = st.columns(3)
                for col_i in range(3):
                    idx = row * 3 + col_i
                    with cols[col_i]:
                        current_val = st.session_state.faces[f][idx]
                        swatch(hsv_to_rgb(st.session_state.legend[current_val]))
                        new_val = st.selectbox(
                            " ", COLOR_NAMES, index=COLOR_NAMES.index(current_val),
                            key=f"edit_{f}_{idx}", label_visibility="collapsed",
                        )
                        st.session_state.faces[f][idx] = new_val

    col1, col2 = st.columns(2)
    if col1.button("Confirm & Solve"):
        st.session_state.stage = "solve"
        st.rerun()
    if col2.button("Start over"):
        st.session_state.legend = {}
        st.session_state.faces = {}
        st.session_state.stage = "legend"
        st.rerun()

# ---------------- SOLVE ----------------
elif st.session_state.stage == "solve":
    try:
        cubestring = build_cubestring(st.session_state.faces)
        st.code(cubestring)
        moves = kociemba.solve(cubestring).split()
        st.write(kociemba.solve(cubestring).split())
        render_cube(st.session_state.faces)
    except Exception as e:
        st.error(f"Scan issue: {e}")

    col1, col2 = st.columns(2)
    if col1.button("Back to Verify"):
        st.session_state.stage = "verify"
        st.rerun()
    if col2.button("Start over"):
        st.session_state.legend = {}
        st.session_state.faces = {}
        st.session_state.stage = "legend"
        st.rerun()