"""Compare mounting height and support, using the same ideal ray caster."""
import json,math,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'server'))
from geometry import estimate

def main():
    rows=[]
    for height in (.35,.40,.45,.50):
        for name,fill,shape in [('vazio',0,0),('piramide-75',75,0),('camada-75',75,4)]:
            raw=subprocess.check_output([str(ROOT/'build/scene_dump'),*map(str,(fill,shape,.15,0,0,4,1,0,0,height))])
            result=estimate(raw)
            rows.append({'sensor_height_m':height,'scene':name,'nominal_floor_footprint_side_m':2*height*math.tan(math.radians(22.5)),'nominal_footprint_at_10cm_side_m':2*(height-.10)*math.tan(math.radians(22.5)),'coverage_fraction':result['coverage_fraction'],'state':result['measurement_state'],'observed_m3':result['observed_volume_m3'],'total_m3':result['total_volume_m3']})
    data={'reference_id':'bench-vl53-30cm-v3','notice':'Ideal zone centers; footprint does not guarantee support or physical precision.','results':rows}
    (ROOT/'build/mounting-comparison.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
