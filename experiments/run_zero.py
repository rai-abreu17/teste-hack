"""Synthetic common-bias and live-only-drift injections for E4, with fresh CRCs."""
import hashlib
import json
import struct
import zlib
from server import geometry as g
from .measured_zero import MeasuredZero, estimate_with_zero
from .run_comparison import OUT,PROTOCOL,capture,error_percent,domain_result
from .truth import Scene,analytical_volume,cell_volumes


def inject(raw, kind, millimetres):
    data = bytearray(raw)
    if kind == 'declared_pose_z':
        struct.pack_into('<f',data,40,struct.unpack_from('<f',data,40)[0]+millimetres/1000)
    elif kind == 'range':
        if int(millimetres) != millimetres:
            raise ValueError('The binary range resolution is one millimetre')
        for k in range(64):
            at = 64+k*10
            if data[at+8] == 1:
                mm = struct.unpack_from('<H',data,at)[0]+int(millimetres)
                struct.pack_into('<H',data,at,mm)
    else:
        raise ValueError('Unknown injection')
    struct.pack_into('<I',data,60,zlib.crc32(data[64:],zlib.crc32(data[:60])))
    return bytes(data)


def compact(result):
    return {k:v for k,v in result.items() if k != 'heights' and k not in ('points','grid')}


def main():
    all_rows = []
    for shape in (0,4):
        scene = Scene(shape=shape)
        truth = cell_volumes(scene)
        expected = analytical_volume(scene)
        live,_ = capture(scene)
        # Fresh native acquisitions differ in sequence; this deterministic mock has
        # no temporal measurement noise. Repeating frames cannot validate averaging.
        empties = [capture(Scene(fill=0),sequence)[0]
                   for sequence in range(1,PROTOCOL['measured_zero_frames']+1)]
        for kind in ('declared_pose_z','range'):
            for mode,biases in [('shared',PROTOCOL['shared_bias_mm']),('live_only_drift',PROTOCOL['drift_mm'])]:
                for bias in biases:
                    zeros = [inject(raw,kind,bias if mode=='shared' else 0) for raw in empties]
                    current = inject(live,kind,bias)
                    for frame in [*zeros,current]:
                        (OUT/'frames'/f'{hashlib.sha256(frame).hexdigest()}.bin').write_bytes(frame)
                    reference = MeasuredZero(zeros)
                    measured = estimate_with_zero(current,reference)
                    analytic = g.estimate(current)
                    for name,r in [('measured_zero',measured),('analytical_reference',analytic)]:
                        heights = r.get('heights',r.get('grid',{}).get('height_m'))
                        mask = [h is not None for h in heights]
                        row = {'shape':shape,'mode':mode,'bias_kind':kind,'bias_mm':bias,'method':name,
                               'reference_total_m3':expected,
                               'frame_sha256':hashlib.sha256(current).hexdigest(),
                               **compact(r),'own_domain':domain_result(heights,truth,mask),
                               'total_error_percent':error_percent(r['total_volume_m3'],expected)}
                        all_rows.append(row)
    output = {'source':'simulation','transport':'native-c-test','rows':all_rows,
              'notes':['Shared errors are added to both empty and filled acquisitions; drift only to the filled frame.',
                       'Pose bias modifies reported metadata, not the true ray-casting pose.',
                       'Range bias adds the same integer distance to each valid return, not the same vertical displacement.',
                       'Empty acquisition noise is deterministic; eight repeats are not eight independent noisy measurements.',
                       'Measured-reference interpolation has finite support and does not remove sampling bias.',
                       'Synthetic cancellation is not a physical calibration or proof that all pose errors cancel.']}
    (OUT/'measured-zero.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(output,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
