"""Execute frozen P-001. Truth and oracle exist only in this evaluator."""

import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / ".ai" / "runs" / "m001-implementation"
OUT = RUN / "results"
FRAMES = OUT / "frames"
BIN = RUN / "bin" / "scene_dump_m001.exe"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from experiments import truth
from experiments.truth import Scene, analytical_volume, cell_volumes
from server import geometry as g
from m001_estimator import fuse_frames


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def error_metrics(value, reference):
    if value is None:
        return {"signed_error_m3": None, "absolute_error_m3": None,
                "signed_error_percent": None, "absolute_error_percent": None}
    signed = value - reference
    relative = None if abs(reference) <= 1e-14 else 100.0 * signed / reference
    return {"signed_error_m3": signed, "absolute_error_m3": abs(signed),
            "signed_error_percent": relative,
            "absolute_error_percent": None if relative is None else abs(relative)}


def domain_metrics(heights, reference_cells, mask):
    cells = sum(mask)
    reference = sum(v for v, selected in zip(reference_cells, mask) if selected)
    estimated = (sum(h for h, selected in zip(heights, mask) if selected) * g.CELL**2
                 if cells else None)
    result = {"cell_count": cells, "area_m2": cells * g.CELL**2,
              "reference_volume_m3": reference, "estimated_volume_m3": estimated}
    result.update(error_metrics(estimated, reference))
    return result


def barycentric_height(triangle, x, y):
    a, b, c = triangle
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        return None
    wa = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
    wb = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
    wc = 1.0 - wa - wb
    if min(wa, wb, wc) < -1e-9:
        return None
    return wa * a[2] + wb * b[2] + wc * c[2]


def true_center_targets(scene):
    """Evaluation-only point truth; estimator never receives these targets."""
    faces = truth.faces(scene)
    targets = []
    for iy in range(g.NY):
        y = (iy + .5) * g.CELL
        for ix in range(g.NX):
            x = (ix + .5) * g.CELL
            candidates = [barycentric_height(face, x, y) for face in faces]
            candidates = [height for height in candidates if height is not None]
            material_height = max(candidates) if candidates else 0.0
            targets.append((x, y, g.base(x, y) + material_height))
    return targets


def run_command(command, command_records, *, input_text=None, kind, output_path=None):
    completed = subprocess.run(command, input=input_text, text=input_text is not None,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    record = {"kind": kind, "command": [str(v) for v in command],
              "exit_code": completed.returncode,
              "stderr": completed.stderr if isinstance(completed.stderr, str)
              else completed.stderr.decode("utf-8", errors="replace")}
    stdout = completed.stdout
    if isinstance(stdout, bytes):
        record.update({"stdout_bytes": len(stdout), "stdout_sha256": hashlib.sha256(stdout).hexdigest()})
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(stdout)
            record["stdout_path"] = str(output_path.relative_to(ROOT))
    else:
        record["stdout"] = stdout
    command_records.append(record)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {command}")
    return stdout


def capture(scene_data, pose, arm_id, scene_id, index, command_records):
    output_path = FRAMES / scene_id / f"{arm_id}-{index + 1}.bin"
    command = [str(BIN), str(scene_data["fill"]), str(scene_data["shape"]),
               str(scene_data["cx"]), str(scene_data["obstacle"]),
               str(scene_data["dropout"]), "4.0", str(pose["sequence"]),
               str(pose["yaw_deg"]), str(pose["tilt_deg"]), str(pose["origin"][2]),
               str(pose["origin"][0]), str(pose["origin"][1])]
    return run_command(command, command_records, kind="capture", output_path=output_path)


def oracle_mask(scene_data, scene, origin, command_records):
    targets = true_center_targets(scene)
    input_text = "".join(f"{x:.9f} {y:.9f} {z:.9f}\n" for x, y, z in targets)
    command = [str(BIN), "--oracle", str(scene_data["fill"]), str(scene_data["shape"]),
               str(scene_data["cx"]), str(scene_data["obstacle"]), str(origin[2]),
               str(origin[0]), str(origin[1])]
    output = run_command(command, command_records, input_text=input_text, kind="oracle")
    values = output.splitlines()
    if len(values) != g.NX * g.NY or any(value not in ("0", "1") for value in values):
        raise RuntimeError(f"oracle returned {len(values)} malformed cells")
    return [value == "1" for value in values]


def evaluate_scene(scene_data, protocol, command_records):
    scene = Scene(fill=scene_data["fill"], shape=scene_data["shape"], cx=scene_data["cx"],
                  obstacle=scene_data["obstacle"], dropout=scene_data["dropout"],
                  range_m=4.0, sensor_z=.40)
    reference_cells = cell_volumes(scene)
    reference_total = analytical_volume(scene)
    if not math.isclose(sum(reference_cells), reference_total, rel_tol=1e-10, abs_tol=1e-14):
        raise AssertionError("exact cell truth differs from analytical total")

    oracle_cache = {}
    arms = []
    for arm in protocol["arms"]:
        frames = [capture(scene_data, pose, arm["id"], scene_data["id"], index, command_records)
                  for index, pose in enumerate(arm["captures"])]
        # The estimator accepts only reference_offset_m; descriptive protocol keys stay outside it.
        fused = fuse_frames(frames, {"reference_offset_m": protocol["fusion"]["reference_offset_m"]})
        origin_masks = []
        per_origin = []
        for pose in arm["captures"]:
            origin = tuple(pose["origin"])
            if origin not in oracle_cache:
                oracle_cache[origin] = oracle_mask(scene_data, scene, origin, command_records)
            mask = oracle_cache[origin]
            origin_masks.append(mask)
            per_origin.append({"origin_m": list(origin), "visible_cell_count": sum(mask)})
        oracle_union = [any(mask[k] for mask in origin_masks) for k in range(g.NX * g.NY)]
        fused["oracle_intrinsic_visibility"] = {
            "definition": "line of sight to true cell-center surface; ignores FoV and orientation",
            "per_capture_origin": per_origin,
            "union_cell_count": sum(oracle_union),
            "union_fraction": sum(oracle_union) / (g.NX * g.NY),
        }
        fused["arm_id"] = arm["id"]
        fused["budget_group"] = arm["budget_group"]
        fused["ray_budget"] = 64 * len(arm["captures"])
        arms.append(fused)

    common_all = [all(arm["heights"][k] is not None for arm in arms)
                  for k in range(g.NX * g.NY)]
    group_masks = {}
    for group in sorted({arm["budget_group"] for arm in arms}):
        members = [arm for arm in arms if arm["budget_group"] == group]
        group_masks[group] = [all(arm["heights"][k] is not None for arm in members)
                              for k in range(g.NX * g.NY)]

    for arm in arms:
        own_mask = [height is not None for height in arm["heights"]]
        arm["evaluation"] = {
            "own_domain": domain_metrics(arm["heights"], reference_cells, own_mask),
            "common_all_arms_domain": domain_metrics(arm["heights"], reference_cells, common_all),
            "common_budget_group_domain": domain_metrics(
                arm["heights"], reference_cells, group_masks[arm["budget_group"]]),
            "total": {"reference_volume_m3": reference_total,
                      "estimated_volume_m3": arm["total_volume_m3"],
                      **error_metrics(arm["total_volume_m3"], reference_total)},
        }
    return {"scene_id": scene_data["id"], "scene_for_evaluator_only": asdict(scene),
            "reference_total_m3": reference_total, "reference_cell_sum_m3": sum(reference_cells),
            "common_all_arms_cell_count": sum(common_all),
            "common_budget_group_cell_counts": {key: sum(mask) for key, mask in group_masks.items()},
            "arms": arms}


def median(values):
    values = [value for value in values if value is not None]
    return statistics.median(values) if values else None


def aggregate(scenes, protocol):
    rows = []
    for arm_spec in protocol["arms"]:
        items = [next(arm for arm in scene["arms"] if arm["arm_id"] == arm_spec["id"])
                 for scene in scenes]
        rows.append({
            "arm_id": arm_spec["id"], "budget_group": arm_spec["budget_group"],
            "ray_budget": 64 * len(arm_spec["captures"]),
            "total_selected_count": sum(item["total_selection"]["selected"] for item in items),
            "total_rejected_count": sum(not item["total_selection"]["selected"] for item in items),
            "median_tin_support_fraction": median([item["tin_support_union_fraction"] for item in items]),
            "median_effective_point_bin_fraction": median([item["effective_point_bin_union_fraction"] for item in items]),
            "median_oracle_intrinsic_visibility_fraction": median(
                [item["oracle_intrinsic_visibility"]["union_fraction"] for item in items]),
            "median_own_domain_signed_error_percent": median(
                [item["evaluation"]["own_domain"]["signed_error_percent"] for item in items]),
            "median_common_group_signed_error_percent": median(
                [item["evaluation"]["common_budget_group_domain"]["signed_error_percent"] for item in items]),
            "median_common_all_signed_error_percent": median(
                [item["evaluation"]["common_all_arms_domain"]["signed_error_percent"] for item in items]),
            "median_max_view_disagreement_mm": median([
                None if item["view_disagreement"]["max_height_range_m"] is None else
                1000 * item["view_disagreement"]["max_height_range_m"] for item in items]),
            "excluded_aggregate": {name: sum(item["excluded_aggregate"][name] for item in items)
                                   for name in items[0]["excluded_aggregate"]},
        })
    return rows


def csv_rows(scenes):
    rows = []
    for scene in scenes:
        for arm in scene["arms"]:
            row = {
                "scene_id": scene["scene_id"], "arm_id": arm["arm_id"],
                "budget_group": arm["budget_group"], "captures": arm["frame_count_input"],
                "ray_budget": arm["ray_budget"], "valid_frames": arm["frame_count_valid"],
                "invalid_frames": len(arm["invalid_frames"]),
                "effective_point_bins": arm["effective_point_bin_union_count"],
                "tin_support_cells": arm["tin_support_union_cell_count"],
                "oracle_visible_cells": arm["oracle_intrinsic_visibility"]["union_cell_count"],
                "own_domain_cells": arm["evaluation"]["own_domain"]["cell_count"],
                "own_signed_error_m3": arm["evaluation"]["own_domain"]["signed_error_m3"],
                "own_absolute_error_m3": arm["evaluation"]["own_domain"]["absolute_error_m3"],
                "own_signed_error_percent": arm["evaluation"]["own_domain"]["signed_error_percent"],
                "own_absolute_error_percent": arm["evaluation"]["own_domain"]["absolute_error_percent"],
                "common_group_cells": arm["evaluation"]["common_budget_group_domain"]["cell_count"],
                "common_group_signed_error_percent": arm["evaluation"]["common_budget_group_domain"]["signed_error_percent"],
                "common_all_cells": arm["evaluation"]["common_all_arms_domain"]["cell_count"],
                "common_all_signed_error_percent": arm["evaluation"]["common_all_arms_domain"]["signed_error_percent"],
                "total_selected": arm["total_selection"]["selected"],
                "total_estimated_m3": arm["total_volume_m3"],
                "total_reference_m3": scene["reference_total_m3"],
                "total_signed_error_percent": arm["evaluation"]["total"]["signed_error_percent"],
                "max_view_disagreement_mm": None if arm["view_disagreement"]["max_height_range_m"] is None
                else 1000 * arm["view_disagreement"]["max_height_range_m"],
                "reject_no_return": arm["excluded_aggregate"]["no_return"],
                "reject_out_of_range": arm["excluded_aggregate"]["out_of_range"],
                "reject_beam": arm["excluded_aggregate"]["beam"],
                "reject_wall_or_outside": arm["excluded_aggregate"]["wall_or_outside"],
                "reject_below_reference": arm["excluded_aggregate"]["below_reference"],
            }
            rows.append(row)
    return rows


def write_table(summary):
    lines = ["# P-001 — resumo por braço", "",
             "Métricas são medianas das nove cenas; `total ok` mostra seleções/9, sem ocultar parciais.", "",
             "| braço | grupo | raios | total ok | bins efetivos | suporte TIN | visibilidade oráculo | erro próprio % | erro comum grupo % |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary:
        percent = lambda value: "—" if value is None else f"{100 * value:.1f}%"
        number = lambda value: "—" if value is None else f"{value:+.2f}"
        lines.append(f"| {row['arm_id']} | {row['budget_group']} | {row['ray_budget']} | "
                     f"{row['total_selected_count']}/9 | {percent(row['median_effective_point_bin_fraction'])} | "
                     f"{percent(row['median_tin_support_fraction'])} | "
                     f"{percent(row['median_oracle_intrinsic_visibility_fraction'])} | "
                     f"{number(row['median_own_domain_signed_error_percent'])} | "
                     f"{number(row['median_common_group_signed_error_percent'])} |")
    lines.extend(["", "`bins efetivos` conta células que contêm pelo menos um retorno utilizável. `suporte TIN` é a união dos suportes interpolados locais por captura. `visibilidade oráculo` testa linha intrínseca e ignora FoV/orientação; não entra no estimador.", ""])
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_svg(summary):
    width, height = 1160, 560
    left, top, chart_h = 95, 70, 360
    colors = {"bins": "#276FBF", "tin": "#F28E2B", "oracle": "#59A14F"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#fbfaf7"/>',
             '<text x="40" y="36" font-family="sans-serif" font-size="24" font-weight="700">P-001: amostragem, suporte TIN e visibilidade geométrica</text>']
    for tick in range(0, 101, 20):
        y = top + chart_h * (1 - tick / 100)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="1125" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="50" y="{y + 5:.1f}" font-family="sans-serif" font-size="13">{tick}%</text>')
    group_w = 1010 / len(summary)
    bar_w = 24
    for index, row in enumerate(summary):
        center = left + group_w * (index + .5)
        values = [("bins", row["median_effective_point_bin_fraction"]),
                  ("tin", row["median_tin_support_fraction"]),
                  ("oracle", row["median_oracle_intrinsic_visibility_fraction"])]
        for offset, (name, value) in enumerate(values):
            bar_h = chart_h * value
            x = center + (offset - 1) * (bar_w + 3) - bar_w / 2
            y = top + chart_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{colors[name]}"/>')
        label = row["arm_id"].replace("_", " ")
        parts.append(f'<text transform="translate({center - 34:.1f},452) rotate(35)" font-family="sans-serif" font-size="12">{label}</text>')
    for i, (name, label) in enumerate((("bins", "bins com retornos"), ("tin", "suporte TIN"), ("oracle", "visibilidade oráculo"))):
        x = 600 + i * 175
        parts.append(f'<rect x="{x}" y="20" width="14" height="14" fill="{colors[name]}"/>')
        parts.append(f'<text x="{x + 20}" y="32" font-family="sans-serif" font-size="13">{label}</text>')
    parts.append('<text x="40" y="540" font-family="sans-serif" font-size="12" fill="#555">Medianas de 9 cenas. Suporte TIN é interpolado; visibilidade intrínseca ignora FoV e não é fornecida ao estimador.</text>')
    parts.append('</svg>')
    (OUT / "support-visibility.svg").write_text("\n".join(parts), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    protocol_path = HERE / "protocol.json"
    frozen = (HERE / "protocol.sha256").read_text(encoding="utf-8").split()[0]
    actual = sha256(protocol_path)
    if frozen != actual:
        raise SystemExit("frozen P-001 protocol hash mismatch")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["comparison_count"] != len(protocol["scenes"]) * len(protocol["arms"]):
        raise SystemExit("comparison count does not match frozen matrix")

    started = utc_now()
    command_records = []
    scenes = []
    for scene_data in protocol["scenes"]:
        scenes.append(evaluate_scene(scene_data, protocol, command_records))
        print(f"P-001 {len(scenes)}/{len(protocol['scenes'])}: {scene_data['id']}", flush=True)
    summary = aggregate(scenes, protocol)
    result = {
        "experiment_id": "P-001", "started_at_utc": started, "finished_at_utc": utc_now(),
        "protocol_sha256": actual, "comparison_count": sum(len(scene["arms"]) for scene in scenes),
        "scene_count": len(scenes), "arm_count": len(protocol["arms"]),
        "scope": "ideal geometric simulator only; no optical noise, physical hardware, pose error, or recalibration",
        "interpretation_limits": [
            "Effective point bins are a sampling metric, not physical area coverage.",
            "TIN support is local per-view interpolation and is not optical visibility or a global cross-view TIN.",
            "Oracle visibility is evaluator-only intrinsic line of sight, ignores FoV/orientation, and never enters fusion.",
            "Comparisons of viewpoint effects are made within equal-budget K3 and K4 groups; K1 is a reference only.",
            "This ideal exact-pose experiment does not test empty-box recalibration, mechanics, backlash, or registration error."
        ],
        "summary_by_arm": summary, "scenes": scenes,
    }
    (OUT / "comparisons.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = csv_rows(scenes)
    with (OUT / "comparisons.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "capture-commands.json").write_text(json.dumps(command_records, ensure_ascii=False, indent=2), encoding="utf-8")
    write_table(summary)
    write_svg(summary)

    tracked = [HERE / "protocol.json", HERE / "protocol.sha256", HERE / "scene_dump_m001.c",
               HERE / "m001_estimator.py", HERE / "run_p001.py", HERE / "test_m001.py",
               ROOT / ".ai/runs/m001/implementation-task.md", ROOT / "wokwi/boxflow-lidar.chip.c",
               ROOT / "server/geometry.py", ROOT / "experiments/truth.py",
               OUT / "comparisons.json", OUT / "comparisons.csv", OUT / "summary.md",
               OUT / "support-visibility.svg", OUT / "capture-commands.json"]
    manifest = {"generated_at_utc": utc_now(), "protocol_sha256": actual,
                "files": {str(path.relative_to(ROOT)): sha256(path) for path in tracked}}
    (OUT / "hash-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"comparison_count": result["comparison_count"],
                      "results": str((OUT / 'comparisons.json').relative_to(ROOT)),
                      "summary": summary}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
