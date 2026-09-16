"""Diagnostic attribution only. Reuse archived frames; never overwrite P001-P004."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
from experiments.truth import Scene, cell_volumes
from run_p003 import triangle_quality_by_cell

SOURCE = ROOT / '.ai/runs/m001-implementation/results'
OUT = ROOT / '.ai/runs/m001-evaluation/results'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fuse(views, qualities, kappa=None, lower=False):
    heights = []
    for cell in range(400):
        available = [(v['heights'][cell], qualities[i][cell])
                     for i, v in enumerate(views) if v['heights'][cell] is not None]
        assert all(q is not None for _, q in available)
        if kappa is not None and available:
            limit = kappa * min(q for _, q in available)
            available = [(h, q) for h, q in available if q <= limit]
        vals = sorted(h for h, _ in available)
        heights.append((vals[(len(vals)-1)//2] if lower else statistics.median(vals)) if vals else None)
    return heights


def errors(heights, reference, mask):
    selected = [i for i, yes in enumerate(mask) if yes]
    assert selected and all(heights[i] is not None for i in selected)
    truth_volume = sum(reference[i] for i in selected)
    residuals = [heights[i] * .015**2 - reference[i] for i in selected]
    signed = sum(residuals)
    spatial = sum(abs(v) for v in residuals)
    return {'signed_percent': signed / truth_volume * 100 if truth_volume else None,
            'absolute_percent': abs(signed) / truth_volume * 100 if truth_volume else None,
            'integrated_absolute_cell_error_percent': spatial / truth_volume * 100 if truth_volume else None,
            'volume_error_m3': signed,
            'mean_absolute_height_error_mm': spatial / (len(selected)*.015**2)*1000}


def main():
    historical = [SOURCE / 'comparisons.json'] + [ROOT / f'.ai/runs/m001-p00{n}/results/comparisons.json' for n in (2, 3, 4)]
    before = {str(p.relative_to(ROOT)): digest(p) for p in historical}
    p001, p002, p003, p004 = [json.loads(p.read_text(encoding='utf-8')) for p in historical]
    p004rows = {r['scene_id']: r for r in p004['rows']}
    p003rows = {r['scene_id']: r for r in p003['rows'] if r['variant'] != 'median'}
    rows, frame_hashes = [], {}
    for scene in p001['scenes']:
        sid = scene['scene_id']
        arms = {a['arm_id']: a for a in scene['arms']}
        aimed = arms['translated3_aimed']
        mask = [all(a['heights'][i] is not None for a in arms.values()) for i in range(400)]
        reference = cell_volumes(Scene(**scene['scene_for_evaluator_only']))
        frames = []
        for i, v in enumerate(aimed['per_view']):
            path = SOURCE / 'frames' / sid / f'translated3_aimed-{i+1}.bin'
            assert digest(path) == v['sha256']
            frame_hashes[str(path.relative_to(ROOT))] = digest(path)
            frames.append(path.read_bytes())
        qualities = [triangle_quality_by_cell(frame) for frame in frames]
        variants = {
            'median_no_trim': fuse(aimed['per_view'], qualities),
            'lower_no_trim': fuse(aimed['per_view'], qualities, lower=True),
            'median_trim2': fuse(aimed['per_view'], qualities, kappa=2),
            'lower_trim2': fuse(aimed['per_view'], qualities, kappa=2, lower=True)}
        assert variants['median_no_trim'] == aimed['heights']
        values = {name: errors(h, reference, mask) for name, h in variants.items()}
        assert math.isclose(values['lower_trim2']['signed_percent'], p004rows[sid]['signed_error_percent'], abs_tol=1e-9)
        fixed = errors(arms['fixed3']['heights'], reference, mask)
        diagnostics = {'scene_id': sid,
            'common_cells': sum(mask), 'common_area_fraction': sum(mask)/400,
            'common_truth_volume_fraction': sum(v for v, yes in zip(reference, mask) if yes)/sum(reference),
            'trimmed_cells': p004rows[sid]['trimmed_cell_count'],
            'lower_only_changed_cells': sum(a != b for a, b in zip(variants['median_no_trim'], variants['lower_no_trim'])),
            'trim_only_changed_cells': sum(a != b for a, b in zip(variants['median_no_trim'], variants['median_trim2'])),
            'fixed3': fixed, 'same_acquisition_variants': values,
            'p003_gain_vs_same_acquisition_median_pp': values['median_no_trim']['absolute_percent'] - p003rows[sid]['absolute_error_percent'],
            'p004_gain_vs_same_acquisition_median_pp': values['median_no_trim']['absolute_percent'] - values['lower_trim2']['absolute_percent'],
            'p004_signed_effect_of_lower_alone_pp': values['lower_no_trim']['signed_percent']-values['median_no_trim']['signed_percent'],
            'p004_signed_effect_of_trim_after_lower_pp': values['lower_trim2']['signed_percent']-values['lower_no_trim']['signed_percent']}
        rows.append(diagnostics)
    assert all(digest(p) == before[str(p.relative_to(ROOT))] for p in historical)
    source_paths = [Path(__file__), HERE / 'run_p003.py',
                    ROOT / 'server/geometry.py', ROOT / 'experiments/truth.py']
    output = {'purpose': 'Post-hoc diagnostic audit, not new candidate selection or holdout validation',
              'historical_hashes_unchanged': before, 'frame_hashes': frame_hashes,
              'audit_source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in source_paths},
              'rows': rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'attribution.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print('scene | common cells | truth share % | trimmed | lower changed | trim changed | P003 gain vs aimed median | P004 gain vs aimed median')
    for r in rows:
        print(f"{r['scene_id']} | {r['common_cells']} | {100*r['common_truth_volume_fraction']:.2f} | {r['trimmed_cells']} | {r['lower_only_changed_cells']} | {r['trim_only_changed_cells']} | {r['p003_gain_vs_same_acquisition_median_pp']:.6f} | {r['p004_gain_vs_same_acquisition_median_pp']:.6f}")
    print('Historical files and 27 frame hashes verified; no new captures.')


if __name__ == '__main__':
    main()
