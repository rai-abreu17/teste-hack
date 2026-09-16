import ast
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

import run_d004 as d004


class D004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((HERE / "protocol_d004.json").read_text(encoding="utf-8"))

    def test_exact_paired_poses_and_shared_centre(self):
        control, candidate = self.protocol["arms"]
        self.assertEqual([item["sequence"] for item in control["captures"]],
                         [201, 202, 203, 204, 101])
        self.assertEqual([item["sequence"] for item in candidate["captures"]],
                         [201, 202, 203, 204, 101])
        self.assertEqual([item["origin"][:2] for item in control["captures"][:4]], [
            [0.1, 0.1], [0.2, 0.1], [0.1, 0.2], [0.2, 0.2],
        ])
        self.assertEqual([item["origin"][:2] for item in candidate["captures"][:4]], [
            [0.1225, 0.1225], [0.1775, 0.1225],
            [0.1225, 0.1775], [0.1775, 0.1775],
        ])
        self.assertEqual(control["captures"][-1], candidate["captures"][-1])
        for arm in self.protocol["arms"]:
            for capture in arm["captures"]:
                self.assertEqual(capture["origin"][2], 0.4)
                self.assertEqual((capture["yaw_deg"], capture["tilt_deg"], capture["roll_deg"]),
                                 (0.0, 0.0, 0.0))

    def test_scene_matrix_is_exact_p001_nine(self):
        p001 = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(self.protocol["scenes"], p001["scenes"])
        self.assertEqual(len(self.protocol["scenes"]), 9)

    def test_capture_budget_and_sources(self):
        self.assertEqual(self.protocol["acquisition_budget"], {
            "archived_k4_frames_reused": 36,
            "archived_shared_centre_frames_reused": 9,
            "new_candidate_diagonal_frames": 36,
            "new_control_or_centre_frames": 0,
        })
        self.assertEqual(self.protocol["candidate_capture_sequences"], [201, 202, 203, 204])

    def test_estimator_contract_is_exact_d003(self):
        d003 = json.loads((HERE / "protocol_d003.json").read_text(encoding="utf-8"))
        self.assertEqual(self.protocol["estimator"], d003["candidate"])
        self.assertEqual(self.protocol["frozen_sources"][".ai/experiments/m001/d003_estimator.py"],
                         d003["frozen_sources"][".ai/experiments/m001/d003_estimator.py"])

    def test_acquisition_runner_has_no_truth_or_estimator_import(self):
        tree = ast.parse((HERE / "run_d004.py").read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse([name for name in imports
                          if name.startswith(("experiments", "truth", "d003_estimator",
                                              "r005_estimator", "server"))])

    def test_archived_centres_and_k4_are_hash_verified(self):
        selected, aliases = d004.verify_archived_inputs(self.protocol)
        self.assertEqual(len(selected), 45)
        self.assertEqual(len(aliases), 9)
        self.assertEqual(sum(item["role"] == "control_k4" for item in selected.values()), 36)
        self.assertEqual(sum(item["role"] == "shared_center_seq101"
                             for item in selected.values()), 9)

    def test_protocol_has_predeclared_stop_boundary(self):
        self.assertEqual(self.protocol["current_stop_boundary"],
                         "After acquisition validation and before reconstruction or volume scoring")
        self.assertTrue(self.protocol["assessment"]["no_post_score_tuning"])
        self.assertFalse(self.protocol["assessment"]["score_during_acquisition"])


if __name__ == "__main__":
    unittest.main()
