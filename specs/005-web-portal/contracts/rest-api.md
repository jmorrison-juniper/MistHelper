# REST API Contracts: Web Portal

**Feature**: 005-web-portal | **Date**: 2026-03-04

## Base URL

```
http://<host>:8055
```

---

## Pages (HTML Responses)

### GET /

**Dashboard** — Portal home page showing system status and recent operations.

- **Response**: HTML (dashboard.html)
- **Template context**: PortalConfig, recent OperationRun list, data directory summary

### GET /data

**Data Browser** — List files available for preview and download.

- **Response**: HTML (data_browser.html)
- **Query params**:
  - `sort` (optional): `name`, `size`, `modified` (default: `modified`)
  - `order` (optional): `asc`, `desc` (default: `desc`)
- **Template context**: DataFile list, PortalConfig

### GET /operations

**Operations Menu** — Categorized list of available operations.

- **Response**: HTML (operations.html)
- **Template context**: Operation list grouped by category, active OperationRun list

### GET /maps

**Map Viewer** — Interactive site/floor plan map viewer (replaces Dash).

- **Response**: HTML (map_viewer.html)
- **Template context**: Site list (from API), PortalConfig

---

## API Endpoints (JSON Responses)

### GET /api/data/files

List all data files with metadata.

**Response** (200):
```json
{
  "files": [
    {
      "name": "site_inventory.csv",
      "path": "site_inventory.csv",
      "size_bytes": 45678,
      "last_modified": "2026-03-04T12:30:00Z",
      "file_type": "csv",
      "is_directory": false
    }
  ],
  "total_count": 15
}
```

### GET /api/data/preview/{path}

Preview file contents with pagination.

**Path params**:
- `path`: URL-encoded relative path within `data/`

**Query params**:
- `page` (optional): Page number, 1-based (default: 1)
- `per_page` (optional): Rows per page (default: 50, max: 200)
- `sort_column` (optional): Column name to sort by
- `sort_order` (optional): `asc` or `desc` (default: `asc`)
- `search` (optional): Filter rows containing this text

**Response** (200) — CSV file:
```json
{
  "columns": ["site_name", "site_id", "country_code"],
  "rows": [
    ["HQ Office", "abc-123", "US"],
    ["Branch 1", "def-456", "UK"]
  ],
  "total_rows": 1500,
  "page": 1,
  "per_page": 50,
  "total_pages": 30
}
```

**Response** (200) — SQLite file (returns table list):
```json
{
  "tables": [
    {
      "table_name": "listOrgSites",
      "row_count": 42,
      "column_names": ["id", "name", "country_code"]
    }
  ]
}
```

**Error** (400):
```json
{"error": "Path traversal not allowed"}
```

**Error** (404):
```json
{"error": "File not found"}
```

### GET /api/data/preview/{path}/{table_name}

Preview a specific SQLite table with pagination.

**Path params**:
- `path`: URL-encoded path to .db file
- `table_name`: SQLite table name

**Query params**: Same as `/api/data/preview/{path}`

**Response** (200): Same format as CSV preview above

### GET /api/data/download/{path}

Download a file from the data directory.

**Path params**:
- `path`: URL-encoded relative path within `data/`

**Response** (200): File content with `Content-Disposition: attachment` header

**Error** (404):
```json
{"error": "File not found"}
```

---

### GET /api/operations/list

List all available non-destructive operations.

**Response** (200):
```json
{
  "categories": [
    {
      "name": "Core Organization",
      "operations": [
        {
          "menu_number": "1",
          "description": "Export all organization alarms from the past day"
        }
      ]
    }
  ],
  "total_count": 89
}
```

### POST /api/operations/run

Start an operation execution.

**Request**:
```json
{
  "menu_number": "11",
  "parameters": {
    "site_id": "abc-123"
  }
}
```

**Headers**:
- `X-CSRFToken`: CSRF token from cookie

**Response** (202):
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "menu_number": "11",
  "description": "List Organization Sites",
  "status": "pending"
}
```

**Error** (400):
```json
{"error": "Menu number 95 is a destructive operation and cannot be run from the portal"}
```

**Error** (409):
```json
{"error": "Operation 11 is already running", "run_id": "existing-run-id"}
```

### GET /api/operations/status/{run_id}

Get current status of an operation run.

**Response** (200):
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "menu_number": "11",
  "description": "List Organization Sites",
  "status": "running",
  "started_at": "2026-03-04T12:35:00Z",
  "completed_at": null,
  "progress_pct": 45,
  "error_message": null,
  "output_files": []
}
```

### GET /api/operations/active

List all currently running operations.

**Response** (200):
```json
{
  "active": [
    {
      "run_id": "550e8400-...",
      "menu_number": "11",
      "description": "List Organization Sites",
      "status": "running",
      "progress_pct": 45
    }
  ]
}
```

---

### GET /api/operations/stream

**SSE (Server-Sent Events)** — Real-time operation status updates.

**Query params**:
- `run_id` (optional): Filter to a specific run. If omitted, streams all operation events.

**Response**: `text/event-stream`

```
event: status
data: {"run_id": "550e...", "status": "running", "progress_pct": 45}

event: log
data: {"run_id": "550e...", "message": "Processing site 5 of 42..."}

event: complete
data: {"run_id": "550e...", "status": "completed", "output_files": ["site_inventory.csv"]}

event: error
data: {"run_id": "550e...", "status": "failed", "error_message": "API token expired"}

event: heartbeat
data: {"timestamp": "2026-03-04T12:35:30Z"}
```

**Event types**:

| Event | Frequency | Data |
|-------|-----------|------|
| `status` | On progress change | run_id, status, progress_pct |
| `log` | Per log line | run_id, message |
| `complete` | Once per run | run_id, status, output_files |
| `error` | Once per run | run_id, status, error_message |
| `heartbeat` | Every 30s | timestamp (keeps connection alive) |

**Connection lifecycle**:
- Client connects via `new EventSource('/api/operations/stream?run_id=...')`
- Server sends events as they occur
- Heartbeat every 30 seconds to prevent proxy timeout
- Client auto-reconnects on disconnect (EventSource spec behavior)

---

### GET /api/operations/parameters/{menu_number}

Get required parameters for an operation (for guided dropdowns — FR-024).

**Response** (200):
```json
{
  "menu_number": "29",
  "description": "Export Site Device Stats",
  "parameters": [
    {
      "name": "site_id",
      "label": "Site",
      "type": "select",
      "required": true,
      "options": [
        {"value": "abc-123", "label": "HQ Office"},
        {"value": "def-456", "label": "Branch 1"}
      ]
    },
    {
      "name": "device_type",
      "label": "Device Type",
      "type": "select",
      "required": false,
      "options": [
        {"value": "ap", "label": "Access Points"},
        {"value": "switch", "label": "Switches"},
        {"value": "gateway", "label": "Gateways"},
        {"value": "all", "label": "All Devices"}
      ]
    }
  ]
}
```

**Response** (200) — Operation with no parameters:
```json
{
  "menu_number": "11",
  "description": "List Organization Sites",
  "parameters": []
}
```

---

### GET /api/themes

List available themes.

**Response** (200):
```json
{
  "themes": [
    {"name": "dark", "display_label": "Dark NOC", "is_default": true},
    {"name": "light", "display_label": "Light Office", "is_default": false},
    {"name": "high-contrast", "display_label": "High Contrast", "is_default": false}
  ],
  "current_default": "dark"
}
```

---

### GET /api/maps/sites

List sites for map viewer dropdown.

**Response** (200):
```json
{
  "sites": [
    {"id": "abc-123", "name": "HQ Office"},
    {"id": "def-456", "name": "Branch 1"}
  ]
}
```

### GET /api/maps/site/{site_id}/maps

List maps for a specific site.

**Response** (200):
```json
{
  "maps": [
    {
      "id": "map-001",
      "name": "Floor 1",
      "width": 1200,
      "height": 800,
      "has_image": true
    }
  ]
}
```

### GET /api/maps/site/{site_id}/map/{map_id}/data

Get map data for Plotly.js rendering.

**Response** (200):
```json
{
  "map_id": "map-001",
  "name": "Floor 1",
  "image_url": "/api/maps/image/map-001",
  "width": 1200,
  "height": 800,
  "devices": [
    {
      "id": "dev-001",
      "name": "AP-Lobby",
      "type": "ap",
      "x": 150.5,
      "y": 320.0,
      "mac": "aa:bb:cc:dd:ee:ff"
    }
  ]
}
```

### GET /api/maps/image/{map_id}

Serve a map background image.

**Response** (200): Image file (PNG/JPEG) with appropriate content type

---

### GET /health

Health check endpoint for container orchestration.

**Response** (200):
```json
{
  "status": "healthy",
  "version": "26.03.04.22.30",
  "services": {
    "web_portal": "running",
    "ssh": "running"
  },
  "uptime_seconds": 3600,
  "data_directory": "/app/data",
  "data_files_count": 15
}
```

---

## Common Error Responses

All error responses follow this format:

```json
{
  "error": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid params, path traversal) |
| 403 | IP not in allowlist |
| 404 | Resource not found |
| 409 | Conflict (duplicate operation) |
| 500 | Internal server error |

## Security Headers

All responses include:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

Note: `'unsafe-inline'` for style-src is needed for Plotly.js inline styles and Bootstrap's runtime style modifications. `data:` for img-src allows Plotly-generated data URIs for map images.
