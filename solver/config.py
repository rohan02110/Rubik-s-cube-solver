"""Central configuration and constants for the Rubik's Cube Solver application."""

from streamlit_webrtc import RTCConfiguration

# WebRTC STUN Server Configuration
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Standard rotation order for capturing cube faces
SCAN_ORDER = ["F", "R", "B", "L", "U", "D"]

# Standard sticker color palette names
COLOR_NAMES = ["White", "Yellow", "Red", "Orange", "Green", "Blue"]

# Step-by-step physical cube rotation instructions for the user
INSTRUCTIONS = {
    "F": (
        "Hold the cube naturally in front of you. Whatever face points at you now is your reference "
        "Front (F) — you'll return to this exact pose twice more."
    ),
    "R": (
        "Without tilting up or down, spin the cube 90° to your right so the face that was on the right "
        "now points at you."
    ),
    "B": "Spin another 90° in the same direction.",
    "L": "Spin another 90° in the same direction — last spin.",
    "U": (
        "Return to the Front-facing pose from step 1. Tilt the cube backward (top rolls away from you) "
        "90°, so the top face points at the camera."
    ),
    "D": (
        "From the Front-facing pose again, tilt the cube forward (top rolls toward you) 90°, so the "
        "bottom face points at the camera."
    ),
}
