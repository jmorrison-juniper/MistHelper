# MistHelper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-07-14

## Active Technologies
- Python 3.13+ (per pyproject.toml `requires-python = ">=3.13"`) + mistapi >= 0.59.0 (Mist API SDK), python-dotenv >= 1.0.0 (001-radius-wlan-config)
- CSV export to `data/` directory for audit trail (001-radius-wlan-config)
- Python 3.13+ + mistapi >= 0.59.0 (002-bulk-radius-enhance)
- CSV audit trail in `data/` directory (002-bulk-radius-enhance)
- Python 3.13+ + mistapi >= 0.59.0 (Mist API SDK), `APIDataFetcher` (internal), `DataExporter` (internal), `DataProcessingUtils` (internal), `TimeUtils` (internal), `ConfigUtils` (internal) (003-menu1-compliance-refactor)
- CSV files in `data/` directory + SQLite (`data/mist_data.db`) via dual output backend (003-menu1-compliance-refactor)
- Python 3.13+ + mistapi >= 0.59.0 (Mist API SDK), internal classes (`APIDataFetcher`, `DataExporter`, `DataProcessingUtils`, `TimeUtils`, `ConfigUtils`, `WebSocketCommands`, `FirmwareManager`) (004-god-class-decomposition)
- Python 3.13+ + Flask (already transitive via Dash — becomes direct), Gunicorn (new), Flask-SocketIO (new, WebSocket support), Bootstrap 5 (new, frontend CSS/JS), Jinja2 (already transitive via Flask) (005-web-portal)
- SQLite (`data/mist_data.db`), CSV files in `data/`, browser localStorage (theme persistence) (005-web-portal)
- Python 3.13+ + Flask, Bootstrap 5 (already bundled), `builtins.input` monkeypatch with `threading.local()` for input interception (006-web-interactivity)
- CSV files in `data/`, SQLite (`data/mist_data.db`), browser localStorage (theme) (006-web-interactivity)
- Python 3.13+ (per constitution constraint) + FastAPI 0.115+, Celery 5.4+, SQLAlchemy 2.0+, (001-mist-ops-platform)
- PostgreSQL 16 (Zalando Operator for K8s HA), Redis 7 (Spotahome (001-mist-ops-platform)
- TypeScript 5.5+ (strict mode) + React 19, React Router 7, TanStack Query 5, Zustand 5, Tailwind CSS 4, Vite 6 (007-ops-frontend-portal)
- N/A (browser-only; all persistence via backend API) (007-ops-frontend-portal)
- Python 3.13+ + `json` (stdlib) for OpenAPI parsing; `pathlib` for file I/O; `re` for operationId-to-mistapi mapping (008-mist-api-docs)
- Filesystem — ~1,013 markdown files in `documentation/api/` subdirectories (008-mist-api-docs)
- Python 3.13+ (stdlib only — json, pathlib, re, logging, argparse) + None (reads existing markdown files and OpenAPI spec) (009-api-docs-enrichment)
- File system — reads/writes markdown files in documentation/api/{category}/ (009-api-docs-enrichment)
- N/A — this is documentation enrichment, not code development. The AI agent edits existing markdown files directly via tool calls. + None — reads existing markdown files and cross-references MistHelper.py source (009-api-docs-enrichment)
- File system — reads/writes markdown files in `documentation/api/{category}/` (009-api-docs-enrichment)
- Python 3.13+ (analysis target), no runtime code produced + Static code analysis of MistHelper.py (~44K lines), maps_manager.py, wsgi.py; enriched API docs (1,013 .md files in `documentation/api/`) (010-endpoint-usage-audit)
- Output as JSON + Markdown files in `specs/010-endpoint-usage-audit/` (010-endpoint-usage-audit)
- Python 3.13 + mistapi 0.60.4 (Mist API SDK), FastAPI, Celery, SQLAlchemy (011-mist-ops-api-audit)
- PostgreSQL 16, Redis 7 (011-mist-ops-api-audit)
- Python 3.13+ + mistapi 0.59+, pytest (new — unit tests only) (012-automated-testing)
- NDJSON files in `data/` directory (`test_events.jsonl`, timestamped variants) (012-automated-testing)
- Python 3.13+ (existing `requires-python = ">=3.13"`) + Ruff, mypy, pytest + pytest-cov, Bandit, pip-audit, Hypothesis, Playwright (dev); mistapi, Flask, Gunicorn, Dash (runtime) (013-ci-quality-pipeline)
- N/A (pipeline infrastructure, no new data storage) (013-ci-quality-pipeline)
- Python 3.13+ + mistapi 0.59+ (Mist API SDK), websocket-client (WebSocket connections), requests (HTTP fallback for non-SDK endpoints) (014-device-utility-commands)
- SQLite (`data/mist_data.db`) + CSV dual output via `DataExporter.write_with_format_selection()` (014-device-utility-commands)
- Python 3.13+ + `mistapi` 0.59+ (API access), `PrettyTable` (screen display), `csv` (stdlib, CSV output) (015-offline-device-report)
- CSV to `data/OfflineDeviceReport_YYYYMMDD_HHMMSS.csv`; SQLite via `DataExporter.write_with_format_selection()` (dual output) (015-offline-device-report)
- Mermaid (GitHub-rendered), Python 3.13 (CI lint script only) + GitHub Mermaid renderer (built-in), Mermaid syntax v11.x (016-mermaid-documentation-suite)
- N/A (documentation-only feature; no runtime data) (016-mermaid-documentation-suite)
- Python 3.13+ + mistapi >= 0.61.3 (Juniper Mist API SDK), websocket-client >= 1.8.0, sshkeyboard >= 2.3.1 (017-mistapi-upgrade-alignment)
- SQLite (`data/mist_data.db`) + CSV dual output via `DataExporter` (017-mistapi-upgrade-alignment)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (feat/018-ssid-template-consolidation)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (feat/018-ssid-template-consolidation)
- Python 3.13+ + mistapi 0.59+, pytest, sqlite3 (stdlib), csv (stdlib) (feat/73-audit-menu-12-org-inventory)
- SQLite (`data/mist_data.db`) + CSV (`data/OrgInventory.csv`) (feat/73-audit-menu-12-org-inventory)
- Python 3.13 + `mistapi` (target floor `>=0.61.4`), `websocket-client` (target floor `>=1.8.0`), `requests`, `python-dotenv` (001-mistapi-sdk-audit)
- N/A for the audit itself; existing MistHelper CSV/SQLite outputs remain unchanged (001-mistapi-sdk-audit)
- Python 3.13+ + `openai>=1.0` (AI API client, OpenAI-compatible surface for all 3 backends), `python-dotenv` (credential loading), `argparse` (stdlib, CLI flags) (183-mist-ideas-analyzer)
- JSON files in `data/mist_ideas_cache/` (per-idea cache + `api_index.json`); output to `data/mist_ideas_analysis.{md,json,csv}` (183-mist-ideas-analyzer)
- Python 3.13+ + `mistapi>=0.61.4`, existing MistHelper utilities (`ConfigUtils`, `InputUtils`, `DataExporter`, `DataProcessingUtils`) (001-wired-client-global-report)
- `data/` CSV exports and `data/mist_data.db` SQLite output via existing exporter flow (001-wired-client-global-report)
- Python 3.13+ + `mistapi>=0.61.4`, `python-arango>=8.3.2`, `redis>=7.4.0` (with hiredis) (184-polyglot-db-migration)
- ArangoDB 3.12 (documents + graph), Redis Stack (TimeSeries module), CSV files (always) (184-polyglot-db-migration)
- Python 3.13+ + mistapi 0.59+ (`orgs.deviceprofiles`, `orgs.vpns`) (186-wan-hub-group-number)
- N/A (no CSV/SQLite output — interactive display + API write only) (186-wan-hub-group-number)
- Python 3.13+ + `mistapi` 0.59+ (Mist API SDK) (187-wan-vpn-builder)
- N/A (API-only, no local persistence) (187-wan-vpn-builder)
- Python 3.13+ + `requests` (present), `subprocess` (stdlib), (189-quality-gate-remediation)
- N/A -- no data model or schema changes (189-quality-gate-remediation)
- Python 3.13+ + mistapi 0.59+, pytest/pytest-cov, ruff, black, mypy, tqdm, PrettyTable (main)
- CSV/SQLite/ArangoDB/Redis outputs via existing exporter flows, JSON report artifacts under `data/` (main)
- Python 3.13+ + `mistapi>=0.59`, `requests`, `python-dotenv`, `ruff`, `black`, `radon`, existing `src/*` extracted modules (feat/194-capture-bootstrap-session-refactor)
- CSV and SQLite outputs under `data/` (plus optional ArangoDB/Redis via existing exporter paths) (feat/194-capture-bootstrap-session-refactor)
- Python 3.13+ + `mistapi>=0.59`, `requests`, existing `src/*` extraction modules, `ruff`, `black`, `radon` (feat/194-capture-bootstrap-session-refactor)
- CSV/SQLite (plus existing optional ArangoDB/Redis paths) under `data/` (feat/194-capture-bootstrap-session-refactor)
- Python 3.13+ (per constitution and `pyproject.toml` py313 target). + mistapi 0.63.1+, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added). (1020-safe-test-clean-run)
- N/A (no schema changes; existing JSONL telemetry under `data/` via `TelemetryEmitter`, unchanged shape — see `data-model.md` §3). (1020-safe-test-clean-run)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`) + Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.63.1` (the verified installed surface is `0.63.3`) (1021-testinteractive-reliability-defects)
- Local append-only JSONL telemetry only; future interactive-test artifacts must remain under an explicitly controlled `data/` subdirectory. No remote persistence or mutations. (1021-testinteractive-reliability-defects)
- Python 3.13 (`pyproject.toml` target `py313`) + `bandit[toml]` (no new runtime dependency) (1032-bandit-severity-gate)
- N/A (comment and guard changes only) (1032-bandit-severity-gate)
- Python 3.13. The workstation interpreter is `.venv\Scripts\python.exe`. The global `python` on this machine is broken and must not run any gate command. + `pylint`, `vulture`, and the GitHub CodeQL Action v4. This work adds no dependency and pins no version. (1033-ci-gate-silencer-removal)
- N/A. The work changes two configuration files and one changelog file. (1033-ci-gate-silencer-removal)
- Python 3.13 or newer. The project interpreter is `.venv\Scripts\python.exe`. The global `python` on this machine is broken. + The standard library only. The change adds `collections.Counter` and no package. (990-redis-entity-id)
- Redis TimeSeries through the `redis-stack` service. The change adds no key, no index, and no migration. (990-redis-entity-id)
- Python 3.13+ + `mistapi>=0.63.1`, `python-dotenv`, `PyYAML`, `structlog`, existing MistHelper utility modules (`InputUtils`, `DataExporter`) (671-mist-get-site-beacon)
- CSV files under `data/`, SQLite (`data/mist_data.db`), optional ArangoDB + Redis through `DatabaseRouter` (671-mist-get-site-beacon)
- Python 3.13 or newer. The `pyproject.toml` file targets `py313`. + `mistapi>=0.63.1`. This feature adds no dependency. (1034-codeql-cleartext-logging)
- No database change. The verdict register is a Markdown file under (1034-codeql-cleartext-logging)
- Python 3.13+. `pyproject.toml` requires `>=3.13` and targets + `mistapi` 0.63.3 (installed and verified), Flask 3.x with (1823-upgrade-capture-portal)
- ArangoDB is the primary store, through (1823-upgrade-capture-portal)
- Python 3.13. + pytest, `mistapi` 0.63.3, and the shipped package (1992-upgrade-rehearsal)
- None. The harness holds the run record in memory. (1992-upgrade-rehearsal)
- Python 3.13 or newer + `mistapi>=0.64.0,<0.65`, Python logging, and the existing source dependency resolver (4030-fetcher-failure-contract)
- No product storage change. The portal regression uses a temporary directory for output evidence. (4030-fetcher-failure-contract)
- Python 3.13 or newer + Python `logging`, `threading`, `pathlib`, and `concurrent.futures`; Flask portal services; pytest (4024-portal-run-isolation)
- Existing shared `data/` filesystem output; existing in-memory operation run records; no database schema change (4024-portal-run-isolation)

- Python 3.13+ + mistapi>=0.59.0, python-dotenv>=1.0.0 (001-radius-wlan-config)
- Python 3.13+ (per constitution and `pyproject.toml` py313 target). + mistapi>=0.64.0,<0.65, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added). (1020-safe-test-clean-run)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`) + Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.64.0,<0.65` (1021-testinteractive-reliability-defects)
- Python 3.13+ (per constitution binding minimum and + stdlib only. `socket` (existing), `struct` (new use (1023-probe-tailored-synthetic-tests)
- Local append-only JSON files under `data/`: (1023-probe-tailored-synthetic-tests)
- Python 3.13+ (`pyproject.toml` requires `>=3.13`; + Standard library only (`logging`, `pathlib`, (1024-vpn-icmp-reachability)
- Local append-only JSONL under `data/` for US3 (1024-vpn-icmp-reachability)
- Python 3.13+ (constitution binding minimum; per `pyproject.toml` py313 target) + Standard library only (`logging`, `pathlib`, `re`, `json`); no new dependencies (1025-probe-emission-log-fixes)
- No persistent state beyond the existing JSONL telemetry pattern; load-time dedup state is per-invocation `set[str]` in memory only (FR-012) (1025-probe-emission-log-fixes)
- Python 3.13+ (per constitution binding minimum + `mistapi>=0.64.0,<0.65` (1029-ap-profile-migration)
- Local files under `data/` only. (1029-ap-profile-migration)
- Python 3.13+ + `mistapi>=0.64.0,<0.65`, `python-dotenv`, `PyYAML`, `structlog`, existing MistHelper utility modules (`InputUtils`, `DataExporter`) (671-mist-get-site-beacon)
- Python 3.13+ + `mistapi>=0.64.0,<0.65`, Flask 3.x, `flask-wtf`, `redis`, `python-arango` through `DatabaseRouter` (1823-upgrade-capture-portal)
- ArangoDB primary (collections `upgrade_captures`, `upgrade_runs`, edge `capture_for_run`, all `natural_pk`); Redis for the site lock only; CSV under `data/` as fallback (1823-upgrade-capture-portal)
- New package `src/interfaces/portals/upgrade_portal/` on port 8056 (`CAPTURE_PORT`). Menu 239 and the `--capture-portal` flag both start it (1823-upgrade-capture-portal)
- Python 3.13. + pytest, `mistapi>=0.64.0,<0.65`, and the shipped package (1992-upgrade-rehearsal)
- Python 3.13 (matches project constitution binding minimum). (1019-test-quality-analyzer)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.13+: Follow standard conventions

## Recent Changes
- 4030-fetcher-failure-contract: Added Python 3.13 or newer + `mistapi>=0.64.0,<0.65`, Python logging, and the existing source dependency resolver
- 4024-portal-run-isolation: Added Python 3.13 or newer + Python `logging`, `threading`, `pathlib`, and `concurrent.futures`; Flask portal services; pytest
- 1992-upgrade-rehearsal: Added Python 3.13. + pytest, `mistapi>=0.64.0,<0.65`, and the shipped package
- 1823-upgrade-capture-portal: New package `src/interfaces/portals/upgrade_portal/` (outside `web_portal/`, which ruff and mypy exclude) on port 8056; new upgrade seam `src/operations/execution/firmware/upgrade_service.py`; menu 239; 30-second JSON poll instead of server-sent events; Redis site lock.

<!-- MANUAL ADDITIONS START -->
## Where the rules live

This file holds the technology context that Spec Kit generates from each plan.
It holds no rule. `AGENTS.md` at the repository root holds the rules that apply
to each repository of this owner, and `.github/copilot-instructions.md` holds
the rules that apply to MistHelper only. Read the two files before you change
a file. If this file disagrees with one of them, obey that file.

Caution: this file carries a stale generation date and old dependency pins,
because each entry records the plan of one feature at its own time. Read the
current pin from `requirements.txt`, otherwise a change can target an old
`mistapi` release.
<!-- MANUAL ADDITIONS END -->
