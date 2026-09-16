import ast
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

import d003_estimator as d
from server import geometry as g


def decoded(points, *, below=0):
    return {
        "points_by_ray": points,
        "excluded": {"no_return": 0, "out_of_range": 0, "beam": 0,
                     "wall_or_outside": 0, "below_reference": below},
        "sensor_pose": {"translation_m": [0.15, 0.15, 0.4],
                        "yaw_deg": 0.0, "tilt_deg": 0.0, "roll_deg": 0.0},
    }


class D003Tests(unittest.TestCase):
    def test_merge_is_deterministic_and_uses_conventional_median(self):
        rows = [(1, 4, (0.0501, 0.0501, 0.030)),
                (0, 2, (0.0502, 0.0500, 0.032))]
        forward = d._merge_points(rows)
        reverse = d._merge_points(list(reversed(rows)))
        self.assertEqual(forward, reverse)
        self.assertEqual(len(forward[0]), 1)
        self.assertAlmostEqual(forward[0][0]["point"][2], 0.031)

    def test_merge_withholds_cross_view_surface_conflict(self):
        accepted, conflicts = d._merge_points([
            (0, 0, (0.0500, 0.0500, 0.020)),
            (1, 0, (0.0501, 0.0501, 0.024)),
        ])
        self.assertEqual(accepted, [])
        self.assertEqual(len(conflicts), 1)
        self.assertGreater(conflicts[0]["z_range_m"], d.MERGED_Z_RANGE_MAX_M)

    def test_pooling_creates_cross_view_triangle(self):
        frames = [b"a", b"b", b"c"]
        points = [[(0.06, 0.06, 0.03)], [(0.09, 0.06, 0.03)], [(0.06, 0.09, 0.03)]]
        with patch.object(d.g, "decode_frame", side_effect=[decoded(x) for x in points]):
            result = d.estimate_frames(frames)
        self.assertEqual(result["raw_point_count"], 3)
        self.assertEqual(result["merged_point_count"], 3)
        self.assertEqual(result["accepted_triangle_count"], 1)
        self.assertGreater(result["support_cell_count"], 0)
        self.assertFalse(result["total_selection"]["selected"])

    def test_maximum_3d_edge_gate_rejects_long_triangle(self):
        sums, counts = [0.0] * 400, [0] * 400
        contributors = [[] for _ in range(400)]
        accepted = d._raster_triangle(
            [(0.02, 0.02, 0.02), (0.14, 0.02, 0.02), (0.02, 0.14, 0.02)],
            0, sums, counts, contributors, 0.0,
        )
        self.assertFalse(accepted)
        self.assertEqual(sum(counts), 0)

    def test_no_extrapolation_beyond_observed_hull(self):
        points = [(0.06, 0.06, 0.03), (0.24, 0.06, 0.03),
                  (0.24, 0.24, 0.03), (0.06, 0.24, 0.03),
                  (0.15, 0.15, 0.03)]
        with patch.object(d.g, "decode_frame", return_value=decoded(points)):
            result = d.estimate_frames([b"frame"])
        self.assertIsNone(result["heights"][0])
        self.assertIsNone(result["heights"][-1])
        self.assertFalse(result["total_selection"]["selected"])

    def test_invalid_and_unavailable_inputs_block_total(self):
        full_grid = [((ix + 0.5) * g.CELL, (iy + 0.5) * g.CELL, 0.02)
                     for iy in range(20) for ix in range(20)]
        with patch.object(d.g, "decode_frame", side_effect=[decoded(full_grid), ValueError("bad")]):
            result = d.estimate_frames([b"good", b"bad"])
        self.assertEqual([x["index"] for x in result["invalid_frames"]], [1])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertIsNone(result["total_volume_m3"])

        with patch.object(d.g, "decode_frame", side_effect=[decoded(full_grid), decoded([], below=1)]):
            result = d.estimate_frames([b"good", b"unavailable"])
        self.assertEqual(result["unavailable_view_indices"], [1])
        self.assertFalse(result["total_selection"]["selected"])

    def test_configuration_validation(self):
        for config in ({"truth": 1}, {"reference_offset_m": math.nan}, [], {"reference_offset_m": True}):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    d.estimate_frames([], config)

    def test_estimator_has_no_truth_or_evaluator_imports(self):
        tree = ast.parse((HERE / "d003_estimator.py").read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = [name for name in imports if name.startswith(("experiments", "run_", "truth"))]
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
