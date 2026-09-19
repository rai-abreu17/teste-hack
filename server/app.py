"""BoxFlow demonstration HTTP receiver and persistent history. Python >=3.10."""
import argparse
import datetime as dt
import hmac
import json
import os
import re
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from geometry import decode_frame, estimate, REFERENCE_ID

STALE_SECONDS = 45
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript("""
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS scans(
            id INTEGER PRIMARY KEY, device TEXT, box TEXT, boot TEXT, seq INTEGER,
            received REAL, source TEXT, transport TEXT, age_ms INTEGER,
            raw BLOB, result TEXT, UNIQUE(device,box,boot,seq));
          CREATE TABLE IF NOT EXISTS attempts(
            id INTEGER PRIMARY KEY, device TEXT, boot TEXT, received REAL, state TEXT, reason TEXT);
        """)

    def accept(self, meta, data, now=None):
        now = time.time() if now is None else now
        measurement = estimate(data)
        with self.lock:
            key = (meta["device"],meta["box"],meta["boot"],measurement["sequence"])
            old = self.db.execute("SELECT raw FROM scans WHERE device=? AND box=? AND boot=? AND seq=?",key).fetchone()
            if old:
                if bytes(old["raw"]) != data:
                    raise ValueError("Mesma identificação com conteúdo diferente")
                return {"accepted": True,"duplicate": True,"sequence":key[-1]}
            last = self.db.execute("SELECT seq FROM scans WHERE device=? AND box=? AND boot=? ORDER BY id DESC LIMIT 1",key[:3]).fetchone()
            if last and measurement["sequence"] <= last["seq"]:
                raise ValueError("Varredura fora de ordem")
            self.db.execute("INSERT INTO scans(device,box,boot,seq,received,source,transport,age_ms,raw,result) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (*key,now,"simulation",meta["transport"],meta["age_ms"],data,json.dumps(measurement,allow_nan=False)))
            self.db.commit()
        return {"accepted":True,"duplicate":False,"sequence":key[-1],
                "state":measurement["measurement_state"],"observed_volume_m3":measurement["observed_volume_m3"]}

    def record_failure(self, meta, reason, now=None):
        with self.lock:
            self.db.execute("INSERT INTO attempts(device,boot,received,state,reason) VALUES(?,?,?,?,?)",
                            (meta["device"],meta["boot"],time.time() if now is None else now,"unavailable",reason))
            self.db.commit()

    def latest(self, now=None, box_id=None):
        now = time.time() if now is None else now
        with self.lock:
            if box_id:
                row = self.db.execute("SELECT * FROM scans WHERE box=? ORDER BY id DESC LIMIT 1",(box_id,)).fetchone()
            else:
                row = self.db.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1").fetchone()
            failure = self.db.execute("SELECT * FROM attempts ORDER BY id DESC LIMIT 1").fetchone()
            if row is None:
                return {"source":"simulation","measurement_state":"unavailable", "box_id":box_id or "BOX-DEMO-01",
                        "reason":failure["reason"] if failure else "Aguardando a primeira varredura.","history":[]}
            result = json.loads(row["result"])
            age = max(0,now-row["received"])+row["age_ms"]/1000
            result.update({"device_id":row["device"],"box_id":row["box"],"boot_id":row["boot"],
                           "source":row["source"],"transport":row["transport"],"received_at":dt.datetime.fromtimestamp(row["received"],dt.timezone.utc).isoformat(),
                           "age_seconds":age,"stale_after_seconds":STALE_SECONDS,
                           "is_previous_measurement":False,
                           "underlying_measurement_state":result["measurement_state"]})
            if failure and failure["device"] == row["device"] and failure["received"] > row["received"]:
                result["measurement_state"] = "unavailable"
                result["is_previous_measurement"] = True
                result["reason"] = "Falha de aquisição: "+failure["reason"]+". A superfície exibida pertence à leitura anterior."
            if age > STALE_SECONDS:
                result["measurement_state"] = "stale"
                result["is_previous_measurement"] = True
                result["reason"] = "Atualização interrompida. Os valores pertencem à última varredura recebida."
            if box_id:
                records = self.db.execute("SELECT seq,received,age_ms,result,boot FROM scans WHERE box=? ORDER BY id DESC LIMIT 80",(box_id,)).fetchall()
            else:
                records = self.db.execute("SELECT seq,received,age_ms,result,boot FROM scans ORDER BY id DESC LIMIT 80").fetchall()
            result["history"] = []
            for r in reversed(records):
                m=json.loads(r["result"])
                result["history"].append({"sequence":r["seq"],"boot_id":r["boot"],"received_at":dt.datetime.fromtimestamp(r["received"],dt.timezone.utc).isoformat(),
                                          "observed_volume_m3":m["observed_volume_m3"],"coverage_fraction":m["coverage_fraction"],"state":m["measurement_state"],
                                          "occupancy_fraction":m.get("occupancy_fraction")})
            return result

    def raw_latest(self):
        with self.lock:
            row=self.db.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1").fetchone()
            if row is None:return None
            d=decode_frame(row["raw"])
            d.pop("points_by_ray")
            d.update({"device_id":row["device"],"box_id":row["box"],"boot_id":row["boot"],"source":"simulation",
                      "record_columns":["range_mm","ux_q15","uy_q15","uz_q15","validity"]})
            return d


def make_server(host, port, store, token=""):
    static=Path(__file__).parent/"static"

    class Handler(BaseHTTPRequestHandler):
        protocol_version="HTTP/1.1"

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def respond(self, code, body, content_type="application/json; charset=utf-8"):
            if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(code);self.send_header("Content-Type",content_type)
            self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff");self.end_headers();self.wfile.write(body)

        def do_GET(self):
            split=urlsplit(self.path)
            path=split.path
            if path=="/api/latest":
                box_id=parse_qs(split.query).get("box_id",[None])[0]
                return self.respond(200,store.latest(box_id=box_id))
            if path=="/api/raw/latest":
                raw=store.raw_latest();return self.respond(200 if raw else 404,raw or {"error":"Sem dados"})
            if path=="/favicon.ico":return self.respond(204,b"", "image/x-icon")
            if path=="/health":return self.respond(200,{"ok":True,"source":"simulation"})
            names={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}
            mime={"/":"text/html; charset=utf-8","/app.js":"text/javascript; charset=utf-8","/style.css":"text/css; charset=utf-8"}
            if path in names:return self.respond(200,(static/names[path]).read_bytes(),mime[path])
            self.respond(404,{"error":"Não encontrado"})

        def metadata(self):
            meta={k:self.headers.get(h,"") for k,h in (("device","X-Device-ID"),("box","X-Box-ID"),("boot","X-Boot-ID"))}
            if not all(ID_PATTERN.fullmatch(v) for v in meta.values()):raise ValueError("Identificação inválida")
            # One explicitly instrumented demo device; box just needs a well-formed id
            # (checked above via ID_PATTERN), so any instrumented box can be targeted.
            if meta["device"]!="boxflow-esp32-demo":raise ValueError("Dispositivo não cadastrado")
            if self.headers.get("X-Source")!="simulation" or self.headers.get("X-Geometry-ID")!=REFERENCE_ID:
                raise ValueError("Origem ou referência incompatível")
            if self.headers.get("X-Acquisition-Clock")!="simulation_monotonic":raise ValueError("Relógio não suportado")
            meta["age_ms"]=int(self.headers.get("X-Frame-Age-Ms","0"))
            if not 0<=meta["age_ms"]<=86400000:raise ValueError("Idade inválida")
            meta["transport"]=self.headers.get("X-Transport","")
            if meta["transport"] not in ("wokwi-esp32","native-c-test"):raise ValueError("Transporte inválido")
            return meta

        def do_POST(self):
            if token and not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+token):
                self.close_connection=True;return self.respond(401,{"error":"Token inválido"})
            try:
                if self.headers.get("Transfer-Encoding"):raise ValueError("Use Content-Length")
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=704:raise ValueError("Corpo ausente ou grande demais")
                meta=self.metadata();data=self.rfile.read(length)
                if len(data)!=length:raise ValueError("Transferência incompleta")
                if self.path=="/api/scans":
                    if self.headers.get("Content-Type")!="application/vnd.boxflow.scan-v2":raise ValueError("Tipo de conteúdo incorreto")
                    return self.respond(200,store.accept(meta,data))
                if self.path=="/api/device-status":
                    content=json.loads(data)
                    if not isinstance(content,dict) or content.get("state")!="unavailable":raise ValueError("Estado inválido")
                    reason=content.get("reason")
                    if not isinstance(reason,str) or not 1<=len(reason)<=120:raise ValueError("Motivo inválido")
                    store.record_failure(meta,reason);return self.respond(200,{"accepted":True})
                self.respond(404,{"error":"Não encontrado"})
            except (ValueError,TypeError,UnicodeError) as e:
                self.close_connection=True;self.respond(400,{"error":str(e)})

    return ThreadingHTTPServer((host,port),Handler)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=8000)
    p.add_argument("--db",default=str(Path(__file__).parent/"boxflow-vl53-30cm-v3.sqlite3"));args=p.parse_args()
    store=Store(args.db);server=make_server(args.host,args.port,store,os.environ.get("BOXFLOW_TOKEN",""))
    print(f"BoxFlow SIMULAÇÃO: http://{args.host}:{server.server_port} | receptor pronto",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();store.db.close()


if __name__=="__main__":main()
