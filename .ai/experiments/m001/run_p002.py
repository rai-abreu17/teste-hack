"""P-002: reuse P-001 frames and ablate only the local TIN edge limit."""

import hashlib
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = ROOT / ".ai" / "runs" / "m001-implementation" / "results"
OUT = ROOT / ".ai" / "runs" / "m001-p002" / "results"
sys.path[:0] = [str(ROOT), str(HERE)]

from experiments.truth import Scene, cell_volumes
from m001_estimator import fuse_frames
from server import geometry as g


def main():
    protocol_path = HERE / "protocol_p002.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol_digest = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    p001 = json.loads((RESULTS / "comparisons.json").read_text(encoding="utf-8"))
    rows = []
    original_limit = g.MAX_EDGE_M
    try:
        for scene_result in p001["scenes"]:
            scene_id = scene_result["scene_id"]
            scene_data = scene_result["scene_for_evaluator_only"]
            scene = Scene(fill=scene_data["fill"], shape=scene_data["shape"],
                          cx=scene_data["cx"], obstacle=scene_data["obstacle"],
                          dropout=scene_data["dropout"], range_m=4.0, sensor_z=.40)
            truth_cells = cell_volumes(scene)
            original_mask = [all(arm["heights"][i] is not None for arm in scene_result["arms"])
                             for i in range(g.NX * g.NY)]
            for arm_id in protocol["arms"]:
                frame_paths = sorted((RESULTS / "frames" / scene_id).glob(f"{arm_id}-*.bin"))
                frames = [path.read_bytes() for path in frame_paths]
                for limit in protocol["max_edge_m"]:
                    g.MAX_EDGE_M = limit
                    fused = fuse_frames(frames, {"reference_offset_m": 0.0})
                    covered = [m and h is not None for m, h in zip(original_mask, fused["heights"])]
                    complete = covered == original_mask
                    reference = sum(v for v, m in zip(truth_cells, original_mask) if m)
                    estimated = sum(h for h, m in zip(fused["heights"], original_mask)
                                    if m and h is not None) * g.CELL ** 2
                    error = None if not complete else 100 * (estimated - reference) / reference
                    rows.append({"scene_id": scene_id, "arm_id": arm_id,
                                 "max_edge_m": limit, "original_common_cells": sum(original_mask),
                                 "original_common_complete": complete,
                                 "tin_support_fraction": fused["tin_support_union_fraction"],
                                 "total_selected": fused["total_selection"]["selected"],
                                 "signed_error_percent": error,
                                 "absolute_error_percent": None if error is None else abs(error)})
    finally:
        g.MAX_EDGE_M = original_limit

    def select(arm, limit):
        return [r for r in rows if r["arm_id"] == arm and r["max_edge_m"] == limit]

    baseline = select("fixed3", 0.10)
    challenger = select("translated3_aimed", 0.07)
    paired = []
    for base, challenge in zip(baseline, challenger):
        delta = None if challenge["absolute_error_percent"] is None else (
            base["absolute_error_percent"] - challenge["absolute_error_percent"])
        paired.append({"scene_id": base["scene_id"], "absolute_error_reduction_pp": delta})
    valid_deltas = [p["absolute_error_reduction_pp"] for p in paired
                    if p["absolute_error_reduction_pp"] is not None]
    summary = {
        "protocol_sha256": protocol_digest,
        "comparison_count": len(rows),
        "baseline": "fixed3@0.10m",
        "challenger": "translated3_aimed@0.07m",
        "paired": paired,
        "median_absolute_error_reduction_pp": statistics.median(valid_deltas) if valid_deltas else None,
        "scene_wins": sum(d > 0 for d in valid_deltas),
        "maximum_regression_pp": max([0.0, *(-d for d in valid_deltas)]),
        "challenger_median_support_fraction": statistics.median(r["tin_support_fraction"] for r in challenger),
        "challenger_total_selected_count": sum(r["total_selected"] for r in challenger),
        "challenger_original_domain_complete_count": sum(r["original_common_complete"] for r in challenger)
    }
    req = protocol["approval"]
    summary["approved"] = (
        summary["median_absolute_error_reduction_pp"] is not None
        and summary["median_absolute_error_reduction_pp"] >= req["median_paired_absolute_error_reduction_pp_min"]
        and summary["scene_wins"] >= req["scene_wins_min"]
        and summary["maximum_regression_pp"] <= req["maximum_regression_pp"]
        and summary["challenger_median_support_fraction"] >= req["median_support_fraction_min"]
        and summary["challenger_total_selected_count"] >= req["total_selected_min"]
        and summary["challenger_original_domain_complete_count"] == len(baseline))
    OUT.mkdir(parents=True, exist_ok=True)
    output = {"experiment_id": "P-002", "scope": "SIMULATED", "summary": summary, "rows": rows}
    (OUT / "comparisons.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
