# MistHelper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-03

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
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (095-audit-menu-8-show-ssrsrx-routing-table)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (095-audit-menu-8-show-ssrsrx-routing-table)

- Python 3.13+ + mistapi>=0.59.0, python-dotenv>=1.0.0 (001-radius-wlan-config)

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
- 001-export-beacons: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
- 095-audit-menu-8-show-ssrsrx-routing-table: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
- 017-mistapi-upgrade-alignment: Added Python 3.13+ + mistapi >= 0.61.3 (Juniper Mist API SDK), websocket-client >= 1.8.0, sshkeyboard >= 2.3.1


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
