# Container Setup

## Build Strategies

Two build strategies are available:

1. **`Containerfile`** (simple, pip only, SSL bypass env overrides for constrained corporate PKI)
2. **`Dockerfile`** (multi-path UV attempt + HEALTHCHECK)

## Local Container Usage

### Docker Compose (interactive shell)

```bash
docker compose build
docker compose run --rm misthelper python MistHelper.py
```

### Podman (direct)

```powershell
podman build -t misthelper -f Containerfile .
podman run -it --rm -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" misthelper python MistHelper.py
```

## Container with SSH + Web Portal

```powershell
# Build and start with SSH server and web portal
podman build -t misthelper -f Containerfile .

# IMPORTANT: Ensure data directory has proper permissions
chmod -R 777 data/

# Start container with SSH (port 2200) and web portal (port 8055)
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 \
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" \
  misthelper
```

## Container Registry

Pre-built images are available from GitHub Container Registry:

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 \
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" \
  ghcr.io/jmorrison-juniper/misthelper:latest
```

## Data Directory Permissions

The container runs MistHelper as a non-root user (`misthelper`) for security. When mounting the `data/` directory as a volume, ensure proper permissions:

```bash
# Option 1: Open permissions (simplest, suitable for development)
chmod -R 777 data/

# Option 2: Match container user UID/GID (more secure for production)
# The misthelper user in the container typically has UID 999
chown -R 999:999 data/
chmod -R 755 data/
```

**Symptom of permission issues:** `PermissionError: [Errno 13] Permission denied: '/app/data/script.log'` -- fix data directory permissions.

## Deployment Options

| Method | File | Description |
|--------|------|-------------|
| Systemd | `deploy/misthelper.service` | Standalone host deployment |
| Podman Quadlet | `deploy/misthelper.container` | Containerized with auto-restart |
| Docker Compose | `compose.yml` | Container orchestration |

See `deploy/.env.example` for environment variable documentation.
