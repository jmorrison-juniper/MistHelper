# Contract: E2E Diagnostics Artifact

**Owner**: `.github/workflows/ci.yml`, job `playwright_shards`, step `Upload shard diagnostics` (lines 939 to 947).

**Enforced by**: The guard class `EvidenceUploadAudit` in `tests/guardrails/test_e2e_shard_partition.py`, added by task T002.

**Consumer**: A maintainer who reads a failed or canceled E2E shard.

## Name and Trigger

- The artifact name starts with `e2e-diagnostics-`, followed by the shard name (line 942).
- The shard names are `upgrade-portal`, `web-portal`, and `websockets-tab`. Their matrix rows start at lines 793, 795, and 797.
- The step runs when `failure() || cancelled()` is true (line 939). A passing shard uploads no diagnostics artifact.

## Contents

| Path in the artifact | Written by | Present when |
|---|---|---|
| `test-artifacts/e2e-${{ matrix.shard }}.log` (line 944) | The `tee` output of the pytest step (line 909) | The pytest step ran |
| `test-artifacts/e2e-phase-trail.jsonl` (line 945) | The E2E run. The writer is not read in this record (U-6). | The E2E run wrote the file |
| `test-artifacts/issue-4229-browser/` (line 946) | Pytest-playwright output, set by `--output` (line 909) | A test failed. Each failed test keeps `test-failed-1.png` (`.venv` pytest-playwright, line 879) and `trace.zip` (line 895). |

## Reading Order

1. Open the failure screenshot in the folder of the failed test. It shows the page at the failure time.
2. Open `trace.zip` with the Playwright trace viewer. It lists each action and its error.
3. Search the shard log for the test name and for `FAILED`.
4. Read the traceback in the shard log, if the log has one.

Caution: a canceled shard log can lack the traceback text. Pytest prints failure details at the end of a run (`.venv` terminal summary, line 1037).

## Failure Modes

- Caution: a canceled shard can lose the traceback text. The failure screenshot and the trace remain.
- Warning: do not delete a diagnostics artifact before the issue records its trace. Deletion removes the only CI copy of that trace.
- The upload step sets `if-no-files-found: warn` (line 947). A missing file produces a warning, and the step does not fail.
- The upload step sets no retention period (lines 939 to 947). The retention setting is unverified (U-8).

## Guard Rules

The guard method `EvidenceUploadAudit.check_upload` asserts five rules:

1. The workflow holds exactly one step named `Upload shard diagnostics`.
2. The step condition equals `${{ failure() || cancelled() }}`.
3. The step paths hold `test-artifacts/issue-4229-browser/`.
4. The step paths hold `test-artifacts/e2e-${{ matrix.shard }}.log`.
5. The pytest step writes its output through `tee "test-artifacts/e2e-${E2E_SHARD}.log"`.

Each of the five rules has one mutation case in `test_a_missing_diagnostic_fails`. Rule 1 uses the `duplicate` case, and rule 5 uses the `tee` case.
