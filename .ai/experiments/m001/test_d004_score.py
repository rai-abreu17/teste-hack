import ast
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

import run_d004_score as score


class D004ScoreTests(unittest.TestCase):
    def test_released_inputs_verify_without_estimation(self):
        protocol, pre, acquisition = score.verify_released_inputs()
        self.assertEqual(protocol["experiment_id"], "D-004")
        self.assertEqual(len(pre["selected_archived_frames"]), 45)
        self.assertEqual(len(acquisition["candidate_frames"]), 36)

    def test_arm_paths_share_exact_center(self):
        for scene_id in ("pyramid_center", "layer_beam", "pyramid_beam_dropout20"):
            control = score.arm_paths(scene_id, "control_k4_plus_shared_center")
            candidate = score.arm_paths(scene_id, "candidate_inset_diagonals_plus_shared_center")
            self.assertEqual(len(control), 5)
            self.assertEqual(len(candidate), 5)
            self.assertEqual(control[-1], candidate[-1])
            self.assertEqual(control[-1].read_bytes(), candidate[-1].read_bytes())

    def test_convex_hull_and_inclusion(self):
        points = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5), (0, 0)]
        hull = score.convex_hull(points)
        self.assertEqual(hull, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        self.assertAlmostEqual(score.polygon_area(hull), 1.0)
        self.assertTrue(score.inside_convex(hull, (0.5, 0.5)))
        self.assertTrue(score.inside_convex(hull, (0, 0.5)))
        self.assertFalse(score.inside_convex(hull, (1.1, 0.5)))

    def test_domain_stats_reports_spatial_error_and_cancellation(self):
        heights = [2.0, 0.0]
        reference = [score.g.CELL ** 2, score.g.CELL ** 2]
        result = score.domain_stats(heights, reference, [0, 1])
        self.assertAlmostEqual(result["signed_error_m3"], 0.0)
        self.assertAlmostEqual(result["integrated_absolute_error_m3"], 2 * score.g.CELL ** 2)
        self.assertIsNone(result["cancellation_ratio"])

    def test_protocol_scene_metadata_is_separate_from_truth_constructor(self):
        protocol = json.loads((HERE / "protocol_d004.json").read_text(encoding="utf-8"))
        scene_data = protocol["scenes"][0]
        physical = {key: value for key, value in scene_data.items() if key != "id"}
        from experiments.truth import Scene
        scene = Scene(**physical)
        self.assertEqual(scene.fill, scene_data["fill"])
        self.assertNotIn("id", physical)

    def test_partial_cannot_pass_gate(self):
        records = []
        for index in range(9):
            records.append({
                "arm_id": "candidate_inset_diagonals_plus_shared_center",
                "total_selection": {"selected": index != 0},
                "company_5pct_total_only": None if index == 0 else True,
            })
        gate = score.aggregate_gate(records)
        self.assertEqual(gate["candidate_total_eligible"], 8)
        self.assertEqual(gate["candidate_total_within_5pct"], 8)
        self.assertFalse(gate["coverage_gate_9_of_9"])
        self.assertFalse(gate["company_gate_9_of_9_total_and_within_5pct"])

    def test_truth_import_is_not_module_level(self):
        tree = ast.parse((HERE / "run_d004_score.py").read_text(encoding="utf-8"))
        top_level_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                top_level_imports.append(node.module or "")
        self.assertFalse([name for name in top_level_imports if name.startswith("experiments")])
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "evaluate_with_truth")
        imports = [node.module for node in ast.walk(function) if isinstance(node, ast.ImportFrom)]
        self.assertIn("experiments", imports)

    def test_protocol_gate_and_estimator_remain_frozen(self):
        protocol = json.loads((HERE / "protocol_d004.json").read_text(encoding="utf-8"))
        self.assertEqual(score.sha256(HERE / "d003_estimator.py"), score.EXPECTED["estimator"])
        self.assertTrue(protocol["assessment"]["no_post_score_tuning"])
        self.assertEqual(protocol["arms"][1]["captures"][0]["origin"], [0.1225, 0.1225, 0.4])


if __name__ == "__main__":
    unittest.main()
