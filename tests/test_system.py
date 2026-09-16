import json
import os
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from geometry import estimate,decode_frame
from app import Store,make_server


def frame(fill=75,shape=0,center=.15,obstacle=0,dropout=0,range_m=4,seq=1,yaw=0,tilt=0,sensor_z=.40):
    return subprocess.check_output([str(ROOT/'build'/'scene_dump'),*[str(x) for x in
        (fill,shape,center,obstacle,dropout,range_m,seq,yaw,tilt,sensor_z)]])


def fix_crc(raw):
    out=bytearray(raw)
    struct.pack_into('<I',out,60,zlib.crc32(out[64:],zlib.crc32(out[:60])))
    return bytes(out)


META={'device':'boxflow-esp32-demo','box':'BOX-DEMO-01','boot':'unit-test-boot','transport':'native-c-test','age_ms':50}


class GeometryTests(unittest.TestCase):
    def test_empty_includes_sloped_bases(self):
        r=estimate(frame(0))
        self.assertLess(r['observed_volume_m3'],.00005)
        self.assertEqual(r['coverage_fraction'],1)
        self.assertEqual(r['measurement_state'],'valid')

    def test_analytic_constant_thickness_layer(self):
        for fill in (25,50,75,100):
            with self.subTest(fill=fill):
                expected=.30*.30*(.10*fill/100)
                r=estimate(frame(fill,shape=4))
                # Compare the observed patch to its exact constant-thickness volume.
                patch=r['observed_area_m2']*(.10*fill/100)
                self.assertAlmostEqual(r['observed_volume_m3'],patch,delta=.00005)
                self.assertGreater(expected,0)

    def test_redistribution_changes_points_not_reference(self):
        left=estimate(frame(center=.10));right=estimate(frame(center=.20))
        self.assertNotEqual(left['points'],right['points'])
        self.assertEqual(left['reference_id'],right['reference_id'])
        self.assertEqual(left['sensor_pose'],right['sensor_pose'])

    def test_occlusion_does_not_publish_total(self):
        r=estimate(frame(obstacle=1))
        self.assertEqual(r['measurement_state'],'partial')
        self.assertIsNone(r['total_volume_m3'])
        self.assertGreater(r['unobserved_possible_volume_m3'],0)

    def test_input_output_sequence(self):
        volumes=[estimate(frame(fill=f))['observed_volume_m3'] for f in (0,25,50,75,50,25,0)]
        self.assertTrue(volumes[0]<volumes[1]<volumes[2]<volumes[3])
        self.assertTrue(volumes[3]>volumes[4]>volumes[5]>volumes[6])

    def test_occlusion_masks_beam_and_preserves_unknowns(self):
        r=estimate(frame(obstacle=1))
        self.assertGreater(r['excluded']['beam'],0)
        self.assertLess(r['coverage_fraction'],1)
        self.assertIsNone(r['total_volume_m3'])
        self.assertIn(None,r['grid']['height_m'])
        self.assertEqual(r['measurement_state'],'partial')
        self.assertGreater(r['unobserved_possible_volume_m3'],0)

    def test_no_return_is_not_zero(self):
        r=estimate(frame(dropout=100))
        self.assertIsNone(r['observed_volume_m3'])
        self.assertEqual(r['measurement_state'],'unavailable')
        self.assertEqual(r['coverage_fraction'],0)

    def test_short_range(self):
        r=estimate(frame(range_m=.2))
        self.assertGreater(r['excluded']['out_of_range'],0)
        self.assertIsNone(r['observed_volume_m3'])

    def test_pose_transform(self):
        r=estimate(frame(yaw=10,tilt=4))
        self.assertGreater(r['observed_volume_m3'],0)
        self.assertEqual(r['sensor_pose']['yaw_deg'],10)
        self.assertEqual(r['excluded']['below_reference'],0)

    def test_vertical_faces_do_not_imply_complete_coverage(self):
        r=estimate(frame(shape=2))
        self.assertEqual(r['measurement_state'],'partial')
        self.assertIsNone(r['total_volume_m3'])
        # Visible flat top can be measured, while hidden floor remains unknown.
        # Quantization means a reconstructed value is not a strict lower bound.
        self.assertGreater(r['observed_volume_m3'],0)
        self.assertGreater(r['unobserved_area_m2'],0)

    def test_truncation_corruption_and_invalid_direction(self):
        raw=frame()
        for invalid in (raw[:-1],raw+bytes(1),raw[:120]+bytes([raw[120]^1])+raw[121:]):
            with self.assertRaises(ValueError):decode_frame(invalid)
        raw=bytearray(raw);raw[66:72]=bytes(6)
        with self.assertRaises(ValueError):decode_frame(fix_crc(raw))

    def test_fixed_8x8_profile_and_protocol_v2(self):
        raw=frame();d=decode_frame(raw)
        self.assertEqual(len(raw),704);self.assertEqual(raw[4],2)
        self.assertEqual(len(d['readings']),64)
        self.assertEqual(d['acquisition_duration_ms'],100)
        self.assertEqual(d['sensor_profile'],'VL53L5CX-inspired-8x8')
        with self.assertRaises(ValueError):decode_frame((ROOT/'tests/fixtures/v1/pyramid_6m3.bin').read_bytes())

    def test_previous_reference_is_rejected_even_with_valid_crc(self):
        raw=bytearray(frame())
        struct.pack_into('<H',raw,30,2)
        with self.assertRaisesRegex(ValueError,'geometria não suportada'):
            decode_frame(fix_crc(raw))

    def test_small_bench_output_uses_square_metres_and_cubic_metres(self):
        r=estimate(frame())
        self.assertAlmostEqual(r['observed_area_m2']+r['unobserved_area_m2'],.09)
        self.assertEqual(r['geometry']['width_m'],.30)
        self.assertEqual(r['geometry']['depth_m'],.30)
        self.assertAlmostEqual(r['sensor_pose']['translation_m'][2],.40,places=6)
        self.assertEqual(r['reference_id'],'bench-vl53-30cm-v3')

    def test_reference_shift_is_independent_of_measurements(self):
        raw=frame();original=bytes(raw)
        low=estimate(raw,reference_offset_m=-.02)
        lower=estimate(raw,reference_offset_m=-.03)
        self.assertEqual(raw,original)
        self.assertAlmostEqual(lower['observed_volume_m3']-low['observed_volume_m3'],low['observed_area_m2']*.01,places=10)
        high=estimate(raw,reference_offset_m=.01)
        self.assertEqual(high['measurement_state'],'unavailable')
        self.assertIsNone(high['total_volume_m3'])

    def test_reference_offset_must_be_finite(self):
        for offset in (float('nan'),float('inf'),.2):
            with self.assertRaises(ValueError):estimate(frame(),reference_offset_m=offset)



class StoreTests(unittest.TestCase):
    def setUp(self):self.store=Store(':memory:')
    def tearDown(self):self.store.db.close()

    def test_duplicate_does_not_refresh_measurement(self):
        a=self.store.accept(META,frame(),now=100)
        b=self.store.accept(META,frame(),now=200)
        self.assertFalse(a['duplicate']);self.assertTrue(b['duplicate'])
        self.assertEqual(len(self.store.latest(now=200)['history']),1)
        self.assertEqual(self.store.latest(now=200)['measurement_state'],'stale')

    def test_same_identity_different_data_and_out_of_order(self):
        self.store.accept(META,frame(seq=2))
        with self.assertRaises(ValueError):self.store.accept(META,frame(fill=50,seq=2))
        with self.assertRaises(ValueError):self.store.accept(META,frame(seq=1))

    def test_boot_session_allows_new_sequence(self):
        self.store.accept(META,frame(seq=20))
        self.store.accept(dict(META,boot='new-session'),frame(seq=1))
        self.assertEqual(len(self.store.latest()['history']),2)

    def test_interrupted_update_and_fault_recovery(self):
        self.store.accept(META,frame(),now=100)
        self.assertEqual(self.store.latest(now=120)['measurement_state'],'valid')
        self.store.record_failure(META,'i2c_nack',now=125)
        self.assertEqual(self.store.latest(now=126)['measurement_state'],'unavailable')
        self.assertEqual(self.store.latest(now=146)['measurement_state'],'stale')
        self.store.accept(META,frame(seq=2),now=150)
        self.assertEqual(self.store.latest(now=151)['measurement_state'],'valid')

    def test_old_frame_receipt_does_not_become_current(self):
        self.store.accept(dict(META,age_ms=60000),frame(),now=100)
        self.assertEqual(self.store.latest(now=101)['measurement_state'],'stale')

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'test.sqlite3';s=Store(path);s.accept(META,frame());s.db.close()
            reopened=Store(path)
            self.assertEqual(reopened.raw_latest()['sequence'],1);reopened.db.close()


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(':memory:');self.server=make_server('127.0.0.1',0,self.store,'test-secret')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.db.close()

    def headers(self):
        return {'Content-Type':'application/vnd.boxflow.scan-v2','X-Device-ID':META['device'],'X-Box-ID':META['box'],
                'X-Boot-ID':META['boot'],'X-Source':'simulation','X-Geometry-ID':'bench-vl53-30cm-v3',
                'X-Acquisition-Clock':'simulation_monotonic','X-Transport':'native-c-test','Authorization':'Bearer test-secret'}

    def test_end_to_end_http_dashboard_and_raw(self):
        req=urllib.request.Request(self.base+'/api/scans',data=frame(),headers=self.headers())
        with self.opener.open(req) as r:self.assertTrue(json.load(r)['accepted'])
        with self.opener.open(self.base+'/api/latest') as r:
            result=json.load(r);self.assertEqual(result['transport'],'native-c-test');self.assertGreater(result['observed_volume_m3'],0);self.assertEqual(result['total_returns'],64)
        with self.opener.open(self.base+'/api/raw/latest') as r:self.assertEqual(len(json.load(r)['readings']),64)
        for path in ('/','/app.js','/style.css','/health'):
            with self.opener.open(self.base+path) as r:self.assertEqual(r.status,200)

    def test_reject_unauthorized_and_truncated(self):
        bad_headers=self.headers();bad_headers.pop('Authorization')
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.opener.open(urllib.request.Request(self.base+'/api/scans',data=frame(),headers=bad_headers))
        self.assertEqual(ctx.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.opener.open(urllib.request.Request(self.base+'/api/scans',data=frame()[:-4],headers=self.headers()))
        self.assertEqual(ctx.exception.code,400)
        self.assertEqual(self.store.latest()['history'],[])


if __name__=='__main__':unittest.main(verbosity=2)
