# Quickstart: Web Portal Interface

**Feature**: 005-web-portal | **Date**: 2026-03-04

## Prerequisites

- Python 3.13+
- Existing MistHelper setup with valid `.env` file
- Container runtime (Podman or Docker) for deployment

## Local Development

### 1. Install Dependencies

```powershell
# From project root (Windows)
.venv\Scripts\Activate.ps1
pip install gunicorn flask flask-wtf
```

### 2. Run the Portal (Development Mode)

```powershell
# Start MistHelper with web portal enabled
python MistHelper.py --web-portal
```

This starts the Flask development server on `http://localhost:8055`.

### 3. Access the Portal

Open `http://localhost:8055` in Chrome, Firefox, or Edge.

## Container Deployment

### 1. Build and Run

```powershell
# Build container (auto-triggered by pushing to main)
git push origin main

# Or build locally
podman build -t misthelper:latest .

# Run with both SSH and web portal
podman run -d --name misthelper `
  -p 2200:2200 `
  -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" `
  -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
```

### 2. Verify

```powershell
# Check container is running
podman ps

# Test web portal
curl http://localhost:8055/health

# Test SSH
ssh -p 2200 misthelper@localhost
```

## ENV Configuration

Add to your `.env` file:

```bash
# Web Portal (all optional — sensible defaults provided)
WEB_PORT=8055
PORTAL_TITLE=MistHelper
PORTAL_THEME=dark
PORTAL_ACCENT_COLOR=#0077B6
PORTAL_LOGO_URL=
PORTAL_ALLOWED_IPS=
PORTAL_SECRET_KEY=
```

## Key URLs

| URL | Purpose |
|-----|---------|
| `http://host:8055/` | Dashboard |
| `http://host:8055/data` | Data browser |
| `http://host:8055/operations` | Run operations |
| `http://host:8055/maps` | Map viewer |
| `http://host:8055/health` | Health check |

## Architecture Overview

```
Browser ──HTTP──→ Gunicorn (port 8055) ──→ Flask App
                     │                        │
                     │                        ├── routes/ (5 blueprints)
                     │                        ├── services/ (5 service classes)
                     │                        └── templates/ (5 Jinja2 templates)
                     │
SSH Client ──SSH──→ sshd (port 2200) ──→ MistHelper CLI
                     │
                     └── Both share: data/ directory, .env config, apisession
```
