# Container Deployment

The container is the supported way to run MistHelper. This page holds the parts
of the container setup that the README does not carry: the other deployment
methods, the proxy certificate, and the rules that keep the two data stores
safe.

Read the README first for the plain start.

## Deployment methods

| Method | File | Description |
|--------|------|-------------|
| Compose | `compose.yml` | The stack of three containers. The supported method. |
| Podman Quadlet | `deploy/misthelper.container` | One container under systemd, with auto-restart |
| Systemd | `deploy/misthelper.service` | A host that runs the code with no container |

`deploy/.env.example` documents every environment variable.

## The three containers

| Container | Purpose |
|-----------|---------|
| `misthelper-app` | The application, the SSH server on port 2200, the web portal on port 8055, and the upgrade capture portal on port 8056 |
| `misthelper-arangodb` | The document store. It holds every capture and every upgrade run. |
| `misthelper-redis` | The site lock store, and the time-series cache |

Warning: the two stores hold your captures and your upgrade runs. A command that
removes them loses that data. Read the next section before you recreate
anything.

## Start the stack

Use the helper script. It picks a compose provider that works on every platform.

```powershell
.\scripts\compose.ps1 up -d     # Start the stack
.\scripts\compose.ps1 down      # Stop the stack
```

Warning: do not run `podman compose` on Windows, because that command can stop
the whole portal. It starts the stack without its application service, so the
portal never answers. The command delegates to an external provider, which sends
the bind mount as a Windows path with a drive letter. The volume parser then
refuses the application service, and the two database services start without it.
Issue #2184 holds that report.

The script needs the native provider. Install it one time with this command:

```powershell
.venv\Scripts\python.exe -m pip install podman-compose
```

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
.\scripts\compose.ps1 run --rm misthelper python -m pytest tests/<file>
.\scripts\compose.ps1 --profile test up -d
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
.\scripts\compose.ps1 rm -s -f <the test service>
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman volume rm misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
podman system df
```

The fourth command confirms the cleanup. An empty result means the cleanup
finished. The fifth command reports the reclaimed space.

Warning: never run `podman volume prune`, and never pass `-v` to a compose
`down` command. Both remove `misthelper-arangodb-data` and
`misthelper-redis-data`. Those two volumes hold every capture and every upgrade
run, and a removed volume is not recoverable. Remove a test volume by name
instead.

## Update the stack to the newest code

Warning: a plain `up` rebuilds. `podman-compose up -d` with no service argument
builds the application image from your working tree and overwrites the published
tag with that build. It prints no line that names the build. If your checkout is
behind `main`, the command downgrades the running container and clears the labels
that name the commit. Issue #2272 holds the measurement.

Update the checkout first, then pull, then name the service.

```powershell
git pull                                        # The build source, if one runs
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman rm -f misthelper-app
.\scripts\compose.ps1 up -d --no-deps misthelper
```

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
.\scripts\compose.ps1 up -d --no-deps misthelper
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
this repository at that place. The container runs as the user `misthelper` and
not as root, so that folder must accept a write.

```bash
chmod -R 777 data/
```

A message that reads `PermissionError: [Errno 13] Permission denied:
'/app/data/script.log'` means the folder refused the write.

## Corporate proxy and TLS certificates

The container image verifies every TLS certificate. It never disables the check.

Warning: do not set `PYTHONHTTPSVERIFY=0`, and do not set a CA bundle variable to
an empty value. Without the check, an attacker on the network path can read your
Mist API token.

If you sit behind a TLS-inspecting proxy such as Zscaler, mount the proxy root
certificate. The container adds it to the system trust store at start time.

```powershell
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
  -v "${PWD}/zscaler-root-ca.crt:/usr/local/share/ca-certificates/corp-root-ca.crt:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
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
`compose.yml` names. `Dockerfile` adds a health check and the UV package
manager. Both verify every TLS certificate.

## Remote access over SSH

The container runs an SSH server on port 2200. A connection starts MistHelper
at once, and it reaches no shell.

Read [the SSH guide](SSH_GUIDE.md) for the full setup.
