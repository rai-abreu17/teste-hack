import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

import run_r007
import run_r007_score as score


class R007PreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((HERE / "protocol_r007.json").read_text(encoding="utf-8"))

    def test_candidate_is_exact_d004_candidate_with_new_sequences(self):
        captures = self.protocol["candidate"]["captures"]
        self.assertEqual([item["sequence"] for item in captures], [701, 702, 703, 704, 705])
        self.assertEqual([item["origin"] for item in captures], [
            [0.1225, 0.1225, 0.4], [0.1775, 0.1225, 0.4],
            [0.1225, 0.1775, 0.4], [0.1775, 0.1775, 0.4],
            [0.15, 0.15, 0.4],
        ])
        for capture in captures:
            self.assertEqual((capture["yaw_deg"], capture["tilt_deg"], capture["roll_deg"]),
                             (0.0, 0.0, 0.0))
        d004 = json.loads((HERE / "protocol_d004.json").read_text(encoding="utf-8"))
        old = d004["arms"][1]["captures"]
        self.assertEqual([item["origin"] for item in captures], [item["origin"] for item in old])

    def test_scene_table_is_fixed_diverse_nonempty_and_new(self):
        scenes = self.protocol["scenes"]
        self.assertEqual(len(scenes), 12)
        self.assertEqual(len({scene["id"] for scene in scenes}), 12)
        self.assertTrue(all(scene["fill"] > 0 for scene in scenes))
        self.assertEqual({scene["shape"] for scene in scenes}, {0, 1, 2, 3, 4})
        self.assertLessEqual(min(scene["fill"] for scene in scenes), 25)
        self.assertGreaterEqual(max(scene["fill"] for scene in scenes), 90)
        self.assertTrue(any(scene["obstacle"] for scene in scenes))
        self.assertTrue(any(scene["dropout"] for scene in scenes))
        pyramid_centers = {scene["cx"] for scene in scenes if scene["shape"] == 0}
        self.assertTrue({0.11, 0.12, 0.17, 0.19}.issubset(pyramid_centers))
        d004 = json.loads((HERE / "protocol_d004.json").read_text(encoding="utf-8"))
        physical_keys = ("fill", "shape", "cx", "obstacle", "dropout")
        old = {tuple(scene[key] for key in physical_keys) for scene in d004["scenes"]}
        new = {tuple(scene[key] for key in physical_keys) for scene in scenes}
        self.assertEqual(len(new), 12)
        self.assertFalse(new & old)

    def test_acquisition_is_exactly_60_new_frames(self):
        acquisition = self.protocol["acquisition"]
        self.assertTrue(acquisition["new_frames_only"])
        self.assertFalse(acquisition["development_frame_reuse_allowed"])
        self.assertEqual(acquisition["views_per_scene"], 5)
        self.assertEqual(acquisition["expected_new_frame_count"], 60)
        self.assertEqual(acquisition["sequences"], [701, 702, 703, 704, 705])

    def test_primary_gate_is_exact_and_partial_fails(self):
        gate = self.protocol["primary_gate"]
        self.assertEqual(gate["required_total_eligible"], 12)
        self.assertEqual(gate["required_total_within_limit"], 12)
        self.assertEqual(gate["absolute_relative_total_volume_error_max"], 0.05)
        passing = [{"scene_id": f"s{i}", "total_selection": {"selected": True},
                    "primary_scene_pass": True} for i in range(12)]
        self.assertTrue(score.aggregate_gate(passing)["all_12_total_eligible_and_each_within_5pct"])
        passing[4] = {"scene_id": "s4", "total_selection": {"selected": False},
                      "primary_scene_pass": False}
        failed = score.aggregate_gate(passing)
        self.assertEqual(failed["partial_or_ineligible"], 1)
        self.assertFalse(failed["all_12_total_eligible_and_each_within_5pct"])

    def test_spatial_error_and_cancellation_are_diagnostic(self):
        cell_area = score.g.CELL ** 2
        result = score.domain_stats([2.0, 0.0], [cell_area, cell_area], [0, 1])
        self.assertAlmostEqual(result["signed_error_m3"], 0.0)
        self.assertAlmostEqual(result["integrated_absolute_error_m3"], 2 * cell_area)
        self.assertIsNone(result["cancellation_ratio"])
        self.assertEqual(self.protocol["secondary_diagnostics"]["gate_effect"].split(".")[0], "None")

    def test_acquisition_runner_cannot_import_estimator_or_truth(self):
        tree = ast.parse((HERE / "run_r007.py").read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = ("experiments", "truth", "d003_estimator", "r005_estimator", "server")
        self.assertFalse([name for name in imports if name.startswith(forbidden)])

    def test_truth_import_is_evaluator_local_and_after_reconstruction(self):
        tree = ast.parse((HERE / "run_r007_score.py").read_text(encoding="utf-8"))
        top_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                top_imports.append(node.module or "")
        self.assertFalse([name for name in top_imports if name.startswith("experiments")])
        evaluator = next(node for node in tree.body
                         if isinstance(node, ast.FunctionDef) and node.name == "evaluate_with_truth")
        evaluator_imports = [node.module for node in ast.walk(evaluator)
                             if isinstance(node, ast.ImportFrom)]
        self.assertIn("experiments", evaluator_imports)
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node.func.id for node in main.body if isinstance(node, ast.Assign)
                 and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                 for node in [node.value]]
        self.assertLess(calls.index("reconstruct_all"), calls.index("evaluate_with_truth"))

    def test_release_must_bind_reviewed_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            path.write_text(json.dumps({
                "experiment_id": "R-007",
                "decision": "RELEASE_R007_OPEN",
                "pre_open_manifest_sha256": "a" * 64,
                "reviewer": "independent-reviewer",
                "reviewed_at_utc": "2026-09-16T00:00:00Z",
            }), encoding="utf-8")
            release = run_r007.verify_release(
                path, "RELEASE_R007_OPEN", "pre_open_manifest_sha256", "a" * 64
            )
            self.assertEqual(release["decision"], "RELEASE_R007_OPEN")
            with self.assertRaises(RuntimeError):
                run_r007.verify_release(
                    path, "RELEASE_R007_OPEN", "pre_open_manifest_sha256", "b" * 64
                )

    def test_preopen_manifest_verifies_and_no_artifacts_exist(self):
        protocol, manifest = run_r007.verify_preopen(require_pristine=True)
        self.assertEqual(protocol["experiment_id"], "R-007")
        self.assertGreaterEqual(len(manifest["frozen_files"]), 12)
        self.assertFalse(run_r007.FRAMES.exists())
        self.assertFalse(run_r007.RESULTS.exists())
        self.assertFalse(run_r007.COMMANDS.exists())
        self.assertFalse(run_r007.ACQUISITION.exists())
        self.assertFalse(run_r007.ACQUISITION_VALIDATION.exists())


if __name__ == "__main__":
    unittest.main()
