"""Execute frozen D-002: fixed3 at z=.40 (archived) versus z=.50 (new).

This is a simulated acquisition development experiment.  The estimator sees
only frame bytes.  Scene truth is constructed only after every frame has been
validated and both acquisition arms have been estimated.
"""

import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / ".ai" / "runs" / "m001-d002" / "results"
ARCHIVE = ROOT / ".ai" / "runs" / "m001-implementation" / "results"
P001_PROTOCOL = HERE / "protocol.json"
P001_RESULTS = ARCHIVE / "comparisons.json"
PROTOCOL = HERE / "protocol_d002.json"
PROTOCOL_HASH = HERE / "protocol_d002.sha256"

sys.path[:0] = [str(ROOT), str(HERE)]
from experiments import truth
from server import geometry as g
from r005_estimator import fuse_frames


EXPECTED_SCENE_KEYS = {"id", "fill", "shape", "cx", "obstacle", "dropout"}
ACQUISITION_IDS = ("control_fixed3", "candidate_fixed3_z050")
CELL_COUNT = g.NX * g.NY
CELL_AREA = g.CELL ** 2


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path):
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message):
    raise RuntimeError(message)


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f"{label} must be a finite number")
    return float(value)


def load_and_validate_protocol():
    if not PROTOCOL.is_file() or not PROTOCOL_HASH.is_file():
        fail("D002 protocol and hash must exist before capture")
    expected_hash = PROTOCOL_HASH.read_text(encoding="utf-8").split()
    if len(expected_hash) != 1 or expected_hash[0] != sha256(PROTOCOL):
        fail("frozen D002 protocol hash mismatch")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("experiment_id") not in ("D-002", "D002"):
        fail("unexpected experiment_id")
    if protocol.get("expected_frame_bytes") != 704:
        fail("D002 requires expected_frame_bytes=704")
    if finite_number(protocol.get("range_m"), "range_m") != 4.0:
        fail("D002 requires range_m=4.0")
    scenes = protocol.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        fail("D002 requires exactly nine scenes")
    if len({scene.get("id") for scene in scenes if isinstance(scene, dict)}) != 9:
        fail("D002 scene ids must be unique")
    for scene in scenes:
        if not isinstance(scene, dict) or set(scene) != EXPECTED_SCENE_KEYS:
            fail("each D002 scene must contain exactly id/fill/shape/cx/obstacle/dropout")

    acquisitions = protocol.get("acquisitions")
    if not isinstance(acquisitions, dict) or set(acquisitions) != set(ACQUISITION_IDS):
        fail(f"acquisitions must be exactly {ACQUISITION_IDS}")
    for acquisition_id in ACQUISITION_IDS:
        acquisition = acquisitions[acquisition_id]
        if not isinstance(acquisition, dict):
            fail(f"{acquisition_id} must be an object")
        poses = acquisition.get("sensor_poses")
        if not isinstance(poses, list) or len(poses) != 3:
            fail(f"{acquisition_id} requires three sensor_poses")
        for index, pose in enumerate(poses):
            if not isinstance(pose, dict) or set(pose) != {"origin", "yaw_deg", "tilt_deg", "sequence"}:
                fail(f"malformed pose {index} in {acquisition_id}")
            origin = pose["origin"]
            if not isinstance(origin, list) or len(origin) != 3:
                fail(f"malformed origin in {acquisition_id} pose {index}")
            values = [finite_number(v, f"{acquisition_id}.origin") for v in origin]
            yaw = finite_number(pose["yaw_deg"], f"{acquisition_id}.yaw_deg")
            tilt = finite_number(pose["tilt_deg"], f"{acquisition_id}.tilt_deg")
            if isinstance(pose["sequence"], bool) or pose["sequence"] != (101 + index):
                fail(f"unexpected sequence in {acquisition_id} pose {index}")
            expected_z = 0.4 if acquisition_id == "control_fixed3" else 0.5
            if values != [0.15, 0.15, expected_z] or yaw != 0.0 or tilt != 0.0:
                fail(f"unexpected D002 pose in {acquisition_id} pose {index}")
    if acquisitions["control_fixed3"].get("archive_arm_id") != "fixed3":
        fail("control_fixed3 must reference archived arm fixed3")
    if acquisitions["candidate_fixed3_z050"].get("archive_arm_id") not in (None, ""):
        fail("candidate acquisition cannot reference an archived arm")

    frozen_sources = protocol.get("frozen_sources")
    if not isinstance(frozen_sources, dict) or not frozen_sources:
        fail("frozen_sources is required")
    for name, expected in frozen_sources.items():
        path = ROOT / name
        if not path.is_file():
            fail(f"missing frozen source: {name}")
        if not isinstance(expected, str) or sha256(path) != expected:
            fail(f"frozen source hash mismatch: {name}")
    executable_name = protocol.get("generator_executable")
    if executable_name not in frozen_sources:
        fail("generator executable must be included in frozen_sources")
    executable = ROOT / executable_name
    if not executable.is_file():
        fail("frozen generator executable does not exist")
    return protocol, executable


def validate_against_archive(protocol):
    p001_protocol = json.loads(P001_PROTOCOL.read_text(encoding="utf-8"))
    if protocol["scenes"] != p001_protocol["scenes"]:
        fail("D002 scene definitions differ from archived P001 protocol")
    fixed3 = next((arm for arm in p001_protocol["arms"] if arm.get("id") == "fixed3"), None)
    if fixed3 is None:
        fail("archived fixed3 arm is missing")
    if protocol["acquisitions"]["control_fixed3"]["sensor_poses"] != fixed3["captures"]:
        fail("D002 control poses differ from archived fixed3 poses")
    original = json.loads(P001_RESULTS.read_text(encoding="utf-8"))
    if [entry.get("scene_id") for entry in original.get("scenes", [])] != [
            scene["id"] for scene in protocol["scenes"]]:
        fail("archived P001 result scene order differs from D002")
    return original


def close(actual, expected):
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6)


def validate_frame(raw, pose, protocol, label):
    if not isinstance(raw, bytes) or len(raw) != protocol["expected_frame_bytes"]:
        fail(f"{label}: expected exactly {protocol['expected_frame_bytes']} frame bytes")
    try:
        decoded = g.decode_frame(raw, reference_offset_m=0.0)
    except Exception as exc:
        fail(f"{label}: frame decode/CRC validation failed: {exc}")
    if decoded["sequence"] != pose["sequence"]:
        fail(f"{label}: sequence mismatch")
    if decoded["acquisition_start_ms"] != pose["sequence"] * 3000:
        fail(f"{label}: deterministic acquisition timestamp mismatch")
    if decoded["acquisition_duration_ms"] != 100:
        fail(f"{label}: acquisition duration mismatch")
    if decoded["columns"] != 8 or decoded["rows"] != 8 or not close(decoded["range_m"], protocol["range_m"]):
        fail(f"{label}: frame geometry/range mismatch")
    actual_pose = decoded["sensor_pose"]
    if (not all(close(a, e) for a, e in zip(actual_pose["translation_m"], pose["origin"]))
            or not close(actual_pose["yaw_deg"], pose["yaw_deg"])
            or not close(actual_pose["tilt_deg"], pose["tilt_deg"])
            or not close(actual_pose["roll_deg"], 0.0)):
        fail(f"{label}: frame pose mismatch")
    if len(decoded["readings"]) != 64 or len(decoded["points_by_ray"]) != 64:
        fail(f"{label}: expected exactly 64 readings")
    return decoded


def control_frames(scene, control_spec, original_entry, protocol, input_hashes):
    archive_arm_id = control_spec["archive_arm_id"]
    arm = next((item for item in original_entry["arms"] if item["arm_id"] == archive_arm_id), None)
    if arm is None or len(arm.get("per_view", [])) != 3:
        fail(f"{scene['id']}: archived fixed3 result is incomplete")
    frames = []
    for index, (pose, archived_view) in enumerate(zip(control_spec["sensor_poses"], arm["per_view"]), 1):
        path = ARCHIVE / "frames" / scene["id"] / f"{archive_arm_id}-{index}.bin"
        if not path.is_file():
            fail(f"missing archived control frame: {relative_path(path)}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != archived_view["sha256"]:
            fail(f"archived control hash mismatch: {relative_path(path)}")
        validate_frame(raw, pose, protocol, f"{scene['id']} control view {index}")
        input_hashes[relative_path(path)] = digest
        frames.append(raw)
    before = time.perf_counter()
    fused = fuse_frames(frames, {"reference_offset_m": 0.0})
    elapsed_ms = (time.perf_counter() - before) * 1000.0
    if fused["heights"] != arm["heights"]:
        fail(f"{scene['id']}: R005 control heights differ from archived fixed3 heights")
    return frames, fused, elapsed_ms


def capture_candidate(executable, scene, candidate_spec, protocol, command_log):
    frames = []
    for index, pose in enumerate(candidate_spec["sensor_poses"], 1):
        command = [
            str(executable), str(scene["fill"]), str(scene["shape"]), str(scene["cx"]),
            str(scene["obstacle"]), str(scene["dropout"]), str(protocol["range_m"]),
            str(pose["sequence"]), str(pose["yaw_deg"]), str(pose["tilt_deg"]),
            str(pose["origin"][2]), str(pose["origin"][0]), str(pose["origin"][1]),
        ]
        started = utc_now()
        before = time.perf_counter()
        completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, check=False)
        elapsed_ms = (time.perf_counter() - before) * 1000.0
        command_log.append({
            "kind": "new_candidate_capture", "scene_id": scene["id"], "view_index": index - 1,
            "command": command, "started_at_utc": started, "finished_at_utc": utc_now(),
            "elapsed_ms": elapsed_ms, "exit_code": completed.returncode,
            "stdout_bytes": len(completed.stdout),
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr": completed.stderr.decode("utf-8", errors="replace"),
        })
        if completed.returncode != 0:
            fail(f"candidate capture failed for {scene['id']} view {index}")
        validate_frame(completed.stdout, pose, protocol, f"{scene['id']} candidate view {index}")
        frames.append(completed.stdout)
    return frames


def point_bin(point):
    ix, iy = math.floor(point[0] / g.CELL), math.floor(point[1] / g.CELL)
    return iy * g.NX + ix if 0 <= ix < g.NX and 0 <= iy < g.NY else None


def acquisition_diagnostics(result):
    union_bins = set()
    per_view = []
    for view in result["per_view"]:
        bins = {point_bin(point) for point in view["decoded"]["points_by_ray"] if point is not None}
        bins.discard(None)
        union_bins.update(bins)
        per_view.append({
            "index": view["index"], "sha256": view["sha256"],
            "sequence": view["decoded"]["sequence"], "pose": view["decoded"]["sensor_pose"],
            "measurement_state": view["measurement_state"],
            "usable_point_count": sum(point is not None for point in view["decoded"]["points_by_ray"]),
            "direct_usable_point_bin_count": len(bins),
            "tin_support_cell_count": sum(height is not None for height in view["heights"]),
            "excluded": view["decoded"]["excluded"],
        })
    return {
        "per_view": per_view,
        "direct_usable_point_bin_union_count": len(union_bins),
        "direct_usable_point_bin_union_fraction": len(union_bins) / CELL_COUNT,
        "tin_support_union_cell_count": result["tin_support_union_cell_count"],
        "tin_support_union_fraction": result["tin_support_union_fraction"],
    }


def stats(heights, reference, indices):
    indices = list(indices)
    if any(heights[index] is None for index in indices):
        fail("attempted to score an unsupported cell")
    residuals = [heights[index] * CELL_AREA - reference[index] for index in indices]
    truth_volume = sum(reference[index] for index in indices)
    estimated_volume = sum(heights[index] * CELL_AREA for index in indices) if indices else None
    signed = sum(residuals)
    spatial = sum(abs(value) for value in residuals)
    return {
        "cell_count": len(indices), "area_m2": len(indices) * CELL_AREA,
        "truth_volume_m3": truth_volume, "estimated_volume_m3": estimated_volume,
        "signed_error_m3": signed, "absolute_volume_error_m3": abs(signed),
        "integrated_absolute_error_m3": spatial,
        "signed_error_percent": 100.0 * signed / truth_volume if truth_volume else None,
        "absolute_error_percent": 100.0 * abs(signed) / truth_volume if truth_volume else None,
        "spatial_error_percent": 100.0 * spatial / truth_volume if truth_volume else None,
        "mean_absolute_height_error_mm": (
            1000.0 * spatial / (len(indices) * CELL_AREA) if indices else None),
    }


def evaluate_pair(scene, control, candidate, control_ms, candidate_ms):
    # Evaluation-only truth starts here; neither fuse_frames call receives it.
    truth_scene = truth.Scene(
        fill=scene["fill"], shape=scene["shape"], cx=scene["cx"],
        obstacle=scene["obstacle"], dropout=scene["dropout"], range_m=4.0,
        sensor_z=0.4,
    )
    reference = truth.cell_volumes(truth_scene)
    analytical = truth.analytical_volume(truth_scene)
    if not math.isclose(sum(reference), analytical, rel_tol=1e-10, abs_tol=1e-14):
        fail(f"{scene['id']}: exact cell truth differs from analytical truth")
    masks = {
        "control_fixed3": [height is not None for height in control["heights"]],
        "candidate_fixed3_z050": [height is not None for height in candidate["heights"]],
    }
    common = [index for index in range(CELL_COUNT) if all(mask[index] for mask in masks.values())]
    acquisitions = {}
    for acquisition_id, result, elapsed_ms in (
            ("control_fixed3", control, control_ms),
            ("candidate_fixed3_z050", candidate, candidate_ms)):
        own = [index for index, supported in enumerate(masks[acquisition_id]) if supported]
        missing = [index for index, supported in enumerate(masks[acquisition_id]) if not supported]
        eligible = result["total_selection"]["selected"]
        if eligible != (len(own) == CELL_COUNT and not result["invalid_frames"]
                        and not result["unavailable_view_indices"]):
            fail(f"{scene['id']} {acquisition_id}: inconsistent total eligibility")
        whole = stats(result["heights"], reference, range(CELL_COUNT)) if eligible else None
        if eligible and not math.isclose(result["total_volume_m3"], whole["estimated_volume_m3"],
                                         rel_tol=0.0, abs_tol=1e-15):
            fail(f"{scene['id']} {acquisition_id}: total volume mismatch")
        acquisitions[acquisition_id] = {
            "algorithm_id": result["algorithm_id"], "measurement_state": result["measurement_state"],
            "support_cells": len(own), "missing_cells": len(missing),
            "total_selection": result["total_selection"],
            "whole_box": whole,
            "company_5pct_total_only": (
                whole["absolute_error_percent"] <= 5.0 if whole is not None
                and whole["absolute_error_percent"] is not None else None),
            "own_supported": stats(result["heights"], reference, own),
            "paired_common_support": stats(result["heights"], reference, common),
            "missing_truth_volume_m3": sum(reference[index] for index in missing),
            "estimator_elapsed_ms_single_run": elapsed_ms,
            "sampling_and_support": acquisition_diagnostics(result),
        }
    lost = [index for index in range(CELL_COUNT) if masks["control_fixed3"][index]
            and not masks["candidate_fixed3_z050"][index]]
    gained = [index for index in range(CELL_COUNT) if masks["candidate_fixed3_z050"][index]
              and not masks["control_fixed3"][index]]
    return {
        "scene_id": scene["id"], "reference_total_m3": analytical,
        "acquisitions": acquisitions,
        "support_change_candidate_vs_control": {
            "common_cell_count": len(common), "lost_cell_count": len(lost),
            "gained_cell_count": len(gained),
            "lost_truth_volume_m3": sum(reference[index] for index in lost),
            "gained_truth_volume_m3": sum(reference[index] for index in gained),
        },
    }


def summary_rows(scene_records):
    rows = []
    for record in scene_records:
        change = record["support_change_candidate_vs_control"]
        for acquisition_id in ACQUISITION_IDS:
            item = record["acquisitions"][acquisition_id]
            diagnostics = item["sampling_and_support"]
            rows.append({
                "scene_id": record["scene_id"], "acquisition": acquisition_id,
                "support_cells": item["support_cells"],
                "direct_usable_point_bin_union_count": diagnostics["direct_usable_point_bin_union_count"],
                "total_selected": item["total_selection"]["selected"],
                "company_5pct_total_only": item["company_5pct_total_only"],
                "total_absolute_error_percent": (
                    item["whole_box"]["absolute_error_percent"] if item["whole_box"] else None),
                "own_spatial_error_percent": item["own_supported"]["spatial_error_percent"],
                "common_cell_count": change["common_cell_count"],
                "common_absolute_error_percent": item["paired_common_support"]["absolute_error_percent"],
                "common_spatial_error_percent": item["paired_common_support"]["spatial_error_percent"],
                "candidate_lost_cells": change["lost_cell_count"],
                "candidate_gained_cells": change["gained_cell_count"],
                "estimator_elapsed_ms_single_run": item["estimator_elapsed_ms_single_run"],
            })
    return rows


def main():
    if OUT.exists():
        raise SystemExit("Refusing to overwrite D002 results")
    started = utc_now()
    protocol, executable = load_and_validate_protocol()
    original = validate_against_archive(protocol)
    original_by_scene = {entry["scene_id"]: entry for entry in original["scenes"]}
    input_hashes = {
        relative_path(PROTOCOL): sha256(PROTOCOL),
        relative_path(PROTOCOL_HASH): sha256(PROTOCOL_HASH),
        relative_path(P001_PROTOCOL): sha256(P001_PROTOCOL),
        relative_path(P001_RESULTS): sha256(P001_RESULTS),
    }
    command_log = []
    work = []
    for scene in protocol["scenes"]:
        control_frames_raw, control, control_ms = control_frames(
            scene, protocol["acquisitions"]["control_fixed3"],
            original_by_scene[scene["id"]], protocol, input_hashes)
        candidate_frames_raw = capture_candidate(
            executable, scene, protocol["acquisitions"]["candidate_fixed3_z050"],
            protocol, command_log)
        before = time.perf_counter()
        candidate = fuse_frames(candidate_frames_raw, {"reference_offset_m": 0.0})
        candidate_ms = (time.perf_counter() - before) * 1000.0
        # Keep bytes and estimates separate from evaluator truth until all captures validate.
        work.append((scene, control_frames_raw, candidate_frames_raw,
                     control, candidate, control_ms, candidate_ms))

    records = [evaluate_pair(scene, control, candidate, control_ms, candidate_ms)
               for scene, _, _, control, candidate, control_ms, candidate_ms in work]
    rows = summary_rows(records)
    if len(command_log) != 27 or len(records) != 9 or len(rows) != 18:
        fail("D002 execution count invariant failed")

    OUT.mkdir(parents=True)
    output_hashes = {}
    for scene, _, candidate_frames, _, _, _, _ in work:
        frame_dir = OUT / "frames" / scene["id"]
        frame_dir.mkdir(parents=True)
        for index, raw in enumerate(candidate_frames, 1):
            path = frame_dir / f"candidate_fixed3_z050-{index}.bin"
            path.write_bytes(raw)
            output_hashes[relative_path(path)] = sha256(path)

    gate = {
        acquisition_id: {
            "eligible_total_count": sum(
                record["acquisitions"][acquisition_id]["whole_box"] is not None for record in records),
            "within_5pct_count": sum(
                record["acquisitions"][acquisition_id]["company_5pct_total_only"] is True
                for record in records),
            "failed_5pct_count": sum(
                record["acquisitions"][acquisition_id]["company_5pct_total_only"] is False
                for record in records),
            "partial_count": sum(
                record["acquisitions"][acquisition_id]["company_5pct_total_only"] is None
                for record in records),
        } for acquisition_id in ACQUISITION_IDS
    }
    result = {
        "experiment_id": "D-002", "started_at_utc": started,
        "finished_at_utc": utc_now(), "protocol_sha256": sha256(PROTOCOL),
        "scope": "ideal simulated acquisition development on previously inspected scenes; not holdout or hardware validation",
        "new_capture_count": 27, "archived_control_frame_count": 27,
        "estimator": "R005 median fusion; no trimming, extrapolation, or zero filling",
        "company_rule": "whole-box total only; eligible iff 400/400 support and no invalid/unavailable view; absolute relative error <=5%",
        "timing_limit": "single local runs and capture calls; descriptive only, not a real-time benchmark",
        "gate_counts": gate, "scenes": records,
    }
    results_path = OUT / "results.json"
    results_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    with (OUT / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "capture-log.json").write_text(
        json.dumps(command_log, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    for path in (results_path, OUT / "summary.csv", OUT / "capture-log.json"):
        output_hashes[relative_path(path)] = sha256(path)
    for name in protocol["frozen_sources"]:
        input_hashes[name.replace("\\", "/")] = sha256(ROOT / name)
    manifest_path = OUT / "hash-manifest.json"
    manifest_path.write_text(json.dumps({
        "protocol_sha256": sha256(PROTOCOL), "inputs": input_hashes,
        "outputs": output_hashes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "experiment_id": "D-002", "new_captures": 27,
        "archived_controls": 27, "gate_counts": gate,
        "results": relative_path(results_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
