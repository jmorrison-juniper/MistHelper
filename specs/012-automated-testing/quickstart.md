# Quickstart: Automated Testing Infrastructure

**Feature**: 012-automated-testing

## Running Unit Tests (Offline)

No API credentials or network access needed.

```powershell
# From project root (Windows local dev)
.venv\Scripts\Activate.ps1
python -m pytest tests/unit/ -v
```

Expected output:

```text
tests/unit/test_data_processing.py::test_flatten_dict_simple PASSED
tests/unit/test_data_processing.py::test_flatten_dict_nested PASSED
tests/unit/test_config_utils.py::test_check_stop_signal_no_file PASSED
tests/unit/test_pk_strategies.py::test_all_strategies_valid PASSED
tests/unit/test_telemetry.py::test_emit_event_format PASSED
...
```

All tests must pass in under 30 seconds.

## Running Live End-to-End Tests

Requires valid `.env` file with Mist API credentials.

```powershell
# Systematic test (all non-destructive ops)
python MistHelper.py --test

# Interactive test (includes site-dependent ops)
python MistHelper.py --testinteractive
```

Results are written to:
- Console: Human-readable summary (existing behavior)
- `data/test_events_YYYYMMDD_HHMMSS.jsonl`: Machine-readable NDJSON events

## Reading Test Results

```powershell
# View all failures
python -c "import json; [print(json.dumps(e, indent=2)) for e in (json.loads(l) for l in open('data/test_events_20260311_143000.jsonl')) if e.get('status')=='fail']"

# View summary
python -c "import json; [print(json.dumps(e, indent=2)) for e in (json.loads(l) for l in open('data/test_events_20260311_143000.jsonl')) if e['event_type']=='test_summary']"
```

## Comparing Test Runs

```powershell
python scripts/compare_test_runs.py data/test_events_RUN_A.jsonl data/test_events_RUN_B.jsonl
```

Output shows: new failures, resolved failures, and timing regressions (>2x slower).

## CI Pipeline

Unit tests run automatically in GitHub Actions on every push to `main` and on pull requests. The container build is gated on test success — if any unit test fails, the container is not built or pushed.

No configuration needed. The workflow at `.github/workflows/container-build.yml` handles everything.

## Adding Tests for New Operations

1. If the operation is non-destructive: it is automatically included in `--test` runs (no action needed)
2. If the operation is destructive: add it to `OperationRegistry` with `category="destructive"` and a `skip_reason`
3. For new utility functions: add unit tests to the appropriate file in `tests/unit/`
