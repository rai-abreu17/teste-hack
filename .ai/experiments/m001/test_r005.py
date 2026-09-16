import json
import math
from pathlib import Path
import struct
import sys
import unittest
import zlib


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = ROOT / ".ai" / "runs" / "m001-implementation" / "results"
sys.path[:0] = [str(ROOT), str(HERE)]

from m001_estimator import fuse_frames as p001_fuse_frames
from r005_estimator import analyze_frame, fuse_frames
from server import geometry as g


def archived_paths():
    return sorted((RESULTS / "frames").glob("*/*.bin"))


def frame_with_below_reference(raw):
    """Make one valid-return point fail only the below-reference gate."""
    data = bytearray(raw)
    pose = struct.unpack_from("<6f", data, 32)
    points = g.decode_frame(raw)["points_by_ray"]
    target = min((i for i, point in enumerate(points) if point is not None),
                 key=lambda i: (points[i][0]-.15)**2 + (points[i][1]-.15)**2)
    record = 64 + target * 10
    mm, ux, uy, uz, status, reserved = struct.unpack_from("<HhhhBB", data, record)
    norm = math.sqrt(ux*ux+uy*uy+uz*uz)
    direction = g.rotate((ux/norm, uy/norm, uz/norm), pose[3], pose[4])
    below_floor_mm = round((-.01-pose[2])/direction[2]*1000)
    struct.pack_into("<HhhhBB", data, record, below_floor_mm, ux, uy, uz, status, reserved)
    crc = zlib.crc32(data[64:], zlib.crc32(data[:60]))
    struct.pack_into("<I", data, 60, crc)
    decoded = g.decode_frame(bytes(data))
    if decoded["excluded"]["below_reference"] == 0:
        raise AssertionError(f"fixture did not create below-reference point at pose {pose}")
    return bytes(data)


class R005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = archived_paths()
        cls.raw = cls.paths[0].read_bytes()

    def test_archive_has_frozen_cardinality(self):
        protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.paths), 225)
        self.assertEqual(len(protocol["scenes"]) * len(protocol["arms"]), 72)

    def test_every_archived_frame_matches_geometry_estimate_exactly(self):
        for path in self.paths:
            with self.subTest(path=path.name):
                result = analyze_frame(path.read_bytes())
                expected = g.estimate(path.read_bytes())
                self.assertEqual(result["heights"], expected["grid"]["height_m"])
                self.assertEqual(result["measurement_state"], expected["measurement_state"])

    def test_all_archived_arms_preserve_conventional_baseline(self):
        protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
        comparisons = json.loads((RESULTS / "comparisons.json").read_text(encoding="utf-8"))
        by_scene = {item["scene_id"]: item for item in comparisons["scenes"]}
        checked = 0
        for scene in protocol["scenes"]:
            arms = {item["arm_id"]: item for item in by_scene[scene["id"]]["arms"]}
            for arm in protocol["arms"]:
                paths = sorted((RESULTS / "frames" / scene["id"]).glob(f"{arm['id']}-*.bin"))
                frames = [path.read_bytes() for path in paths]
                current = fuse_frames(frames)
                historical = p001_fuse_frames(frames, {"reference_offset_m": 0.0})
                self.assertEqual(current["heights"], historical["heights"])
                self.assertEqual(current["heights"], arms[arm["id"]]["heights"])
                self.assertEqual(current["measurement_state"], historical["measurement_state"])
                self.assertEqual(current["total_selection"], historical["total_selection"])
                self.assertEqual(current["total_volume_m3"], historical["total_volume_m3"])
                self.assertEqual(
                    current["tin_support_union_fraction"],
                    historical["tin_support_union_fraction"],
                )
                checked += 1
        self.assertEqual(checked, 72)

    def test_contributor_average_and_quality_are_coherent(self):
        result = analyze_frame(self.raw)
        self.assertEqual(len(result["heights"]), 400)
        self.assertEqual(len(result["contributions"]), 400)
        self.assertEqual(len(result["quality"]), 400)
        for height, contributions, quality in zip(
                result["heights"], result["contributions"], result["quality"]):
            if not contributions:
                self.assertIsNone(height)
                self.assertIsNone(quality)
                continue
            self.assertEqual(
                height,
                sum(item["height_m"] for item in contributions) / len(contributions),
            )
            self.assertEqual(
                quality,
                sum(item["max_edge_m"] for item in contributions) / len(contributions),
            )
            for item in contributions:
                self.assertEqual(len(item["triangle_indices"]), 3)
                self.assertGreater(item["projected_area_m2"], 0.0)
                self.assertLessEqual(item["max_edge_m"], g.MAX_EDGE_M)

    def test_crc_corruption_is_rejected_as_one_indexed_frame(self):
        corrupt = bytearray(self.raw)
        corrupt[-1] ^= 1
        result = fuse_frames([bytes(corrupt)])
        self.assertEqual([item["index"] for item in result["invalid_frames"]], [0])
        self.assertEqual(result["measurement_state"], "unavailable")
        self.assertIsNone(result["total_volume_m3"])

    def test_invalid_between_valid_preserves_original_indices_and_rejects_total(self):
        corrupt = bytearray(self.raw)
        corrupt[-1] ^= 1
        result = fuse_frames([self.raw, bytes(corrupt), self.raw])
        self.assertEqual([view["index"] for view in result["per_view"]], [0, 2])
        self.assertEqual([item["index"] for item in result["invalid_frames"]], [1])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertIn("invalid_frames_1", result["total_selection"]["rejection_reasons"])
        self.assertEqual(result["measurement_state"], "partial")

    def test_unavailable_view_with_partial_heights_is_skipped_and_rejects_total(self):
        unavailable = frame_with_below_reference(self.raw)
        view = analyze_frame(unavailable)
        self.assertEqual(view["measurement_state"], "unavailable")
        self.assertTrue(any(height is not None for height in view["heights"]))
        result = fuse_frames([self.raw, unavailable])
        self.assertEqual(result["heights"], analyze_frame(self.raw)["heights"])
        self.assertEqual(result["unavailable_view_indices"], [1])
        self.assertFalse(result["total_selection"]["selected"])
        self.assertIn("unavailable_views_1", result["total_selection"]["rejection_reasons"])

    def test_empty_and_invalid_inputs(self):
        result = fuse_frames([])
        self.assertEqual(result["measurement_state"], "unavailable")
        self.assertEqual(result["tin_support_union_fraction"], 0.0)
        self.assertIsNone(result["total_volume_m3"])
        for config in (
                {"reference_offset_m": math.nan},
                {"reference_offset_m": math.inf},
                {"reference_offset_m": 0.11},
                {"truth": "forbidden"},
                [],
        ):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    fuse_frames([], config)
        with self.assertRaises(ValueError):
            analyze_frame(self.raw, math.nan)
        with self.assertRaises(ValueError):
            fuse_frames([], trim_kappa=math.nan)
        with self.assertRaises(ValueError):
            fuse_frames([], lower=1)

    def test_lower_median_and_trimming_use_per_view_quality(self):
        paths = sorted((RESULTS / 'frames' / 'pyramid_beam').glob('translated3_aimed-*.bin'))
        frames = [path.read_bytes() for path in paths]
        conventional = fuse_frames(frames)
        lower = fuse_frames(frames, lower=True)
        trimmed = fuse_frames(frames, trim_kappa=1.0)
        for cell in range(g.NX * g.NY):
            candidates = [
                (view["quality"][cell], view["index"], view["heights"][cell])
                for view in conventional["per_view"]
                if view["measurement_state"] != "unavailable"
                and view["heights"][cell] is not None
            ]
            if not candidates:
                continue
            values = sorted(item[2] for item in candidates)
            self.assertEqual(lower["heights"][cell], values[(len(values) - 1) // 2])
            minimum = min(item[0] for item in candidates)
            retained = [item[2] for item in candidates if item[0] <= minimum]
            self.assertEqual(trimmed["heights"][cell], statistics_median(retained))

    def test_faults_never_select_total_in_any_factorial_arm(self):
        good = (RESULTS / 'frames/pyramid_center/baseline_fixed1-1.bin').read_bytes()
        self.assertTrue(fuse_frames([good])["total_selection"]["selected"])
        for kappa in (None, 2.0):
            for lower in (False, True):
                for bad in (b'', good[:-1], b'bad', None):
                    result = fuse_frames([good, bad, good], trim_kappa=kappa, lower=lower)
                    self.assertFalse(result['total_selection']['selected'])
                    self.assertIsNone(result['total_volume_m3'])
                    self.assertEqual([v['index'] for v in result['per_view']], [0, 2])
                    self.assertEqual(result['heights'], analyze_frame(good)['heights'])

    def test_estimator_has_no_truth_or_evaluation_imports(self):
        import ast
        tree = ast.parse((HERE / 'r005_estimator.py').read_text(encoding='utf-8'))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or '')
        self.assertEqual([s for s in imports if s.startswith(('experiments', 'run_', 'truth'))], [])


def statistics_median(values):
    values = sorted(values)
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


if __name__ == "__main__":
    unittest.main()
