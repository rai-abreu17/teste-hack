"""Shift only the estimator's empty-box reference; measurements stay unchanged.

The optional plot requires matplotlib. JSON/table generation uses the standard
library. The v1 fixture reproduces the user's original 48 m2 sensitivity case.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from geometry import estimate


def sweep():
    fixture=ROOT/'tests/fixtures/v1'
    spec=importlib.util.spec_from_file_location('geometry_v1',fixture/'geometry_v1.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    previous_base=old.base
    raw_old=(fixture/'pyramid_6m3.bin').read_bytes()
    raw_new=(ROOT/'samples/04-entrada-75.bin').read_bytes()
    rows=[]
    for offset_mm in range(-30,51):
        shift=offset_mm/1000
        # This changes only b(x,y) in the estimator, never the stored raw frame.
        with patch.object(old,'base',lambda x,y:previous_base(x,y)+shift):
            v1=old.estimate(raw_old)
        v2=estimate(raw_new,reference_offset_m=shift)
        for profile,reference,result in [('v1-48m2',6.0,v1),('vl53-maquette-0.09m2',.0005625,v2)]:
            value=result['observed_volume_m3']
            rows.append({'profile':profile,'reference_offset_mm':offset_mm,'analytical_volume_m3':reference,
                         'observed_volume_m3':value,'total_volume_m3':result['total_volume_m3'],
                         'difference_m3':None if value is None else value-reference,
                         'state':result['measurement_state'],'coverage_fraction':result['coverage_fraction']})
    return {'note':'Only the estimator reference is shifted. Curves include diagnostic observed values even when measurement is unavailable; they are not accepted totals.',
            'sha256_raw':{'v1':hashlib.sha256(raw_old).hexdigest(),'v3':hashlib.sha256(raw_new).hexdigest()},'results':rows}


def plot(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for ax,profile,title in zip(axes,('v1-48m2','vl53-maquette-0.09m2'),('Cena anterior · 48 m² · referência 6 m³','Maquete 8×8 · 0,09 m² · referência 0,0005625 m³')):
        values=[r for r in data['results'] if r['profile']==profile]
        ax.plot([r['reference_offset_mm'] for r in values],[r['observed_volume_m3'] for r in values],color='#187e9b',label='Observado (diagnóstico)')
        bad=[r for r in values if r['state']=='unavailable' and r['observed_volume_m3'] is not None]
        ax.scatter([r['reference_offset_mm'] for r in bad],[r['observed_volume_m3'] for r in bad],s=10,color='#b94b43',label='Medição indisponível',zorder=3)
        ax.axhline(values[0]['analytical_volume_m3'],color='#488558',linestyle='--',label='Volume analítico')
        ax.axvline(0,color='#95a7ae',linewidth=.8)
        ax.set(title=title,xlabel='Deslocamento da referência do estimador (mm)',ylabel='Volume observado (m³)')
        ax.grid(alpha=.18);ax.legend(fontsize=8);ax.ticklabel_format(axis='y',style='plain',useOffset=False)
    fig.suptitle('Referência deslocada; mesmos quadros brutos em toda a curva',fontsize=13)
    fig.savefig(ROOT/'docs/reference-sensitivity.png',dpi=170);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plot',action='store_true');args=parser.parse_args()
    data=sweep();(ROOT/'build/reference-sensitivity.json').write_text(json.dumps(data,indent=2)+'\n')
    if args.plot:plot(data)
    for r in data['results']:
        if r['reference_offset_mm'] in (-20,-10,0,10,50):print(json.dumps(r))


if __name__=='__main__':main()
