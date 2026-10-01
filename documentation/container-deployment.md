# Container Deployment

The container is the supported way to run MistHelper. This page holds the parts
of the container setup that the README does not carry: the other deployment
methods, the proxy certificate, and the rules that keep the two data stores
safe.

Read the README first for the plain start.

## Deployment methods

| Method | File | Description |
|--------|------|-------------|
| Compose | `compose.yml`, `compose.build.yml` | The stack of three required services and one monitoring profile. The supported method. |
| Podman Quadlet | `deploy/misthelper.container` | One container under systemd, with auto-restart |
| Systemd | `deploy/misthelper.service` | A host that runs the code with no container |

`deploy/.env.example` documents every environment variable.

## The compose services

| Service | Purpose |
|-----------|---------|
| `misthelper-app` | The application, the SSH server on port 2200, the web portal on port 8055, and the upgrade capture portal on port 8056 |
| `misthelper-arangodb` | The document store. It holds every capture and every upgrade run. |
| `misthelper-redis` | The site lock store, and the time-series cache |
| `misthelper-observium` | Optional SNMP monitoring service. The `monitoring` profile starts it. |

Warning: the two stores hold your captures and your upgrade runs. A command that
removes them loses that data. Read the next section before you recreate
anything.

## Start the stack

Use the standard compose command. It keeps the services on
`misthelper-network`, so the application resolves `misthelper-arangodb` and
`misthelper-redis` by name.

```powershell
podman compose up -d     # Start the application, ArangoDB, and Redis
podman compose down      # Stop the stack without removing volumes
```

To start Observium, add its profile.

```powershell
podman compose --profile monitoring up -d
```

Warning: do not pass `-v` to the `down` command. That option removes the production store volumes, and the upgrade records are not recoverable.

### Name the compose provider on Windows

`podman compose` calls an external provider. The default provider on Windows
sends the bind mount as a Windows path with a drive letter. The volume parser
then refuses the application service, and the two database services start
without it. The portal never answers. Issue #2184 holds that report.

Name `podman-compose` as the provider, and the standard command works. Issue
#3465 holds the measurement.

```powershell
.venv\Scripts\python.exe -m pip install podman-compose
$env:PODMAN_COMPOSE_PROVIDER = "podman-compose.exe"
```

The environment variable holds for one shell. To keep the provider for every
shell, add it to `containers.conf` instead. Read `containers.conf(5)` for the
file location on your host.

```toml
[engine]
compose_providers = ["podman-compose.exe"]
```

### The optional helper script

`scripts\compose.ps1` selects the provider for you, merges the build overlay,
merges the corporate-certificate overlay, and checks the image revision label.
When `check-revision` reports that no later commit changes an image input, the
running image is current even if `main` has advanced through documentation,
specification, workflow, or other non-image changes. When it names changed
image inputs, pull the image before restarting the application. It is in-house
development tooling, so a deployment must not depend on it. Every command in
this document runs without it.

## Docker deployment parity status

Docker is compatible in the source files, but this document does not make
Docker a verified deployment method. Issue #2721 checked the repository files
on a Windows host where `docker` was not installed. No local Docker start, DNS
test, health test, or data folder write test ran on that host.

Use Podman for production until a Docker host passes the verification list
below.

| Area | Status | Parity statement |
| - | - | - |
| Compose services | Analysis only | `compose.yml` defines the same application, ArangoDB, Redis, and optional Observium services for any Compose provider. |
| Service DNS | Analysis only | The application uses `misthelper-arangodb` and `misthelper-redis` on `misthelper-network`. A Docker host must still prove those names resolve. |
| Published ports | Analysis only | `compose.yml` publishes the same host ports for Docker and Podman. A Docker host must still prove no local process holds them. |
| Data folder ownership | Analysis only | The image runs as `misthelper` with UID 1000, so a Docker host must still prove that `data` accepts writes from that identifier. |
| Health checks | Analysis only | Compose health checks exist for the three required services. A Docker image build should also keep the Containerfile `HEALTHCHECK`. |
| Image health check in OCI format | Verified Podman difference | A Podman OCI image build can drop the Containerfile `HEALTHCHECK`, so the Quadlet unit states the probe again. Docker image health-check behavior was not tested here. |
| Compose provider | Verified Windows difference | `podman compose` needs `podman-compose` as its provider on Windows. Issue #3465 holds that measurement. Docker Compose was not tested here. |
| Systemd Quadlet | Verified Podman-only path | `deploy\misthelper.container` is a Podman Quadlet unit. This repository provides no Docker systemd unit. |
| Host systemd service | Verified separate path | `deploy\misthelper.service` runs Python on the host without a container runtime. It is not Docker or Podman parity. |
| `--no-deps` update | Analysis only | The documented Podman update leaves ArangoDB and Redis running. A Docker host must still prove the same behavior. |

The analysis above comes from these files.

- `compose.yml` defines service names, ports, volumes, health checks,
  `depends_on`, and `misthelper-network`.
- `Containerfile` and `Dockerfile` define the non-root user with UID 1000,
  `/app/data`, the exposed ports, and the image health check.
- `compose.build.yml` holds the build overlay, and
  `deploy\compose.corporate-ca.yml` holds the corporate-certificate overlay.
- `deploy\misthelper.container` defines Podman Quadlet health and restart
  settings.
- `deploy\misthelper.service` defines the host Python service.
- `tests\guardrails\test_compose_naming_policy.py` proves the service names,
  network name, project subnet, store addresses, and published port policy.

Before you document Docker as a supported deployment method, run these checks
on a host with Docker installed.

1. Run `docker --version` and record the result.
2. Run `docker compose config` and confirm that every service joins
   `misthelper-network`.
3. Start the stack with Docker Compose in a clean test environment.
4. Confirm that `misthelper-app` resolves `misthelper-arangodb` and
   `misthelper-redis`.
5. Confirm that the three required services report healthy.
6. Confirm that `/app/data` can write `script.log` through the mounted `data`
   folder.
7. Confirm that `docker compose up -d --no-deps misthelper` does not recreate
   ArangoDB or Redis.
8. Confirm that a Docker build keeps the image `HEALTHCHECK`.
9. Add Docker guardrail tests before you publish Docker commands for operators.

## Test and debug containers

This section covers every container that you start for a test, for a debug
session, or for an end-to-end run. It does not cover the deployment methods
above. `.github/copilot-instructions.md` § "Test and Debug Containers" holds the
same policy for an agent.

**Rule 1. Start the container inside the compose group.**

Never start a one-off container outside the group. A container outside the
group joins no `misthelper-network`, so it cannot reach `misthelper-arangodb`
or `misthelper-redis` by name.

```powershell
podman compose run --rm misthelper python -m pytest tests/<file>
podman compose --profile test up -d
```

If the test needs a new service, add the service to `compose.yml` under a
profile. A profile keeps the service out of the normal `up`.

**Rule 2. Name an ephemeral container for its issue or its pull request.**

An ephemeral container serves one investigation and then goes away. Give the
container, the volume, and the network this name.

```text
misthelper-tmp-<issue|pr><number>-<slug>
```

For example, `misthelper-tmp-issue2059-portcheck`. A reader who finds the
container three days later can open the issue and learn why it runs.

**Rule 3. Never publish a production local port.**

| Port | Owner |
| - | - |
| 1161/udp | The SNMP service |
| 1514/udp | The Observium syslog receiver |
| 2200 | The SSH runner |
| 8055 | The web portal |
| 8056 | The upgrade capture portal |
| 8057 | The metrics gateway |
| 8668 | The Observium web interface |
| 9379 | Redis |
| 9526 | The RedisInsight web UI |
| 9529 | ArangoDB |

Read `compose.yml` before you pick a port. That file is the source of truth,
and the table above can drift.

Publish an ephemeral port in the range 9600 through 9699 instead, and bind it
to `127.0.0.1`.

Warning: an ephemeral container that publishes 9529 or 9379 takes the port from
the running store. The portal then writes a capture into the wrong database, and
the operator loses the upgrade record. Issue #2059 records that collision.

**Rule 4. Remove the container when the test ends.**

Never leave a test container running. A stopped container still holds its image
layers, its volume, and its log file.

```powershell
podman compose rm -s -f <the test service>
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman volume rm misthelper-tmp-<issue|pr><number>-<slug>
podman network rm misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
podman volume ls --filter "name=misthelper-tmp-" --format "{{.Name}}"
podman system df
```

The `ps` and `volume ls` commands confirm the cleanup. Empty results mean the cleanup finished. The final command reports the reclaimed space.

Warning: never run `podman volume prune`, and never pass `-v` to a compose
`down` command. Both remove `misthelper-arangodb-data` and
`misthelper-redis-data`. Those two volumes hold every capture and every upgrade
run, and a removed volume is not recoverable. Remove a test volume by name
instead.

## Update the stack to the newest code

Warning: a compose file with an application build section can overwrite the
published tag with a local build. If the checkout is old, the command can
downgrade the running container and remove the commit labels. Issue #2272 holds
the measurement.

The application build section now lives in `compose.build.yml`. A plain `up`
reads only `compose.yml`, so it cannot build the application image. The recipe
below remains the safe update path.

Update the checkout first, then pull, then name the service.

```powershell
git pull                                        # The build source, if one runs
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman rm -f misthelper-app
podman compose up -d --no-deps misthelper
```

## Build the image from your working tree

`compose.build.yml` holds the build overlay. Name it only for an explicit build
request, so a normal `up` never rebuilds.

```powershell
podman compose -f compose.yml -f compose.build.yml build
```

Warning: a build from a checkout that is behind `main` overwrites the published
tag with a stale build and clears the labels that name the commit. Run
`git pull` before the build, and read the revision after the run.

## Check the revision of the running container

Read the commit label from the running image, then compare it against
`origin/main`.

```powershell
podman inspect misthelper-app --format "{{ index .Config.Labels \"org.opencontainers.image.revision\" }}"
git rev-parse origin/main
```

An empty label names a local build, because only the CI build writes the label.
A label that differs from `origin/main` names an image that CI published for an
older commit.

Continuous integration builds and publishes an image for every commit that
changes `src/`, `web_portal/`, `MistHelper.py`, `requirements.txt`, or the
`Containerfile`. A pull therefore gives you the tested image, and no local build
is needed. Read `.github/workflows/container-build.yml` for the full path list.

## Read the commit that a container runs

```powershell
podman inspect misthelper-app --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
```

Compare that value against `git rev-parse origin/main`. An empty answer names a
local build, because only the continuous integration build writes the label.

## Recreate the application container alone

After a new image, recreate the application container and leave the two stores
running. Remove the container first, then name the service.

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman rm -f misthelper-app
podman compose up -d --no-deps misthelper
```

Caution: pass `--no-deps` and name the service. Without both, compose tries to
create `misthelper-arangodb` and `misthelper-redis` again, and it stops with
`the container name is already in use`. Those two stores hold every capture and
every upgrade run, so this pair of commands is the one that leaves them
untouched. Issue #2228 holds that report.

The plain start command is still the right command for a cold start, when no
container of the stack runs yet.

## The data folder

The container writes to `/app/data`, and the stack mounts the `data` folder of
this repository at that place. The container runs as the user `misthelper`, and
that account holds UID 1000 and GID 1000. `Containerfile` pins both numbers, and
`tests/guardrails/test_container_account_identifiers.py` holds this document to
the pinned value.

Confirm the identifiers from the image at any time:

```powershell
podman run --rm --entrypoint "" ghcr.io/jmorrison-juniper/misthelper:latest id misthelper
```

On Windows and on macOS, no step is needed. The container runtime runs in a
virtual machine, and the file share presents the folder as writable for every
identifier. Issue #3465 holds that measurement.

On Linux with rootless Podman, give the folder to the container account. The
`podman unshare` prefix maps UID 1000 of the container to the matching host
identifier in your user namespace.

```bash
podman unshare chown -R 1000:1000 data
```

On Linux with rootful Podman or with Docker, the container identifier is the
host identifier, so the plain command is correct.

```bash
sudo chown -R 1000:1000 data
```

Warning: do not run `chmod -R 777 data`. That command gives every account on the
host the right to read your captures and to change your logs, and no supported
host needs it.

A message that reads `PermissionError: [Errno 13] Permission denied:
'/app/data/script.log'` means the folder refused the write.

## Corporate proxy and TLS certificates

The container image verifies every TLS certificate. It never disables the check.

Warning: do not set `PYTHONHTTPSVERIFY=0`, and do not set a CA bundle variable to
an empty value. Without the check, an attacker on the network path can read your
Mist API token.

If you sit behind a TLS-inspecting proxy such as Zscaler, save the proxy root certificate as `zscaler-root-ca.crt` in the repository root. Then start the stack with the compose overlay. The container adds the certificate to the system trust store at start time.

```powershell
podman compose -f compose.yml -f deploy\compose.corporate-ca.yml up -d
```

To build behind the same proxy, add the root certificate at build time:

```powershell
podman build --build-arg INSTALL_CORPORATE_CA=true -t misthelper -f Containerfile .
```

## Build the image

The registry builds the image on each push to `main`. To build it yourself:

```powershell
podman build -t misthelper:local -f Containerfile .
```

Caution: a proxy that inspects TLS blocks a `podman push` to the registry from a
corporate network. Let GitHub Actions build and push the image instead. The
runner sits outside the corporate network.

Two build files exist. `Containerfile` builds with pip and is the file that
`compose.build.yml` names. `Dockerfile` adds a health check and the UV package
manager. Both verify every TLS certificate.

## Gunicorn control sockets

Two masters of Gunicorn run as the `misthelper` account.
Each master has its own control socket.

| Portal | Default port | Control socket |
| - | - | - |
| Web portal | 8055 | `/home/misthelper/.gunicorn/portal.ctl` |
| Upgrade capture portal | 8056 | `/home/misthelper/.gunicorn/capture.ctl` |

Use the socket of the intended portal for a Gunicorn control command.
The two masters retain these separate paths after a SIGHUP reload.
Gunicorn creates the socket directory and applies its default `0600` socket mode.

Caution: a shared control socket can cause a command to reach the wrong portal.

The repair needs a new image and an approved application container restart.
An isolated process test does not authorize that restart.
See [issue #3370](https://github.com/jmorrison-juniper/MistHelper/issues/3370).

## Remote access over SSH

The container runs an SSH server on port 2200. A connection starts MistHelper
at once, and it reaches no shell.

Read [the SSH guide](SSH_GUIDE.md) for the full setup.
