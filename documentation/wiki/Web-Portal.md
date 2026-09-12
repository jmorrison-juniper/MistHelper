# Web Portal

MistHelper includes a Flask-based web portal for browser access to data, operations, and map viewing.

## Quick Start

```powershell
# Local development (Windows)
python MistHelper.py --web-portal

# Container (runs automatically alongside SSH)
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 \
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" \
  ghcr.io/jmorrison-juniper/misthelper:latest
```

Open http://localhost:8055 in your browser.

Caution: the command above starts the production local stack. If you start a
container for a test, for a debug session, or for an end-to-end run, obey the
policy in [Container Setup](Container-Setup#test-and-debug-containers). Start
the container inside the compose group. Name it
`misthelper-tmp-<issue|pr><number>-<slug>`. Publish a port in the range 9600
through 9699. Remove the container when the test ends. A test container that
publishes 8055 takes the port from the running portal, and the portal then stops
answering.

## Features

- **Data Browser**: Browse, preview, search, and download CSV/SQLite output files
- **Operations**: Run non-destructive data extraction operations (menus 1-89) with real-time SSE progress
- **Map Viewer**: Interactive Plotly.js floor plan viewer with device markers
- **Themes**: Dark, Light, and High Contrast themes with instant switching (persisted in localStorage)
- **Branding**: Customize title, logo, and accent color via ENV variables

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORTAL_TITLE` | `MistHelper` | Browser tab and navbar title |
| `PORTAL_LOGO_URL` | `/static/img/logo-default.svg` | Logo image URL |
| `PORTAL_ACCENT_COLOR` | `#0d6efd` | Accent color for buttons and highlights |
| `PORTAL_THEME` | `dark` | Default theme (dark, light, high-contrast) |
| `WEB_PORT` | `8055` | Web portal listen port |
| `PORTAL_ALLOWED_IPS` | *(empty = all)* | Comma-separated CIDR allowlist |
| `PORTAL_SECRET_KEY` | *(auto-generated)* | Flask session secret key |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard with data summary |
| `/data` | GET | Data browser page |
| `/operations` | GET | Operations page |
| `/maps` | GET | Map viewer page |
| `/health` | GET | Liveness probe. Reports that the process runs. Reads no disk. |
| `/ready` | GET | Readiness probe. Tests the data directory, the database, and the Mist session. Returns code 503 and names each failed check. |
| `/api/data/files` | GET | List data files |
| `/api/operations/list` | GET | List available operations |
| `/api/operations/run` | POST | Run an operation |
| `/api/operations/stream` | GET | SSE event stream |
