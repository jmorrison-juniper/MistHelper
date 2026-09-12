# Container Setup

## Build Strategies

Two build strategies are available:

1. **`Containerfile`** (simple, pip only, TLS verification on, optional corporate root certificate)
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

## Corporate Proxy and TLS Certificates

The image verifies every TLS certificate. It never disables the check.

Warning: Do not set `PYTHONHTTPSVERIFY=0`, and do not set `REQUESTS_CA_BUNDLE`,
`CURL_CA_BUNDLE`, or `SSL_CERT_FILE` to an empty value. Without the check, an
attacker on the network path can present a self-signed certificate and read your
Mist API token. Issue #1906 records the earlier defect.

### Run behind a TLS-inspecting proxy

Mount the proxy root certificate into `/usr/local/share/ca-certificates`. The
container entrypoint adds the certificate to the system trust store at start
time, and it writes the result to `data/ssh.log`.

```powershell
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
  -v "${PWD}/zscaler-root-ca.crt:/usr/local/share/ca-certificates/corp-root-ca.crt:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
```

Confirm the result:

```powershell
podman exec misthelper env | Select-String "CA_BUNDLE|SSL_CERT_FILE|PYTHONHTTPSVERIFY"
Select-String -Path data/ssh.log -Pattern "\[TLS\]"
```

### Build behind a TLS-inspecting proxy

The build fetches packages from PyPI over verified TLS. If the proxy replaces
the PyPI certificate, add the proxy root certificate at build time:

```powershell
podman build --build-arg INSTALL_CORPORATE_CA=true -t misthelper -f Containerfile .
```

The build reads the certificate from `zscaler-root-ca.crt` in the repository
root. To use a different file, pass `--build-arg CORPORATE_CA_FILE=<path>`. The
path is relative to the build context.

The default build argument value is `false`, so the published image ships a
clean trust store.

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
