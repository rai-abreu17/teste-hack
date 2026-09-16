"""Frozen D003 development evaluator. Reuses archived K4 frames only."""

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

from experiments import truth
from server import geometry as g
from d003_estimator import estimate_frames as pooled_estimate
from r005_estimator import fuse_frames as control_estimate


SOURCE = ROOT / ".ai/runs/m001-implementation/results"
OUT = ROOT / ".ai/runs/m001-d003/results"
ACQUISITION = "translated4_corners_level"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(heights, reference, indices):
    indices = list(indices)
    assert all(heights[index] is not None for index in indices)
    residuals = [heights[index] * g.CELL ** 2 - reference[index] for index in indices]
    signed = sum(residuals)
    spatial = sum(abs(value) for value in residuals)
    volume = sum(reference[index] for index in indices)
    return {
        "cell_count": len(indices),
        "area_m2": len(indices) * g.CELL ** 2,
        "truth_volume_m3": volume,
        "estimated_volume_m3": volume + signed if indices else None,
        "signed_error_m3": signed,
        "absolute_volume_error_m3": abs(signed),
        "integrated_absolute_error_m3": spatial,
        "signed_error_percent": signed / volume * 100 if volume else None,
        "absolute_error_percent": abs(signed) / volume * 100 if volume else None,
        "spatial_error_percent": spatial / volume * 100 if volume else None,
        "mean_absolute_height_error_mm": spatial / (len(indices) * g.CELL ** 2) * 1000 if indices else None,
        "cancellation_ratio": spatial / abs(signed) if abs(signed) > 0 else None,
    }


def main():
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite D003 results: {OUT}")
    protocol_path = HERE / "protocol_d003.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected_protocol_hash = (HERE / "protocol_d003.sha256").read_text(encoding="utf-8").split()[0]
    assert sha(protocol_path) == expected_protocol_hash
    for name, checksum in protocol["frozen_sources"].items():
        assert sha(ROOT / name) == checksum, name

    historical_path = SOURCE / "comparisons.json"
    original = json.loads(historical_path.read_text(encoding="utf-8"))
    assert [scene["scene_id"] for scene in original["scenes"]] == protocol["inputs"]["scene_ids"]
    hashes = {str(historical_path.relative_to(ROOT)): sha(historical_path)}
    records, details = [], []
    for entry in original["scenes"]:
        scene_id = entry["scene_id"]
        archived = {arm["arm_id"]: arm for arm in entry["arms"]}[ACQUISITION]
        paths = sorted((SOURCE / "frames" / scene_id).glob(f"{ACQUISITION}-*.bin"))
        assert len(paths) == 4
        for path, view in zip(paths, archived["per_view"]):
            assert sha(path) == view["sha256"]
            hashes[str(path.relative_to(ROOT))] = sha(path)
        frames = [path.read_bytes() for path in paths]

        reference = truth.cell_volumes(truth.Scene(**entry["scene_for_evaluator_only"]))
        assert math.isclose(sum(reference), truth.analytical_volume(
            truth.Scene(**entry["scene_for_evaluator_only"])), abs_tol=1e-12)

        start = time.perf_counter()
        control = control_estimate(frames)
        control_ms = (time.perf_counter() - start) * 1000
        assert control["heights"] == archived["heights"]
        start = time.perf_counter()
        candidate = pooled_estimate(frames)
        candidate_ms = (time.perf_counter() - start) * 1000
        assert not candidate["invalid_frames"] and not candidate["unavailable_view_indices"]

        common = [
            index for index in range(g.NX * g.NY)
            if control["heights"][index] is not None and candidate["heights"][index] is not None
        ]
        for method, result, elapsed in (
            ("r005_per_view_grid_median", control, control_ms),
            ("d003_pooled_xyz_delaunay", candidate, candidate_ms),
        ):
            heights = result["heights"]
            supported = [index for index, value in enumerate(heights) if value is not None]
            missing = [index for index, value in enumerate(heights) if value is None]
            eligible = result["total_selection"]["selected"]
            assert eligible == (
                len(supported) == g.NX * g.NY
                and not result["invalid_frames"]
                and not result["unavailable_view_indices"]
                and (method != "d003_pooled_xyz_delaunay"
                     or (result["qhull_error"] is None and result["coplanar_point_count"] == 0))
            )
            whole = stats(heights, reference, range(g.NX * g.NY)) if eligible else None
            records.append({
                "scene_id": scene_id,
                "acquisition": ACQUISITION,
                "method": method,
                "support_cells": len(supported),
                "total_selection": result["total_selection"],
                "whole_box": whole,
                "company_5pct_total_only": (
                    whole["absolute_error_percent"] <= 5
                    if whole and whole["absolute_error_percent"] is not None else None
                ),
                "own": stats(heights, reference, supported),
                "common": stats(heights, reference, common),
                "unsupported": {
                    "cell_count": len(missing),
                    "area_m2": len(missing) * g.CELL ** 2,
                    "truth_volume_m3": sum(reference[index] for index in missing),
                },
                "elapsed_ms_single_run": elapsed,
                "raw_point_count": result.get("raw_point_count"),
                "merged_point_count": result.get("merged_point_count"),
                "merge_conflict_count": result.get("merge_conflict_count"),
                "delaunay_simplex_count": result.get("delaunay_simplex_count"),
                "accepted_triangle_count": result.get("accepted_triangle_count"),
                "long_or_degenerate_triangle_count": result.get("long_or_degenerate_triangle_count"),
            })
        details.append({"scene_id": scene_id, "candidate": candidate})

    assert len(records) == 18 and len(details) == 9 and len(hashes) == 37
    OUT.mkdir(parents=True)
    result_file = {
        "experiment_id": "D-003",
        "scope": "SIMULATED development on previously inspected scenes; not holdout",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha(protocol_path),
        "new_captures": 0,
        "frames_reused": 36,
        "records": records,
        "interpretation_limits": protocol["interpretation_limits"],
    }
    (OUT / "results.json").write_text(
        json.dumps(result_file, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    (OUT / "details.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    rows = []
    for record in records:
        rows.append({
            "scene": record["scene_id"],
            "method": record["method"],
            "support_cells": record["support_cells"],
            "total_error_percent": record["whole_box"]["absolute_error_percent"] if record["whole_box"] else None,
            "total_within_5pct": record["company_5pct_total_only"],
            "own_signed_error_percent": record["own"]["signed_error_percent"],
            "own_spatial_error_percent": record["own"]["spatial_error_percent"],
            "common_signed_error_percent": record["common"]["signed_error_percent"],
            "common_spatial_error_percent": record["common"]["spatial_error_percent"],
            "missing_truth_volume_m3": record["unsupported"]["truth_volume_m3"],
            "merge_conflicts": record["merge_conflict_count"],
            "elapsed_ms_single_run": record["elapsed_ms_single_run"],
        })
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    for path in [protocol_path, HERE / "protocol_d003.sha256", *(ROOT / name for name in protocol["frozen_sources"]), *OUT.iterdir()]:
        hashes[str(path.relative_to(ROOT))] = sha(path)
    (OUT / "hash-manifest.json").write_text(
        json.dumps({"files": hashes}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
