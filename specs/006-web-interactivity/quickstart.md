# Quickstart: Web Portal Interactivity

**Feature**: 006-web-interactivity  
**Branch**: `006-web-interactivity`

## Developer Setup

```powershell
# 1. Switch to feature branch
git checkout 006-web-interactivity

# 2. Activate venv (Windows 11 standard environment)
.venv\Scripts\Activate.ps1

# 3. Install dependencies (no new deps for this feature)
uv pip install -r requirements.txt

# 4. Run locally
python MistHelper.py
# Open http://localhost:8055 in browser
```

## Architecture Overview

```text
Browser (operations.html)
  │
  ├── GET /api/operations/parameters/{menu}  → ParameterRegistry lookup
  │     Returns parameter definitions → JS renders form controls
  │
  ├── GET /api/operations/sites              → Mist API (org sites)
  │     Populates site dropdown
  │
  ├── GET /api/operations/sites/{id}/devices → Mist API (site devices)
  │     Populates device dropdown (after site selection)
  │
  ├── POST /api/operations/run               → OperationExecutor
  │     Sends {menu_number, parameters: {input_answers: [...]}}
  │     │
  │     └── web_input_context(answers)       → InputInterceptor
  │           Sets thread-local deque
  │           │
  │           └── func()                     → MistHelper operation
  │                 Calls input() → builtins.input → _patched_input()
  │                 Pops answer from deque
  │
  └── EventSource /api/operations/stream     → SSE (existing)
        Real-time log + completion events

Browser (data_browser.html / operations.html)
  │
  └── Preview button → Bootstrap 5 modal
        GET /api/data/preview/{path}         → DataBrowserService (existing)
        Paginated table with search/sort/export
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `web_portal/services/operation.py` | Add `PARAMETER_REGISTRY`, expand `get_operation_parameters()`, use `web_input_context` in `_execute_operation()` |
| `web_portal/services/input_hook.py` | **NEW**: `InputInterceptor` class with `install()`, `web_input_context()` |
| `web_portal/services/security.py` → `config.py` | Rename, merge `ThemeManager` from `theme.py` |
| `web_portal/routes/operations.py` | Add `/api/operations/sites`, `/api/operations/sites/<id>/devices`, `/api/operations/sites/<id>/clients` endpoints |
| `web_portal/static/js/operations.js` | Extend parameter rendering (dropdowns, dependency chains) |
| `web_portal/static/js/data_preview.js` | **NEW**: Modal preview component (shared between pages) |
| `web_portal/templates/data_browser.html` | Replace inline preview with modal |
| `web_portal/templates/operations.html` | Add modal include, parameter form area already exists |
| `web_portal/templates/base.html` | Add `data_preview.js` script include |
| `web_portal/app.py` | Call `InputInterceptor.install()` at startup, update imports for config.py |

## Testing

```powershell
# Run automated tests
python MistHelper.py --test

# Manual verification
# 1. Open http://localhost:8055/operations
# 2. Select Menu 31 (Site device list)
# 3. Verify site dropdown appears
# 4. Select a site, click Run
# 5. Verify operation completes with log output

# 6. Open http://localhost:8055/data
# 7. Click Preview on a CSV file
# 8. Verify modal appears with sortable, searchable table
# 9. Press Escape — verify modal closes, page unchanged
```
