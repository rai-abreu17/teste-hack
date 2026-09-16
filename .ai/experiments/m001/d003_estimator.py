"""D003 truth-free pooled-point Delaunay reconstruction.

All accepted XYZ returns from the supplied views are registered in the box
coordinate system before one XY Delaunay triangulation is built.  The module
never imports scene truth or an evaluator.  It does not extrapolate outside
the convex hull of accepted observations.
"""

from collections import defaultdict
from collections.abc import Mapping
import hashlib
import math
import statistics

import numpy as np
from scipy.spatial import Delaunay, QhullError

from server import geometry as g


ALGORITHM_ID = "d003-pooled-xyz-delaunay-v1"
XY_MERGE_QUANTUM_M = 0.0005
MERGED_Z_RANGE_MAX_M = 0.003
QHULL_OPTIONS = "Qbb Qc Qz Q12"


def _reference_offset(value):
    if isinstance(value, bool):
        raise ValueError("invalid reference_offset_m")
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid reference_offset_m") from exc
    if not math.isfinite(value) or abs(value) > 0.10:
        raise ValueError("invalid reference_offset_m")
    return value


def _config(config):
    if config is None:
        config = {}
    if not isinstance(config, Mapping):
        raise ValueError("configuration must be a mapping or None")
    unknown = set(config) - {"reference_offset_m"}
    if unknown:
        raise ValueError(f"unsupported configuration keys: {sorted(map(str, unknown))}")
    return _reference_offset(config.get("reference_offset_m", 0.0))


def _merge_points(points):
    """Deterministically merge sub-millimetre XY coincidences.

    The XY key is a fixed nearest-0.5-mm bin.  A cluster is retained at the
    median measured XYZ only when its observed Z range is at most 3 mm.
    Larger ranges are treated as cross-view surface conflicts and withheld.
    """
    groups = defaultdict(list)
    for view_index, ray_index, point in points:
        key = (
            math.floor(point[0] / XY_MERGE_QUANTUM_M + 0.5),
            math.floor(point[1] / XY_MERGE_QUANTUM_M + 0.5),
        )
        groups[key].append((view_index, ray_index, point))

    accepted, conflicts = [], []
    for key in sorted(groups):
        items = groups[key]
        xs = [item[2][0] for item in items]
        ys = [item[2][1] for item in items]
        zs = [item[2][2] for item in items]
        z_range = max(zs) - min(zs)
        record = {
            "xy_bin": list(key),
            "observation_count": len(items),
            "view_indices": sorted({item[0] for item in items}),
            "ray_indices": [[item[0], item[1]] for item in sorted(items)],
            "z_range_m": z_range,
        }
        if z_range > MERGED_Z_RANGE_MAX_M:
            conflicts.append(record)
            continue
        accepted.append({
            **record,
            "point": [statistics.median(xs), statistics.median(ys), statistics.median(zs)],
        })
    accepted.sort(key=lambda item: tuple(item["point"]))
    return accepted, conflicts


def _raster_triangle(vertices, triangle_id, sums, counts, contributors, reference_offset_m):
    a, b, c = vertices
    edges = [math.dist(p, q) for p, q in ((a, b), (b, c), (c, a))]
    if max(edges) > g.MAX_EDGE_M:
        return False
    den = ((b[1] - c[1]) * (a[0] - c[0])
           + (c[0] - b[0]) * (a[1] - c[1]))
    if abs(den) < 1e-12:
        return False
    ix0 = max(0, math.ceil(min(v[0] for v in vertices) / g.CELL - 0.5))
    ix1 = min(g.NX - 1, math.floor(max(v[0] for v in vertices) / g.CELL - 0.5))
    iy0 = max(0, math.ceil(min(v[1] for v in vertices) / g.CELL - 0.5))
    iy1 = min(g.NY - 1, math.floor(max(v[1] for v in vertices) / g.CELL - 0.5))
    for iy in range(iy0, iy1 + 1):
        y = (iy + 0.5) * g.CELL
        for ix in range(ix0, ix1 + 1):
            x = (ix + 0.5) * g.CELL
            wa = (((b[1] - c[1]) * (x - c[0])
                   + (c[0] - b[0]) * (y - c[1])) / den)
            wb = (((c[1] - a[1]) * (x - c[0])
                   + (a[0] - c[0]) * (y - c[1])) / den)
            wc = 1 - wa - wb
            if min(wa, wb, wc) < -1e-7:
                continue
            height = sum(
                weight * (vertex[2] - g.base(vertex[0], vertex[1]) - reference_offset_m)
                for weight, vertex in ((wa, a), (wb, b), (wc, c))
            )
            if height < -g.BELOW_REFERENCE_TOLERANCE_M:
                continue
            cell = iy * g.NX + ix
            sums[cell] += max(0.0, height)
            counts[cell] += 1
            contributors[cell].append(triangle_id)
    return True


def estimate_frames(frames, config=None):
    reference_offset_m = _config(config)
    frames = list(frames)
    decoded_frames, invalid_frames, unavailable = [], [], []
    raw_points = []
    for view_index, raw in enumerate(frames):
        try:
            decoded = g.decode_frame(raw, reference_offset_m)
        except Exception as exc:
            invalid_frames.append({
                "index": view_index,
                "sha256": hashlib.sha256(raw).hexdigest() if isinstance(raw, bytes) else None,
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        frame_points = [
            (view_index, ray_index, point)
            for ray_index, point in enumerate(decoded["points_by_ray"])
            if point is not None
        ]
        state = "unavailable" if decoded["excluded"]["below_reference"] or not frame_points else "usable"
        if state == "unavailable":
            unavailable.append(view_index)
        else:
            raw_points.extend(frame_points)
        decoded_frames.append({
            "original_index": view_index,
            "state": state,
            "sensor_pose": decoded["sensor_pose"],
            "excluded": decoded["excluded"],
            "accepted_point_count": len(frame_points),
        })

    merged, conflicts = _merge_points(raw_points)
    points = [tuple(item["point"]) for item in merged]
    sums, counts = [0.0] * (g.NX * g.NY), [0] * (g.NX * g.NY)
    contributors = [[] for _ in range(g.NX * g.NY)]
    simplices, accepted_triangles, long_edge_triangles = [], [], []
    qhull_error = None
    coplanar_point_count = 0
    if len(points) >= 3:
        try:
            triangulation = Delaunay(
                np.asarray([(p[0], p[1]) for p in points], dtype=float),
                qhull_options=QHULL_OPTIONS,
            )
            coplanar_point_count = len(triangulation.coplanar)
            simplices = sorted(tuple(sorted(map(int, simplex))) for simplex in triangulation.simplices)
            for triangle_id, indices in enumerate(simplices):
                vertices = [points[index] for index in indices]
                if _raster_triangle(vertices, triangle_id, sums, counts, contributors, reference_offset_m):
                    accepted_triangles.append(list(indices))
                else:
                    long_edge_triangles.append(list(indices))
        except QhullError as exc:
            qhull_error = str(exc).splitlines()[0]

    heights = [value / count if count else None for value, count in zip(sums, counts)]
    supported = sum(value is not None for value in heights)
    observed = sum(value for value in heights if value is not None) * g.CELL ** 2 if supported else None
    total_eligible = (
        supported == g.NX * g.NY
        and not invalid_frames
        and not unavailable
        and qhull_error is None
        and coplanar_point_count == 0
    )
    reasons = []
    if supported != g.NX * g.NY:
        reasons.append(f"support_{supported}_of_{g.NX * g.NY}")
    if invalid_frames:
        reasons.append(f"invalid_frames_{len(invalid_frames)}")
    if unavailable:
        reasons.append(f"unavailable_views_{len(unavailable)}")
    if qhull_error:
        reasons.append("qhull_error")
    if coplanar_point_count:
        reasons.append(f"qhull_omitted_points_{coplanar_point_count}")

    return {
        "algorithm_id": ALGORITHM_ID,
        "frame_count_input": len(frames),
        "decoded_frames": decoded_frames,
        "invalid_frames": invalid_frames,
        "unavailable_view_indices": unavailable,
        "raw_point_count": len(raw_points),
        "merged_point_count": len(points),
        "merge_conflict_count": len(conflicts),
        "merge_conflicts": conflicts,
        "merged_points": merged,
        "delaunay_simplex_count": len(simplices),
        "accepted_triangle_count": len(accepted_triangles),
        "long_or_degenerate_triangle_count": len(long_edge_triangles),
        "accepted_triangles": accepted_triangles,
        "qhull_options": QHULL_OPTIONS,
        "qhull_error": qhull_error,
        "coplanar_point_count": coplanar_point_count,
        "heights": heights,
        "triangle_contributors_by_cell": contributors,
        "support_cell_count": supported,
        "support_fraction": supported / (g.NX * g.NY),
        "measurement_state": "valid" if total_eligible else "partial" if supported else "unavailable",
        "observed_volume_m3": observed,
        "total_volume_m3": observed if total_eligible else None,
        "total_selection": {"selected": total_eligible, "rejection_reasons": reasons},
        "parameters": {
            "xy_merge_quantum_m": XY_MERGE_QUANTUM_M,
            "merged_z_range_max_m": MERGED_Z_RANGE_MAX_M,
            "maximum_3d_triangle_edge_m": g.MAX_EDGE_M,
            "outside_convex_hull": "unsupported",
            "cross_view_height_policy": "median if Z range <= threshold; otherwise withhold cluster",
        },
    }
