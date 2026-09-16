import ast
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

import d001_estimator as d
from server import geometry as g


def planar_points(columns, rows, height, *, x0=0.06, y0=0.06, step=0.03):
    points = []
    for row in range(rows):
        for column in range(columns):
            x = x0 + column * step
            y = y0 + row * step
            material_height = height(x, y)
            points.append((x, y, g.base(x, y) + material_height))
    return points


class D001Tests(unittest.TestCase):
    def test_four_vertex_plane_is_supported_and_three_point_plane_is_not(self):
        points = planar_points(2, 2, lambda x, y: 0.01 + 0.2*x - 0.1*y)
        patches, triangles, rejected = d._segment_patches(points, 2, 2)
        self.assertEqual(len(triangles), 2)
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["vertex_indices"], [0, 1, 2, 3])
        self.assertLess(patches[0]["maximum_residual_m"], 1e-10)
        self.assertEqual(rejected, [])

        points[3] = None
        patches, triangles, rejected = d._segment_patches(points, 2, 2)
        self.assertEqual(patches, [])
        self.assertLessEqual(len(triangles), 1)

    def test_two_millimetre_plane_consistency_gate_splits_incompatible_region(self):
        points = planar_points(4, 3, lambda x, y: 0.02)
        # One column differs by more than the frozen 2 mm quantization gate.
        for index in (3, 7, 11):
            x, y, z = points[index]
            points[index] = (x, y, z + 0.006)
        patches, _, _ = d._segment_patches(points, 4, 3)
        self.assertGreaterEqual(len(patches), 2)
        for item in patches:
            self.assertGreaterEqual(len(item["vertex_indices"]), 4)
            self.assertLessEqual(item["maximum_residual_m"], d.PLANE_TOLERANCE_M)

    def test_exact_four_point_false_ramp_is_a_documented_ambiguity(self):
        # Two low and two high samples are algebraically identical to a planar
        # ramp.  The truth-free four-point rule therefore accepts this case;
        # the test preserves the limitation instead of hiding it by tuning.
        points = planar_points(
            2, 2, lambda x, y: 0.01 if x < 0.075 else 0.05,
            x0=0.06, step=0.03,
        )
        patches, _, rejected = d._segment_patches(points, 2, 2)
        self.assertEqual(len(patches), 1)
        self.assertEqual(rejected, [])
        self.assertLess(patches[0]["maximum_residual_m"], 1e-10)

    def test_patch_hull_labels_bounded_hole_as_model(self):
        points = planar_points(3, 3, lambda x, y: 0.04)
        patches, triangles, _ = d._segment_patches(points, 3, 3)
        self.assertEqual(len(patches), 1)
        patch_item = patches[0]
        # Remove triangles touching the centre from direct support while retaining
        # the already-supported plane vertices to exercise only hull reconstruction.
        corner_triangles = {
            triangle_id: indices for triangle_id, indices in triangles.items()
            if 4 not in indices
        }
        patch_item = dict(patch_item)
        patch_item["triangle_ids"] = sorted(corner_triangles)
        candidates = d._patch_candidates(patch_item, corner_triangles, points)
        center = 6 * g.NX + 6  # x=y=0.0975, inside the observed point hull.
        self.assertEqual(candidates[center]["kind"], "model")
        self.assertAlmostEqual(candidates[center]["height_m"], 0.04, places=10)

    def test_hull_does_not_extrapolate_beyond_half_max_edge_from_vertices(self):
        patch_item = {
            "triangle_ids": [],
            "vertex_indices": [0, 1, 2, 3],
            "coefficients": (0.0, 0.0, 0.03),
        }
        points = [(0.02, 0.02, 0.03), (0.28, 0.02, 0.03),
                  (0.28, 0.28, 0.03), (0.02, 0.28, 0.03)]
        candidates = d._patch_candidates(patch_item, {}, points)
        center = 10 * g.NX + 10
        self.assertNotIn(center, candidates)

    def test_fusion_prefers_observed_then_uses_conventional_median(self):
        def view(value, kind, state="partial"):
            heights = [None] * 400
            kinds = [None] * 400
            heights[0], kinds[0] = value, kind
            return {
                "algorithm_id": d.ALGORITHM_ID, "heights": heights,
                "support_kind_by_cell": kinds, "measurement_state": state,
                "patches": [], "valid_local_triangle_count": 0,
                "accepted_patch_triangle_count": 0, "rejected_triangle_ids": [],
                "conflicts": [], "sensor_pose": {}, "excluded": {},
            }

        with patch.object(d, "analyze_frame", side_effect=[
                view(0.09, "model"), view(0.02, "observed"), view(0.04, "observed")]):
            result = d.fuse_frames([b"a", b"b", b"c"])
        self.assertEqual(result["support_kind_by_cell"][0], "observed")
        self.assertEqual(result["heights"][0], 0.03)
        self.assertEqual(result["selected_view_indices_by_cell"][0], [1, 2])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertEqual(result["model_support_cell_count"], 0)
        self.assertAlmostEqual(result["observed_volume_m3"], 0.03 * g.CELL ** 2)
        self.assertAlmostEqual(
            result["reconstructed_supported_volume_m3"], 0.03 * g.CELL ** 2,
        )

    def test_invalid_input_and_configuration_never_select_total(self):
        result = d.fuse_frames([b"bad"])
        self.assertEqual([item["index"] for item in result["invalid_frames"]], [0])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertIsNone(result["total_volume_m3"])
        for config in ({"truth": 1}, {"reference_offset_m": math.nan}, []):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    d.fuse_frames([], config)

    def test_unavailable_and_invalid_views_cannot_contaminate_or_select_total(self):
        def full_view(value, state):
            return {
                "algorithm_id": d.ALGORITHM_ID,
                "heights": [value] * 400,
                "support_kind_by_cell": ["observed"] * 400,
                "measurement_state": state,
                "patches": [], "valid_local_triangle_count": 0,
                "accepted_patch_triangle_count": 0, "rejected_triangle_ids": [],
                "conflicts": [], "sensor_pose": {}, "excluded": {},
            }

        with patch.object(d, "analyze_frame", side_effect=[
                full_view(0.02, "model_supported"),
                full_view(0.10, "unavailable"),
                ValueError("synthetic invalid frame"),
        ]):
            result = d.fuse_frames([b"good", b"unavailable", b"invalid"])
        self.assertEqual(result["heights"], [0.02] * 400)
        self.assertEqual(result["unavailable_view_indices"], [1])
        self.assertEqual([item["index"] for item in result["invalid_frames"]], [2])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertIsNone(result["total_volume_m3"])
        self.assertIn("unavailable_views_1", result["total_selection"]["rejection_reasons"])
        self.assertIn("invalid_frames_1", result["total_selection"]["rejection_reasons"])

    def test_estimator_has_no_truth_evaluator_or_scipy_imports(self):
        tree = ast.parse((HERE / "d001_estimator.py").read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = [
            name for name in imports
            if name.startswith(("experiments", "run_", "truth", "scipy", "numpy"))
        ]
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
