# Systematic Test Mode

## Running Tests

### Automated Safe-Operation Test (`--test`)

Behavior:
- Dynamically enumerates the 73 `safe` menu items from `src/utils/operation_registry.py`
- Skips resource-intensive, interactive, WebSocket, continuous-loop, and destructive operations
- Executes in optimized order (fastest endpoints first) to minimize cumulative runtime
- Saves partial results even on rate limiting or exceptions

You can combine with `--output-format sqlite` and `--fast`:
```bash
python MistHelper.py --test --output-format sqlite --fast
```

### Unit Tests (Offline, No Credentials Required)

Run the offline unit test suite. It needs no API token or network access.

```bash
python -m pytest tests/unit/ -v
```

Tests cover data processing utilities, telemetry event schemas, primary key strategy validation, and configuration helpers.

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

GitHub Actions runs the quality gates on pull requests and on pushes to `main`.
The container build uses a separate workflow.

### Quality Gates

Every pull request runs these checks through GitHub Actions:

| Gate | Tool | Threshold |
|------|------|-----------|
| Lint | Ruff | Zero violations |
| Type Check | mypy --strict | Phased enforcement |
| Tests | pytest + coverage | >= 80% |
| Security | Bandit | Zero findings |
| Dependencies | pip-audit | Zero vulnerabilities |
| Format | Black | Zero files need formatting |
| Complexity | Radon | No block above the configured limit |
| Dead code | Vulture | Zero findings above the configured confidence |
| Documentation | pydocstyle and interrogate | Style passes and docstring coverage meets the threshold |
| Diagram references | Diagram and Mermaid linters | Every reference resolves and every Mermaid block parses |
| Ops portal | npm | Audit, type check, lint, and tests pass |
