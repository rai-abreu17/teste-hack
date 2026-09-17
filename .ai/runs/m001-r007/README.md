# M001-R007

This directory is at the **pre-open stop boundary**. Do not run capture or scoring until an independent reviewer releases the exact frozen manifest.

Frozen sources live under `.ai/experiments/m001/`:

- `protocol_r007.json` and `protocol_r007.sha256`: fixed candidate, 12-scene table, acquisition contract, metrics, and gate.
- `capture-plan-v2.json`: canonical structural plan tying every sequence to exact command and pose.
- `run_r007.py`: pre-open verification, one-shot 60-frame acquisition, and truth-free acquisition validation with structural equality.
- `run_r007_score.py`: one-shot truth-free reconstruction followed by evaluator-only truth scoring.
- `test_r007.py`: preregistration, isolation, gate, and integrity tests that do not capture or score.

The current files in this run directory are only preregistration artifacts. In particular, `frames/`, `results/`, `capture-commands.json`, `acquisition-manifest.json`, `acquisition-validation.json`, `validation.json`, and `REPORT.md` do not exist.

## Independent release sequence

1. Recalculate every entry in `pre-open-manifest.json`, confirm the no-artifact proof, inspect the fixed scene table and code, and create `independent-pre-open-release.json` with:

   ```json
   {
     "experiment_id": "R-007",
     "decision": "RELEASE_R007_OPEN",
     "pre_open_manifest_sha256": "<sha256 of pre-open-manifest.json>",
     "review_type": "automated-review",
     "reviewed_at_utc": "<ISO-8601 UTC>"
   }
   ```

2. Only after that release, run `python .ai/experiments/m001/run_r007.py capture` once, then `python .ai/experiments/m001/run_r007.py validate` once.
3. Automatically inspect the acquisition and its validation. Create `independent-score-release.json` with decision `RELEASE_R007_SCORE`, binding four hashes (`pre_open_manifest_sha256`, `capture_plan_sha256`, `acquisition_manifest_sha256`, `acquisition_validation_sha256`), review_type "automated-review", and UTC timestamp.
4. Only after the score release, run `python .ai/experiments/m001/run_r007_score.py` once.

The runners refuse overwrite. A failed or partial acquisition consumes this reserved matrix and must be reported; it must not be repaired by dropping scenes or generating replacement sequences.

## Safe pre-open checks

The following checks do not capture, reconstruct, import truth, or score:

```text
python -m unittest .ai/experiments/m001/test_r007.py
python .ai/experiments/m001/run_r007.py verify-preopen
```

R007 is SIMULATED. Even a pass does not establish physical or deployment performance.
