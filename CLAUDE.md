# MistHelper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-07-14

## Active Technologies
- Python 3.13+ (per constitution and `pyproject.toml` py313 target). + mistapi 0.63.1+, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added). (1020-safe-test-clean-run)
- N/A (no schema changes; existing JSONL telemetry under `data/` via `TelemetryEmitter`, unchanged shape — see `data-model.md` §3). (1020-safe-test-clean-run)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`) + Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.63.1` (the verified installed surface is `0.63.3`) (1021-testinteractive-reliability-defects)
- Local append-only JSONL telemetry only; future interactive-test artifacts must remain under an explicitly controlled `data/` subdirectory. No remote persistence or mutations. (1021-testinteractive-reliability-defects)
- Python 3.13+ (per constitution binding minimum and + stdlib only. `socket` (existing), `struct` (new use (1023-probe-tailored-synthetic-tests)
- Local append-only JSON files under `data/`: (1023-probe-tailored-synthetic-tests)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`; + Standard library only (`logging`, `pathlib`, (1024-vpn-icmp-reachability)
- Local append-only JSONL under `data/` for US3 (1024-vpn-icmp-reachability)
- Python 3.13+ (constitution binding minimum; per `pyproject.toml` py313 target) + Standard library only (`logging`, `pathlib`, `re`, `json`); no new dependencies (1025-probe-emission-log-fixes)
- No persistent state beyond the existing JSONL telemetry pattern; load-time dedup state is per-invocation `set[str]` in memory only (FR-012) (1025-probe-emission-log-fixes)
- Python 3.13+ (per constitution binding minimum + `mistapi >= 0.63.1` (verified installed (1029-ap-profile-migration)
- Local files under `data/` only. (1029-ap-profile-migration)
- Python 3.13+ + `mistapi>=0.63.1`, `python-dotenv`, `PyYAML`, `structlog`, existing MistHelper utility modules (`InputUtils`, `DataExporter`) (671-mist-get-site-beacon)
- CSV files under `data/`, SQLite (`data/mist_data.db`), optional ArangoDB + Redis through `DatabaseRouter` (671-mist-get-site-beacon)
- Python 3.13+ + `mistapi` 0.63.3, Flask 3.x, `flask-wtf`, `redis`, `python-arango` through `DatabaseRouter` (1823-upgrade-capture-portal)
- ArangoDB primary (collections `upgrade_captures`, `upgrade_runs`, edge `capture_for_run`, all `natural_pk`); Redis for the site lock only; CSV under `data/` as fallback (1823-upgrade-capture-portal)
- New package `src/upgrade_portal/` on port 8056 (`CAPTURE_PORT`). Menu 239 and the `--capture-portal` flag both start it (1823-upgrade-capture-portal)

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
- 1823-upgrade-capture-portal: New package `src/upgrade_portal/` (outside `web_portal/`, which ruff and mypy exclude) on port 8056; new upgrade seam `src/firmware/upgrade_service.py`; menu 239; 30-second JSON poll instead of server-sent events; Redis site lock.
- 671-mist-get-site-beacon: Added Python 3.13+ + `mistapi>=0.63.1`, `python-dotenv`, `PyYAML`, `structlog`, existing MistHelper utility modules (`InputUtils`, `DataExporter`)
- 1029-ap-profile-migration: Added menus 207 (migrate APs between device profiles) and 208 (revert); writes JSON backup and JSONL audit under `data/`.

<!-- MANUAL ADDITIONS START -->

## Writing Style: Simplified Technical English (STE)

All documentation, code comments, pull request text, error messages, user-facing
communication and printed output, and agent output MUST follow the Simplified
Technical English writing guide at `documentation/ASD-STE100_writing-guide.md`
(distilled from ASD-STE100 Issue 9).

Core defaults: one word = one meaning; one term per concept, reused consistently
(no synonym swapping); active voice; simple tenses; short sentences (<=20 words for
instructions, <=25 for descriptions); imperative for instructions with one action
per step and the condition first ("If X, do Y"); no semicolons, slang, jargon,
phrasal verbs, or Latin abbreviations (e.g./i.e./etc.); American spelling; never
alter quoted strings or identifiers. Warnings lead with a signal word (Warning =
harm/irreversible; Caution = recoverable) and state the specific consequence.

### Precedence: STE outranks caveman

STE outranks the caveman compression rules in
`.github/instructions/caveman.instructions.md`. If the two rule sets conflict,
obey STE. STE is NON-NEGOTIABLE. Caveman is a preference.

Caveman may remove filler, pleasantries, and hedging. Caveman must not drop an
article, write a fragment, swap a synonym, or use slang. Use the caveman `lite`
level, because it is the only level that obeys STE.

<!-- MANUAL ADDITIONS END -->
