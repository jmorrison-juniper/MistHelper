# Container Setup

## Build Strategies

Two build strategies are available:

1. **`Containerfile`** (simple, pip only, TLS verification on, optional corporate root certificate)
2. **`Dockerfile`** (multi-path UV attempt + HEALTHCHECK)

## Local Container Usage

Warning: the commands in this section start the production local stack. If you
start a container for a test, for a debug session, or for an end-to-end run,
obey the "Test and debug containers" section below instead.

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

## Test and debug containers

This section covers every container that you start for a test, for a debug
session, or for an end-to-end run. The section "Test and debug containers" in
`documentation/container-deployment.md` holds the same policy. That page also
holds the full cleanup commands.

**Rule 1. Start the container inside the compose group.** Use
`.\scripts\compose.ps1 run --rm`, or add the service to `compose.yml` under a
profile. Never start a one-off container with a bare `podman run`. A container
outside the group joins no `misthelper-network`, so it cannot reach
`misthelper-arangodb` or `misthelper-redis` by name.

**Rule 2. Name an ephemeral container for its issue or its pull request.** Use
`misthelper-tmp-<issue|pr><number>-<slug>` for the container, the volume, and
the network. For example, `misthelper-tmp-issue2059-portcheck`. A reader who
finds the container three days later can open the issue and learn why it runs.

**Rule 3. Never publish a production local port.** Read `compose.yml` for the
current set. Today it holds 1161/udp, 1514/udp, 2200, 8055, 8056, 8057, 8668,
9379, 9526, and 9529. Publish an ephemeral port in the range 9600 through 9699,
bound to `127.0.0.1`.

**Rule 4. Remove the container when the test ends.** Never leave a test
container running. A stopped container still holds its image layers, its volume,
and its log file.

```powershell
.\scripts\compose.ps1 rm -s -f <the test service>
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman volume rm misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
```

The last command confirms the cleanup. An empty result means the cleanup
finished.

Warning: never run `podman volume prune`, and never pass `-v` to a compose
`down` command. Both remove `misthelper-arangodb-data` and
`misthelper-redis-data`. Those two volumes hold every capture and every upgrade
run, and a removed volume is not recoverable.

Warning: a test container that publishes 9529 or 9379 takes the port from the
running store. The upgrade portal then writes a capture into the wrong database,
and the operator loses the upgrade record. Issue #2059 records that collision.

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
