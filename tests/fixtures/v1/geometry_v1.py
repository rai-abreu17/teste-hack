"""Estimator: decoded distances -> box points -> local TIN -> horizontal grid.

No access to the simulation's fill, shape, center or analytical volume.
Standard library only. Geometry is a versioned hypothetical empty-box reference.
"""
import math
import struct
import zlib

REFERENCE_ID = "demo-box-v1"
ALGORITHM_ID = "angular-tin-grid-v1"
WIDTH, DEPTH, HEIGHT, CELL = 8.0, 6.0, 6.0, 0.25
NX, NY = 32, 24
MAX_EDGE_M = 0.80
MIN_COVERAGE = 1.0  # A total is only available when every grid center has support.


def base(x, y):
    return max(0.0, 0.5-x, x-7.5)


def in_beam(p):
    x, y, z = p
    return 4.29 <= x <= 4.71 and -0.01 <= y <= 6.01 and 3.79 <= z <= 4.21


def rotate(u, yaw, tilt):
    y, t = math.radians(yaw), math.radians(tilt)
    x = math.cos(t)*u[0] + math.sin(t)*u[2]
    z = -math.sin(t)*u[0] + math.cos(t)*u[2]
    return (math.cos(y)*x-math.sin(y)*u[1], math.sin(y)*x+math.cos(y)*u[1], z)


def decode_frame(data):
    if len(data) < 64 or len(data) > 31914:
        raise ValueError("Tamanho de quadro inválido")
    if data[:4] != b"BFLD" or data[4:6] != b"\x01\x01":
        raise ValueError("Identificação, versão ou estado do sensor inválido")
    hsize, = struct.unpack_from("<H", data, 6)
    sequence, start_ms, duration_ms = struct.unpack_from("<IQI", data, 8)
    cols, rows, record_size, geometry_version = struct.unpack_from("<HHHH", data, 24)
    pose = struct.unpack_from("<6f", data, 32)
    range_mm, payload_size, crc = struct.unpack_from("<HHI", data, 56)
    if not (hsize == 64 and record_size == 10 and geometry_version == 1 and
            9 <= cols <= 65 and 9 <= rows <= 49 and payload_size == cols*rows*10 and
            len(data) == 64+payload_size and 500 <= range_mm <= 30000 and duration_ms == 50):
        raise ValueError("Cabeçalho inconsistente ou geometria não suportada")
    if not all(math.isfinite(v) for v in pose):
        raise ValueError("Pose não finita")
    if not (1 <= pose[0] <= 7 and 1 <= pose[1] <= 5 and 4.6-1e-5 <= pose[2] <= 5.9+1e-5
            and -45 <= pose[3] <= 45 and -20 <= pose[4] <= 20 and pose[5] == 0):
        raise ValueError("Pose fora do envelope da geometria de demonstração")
    actual = zlib.crc32(data[64:], zlib.crc32(data[:60]))
    if actual != crc:
        raise ValueError("CRC inválido; quadro rejeitado por inteiro")
    readings, points = [], []
    excluded = {"no_return": 0, "out_of_range": 0, "beam": 0, "wall_or_outside": 0, "below_reference": 0}
    for mm, ux, uy, uz, status, reserved in struct.iter_unpack("<HhhhBB", data[64:]):
        if status not in (0, 1, 2) or reserved != 0 or (status != 1 and mm != 0):
            raise ValueError("Indicador de leitura inválido")
        u = (ux/32767, uy/32767, uz/32767)
        norm = math.sqrt(sum(v*v for v in u))
        if abs(norm-1) > 0.0001 or uz >= 0:
            raise ValueError("Direção inválida")
        if status == 1 and not 1 <= mm <= range_mm:
            raise ValueError("Distância inválida")
        readings.append([mm, ux, uy, uz, status])
        if status != 1:
            excluded["no_return" if status == 0 else "out_of_range"] += 1
            points.append(None)
            continue
        d = rotate(tuple(v/norm for v in u), pose[3], pose[4])
        p = tuple(pose[k] + mm/1000*d[k] for k in range(3))
        x, y, z = p
        if in_beam(p):
            excluded["beam"] += 1
            points.append(None)
        elif not (0.003 < x < WIDTH-0.003 and 0.003 < y < DEPTH-0.003 and z < HEIGHT):
            excluded["wall_or_outside"] += 1
            points.append(None)
        elif z < base(x,y)-0.03:
            excluded["below_reference"] += 1
            points.append(None)
        else:
            points.append(p)
    return {"sequence": sequence, "acquisition_start_ms": start_ms,
            "acquisition_duration_ms": duration_ms, "acquisition_clock": "simulation_monotonic",
            "reference_id": REFERENCE_ID, "columns": cols, "rows": rows, "range_m": range_mm/1000,
            "sensor_pose": {"translation_m": list(pose[:3]), "yaw_deg": pose[3], "tilt_deg": pose[4], "roll_deg": pose[5]},
            "readings": readings, "points_by_ray": points, "excluded": excluded}


def raster_triangle(points, indices, sums, counts):
    verts = [points[k] for k in indices]
    if any(v is None for v in verts):
        return
    a, b, c = verts
    # Local adjacency plus a maximum 3D edge; never bridge arbitrary distant points.
    if any(math.dist(p,q) > MAX_EDGE_M for p,q in ((a,b),(b,c),(c,a))):
        return
    den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(den) < 1e-9:  # Vertical faces do not have horizontal integration area.
        return
    ix0 = max(0, math.ceil(min(v[0] for v in verts)/CELL-0.5))
    ix1 = min(NX-1, math.floor(max(v[0] for v in verts)/CELL-0.5))
    iy0 = max(0, math.ceil(min(v[1] for v in verts)/CELL-0.5))
    iy1 = min(NY-1, math.floor(max(v[1] for v in verts)/CELL-0.5))
    for iy in range(iy0, iy1+1):
        y = (iy+0.5)*CELL
        for ix in range(ix0, ix1+1):
            x = (ix+0.5)*CELL
            wa = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1]))/den
            wb = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1]))/den
            wc = 1-wa-wb
            if min(wa,wb,wc) < -1e-7:
                continue
            z = wa*a[2]+wb*b[2]+wc*c[2]
            if z < base(x,y)-0.03:
                continue
            k = iy*NX+ix
            sums[k] += max(0, z-base(x,y))
            counts[k] += 1


def estimate(data):
    decoded = decode_frame(data)
    points, cols, rows = decoded["points_by_ray"], decoded["columns"], decoded["rows"]
    sums, counts = [0.0]*(NX*NY), [0]*(NX*NY)
    for row in range(rows-1):
        for col in range(cols-1):
            a = row*cols+col
            raster_triangle(points,(a,a+1,a+cols+1),sums,counts)
            raster_triangle(points,(a,a+cols+1,a+cols),sums,counts)
    heights = [s/n if n else None for s,n in zip(sums,counts)]
    covered = sum(h is not None for h in heights)
    coverage = covered/(NX*NY)
    observed = sum(h for h in heights if h is not None)*CELL*CELL if covered else None
    # Ambiguity from missing cells only. This is not an uncertainty interval.
    missing_max = sum((HEIGHT-base((k%NX+0.5)*CELL,(k//NX+0.5)*CELL))*CELL*CELL
                      for k,h in enumerate(heights) if h is None)
    state = "valid" if covered == NX*NY else "partial" if covered else "unavailable"
    reason = ("Todas as células têm suporte local; validade restrita ao modelo simulado." if state == "valid" else
              "Há células sem observação; o volume mostrado cobre somente a região reconstruída." if covered else
              "Não há superfície suficiente para calcular volume.")
    if decoded["excluded"]["below_reference"]:
        state = "unavailable"
        reason = "Pontos abaixo da referência; verificar pose e calibração."
    total = observed if state == "valid" else None
    public = {k:v for k,v in decoded.items() if k not in ("points_by_ray","readings")}
    public.update({"algorithm_id": ALGORITHM_ID, "measurement_state": state, "reason": reason,
                   "observed_volume_m3": observed, "total_volume_m3": total,
                   "coverage_fraction": coverage, "observed_area_m2": covered*CELL*CELL,
                   "unobserved_area_m2": (NX*NY-covered)*CELL*CELL,
                   "unobserved_possible_volume_m3": missing_max,
                   "valid_returns": sum(r[4]==1 for r in decoded["readings"]),
                   "total_returns": len(points), "grid": {"nx":NX,"ny":NY,"cell_m":CELL,"height_m":heights},
                   "points": [list(p) for p in points if p is not None],
                   "geometry": {"width_m":WIDTH,"depth_m":DEPTH,"height_m":HEIGHT,
                                "hypothetical":True,"reference_id":REFERENCE_ID}})
    return public
