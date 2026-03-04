# Data Model: Web Portal Interface

**Feature**: 005-web-portal | **Date**: 2026-03-04

## Entities

### 1. DataFile

Represents a file in the `data/` directory available for browsing and download.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `name` | str | Filesystem | Filename (e.g., `site_inventory.csv`) |
| `path` | str | Filesystem | Relative path from `data/` |
| `size_bytes` | int | `os.stat()` | File size in bytes |
| `last_modified` | datetime | `os.stat().st_mtime` | Last modification timestamp |
| `file_type` | str | Extension | `csv`, `sqlite`, `log`, `json` |
| `is_directory` | bool | Filesystem | True for subdirectories |

**Validation rules**:
- Path must be within `data/` directory (no path traversal: reject `..` components)
- Only expose known file types: `.csv`, `.db`, `.sqlite`, `.log`, `.json`
- Hidden files (starting with `.`) are excluded

**No database table** — derived from filesystem at request time via `os.scandir()`.

---

### 2. Operation

Represents a MistHelper menu operation that can be executed from the portal.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `menu_number` | str | `menu_actions` dict key | Natural key (e.g., `"11"`) |
| `description` | str | `menu_actions` dict value[1] | Human-readable name |
| `category` | str | Derived from menu number range | e.g., "Data Extraction", "WebSocket Commands" |
| `is_safe` | bool | Derived | True for menus 1-89, False for 90+ |

**Category mapping** (derived from menu number ranges):

| Range | Category |
|-------|----------|
| 1-4 | Core Organization |
| 5-8 | WebSocket Device Commands |
| 9-10 | Packet Captures |
| 11-19 | Organization Exports |
| 20-28 | Location Exports |
| 29-34 | Site Data Exports |
| 35-39 | Template Exports |
| 40-41 | Statistics & Analytics |
| 42-48 | Security & Configuration |
| 49-62 | Site Config & Monitoring |
| 63-65 | Work In Progress |
| 66-89 | Insights & Diagnostics |

**No database table** — derived from `menu_actions` dictionary at startup.

---

### 3. OperationRun

Tracks an in-progress or completed operation execution triggered from the portal.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `run_id` | str | `uuid.uuid4()` | Unique run identifier |
| `menu_number` | str | User selection | Which operation to run |
| `description` | str | From `menu_actions` | Human-readable operation name |
| `status` | str | Runtime | `pending`, `running`, `completed`, `failed` |
| `started_at` | datetime | Runtime | When execution began |
| `completed_at` | datetime | Runtime | When execution finished (None if running) |
| `progress_pct` | int | Runtime | 0-100 progress percentage |
| `log_messages` | list[str] | Runtime | Captured log output lines |
| `error_message` | str | Runtime | Error details if failed (None if success) |
| `output_files` | list[str] | Runtime | Paths to output files created |

**State transitions**:
```
pending → running → completed
pending → running → failed
```

**No database table** — held in-memory in a `dict[str, OperationRun]` managed by `OperationExecutor`. Lost on Gunicorn restart (intentional — these are transient execution records, not persistent data).

**Thread safety**: Protected by `threading.Lock` for concurrent access from SSE streams and operation threads.

---

### 4. Theme

Represents a CSS theme available in the portal.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `name` | str | Filename stem | e.g., `dark`, `light`, `high-contrast` |
| `display_label` | str | Derived | e.g., `Dark NOC`, `Light Office`, `High Contrast` |
| `css_path` | str | Static file | e.g., `/static/css/themes/dark.css` |
| `is_default` | bool | ENV | True if matches `PORTAL_THEME` ENV value |

**No database table** — derived from files in `static/css/themes/` directory.

**Persistence**: User's selected theme stored in browser `localStorage` (key: `misthelper-theme`).

---

### 5. PortalConfig

ENV-driven configuration loaded at application startup.

| Field | Type | ENV Variable | Default |
|-------|------|-------------|---------|
| `title` | str | `PORTAL_TITLE` | `MistHelper` |
| `logo_url` | str | `PORTAL_LOGO_URL` | `/static/img/logo-default.svg` |
| `accent_color` | str | `PORTAL_ACCENT_COLOR` | `#0077B6` (Juniper blue) |
| `theme` | str | `PORTAL_THEME` | `dark` |
| `web_port` | int | `WEB_PORT` | `8055` |
| `allowed_ips` | list[str] | `PORTAL_ALLOWED_IPS` | `[]` (empty = allow all) |
| `secret_key` | str | `PORTAL_SECRET_KEY` | Auto-generated UUID |

**Validation rules**:
- `accent_color` must match `#[0-9A-Fa-f]{6}` pattern
- `theme` must be one of the available theme names
- `web_port` must be 1024-65535
- `allowed_ips` entries must be valid CIDR notation (e.g., `10.0.0.0/8`)

**Immutable after startup** — loaded once in app factory, stored on `app.config`.

---

### 6. SQLiteTableInfo

Metadata about a table in the SQLite database for the data browser.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `table_name` | str | `sqlite_master` | Name of the table |
| `row_count` | int | `SELECT COUNT(*)` | Number of rows |
| `column_names` | list[str] | `PRAGMA table_info` | Column names in order |
| `column_types` | list[str] | `PRAGMA table_info` | SQLite column types |

**No database table** — queried on demand from `data/mist_data.db`.

---

## Relationships

```
PortalConfig ─── configures ──→ Theme (default selection)
Operation ─── triggers ──→ OperationRun (1:many)
OperationRun ─── produces ──→ DataFile (0:many, via output_files)
DataFile ─── may contain ──→ SQLiteTableInfo (1:many, if .db file)
```

## Data Flow

```
Browser Request
    │
    ├── GET /                    → PortalConfig + recent OperationRuns → dashboard.html
    ├── GET /data                → DataFile list (os.scandir) → data_browser.html
    ├── GET /data/preview/<path> → CSV/SQLite → paginated JSON → table rendering
    ├── GET /data/download/<path>→ send_file() → browser download
    ├── GET /operations          → Operation list (menu_actions) → operations.html
    ├── POST /api/operations/run → OperationExecutor.start() → OperationRun created
    ├── GET /api/operations/stream → SSE stream → OperationRun status updates
    ├── GET /maps                → MapsManager data → map_viewer.html
    ├── GET /api/themes          → Theme list → JSON
    ├── GET /health              → {"status": "healthy"} → JSON
    └── Static files             → /static/css, /static/js, /static/vendor
```
