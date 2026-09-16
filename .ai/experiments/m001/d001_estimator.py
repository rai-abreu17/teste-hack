"""D-001 truth-free piecewise-plane reconstruction over archived ToF frames.

The candidate differs from the existing local TIN only where the observations
support a plane with at least four independent vertices.  Three-point planes
are never sufficient.  A fitted patch can cover a bounded hole inside its
observed convex hull; those cells remain explicitly labelled ``model``.

There are no simulator, scene-label, truth-volume, or evaluator imports.
"""

from collections import defaultdict
from collections.abc import Mapping
import hashlib
import itertools
import math
import statistics
import struct

from server import geometry as g


ALGORITHM_ID = "d001-piecewise-plane-hull-v1"
PLANE_TOLERANCE_M = 0.002
MIN_PATCH_VERTICES = 4
MIN_PATCH_TRIANGLES = 2
MODEL_NEAREST_LIMIT_M = g.MAX_EDGE_M / 2.0


def _reference_offset(config):
    if config is None:
        config = {}
    if not isinstance(config, Mapping):
        raise ValueError("config must be a mapping or None")
    unknown = set(config) - {"reference_offset_m"}
    if unknown:
        raise ValueError(f"unsupported configuration keys: {sorted(map(str, unknown))}")
    value = config.get("reference_offset_m", 0.0)
    if isinstance(value, bool):
        raise ValueError("invalid reference_offset_m")
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid reference_offset_m") from exc
    if not math.isfinite(value) or abs(value) > 0.10:
        raise ValueError("invalid reference_offset_m")
    return value


def _triangles(columns, rows):
    triangle_id = 0
    for row in range(rows - 1):
        for column in range(columns - 1):
            a = row * columns + column
            yield triangle_id, (a, a + 1, a + columns + 1)
            triangle_id += 1
            yield triangle_id, (a, a + columns + 1, a + columns)
            triangle_id += 1


def _valid_triangle(points, indices):
    vertices = [points[index] for index in indices]
    if any(vertex is None for vertex in vertices):
        return False
    if any(math.dist(a, b) > g.MAX_EDGE_M
           for a, b in ((vertices[0], vertices[1]),
                        (vertices[1], vertices[2]),
                        (vertices[2], vertices[0]))):
        return False
    a, b, c = vertices
    determinant = ((b[1] - c[1]) * (a[0] - c[0])
                   + (c[0] - b[0]) * (a[1] - c[1]))
    return abs(determinant) >= 1e-9


def _solve_3x3(matrix, vector):
    augmented = [list(row) + [value] for row, value in zip(matrix, vector)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            scale = augmented[row][column]
            augmented[row] = [
                value - scale * reference
                for value, reference in zip(augmented[row], augmented[column])
            ]
    return tuple(augmented[row][3] for row in range(3))


def _fit_plane(vertex_indices, points, reference_offset_m):
    """Least-squares material-height plane h = ax + by + c."""
    rows = []
    values = []
    for index in sorted(vertex_indices):
        x, y, z = points[index]
        rows.append((x, y, 1.0))
        values.append(z - g.base(x, y) - reference_offset_m)
    normal = [[sum(row[i] * row[j] for row in rows) for j in range(3)]
              for i in range(3)]
    rhs = [sum(row[i] * value for row, value in zip(rows, values))
           for i in range(3)]
    coefficients = _solve_3x3(normal, rhs)
    if coefficients is None:
        return None
    residuals = [
        abs(sum(coefficient * term for coefficient, term in zip(coefficients, row)) - value)
        for row, value in zip(rows, values)
    ]
    return {
        "coefficients": coefficients,
        "maximum_residual_m": max(residuals),
        "rms_residual_m": math.sqrt(sum(value * value for value in residuals) / len(residuals)),
    }


def _segment_patches(points, columns, rows, reference_offset_m=0.0):
    triangles = {
        triangle_id: indices
        for triangle_id, indices in _triangles(columns, rows)
        if _valid_triangle(points, indices)
    }
    edge_to_triangles = defaultdict(list)
    for triangle_id, indices in triangles.items():
        for edge in itertools.combinations(indices, 2):
            edge_to_triangles[tuple(sorted(edge))].append(triangle_id)
    neighbors = defaultdict(set)
    for ids in edge_to_triangles.values():
        for left, right in itertools.combinations(ids, 2):
            neighbors[left].add(right)
            neighbors[right].add(left)

    unassigned = set(triangles)
    patches = []
    rejected = []
    while unassigned:
        seed = min(unassigned)
        seed_options = []
        for neighbor in sorted(neighbors[seed] & unassigned):
            vertex_indices = set(triangles[seed]) | set(triangles[neighbor])
            if len(vertex_indices) < MIN_PATCH_VERTICES:
                continue
            fit = _fit_plane(vertex_indices, points, reference_offset_m)
            if fit is not None and fit["maximum_residual_m"] <= PLANE_TOLERANCE_M:
                seed_options.append((fit["maximum_residual_m"], neighbor, fit, vertex_indices))
        if not seed_options:
            unassigned.remove(seed)
            rejected.append(seed)
            continue

        _, neighbor, fit, vertex_indices = min(seed_options, key=lambda item: (item[0], item[1]))
        patch_triangles = {seed, neighbor}
        unassigned.remove(seed)
        unassigned.remove(neighbor)

        changed = True
        while changed:
            changed = False
            frontier = sorted(set().union(*(neighbors[item] for item in patch_triangles)) & unassigned)
            for candidate in frontier:
                candidate_vertices = vertex_indices | set(triangles[candidate])
                candidate_fit = _fit_plane(candidate_vertices, points, reference_offset_m)
                if (candidate_fit is not None
                        and candidate_fit["maximum_residual_m"] <= PLANE_TOLERANCE_M):
                    patch_triangles.add(candidate)
                    vertex_indices = candidate_vertices
                    fit = candidate_fit
                    unassigned.remove(candidate)
                    changed = True

        patches.append({
            "patch_id": len(patches),
            "triangle_ids": sorted(patch_triangles),
            "vertex_indices": sorted(vertex_indices),
            "coefficients": fit["coefficients"],
            "maximum_residual_m": fit["maximum_residual_m"],
            "rms_residual_m": fit["rms_residual_m"],
        })
    return patches, triangles, rejected


def _triangle_cells(vertices):
    a, b, c = vertices
    denominator = ((b[1] - c[1]) * (a[0] - c[0])
                   + (c[0] - b[0]) * (a[1] - c[1]))
    if abs(denominator) < 1e-9:
        return set()
    ix0 = max(0, math.ceil(min(value[0] for value in vertices) / g.CELL - 0.5))
    ix1 = min(g.NX - 1, math.floor(max(value[0] for value in vertices) / g.CELL - 0.5))
    iy0 = max(0, math.ceil(min(value[1] for value in vertices) / g.CELL - 0.5))
    iy1 = min(g.NY - 1, math.floor(max(value[1] for value in vertices) / g.CELL - 0.5))
    cells = set()
    for iy in range(iy0, iy1 + 1):
        y = (iy + 0.5) * g.CELL
        for ix in range(ix0, ix1 + 1):
            x = (ix + 0.5) * g.CELL
            wa = (((b[1] - c[1]) * (x - c[0])
                   + (c[0] - b[0]) * (y - c[1])) / denominator)
            wb = (((c[1] - a[1]) * (x - c[0])
                   + (a[0] - c[0]) * (y - c[1])) / denominator)
            if min(wa, wb, 1.0 - wa - wb) >= -1e-7:
                cells.add(iy * g.NX + ix)
    return cells


def _convex_hull(xy_points):
    points = sorted(set(xy_points))
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


def _inside_convex(point, polygon):
    if len(polygon) < 3:
        return False
    signs = []
    for index, a in enumerate(polygon):
        b = polygon[(index + 1) % len(polygon)]
        cross = ((b[0] - a[0]) * (point[1] - a[1])
                 - (b[1] - a[1]) * (point[0] - a[0]))
        if abs(cross) > 1e-10:
            signs.append(cross > 0)
    return not signs or all(sign == signs[0] for sign in signs)


def _patch_candidates(patch, triangles, points):
    observed_cells = set()
    for triangle_id in patch["triangle_ids"]:
        observed_cells.update(_triangle_cells([points[index] for index in triangles[triangle_id]]))
    xy_points = [(points[index][0], points[index][1]) for index in patch["vertex_indices"]]
    hull = _convex_hull(xy_points)
    a, b, c = patch["coefficients"]
    candidates = {}
    for cell in range(g.NX * g.NY):
        x = (cell % g.NX + 0.5) * g.CELL
        y = (cell // g.NX + 0.5) * g.CELL
        kind = None
        if cell in observed_cells:
            kind = "observed"
        elif (_inside_convex((x, y), hull)
              and min(math.hypot(x - px, y - py) for px, py in xy_points)
              <= MODEL_NEAREST_LIMIT_M):
            kind = "model"
        if kind is None:
            continue
        height = a * x + b * y + c
        if height < -g.BELOW_REFERENCE_TOLERANCE_M:
            continue
        candidates[cell] = {"kind": kind, "height_m": max(0.0, height)}
    return candidates


def analyze_frame(raw, reference_offset_m=0.0):
    if isinstance(reference_offset_m, bool):
        raise ValueError("invalid reference_offset_m")
    try:
        reference_offset_m = float(reference_offset_m)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid reference_offset_m") from exc
    if not math.isfinite(reference_offset_m) or abs(reference_offset_m) > 0.10:
        raise ValueError("invalid reference_offset_m")
    decoded = g.decode_frame(raw, reference_offset_m)
    points = decoded["points_by_ray"]
    patches, triangles, rejected = _segment_patches(
        points, decoded["columns"], decoded["rows"], reference_offset_m,
    )
    by_cell = [[] for _ in range(g.NX * g.NY)]
    patch_diagnostics = []
    for patch in patches:
        candidates = _patch_candidates(patch, triangles, points)
        for cell, candidate in candidates.items():
            by_cell[cell].append({"patch_id": patch["patch_id"], **candidate})
        patch_diagnostics.append({
            key: (list(value) if key == "coefficients" else value)
            for key, value in patch.items()
        } | {
            "observed_support_cell_count": sum(
                candidate["kind"] == "observed" for candidate in candidates.values()
            ),
            "model_support_cell_count": sum(
                candidate["kind"] == "model" for candidate in candidates.values()
            ),
        })

    heights = []
    support_kinds = []
    conflicts = []
    for cell, candidates in enumerate(by_cell):
        observed = [item for item in candidates if item["kind"] == "observed"]
        selected = observed or candidates
        if not selected:
            heights.append(None)
            support_kinds.append(None)
            continue
        values = [item["height_m"] for item in selected]
        if max(values) - min(values) > PLANE_TOLERANCE_M:
            heights.append(None)
            support_kinds.append(None)
            conflicts.append({
                "cell": cell,
                "patch_ids": [item["patch_id"] for item in selected],
                "height_range_m": max(values) - min(values),
            })
            continue
        heights.append(statistics.median(values))
        support_kinds.append("observed" if observed else "model")

    supported = sum(value is not None for value in heights)
    unavailable = bool(decoded["excluded"]["below_reference"])
    state = ("unavailable" if unavailable or supported == 0 else
             "model_supported" if supported == g.NX * g.NY else "partial")
    return {
        "algorithm_id": ALGORITHM_ID,
        "heights": heights,
        "support_kind_by_cell": support_kinds,
        "measurement_state": state,
        "patches": patch_diagnostics,
        "valid_local_triangle_count": len(triangles),
        "accepted_patch_triangle_count": sum(len(item["triangle_ids"]) for item in patches),
        "rejected_triangle_ids": rejected,
        "conflicts": conflicts,
        "sensor_pose": decoded["sensor_pose"],
        "excluded": decoded["excluded"],
    }


def _sha256(raw):
    try:
        return hashlib.sha256(raw).hexdigest()
    except (TypeError, ValueError, BufferError):
        return None


def fuse_frames(frames, config=None):
    """Reconstruct and conventionally median-fuse multiple fixed views."""
    reference_offset_m = _reference_offset(config)
    if isinstance(frames, (bytes, bytearray, memoryview, str)) or frames is None:
        raise ValueError("frames must be an iterable of frame objects")
    try:
        indexed_frames = enumerate(frames)
    except TypeError as exc:
        raise ValueError("frames must be an iterable of frame objects") from exc

    per_view = []
    invalid_frames = []
    input_count = 0
    for index, raw in indexed_frames:
        input_count += 1
        digest = _sha256(raw)
        try:
            view = analyze_frame(raw, reference_offset_m)
        except (ValueError, TypeError, struct.error, OverflowError) as exc:
            invalid_frames.append({"index": index, "sha256": digest, "error": str(exc)})
            continue
        view.update({"index": index, "sha256": digest})
        per_view.append(view)

    heights = []
    support_kinds = []
    selected_view_indices = []
    for cell in range(g.NX * g.NY):
        candidates = [
            (view["support_kind_by_cell"][cell], view["index"], view["heights"][cell])
            for view in per_view
            if view["measurement_state"] != "unavailable" and view["heights"][cell] is not None
        ]
        observed = [item for item in candidates if item[0] == "observed"]
        selected = observed or candidates
        if not selected:
            heights.append(None)
            support_kinds.append(None)
            selected_view_indices.append([])
            continue
        heights.append(statistics.median(item[2] for item in selected))
        support_kinds.append("observed" if observed else "model")
        selected_view_indices.append([item[1] for item in selected])

    observed_count = sum(kind == "observed" for kind in support_kinds)
    model_count = sum(kind == "model" for kind in support_kinds)
    supported = observed_count + model_count
    unavailable_indices = [
        view["index"] for view in per_view if view["measurement_state"] == "unavailable"
    ]
    total_selected = (
        supported == g.NX * g.NY and not invalid_frames and not unavailable_indices
    )
    reconstructed_volume = (
        sum(value for value in heights if value is not None) * g.CELL ** 2
        if supported else None
    )
    observed_volume = sum(
        heights[cell] for cell, kind in enumerate(support_kinds) if kind == "observed"
    ) * g.CELL ** 2
    model_fill_volume = sum(
        heights[cell] for cell, kind in enumerate(support_kinds) if kind == "model"
    ) * g.CELL ** 2
    rejection_reasons = []
    if supported != g.NX * g.NY:
        rejection_reasons.append(f"support_{supported}_of_{g.NX * g.NY}")
    if invalid_frames:
        rejection_reasons.append(f"invalid_frames_{len(invalid_frames)}")
    if unavailable_indices:
        rejection_reasons.append(f"unavailable_views_{len(unavailable_indices)}")
    state = ("model_supported" if total_selected else
             "partial" if supported else "unavailable")
    return {
        "algorithm_id": ALGORITHM_ID,
        "parameters": {
            "plane_tolerance_m": PLANE_TOLERANCE_M,
            "minimum_patch_vertices": MIN_PATCH_VERTICES,
            "minimum_patch_triangles": MIN_PATCH_TRIANGLES,
            "maximum_local_edge_m": g.MAX_EDGE_M,
            "model_nearest_limit_m": MODEL_NEAREST_LIMIT_M,
            "cross_view_fusion": "conventional_median_observed_first",
        },
        "frame_count_input": input_count,
        "frame_count_valid": len(per_view),
        "heights": heights,
        "support_kind_by_cell": support_kinds,
        "selected_view_indices_by_cell": selected_view_indices,
        "per_view": per_view,
        "invalid_frames": invalid_frames,
        "unavailable_view_indices": unavailable_indices,
        "measurement_state": state,
        "observed_support_cell_count": observed_count,
        "model_support_cell_count": model_count,
        "supported_cell_count": supported,
        "support_fraction": supported / (g.NX * g.NY),
        "observed_supported_volume_m3": observed_volume,
        "model_fill_volume_m3": model_fill_volume,
        "reconstructed_supported_volume_m3": reconstructed_volume,
        "observed_volume_m3": observed_volume if observed_count else None,
        "total_volume_m3": reconstructed_volume if total_selected else None,
        "model_based_total": total_selected and model_count > 0,
        "total_selection": {
            "selected": total_selected,
            "rejection_reasons": rejection_reasons,
        },
    }
