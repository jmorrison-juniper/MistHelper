# Quickstart: Validate the `echo()` Refactor

**Feature**: `1031-warning-echo-refactor`

This is a runnable validation guide. It proves the refactor met every success criterion in the spec. Run these steps end-to-end after `/speckit.implement` lands the change.

## Prerequisites

- Python 3.13+ installed and available on `PATH`.
- Repo checked out at branch `1031-warning-echo-refactor`.
- Working directory is the repo root.
- No `data/` cleanup required; the script log rotates naturally.

## Setup (once, before the refactor lands)

Capture the "before" baseline on `main`.

```bash
git checkout main
python MistHelper.py --test > /tmp/echo_refactor_before.stdout 2>&1
cp data/script.log /tmp/echo_refactor_before.log
grep -c "^.*WARNING - " /tmp/echo_refactor_before.log > /tmp/echo_refactor_before.warning_count
```

Expected baseline: `warning_count` in the low thousands (roughly 7,900 per the spec's SC-004).

## Run 1: Helper unit tests

Once `src/utils/console.py` and `tests/unit/utils/test_console.py` are in place, run:

```bash
cd src && pytest ../tests/unit/utils/test_console.py -v
```

**Expected**: all 5 tests pass. Every one of the contract clauses C-1 through C-5 is exercised.

If any test fails, do not proceed. The helper contract is broken and the migration is unsafe.

## Run 2: Full quality gate

```bash
cd src
ruff check .
black --check .
mypy .
pytest
pydocstyle
interrogate -c pyproject.toml
pydoclint --style=google .
radon cc . -a -nc
bandit -c pyproject.toml -r .
vulture .
pylint .
```

**Expected**: every gate green. No new waivers introduced by this refactor (FR-016).

## Run 3: Scripted end-to-end capture (after refactor lands)

Check out the refactor branch and re-run the same scripted session used for the baseline.

```bash
git checkout 1031-warning-echo-refactor
python MistHelper.py --test > /tmp/echo_refactor_after.stdout 2>&1
cp data/script.log /tmp/echo_refactor_after.log
```

## Gate: byte-identical stdout (SC-003)

```bash
diff /tmp/echo_refactor_before.stdout /tmp/echo_refactor_after.stdout
```

**Expected**: empty output. Exit code 0.

If the diff is non-empty, one of the 170 migrated sites changed message text, changed argument order, or dropped a call. Investigate the first differing hunk. Common failures:

- Missed a multi-line `logging.warning(...)` variant where the marker was on the closing `)` line — the rewrite tool skipped it, so the site still emits at WARNING (would show as a missing stdout line only if console handler is not at INFO — but WARNING >= INFO, so it should still print; the more likely cause is the tool corrupting an arg list).
- Corrupted a `%s` format string during rewrite (message text edit).

## Gate: WARNING channel is clean (SC-004)

```bash
grep -c "^.*WARNING - " /tmp/echo_refactor_after.log
```

**Expected**: a small number, bounded above by the count of genuine warnings raised during the scripted session. The spec quotes "~32" as the ceiling from static analysis of the tree; a realistic scripted run may hit only 2 or 3 of them.

Cross-check: every remaining WARNING line matches one of the known-legitimate causes (matplotlib import failure, UV package-manager error, requirements-file parse errors, mistapi access errors, tqdm fallback). Grep for menu-item, prompt, and progress text — none should appear at WARNING:

```bash
grep "WARNING - " /tmp/echo_refactor_after.log | grep -E "^.*(Menu|Report|Select|:  )"
```

**Expected**: empty. Any hit is a legacy site that escaped migration.

## Gate: marker is gone from the tree (SC-001)

```bash
grep -R "# Legacy console echo routed via logger\." src MistHelper.py
```

**Expected**: empty. Exit code 1.

## Gate: no legacy WARNING pattern remains (SC-002)

```bash
grep -Rn "logging.warning" src MistHelper.py | grep -F "Legacy console echo"
```

**Expected**: empty. Exit code 1.

## Gate: every migrated file imports from the same path (FR-011)

```bash
for f in \
  MistHelper.py \
  src/reports/e911_bssid.py \
  src/reports/offline_device_reporter.py \
  src/reports/global_wired_client_report_generator.py \
  src/reports/wired_client_manufacturer_report_generator.py \
  src/reports/sfp_transceiver_data_processor.py \
  src/auth/interactive/clouds.py; do
    echo -n "$f: "
    grep -c "from src.utils.console import echo" "$f"
done
```

**Expected**: every file reports `1`. Not zero (would mean the file uses `echo` without importing it — an `NameError` at runtime), not more than 1 (would mean duplicate import).

## Gate: legitimate warnings are still WARNING (FR-013)

Cross-check the count of remaining `logging.warning(` calls in the seven affected files.

```bash
grep -Rn "logging.warning(" \
  MistHelper.py \
  src/reports/e911_bssid.py \
  src/reports/offline_device_reporter.py \
  src/reports/global_wired_client_report_generator.py \
  src/reports/wired_client_manufacturer_report_generator.py \
  src/reports/sfp_transceiver_data_processor.py \
  src/auth/interactive/clouds.py \
  | wc -l
```

**Expected**: approximately 32 (per the input description). A materially different count is a red flag:

- Much lower (< 25): the migration script over-rewrote and touched calls without markers — restore from backup and fix the tool.
- Much higher (> 40): some legacy sites were missing markers and got left behind — audit the diff of the seven files and add echoes manually.

## Summary of expected outcomes

| Gate | Command | Expected |
|---|---|---|
| Unit tests | `pytest tests/unit/utils/test_console.py` | 5 pass |
| Full quality suite | `ruff / black / mypy / pytest / interrogate / pydoclint / radon / bandit / vulture / pylint` | all green |
| Byte-identical stdout | `diff before.stdout after.stdout` | empty |
| WARNING count drop | `grep -c WARNING - after.log` | small, bounded by real warnings |
| No menu text at WARNING | `grep WARNING - after.log \| grep -E "Menu\|Report\|Select"` | empty |
| Marker gone | `grep -R "# Legacy console echo routed via logger\." src MistHelper.py` | empty |
| Legacy pattern gone | `grep logging.warning ... \| grep Legacy console echo` | empty |
| Import present | `grep -c "from src.utils.console import echo" <file>` | 1 in every migrated file |
| Legitimate warnings preserved | `grep -c logging.warning( ...` | approximately 32 |

If every gate passes, the refactor met all seven success criteria (SC-001 through SC-007) and is ready to merge.
