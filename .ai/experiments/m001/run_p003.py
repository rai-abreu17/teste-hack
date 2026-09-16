"""P-003: reuse P-001 frames and ablate only cross-view fusion."""

import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P001_RESULTS = ROOT / ".ai" / "runs" / "m001-implementation" / "results"
OUT = ROOT / ".ai" / "runs" / "m001-p003" / "results"
sys.path[:0] = [str(ROOT), str(HERE)]

from experiments.truth import Scene, cell_volumes
from m001_estimator import fuse_frames
from server import geometry as g


def triangle_quality_by_cell(raw):
    """Return per-cell compactness using only decoded measurement geometry."""
    decoded = g.decode_frame(raw)
    points = decoded["points_by_ray"]
    cols, rows = decoded["columns"], decoded["rows"]
    quality = [None] * (g.NX * g.NY)
    for row in range(rows - 1):
        for col in range(cols - 1):
            a = row * cols + col
            for indices in ((a, a + 1, a + cols + 1), (a, a + cols + 1, a + cols)):
                verts = [points[index] for index in indices]
                if any(vertex is None for vertex in verts):
                    continue
                p, q, r = verts
                edges = (math.dist(p, q), math.dist(q, r), math.dist(r, p))
                compactness = max(edges)
                if compactness > g.MAX_EDGE_M:
                    continue
                denominator = ((q[1] - r[1]) * (p[0] - r[0])
                               + (r[0] - q[0]) * (p[1] - r[1]))
                if abs(denominator) < 1e-9:
                    continue
                ix0 = max(0, math.ceil(min(v[0] for v in verts) / g.CELL - 0.5))
                ix1 = min(g.NX - 1, math.floor(max(v[0] for v in verts) / g.CELL - 0.5))
                iy0 = max(0, math.ceil(min(v[1] for v in verts) / g.CELL - 0.5))
                iy1 = min(g.NY - 1, math.floor(max(v[1] for v in verts) / g.CELL - 0.5))
                for iy in range(iy0, iy1 + 1):
                    y = (iy + 0.5) * g.CELL
                    for ix in range(ix0, ix1 + 1):
                        x = (ix + 0.5) * g.CELL
                        wa = ((q[1] - r[1]) * (x - r[0]) + (r[0] - q[0]) * (y - r[1])) / denominator
                        wb = ((r[1] - p[1]) * (x - r[0]) + (p[0] - r[0]) * (y - r[1])) / denominator
                        wc = 1.0 - wa - wb
                        if min(wa, wb, wc) < -1e-7:
                            continue
                        index = iy * g.NX + ix
                        if quality[index] is None or compactness < quality[index]:
                            quality[index] = compactness
    return quality


def compact_fusion(frames):
    conventional = fuse_frames(frames, {"reference_offset_m": 0.0})
    qualities = [triangle_quality_by_cell(frame) for frame in frames]
    heights = []
    selections = [0] * len(frames)
    for cell in range(g.NX * g.NY):
        candidates = []
        for view_index, view in enumerate(conventional["per_view"]):
            height = view["heights"][cell]
            quality = qualities[view_index][cell]
            if height is not None and quality is not None:
                candidates.append((quality, view_index, height))
        if not candidates:
            heights.append(None)
            continue
        _, view_index, height = min(candidates)
        selections[view_index] += 1
        heights.append(height)
    return {"heights": heights,
            "support_fraction": sum(h is not None for h in heights) / (g.NX * g.NY),
            "total_selected": all(h is not None for h in heights),
            "selected_cells_by_view": selections}


def metrics(heights, truth_cells, mask):
    complete = all(not selected or height is not None for selected, height in zip(mask, heights))
    if not complete:
        return complete, None
    reference = sum(value for value, selected in zip(truth_cells, mask) if selected)
    estimated = sum(height for height, selected in zip(heights, mask) if selected) * g.CELL ** 2
    signed = 100.0 * (estimated - reference) / reference
    return complete, signed


def main():
    protocol_path = HERE / "protocol_p003.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol_digest = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    p001 = json.loads((P001_RESULTS / "comparisons.json").read_text(encoding="utf-8"))
    rows = []
    paired = []
    for scene_result in p001["scenes"]:
        scene_id = scene_result["scene_id"]
        data = scene_result["scene_for_evaluator_only"]
        scene = Scene(fill=data["fill"], shape=data["shape"], cx=data["cx"],
                      obstacle=data["obstacle"], dropout=data["dropout"],
                      range_m=4.0, sensor_z=.40)
        truth_cells = cell_volumes(scene)
        original_mask = [all(arm["heights"][cell] is not None for arm in scene_result["arms"])
                         for cell in range(g.NX * g.NY)]

        p001_by_arm = {arm["arm_id"]: arm for arm in scene_result["arms"]}
        baseline = p001_by_arm["fixed3"]
        baseline_error = baseline["evaluation"]["common_all_arms_domain"]["signed_error_percent"]
        frames = [path.read_bytes() for path in sorted(
            (P001_RESULTS / "frames" / scene_id).glob("translated3_aimed-*.bin"))]
        median = fuse_frames(frames, {"reference_offset_m": 0.0})
        compact = compact_fusion(frames)
        if median["heights"] != p001_by_arm["translated3_aimed"]["heights"]:
            raise AssertionError(f"P-001 median was not reproduced for {scene_id}")
        if compact["support_fraction"] != median["tin_support_union_fraction"]:
            raise AssertionError(f"fusion changed support for {scene_id}")

        for variant, heights, support, total, selections in (
                ("median", median["heights"], median["tin_support_union_fraction"],
                 median["total_selection"]["selected"], None),
                ("most_compact_local_triangle", compact["heights"], compact["support_fraction"],
                 compact["total_selected"], compact["selected_cells_by_view"])):
            complete, signed = metrics(heights, truth_cells, original_mask)
            rows.append({"scene_id": scene_id, "variant": variant,
                         "original_common_cells": sum(original_mask),
                         "original_domain_complete": complete,
                         "tin_support_fraction": support, "total_selected": total,
                         "signed_error_percent": signed,
                         "absolute_error_percent": None if signed is None else abs(signed),
                         "selected_cells_by_view": selections})
        challenge = rows[-1]
        reduction = (None if challenge["absolute_error_percent"] is None else
                     abs(baseline_error) - challenge["absolute_error_percent"])
        paired.append({"scene_id": scene_id,
                       "baseline_absolute_error_percent": abs(baseline_error),
                       "challenger_absolute_error_percent": challenge["absolute_error_percent"],
                       "absolute_error_reduction_pp": reduction})

    challenger = [row for row in rows if row["variant"] == "most_compact_local_triangle"]
    deltas = [row["absolute_error_reduction_pp"] for row in paired
              if row["absolute_error_reduction_pp"] is not None]
    summary = {
        "protocol_sha256": protocol_digest,
        "comparison_count": len(rows), "paired": paired,
        "median_absolute_error_reduction_pp": statistics.median(deltas) if deltas else None,
        "scene_wins": sum(delta > 0 for delta in deltas),
        "maximum_regression_pp": max([0.0, *(-delta for delta in deltas)]),
        "challenger_median_support_fraction": statistics.median(row["tin_support_fraction"] for row in challenger),
        "challenger_total_selected_count": sum(row["total_selected"] for row in challenger),
        "challenger_original_domain_complete_count": sum(row["original_domain_complete"] for row in challenger)
    }
    req = protocol["approval"]
    summary["approved"] = (
        summary["median_absolute_error_reduction_pp"] >= req["median_paired_absolute_error_reduction_pp_min"]
        and summary["scene_wins"] >= req["scene_wins_min"]
        and summary["maximum_regression_pp"] <= req["maximum_regression_pp"]
        and summary["challenger_median_support_fraction"] >= req["median_support_fraction_min"]
        and summary["challenger_total_selected_count"] >= req["total_selected_min"]
        and summary["challenger_original_domain_complete_count"] == req["original_domain_complete_count"])
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"experiment_id": "P-003", "scope": "SIMULATED", "summary": summary, "rows": rows}
    (OUT / "comparisons.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
