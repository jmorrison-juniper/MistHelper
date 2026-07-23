# MistHelper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-07-14

## Active Technologies
- Python 3.13+ (per constitution and `pyproject.toml` py313 target). + mistapi 0.63.1+, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added). (1020-safe-test-clean-run)
- N/A (no schema changes; existing JSONL telemetry under `data/` via `TelemetryEmitter`, unchanged shape — see `data-model.md` §3). (1020-safe-test-clean-run)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`) + Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.63.1` (the verified installed surface is `0.63.3`) (1021-testinteractive-reliability-defects)
- Local append-only JSONL telemetry only; future interactive-test artifacts must remain under an explicitly controlled `data/` subdirectory. No remote persistence or mutations. (1021-testinteractive-reliability-defects)

- Python 3.13 (matches project constitution binding minimum). (1019-test-quality-analyzer)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.13 (matches project constitution binding minimum).: Follow standard conventions

## Recent Changes
- 1021-testinteractive-reliability-defects: Added Python 3.13+ (`pyproject.toml` requires `>=3.13`) + Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.63.1` (the verified installed surface is `0.63.3`)
- 1020-safe-test-clean-run: Added Python 3.13+ (per constitution and `pyproject.toml` py313 target). + mistapi 0.63.1+, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added).

- 1019-test-quality-analyzer: Added Python 3.13 (matches project constitution binding minimum).

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
