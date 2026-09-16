"""Frozen R006 diagnostic evaluation. Reuses frames, never acquires new ones."""
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
from experiments import truth
from server import geometry as g
from r005_estimator import fuse_frames

SOURCE = ROOT / '.ai/runs/m001-implementation/results'
OUT = ROOT / '.ai/runs/m001-r006/results'
CELL_AREA = g.CELL**2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normal(face):
    a, b, c = face
    u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(x*x for x in n))
    return tuple(x/length for x in n) if length else None


def transition_edges(faces):
    edges = {}
    for face in faces:
        for a, b in zip(face, (face[1], face[2], face[0])):
            key = tuple(sorted((tuple(round(x, 12) for x in a[:2]),
                                tuple(round(x, 12) for x in b[:2]))))
            edges.setdefault(key, []).append(face)
    keep = []
    for edge, neighbors in edges.items():
        if len(neighbors) == 1:
            keep.append(edge)
            continue
        ns = [normal(f) for f in neighbors]
        coplanar = all(n is not None for n in ns)
        if coplanar:
            n0, origin = ns[0], neighbors[0][0]
            coplanar = all(abs(abs(sum(a*b for a, b in zip(n0, n)))-1) <= 1e-9 for n in ns)
            coplanar = coplanar and all(abs(sum(n0[i]*(v[i]-origin[i]) for i in range(3))) <= 1e-9
                                       for face in neighbors for v in face)
        if not coplanar:
            keep.append(edge)
    return keep


def point_segment_distance(point, edge):
    a, b = edge
    v = (b[0]-a[0], b[1]-a[1])
    length2 = sum(x*x for x in v)
    t = max(0, min(1, sum((point[i]-a[i])*v[i] for i in range(2))/length2)) if length2 else 0
    return math.hypot(*(point[i]-a[i]-t*v[i] for i in range(2)))


def center_height(faces, x, y):
    candidates = [0.0]
    for a, b, c in faces:
        den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-12:
            continue
        wa = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1]))/den
        wb = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1]))/den
        wc = 1-wa-wb
        if min(wa, wb, wc) >= -1e-9:
            candidates.append(wa*a[2]+wb*b[2]+wc*c[2])
    return max(candidates)


def beam_blocked(origin, target):
    entry, leave = 0.0, 1.0
    for i, (low, high) in enumerate(((.17, .20), (0, .3), (.18, .20))):
        delta = target[i]-origin[i]
        if abs(delta) < 1e-12:
            if not low <= origin[i] <= high:
                return False
        else:
            a, b = sorted(((low-origin[i])/delta, (high-origin[i])/delta))
            entry, leave = max(entry, a), min(leave, b)
            if entry > leave:
                return False
    return leave > 1e-9 and entry < 1-1e-9


def in_fov(pose, target, scale=1):
    d = [target[i]-pose['translation_m'][i] for i in range(3)]
    y, t = math.radians(pose['yaw_deg']), math.radians(pose['tilt_deg'])
    x, yy = math.cos(y)*d[0]+math.sin(y)*d[1], -math.sin(y)*d[0]+math.cos(y)*d[1]
    xx, z = math.cos(t)*x-math.sin(t)*d[2], math.sin(t)*x+math.cos(t)*d[2]
    return z < 0 and max(abs(xx/-z), abs(yy/-z)) <= scale*math.tan(math.radians(22.5))+1e-12


def stats(heights, ref, indices):
    indices = list(indices)
    assert all(heights[i] is not None for i in indices)
    residuals = [(heights[i]*CELL_AREA-ref[i]) for i in indices]
    signed, spatial = sum(residuals), sum(abs(x) for x in residuals)
    volume = sum(ref[i] for i in indices)
    return {'cell_count': len(indices), 'area_m2': len(indices)*CELL_AREA,
            'truth_volume_m3': volume, 'estimated_volume_m3': volume+signed if indices else None,
            'signed_error_m3': signed, 'absolute_volume_error_m3': abs(signed),
            'integrated_absolute_error_m3': spatial,
            'signed_error_percent': signed/volume*100 if volume else None,
            'absolute_error_percent': abs(signed)/volume*100 if volume else None,
            'spatial_error_percent': spatial/volume*100 if volume else None,
            'mean_absolute_height_error_mm': spatial/(len(indices)*CELL_AREA)*1000 if indices else None}


def grouped(heights, ref, indices, transitions, shadows):
    whole = stats(heights, ref, indices)
    selectors = {
        'transition': lambda i: transitions[i], 'planar': lambda i: not transitions[i],
        'shadow': lambda i: shadows[i], 'not_shadow': lambda i: not shadows[i],
        'transition_or_shadow': lambda i: transitions[i] or shadows[i],
        'remaining': lambda i: not (transitions[i] or shadows[i]),
        'transition_and_shadow': lambda i: transitions[i] and shadows[i],
        'transition_only': lambda i: transitions[i] and not shadows[i],
        'shadow_only': lambda i: shadows[i] and not transitions[i],
        'neither': lambda i: not transitions[i] and not shadows[i]}
    groups = {}
    for name, predicate in selectors.items():
        part = stats(heights, ref, [i for i in indices if predicate(i)])
        for field, denom in (('error_fraction', 'integrated_absolute_error_m3'),
                             ('area_fraction', 'area_m2'), ('truth_fraction', 'truth_volume_m3')):
            part[field] = part[denom]/whole[denom] if whole[denom] else None
        groups[name] = part
    for names in (('transition', 'planar'), ('shadow', 'not_shadow'),
                  ('transition_or_shadow', 'remaining'),
                  ('transition_and_shadow', 'transition_only', 'shadow_only', 'neither')):
        for key in ('cell_count', 'area_m2', 'truth_volume_m3', 'signed_error_m3', 'integrated_absolute_error_m3'):
            assert math.isclose(sum(groups[n][key] for n in names), whole[key], abs_tol=1e-12)
    concern = groups['transition_or_shadow']['mean_absolute_height_error_mm']
    remaining = groups['remaining']['mean_absolute_height_error_mm']
    ratio = concern/remaining if concern is not None and remaining is not None and remaining > 0 else None
    return {'overall': whole, 'groups': groups,
            'transition_or_shadow_error_density_ratio': ratio,
            'higher_error_density_in_concern': ratio > 1 if ratio is not None else None}


def maps_svg(scenes):
    width, panel, step = 1280, 235, 9
    height = 80+len(scenes)*225
    items = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#fafafa"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#202020;font-size:12px}</style>',
             '<text x="20" y="24">R006 · SIMULATED · residual: blue negative / red positive, saturation ±20 mm; gray missing</text>',
             '<text x="20" y="44">No promotion. Geometry: orange transition, purple potential beam shadow (all aimed views), white planar.</text>']
    for row, scene in enumerate(scenes):
        y = 75+row*225
        items.append(f'<text x="20" y="{y}">{html.escape(scene["scene_id"])}</text>')
        panels = [('geometry', None)] + [(k, scene['maps'][k]) for k in ('fixed3_median', 'aimed_median', 'aimed_lower', 'aimed_lower_trim2')]
        for p, (label, values) in enumerate(panels):
            x0 = 20+p*panel
            items.append(f'<text x="{x0}" y="{y+17}">{label}</text>')
            for i in range(400):
                if values is None:
                    color = '#8855bb' if scene['shadow'][i] else '#edac50' if scene['transition'][i] else '#ffffff'
                elif values[i] is None:
                    color = '#999999'
                else:
                    value = max(-1, min(1, values[i]/20))
                    pale = round(250-180*abs(value))
                    color = f'rgb(240,{pale},{pale})' if value >= 0 else f'rgb({pale},{pale},240)'
                items.append(f'<rect x="{x0+(i%20)*step}" y="{y+25+(i//20)*step}" width="{step}" height="{step}" fill="{color}"/>')
    return ''.join(items)+'</svg>'


def main():
    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite diagnostic results: {OUT}')
    protocol_path = HERE / 'protocol_r006.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf-8'))
    assert sha(protocol_path) == (HERE/'protocol_r006.sha256').read_text().split()[0]
    historical_path = SOURCE/'comparisons.json'
    historical_digest = sha(historical_path)
    original = json.loads(historical_path.read_text(encoding='utf-8'))
    specs = protocol['estimator']['fixed_acquisition_comparison'][:1]+protocol['estimator']['same_acquisition_attribution_only']
    assert [s['scene_id'] for s in original['scenes']] == protocol['inputs']['scene_ids']
    records, cell_records, view_records, map_records, hashes = [], [], [], [], {}
    for original_scene in original['scenes']:
        sid = original_scene['scene_id']
        scene = truth.Scene(**original_scene['scene_for_evaluator_only'])
        ref = truth.cell_volumes(scene)
        assert math.isclose(sum(ref), truth.analytical_volume(scene), abs_tol=1e-12)
        faces = truth.faces(scene)
        edges = transition_edges(faces)
        targets = [((i%20+.5)*g.CELL, (i//20+.5)*g.CELL) for i in range(400)]
        transitions = [any(point_segment_distance(p, e) <= g.CELL+1e-12 for e in edges) for p in targets]
        targets = [(x,y,g.base(x,y)+center_height(faces,x,y)) for x,y in targets]
        archived = {a['arm_id']: a for a in original_scene['arms']}
        acquisitions, captured = {}, {}
        for acquisition in protocol['inputs']['acquisitions']:
            frames = []
            paths = sorted((SOURCE/'frames'/sid).glob(f'{acquisition}-*.bin'))
            assert len(paths) == protocol['inputs']['captures_per_acquisition']
            for path, view in zip(paths, archived[acquisition]['per_view']):
                assert sha(path) == view['sha256']
                hashes[str(path.relative_to(ROOT))] = sha(path)
                frames.append(path.read_bytes())
            captured[acquisition] = frames
            base = fuse_frames(frames)
            assert not base['invalid_frames'] and not base['unavailable_view_indices']
            assert base['heights'] == archived[acquisition]['heights']
            acquisitions[acquisition] = base
            for view in base['per_view']:
                pose = view['decoded']['sensor_pose']
                counts = [0]*400
                for point in view['decoded']['points_by_ray']:
                    if point is not None:
                        ix, iy = math.floor(point[0]/g.CELL), math.floor(point[1]/g.CELL)
                        if 0 <= ix < 20 and 0 <= iy < 20:
                            counts[iy*20+ix] += 1
                view['point_bins'] = counts
                view['fov'] = [in_fov(pose,t) for t in targets]
                view['zone_center_span'] = [in_fov(pose,t,.875) for t in targets]
                view['beam_shadow'] = [bool(scene.obstacle) and beam_blocked(pose['translation_m'],t) for t in targets]
                view_records.append({'scene_id':sid,'acquisition':acquisition, **view})
        common = [i for i in range(400) if all(a['heights'][i] is not None for a in acquisitions.values())]
        maps = {}
        for spec in specs:
            base = acquisitions[spec['acquisition']]
            result = base if spec['trim_kappa'] is None and not spec['lower'] else fuse_frames(
                captured[spec['acquisition']], trim_kappa=spec['trim_kappa'], lower=spec['lower'])
            heights = result['heights']
            assert [h is not None for h in heights] == [h is not None for h in base['heights']]
            own = [i for i,h in enumerate(heights) if h is not None]
            missing = [i for i,h in enumerate(heights) if h is None]
            shadow = [all(v['beam_shadow'][i] for v in base['per_view']) for i in range(400)]
            any_shadow = [any(v['beam_shadow'][i] for v in base['per_view']) for i in range(400)]
            total = stats(heights,ref,range(400)) if result['total_selection']['selected'] else None
            passes5 = total['absolute_error_percent'] <= 5 if total and total['absolute_error_percent'] is not None else None
            record = {'scene_id':sid,'shape':scene.shape,'obstacle':scene.obstacle,'dropout':scene.dropout,
                'method':spec['id'],'total_selection':result['total_selection'], 'whole_box':total,
                'company_5pct_total_only':passes5, 'trimmed_cells':result['trimmed_cell_count'],
                'own':grouped(heights,ref,own,transitions,shadow),
                'common_fixed3_aimed':grouped(heights,ref,common,transitions,shadow),
                'unsupported':{'cell_count':len(missing),'area_m2':len(missing)*CELL_AREA,
                               'truth_volume_m3':sum(ref[i] for i in missing)},
                'continuous_fov_union_cells':sum(any(v['fov'][i] for v in base['per_view']) for i in range(400)),
                'point_bin_union_cells':sum(any(v['point_bins'][i]>0 for v in base['per_view']) for i in range(400)),
                'potential_beam_shadow_all_views_cells':sum(shadow)}
            assert record['own']['overall']['cell_count']+len(missing)==400
            assert math.isclose(record['own']['overall']['truth_volume_m3']+record['unsupported']['truth_volume_m3'],sum(ref),abs_tol=1e-12)
            records.append(record)
            maps[spec['id']] = [(h-ref[i]/CELL_AREA)*1000 if h is not None else None for i,h in enumerate(heights)]
            for i in range(400):
                values = [v['heights'][i] for v in base['per_view'] if v['heights'][i] is not None]
                cell_records.append({'scene_id':sid,'method':spec['id'],'cell':i,'height_m':heights[i],
                    'truth_volume_m3':ref[i], 'truth_mean_height_m':ref[i]/CELL_AREA,
                    'signed_residual_m3':heights[i]*CELL_AREA-ref[i] if heights[i] is not None else None,
                    'transition':transitions[i],'potential_beam_shadow_all_views':shadow[i],
                    'potential_beam_shadow_any_view':any_shadow[i],
                    'views_supporting':len(values), 'height_range_m':max(values)-min(values) if values else None,
                    'height_population_std_m':statistics.pstdev(values) if values else None,
                    'usable_returns_in_bin':sum(v['point_bins'][i] for v in base['per_view']),
                    'continuous_fov_union':any(v['fov'][i] for v in base['per_view']),
                    'zone_center_span_union':any(v['zone_center_span'][i] for v in base['per_view'])})
        map_records.append({'scene_id':sid,'transition':transitions,'shadow':[
            all(v['beam_shadow'][i] for v in acquisitions['translated3_aimed']['per_view']) for i in range(400)],'maps':maps})
    assert len(hashes)==54 and len(records)==45 and len(cell_records)==18000 and len(view_records)==54
    assert sha(historical_path)==historical_digest
    group_aggregates=[]
    for shape, obstacle, dropout, method in sorted({(r['shape'],r['obstacle'],r['dropout'],r['method']) for r in records}):
        selected=[r for r in records if (r['shape'],r['obstacle'],r['dropout'],r['method'])==(shape,obstacle,dropout,method)]
        group_aggregates.append({'shape':shape,'obstacle':obstacle,'dropout':dropout,'method':method,
            'scenes':[r['scene_id'] for r in selected],
            'pooled_own_absolute_cell_error_m3':sum(r['own']['overall']['integrated_absolute_error_m3'] for r in selected),
            'pooled_own_area_m2':sum(r['own']['overall']['area_m2'] for r in selected),
            'total_eligible':sum(r['whole_box'] is not None for r in selected),
            'total_within_5pct':sum(r['company_5pct_total_only'] is True for r in selected)})
    OUT.mkdir(parents=True)
    result={'experiment_id':'R-006','scope':'SIMULATED diagnostic; not holdout',
        'protocol_sha256':sha(protocol_path),'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'company_requirement':{'relative_absolute_volume_error_max':.05,
           'source':'User: 0,05 error between measured and real volume; interpreted as relative 5%',
           'post_protocol_supplement':True,'applies_only_to_eligible_total':True,'latency_requirement':None},
        'comparison_count':len(records),'records':records,'descriptive_family_aggregates':group_aggregates,
        'interpretation_limits':protocol['interpretation_limits']}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for filename, entries in (('cells.jsonl',cell_records),('views.jsonl',view_records)):
        with (OUT/filename).open('w',encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    (OUT/'maps.svg').write_text(maps_svg(map_records),encoding='utf-8')
    table=[]
    for r in records:
        table.append({'scene':r['scene_id'],'method':r['method'],'support_cells':r['own']['overall']['cell_count'],
            'common_cells':r['common_fixed3_aimed']['overall']['cell_count'],
            'common_signed_error_percent':r['common_fixed3_aimed']['overall']['signed_error_percent'],
            'common_spatial_error_percent':r['common_fixed3_aimed']['overall']['spatial_error_percent'],
            'own_error_density_ratio':r['own']['transition_or_shadow_error_density_ratio'],
            'common_error_density_ratio':r['common_fixed3_aimed']['transition_or_shadow_error_density_ratio'],
            'total_error_percent':r['whole_box']['absolute_error_percent'] if r['whole_box'] else None,
            'total_within_5pct':r['company_5pct_total_only'],'trimmed_cells':r['trimmed_cells']})
    with (OUT/'summary.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0])); writer.writeheader();writer.writerows(table)
    for path in (Path(__file__),HERE/'r005_estimator.py',HERE/'protocol_r006.json',ROOT/'server/geometry.py',ROOT/'experiments/truth.py',historical_path):
        hashes[str(path.relative_to(ROOT))]=sha(path)
    for path in OUT.iterdir():
        hashes[str(path.relative_to(ROOT))]=sha(path)
    (OUT/'hash-manifest.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({'comparisons':len(records),'frames_reused':54,'cells':len(cell_records),'new_captures':0,'output':str(OUT)},ensure_ascii=False))
    for r in table:
        if r['method'] in ('fixed3_median','aimed_median'):
            print(json.dumps(r,ensure_ascii=False))


if __name__=='__main__':
    main()
