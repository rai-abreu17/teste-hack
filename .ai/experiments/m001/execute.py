"""Compile, test, and execute P-001 while recording commands and real outputs."""

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / ".ai" / "runs" / "m001-implementation"
BIN_DIR = RUN / "bin"
LOG = RUN / "command-log.json"


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise SystemExit("gcc or clang is required")
    commands = [
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         str(HERE / "scene_dump_m001.c"), "-lm", "-o", str(BIN_DIR / "scene_dump_m001.exe")],
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         str(ROOT / "tools" / "scene_dump.c"), "-lm", "-o", str(BIN_DIR / "scene_dump_legacy.exe")],
        [sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py", "-v"],
        [sys.executable, str(HERE / "run_p001.py")],
    ]
    record = {"delegation_started_at_utc": "2026-09-13T23:17:47Z",
              "executor_started_at_utc": now(), "commands": []}
    for command in commands:
        started = now()
        completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, check=False)
        item = {"command": [str(value) for value in command], "started_at_utc": started,
                "finished_at_utc": now(), "exit_code": completed.returncode,
                "stdout": completed.stdout, "stderr": completed.stderr}
        record["commands"].append(item)
        print(f"exit={completed.returncode}: {' '.join(map(str, command))}", flush=True)
        if completed.stdout:
            print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n", flush=True)
        if completed.stderr:
            print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
        if completed.returncode:
            record["executor_finished_at_utc"] = now()
            LOG.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            raise SystemExit(completed.returncode)
    record["executor_finished_at_utc"] = now()
    LOG.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
