"""Unit tests for the Rubik's Cube Solver package."""

import unittest
import kociemba
from solver.config import COLOR_NAMES, SCAN_ORDER
from solver.cube_solver import STRING_ORDER, build_cubestring
from solver.color_classifier import classify_hsv, _nearest_center


class TestColorClassifier(unittest.TestCase):
    """Tests for the stateless HSV color classifier."""

    def test_white_low_saturation(self):
        """Very low S and high V → White, regardless of hue."""
        self.assertEqual(classify_hsv(0.0,   10.0, 240.0), "White")
        self.assertEqual(classify_hsv(90.0,  15.0, 200.0), "White")   # noisy hue
        self.assertEqual(classify_hsv(130.0, 20.0, 210.0), "White")   # high noisy hue

    def test_yellow(self):
        self.assertEqual(classify_hsv(27.0, 200.0, 220.0), "Yellow")
        self.assertEqual(classify_hsv(30.0, 180.0, 210.0), "Yellow")

    def test_red(self):
        # Hue near 0°
        self.assertEqual(classify_hsv(2.0,  210.0, 200.0), "Red")
        # Hue near 180° (wrap-around)
        self.assertEqual(classify_hsv(170.0, 200.0, 190.0), "Red")

    def test_orange(self):
        self.assertEqual(classify_hsv(13.0, 220.0, 215.0), "Orange")
        self.assertEqual(classify_hsv(18.0, 180.0, 200.0), "Orange")

    def test_green(self):
        self.assertEqual(classify_hsv(60.0, 190.0, 180.0), "Green")
        self.assertEqual(classify_hsv(75.0, 150.0, 160.0), "Green")

    def test_blue(self):
        self.assertEqual(classify_hsv(110.0, 200.0, 185.0), "Blue")
        self.assertEqual(classify_hsv(120.0, 160.0, 170.0), "Blue")

    def test_fallback_returns_valid_color(self):
        """Fallback nearest-center must always return one of the 6 valid names."""
        result = _nearest_center(50.0, 30.0, 30.0)
        self.assertIn(result, COLOR_NAMES)

    def test_all_results_are_valid_names(self):
        """Every classify_hsv call must return a known color name."""
        test_samples = [
            (0, 0, 255), (179, 255, 255), (30, 255, 255),
            (60, 255, 255), (120, 255, 255), (0, 255, 0),
        ]
        for h, s, v in test_samples:
            result = classify_hsv(h, s, v)
            self.assertIn(result, COLOR_NAMES, msg=f"classify_hsv({h},{s},{v}) = {result!r}")

    def test_custom_legend_classification(self):
        """If a legend is provided, matching should be done against the legend."""
        custom_legend = {
            "White":  [0.0, 10.0, 240.0],
            "Yellow": [30.0, 200.0, 220.0],
            "Red":    [5.0, 210.0, 200.0],
            "Orange": [15.0, 220.0, 220.0],
            "Green":  [60.0, 190.0, 180.0],
            "Blue":   [115.0, 200.0, 185.0]
        }

        # Samples matching specific custom centers
        self.assertEqual(classify_hsv(14.0, 215.0, 210.0, legend=custom_legend), "Orange")
        self.assertEqual(classify_hsv(4.0, 205.0, 195.0, legend=custom_legend), "Red")
        self.assertEqual(classify_hsv(112.0, 195.0, 180.0, legend=custom_legend), "Blue")

        # Test fallback / nearest behavior when legend is invalid or missing colors
        bad_legend = {"Red": "not a list"}
        self.assertEqual(classify_hsv(110.0, 200.0, 185.0, legend=bad_legend), "Blue")


class TestCubeSolver(unittest.TestCase):
    """Tests for cubestring construction and Kociemba integration."""

    def setUp(self):
        self.solved_faces = {
            "U": ["White"]  * 9,
            "R": ["Red"]    * 9,
            "F": ["Green"]  * 9,
            "D": ["Yellow"] * 9,
            "L": ["Orange"] * 9,
            "B": ["Blue"]   * 9,
        }

    def test_build_cubestring_length(self):
        cs = build_cubestring(self.solved_faces)
        self.assertEqual(len(cs), 54)
        self.assertTrue(all(c in "URFDLB" for c in cs))

    def test_duplicate_center_raises(self):
        bad = {k: list(v) for k, v in self.solved_faces.items()}
        bad["D"][4] = "White"
        with self.assertRaises(ValueError) as ctx:
            build_cubestring(bad)
        self.assertIn("same center color", str(ctx.exception))

    def test_unmapped_sticker_raises(self):
        bad = {k: list(v) for k, v in self.solved_faces.items()}
        bad["U"][0] = "Purple"
        with self.assertRaises(ValueError) as ctx:
            build_cubestring(bad)
        self.assertIn("Purple", str(ctx.exception))

    def test_kociemba_returns_string(self):
        cs = build_cubestring(self.solved_faces)
        solution = kociemba.solve(cs)
        self.assertIsInstance(solution, str)


class TestConfig(unittest.TestCase):
    """Sanity checks for configuration constants."""

    def test_color_names_count(self):
        self.assertEqual(len(COLOR_NAMES), 6)

    def test_scan_order_count(self):
        self.assertEqual(len(SCAN_ORDER), 6)

    def test_string_order_count(self):
        self.assertEqual(len(STRING_ORDER), 6)


if __name__ == "__main__":
    unittest.main()
