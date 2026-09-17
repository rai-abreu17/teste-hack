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
                "review_type": "automated-review",
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



from unittest.mock import patch, MagicMock

class R007ValidationTamperingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((HERE / "protocol_r007.json").read_text(encoding="utf-8"))
        cls.plan = run_r007.derive_canonical_plan(cls.protocol)
        
    def setUp(self):
        # Create a valid baseline
        self.commands = []
        self.recorded = {}
        for entry in self.plan:
            self.commands.append({
                "kind": "r007_reserved_capture",
                "command_id": entry["command_id"],
                "scene_id": entry["scene_id"],
                "sequence": entry["sequence"],
                "command": entry["argv"],
                "exit_code": 0,
                "stderr": "",
                "stdout_bytes": 704,
                "stdout_sha256": "hash_file",
                "stdout_path": entry["stdout_path"],
            })
            self.recorded[entry["stdout_path"]] = {
                "sha256": "hash_file",
                "scene_id": entry["scene_id"],
                "header": {
                    "sequence": entry["sequence"],
                    "sensor_pose": {
                        "translation_m": entry["pose"]["origin"],
                        "yaw_deg": entry["pose"]["yaw_deg"],
                        "tilt_deg": entry["pose"]["tilt_deg"],
                        "roll_deg": entry["pose"]["roll_deg"]
                    },
                    "bytes": 704,
                    "crc32": "fakecrc"
                }
            }
        
        self.acquisition = {
            "experiment_id": "R-007",
            "pre_open_manifest_sha256": "hash_preopen",
            "protocol_sha256": run_r007.sha256(HERE / "protocol_r007.json"),
            "simulator_sha256": "hash_sim",
            "candidate_frames": self.recorded,
            "capture_commands_sha256": "hash_file",
            "counts": {"development_frames_reused": 0},
            "truth_imported": False,
            "estimator_imported": False,
            "volume_results_present": False,
        }
        
        self.patcher_preopen = patch("run_r007.verify_preopen")
        self.mock_preopen = self.patcher_preopen.start()
        self.mock_preopen.return_value = (self.protocol, {"frozen_files": {}})
        
        self.patcher_acq = patch("run_r007.ACQUISITION")
        self.mock_acq = self.patcher_acq.start()
        self.mock_acq.read_text.side_effect = lambda **k: json.dumps(self.acquisition)
        
        self.patcher_cmd = patch("run_r007.COMMANDS")
        self.mock_cmd = self.patcher_cmd.start()
        self.mock_cmd.read_text.side_effect = lambda **k: json.dumps(self.commands)
        
        self.patcher_plan = patch("run_r007.CAPTURE_PLAN")
        self.mock_plan = self.patcher_plan.start()
        self.mock_plan.read_text.side_effect = lambda **k: json.dumps(self.plan)
        
        self.patcher_frames = patch("run_r007.FRAMES", new_callable=MagicMock)
        self.mock_frames = self.patcher_frames.start()
        self.mock_frames.exists.return_value = True
        
        # Mock paths
        self.patcher_rglob = patch("pathlib.Path.rglob")
        self.mock_rglob = self.patcher_rglob.start()
        self.mock_rglob.return_value = [] # results.rglob
        
        self.patcher_iterdir = patch("pathlib.Path.iterdir")
        self.mock_iterdir = self.patcher_iterdir.start()
        
        self.patcher_glob = patch('pathlib.Path.glob')
        self.mock_glob = self.patcher_glob.start()
        self.patcher_read_bytes = patch('pathlib.Path.read_bytes')
        self.mock_read_bytes = self.patcher_read_bytes.start()
        self.mock_read_bytes.return_value = b'fake'
        
        self.patcher_sha256 = patch("run_r007.sha256")
        self.mock_sha256 = self.patcher_sha256.start()
        self.mock_sha256.side_effect = self.fake_sha256
        
        self.patcher_validate_header = patch("run_r007.validate_frame_header")
        self.mock_validate_header = self.patcher_validate_header.start()
        self.mock_validate_header.side_effect = self.fake_validate_header
        
        self.patcher_results = patch("run_r007.RESULTS", new_callable=MagicMock)
        self.mock_results = self.patcher_results.start()
        self.mock_results.exists.return_value = False
        self.mock_results.rglob.return_value = []
        
        self.patcher_acq_val = patch("run_r007.ACQUISITION_VALIDATION", new_callable=MagicMock)
        self.mock_acq_val = self.patcher_acq_val.start()

    def tearDown(self):
        patch.stopall()
        
    def fake_sha256(self, path):
        if str(path).endswith("protocol_r007.json"):
            return "174d056b6e1e057167a55d8e8a09b6b4defdf13cb3e2939eddf703f005ceb232"
        if str(path).endswith("pre-open-manifest.json"):
            return "hash_preopen"
        if str(path).endswith("scene_dump_m001.exe"):
            return "hash_sim"
        key = run_r007.relative(path)
        if key in self.recorded:
            return self.recorded[key]["sha256"]
        return "hash_file"

    def fake_validate_header(self, raw, expected_capture):
        # Find which key this would correspond to
        seq = expected_capture['sequence']
        origin = expected_capture['origin']
        for key, item in self.recorded.items():
            if item['header']['sequence'] == seq and item['header']['sensor_pose']['translation_m'] == origin:
                return item['header']
        raise RuntimeError('header mismatch')

    def _setup_mock_filesystem(self):
        # mock FRAMES.rglob to return 60 files
        mock_paths = []
        for key in self.recorded:
            mock_path = MagicMock()
            mock_path.name = Path(key).name
            mock_path.read_bytes.return_value = b"fake"
            # allow relative() to work by pretending it's relative to root
            mock_path.relative_to.return_value = Path(key)
            mock_paths.append(mock_path)
            
        self.mock_frames.rglob.return_value = mock_paths
        
        # mock FRAMES.iterdir for scene dirs
        scene_dirs = []
        for s in set(item["scene_id"] for item in self.plan):
            mock_dir = MagicMock()
            mock_dir.name = s
            mock_dir.is_dir.return_value = True
            scene_dirs.append(mock_dir)
        self.mock_frames.iterdir.return_value = scene_dirs
        
        # mock FRAMES / scene_id glob
        def side_glob(pattern):
            return [1,2,3,4,5]
        self.mock_frames.__truediv__.return_value.glob.side_effect = side_glob
        
        # We also have to mock pathlib.Path reading in validate_acquisition for frame paths.
        # It does `path = ROOT / plan_entry["stdout_path"]`, then `key = relative(path)`.
        # `key in recorded` works because we use strings.
        # `header = validate_frame_header(path.read_bytes(), capture_spec)` needs `path.read_bytes`.
        # Instead of mocking Path everywhere, we mock `path.read_bytes` inside `validate_acquisition`? No, we already mocked `validate_frame_header` so we don't need real bytes.
        pass

    def run_validation(self):
        self._setup_mock_filesystem()
        try:
            return run_r007.validate_acquisition()
        except RuntimeError:
            # We intercept the exception and read what was written to validation
            written = json.loads(self.mock_acq_val.write_text.call_args[0][0])
            return written

    def test_baseline_passes(self):
        val = self.run_validation()
        
        self.assertTrue(val["passed"])
        
    def test_tampering_swap_scene_id(self):
        self.commands[0]["scene_id"] = "different_scene"
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_change_argv(self):
        self.commands[0]["command"][0] = "malicious.exe"
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_change_sequence(self):
        self.commands[0]["sequence"] = 999
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_reorder_commands(self):
        self.commands[0], self.commands[1] = self.commands[1], self.commands[0]
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_extra_frame(self):
        self.commands.append(self.commands[0].copy())
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])
        
    def test_tampering_missing_frame(self):
        self.commands.pop()
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_duplicate_stdout_path(self):
        self.commands[1]["stdout_path"] = self.commands[0]["stdout_path"]
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_duplicate_command_id(self):
        self.commands[1]["command_id"] = self.commands[0]["command_id"]
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_replace_hash(self):
        key = self.plan[0]["stdout_path"]
        self.recorded[key]["sha256"] = "altered"
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_replace_stdout_sha256(self):
        self.commands[0]["stdout_sha256"] = "altered"
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])

    def test_tampering_repoint_valid_frame(self):
        # Scene 1 claims it has the file of Scene 2
        key1 = self.plan[0]["stdout_path"]
        key2 = self.plan[1]["stdout_path"]
        self.recorded[key1] = self.recorded[key2].copy()
        # Even if we change scene_id to match, it should fail hash checks or plan checks
        val = self.run_validation()
        self.assertFalse(val["passed"])
        self.assertFalse(val["checks"]["capture_plan_matches"])


if __name__ == '__main__':
    unittest.main()
