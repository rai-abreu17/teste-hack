"""Development evaluation on archived scenes. Never a reserved-set validation."""
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
from experiments import truth
from r005_estimator import fuse_frames as baseline
from d001_estimator import fuse_frames as candidate
from run_r006 import stats

SOURCE = ROOT / '.ai/runs/m001-implementation/results'
OUT = ROOT / '.ai/runs/m001-d001/results'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise SystemExit('Refusing to overwrite D001 results')
    protocol_path = HERE / 'protocol_d001.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf-8'))
    assert sha(protocol_path) == (HERE/'protocol_d001.sha256').read_text().split()[0]
    for name, checksum in protocol['frozen_sources'].items():
        assert sha(ROOT/name) == checksum, name
    source = SOURCE/'comparisons.json'
    original = json.loads(source.read_text(encoding='utf-8'))
    assert [s['scene_id'] for s in original['scenes']] == protocol['scene_ids']
    hashes = {str(source.relative_to(ROOT)): sha(source)}
    records, details = [], []
    for entry in original['scenes']:
        sid = entry['scene_id']
        assert sid in protocol['scene_ids']
        reference = truth.cell_volumes(truth.Scene(**entry['scene_for_evaluator_only']))
        archived = {arm['arm_id']: arm for arm in entry['arms']}
        for acquisition in protocol['acquisitions']:
            paths = sorted((SOURCE/'frames'/sid).glob(f'{acquisition}-*.bin'))
            assert len(paths) == 3
            for path, view in zip(paths, archived[acquisition]['per_view']):
                assert sha(path) == view['sha256']
                hashes[str(path.relative_to(ROOT))] = sha(path)
            frames = [path.read_bytes() for path in paths]
            before = time.perf_counter()
            control = baseline(frames)
            control_ms = (time.perf_counter()-before)*1000
            assert control['heights'] == archived[acquisition]['heights']
            before = time.perf_counter()
            proposed = candidate(frames)
            candidate_ms = (time.perf_counter()-before)*1000
            common = [i for i in range(400) if control['heights'][i] is not None and proposed['heights'][i] is not None]
            for name, result, elapsed in [('baseline',control,control_ms),('surface_patches',proposed,candidate_ms)]:
                heights = result['heights']
                assert len(heights) == 400
                assert all(h is None or (math.isfinite(h) and h >= 0) for h in heights)
                own = [i for i,h in enumerate(heights) if h is not None]
                missing = [i for i,h in enumerate(heights) if h is None]
                eligible = result['total_selection']['selected']
                assert eligible == (len(own) == 400 and not result['invalid_frames'] and not result['unavailable_view_indices'])
                if name == 'surface_patches':
                    kinds = result['support_kind_by_cell']
                    assert len(kinds) == 400 and all(k in (None,'observed','model') for k in kinds)
                    assert all((h is None) == (k is None) for h,k in zip(heights,kinds))
                total = stats(heights,reference,range(400)) if eligible else None
                record = {'scene_id':sid,'acquisition':acquisition,'method':name,
                    'support_cells':len(own),'total_selection':result['total_selection'],
                    'model_support_cells':sum(k == 'model' for k in result.get('support_kind_by_cell',[])),
                    'model_based_total':eligible and any(k == 'model' for k in result.get('support_kind_by_cell',[])),
                    'whole_box':total,'company_5pct_total_only': total['absolute_error_percent'] <= 5 if total and total['absolute_error_percent'] is not None else None,
                    'own':stats(heights,reference,own),'common':stats(heights,reference,common),
                    'missing_truth_volume_m3':sum(reference[i] for i in missing),
                    'support_lost_vs_control':sum(control['heights'][i] is not None and heights[i] is None for i in range(400)),
                    'support_gained_vs_control':sum(control['heights'][i] is None and heights[i] is not None for i in range(400)),
                    'elapsed_ms_single_run':elapsed}
                records.append(record)
            details.append({'scene_id':sid,'acquisition':acquisition,'candidate':proposed})
    assert len(records) == 36 and len(hashes) == 55
    OUT.mkdir(parents=True)
    result = {'experiment_id':'D-001','scope':'SIMULATED development on previously inspected scenes; not holdout',
        'created_at_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':sha(protocol_path),
        'records':records,'latency_limit':None,'timing_limit':'single local run; descriptive, not realtime benchmark'}
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    (OUT/'details.json').write_text(json.dumps(details,indent=2,allow_nan=False),encoding='utf-8')
    rows = [{k:r[k] for k in ['scene_id','acquisition','method','support_cells','model_support_cells','model_based_total','company_5pct_total_only','support_lost_vs_control','support_gained_vs_control','elapsed_ms_single_run']} | {
        'total_error_percent':r['whole_box']['absolute_error_percent'] if r['whole_box'] else None,
        'common_spatial_error_percent':r['common']['spatial_error_percent'],
        'common_absolute_error_percent':r['common']['absolute_error_percent']} for r in records]
    with (OUT/'summary.csv').open('w',newline='',encoding='utf-8') as stream:
        writer = csv.DictWriter(stream,fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for path in [protocol_path,HERE/'protocol_d001.sha256',*(ROOT/n for n in protocol['frozen_sources']),*OUT.iterdir()]:
        hashes[str(path.relative_to(ROOT))] = sha(path)
    (OUT/'hash-manifest.json').write_text(json.dumps({'files':hashes},indent=2),encoding='utf-8')
    print(json.dumps(rows,indent=2))


if __name__ == '__main__':
    main()
