"""Evaluation ONLY: exact integration of independently specified solid surfaces.

Never imported by estimators. Scene parameters are supplied by the evaluator.
Clipping a linear triangular face to a grid cell preserves its exact integral.
This is reference integration, not an estimator using the simulated geometry.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    fill: float = 75
    shape: int = 0
    cx: float = .15
    obstacle: int = 0
    dropout: int = 0
    range_m: float = 4
    sensor_z: float = .40


def pyramid(cx, cy, side, height):
    d = side / 2
    corners = [(cx-d, cy-d, 0), (cx+d, cy-d, 0),
               (cx+d, cy+d, 0), (cx-d, cy+d, 0)]
    return [(corners[i], corners[(i+1) % 4], (cx, cy, height))
            for i in range(4)]


def faces(scene):
    h = .10 * scene.fill / 100
    if scene.shape == 0:
        return pyramid(scene.cx, .15, .15, h)
    if scene.shape == 1:
        return pyramid(.09, .15, .10, h) + pyramid(.21, .15, .10, .7*h)
    if scene.shape in (2, 3):
        x0, x1, y0, y1 = scene.cx-.075, scene.cx+.075, .075, .225
        z0 = 0 if scene.shape == 3 else h
        a, b, c, d = (x0,y0,z0), (x1,y0,h), (x1,y1,h), (x0,y1,z0)
    elif scene.shape == 4:
        a, b, c, d = (0,0,h), (.30,0,h), (.30,.30,h), (0,.30,h)
    else:
        raise ValueError('Unknown evaluator shape')
    return [(a,b,c), (a,c,d)]


def analytical_volume(scene):
    h = .10 * scene.fill / 100
    return {0: .15**2*h/3, 1: .10**2*h*1.7/3,
            2: .15**2*h, 3: .15**2*h/2, 4: .30**2*h}[scene.shape]


def clip(poly, axis, boundary, greater):
    if not poly:
        return []
    out = []
    prev = poly[-1]
    inside_prev = prev[axis] >= boundary if greater else prev[axis] <= boundary
    for cur in poly:
        inside = cur[axis] >= boundary if greater else cur[axis] <= boundary
        if inside != inside_prev:
            t = (boundary-prev[axis])/(cur[axis]-prev[axis])
            out.append(tuple(prev[k] + t*(cur[k]-prev[k]) for k in range(3)))
        if inside:
            out.append(cur)
        prev, inside_prev = cur, inside
    return out


def integral(poly):
    if len(poly) < 3:
        return 0.0
    a = poly[0]
    result = 0.0
    for b, c in zip(poly[1:-1], poly[2:]):
        area = abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
        result += area*(a[2]+b[2]+c[2])/3
    return result


def cell_volumes(scene, nx=20, ny=20, cell=.015):
    triangles = faces(scene)
    out = []
    for iy in range(ny):
        for ix in range(nx):
            total = 0.0
            for triangle in triangles:
                p = list(triangle)
                for axis, boundary, greater in [(0,ix*cell,True), (0,(ix+1)*cell,False),
                                                (1,iy*cell,True), (1,(iy+1)*cell,False)]:
                    p = clip(p, axis, boundary, greater)
                total += integral(p)
            out.append(total)
    return out
