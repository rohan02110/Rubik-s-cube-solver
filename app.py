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
    st.success("All 6 faces captured — tap any sticker to cycle its color")

    st.markdown("**Legend**")
    legend_cols = st.columns(6)
    for col, name in zip(legend_cols, COLOR_NAMES):
        with col:
            swatch(hsv_to_rgb(st.session_state.legend[name]))
            st.caption(name)

    st.caption("Tap a sticker to cycle: White → Yellow → Red → Orange → Green → Blue")

    # Build one CSS rule per sticker so its button shows the right color
    style_rules = []
    for f in STRING_ORDER:
        for idx in range(9):
            key = f"tap_{f}_{idx}"
            current_val = st.session_state.faces[f][idx]
            r, g, b = hsv_to_rgb(st.session_state.legend[current_val])
            style_rules.append(
                f".st-key-{key} button {{"
                f"background-color: rgb({r},{g},{b}) !important;"
                f"height: 44px; width: 44px; border: 2px solid #333;"
                f"border-radius: 6px; padding: 0; min-height: 44px;"
                f"margin: 0 auto; display: block;}}"
            )
    st.markdown(f"<style>{''.join(style_rules)}</style>", unsafe_allow_html=True)

    def sticker_button(f, idx, container):
        key = f"tap_{f}_{idx}"
        with container:
            if st.button(" ", key=key):
                current_val = st.session_state.faces[f][idx]
                next_i = (COLOR_NAMES.index(current_val) + 1) % len(COLOR_NAMES)
                st.session_state.faces[f][idx] = COLOR_NAMES[next_i]
                st.rerun()

    def render_centered_face(f):
        for row in range(3):
            cols = st.columns(12)
            for col_i in range(3):
                idx = row * 3 + col_i
                sticker_button(f, idx, cols[3 + col_i])

    # U face
    st.caption("U")
    render_centered_face("U")

    # L, F, R, B in one band
    st.caption("L · F · R · B")
    for row in range(3):
        cols = st.columns(12)
        for face_i, f in enumerate(["L", "F", "R", "B"]):
            offset = face_i * 3
            for col_i in range(3):
                idx = row * 3 + col_i
                sticker_button(f, idx, cols[offset + col_i])

    # D face
    st.caption("D")
    render_centered_face("D")

    col1, col2, col3 = st.columns(3)
    if col1.button("Solve"):
        st.session_state.stage = "solve"
        st.rerun()
    if col2.button("Rescan Cube"):
        st.session_state.faces = {}
        st.session_state.stage = "scan"
        st.rerun()
    if col3.button("Rescan Legend"):
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
        render_cube(st.session_state.faces, moves)
    except Exception as e:
        st.error(f"Scan issue: {e}")

    col1, col2, col3 = st.columns(3)
    if col1.button("Back to Verify"):
        st.session_state.stage = "verify"
        st.rerun()
    if col2.button("Rescan Cube"):
        st.session_state.faces = {}
        st.session_state.stage = "scan"
        st.rerun()
    if col3.button("Rescan Legend"):
        st.session_state.legend = {}
        st.session_state.faces = {}
        st.session_state.stage = "legend"
        st.rerun()