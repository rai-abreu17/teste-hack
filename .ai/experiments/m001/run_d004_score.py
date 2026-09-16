"""Score the independently released D004 acquisition exactly once.

All 18 arm/scene reconstructions are completed without importing scene truth.
Only then does the evaluator import ``experiments.truth`` and compute error
metrics.  The script refuses to overwrite results and verifies the entire
pre-score hash chain before calling the frozen D003 estimator.
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


RUN = ROOT / ".ai/runs/m001-d004"
SOURCE = ROOT / ".ai/runs/m001-implementation/results"
OUT = RUN / "results"
PROTOCOL = HERE / "protocol_d004.json"
PROTOCOL_HASH = HERE / "protocol_d004.sha256"
PRE = RUN / "pre-acquisition-manifest.json"
CAPTURE_COMMANDS = RUN / "capture-commands.json"
ACQUISITION = RUN / "acquisition-manifest.json"
ACQUISITION_VALIDATION = RUN / "acquisition-validation.json"
RELEASE = RUN / "sol-pre-score-review.md"
VALIDATION = RUN / "validation.json"
REPORT = RUN / "REPORT.md"

EXPECTED = {
    "protocol": "ddfcf8013a9661b81679e9efce1544afd35f1bd1c3dc9785edc7135fbceff521",
    "protocol_hash_file": "d958ab2b9b5dffb8952816d236d113c11306795b7cb8a288c52deae07006e60f",
    "pre": "6ec13daa6f7049123e8649ba22c69cacb5ff6e4b8d7e2426f37cf456e152df5b",
    "capture_commands": "fbaa0308c9304dee9ed7ef68bb365e6f5580f6816b7669168e51ec643c72f6ca",
    "acquisition": "2413dc80b289242d391e51d2aaccac3c8eef048d5289df20c35738e2b30c4c8c",
    "acquisition_validation": "085df3312acdbec092528c708985f412570556ce9d5e4e4669f7e7d19162cfb6",
    "release": "a5bba458fe3502ce60cefd2fdd79aec3558c008bfb638c259067b4823392b99d",
    "estimator": "bdc14436bf06d54ca2d43bc90da40a937817a39d6f5779fd5627817663b0df83",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _assert_hash(path, expected):
    actual = sha256(path) if path.is_file() else None
    if actual != expected:
        raise RuntimeError(f"pre-score hash mismatch: {relative(path)}: {actual} != {expected}")


def verify_released_inputs():
    for path, key in (
        (PROTOCOL, "protocol"), (PROTOCOL_HASH, "protocol_hash_file"), (PRE, "pre"),
        (CAPTURE_COMMANDS, "capture_commands"), (ACQUISITION, "acquisition"),
        (ACQUISITION_VALIDATION, "acquisition_validation"), (RELEASE, "release"),
        (HERE / "d003_estimator.py", "estimator"),
    ):
        _assert_hash(path, EXPECTED[key])
    if PROTOCOL_HASH.read_text(encoding="utf-8").split()[0] != EXPECTED["protocol"]:
        raise RuntimeError("protocol hash file does not release the expected protocol")
    release_text = RELEASE.read_text(encoding="utf-8")
    if "LIBERAR a fase de pontua" not in release_text or "Esta libera" not in release_text:
        raise RuntimeError("independent pre-score release language not found")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    pre = json.loads(PRE.read_text(encoding="utf-8"))
    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    validation = json.loads(ACQUISITION_VALIDATION.read_text(encoding="utf-8"))
    if not validation["passed"] or validation["protocol_sha256"] != EXPECTED["protocol"]:
        raise RuntimeError("acquisition was not released from a passing validation")
    if acquisition["pre_acquisition_manifest_sha256"] != EXPECTED["pre"]:
        raise RuntimeError("acquisition does not descend from the released pre-manifest")
    if acquisition["capture_commands_sha256"] != EXPECTED["capture_commands"]:
        raise RuntimeError("capture command log changed")
    if acquisition["truth_or_estimator_used"] or acquisition["volume_results_present"]:
        raise RuntimeError("pre-score acquisition isolation contract failed")
    for name, checksum in protocol["frozen_sources"].items():
        _assert_hash(ROOT / name, checksum)
    for name, item in pre["selected_archived_frames"].items():
        _assert_hash(ROOT / name, item["sha256"])
    for name, item in pre["centre_identity_aliases"].items():
        _assert_hash(ROOT / name, item["sha256"])
        if (ROOT / name).read_bytes() != (ROOT / item["identical_to"]).read_bytes():
            raise RuntimeError(f"shared centre identity changed: {name}")
    for name, item in acquisition["candidate_frames"].items():
        _assert_hash(ROOT / name, item["sha256"])
    if len(pre["selected_archived_frames"]) != 45 or len(acquisition["candidate_frames"]) != 36:
        raise RuntimeError("released frame counts changed")
    return protocol, pre, acquisition


def arm_paths(scene_id, arm_id):
    center = SOURCE / "frames" / scene_id / "baseline_fixed1-1.bin"
    if arm_id == "control_k4_plus_shared_center":
        diagonals = [SOURCE / "frames" / scene_id / f"translated4_corners_level-{index}.bin"
                     for index in range(1, 5)]
    elif arm_id == "candidate_inset_diagonals_plus_shared_center":
        diagonals = [RUN / "frames" / scene_id / f"candidate_diagonals-{sequence}.bin"
                     for sequence in range(201, 205)]
    else:
        raise ValueError(f"unknown D004 arm: {arm_id}")
    return [*diagonals, center]


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
        x = (index % g.NX + 0.5) * g.CELL
        y = (index // g.NX + 0.5) * g.CELL
        if inside_convex(hull, (x, y)):
            inside.append(index)
    support_set = set(supported)
    inside_set = set(inside)
    excluded = {name: sum(frame["excluded"][name] for frame in result["decoded_frames"])
                for name in result["decoded_frames"][0]["excluded"]}
    xs, ys = [p[0] for p in hull], [p[1] for p in hull]
    return {
        "frame_count": result["frame_count_input"],
        "support_cells": len(supported),
        "support_fraction": result["support_fraction"],
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
        "outside_hull_cell_indices": sorted(set(range(g.NX * g.NY)) - inside_set),
        "inside_hull_unsupported_cell_count": len(inside_set - support_set),
        "inside_hull_unsupported_cell_indices": sorted(inside_set - support_set),
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
    """Complete every truth-free estimate before evaluator truth is imported."""
    reconstructed = []
    for scene in protocol["scenes"]:
        arms = []
        for arm in protocol["arms"]:
            paths = arm_paths(scene["id"], arm["id"])
            frames = [path.read_bytes() for path in paths]
            if frames[-1] != (SOURCE / "frames" / scene["id"] / "fixed3-1.bin").read_bytes():
                raise RuntimeError(f"shared centre alias changed: {scene['id']}")
            start = time.perf_counter()
            estimate = estimate_frames(frames)
            elapsed_ms = (time.perf_counter() - start) * 1000
            arms.append({
                "arm_id": arm["id"],
                "input_paths": [relative(path) for path in paths],
                "input_sha256": [sha256(path) for path in paths],
                "elapsed_ms_single_run": elapsed_ms,
                "truth_free": truth_free_summary(estimate),
                "estimate": estimate,
            })
        reconstructed.append({"scene": scene, "arms": arms})
    if len(reconstructed) != 9 or sum(len(item["arms"]) for item in reconstructed) != 18:
        raise RuntimeError("D004 reconstruction matrix is incomplete")
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
    """Evaluator-only phase. This is the first execution-time truth import."""
    from experiments import truth

    records, details, pairs = [], [], []
    for item in reconstructed:
        scene_data = item["scene"]
        scene = truth.Scene(**{key: value for key, value in scene_data.items() if key != "id"})
        reference = truth.cell_volumes(scene)
        analytical = truth.analytical_volume(scene)
        if not math.isclose(sum(reference), analytical, rel_tol=1e-10, abs_tol=1e-14):
            raise RuntimeError(f"truth integration mismatch: {scene_data['id']}")
        control, candidate = item["arms"]
        control_support = set(control["truth_free"]["supported_cell_indices"])
        candidate_support = set(candidate["truth_free"]["supported_cell_indices"])
        common = sorted(control_support & candidate_support)
        gained = sorted(candidate_support - control_support)
        lost = sorted(control_support - candidate_support)
        pair = {
            "scene_id": scene_data["id"],
            "control_support_cells": len(control_support),
            "candidate_support_cells": len(candidate_support),
            "candidate_minus_control_support_cells": len(candidate_support) - len(control_support),
            "gained_cell_count": len(gained),
            "gained_cell_indices": gained,
            "lost_cell_count": len(lost),
            "lost_cell_indices": lost,
            "common_cell_count": len(common),
        }
        for arm in item["arms"]:
            estimate = arm["estimate"]
            heights = estimate["heights"]
            supported = arm["truth_free"]["supported_cell_indices"]
            missing = sorted(set(range(g.NX * g.NY)) - set(supported))
            eligible = estimate["total_selection"]["selected"]
            whole = domain_stats(heights, reference, range(g.NX * g.NY)) if eligible else None
            own = domain_stats(heights, reference, supported)
            common_stats = domain_stats(heights, reference, common)
            record = {
                "scene_id": scene_data["id"],
                "arm_id": arm["arm_id"],
                "support_cells": len(supported),
                "total_selection": estimate["total_selection"],
                "whole_box": whole,
                "company_5pct_total_only": (
                    whole["absolute_error_percent"] <= 5.0
                    if whole and whole["absolute_error_percent"] is not None else None
                ),
                "own": own,
                "common": common_stats,
                "unsupported": {
                    "cell_count": len(missing),
                    "area_m2": len(missing) * g.CELL ** 2,
                    "truth_volume_m3": sum(reference[index] for index in missing),
                },
                "elapsed_ms_single_run": arm["elapsed_ms_single_run"],
                **{key: arm["truth_free"][key] for key in (
                    "accepted_return_hull", "outside_hull_cell_count",
                    "inside_hull_unsupported_cell_count", "rejected_returns",
                    "invalid_frame_count", "unavailable_view_count", "raw_point_count",
                    "merged_point_count", "merge_conflict_count", "delaunay_simplex_count",
                    "accepted_triangle_count", "long_or_degenerate_triangle_count",
                    "qhull_error", "coplanar_point_count")},
            }
            records.append(record)
            pair[f"{arm['arm_id']}_common"] = common_stats
        pairs.append(pair)
        details.append({
            "scene_id": scene_data["id"],
            "scene_for_evaluator_only": scene_data,
            "truth_total_m3": analytical,
            "paired": pair,
            "arms": item["arms"],
        })
    return records, details, pairs


def aggregate_gate(records):
    candidate = [record for record in records
                 if record["arm_id"] == "candidate_inset_diagonals_plus_shared_center"]
    total_count = sum(record["total_selection"]["selected"] for record in candidate)
    within_count = sum(record["company_5pct_total_only"] is True for record in candidate)
    partial_count = sum(not record["total_selection"]["selected"] for record in candidate)
    return {
        "candidate_total_eligible": total_count,
        "candidate_total_within_5pct": within_count,
        "candidate_partial": partial_count,
        "coverage_gate_9_of_9": total_count == 9,
        "company_gate_9_of_9_total_and_within_5pct": total_count == 9 and within_count == 9,
        "reserved_R007_used": False,
    }


def write_summary(records):
    rows = []
    for record in records:
        whole = record["whole_box"]
        rows.append({
            "scene": record["scene_id"],
            "arm": record["arm_id"],
            "support_cells": record["support_cells"],
            "total_eligible": record["total_selection"]["selected"],
            "total_absolute_error_percent": whole["absolute_error_percent"] if whole else None,
            "total_within_5pct": record["company_5pct_total_only"],
            "own_signed_error_percent": record["own"]["signed_error_percent"],
            "own_spatial_error_percent": record["own"]["spatial_error_percent"],
            "own_cancellation_ratio": record["own"]["cancellation_ratio"],
            "common_signed_error_percent": record["common"]["signed_error_percent"],
            "common_spatial_error_percent": record["common"]["spatial_error_percent"],
            "common_cancellation_ratio": record["common"]["cancellation_ratio"],
            "hull_min_x_m": record["accepted_return_hull"]["bounds_m"]["x"][0],
            "hull_max_x_m": record["accepted_return_hull"]["bounds_m"]["x"][1],
            "hull_min_y_m": record["accepted_return_hull"]["bounds_m"]["y"][0],
            "hull_max_y_m": record["accepted_return_hull"]["bounds_m"]["y"][1],
            "outside_hull_cells": record["outside_hull_cell_count"],
            "inside_hull_unsupported_cells": record["inside_hull_unsupported_cell_count"],
            "raw_points": record["raw_point_count"],
            "merged_points": record["merged_point_count"],
            "merge_conflicts": record["merge_conflict_count"],
            "elapsed_ms_single_run": record["elapsed_ms_single_run"],
        })
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(records, pairs, gate):
    by_key = {(record["scene_id"], record["arm_id"]): record for record in records}
    lines = [
        "# D004 — comparação pareada de cinco vistas", "",
        "**SIMULADO, desenvolvimento.** A pontuação foi executada somente após liberação independente. "
        "O estimador D003, as poses e os limiares permaneceram congelados.", "",
        "## Gates", "",
        f"- Candidato total elegível: **{gate['candidate_total_eligible']}/9**.",
        f"- Candidato total elegível e dentro de 5%: **{gate['candidate_total_within_5pct']}/9**.",
        f"- Candidato parcial: **{gate['candidate_partial']}/9**.",
        f"- Gate de cobertura 9/9: **{'PASSOU' if gate['coverage_gate_9_of_9'] else 'FALHOU'}**.",
        f"- Gate empresarial 9/9 total e <=5%: **{'PASSOU' if gate['company_gate_9_of_9_total_and_within_5pct'] else 'FALHOU'}**.",
        "", "Estimativas parciais nunca foram tratadas como volume total.", "",
        "## Resultado por cena", "",
        "| cena | suporte controle | suporte candidato | delta | ganhas | perdidas | erro total candidato | erro espacial próprio candidato |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair in pairs:
        candidate = by_key[(pair["scene_id"], "candidate_inset_diagonals_plus_shared_center")]
        total = ("—" if candidate["whole_box"] is None
                 else f"{candidate['whole_box']['absolute_error_percent']:.3f}%")
        spatial = candidate["own"]["spatial_error_percent"]
        lines.append(
            f"| {pair['scene_id']} | {pair['control_support_cells']} | "
            f"{pair['candidate_support_cells']} | {pair['candidate_minus_control_support_cells']:+d} | "
            f"{pair['gained_cell_count']} | {pair['lost_cell_count']} | {total} | {spatial:.3f}% |"
        )
    lines.extend([
        "", "## Integridade", "",
        f"- Protocolo: `{EXPECTED['protocol']}`.",
        f"- Estimador D003: `{EXPECTED['estimator']}`.",
        f"- Liberação pré-score: `{EXPECTED['release']}`.",
        "- Foram usados cinco quadros por braço e cena, com o mesmo binário central nos dois braços.",
        "- R007 não foi usado.", "",
        "Os resultados continuam limitados ao simulador ideal e às nove cenas de desenvolvimento já inspecionadas.", "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def build_hash_manifest(protocol, pre, acquisition):
    paths = {
        PROTOCOL, PROTOCOL_HASH, PRE, CAPTURE_COMMANDS, ACQUISITION,
        ACQUISITION_VALIDATION, RELEASE, HERE / "d003_estimator.py",
        HERE / "run_d004_score.py", HERE / "test_d004_score.py",
        ROOT / "server/geometry.py", ROOT / "experiments/truth.py",
        OUT / "results.json", OUT / "details.json", OUT / "summary.csv",
        VALIDATION, REPORT,
    }
    paths.update(ROOT / name for name in pre["selected_archived_frames"])
    paths.update(ROOT / name for name in pre["centre_identity_aliases"])
    paths.update(ROOT / name for name in acquisition["candidate_frames"])
    for name in protocol["frozen_sources"]:
        paths.add(ROOT / name)
    files = {relative(path): sha256(path) for path in sorted(paths, key=lambda p: relative(p))}
    (OUT / "hash-manifest.json").write_text(
        json.dumps({"experiment_id": "D-004", "files": files}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return files


def main():
    if OUT.exists() or VALIDATION.exists() or REPORT.exists():
        raise SystemExit("Refusing to overwrite D004 score artifacts")
    protocol, pre, acquisition = verify_released_inputs()

    # This complete phase has no evaluator-truth import or truth-derived values.
    reconstructed = reconstruct_all(protocol)

    records, details, pairs = evaluate_with_truth(reconstructed)
    gate = aggregate_gate(records)
    OUT.mkdir(parents=True)
    result = {
        "experiment_id": "D-004",
        "scope": "SIMULATED paired development comparison; not holdout or physical validation",
        "created_at_utc": utc_now(),
        "protocol_sha256": EXPECTED["protocol"],
        "pre_score_release_sha256": EXPECTED["release"],
        "estimator_sha256": EXPECTED["estimator"],
        "truth_free_reconstructions_completed_before_truth_evaluation": 18,
        "gate": gate,
        "paired": pairs,
        "records": records,
        "interpretation_limits": protocol["interpretation_limits"],
    }
    (OUT / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (OUT / "details.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    write_summary(records)
    checks = {
        "released_hash_chain_verified_before_estimation": True,
        "truth_free_reconstruction_count_18": len(records) == 18,
        "scene_pair_count_9": len(pairs) == 9,
        "same_center_path_per_pair": all(item["arms"][0]["input_paths"][-1]
                                         == item["arms"][1]["input_paths"][-1]
                                         for item in reconstructed),
        "five_frames_per_arm": all(arm["estimate"]["frame_count_input"] == 5
                                   for item in reconstructed for arm in item["arms"]),
        "no_invalid_frames": all(record["invalid_frame_count"] == 0 for record in records),
        "no_unavailable_views": all(record["unavailable_view_count"] == 0 for record in records),
        "partial_never_passes_company_gate": all(record["total_selection"]["selected"]
                                                  or record["company_5pct_total_only"] is None
                                                  for record in records),
        "candidate_gate_consistent": gate["company_gate_9_of_9_total_and_within_5pct"]
                                     == (gate["candidate_total_eligible"] == 9
                                         and gate["candidate_total_within_5pct"] == 9),
        "reserved_R007_unused": not gate["reserved_R007_used"],
    }
    validation = {
        "experiment_id": "D-004",
        "checked_at_utc": utc_now(),
        "passed": all(checks.values()),
        "checks": checks,
        "gate": gate,
        "protocol_sha256": EXPECTED["protocol"],
        "pre_score_release_sha256": EXPECTED["release"],
        "estimator_sha256": EXPECTED["estimator"],
        "result_hashes": {
            "results.json": sha256(OUT / "results.json"),
            "details.json": sha256(OUT / "details.json"),
            "summary.csv": sha256(OUT / "summary.csv"),
        },
    }
    VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(records, pairs, gate)
    build_hash_manifest(protocol, pre, acquisition)
    if not validation["passed"]:
        raise RuntimeError("D004 scoring validation failed")
    print(json.dumps({"gate": gate, "pairs": pairs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
