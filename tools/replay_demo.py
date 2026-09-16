"""Replay recorded native-C ray frames to the same HTTP endpoint as the ESP32."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.parse
import uuid

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:8000');p.add_argument('--interval',type=float,default=3)
    p.add_argument('--loop',action='store_true');args=p.parse_args()
    if args.interval<0:raise SystemExit('Intervalo não pode ser negativo')
    samples=json.loads((ROOT/'samples'/'manifest.json').read_text(encoding='utf-8'))['samples']
    local=urllib.parse.urlparse(args.url).hostname in ('127.0.0.1','localhost','::1')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({})) if local else urllib.request.build_opener()
    while True:
        boot='replay-'+uuid.uuid4().hex
        for item in samples:
            headers={'Content-Type':'application/vnd.boxflow.scan-v2','X-Device-ID':'boxflow-esp32-demo','X-Box-ID':'BOX-DEMO-01',
                     'X-Boot-ID':boot,'X-Source':'simulation','X-Geometry-ID':'bench-vl53-30cm-v3','X-Acquisition-Clock':'simulation_monotonic',
                     'X-Transport':'native-c-test','X-Frame-Age-Ms':'0'}
            if os.environ.get('BOXFLOW_TOKEN'):headers['Authorization']='Bearer '+os.environ['BOXFLOW_TOKEN']
            request=urllib.request.Request(args.url.rstrip('/')+'/api/scans',data=(ROOT/'samples'/item['file']).read_bytes(),headers=headers)
            try:
                with opener.open(request,timeout=12) as r:print(item['name'],r.read().decode(),flush=True)
            except OSError as e:raise SystemExit(f'Receptor não acessível: {e}. Inicie python server/app.py primeiro.')
            time.sleep(args.interval)
        if not args.loop:break


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
