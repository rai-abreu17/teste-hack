"""P-004: compactness trimming followed by lower-median fusion."""

import hashlib
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P001_RESULTS = ROOT / ".ai" / "runs" / "m001-implementation" / "results"
OUT = ROOT / ".ai" / "runs" / "m001-p004" / "results"
sys.path[:0] = [str(ROOT), str(HERE)]

from experiments.truth import Scene, cell_volumes
from m001_estimator import fuse_frames
from run_p003 import triangle_quality_by_cell, metrics
from server import geometry as g


def trimmed_fusion(frames, kappa):
    conventional = fuse_frames(frames, {"reference_offset_m": 0.0})
    qualities = [triangle_quality_by_cell(frame) for frame in frames]
    heights, retained_histogram = [], {"1": 0, "2": 0, "3": 0}
    trimmed_cells = 0
    for cell in range(g.NX * g.NY):
        candidates = []
        for view_index, view in enumerate(conventional["per_view"]):
            if view["heights"][cell] is not None and qualities[view_index][cell] is not None:
                candidates.append((qualities[view_index][cell], view_index, view["heights"][cell]))
        if not candidates:
            heights.append(None)
            continue
        minimum = min(item[0] for item in candidates)
        retained = [item for item in candidates if item[0] <= kappa * minimum]
        if len(retained) < len(candidates):
            trimmed_cells += 1
        retained_histogram[str(len(retained))] += 1
        values = sorted(item[2] for item in retained)
        heights.append(values[(len(values) - 1) // 2])
    return {"heights": heights,
            "support_fraction": sum(value is not None for value in heights) / (g.NX * g.NY),
            "total_selected": all(value is not None for value in heights),
            "trimmed_cell_count": trimmed_cells,
            "retained_view_count_histogram": retained_histogram}


def main():
    protocol_path = HERE / "protocol_p004.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    p001 = json.loads((P001_RESULTS / "comparisons.json").read_text(encoding="utf-8"))
    rows, paired = [], []
    for scene_result in p001["scenes"]:
        scene_id = scene_result["scene_id"]
        data = scene_result["scene_for_evaluator_only"]
        scene = Scene(fill=data["fill"], shape=data["shape"], cx=data["cx"],
                      obstacle=data["obstacle"], dropout=data["dropout"],
                      range_m=4.0, sensor_z=.40)
        truth_cells = cell_volumes(scene)
        original_mask = [all(arm["heights"][cell] is not None for arm in scene_result["arms"])
                         for cell in range(g.NX * g.NY)]
        original = {arm["arm_id"]: arm for arm in scene_result["arms"]}
        baseline_error = abs(original["fixed3"]["evaluation"]["common_all_arms_domain"]["signed_error_percent"])
        frames = [path.read_bytes() for path in sorted(
            (P001_RESULTS / "frames" / scene_id).glob("translated3_aimed-*.bin"))]
        median = fuse_frames(frames, {"reference_offset_m": 0.0})
        result = trimmed_fusion(frames, protocol["kappa"])
        if median["heights"] != original["translated3_aimed"]["heights"]:
            raise AssertionError(f"P-001 median mismatch: {scene_id}")
        if result["support_fraction"] != median["tin_support_union_fraction"]:
            raise AssertionError(f"support changed: {scene_id}")
        complete, signed = metrics(result["heights"], truth_cells, original_mask)
        absolute = None if signed is None else abs(signed)
        reduction = None if absolute is None else baseline_error - absolute
        row = {"scene_id": scene_id, "original_domain_complete": complete,
               "tin_support_fraction": result["support_fraction"],
               "total_selected": result["total_selected"],
               "signed_error_percent": signed, "absolute_error_percent": absolute,
               "absolute_error_reduction_pp": reduction,
               "trimmed_cell_count": result["trimmed_cell_count"],
               "retained_view_count_histogram": result["retained_view_count_histogram"]}
        rows.append(row)
        paired.append({"scene_id": scene_id,
                       "baseline_absolute_error_percent": baseline_error,
                       "challenger_absolute_error_percent": absolute,
                       "absolute_error_reduction_pp": reduction})
    deltas = [item["absolute_error_reduction_pp"] for item in paired
              if item["absolute_error_reduction_pp"] is not None]
    summary = {"protocol_sha256": digest, "comparison_count": len(rows), "paired": paired,
               "median_absolute_error_reduction_pp": statistics.median(deltas),
               "scene_wins": sum(delta > 0 for delta in deltas),
               "maximum_regression_pp": max([0.0, *(-delta for delta in deltas)]),
               "challenger_median_support_fraction": statistics.median(row["tin_support_fraction"] for row in rows),
               "challenger_total_selected_count": sum(row["total_selected"] for row in rows),
               "challenger_original_domain_complete_count": sum(row["original_domain_complete"] for row in rows)}
    hard = json.loads((ROOT / ".ai" / "runs" / "m001-p003" / "results" / "comparisons.json").read_text(encoding="utf-8"))
    hard_gain = {item["scene_id"]: item["absolute_error_reduction_pp"] for item in hard["summary"]["paired"]}
    summary["prediction_checks"] = {
        "prism_ramp_regression_within_2pp": all(next(row for row in rows if row["scene_id"] == scene)["absolute_error_reduction_pp"] >= -2 for scene in ("prism", "ramp")),
        "half_gain_retained": {scene: next(row for row in rows if row["scene_id"] == scene)["absolute_error_reduction_pp"] >= 0.5 * hard_gain[scene]
                               for scene in protocol["predictions"]["retain_half_gain_for"]}}
    req = protocol["approval"]
    summary["approved"] = (summary["median_absolute_error_reduction_pp"] >= req["median_paired_absolute_error_reduction_pp_min"]
                           and summary["scene_wins"] >= req["scene_wins_min"]
                           and summary["maximum_regression_pp"] <= req["maximum_regression_pp"]
                           and summary["challenger_median_support_fraction"] >= req["median_support_fraction_min"]
                           and summary["challenger_total_selected_count"] >= req["total_selected_min"]
                           and summary["challenger_original_domain_complete_count"] == req["original_domain_complete_count"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "comparisons.json").write_text(json.dumps({"experiment_id": "P-004", "scope": "SIMULATED", "summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
