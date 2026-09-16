"""Controlled ideal 64-zone versus 3185-ray comparison; not a real sensor mode."""
import hashlib,json,shutil,subprocess,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'));sys.path.insert(0,str(ROOT/'tools'))
from geometry import estimate
from generate_samples import SCENES

def once(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Review source adaptation: '+old)
    return text.replace(old,new,1)

def main():
    cc=shutil.which('gcc') or shutil.which('clang')
    if not cc:raise SystemExit('Install GCC or Clang.')
    out=ROOT/'build/comparison';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'wokwi/boxflow-lidar.chip.c').read_text()
    dense=once(source,'#define BF_MAX_COLS 8','#define BF_MAX_COLS 65')
    dense=once(dense,'#define BF_MAX_ROWS 8','#define BF_MAX_ROWS 49')
    dense=once(dense,'s.cols=8;s.rows=8;','s.cols=65;s.rows=49;')
    dense=once(dense,'((float)col+.5f)/8','((float)col+.5f)/s.cols')
    dense=once(dense,'((float)row+.5f)/8','((float)row+.5f)/s.rows')
    harness=(ROOT/'tools/scene_dump.c').read_text().split('// Native harness',1)[1]
    (out/'dense.c').write_text('#define BOXFLOW_HOST\n'+dense+'\n// Native harness'+harness)
    subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(out/'dense.c'),'-lm','-o',str(out/'dense')],check=True)
    decoder=once((ROOT/'server/geometry.py').read_text(),'len(data) > 704','len(data) > 31914')
    decoder=once(decoder,'cols == 8 and rows == 8','cols == 65 and rows == 49')
    module=types.ModuleType('dense_comparison');exec(compile(decoder,'dense_comparison','exec'),module.__dict__)
    rows=[]
    for seq,(name,fill,shape,cx,obstacle,dropout,range_m,expected) in enumerate(SCENES,1):
        args=list(map(str,(fill,shape,cx,obstacle,dropout,range_m,seq)))
        item={'scene':name,'analytical_total_m3':expected}
        for profile,exe,estimator in [('64_zones',ROOT/'build/scene_dump',estimate),('3185_ideal_rays',out/'dense',module.estimate)]:
            result=estimator(subprocess.check_output([str(exe),*args]));total=result['total_volume_m3']
            item[profile]={'state':result['measurement_state'],'observed_m3':result['observed_volume_m3'],'total_m3':total,'coverage_fraction':result['coverage_fraction'],'relative_total_error_percent':None if total is None or expected==0 else 100*(total-expected)/expected}
        rows.append(item)
    result={'notice':'Ideal dense benchmark, not a commercial sensor or a VL53L5CX mode.','controlled':{'bench_m':[.3,.3,.15],'pose_m':[.15,.15,.4],'horizontal_fov_deg':45,'vertical_fov_deg':45,'range_limit_m':4,'grid_m':.015,'max_edge_m':.1},'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'results':rows}
    (ROOT/'build/resolution-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
