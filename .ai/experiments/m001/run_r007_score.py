"""Score the released R007 acquisition once under the frozen primary gate.

All twelve estimates are reconstructed before the evaluator imports scene
truth.  The script verifies the pre-open chain, acquisition chain, and an
independent score release, and refuses to overwrite any score artifact.
"""

import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]

from d003_estimator import estimate_frames
from server import geometry as g
import run_r007 as acquisition_runner


RUN = ROOT / ".ai/runs/m001-r007"
FRAMES = RUN / "frames"
OUT = RUN / "results"
PROTOCOL = HERE / "protocol_r007.json"
PRE_OPEN = RUN / "pre-open-manifest.json"
COMMANDS = RUN / "capture-commands.json"
ACQUISITION = RUN / "acquisition-manifest.json"
ACQUISITION_VALIDATION = RUN / "acquisition-validation.json"
SCORE_RELEASE = RUN / "independent-score-release.json"
VALIDATION = RUN / "validation.json"
REPORT = RUN / "REPORT.md"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_released_inputs():
    if OUT.exists() or VALIDATION.exists() or REPORT.exists():
        raise RuntimeError("refusing to overwrite R007 score artifacts")
    protocol, _manifest = acquisition_runner.verify_preopen(require_pristine=False)
    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    validation = json.loads(ACQUISITION_VALIDATION.read_text(encoding="utf-8"))
    commands = json.loads(COMMANDS.read_text(encoding="utf-8"))
    if not validation.get("passed") or validation.get("phase") != "AWAITING_INDEPENDENT_SCORE_RELEASE":
        raise RuntimeError("R007 acquisition has no passing validation")
    if validation.get("acquisition_manifest_sha256") != sha256(ACQUISITION):
        raise RuntimeError("acquisition manifest changed after validation")
    if validation.get("capture_commands_sha256") != sha256(COMMANDS):
        raise RuntimeError("capture commands changed after validation")
    if validation.get("capture_plan_sha256") != sha256(acquisition_runner.CAPTURE_PLAN):
        raise RuntimeError("acquisition validation does not bind capture plan")

    acquisition_runner.verify_release(
        SCORE_RELEASE, "RELEASE_R007_SCORE", "acquisition_validation_sha256",
        sha256(ACQUISITION_VALIDATION),
    )
    release = json.loads(SCORE_RELEASE.read_text(encoding="utf-8"))
    
    if release.get("pre_open_manifest_sha256") != sha256(PRE_OPEN):
        raise RuntimeError("score release does not bind pre-open manifest")
    if release.get("capture_plan_sha256") != sha256(acquisition_runner.CAPTURE_PLAN):
        raise RuntimeError("score release does not bind capture plan")
    if release.get("acquisition_manifest_sha256") != sha256(ACQUISITION):
        raise RuntimeError("score release does not bind acquisition manifest")
    
    if len(acquisition.get("candidate_frames", {})) != 60 or len(commands) != 60:
        raise RuntimeError("R007 acquisition is incomplete")
    expected = set()
    for scene in protocol["scenes"]:
        for capture in protocol["candidate"]["captures"]:
            expected.add(relative(FRAMES / scene["id"] / f"candidate-{capture['sequence']}.bin"))
    if set(acquisition["candidate_frames"]) != expected:
        raise RuntimeError("R007 frame set differs from fixed 12 x 5 matrix")
    for name, item in acquisition["candidate_frames"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise RuntimeError(f"R007 frame hash mismatch: {name}")
    return protocol, acquisition, validation


def scene_paths(scene_id, protocol):
    return [FRAMES / scene_id / f"candidate-{item['sequence']}.bin"
            for item in protocol["candidate"]["captures"]]


def convex_hull(points):
    points = sorted(set((float(x), float(y)) for x, y in points))
    if len(points) <= 1:
        return points

    def cross(origin, a, b):
        return ((a[0] - origin[0]) * (b[1] - origin[1])
                - (a[1] - origin[1]) * (b[0] - origin[0]))

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def polygon_area(polygon):
    if len(polygon) < 3:
        return 0.0
    return abs(sum(a[0] * b[1] - a[1] * b[0]
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2


def inside_convex(polygon, point, tolerance=1e-10):
    if len(polygon) < 3:
        return False
    signs = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        cross = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
        if abs(cross) > tolerance:
            signs.append(cross > 0)
    return not signs or all(sign == signs[0] for sign in signs)


def truth_free_summary(result):
    supported = [index for index, value in enumerate(result["heights"]) if value is not None]
    points = [(item["point"][0], item["point"][1]) for item in result["merged_points"]]
    hull = convex_hull(points)
    inside = []
    for index in range(g.NX * g.NY):
        point = ((index % g.NX + 0.5) * g.CELL, (index // g.NX + 0.5) * g.CELL)
        if inside_convex(hull, point):
            inside.append(index)
    support_set, inside_set = set(supported), set(inside)
    excluded = {name: sum(frame["excluded"][name] for frame in result["decoded_frames"])
                for name in result["decoded_frames"][0]["excluded"]}
    xs, ys = [point[0] for point in hull], [point[1] for point in hull]
    return {
        "frame_count": result["frame_count_input"],
        "support_cells": len(supported),
        "supported_cell_indices": supported,
        "total_selection": result["total_selection"],
        "measurement_state": result["measurement_state"],
        "accepted_return_hull": {
            "vertices_xy_m": [list(point) for point in hull],
            "vertex_count": len(hull),
            "area_m2": polygon_area(hull),
            "bounds_m": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)]} if hull else None,
            "grid_centers_inside_or_on": len(inside),
        },
        "outside_hull_cell_count": g.NX * g.NY - len(inside_set),
        "inside_hull_unsupported_cell_count": len(inside_set - support_set),
        "rejected_returns": excluded,
        "invalid_frame_count": len(result["invalid_frames"]),
        "unavailable_view_count": len(result["unavailable_view_indices"]),
        "raw_point_count": result["raw_point_count"],
        "merged_point_count": result["merged_point_count"],
        "merge_conflict_count": result["merge_conflict_count"],
        "delaunay_simplex_count": result["delaunay_simplex_count"],
        "accepted_triangle_count": result["accepted_triangle_count"],
        "long_or_degenerate_triangle_count": result["long_or_degenerate_triangle_count"],
        "qhull_error": result["qhull_error"],
        "coplanar_point_count": result["coplanar_point_count"],
    }


def reconstruct_all(protocol):
    """Finish the complete truth-free phase before evaluator truth is imported."""
    reconstructed = []
    for scene in protocol["scenes"]:
        paths = scene_paths(scene["id"], protocol)
        start = time.perf_counter()
        estimate = estimate_frames([path.read_bytes() for path in paths])
        elapsed_ms = (time.perf_counter() - start) * 1000
        reconstructed.append({
            "scene": scene,
            "input_paths": [relative(path) for path in paths],
            "input_sha256": [sha256(path) for path in paths],
            "elapsed_ms_single_run": elapsed_ms,
            "truth_free": truth_free_summary(estimate),
            "estimate": estimate,
        })
    if len(reconstructed) != 12 or any(item["estimate"]["frame_count_input"] != 5
                                        for item in reconstructed):
        raise RuntimeError("R007 reconstruction matrix is incomplete")
    return reconstructed


def domain_stats(heights, reference, indices):
    indices = list(indices)
    if not indices:
        return {"cell_count": 0, "area_m2": 0.0, "truth_volume_m3": 0.0,
                "estimated_volume_m3": None, "signed_error_m3": None,
                "absolute_volume_error_m3": None, "integrated_absolute_error_m3": None,
                "signed_error_percent": None, "absolute_error_percent": None,
                "spatial_error_percent": None, "mean_absolute_height_error_mm": None,
                "cancellation_ratio": None}
    if any(heights[index] is None for index in indices):
        raise ValueError("domain includes unsupported cell")
    residuals = [heights[index] * g.CELL ** 2 - reference[index] for index in indices]
    signed = sum(residuals)
    spatial = sum(abs(value) for value in residuals)
    truth_volume = sum(reference[index] for index in indices)
    estimated = truth_volume + signed
    return {
        "cell_count": len(indices),
        "area_m2": len(indices) * g.CELL ** 2,
        "truth_volume_m3": truth_volume,
        "estimated_volume_m3": estimated,
        "signed_error_m3": signed,
        "absolute_volume_error_m3": abs(signed),
        "integrated_absolute_error_m3": spatial,
        "signed_error_percent": signed / truth_volume * 100 if truth_volume else None,
        "absolute_error_percent": abs(signed) / truth_volume * 100 if truth_volume else None,
        "spatial_error_percent": spatial / truth_volume * 100 if truth_volume else None,
        "mean_absolute_height_error_mm": spatial / (len(indices) * g.CELL ** 2) * 1000,
        "cancellation_ratio": spatial / abs(signed) if abs(signed) > 0 else None,
    }


def evaluate_with_truth(reconstructed):
    """Evaluator-only phase and the first runtime import of scene truth."""
    from experiments import truth

    records, details = [], []
    for item in reconstructed:
        scene_data = item["scene"]
        scene = truth.Scene(**{key: value for key, value in scene_data.items() if key != "id"})
        reference = truth.cell_volumes(scene)
        analytical = truth.analytical_volume(scene)
        if analytical <= 0 or not math.isclose(sum(reference), analytical,
                                                rel_tol=1e-10, abs_tol=1e-14):
            raise RuntimeError(f"truth integration mismatch or empty scene: {scene_data['id']}")
        estimate = item["estimate"]
        heights = estimate["heights"]
        supported = item["truth_free"]["supported_cell_indices"]
        missing = sorted(set(range(g.NX * g.NY)) - set(supported))
        eligible = estimate["total_selection"]["selected"]
        whole = domain_stats(heights, reference, range(g.NX * g.NY)) if eligible else None
        own = domain_stats(heights, reference, supported)
        within = (whole["absolute_error_percent"] <= 5.0
                  if whole and whole["absolute_error_percent"] is not None else None)
        record = {
            "scene_id": scene_data["id"],
            "shape": scene_data["shape"],
            "fill": scene_data["fill"],
            "obstacle": scene_data["obstacle"],
            "dropout": scene_data["dropout"],
            "support_cells": len(supported),
            "total_selection": estimate["total_selection"],
            "whole_box": whole,
            "primary_scene_pass": within is True,
            "own": own,
            "unsupported": {
                "cell_count": len(missing),
                "area_m2": len(missing) * g.CELL ** 2,
                "truth_volume_m3": sum(reference[index] for index in missing),
            },
            "elapsed_ms_single_run": item["elapsed_ms_single_run"],
            **{key: item["truth_free"][key] for key in (
                "accepted_return_hull", "outside_hull_cell_count",
                "inside_hull_unsupported_cell_count", "rejected_returns",
                "invalid_frame_count", "unavailable_view_count", "raw_point_count",
                "merged_point_count", "merge_conflict_count", "delaunay_simplex_count",
                "accepted_triangle_count", "long_or_degenerate_triangle_count",
                "qhull_error", "coplanar_point_count")},
        }
        records.append(record)
        details.append({
            "scene_id": scene_data["id"],
            "scene_for_evaluator_only": scene_data,
            "truth_total_m3": analytical,
            "input_paths": item["input_paths"],
            "input_sha256": item["input_sha256"],
            "estimate": estimate,
            "record": record,
        })
    return records, details


def aggregate_gate(records):
    eligible = sum(record["total_selection"]["selected"] for record in records)
    passed = sum(record["primary_scene_pass"] for record in records)
    partial = sum(not record["total_selection"]["selected"] for record in records)
    failed_ids = [record["scene_id"] for record in records if not record["primary_scene_pass"]]
    return {
        "scene_count": len(records),
        "total_eligible": eligible,
        "total_within_5pct": passed,
        "partial_or_ineligible": partial,
        "failed_scene_ids": failed_ids,
        "all_12_total_eligible_and_each_within_5pct": (
            len(records) == 12 and eligible == 12 and passed == 12
        ),
    }


def write_summary(records):
    rows = []
    for record in records:
        whole = record["whole_box"]
        rows.append({
            "scene": record["scene_id"], "shape": record["shape"], "fill": record["fill"],
            "obstacle": record["obstacle"], "dropout": record["dropout"],
            "support_cells": record["support_cells"],
            "total_eligible": record["total_selection"]["selected"],
            "total_absolute_error_percent": whole["absolute_error_percent"] if whole else None,
            "primary_scene_pass": record["primary_scene_pass"],
            "own_signed_error_percent": record["own"]["signed_error_percent"],
            "own_spatial_error_percent": record["own"]["spatial_error_percent"],
            "own_cancellation_ratio": record["own"]["cancellation_ratio"],
            "unsupported_truth_volume_m3": record["unsupported"]["truth_volume_m3"],
            "invalid_frames": record["invalid_frame_count"],
            "unavailable_views": record["unavailable_view_count"],
            "raw_points": record["raw_point_count"], "merged_points": record["merged_point_count"],
            "merge_conflicts": record["merge_conflict_count"],
            "elapsed_ms_single_run": record["elapsed_ms_single_run"],
        })
    with (OUT / "summary.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(records, gate):
    verdict = "PASS" if gate["all_12_total_eligible_and_each_within_5pct"] else "FAIL"
    lines = [
        "# R007 reserved simulated validation", "",
        f"**{verdict}.** This is a SIMULATED reserved holdout result, not physical validation.", "",
        "## Primary gate", "",
        f"- Total eligible: **{gate['total_eligible']}/12**.",
        f"- Total eligible and within 5%: **{gate['total_within_5pct']}/12**.",
        f"- Partial or ineligible: **{gate['partial_or_ineligible']}/12**.",
        f"- All 12 total eligible and each absolute relative total-volume error <=5%: **{verdict}**.",
        "", "Any partial result fails. Spatial error and cancellation are reported but do not alter the gate.", "",
        "## Per scene", "",
        "| scene | support | total error | spatial error | cancellation | pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        whole = record["whole_box"]
        total = "--" if whole is None else f"{whole['absolute_error_percent']:.3f}%"
        spatial = record["own"]["spatial_error_percent"]
        cancellation = record["own"]["cancellation_ratio"]
        lines.append(
            f"| {record['scene_id']} | {record['support_cells']}/400 | {total} | "
            f"{spatial:.3f}% | {'--' if cancellation is None else f'{cancellation:.2f}x'} | "
            f"{'PASS' if record['primary_scene_pass'] else 'FAIL'} |"
        )
    lines.extend(["", "The scene table, candidate, estimator, runners, evaluator, tests, simulator, and gate were frozen before capture.", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_result_manifest(paths):
    files = {relative(path): sha256(path) for path in sorted(paths, key=relative)}
    (OUT / "hash-manifest.json").write_text(
        json.dumps({"experiment_id": "R-007", "files": files}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    protocol, acquisition, acquisition_validation = verify_released_inputs()

    reconstructed = reconstruct_all(protocol)
    records, details = evaluate_with_truth(reconstructed)
    gate = aggregate_gate(records)

    OUT.mkdir(parents=True, exist_ok=False)
    results = {
        "experiment_id": "R-007",
        "scope": protocol["scope"],
        "created_at_utc": utc_now(),
        "protocol_sha256": sha256(PROTOCOL),
        "pre_open_manifest_sha256": sha256(PRE_OPEN),
        "acquisition_manifest_sha256": sha256(ACQUISITION),
        "acquisition_validation_sha256": sha256(ACQUISITION_VALIDATION),
        "score_release_sha256": sha256(SCORE_RELEASE),
        "truth_free_reconstructions_completed_before_truth_evaluation": 12,
        "gate": gate,
        "records": records,
        "interpretation_limits": protocol["interpretation_limits"],
    }
    (OUT / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (OUT / "details.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    write_summary(records)
    checks = {
        "frozen_pre_open_chain_verified_before_estimation": True,
        "released_acquisition_chain_verified_before_estimation": True,
        "truth_free_reconstruction_count_12": len(reconstructed) == 12,
        "five_new_frames_per_scene": all(len(item["input_paths"]) == 5 for item in reconstructed),
        "unique_input_frame_count_60": len({path for item in reconstructed for path in item["input_paths"]}) == 60,
        "no_invalid_frames": all(record["invalid_frame_count"] == 0 for record in records),
        "no_unavailable_views": all(record["unavailable_view_count"] == 0 for record in records),
        "partial_never_passes": all(record["total_selection"]["selected"] or not record["primary_scene_pass"]
                                     for record in records),
        "gate_is_exact_12_of_12": gate["all_12_total_eligible_and_each_within_5pct"]
                                  == (gate["total_eligible"] == 12
                                      and gate["total_within_5pct"] == 12),
        "spatial_and_cancellation_reported": all("spatial_error_percent" in record["own"]
                                                  and "cancellation_ratio" in record["own"]
                                                  for record in records),
    }
    validation = {
        "experiment_id": "R-007",
        "checked_at_utc": utc_now(),
        "passed": all(checks.values()),
        "checks": checks,
        "gate": gate,
        "result_hashes": {
            "results.json": sha256(OUT / "results.json"),
            "details.json": sha256(OUT / "details.json"),
            "summary.csv": sha256(OUT / "summary.csv"),
        },
    }
    VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(records, gate)
    write_result_manifest({
        PROTOCOL, PRE_OPEN, COMMANDS, ACQUISITION, ACQUISITION_VALIDATION, SCORE_RELEASE,
        HERE / "d003_estimator.py", HERE / "run_r007.py", HERE / "run_r007_score.py",
        HERE / "test_r007.py", ROOT / "experiments/truth.py", ROOT / "server/geometry.py",
        OUT / "results.json", OUT / "details.json", OUT / "summary.csv", VALIDATION, REPORT,
        *(ROOT / name for name in acquisition["candidate_frames"]),
    })
    if not validation["passed"]:
        raise RuntimeError("R007 score validation failed")
    print(json.dumps({"gate": gate, "validation_passed": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
