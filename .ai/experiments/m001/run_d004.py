"""Prepare and acquire D004 without reconstructing or scoring any scene.

The runner has deliberately narrow responsibilities:

* verify the frozen protocol and every frozen source;
* prove the archived K4 and sequence-101 centre-frame identities;
* write the pre-acquisition manifest before starting the simulator;
* acquire only the four candidate diagonal views for each scene; and
* validate frame envelopes, headers, poses, sequences, CRCs and hashes.

It never imports an estimator or scene truth.  D004 reconstruction and volume
scoring remain unavailable until an independent review releases that phase.
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
SOURCE = ROOT / ".ai/runs/m001-implementation/results"
RUN = ROOT / ".ai/runs/m001-d004"
FRAMES = RUN / "frames"
BIN = ROOT / ".ai/runs/m001-implementation/bin/scene_dump_m001.exe"
PROTOCOL_PATH = HERE / "protocol_d004.json"
PROTOCOL_HASH_PATH = HERE / "protocol_d004.sha256"
PRE_MANIFEST = RUN / "pre-acquisition-manifest.json"
COMMANDS_PATH = RUN / "capture-commands.json"
ACQUISITION_MANIFEST = RUN / "acquisition-manifest.json"
VALIDATION_PATH = RUN / "acquisition-validation.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def load_protocol():
    expected = PROTOCOL_HASH_PATH.read_text(encoding="utf-8").split()[0]
    actual = sha256(PROTOCOL_PATH)
    if actual != expected:
        raise RuntimeError(f"frozen D004 protocol hash mismatch: {actual} != {expected}")
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    for name, checksum in protocol["frozen_sources"].items():
        path = ROOT / name
        actual_source = sha256(path) if path.is_file() else None
        if actual_source != checksum:
            raise RuntimeError(f"frozen source mismatch: {name}")
    return protocol, actual


def archived_command_map():
    records = json.loads((SOURCE / "capture-commands.json").read_text(encoding="utf-8"))
    return {
        Path(record["stdout_path"]).as_posix(): record
        for record in records
        if record.get("kind") == "capture" and record.get("stdout_path")
    }


def validate_frame_header(raw, expected_capture):
    if len(raw) != 704 or raw[:6] != b"BFLD\x02\x01":
        raise RuntimeError("invalid D004 frame envelope or identity")
    header_size, = struct.unpack_from("<H", raw, 6)
    sequence, _start_ms, duration_ms = struct.unpack_from("<IQI", raw, 8)
    cols, rows, record_size, geometry_version = struct.unpack_from("<HHHH", raw, 24)
    pose = struct.unpack_from("<6f", raw, 32)
    range_mm, payload_size, crc = struct.unpack_from("<HHI", raw, 56)
    actual_crc = zlib.crc32(raw[64:], zlib.crc32(raw[:60]))
    if not (header_size == 64 and duration_ms == 100 and cols == rows == 8
            and record_size == 10 and geometry_version == 3 and range_mm == 4000
            and payload_size == 640 and actual_crc == crc):
        raise RuntimeError("invalid D004 frame header or CRC")
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


def verify_archived_inputs(protocol):
    commands = archived_command_map()
    selected, aliases = {}, {}
    for scene in protocol["scenes"]:
        scene_id = scene["id"]
        center = SOURCE / "frames" / scene_id / "baseline_fixed1-1.bin"
        center_alias = SOURCE / "frames" / scene_id / "fixed3-1.bin"
        center_key, alias_key = relative(center), relative(center_alias)
        if center.read_bytes() != center_alias.read_bytes():
            raise RuntimeError(f"centre seq101 identity failed: {scene_id}")
        for path in (center, center_alias):
            command = commands.get(relative(path))
            if command is None or command["stdout_sha256"] != sha256(path):
                raise RuntimeError(f"archived command/hash mismatch: {relative(path)}")
        expected_center = protocol["arms"][0]["captures"][-1]
        header = validate_frame_header(center.read_bytes(), expected_center)
        selected[center_key] = {"sha256": sha256(center), "role": "shared_center_seq101",
                                "header": header}
        aliases[alias_key] = {"sha256": sha256(center_alias), "identical_to": center_key}

        for index, capture in enumerate(protocol["arms"][0]["captures"][:4], start=1):
            path = SOURCE / "frames" / scene_id / f"translated4_corners_level-{index}.bin"
            key = relative(path)
            command = commands.get(key)
            if command is None or command["stdout_sha256"] != sha256(path):
                raise RuntimeError(f"archived K4 command/hash mismatch: {key}")
            selected[key] = {"sha256": sha256(path), "role": "control_k4",
                             "header": validate_frame_header(path.read_bytes(), capture)}
    if len(selected) != 45 or len(aliases) != 9:
        raise RuntimeError("D004 requires exactly 45 selected archived frames and 9 aliases")
    return selected, aliases


def prepare():
    protocol, protocol_hash = load_protocol()
    if any(FRAMES.rglob("*.bin")):
        raise RuntimeError("candidate frames already exist; refusing to create a late pre-manifest")
    selected, aliases = verify_archived_inputs(protocol)
    files = {
        relative(PROTOCOL_PATH): protocol_hash,
        relative(PROTOCOL_HASH_PATH): sha256(PROTOCOL_HASH_PATH),
        **protocol["frozen_sources"],
    }
    manifest = {
        "experiment_id": "D-004",
        "created_at_utc": utc_now(),
        "phase": "before candidate acquisition and before all scoring",
        "protocol_sha256": protocol_hash,
        "frozen_files": dict(sorted(files.items())),
        "selected_archived_frames": dict(sorted(selected.items())),
        "centre_identity_aliases": dict(sorted(aliases.items())),
        "counts": {"selected_archived_frames": len(selected), "control_k4": 36,
                   "shared_centres": 9, "centre_aliases_checked": len(aliases),
                   "candidate_frames_existing": 0},
        "truth_or_estimator_used": False,
    }
    RUN.mkdir(parents=True, exist_ok=True)
    if PRE_MANIFEST.exists():
        raise RuntimeError(f"refusing to overwrite pre-manifest: {PRE_MANIFEST}")
    PRE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return manifest


def capture_candidate():
    protocol, protocol_hash = load_protocol()
    if not PRE_MANIFEST.is_file():
        raise RuntimeError("pre-acquisition manifest must exist before capture")
    pre = json.loads(PRE_MANIFEST.read_text(encoding="utf-8"))
    if pre["protocol_sha256"] != protocol_hash or pre["truth_or_estimator_used"]:
        raise RuntimeError("invalid pre-acquisition manifest")
    current_selected, current_aliases = verify_archived_inputs(protocol)
    if current_selected != pre["selected_archived_frames"] or current_aliases != pre["centre_identity_aliases"]:
        raise RuntimeError("archived inputs changed after pre-registration")
    if any(FRAMES.rglob("*.bin")) or COMMANDS_PATH.exists() or ACQUISITION_MANIFEST.exists():
        raise RuntimeError("refusing to overwrite D004 acquisition artifacts")

    candidate = protocol["arms"][1]
    commands, captured = [], {}
    for scene in protocol["scenes"]:
        scene_dir = FRAMES / scene["id"]
        scene_dir.mkdir(parents=True, exist_ok=False)
        for capture_spec in candidate["captures"][:4]:
            sequence = capture_spec["sequence"]
            output = scene_dir / f"candidate_diagonals-{sequence}.bin"
            command = [
                str(BIN), str(scene["fill"]), str(scene["shape"]), str(scene["cx"]),
                str(scene["obstacle"]), str(scene["dropout"]), str(protocol["range_m"]),
                str(sequence), str(capture_spec["yaw_deg"]), str(capture_spec["tilt_deg"]),
                str(capture_spec["origin"][2]), str(capture_spec["origin"][0]),
                str(capture_spec["origin"][1]),
            ]
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       check=False)
            record = {
                "kind": "candidate_capture",
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
                raise RuntimeError(f"candidate capture failed: {scene['id']} seq{sequence}")
            header = validate_frame_header(completed.stdout, capture_spec)
            output.write_bytes(completed.stdout)
            captured[relative(output)] = {"sha256": sha256(output), "scene_id": scene["id"],
                                          "header": header}
    if len(captured) != 36:
        raise RuntimeError(f"expected 36 candidate frames, got {len(captured)}")
    COMMANDS_PATH.write_text(json.dumps(commands, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    manifest = {
        "experiment_id": "D-004",
        "created_at_utc": utc_now(),
        "phase": "acquisition complete; reconstruction and volume scoring not run",
        "protocol_sha256": protocol_hash,
        "pre_acquisition_manifest_sha256": sha256(PRE_MANIFEST),
        "simulator_sha256": sha256(BIN),
        "candidate_frames": dict(sorted(captured.items())),
        "counts": {"new_candidate_frames": len(captured), "reused_control_frames": 36,
                   "reused_shared_centres": 9, "total_inputs_per_arm": 45},
        "capture_commands_sha256": sha256(COMMANDS_PATH),
        "truth_or_estimator_used": False,
        "volume_results_present": False,
    }
    ACQUISITION_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
    return manifest


def validate_acquisition():
    protocol, protocol_hash = load_protocol()
    pre = json.loads(PRE_MANIFEST.read_text(encoding="utf-8"))
    acquisition = json.loads(ACQUISITION_MANIFEST.read_text(encoding="utf-8"))
    selected, aliases = verify_archived_inputs(protocol)
    checks = {
        "protocol_hash_matches": pre["protocol_sha256"] == protocol_hash == acquisition["protocol_sha256"],
        "pre_manifest_unchanged": acquisition["pre_acquisition_manifest_sha256"] == sha256(PRE_MANIFEST),
        "frozen_sources_unchanged": all(sha256(ROOT / name) == checksum
                                        for name, checksum in protocol["frozen_sources"].items()),
        "archived_45_unchanged": selected == pre["selected_archived_frames"],
        "centre_9_identity_pairs_unchanged": aliases == pre["centre_identity_aliases"],
        "candidate_frame_count_36": len(acquisition["candidate_frames"]) == 36,
        "candidate_hashes_match": all(sha256(ROOT / name) == item["sha256"]
                                      for name, item in acquisition["candidate_frames"].items()),
        "only_candidate_sequences_201_204": sorted({item["header"]["sequence"]
                                                     for item in acquisition["candidate_frames"].values()})
                                                == [201, 202, 203, 204],
        "no_truth_or_estimator_used": not pre["truth_or_estimator_used"]
                                      and not acquisition["truth_or_estimator_used"],
        "no_volume_results": not acquisition["volume_results_present"]
                             and not (RUN / "results").exists(),
        "reserved_r007_unused": "r007" not in " ".join(acquisition["candidate_frames"]).lower(),
    }
    result = {
        "experiment_id": "D-004",
        "checked_at_utc": utc_now(),
        "phase": "ready for independent pre-scoring review",
        "passed": all(checks.values()),
        "checks": checks,
        "counts": acquisition["counts"],
        "protocol_sha256": protocol_hash,
        "pre_acquisition_manifest_sha256": sha256(PRE_MANIFEST),
        "acquisition_manifest_sha256": sha256(ACQUISITION_MANIFEST),
        "capture_commands_sha256": sha256(COMMANDS_PATH),
    }
    VALIDATION_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    if not result["passed"]:
        raise RuntimeError("D004 acquisition validation failed")
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "capture", "validate", "all"))
    args = parser.parse_args()
    if args.phase in ("prepare", "all"):
        prepare()
    if args.phase in ("capture", "all"):
        capture_candidate()
    if args.phase in ("validate", "all"):
        result = validate_acquisition()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
