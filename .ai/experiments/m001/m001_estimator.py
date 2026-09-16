"""P-001 multi-view fusion. Inputs are frame bytes and fixed fusion config only."""

import hashlib
import math
import statistics
import struct

from server import geometry as g


def _point_bin(point):
    ix = math.floor(point[0] / g.CELL)
    iy = math.floor(point[1] / g.CELL)
    if 0 <= ix < g.NX and 0 <= iy < g.NY:
        return iy * g.NX + ix
    return None


def fuse_frames(frames, config):
    """Fuse only independent per-frame grids; never form triangles across views."""
    unknown = set(config) - {"reference_offset_m"}
    if unknown:
        raise ValueError(f"unsupported fusion configuration keys: {sorted(unknown)}")
    reference_offset_m = float(config.get("reference_offset_m", 0.0))
    per_view = []
    invalid_frames = []
    excluded = {name: 0 for name in
                ("no_return", "out_of_range", "beam", "wall_or_outside", "below_reference")}
    point_bins_union = set()

    for index, raw in enumerate(frames):
        digest = hashlib.sha256(raw).hexdigest()
        try:
            decoded = g.decode_frame(raw, reference_offset_m)
            estimate = g.estimate(raw, reference_offset_m)
        except (ValueError, TypeError, struct.error) as exc:
            invalid_frames.append({"index": index, "sha256": digest, "error": str(exc)})
            continue
        heights = estimate["grid"]["height_m"]
        support = [height is not None for height in heights]
        point_bins = {_point_bin(point) for point in decoded["points_by_ray"] if point is not None}
        point_bins.discard(None)
        point_bins_union.update(point_bins)
        for name, count in decoded["excluded"].items():
            excluded[name] += count
        per_view.append({
            "index": index,
            "sha256": digest,
            "sequence": decoded["sequence"],
            "pose": decoded["sensor_pose"],
            "measurement_state": estimate["measurement_state"],
            "heights": heights,
            "support_cell_count": sum(support),
            "effective_point_bin_count": len(point_bins),
            "valid_return_count": sum(point is not None for point in decoded["points_by_ray"]),
            "excluded": decoded["excluded"],
        })

    fused_heights = []
    ranges = []
    multi_view_cells = 0
    for cell in range(g.NX * g.NY):
        values = [view["heights"][cell] for view in per_view if view["heights"][cell] is not None]
        fused_heights.append(statistics.median(values) if values else None)
        if len(values) >= 2:
            multi_view_cells += 1
            ranges.append(max(values) - min(values))

    supported = sum(value is not None for value in fused_heights)
    unusable_views = sum(view["measurement_state"] == "unavailable" for view in per_view)
    total_eligible = supported == g.NX * g.NY and not invalid_frames and unusable_views == 0
    observed = (sum(value for value in fused_heights if value is not None) * g.CELL**2
                if supported else None)
    if total_eligible:
        state = "valid"
    elif supported:
        state = "partial"
    else:
        state = "unavailable"
    rejection_reasons = []
    if supported != g.NX * g.NY:
        rejection_reasons.append(f"support_{supported}_of_{g.NX * g.NY}")
    if invalid_frames:
        rejection_reasons.append(f"invalid_frames_{len(invalid_frames)}")
    if unusable_views:
        rejection_reasons.append(f"unavailable_views_{unusable_views}")

    return {
        "algorithm_id": "p001-per-view-tin-median-v1",
        "measurement_state": state,
        "frame_count_input": len(frames),
        "frame_count_valid": len(per_view),
        "invalid_frames": invalid_frames,
        "per_view": per_view,
        "heights": fused_heights,
        "tin_support_union_cell_count": supported,
        "tin_support_union_fraction": supported / (g.NX * g.NY),
        "effective_point_bin_union_count": len(point_bins_union),
        "effective_point_bin_union_fraction": len(point_bins_union) / (g.NX * g.NY),
        "excluded_aggregate": excluded,
        "observed_volume_m3": observed,
        "total_volume_m3": observed if total_eligible else None,
        "total_selection": {"selected": total_eligible, "rejection_reasons": rejection_reasons},
        "view_disagreement": {
            "cells_with_two_or_more_views": multi_view_cells,
            "median_height_range_m": statistics.median(ranges) if ranges else None,
            "mean_height_range_m": statistics.mean(ranges) if ranges else None,
            "max_height_range_m": max(ranges) if ranges else None,
        },
    }
