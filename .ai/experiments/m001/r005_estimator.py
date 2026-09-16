"""R-005 truth-free, instrumented per-view TIN and cross-view fusion.

The raster equations, triangle order, thresholds, and per-view averaging mirror
``server.geometry.estimate``.  Instrumentation records the exact triangles
whose heights enter each cell; diagnostic quality is the mean maximum 3-D edge
length across that same contributor set.  It is not a calibrated uncertainty.
"""

from collections.abc import Mapping
import hashlib
import math
import statistics
import struct

from server import geometry as g


ALGORITHM_ID = "r005-instrumented-per-view-tin-fusion-v1"
QUALITY_DEFINITION = (
    "diagnostic mean(max_edge_m) over exactly the triangles contributing to "
    "the per-view cell height; not calibrated"
)


def _reference_offset(value):
    if isinstance(value, bool):
        raise ValueError("invalid reference_offset_m")
    try:
        reference_offset_m = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid reference_offset_m") from exc
    if not math.isfinite(reference_offset_m) or abs(reference_offset_m) > 0.10:
        raise ValueError("invalid reference_offset_m")
    return reference_offset_m


def _fusion_config(config, trim_kappa, lower):
    if config is None:
        config = {}
    if not isinstance(config, Mapping):
        raise ValueError("fusion config must be a mapping or None")
    unknown = set(config) - {"reference_offset_m"}
    if unknown:
        raise ValueError(f"unsupported fusion configuration keys: {sorted(map(str, unknown))}")
    reference_offset_m = _reference_offset(config.get("reference_offset_m", 0.0))
    if trim_kappa is not None:
        if isinstance(trim_kappa, bool):
            raise ValueError("trim_kappa must be a finite number >= 1")
        try:
            trim_kappa = float(trim_kappa)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("trim_kappa must be a finite number >= 1") from exc
        if not math.isfinite(trim_kappa) or trim_kappa < 1.0:
            raise ValueError("trim_kappa must be a finite number >= 1")
    if not isinstance(lower, bool):
        raise ValueError("lower must be bool")
    return reference_offset_m, trim_kappa


def _raster_triangle(decoded, indices, triangle_id, contributions, reference_offset_m):
    points = decoded["points_by_ray"]
    verts = [points[k] for k in indices]
    if any(v is None for v in verts):
        return
    a, b, c = verts
    edges = tuple(math.dist(p, q) for p, q in ((a, b), (b, c), (c, a)))
    max_edge_m = max(edges)
    if any(edge > g.MAX_EDGE_M for edge in edges):
        return
    den = ((b[1] - c[1]) * (a[0] - c[0])
           + (c[0] - b[0]) * (a[1] - c[1]))
    if abs(den) < 1e-9:
        return
    projected_area_m2 = abs(den) / 2.0
    ix0 = max(0, math.ceil(min(v[0] for v in verts) / g.CELL - 0.5))
    ix1 = min(g.NX - 1, math.floor(max(v[0] for v in verts) / g.CELL - 0.5))
    iy0 = max(0, math.ceil(min(v[1] for v in verts) / g.CELL - 0.5))
    iy1 = min(g.NY - 1, math.floor(max(v[1] for v in verts) / g.CELL - 0.5))
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
                w * (v[2] - g.base(v[0], v[1]) - reference_offset_m)
                for w, v in ((wa, a), (wb, b), (wc, c))
            )
            if height < -g.BELOW_REFERENCE_TOLERANCE_M:
                continue
            cell = iy * g.NX + ix
            contributions[cell].append({
                "triangle_id": triangle_id,
                "triangle_indices": list(indices),
                "height_m": max(0, height),
                "max_edge_m": max_edge_m,
                "projected_area_m2": projected_area_m2,
            })


def analyze_frame(raw, reference_offset_m=0.0):
    """Decode one frame and expose the exact local-TIN cell contributors."""
    reference_offset_m = _reference_offset(reference_offset_m)
    decoded = g.decode_frame(raw, reference_offset_m)
    cols, rows = decoded["columns"], decoded["rows"]
    contributions = [[] for _ in range(g.NX * g.NY)]
    triangle_id = 0
    for row in range(rows - 1):
        for col in range(cols - 1):
            a = row * cols + col
            _raster_triangle(
                decoded, (a, a + 1, a + cols + 1), triangle_id,
                contributions, reference_offset_m,
            )
            triangle_id += 1
            _raster_triangle(
                decoded, (a, a + cols + 1, a + cols), triangle_id,
                contributions, reference_offset_m,
            )
            triangle_id += 1

    heights = [
        (sum(item["height_m"] for item in cell) / len(cell)) if cell else None
        for cell in contributions
    ]
    quality = [
        (sum(item["max_edge_m"] for item in cell) / len(cell)) if cell else None
        for cell in contributions
    ]
    covered = sum(height is not None for height in heights)
    measurement_state = (
        "valid" if covered == g.NX * g.NY
        else "partial" if covered
        else "unavailable"
    )
    if decoded["excluded"]["below_reference"]:
        measurement_state = "unavailable"
    return {
        "heights": heights,
        "contributions": contributions,
        "quality": quality,
        "quality_definition": QUALITY_DEFINITION,
        "decoded": decoded,
        "measurement_state": measurement_state,
    }


def _sha256(raw):
    try:
        return hashlib.sha256(raw).hexdigest()
    except (TypeError, ValueError, BufferError):
        return None


def fuse_frames(frames, config=None, *, trim_kappa=None, lower=False):
    """Fuse independent per-frame grids with optional quality trimming.

    Unavailable decoded views remain in ``per_view`` for attribution but supply
    no fusion candidates.  Any invalid or unavailable input explicitly
    disqualifies total-volume selection.
    """
    reference_offset_m, trim_kappa = _fusion_config(config, trim_kappa, lower)
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
            analysis = analyze_frame(raw, reference_offset_m)
        except (ValueError, TypeError, struct.error, OverflowError) as exc:
            invalid_frames.append({
                "index": index,
                "sha256": digest,
                "error": str(exc),
            })
            continue
        analysis.update({"index": index, "sha256": digest})
        per_view.append(analysis)

    fused_heights = []
    selected_view_indices = []
    trimmed_cell_count = 0
    for cell in range(g.NX * g.NY):
        candidates = [
            (view["quality"][cell], view["index"], view["heights"][cell])
            for view in per_view
            if view["measurement_state"] != "unavailable"
            and view["heights"][cell] is not None
            and view["quality"][cell] is not None
        ]
        retained = candidates
        if candidates and trim_kappa is not None:
            minimum = min(item[0] for item in candidates)
            retained = [item for item in candidates if item[0] <= trim_kappa * minimum]
            if len(retained) < len(candidates):
                trimmed_cell_count += 1
        if not retained:
            fused_heights.append(None)
            selected_view_indices.append([])
            continue
        values = sorted(item[2] for item in retained)
        fused_heights.append(
            values[(len(values) - 1) // 2] if lower else statistics.median(values)
        )
        selected_view_indices.append([item[1] for item in retained])

    supported = sum(value is not None for value in fused_heights)
    unavailable_indices = [
        view["index"] for view in per_view
        if view["measurement_state"] == "unavailable"
    ]
    total_eligible = (
        supported == g.NX * g.NY
        and not invalid_frames
        and not unavailable_indices
    )
    observed = (
        sum(value for value in fused_heights if value is not None) * g.CELL ** 2
        if supported else None
    )
    measurement_state = (
        "valid" if total_eligible
        else "partial" if supported
        else "unavailable"
    )
    rejection_reasons = []
    if supported != g.NX * g.NY:
        rejection_reasons.append(f"support_{supported}_of_{g.NX * g.NY}")
    if invalid_frames:
        rejection_reasons.append(f"invalid_frames_{len(invalid_frames)}")
    if unavailable_indices:
        rejection_reasons.append(f"unavailable_views_{len(unavailable_indices)}")

    return {
        "algorithm_id": ALGORITHM_ID,
        "frame_count_input": input_count,
        "frame_count_valid": len(per_view),
        "heights": fused_heights,
        "per_view": per_view,
        "invalid_frames": invalid_frames,
        "measurement_state": measurement_state,
        "observed_volume_m3": observed,
        "total_volume_m3": observed if total_eligible else None,
        "total_selection": {
            "selected": total_eligible,
            "rejection_reasons": rejection_reasons,
        },
        "tin_support_union_cell_count": supported,
        "tin_support_union_fraction": supported / (g.NX * g.NY),
        "unavailable_view_indices": unavailable_indices,
        "selected_view_indices_by_cell": selected_view_indices,
        "trim_kappa": trim_kappa,
        "lower": lower,
        "trimmed_cell_count": trimmed_cell_count,
        "quality_definition": QUALITY_DEFINITION,
    }
