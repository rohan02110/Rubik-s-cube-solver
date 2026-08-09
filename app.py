"""Rubik's Cube Solver — Main Streamlit Web Application.

Workflow (2 stages):
  1. Smart Scan — live camera with real-time color classification overlay,
     inline 3×3 correction grid, one face at a time, 6 total.
  2. Solve — Kociemba algorithm + interactive 3D step-by-step viewer.
"""

import queue
import kociemba
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from solver import (
    COLOR_NAMES,
    INSTRUCTIONS,
    RTC_CONFIGURATION,
    SCAN_ORDER,
    STRING_ORDER,
    build_cubestring,
    make_scan_callback,
    render_cube,
    result_queue,
)

# ── RGB display colors for Streamlit CSS ──────────────────────────────────────
_COLOR_RGB: dict[str, tuple[int, int, int]] = {
    "White":  (255, 255, 255),
    "Yellow": (255, 215, 0),
    "Red":    (215, 30,  30),
    "Orange": (255, 140, 0),
    "Green":  (30,  175, 30),
    "Blue":   (30,  100, 215),
}


def _inject_grid_css(face: str, display_colors: list[str]) -> None:
    """Inject per-button CSS so each correction cell shows its sticker color."""
    rules = []
    for i, cname in enumerate(display_colors):
        key = f"cell_{face}_{i}"
        r, g, b = _COLOR_RGB.get(cname, (128, 128, 128))
        text = "#111" if cname in ("White", "Yellow") else "#eee"
        rules.append(
            f".st-key-{key} button {{"
            f"background-color:rgb({r},{g},{b}) !important;"
            f"height:54px;width:54px;border:2px solid #444;"
            f"border-radius:8px;min-height:54px;"
            f"font-weight:700;font-size:14px;color:{text} !important;"
            f"margin:2px auto;display:block;}}"
        )
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def _face_mini_html(face_colors: list[str]) -> str:
    """Render a compact 3×3 color grid as inline HTML."""
    cells = [
        f'<div style="display:inline-block;width:16px;height:16px;'
        f'background:rgb{_COLOR_RGB.get(c,(128,128,128))};'
        f'border:1px solid #555;border-radius:2px;margin:1px;"></div>'
        for c in face_colors
    ]
    return "".join(
        f'<div style="display:block;line-height:0;">{"".join(cells[r*3:r*3+3])}</div>'
        for r in range(3)
    )


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Rubik's Cube Solver", layout="centered", page_icon="🧩")
st.title("Rubik's Cube Solver 🧩")

with st.sidebar:
    st.markdown("### 📖 Move Notation")
    st.markdown("""
- **R / L** = Right / Left
- **U / D** = Up / Down
- **F / B** = Front / Back
- **`'`** = Counter-clockwise
- **`2`** = Half turn (180°)
""")
    st.divider()
    st.markdown("### 🎨 Color Key")
    for name, (r, g, b) in _COLOR_RGB.items():
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
            f'<div style="width:18px;height:18px;background:rgb({r},{g},{b});'
            f'border:1px solid #666;border-radius:3px;"></div>'
            f'<span style="font-size:13px;">{name}</span></div>',
            unsafe_allow_html=True,
        )

# ── Session state ─────────────────────────────────────────────────────────────
if "faces" not in st.session_state:
    st.session_state.faces: dict[str, list[str]] = {}
if "stage" not in st.session_state:
    st.session_state.stage: str = "scan"
if "corrections" not in st.session_state:
    st.session_state.corrections: dict[str, dict[int, str]] = {}


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 1 — SMART SCAN
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "scan":
    remaining = [f for f in SCAN_ORDER if f not in st.session_state.faces]
    done = len(SCAN_ORDER) - len(remaining)

    st.progress(done / 6, text=f"**{done} / 6 faces scanned**")

    current = remaining[0]
    step = SCAN_ORDER.index(current) + 1

    st.subheader(f"Face {step} / 6 — **{current}**")
    st.info(INSTRUCTIONS[current])

    # ── 1. Live camera ────────────────────────────────────────────────────────
    ctx = webrtc_streamer(
        key=f"scanner_{current}",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=make_scan_callback(),
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration=RTC_CONFIGURATION,
    )

    # ── Auto-populate verification grid from live feed ─────────────────────────
    # Latest live detection is always fetched; per-cell user corrections override.
    cache_key = f"_det_{current}"
    live_detected: list[str] = st.session_state.get(cache_key, ["White"] * 9)
    try:
        _, live_colors = result_queue.get_nowait()
        st.session_state[cache_key] = live_colors
        live_detected = live_colors
    except queue.Empty:
        pass

    corrs = st.session_state.corrections.get(current, {})
    display_tiles: list[str] = [corrs.get(i, live_detected[i]) for i in range(9)]

    is_playing = ctx is not None and ctx.state.playing

    st.divider()

    # ── 2. Verification Tiles Grid ────────────────────────────────────────────
    _inject_grid_css(current, display_tiles)
    st.caption("🔍 **Verification Tiles** — auto-updated from camera. Tap any cell to correct a misread color.")

    for row in range(3):
        cols = st.columns(3)
        for col_i in range(3):
            idx = row * 3 + col_i
            with cols[col_i]:
                if st.button(display_tiles[idx][0], key=f"cell_{current}_{idx}"):
                    next_color = COLOR_NAMES[
                        (COLOR_NAMES.index(display_tiles[idx]) + 1) % len(COLOR_NAMES)
                    ]
                    st.session_state.corrections.setdefault(current, {})[idx] = next_color
                    st.rerun()

    st.divider()

    # ── 3. Lock-in / Reset ────────────────────────────────────────────────────
    col_lock, col_reset = st.columns([3, 1])

    if col_lock.button(
        f"✅ Lock in Face {current}",
        type="primary",
        disabled=not is_playing,
        use_container_width=True,
    ):
        # Grab one final fresh frame; merge with any user corrections
        try:
            _, fresh = result_queue.get(timeout=1)
        except queue.Empty:
            fresh = live_detected

        final = [st.session_state.corrections.get(current, {}).get(i, fresh[i]) for i in range(9)]
        st.session_state.faces[current] = final
        st.session_state.corrections.pop(current, None)
        st.session_state.pop(cache_key, None)

        if len(st.session_state.faces) == 6:
            st.session_state.stage = "solve"
        st.rerun()

    if col_reset.button("🔄 Reset", use_container_width=True):
        keys_to_del = [k for k in st.session_state if k.startswith("_det_")]
        for k in keys_to_del:
            del st.session_state[k]
        st.session_state.faces = {}
        st.session_state.corrections = {}
        st.session_state.stage = "scan"
        st.rerun()

    # ── Completed faces summary ───────────────────────────────────────────────
    if st.session_state.faces:
        with st.expander(f"✅ Completed faces  ({done} / 6)", expanded=False):
            for face_key, face_colors in st.session_state.faces.items():
                st.markdown(
                    f"**{face_key}** &nbsp; {_face_mini_html(face_colors)}",
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 2 — SOLVE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "solve":
    st.subheader("Solution")

    try:
        cubestring = build_cubestring(st.session_state.faces)
        moves = kociemba.solve(cubestring).split()
        st.success(f"Solution found — **{len(moves)} moves**")
        render_cube(st.session_state.faces, moves)
    except Exception as e:
        st.error(f"Cube state error: {e}")
        st.info("Re-scan any face with wrong colors using the options below.")

    st.divider()
    col1, col2 = st.columns(2)

    if col1.button("🔄 Scan All Again", use_container_width=True):
        keys_to_del = [k for k in st.session_state if k.startswith("_det_")]
        for k in keys_to_del:
            del st.session_state[k]
        st.session_state.faces = {}
        st.session_state.corrections = {}
        st.session_state.stage = "scan"
        st.rerun()

    with col2:
        rescan_face = st.selectbox(
            "Re-scan one face",
            options=SCAN_ORDER,
            label_visibility="collapsed",
        )
        if st.button(f"Re-scan  {rescan_face}", use_container_width=True):
            st.session_state.faces.pop(rescan_face, None)
            st.session_state.stage = "scan"
            st.rerun()