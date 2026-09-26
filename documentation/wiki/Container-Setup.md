# Container Setup

## Build files

`Containerfile` and `Dockerfile` hold the same bytes. The repository keeps both
names so that a Podman reader and a Docker reader each find the file they
expect. `tests/unit/container/test_build_files_match.py` fails when the two
files differ, so edit one file and copy it over the other.

Both files install with pip, keep TLS verification on, accept an optional
corporate root certificate, and declare a `HEALTHCHECK`.

## Compose provider

`podman compose` calls an external provider. On Windows the default provider
sends the bind mount as a Windows path with a drive letter, and the volume
parser then refuses the application service. Name `podman-compose` as the
provider one time, and the standard command works:

```powershell
.venv\Scripts\python.exe -m pip install podman-compose
$env:PODMAN_COMPOSE_PROVIDER = "podman-compose.exe"
```

To keep the setting for every shell, add the provider to `containers.conf`
instead. Read `containers.conf(5)` for the file location on your host.

```toml
[engine]
compose_providers = ["podman-compose.exe"]
```

Issue #2184 holds the report of the default-provider failure, and issue #3465
holds the measurement that the provider setting corrects it.

`scripts\compose.ps1` is an optional in-house convenience. It selects the
provider for you and it merges the build and corporate-certificate overlays.
It is development tooling, so a deployment must not depend on it.

## Local Container Usage

Warning: the commands in this section start the production local stack. If you
start a container for a test, for a debug session, or for an end-to-end run,
obey the "Test and debug containers" section below instead.

### Start the supported stack

```powershell
podman compose up -d
```

The command starts the application, the document store, and the site lock store on `misthelper-network`. The application resolves `misthelper-arangodb` and `misthelper-redis` by name.

### Build from the working tree

```powershell
podman compose -f compose.yml -f compose.build.yml build
podman compose up -d --no-deps misthelper
```

Caution: use a local build only when you need the code in your checkout. A checkout that is behind `main` can start old code.

## Container with SSH + Web Portal

```powershell
podman compose up -d
```

The application container starts the SSH server on port 2200, the web portal on port 8055, and the upgrade capture portal on port 8056.

## Test and debug containers

This section covers every container that you start for a test, for a debug
session, or for an end-to-end run. The section "Test and debug containers" in
`documentation/container-deployment.md` holds the same policy. That page also
holds the full cleanup commands.

**Rule 1. Start the container inside the compose group.** Use
`podman compose run --rm`, or add the service to `compose.yml` under a
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
podman compose rm -s -f <the test service>
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman volume rm misthelper-tmp-<issue|pr><number>-<slug>
podman network rm misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
podman volume ls --filter "name=misthelper-tmp-" --format "{{.Name}}"
```

The last two commands confirm the cleanup. Empty results mean the cleanup finished.

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
podman compose -f compose.yml -f deploy\compose.corporate-ca.yml up -d
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
podman rm -f misthelper-app
podman compose up -d --no-deps misthelper
```

## Data Directory Permissions

The container runs MistHelper as the non-root user `misthelper`, and that
account holds UID 1000 and GID 1000. The stack mounts the `data` folder of this
repository at `/app/data`, so that folder must accept a write from UID 1000.

Confirm the identifiers from the image at any time:

```powershell
podman run --rm --entrypoint "" ghcr.io/jmorrison-juniper/misthelper:latest id misthelper
```

**Windows and macOS: no step is needed.** The container runtime runs in a
virtual machine, and the file share presents the folder as writable for every
identifier. Issue #3465 holds the measurement.

**Linux, rootless Podman:** give the folder to the container account. The
`podman unshare` prefix maps UID 1000 of the container to the matching host
identifier in your user namespace.

```bash
podman unshare chown -R 1000:1000 data
```

**Linux, rootful Podman or Docker:** the container identifier is the host
identifier, so the plain command is correct.

```bash
sudo chown -R 1000:1000 data
```

Warning: do not run `chmod -R 777 data`. That command gives every account on the
host the right to read your captures and to change your logs, and no supported
host needs it.

**Symptom of permission issues:** `PermissionError: [Errno 13] Permission denied: '/app/data/script.log'` -- fix data directory permissions.

## Deployment Options

| Method | File | Description |
|--------|------|-------------|
| Systemd | `deploy/misthelper.service` | Standalone host deployment |
| Podman Quadlet | `deploy/misthelper.container` | Containerized with auto-restart |
| Docker Compose | `compose.yml` | Container orchestration |

See `deploy/.env.example` for environment variable documentation.
