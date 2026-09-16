"""Offline candidate estimators. Inputs: binary frame and fixed configuration.

No simulator, scene parameters, truth volumes or evaluator imports.
E1/E2 preserve the production reference, integration and missing-cell policy.
E3 is explicitly a conditional model estimate, not an observed total.
"""
import math
import numpy as np
from scipy.optimize import least_squares
from server import geometry as g


def grid_result(heights, below_reference=0):
    covered = sum(v is not None for v in heights)
    state = 'valid' if covered == g.NX*g.NY else 'partial' if covered else 'unavailable'
    if below_reference:
        state = 'unavailable'
    observed = sum(v for v in heights if v is not None)*g.CELL**2 if covered else None
    return {'measurement_state': state, 'observed_volume_m3': observed,
            'total_volume_m3': observed if state == 'valid' else None,
            'coverage_fraction': covered/(g.NX*g.NY), 'heights': heights,
            'below_reference_points': below_reference}


def triangles(cols, rows):
    for row in range(rows-1):
        for col in range(cols-1):
            a = row*cols+col
            yield a,a+1,a+cols+1
            yield a,a+cols+1,a+cols


def slope_degrees(vertices, heights):
    a,b,c = vertices
    dx1,dy1,dx2,dy2 = b[0]-a[0], b[1]-a[1], c[0]-a[0], c[1]-a[1]
    det = dx1*dy2-dx2*dy1
    if abs(det) < 1e-9:
        return None
    dh1,dh2 = heights[1]-heights[0], heights[2]-heights[0]
    gx,gy = (dh1*dy2-dh2*dy1)/det, (dx1*dh2-dx2*dh1)/det
    return math.degrees(math.atan(math.hypot(gx,gy)))


def estimate_tin(data, roi=8, max_slope_deg=None):
    if roi not in (8,6,4):
        raise ValueError('ROI must be 8, 6 or 4 centered zones')
    if max_slope_deg is not None and not 0 < max_slope_deg < 90:
        raise ValueError('Invalid gradient limit')
    decoded = g.decode_frame(data)
    points = list(decoded['points_by_ray'])
    margin = (8-roi)//2
    for k in range(64):
        if not (margin <= k//8 < 8-margin and margin <= k%8 < 8-margin):
            points[k] = None
    sums, counts = [0.0]*400, [0]*400
    rejected = 0
    for ids in triangles(8,8):
        vertices = [points[i] for i in ids]
        if max_slope_deg is not None and all(p is not None for p in vertices):
            heights = [p[2]-g.base(p[0],p[1]) for p in vertices]
            angle = slope_degrees(vertices, heights)
            if angle is not None and angle > max_slope_deg:
                rejected += 1
                continue
        # Keep the existing maximum edge guard and exact rasterizer.
        g.raster_triangle(points, ids, sums, counts)
    out = grid_result([s/n if n else None for s,n in zip(sums,counts)],
                      decoded['excluded']['below_reference'])
    out.update({'roi': roi, 'max_slope_deg': max_slope_deg,
                'gradient_rejected_triangles': rejected})
    return out


def model_surface(xy, parameters, prior):
    cx,cy,height,slope = parameters
    delta = np.abs(xy-np.array([cx,cy]))
    if prior == 'square_pyramid':
        radius = delta.max(axis=1)
    elif prior == 'cone':
        radius = np.sqrt((delta**2).sum(axis=1))
    else:
        raise ValueError('Unknown declared prior')
    return np.maximum(0.0, height-slope*radius)


def estimate_parametric(data, prior, bounds, gates):
    if prior not in ('square_pyramid','cone'):
        raise ValueError('Declare square_pyramid or cone explicitly')
    decoded = g.decode_frame(data)
    points = np.asarray([p for p in decoded['points_by_ray'] if p is not None], dtype=float)
    out = {'prior': prior, 'measurement_state': 'inconclusive',
           'model_volume_m3': None, 'candidate_model_volume_m3': None,
           'precision_status': 'not_validated', 'failed_gates': []}
    if len(points) == 0:
        out['failed_gates'] = ['no_points']
        return out
    xy = points[:,:2]
    heights = points[:,2] - np.array([g.base(x,y) for x,y in xy])
    positive = heights > gates['positive_threshold_m']
    floor = ~positive
    out.update({'point_count': len(points), 'positive_points': int(positive.sum()),
                'floor_points': int(floor.sum())})
    if decoded['excluded']['below_reference']:
        out['failed_gates'].append('below_reference')
    if positive.sum() < gates['minimum_positive_points']:
        out['failed_gates'].append('too_few_positive_points')
    if floor.sum() < gates['minimum_floor_points']:
        out['failed_gates'].append('too_few_floor_points')
    if out['failed_gates']:
        return out
    margin = bounds['center_margin_m']
    lower = np.array([margin,margin,bounds['height_m'][0],math.tan(math.radians(bounds['slope_deg'][0]))])
    upper = np.array([g.WIDTH-margin,g.DEPTH-margin,bounds['height_m'][1],math.tan(math.radians(bounds['slope_deg'][1]))])
    center = np.average(xy[positive], axis=0, weights=heights[positive])
    peak_center = xy[np.argmax(heights)]
    candidates = []
    def residual(p):
        return model_surface(xy,p,prior)-heights
    # Deterministic starts are derived from measurements, never from true geometry.
    for c in (center, peak_center):
        for angle in (30,45,60):
            slope = math.tan(math.radians(angle))
            initial = np.array([*c, float(max(heights)+slope*.02), slope])
            initial = np.maximum(lower+1e-8,np.minimum(upper-1e-8,initial))
            fit = least_squares(residual, initial, bounds=(lower,upper),
                                loss='linear', x_scale='jac', max_nfev=600,
                                ftol=1e-11, xtol=1e-11, gtol=1e-11)
            candidates.append(fit)
    fit = min(candidates, key=lambda f: float(np.dot(f.fun,f.fun)))
    cx,cy,h,m = [float(v) for v in fit.x]
    rms = float(np.sqrt(np.mean(fit.fun**2)))
    maximum = float(np.max(np.abs(fit.fun)))
    singular = np.linalg.svd(fit.jac,compute_uv=False)
    condition = float(singular[0]/singular[-1]) if singular[-1] > 1e-12 else None
    rank = int(np.linalg.matrix_rank(fit.jac))
    radius = h/m
    volume = (4 if prior == 'square_pyramid' else math.pi)*h*radius**2/3
    out.update({'parameters': {'center_x_m':cx,'center_y_m':cy,'height_m':h,
                               'slope':m,'slope_deg':math.degrees(math.atan(m)),
                               'base_half_width_or_radius_m':radius},
                'rms_m':rms, 'maximum_residual_m':maximum, 'jacobian_rank':rank,
                'jacobian_condition':condition, 'candidate_model_volume_m3':volume})
    if not fit.success:
        out['failed_gates'].append('optimizer_not_converged')
    if rms > gates['maximum_rms_m']:
        out['failed_gates'].append('rms')
    if maximum > gates['maximum_absolute_residual_m']:
        out['failed_gates'].append('maximum_residual')
    if rank < 4 or condition is None or condition > gates['maximum_jacobian_condition']:
        out['failed_gates'].append('not_identifiable')
    if not (radius <= cx <= g.WIDTH-radius and radius <= cy <= g.DEPTH-radius):
        out['failed_gates'].append('footprint_outside_box')
    if any(abs(fit.x[i]-lower[i]) < 1e-6 or abs(fit.x[i]-upper[i]) < 1e-6 for i in range(4)):
        out['failed_gates'].append('parameter_at_bound')
    if not out['failed_gates']:
        out['measurement_state'] = 'model_supported'
        out['model_volume_m3'] = volume
    return out
