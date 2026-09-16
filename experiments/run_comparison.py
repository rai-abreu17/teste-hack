"""Reproduce E0/E1/E2/E3. Run from the project root: python -m experiments.run_comparison.

Only this evaluator knows scene parameters and analytical truth. All estimators
receive binary measurements plus the configuration frozen in protocol.json.
"""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import shutil

from server import geometry as g
from .estimators import estimate_tin, estimate_parametric
from .truth import Scene, analytical_volume, cell_volumes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/experiments'
PROTOCOL = json.loads((ROOT/'experiments/protocol.json').read_text())


def capture(scene, sequence=1):
    args = [scene.fill,scene.shape,scene.cx,scene.obstacle,scene.dropout,scene.range_m,
            sequence,0,0,scene.sensor_z]
    raw = subprocess.check_output([str(ROOT/'build/scene_dump'),*map(str,args)])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'frames').mkdir(exist_ok=True)
    digest = hashlib.sha256(raw).hexdigest()
    (OUT/'frames'/f'{digest}.bin').write_bytes(raw)
    return raw, digest


def statistics_of(values):
    values = [float(v) for v in values if v is not None]
    if not values:
        return {'count':0, 'signed_median_percent':None,'signed_mean_percent':None,
                'min_percent':None,'max_percent':None,'range_pp':None,'population_std_pp':None}
    return {'count':len(values), 'signed_median_percent':statistics.median(values),
            'signed_mean_percent':statistics.mean(values), 'min_percent':min(values),
            'max_percent':max(values), 'range_pp':max(values)-min(values),
            'population_std_pp':statistics.pstdev(values)}


def error_percent(value, reference):
    return None if value is None or reference <= 1e-14 else 100*(value-reference)/reference


def domain_result(heights, truth, mask):
    expected = sum(t for t,m in zip(truth,mask) if m)
    area = sum(mask)*g.CELL**2
    estimated = sum(h for h,m in zip(heights,mask) if m)*g.CELL**2 if any(mask) else None
    return {'area_m2':area,'reference_volume_m3':expected,'estimated_volume_m3':estimated,
            'error_percent':error_percent(estimated,expected)}


def variants(raw):
    result = {'baseline_8x8':estimate_tin(raw)}
    for roi in (6,4):
        result[f'roi_{roi}x{roi}'] = estimate_tin(raw,roi=roi)
    for angle in PROTOCOL['gradient_limits_deg']:
        result[f'gradient_{angle}deg'] = estimate_tin(raw,max_slope_deg=angle)
    return result


def evaluate(scene, label, include_models=True):
    raw, digest = capture(scene)
    truth = cell_volumes(scene)
    expected = analytical_volume(scene)
    if not math.isclose(sum(truth),expected,rel_tol=1e-10,abs_tol=1e-14):
        raise AssertionError('Reference clipping differs from independent solid formula')
    candidates = variants(raw)
    production = g.estimate(raw)
    base = candidates['baseline_8x8']
    if (base['heights'] != production['grid']['height_m'] or
            base['measurement_state'] != production['measurement_state']):
        raise AssertionError('Experimental baseline differs from production')
    common = [all(r['heights'][k] is not None for r in candidates.values()) for k in range(400)]
    for name,r in candidates.items():
        mask = [h is not None for h in r['heights']]
        pair = [a and b is not None for a,b in zip(mask,base['heights'])]
        r['own_domain'] = domain_result(r['heights'],truth,mask)
        r['common_all_filters_domain'] = domain_result(r['heights'],truth,common)
        r['pair_common_candidate'] = domain_result(r['heights'],truth,pair)
        r['pair_common_baseline'] = domain_result(base['heights'],truth,pair)
        r['reference_volume_retained_fraction'] = sum(v for v,m in zip(truth,mask) if m)/expected if expected else None
        r['total_error_percent'] = error_percent(r['total_volume_m3'],expected)
    models = {}
    if include_models:
        for prior in PROTOCOL['parametric_priors']:
            r = estimate_parametric(raw,prior,PROTOCOL['fit_bounds'],PROTOCOL['fit_gates'])
            r['model_error_percent'] = error_percent(r['model_volume_m3'],expected)
            r['candidate_error_percent_diagnostic_only'] = error_percent(r['candidate_model_volume_m3'],expected)
            models[prior] = r
    return {'label':label,'scene_for_evaluation_only':asdict(scene),'frame_sha256':digest,
            'reference_total_m3':expected, 'tin':candidates,'models':models}


def summarize(rows):
    out = {}
    for name in rows[0]['tin']:
        results = [r['tin'][name] for r in rows]
        states = [r['measurement_state'] for r in results]
        retained = [r['reference_volume_retained_fraction'] for r in results if r['reference_volume_retained_fraction'] is not None]
        out[name] = {'total_error':statistics_of([r['total_error_percent'] for r in results]),
                     'own_domain_error':statistics_of([r['own_domain']['error_percent'] for r in results]),
                     'common_all_filters_error':statistics_of([r['common_all_filters_domain']['error_percent'] for r in results]),
                     'pair_common_candidate_error':statistics_of([r['pair_common_candidate']['error_percent'] for r in results]),
                     'pair_common_baseline_error':statistics_of([r['pair_common_baseline']['error_percent'] for r in results]),
                     'valid_count':states.count('valid'),'partial_count':states.count('partial'),
                     'unavailable_count':states.count('unavailable'),
                     'state_changes':sum(a!=b for a,b in zip(states,states[1:])),
                     'coverage_min':min(r['coverage_fraction'] for r in results),
                     'coverage_max':max(r['coverage_fraction'] for r in results),
                     'reference_volume_retained_min':min(retained) if retained else None,
                     'reference_volume_retained_max':max(retained) if retained else None,
                     'gradient_rejected_triangles_sum':sum(r['gradient_rejected_triangles'] for r in results)}
    for prior in PROTOCOL['parametric_priors']:
        results = [r['models'][prior] for r in rows]
        states = [r['measurement_state'] for r in results]
        out['model_'+prior] = {'model_error':statistics_of([r['model_error_percent'] for r in results]),
                              'accepted_count':states.count('model_supported'),
                              'inconclusive_count':states.count('inconclusive'),
                              'state_changes':sum(a!=b for a,b in zip(states,states[1:]))}
    return out


def main():
    frozen = (ROOT/'experiments/protocol.sha256').read_text().split()[0]
    actual = hashlib.sha256((ROOT/'experiments/protocol.json').read_bytes()).hexdigest()
    if frozen != actual:
        raise SystemExit('Frozen protocol changed. Register and describe a separate experiment.')
    if not (ROOT/'build/scene_dump').exists():
        compiler = shutil.which('gcc') or shutil.which('clang')
        if compiler is None:
            raise SystemExit('Instale GCC ou Clang; para uma amostra pronta use experiments.analyze_frame.')
        (ROOT/'build').mkdir(exist_ok=True)
        subprocess.run([compiler,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tools/scene_dump.c'),
                        '-lm','-o',str(ROOT/'build/scene_dump')],check=True)
    train = []
    for i,x in enumerate(PROTOCOL['position_m']):
        train.append(evaluate(Scene(cx=x),f'position_{x:.3f}'))
        if i%5 == 0:
            print(f'E0-E3 sweep {i+1}/21',flush=True)
    held = []
    for fill in PROTOCOL['held_out_fill_percent']:
        for x in PROTOCOL['held_out_position_m']:
            held.append(evaluate(Scene(fill=fill,cx=x),f'held_{fill}_{x:.3f}'))
        print(f'Held-out fill={fill}: 20 positions',flush=True)
    controls = []
    for shape in (1,2,3,4):
        for x in (.13,.15,.17):
            controls.append(evaluate(Scene(shape=shape,cx=x),f'control_shape{shape}_{x}'))
    for name,scene in [('occlusion',Scene(obstacle=1)),('dropout20',Scene(dropout=20)),
                       ('dropout50',Scene(dropout=50)),('dropout100',Scene(dropout=100)),
                       ('range',Scene(range_m=.2)),('empty',Scene(fill=0))]:
        controls.append(evaluate(scene,name))
    height = []
    for shape in (0,4):
        for cm in range(28,51):
            s = Scene(shape=shape,sensor_z=cm/100)
            raw,digest = capture(s)
            r = g.estimate(raw)
            height.append({'shape':shape,'fill':75,'sensor_z_cm':cm,'frame_sha256':digest,
                           'coverage_fraction':r['coverage_fraction'],'measurement_state':r['measurement_state'],
                           'total_error_percent':error_percent(r['total_volume_m3'],analytical_volume(s)),
                           'observed_minus_whole_reference_percent_DIAGNOSTIC_ONLY':error_percent(r['observed_volume_m3'],analytical_volume(s))})
    result = {'source':'simulation','transport':'native-c-test','protocol_sha256':actual,
              'notes':['Finite optical zones, sensor noise and mixed returns are not simulated.',
                       'Observed-domain errors use exact truth integrated over reported grid cells.',
                       'Common masks are recomputed per scene and must be read with their retained area/volume.',
                       'Model totals are conditional extrapolations, not measured 100% coverage.',
                       'Held-out positions and heights use the same generating family; this is not physical or cross-family validation.'],
              'position_sweep':train,'held_out':held,'negative_controls':controls,'height_sweep':height,
              'position_summary':summarize(train),'held_out_summary':summarize(held),
              'held_out_by_fill':{str(f):summarize([r for r in held if r['scene_for_evaluation_only']['fill']==f])
                                  for f in PROTOCOL['held_out_fill_percent']}}
    (OUT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'position_summary':result['position_summary'],
                      'held_out_summary':result['held_out_summary']},ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
