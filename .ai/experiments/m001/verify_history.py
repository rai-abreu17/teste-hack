"""Check historical artifacts against their already-recorded hashes; no recapture."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.ai/runs/m001-r005-r006/integrity.json'


def main():
    original_path = ROOT / '.ai/runs/m001-implementation/results/hash-manifest.json'
    audit_path = ROOT / '.ai/runs/m001-evaluation/results/attribution.json'
    original = json.loads(original_path.read_text(encoding='utf-8'))
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    expected = {**original['files'], **audit['historical_hashes_unchanged'],
                **audit['frame_hashes'], **audit['audit_source_hashes']}
    normalized = {}
    for name, checksum in expected.items():
        path = ROOT / name
        key = path.relative_to(ROOT).as_posix()
        if key in normalized and normalized[key] != checksum:
            raise AssertionError(f'Conflicting historical hash: {key}')
        normalized[key] = checksum
    mismatches = []
    for name, checksum in normalized.items():
        path = ROOT / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != checksum:
            mismatches.append({'path': name, 'expected': checksum, 'actual': actual})
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'historical_artifacts_checked': len(normalized),
              'sources': [str(original_path.relative_to(ROOT)), str(audit_path.relative_to(ROOT))],
              'mismatches': mismatches, 'passed': not mismatches}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
