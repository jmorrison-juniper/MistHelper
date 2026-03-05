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
- 006-web-interactivity: Added `builtins.input` monkeypatch with `threading.local()` for input interception, `InputInterceptor` class, `PARAMETER_REGISTRY`, Bootstrap 5 modal preview, new API endpoints for sites/devices/clients
- 005-web-portal: Added Python 3.13+ + Flask (already transitive via Dash — becomes direct), Gunicorn (new), Flask-SocketIO (new, WebSocket support), Bootstrap 5 (new, frontend CSS/JS), Jinja2 (already transitive via Flask)
- 004-god-class-decomposition: Added Python 3.13+ + mistapi >= 0.59.0 (Mist API SDK), internal classes (`APIDataFetcher`, `DataExporter`, `DataProcessingUtils`, `TimeUtils`, `ConfigUtils`, `WebSocketCommands`, `FirmwareManager`)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
