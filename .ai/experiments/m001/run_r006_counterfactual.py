"""Algebraic evaluator-only intervention; never exports a usable estimator."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'.ai/runs/m001-r006-counterfactual/results.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise RuntimeError('Counterfactual output already exists')
    protocol_path=HERE/'protocol_r006_counterfactual.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
    assert sha(protocol_path)==(HERE/'protocol_r006_counterfactual.sha256').read_text().split()[0]
    source=ROOT/protocol['source']
    checksum=sha(source)
    data=json.loads(source.read_text(encoding='utf-8'))
    rows=[]
    for r in data['records']:
        if r['method'] not in protocol['methods']:
            continue
        row={'scene_id':r['scene_id'],'method':r['method'],
             'total_eligible_before_and_after':r['total_selection']['selected'],
             'primary_diagnostic':r['scene_id'] in protocol['primary_diagnostic_scenes']}
        for domain in protocol['domains']:
            total=r[domain]['overall']
            transition=r[domain]['groups']['transition']
            planar=r[domain]['groups']['planar']
            residual=total['signed_error_m3']-transition['signed_error_m3']
            assert abs(residual-planar['signed_error_m3'])<1e-12
            volume=total['truth_volume_m3']
            relative=abs(residual)/volume if volume else None
            row[domain]={'volume_error_before_liters':total['signed_error_m3']*1000,
                'volume_error_after_liters':residual*1000,
                'absolute_error_before_percent':total['absolute_error_percent'],
                'absolute_error_after_percent':relative*100 if relative is not None else None,
                'unchanged_support_cells':total['cell_count'],
                'ideal_total_within5pct':relative<=.05 if relative is not None and r['total_selection']['selected'] else None}
        rows.append(row)
    assert len(rows)==18 and sha(source)==checksum
    result={'id':'R006-C','scope':'EVALUATOR-ONLY counterfactual; not measured estimator performance',
            'protocol_sha256':sha(protocol_path),'source_sha256':checksum,'rows':rows,
            'limitations':protocol['limitations']}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:
        if r['primary_diagnostic']:
            print(json.dumps(r,ensure_ascii=False))


if __name__=='__main__':
    main()
