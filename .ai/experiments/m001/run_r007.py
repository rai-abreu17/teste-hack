"""Acquire the preregistered R007 holdout after independent release.

This runner never imports the estimator or truth evaluator.  Before capture it
verifies every pre-open hash, the independent release, and the absence of any
R007 frame or result.  Capture is one-shot and generates all five candidate
views for all twelve fixed scenes.
"""

from argparse import ArgumentParser
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / ".ai/runs/m001-r007"
FRAMES = RUN / "frames"
RESULTS = RUN / "results"
PROTOCOL = HERE / "protocol_r007.json"
PROTOCOL_HASH = HERE / "protocol_r007.sha256"
PRE_OPEN = RUN / "pre-open-manifest.json"
PRE_OPEN_RELEASE = RUN / "independent-pre-open-release.json"
COMMANDS = RUN / "capture-commands.json"
ACQUISITION = RUN / "acquisition-manifest.json"
ACQUISITION_VALIDATION = RUN / "acquisition-validation.json"
SIMULATOR = ROOT / ".ai/runs/m001-implementation/bin/scene_dump_m001.exe"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_protocol():
    expected = PROTOCOL_HASH.read_text(encoding="utf-8").split()[0]
    actual = sha256(PROTOCOL)
    if actual != expected:
        raise RuntimeError(f"frozen R007 protocol hash mismatch: {actual} != {expected}")
    return json.loads(PROTOCOL.read_text(encoding="utf-8")), actual


def verify_preopen(require_pristine=True):
    protocol, protocol_hash = load_protocol()
    manifest = json.loads(PRE_OPEN.read_text(encoding="utf-8"))
    if manifest.get("experiment_id") != "R-007" or manifest.get("phase") != "PRE_OPEN":
        raise RuntimeError("invalid R007 pre-open manifest identity")
    if manifest.get("protocol_sha256") != protocol_hash:
        raise RuntimeError("pre-open manifest does not bind the frozen protocol")
    for name, expected in manifest["frozen_files"].items():
        path = ROOT / name
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            raise RuntimeError(f"pre-open hash mismatch: {name}: {actual} != {expected}")
    if manifest["counts"] != {
        "fixed_scenes": 12,
        "views_per_scene": 5,
        "expected_new_frames": 60,
        "existing_r007_frames": 0,
        "existing_r007_result_files": 0,
    }:
        raise RuntimeError("invalid pre-open artifact counts")
    if require_pristine:
        frames = list(FRAMES.rglob("*.bin")) if FRAMES.exists() else []
        result_files = [path for path in RESULTS.rglob("*") if path.is_file()] if RESULTS.exists() else []
        forbidden = [COMMANDS, ACQUISITION, ACQUISITION_VALIDATION]
        if frames or result_files or any(path.exists() for path in forbidden):
            raise RuntimeError("R007 is no longer pristine; capture is one-shot")
    return protocol, manifest


def verify_release(release_path, expected_decision, binding_key, binding_hash):
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if release.get("experiment_id") != "R-007":
        raise RuntimeError("independent release has wrong experiment identity")
    if release.get("decision") != expected_decision:
        raise RuntimeError(f"independent release decision must be {expected_decision}")
    if release.get(binding_key) != binding_hash:
        raise RuntimeError(f"independent release does not bind {binding_key}")
    reviewer = release.get("reviewer")
    reviewed_at = release.get("reviewed_at_utc")
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(reviewed_at, str) or not reviewed_at:
        raise RuntimeError("independent release requires reviewer and reviewed_at_utc")
    return release


def validate_frame_header(raw, expected_capture):
    if len(raw) != 704 or raw[:6] != b"BFLD\x02\x01":
        raise RuntimeError("invalid R007 frame envelope or identity")
    header_size, = struct.unpack_from("<H", raw, 6)
    sequence, _start_ms, duration_ms = struct.unpack_from("<IQI", raw, 8)
    cols, rows, record_size, geometry_version = struct.unpack_from("<HHHH", raw, 24)
    pose = struct.unpack_from("<6f", raw, 32)
    range_mm, payload_size, crc = struct.unpack_from("<HHI", raw, 56)
    actual_crc = zlib.crc32(raw[64:], zlib.crc32(raw[:60]))
    if not (header_size == 64 and duration_ms == 100 and cols == rows == 8
            and record_size == 10 and geometry_version == 3 and range_mm == 4000
            and payload_size == 640 and actual_crc == crc):
        raise RuntimeError("invalid R007 frame header or CRC")
    expected_pose = [*expected_capture["origin"], expected_capture["yaw_deg"],
                     expected_capture["tilt_deg"], expected_capture["roll_deg"]]
    if sequence != expected_capture["sequence"]:
        raise RuntimeError(f"sequence mismatch: {sequence} != {expected_capture['sequence']}")
    if any(abs(actual - expected) > 1e-7 for actual, expected in zip(pose, expected_pose)):
        raise RuntimeError(f"pose mismatch: {list(pose)} != {expected_pose}")
    return {
        "sequence": sequence,
        "sensor_pose": {
            "translation_m": list(pose[:3]),
            "yaw_deg": pose[3],
            "tilt_deg": pose[4],
            "roll_deg": pose[5],
        },
        "bytes": len(raw),
        "crc32": f"{crc:08x}",
    }


def capture():
    protocol, manifest = verify_preopen(require_pristine=True)
    manifest_hash = sha256(PRE_OPEN)
    verify_release(PRE_OPEN_RELEASE, "RELEASE_R007_OPEN",
                   "pre_open_manifest_sha256", manifest_hash)
    if sha256(SIMULATOR) != manifest["frozen_files"][relative(SIMULATOR)]:
        raise RuntimeError("simulator changed after independent release")

    commands, captured = [], {}
    for scene in protocol["scenes"]:
        scene_dir = FRAMES / scene["id"]
        scene_dir.mkdir(parents=True, exist_ok=False)
        for capture_spec in protocol["candidate"]["captures"]:
            sequence = capture_spec["sequence"]
            output = scene_dir / f"candidate-{sequence}.bin"
            command = [
                str(SIMULATOR), str(scene["fill"]), str(scene["shape"]), str(scene["cx"]),
                str(scene["obstacle"]), str(scene["dropout"]), str(scene["range_m"]),
                str(sequence), str(capture_spec["yaw_deg"]), str(capture_spec["tilt_deg"]),
                str(capture_spec["origin"][2]), str(capture_spec["origin"][0]),
                str(capture_spec["origin"][1]),
            ]
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       check=False)
            record = {
                "kind": "r007_reserved_capture",
                "scene_id": scene["id"],
                "sequence": sequence,
                "command": command,
                "exit_code": completed.returncode,
                "stderr": completed.stderr.decode("utf-8", errors="replace"),
                "stdout_bytes": len(completed.stdout),
                "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
                "stdout_path": relative(output),
            }
            commands.append(record)
            if completed.returncode:
                raise RuntimeError(f"R007 capture failed: {scene['id']} seq{sequence}")
            header = validate_frame_header(completed.stdout, capture_spec)
            with output.open("xb") as stream:
                stream.write(completed.stdout)
            captured[relative(output)] = {
                "sha256": sha256(output),
                "scene_id": scene["id"],
                "header": header,
            }

    if len(captured) != 60:
        raise RuntimeError(f"expected 60 new R007 frames, got {len(captured)}")
    COMMANDS.write_text(json.dumps(commands, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    acquisition = {
        "experiment_id": "R-007",
        "created_at_utc": utc_now(),
        "phase": "ACQUIRED_TRUTH_FREE_NOT_SCORED",
        "protocol_sha256": sha256(PROTOCOL),
        "pre_open_manifest_sha256": manifest_hash,
        "pre_open_release_sha256": sha256(PRE_OPEN_RELEASE),
        "simulator_sha256": sha256(SIMULATOR),
        "candidate_frames": dict(sorted(captured.items())),
        "capture_commands_sha256": sha256(COMMANDS),
        "counts": {"new_frames": 60, "scenes": 12, "views_per_scene": 5,
                   "development_frames_reused": 0},
        "truth_imported": False,
        "estimator_imported": False,
        "volume_results_present": False,
    }
    ACQUISITION.write_text(json.dumps(acquisition, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return acquisition


def validate_acquisition():
    protocol, manifest = verify_preopen(require_pristine=False)
    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    commands = json.loads(COMMANDS.read_text(encoding="utf-8"))
    expected_sequences = [item["sequence"] for item in protocol["candidate"]["captures"]]
    scene_ids = [scene["id"] for scene in protocol["scenes"]]
    frame_paths = list(FRAMES.rglob("*.bin"))
    recorded = acquisition["candidate_frames"]
    headers_ok = True
    hashes_ok = True
    for scene in protocol["scenes"]:
        for capture_spec in protocol["candidate"]["captures"]:
            path = FRAMES / scene["id"] / f"candidate-{capture_spec['sequence']}.bin"
            key = relative(path)
            try:
                header = validate_frame_header(path.read_bytes(), capture_spec)
                headers_ok &= recorded[key]["header"] == header
                hashes_ok &= recorded[key]["sha256"] == sha256(path)
            except (KeyError, OSError, RuntimeError):
                headers_ok = False
                hashes_ok = False
    result_files = [path for path in RESULTS.rglob("*") if path.is_file()] if RESULTS.exists() else []
    checks = {
        "pre_open_hash_chain_verified": acquisition["pre_open_manifest_sha256"] == sha256(PRE_OPEN),
        "protocol_hash_matches": acquisition["protocol_sha256"] == sha256(PROTOCOL),
        "simulator_hash_matches": acquisition["simulator_sha256"] == sha256(SIMULATOR),
        "exactly_60_new_frames": len(frame_paths) == len(recorded) == 60,
        "exactly_12_scenes": sorted(path.name for path in FRAMES.iterdir() if path.is_dir()) == sorted(scene_ids),
        "five_frames_each": all(len(list((FRAMES / scene_id).glob("*.bin"))) == 5 for scene_id in scene_ids),
        "only_sequences_701_705": sorted({item["header"]["sequence"] for item in recorded.values()}) == expected_sequences,
        "headers_poses_crc_valid": headers_ok,
        "frame_hashes_match": hashes_ok,
        "capture_command_count_60": len(commands) == 60,
        "capture_commands_hash_matches": acquisition["capture_commands_sha256"] == sha256(COMMANDS),
        "no_development_frames_reused": acquisition["counts"]["development_frames_reused"] == 0,
        "no_truth_or_estimator_used": not acquisition["truth_imported"] and not acquisition["estimator_imported"],
        "no_results_or_scores": not result_files and not acquisition["volume_results_present"],
        "scene_table_unchanged": len(protocol["scenes"]) == 12,
        "frozen_files_unchanged": all(sha256(ROOT / name) == digest
                                       for name, digest in manifest["frozen_files"].items()),
    }
    validation = {
        "experiment_id": "R-007",
        "checked_at_utc": utc_now(),
        "phase": "AWAITING_INDEPENDENT_SCORE_RELEASE",
        "passed": all(checks.values()),
        "checks": checks,
        "protocol_sha256": sha256(PROTOCOL),
        "pre_open_manifest_sha256": sha256(PRE_OPEN),
        "acquisition_manifest_sha256": sha256(ACQUISITION),
        "capture_commands_sha256": sha256(COMMANDS),
    }
    ACQUISITION_VALIDATION.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not validation["passed"]:
        raise RuntimeError("R007 acquisition validation failed")
    return validation


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("verify-preopen", "capture", "validate"))
    args = parser.parse_args()
    if args.phase == "verify-preopen":
        protocol, manifest = verify_preopen(require_pristine=True)
        print(json.dumps({"experiment_id": protocol["experiment_id"],
                          "pre_open_manifest_sha256": sha256(PRE_OPEN),
                          "frozen_file_count": len(manifest["frozen_files"]),
                          "ready_for_independent_review": True}, indent=2))
    elif args.phase == "capture":
        print(json.dumps(capture(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(validate_acquisition(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
