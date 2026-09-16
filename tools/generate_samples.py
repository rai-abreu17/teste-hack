"""Build and execute the same C geometry used by the custom chip."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from geometry import estimate

# Independent analytic solid volumes, metres throughout.
SCENES=[
 ('vazio',0,0,.15,0,0,4,0),
 ('entrada-25',25,0,.15,0,0,4,.15*.15*.025/3),
 ('entrada-50',50,0,.15,0,0,4,.15*.15*.050/3),
 ('entrada-75',75,0,.15,0,0,4,.15*.15*.075/3),
 ('entrada-100',100,0,.15,0,0,4,.15*.15*.100/3),
 ('redistribuicao',75,0,.20,0,0,4,.15*.15*.075/3),
 ('duas-pilhas',75,1,.15,0,0,4,.10*.10*(.075+.0525)/3),
 ('oclusao',75,0,.15,1,0,4,.15*.15*.075/3),
 ('sem-retorno',75,0,.15,0,100,4,.15*.15*.075/3),
 ('fora-alcance',75,0,.15,0,0,.2,.15*.15*.075/3),
 ('retirada-50',50,0,.15,0,0,4,.15*.15*.050/3),
 ('retirada-25',25,0,.15,0,0,4,.15*.15*.025/3),
 ('retirada-vazio',0,0,.15,0,0,4,0),
 ('prisma',75,2,.15,0,0,4,.15*.15*.075),
 ('rampa',75,3,.15,0,0,4,.15*.15*.075/2),
 ('camada',75,4,.15,0,0,4,.30*.30*.075),
 ('principal',75,0,.15,0,0,4,.15*.15*.075/3),
]


def main():
    cc=shutil.which('gcc') or shutil.which('clang')
    if not cc:raise SystemExit('Instale GCC ou Clang para regenerar. As amostras prontas já estão em samples/.')
    (ROOT/'build').mkdir(exist_ok=True);(ROOT/'samples').mkdir(exist_ok=True)
    subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tools'/'scene_dump.c'),'-lm','-o',str(ROOT/'build'/'scene_dump')],check=True)
    legacy=ROOT/'samples/16-principal.bin'
    if legacy.exists():legacy.unlink()
    rows=[]
    for seq,(name,fill,shape,cx,obstacle,dropout,range_m,expected) in enumerate(SCENES,1):
        raw=subprocess.check_output([str(ROOT/'build'/'scene_dump'),*[str(v) for v in (fill,shape,cx,obstacle,dropout,range_m,seq)]])
        path=ROOT/'samples'/f'{seq:02d}-{name}.bin';path.write_bytes(raw);r=estimate(raw)
        observed=r['observed_volume_m3'];total=r['total_volume_m3']
        rows.append({'file':path.name,'name':name,'sequence':seq,'analytical_total_m3':expected,
                     'observed_m3':observed,'reconstructed_total_m3':total,
                     'difference_observed_minus_reference_m3':None if observed is None else observed-expected,
                     'total_relative_error_percent':None if total is None or expected==0 else 100*(total-expected)/expected,
                     'meets_5_percent_development_goal':None if total is None or expected==0 else abs(total-expected)/expected<=.05,
                     'coverage_fraction':r['coverage_fraction'],'state':r['measurement_state'],
                     'scene_args':[fill,shape,cx,obstacle,dropout,range_m,seq]})
    manifest={'source':'simulation','transport':'native-c-test',
              'reference_id':'bench-vl53-30cm-v3','sensor_profile':'VL53L5CX-inspired-8x8',
              'chip_source_sha256':hashlib.sha256((ROOT/'wokwi'/'boxflow-lidar.chip.c').read_bytes()).hexdigest(),
              'note':'Volumes de referência são fórmulas analíticas de sólidos. Amostras binárias contêm somente leituras e cabeçalho; não contêm esses volumes.',
              'samples':rows}
    (ROOT/'samples'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
