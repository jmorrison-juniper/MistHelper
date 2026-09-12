# Systematic Test Mode

## Running Tests

### Automated Safe-Operation Test (`--test`)

Behavior:
- Dynamically enumerates safe menu items (GET, non-interactive, non-destructive)
- Skips heavy, WIP, interactive, WebSocket, continuous, destructive operations (documented inline in code)
- Executes in optimized order (fastest endpoints first) to minimize cumulative runtime
- Saves partial results even on rate limiting or exceptions

You can combine with `--output-format sqlite` and `--fast`:
```bash
python MistHelper.py --test --output-format sqlite --fast
```

### Unit Tests (Offline, No Credentials Required)

Run the offline unit test suite -- no API token or network access needed:

```bash
python -m pytest tests/unit/ -v
```

Tests cover data processing utilities, telemetry event schemas, primary key strategy validation, and configuration helpers. All tests complete in under 30 seconds.

## NDJSON Test Event Output

Both `--test` and `--testinteractive` emit structured NDJSON events to timestamped files:

```text
data/test_events_YYYYMMDD_HHMMSS.jsonl
```

Each line is a self-contained JSON object with fields: `event_type`, `timestamp`, `menu_option`, `status`, `duration_seconds`. AI agents and CI pipelines can parse results without regex.

## Comparing Test Runs

Use the comparison utility to detect regressions between two test runs:

```bash
python scripts/compare_test_runs.py data/test_events_20260311_143000.jsonl data/test_events_20260312_100000.jsonl
```

The report flags new failures, resolved failures, and timing regressions (>2x slower). Exit code 1 if regressions are found.

## CI Pipeline

Unit tests run automatically in GitHub Actions on every push. The pipeline has three sequential jobs: `validate` (syntax check) -> `test` (pytest) -> `build-and-push` (container image). Test failures block container deployment.

### Quality Gates

Every PR runs these checks in parallel via GitHub Actions:

| Gate | Tool | Threshold |
|------|------|-----------|
| Lint | Ruff | Zero violations |
| Type Check | mypy --strict | Phased enforcement |
| Tests | pytest + coverage | >= 80% |
| Security | Bandit | Zero findings |
| Dependencies | pip-audit | Zero vulnerabilities |
