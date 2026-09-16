"""E4: a measured empty surface, learned only from binary empty acquisitions.

No scene truth is accepted. A broad, fixed validation envelope is used while
decoding so the old analytical floor cannot remove biased empty measurements.
The analytical floor is NOT subtracted: all heights use the learned surface.
Pose changes are reported. This offline diagnostic does not auto-authorize a
new calibration for a physically moved sensor.
"""
import math
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from server import geometry as g
from .estimators import grid_result, triangles


def decode_without_analytical_floor_rejection(raw):
    # Keeps binary, range, pose, wall and beam validation. The fixed -10 cm
    # envelope is independent of the evaluator's injected bias.
    return g.decode_frame(raw,reference_offset_m=-.10)


class MeasuredZero:
    def __init__(self, frames):
        if not frames:
            raise ValueError('Empty-reference frames required')
        readings = [decode_without_analytical_floor_rejection(raw) for raw in frames]
        self.pose = readings[0]['sensor_pose']
        if any(r['sensor_pose'] != self.pose for r in readings):
            raise ValueError('Reference acquisitions must have the same declared pose')
        directions = [r[1:4] for r in readings[0]['readings']]
        if any([v[1:4] for v in r['readings']] != directions for r in readings):
            raise ValueError('Reference directions changed')
        self.directions = directions
        # Require a return in every reference acquisition for each retained zone.
        points = []
        deviations = []
        for k in range(64):
            values = [r['points_by_ray'][k] for r in readings]
            if all(v is not None for v in values):
                arr = np.asarray(values)
                points.append(arr.mean(axis=0))
                deviations.append(float(arr[:,2].std()))
        if len(points) < 4:
            raise ValueError('Insufficient empty-surface support')
        self.points = np.asarray(points)
        self.interpolate = LinearNDInterpolator(self.points[:,:2],self.points[:,2],fill_value=np.nan)
        self.frame_count = len(frames)
        self.repeatability_std_z_m_max = max(deviations)

    def heights_at(self, points):
        xy = np.asarray([p[:2] for p in points])
        return np.asarray([p[2] for p in points])-self.interpolate(xy)


def raster(vertices, heights, sums, counts):
    a,b,c = vertices
    if any(math.dist(p,q) > g.MAX_EDGE_M for p,q in ((a,b),(b,c),(c,a))):
        return
    den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-9:
        return
    x0 = max(0,math.ceil(min(p[0] for p in vertices)/g.CELL-.5))
    x1 = min(g.NX-1,math.floor(max(p[0] for p in vertices)/g.CELL-.5))
    y0 = max(0,math.ceil(min(p[1] for p in vertices)/g.CELL-.5))
    y1 = min(g.NY-1,math.floor(max(p[1] for p in vertices)/g.CELL-.5))
    for iy in range(y0,y1+1):
        for ix in range(x0,x1+1):
            x,y = (ix+.5)*g.CELL,(iy+.5)*g.CELL
            wa = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
            wb = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
            wc = 1-wa-wb
            if min(wa,wb,wc) < -1e-7:
                continue
            height = sum(w*h for w,h in zip((wa,wb,wc),heights))
            if height < -g.BELOW_REFERENCE_TOLERANCE_M:
                continue
            k = iy*g.NX+ix
            sums[k] += max(0,height)
            counts[k] += 1


def estimate_with_zero(raw, reference):
    decoded = decode_without_analytical_floor_rejection(raw)
    if [v[1:4] for v in decoded['readings']] != reference.directions:
        raise ValueError('Live directions differ from the learned reference')
    points = decoded['points_by_ray']
    hs = [None]*64
    missing_ref, below = 0,0
    for k,p in enumerate(points):
        if p is None:
            continue
        h = float(reference.heights_at([p])[0])
        if not math.isfinite(h):
            missing_ref += 1
        elif h < -g.BELOW_REFERENCE_TOLERANCE_M:
            below += 1
        else:
            hs[k] = h
    sums,counts = [0.0]*400,[0]*400
    for ids in triangles(8,8):
        if all(hs[k] is not None for k in ids):
            raster([points[k] for k in ids],[hs[k] for k in ids],sums,counts)
    result = grid_result([s/n if n else None for s,n in zip(sums,counts)],below)
    result.update({'reference_frame_count':reference.frame_count,
                   'reference_points':len(reference.points),
                   'missing_reference_points':missing_ref,
                   'reference_repeatability_std_z_m_max':reference.repeatability_std_z_m_max,
                   'declared_pose_changed':decoded['sensor_pose'] != reference.pose,
                   'status':'offline_diagnostic_only'})
    return result
