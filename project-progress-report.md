# Rubik's Cube Solver — Progress Notes (updated)

Rough log, not a formal report. Continuing from before — a lot has changed since the last one.

## Stack (current)
Streamlit (all Python, frontend + backend) → `streamlit-webrtc` for live video → OpenCV for color sampling → legend-based nearest-match color classification → kociemba for solving. Dev locally, deploy via Streamlit Community Cloud, code on GitHub.

Dropped along the way: Replit + Flask + JS (switched to Streamlit early on), manual HSV slider calibration (too tedious), and — most recently — scikit-learn k-means clustering (replaced by the legend approach below). None of those are in the current app anymore.

## Current app flow: Legend → Scan → Verify → Solve

- **Legend stage (newest addition):** before scanning, the user shows each of their cube's 6 real sticker colors to the camera once and captures a reference sample for each. Everything after this matches stickers against these 6 real anchors instead of guessing.
- **Scan stage:** live camera feed via `streamlit-webrtc` (not single-photo capture anymore) with a white 3×3 grid overlaid, live color swatches per cell updating in real time, and background dimmed outside the grid. Walks through 6 faces in a physically sensible rotation order (F → R → B → L → U → D) with an on-screen instruction for how to rotate the cube between shots. One "Lock in" click per face — not a full shutter/photo click, just confirming what's already showing live.
- **Verify stage (added recently):** shows every one of the 54 stickers as a color swatch with a dropdown to manually reassign any that got misread — without needing to rescan the whole cube. Also shows the 6 legend colors as a reference legend at the top, which doubles as a diagnostic (if two legend colors look near-identical, that's a real lighting/color-similarity issue, not a bug).
- **Solve stage:** builds the 54-character cubestring, calls `kociemba.solve()`, shows the move list. Catches both invalid-cube-state errors and "two faces same color" errors with a readable message instead of crashing.

## Why the color-detection approach changed twice

1. Started with manual HSV sliders per color — worked, but tedious to redo every session.
2. Switched to k-means clustering (no manual numbers, adapts to lighting automatically) — better, but had a real recurring bug: red and orange kept getting confused, since clustering has no concept of "true" colors and just finds whatever 6 groups best separate the data — when two colors are genuinely close in hue, it can merge or split them unpredictably.
3. Just moved to the legend approach — user captures their own 6 real reference colors right before scanning, then every sticker gets matched to its *nearest* real anchor. Anchored matching should hold up much better on close colors like red/orange than blind clustering did. **Not yet tested against a real cube** — this is the immediate next thing to verify.

## Bugs hit and fixed along the way
- `kociemba` failing to install on Windows — needed Microsoft C++ Build Tools.
- Git/GitHub hiccups: `.gitignore` typed into the terminal instead of saved as a file, placeholder `<your-username>` left in a remote URL, a push rejected because the GitHub repo wasn't empty.
- PowerShell doesn't support `&&` chaining like Bash.
- A `STRING_ORDER` vs `FACES` naming mismatch, and separately an `ImportError` that turned out to be a stale Streamlit process serving old code even after the file itself was already fixed.
- Color-collision errors traced first to loose framing (fingers/background creeping into shot, fixed by tightening the sampling margin), and then to genuine red/orange similarity under clustering (prompted the move to the legend approach above).

## Not done / open right now
- **Test the legend rewrite end to end** — written but not yet run against a real cube. First thing to check: does it actually fix red vs. orange.
- **Clean up dead code** — `calibrate.py`, `solver/colors.py` (old manual calibration) and the clustering functions in `cube_solver.py` (`cluster_faces`, `compute_cluster_colors`, `guess_name`, `cluster_names`) are all superseded now and can be deleted.
- **scikit-learn** can come out of `requirements.txt` — nothing uses it anymore.
- **Redeploy to Streamlit Community Cloud** — the live deployed version predates the webrtc rewrite entirely; needs a fresh push, and webrtc specifically has a known open question about whether it'll connect reliably over the internet on the cloud deployment (works fine locally, cloud not yet tested — flagged earlier as a possible STUN/TURN issue).
- **Phase 4 (3D visualization)** — still not started. Plan remains: Three.js cube embedded via `st.components.v1.html()`, painted with scanned colors, animated through the kociemba move list step by step.
