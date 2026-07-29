import streamlit as st
import queue
import kociemba
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from solver.live_scan import result_queue, make_callback
from solver.cube_solver import (
    cluster_faces, build_cubestring, compute_cluster_colors, cluster_names, STRING_ORDER
)

SCAN_ORDER = ["F", "R", "B", "L", "U", "D"]

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
if "stage" not in st.session_state:
    st.session_state.stage = "scan"

# ---------------- SCAN ----------------
if st.session_state.stage == "scan":
    remaining = [f for f in SCAN_ORDER if f not in st.session_state.hsv]

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
        )

        if ctx.state.playing:
            if st.button(f"Lock in {current} face"):
                try:
                    st.session_state.hsv[current] = result_queue.get(timeout=1)
                    st.rerun()
                except queue.Empty:
                    st.warning("No frame yet — wait a second and try again.")
    else:
        st.session_state.faces = cluster_faces(st.session_state.hsv)
        st.session_state.stage = "verify"
        st.rerun()

# ---------------- VERIFY ----------------
elif st.session_state.stage == "verify":
    st.success("All 6 faces captured — check each sticker and fix any misreads")

    colors = compute_cluster_colors(st.session_state.hsv, st.session_state.faces)
    names = cluster_names(st.session_state.hsv, st.session_state.faces)
    options = sorted(colors.keys())

    st.markdown("**Legend**")
    legend_cols = st.columns(len(options))
    for col, c in zip(legend_cols, options):
        with col:
            swatch(colors[c])
            st.caption(names[c])

    for f in STRING_ORDER:
        with st.expander(f"{f} face", expanded=True):
            for row in range(3):
                cols = st.columns(3)
                for col_i in range(3):
                    idx = row * 3 + col_i
                    with cols[col_i]:
                        current_val = st.session_state.faces[f][idx]
                        swatch(colors[current_val])
                        new_val = st.selectbox(
                            " ", options, index=options.index(current_val),
                            format_func=lambda c: names[c],
                            key=f"edit_{f}_{idx}", label_visibility="collapsed",
                        )
                        st.session_state.faces[f][idx] = new_val

    col1, col2 = st.columns(2)
    if col1.button("Confirm & Solve"):
        st.session_state.stage = "solve"
        st.rerun()
    if col2.button("Rescan everything"):
        st.session_state.hsv = {}
        st.session_state.stage = "scan"
        st.rerun()

# ---------------- SOLVE ----------------
elif st.session_state.stage == "solve":
    try:
        cubestring = build_cubestring(st.session_state.faces)
        st.code(cubestring)
        st.write(kociemba.solve(cubestring).split())
    except Exception as e:
        st.error(f"Scan issue: {e}")

    col1, col2 = st.columns(2)
    if col1.button("Back to Verify"):
        st.session_state.stage = "verify"
        st.rerun()
    if col2.button("Rescan everything"):
        st.session_state.hsv = {}
        st.session_state.stage = "scan"
        st.rerun()