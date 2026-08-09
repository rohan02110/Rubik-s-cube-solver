"""Rubik's Cube Solver — public package API."""

from solver.color_classifier import classify_hsv
from solver.cube3d import render_cube
from solver.cube_solver import STRING_ORDER, build_cubestring
from solver.live_scan import make_scan_callback, result_queue
from solver.config import COLOR_NAMES, INSTRUCTIONS, RTC_CONFIGURATION, SCAN_ORDER

__all__ = [
    # Color classification
    "classify_hsv",
    # Cube solving
    "build_cubestring",
    "STRING_ORDER",
    # Live scan
    "make_scan_callback",
    "result_queue",
    # 3D renderer
    "render_cube",
    # Configuration
    "RTC_CONFIGURATION",
    "SCAN_ORDER",
    "COLOR_NAMES",
    "INSTRUCTIONS",
]
