import ast
import json
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / ".ai" / "runs" / "m001-implementation"
BIN = RUN / "bin" / "scene_dump_m001.exe"
LEGACY_BIN = RUN / "bin" / "scene_dump_legacy.exe"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from server import geometry as g
from m001_estimator import fuse_frames


def capture(sequence=101, yaw=0, tilt=0, x=.15, y=.15, dropout=0):
    args = [.75, 0, .15, 0, dropout, 4, sequence, yaw, tilt, .40, x, y]
    return subprocess.check_output([str(BIN), *map(str, args)])


class P001Tests(unittest.TestCase):
    def test_frame_and_pose_are_valid(self):
        decoded = g.decode_frame(capture(yaw=-20, tilt=10, x=.10, y=.20))
        self.assertEqual(decoded["sequence"], 101)
        self.assertAlmostEqual(decoded["sensor_pose"]["translation_m"][0], .10, places=6)
        self.assertAlmostEqual(decoded["sensor_pose"]["translation_m"][1], .20, places=6)
        self.assertEqual(decoded["sensor_pose"]["yaw_deg"], -20)
        self.assertEqual(decoded["sensor_pose"]["tilt_deg"], 10)

    def test_one_view_reproduces_geometry_estimate(self):
        raw = capture()
        fused = fuse_frames([raw], {"reference_offset_m": 0.0})
        expected = g.estimate(raw)
        self.assertEqual(fused["heights"], expected["grid"]["height_m"])
        self.assertEqual(fused["measurement_state"], expected["measurement_state"])

    def test_no_dropout_repetition_changes_neither_height_nor_support(self):
        frames = [capture(sequence=n) for n in (101, 102, 103)]
        one = fuse_frames(frames[:1], {"reference_offset_m": 0.0})
        three = fuse_frames(frames, {"reference_offset_m": 0.0})
        self.assertEqual(one["heights"], three["heights"])
        self.assertEqual(one["tin_support_union_cell_count"], three["tin_support_union_cell_count"])
        self.assertEqual(three["view_disagreement"]["max_height_range_m"], 0.0)

    def test_frame_order_does_not_change_fusion(self):
        frames = [capture(sequence=101, tilt=-10), capture(sequence=102),
                  capture(sequence=103, tilt=10)]
        direct = fuse_frames(frames, {"reference_offset_m": 0.0})
        reverse = fuse_frames(list(reversed(frames)), {"reference_offset_m": 0.0})
        self.assertEqual(direct["heights"], reverse["heights"])
        self.assertEqual(direct["tin_support_union_cell_count"], reverse["tin_support_union_cell_count"])

    def test_evaluator_truth_does_not_leak_into_fusion(self):
        tree = ast.parse((HERE / "m001_estimator.py").read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(name == "experiments.truth" or name.endswith(".truth") for name in imports))
        with self.assertRaises(ValueError):
            fuse_frames([capture()], {"scene": "must not enter estimator"})

    def test_new_harness_defaults_match_original_harness_exactly(self):
        args = [75, 0, .15, 0, 0, 4, 7, 0, 0, .40]
        old = subprocess.check_output([str(LEGACY_BIN), *map(str, args)])
        new = subprocess.check_output([str(BIN), *map(str, args)])
        self.assertEqual(old, new)  # Includes sequence, timestamp, pose and CRC.

    def test_protocol_count_and_aim_angles_are_frozen(self):
        protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["comparison_count"], len(protocol["scenes"]) * len(protocol["arms"]))
        aimed = next(arm for arm in protocol["arms"] if arm["id"] == "translated3_aimed")
        self.assertAlmostEqual(aimed["captures"][0]["tilt_deg"], -7.125016348901798, places=12)
        self.assertAlmostEqual(aimed["captures"][2]["tilt_deg"], 7.1250163489018, places=12)


if __name__ == "__main__":
    unittest.main()
