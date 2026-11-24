# MistHelper

Network operations and data export for the Juniper Mist Cloud.

[![Quality Gates](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml)
[![Container Build](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml)

## What

MistHelper is a menu-driven tool for the Juniper Mist Cloud. It reads your organizations, sites, devices, and clients. It writes each result to a CSV file or to a database.

It runs change operations, such as a firmware upgrade. A change operation changes the Mist Cloud or a device. It also serves a web portal, an upgrade capture portal, and a metrics gateway.

## Why

The Mist web interface answers one question at a time, on one page. An operator who must report on a full organization cannot work that way.

MistHelper turns each read into one numbered operation. One operation writes the data of a full organization to a CSV file or a database table. A scheduled job can run the same operation again.

Two rules shape the tool. A change operation asks a person to type a confirmation word before it runs. An automated test run does not start a change operation.

## Who

MistHelper is for network operators who manage one or more Mist organizations. You do not have to write Python.

You can use a Mist API token. You can also run `--login` with your Mist email and password. If Mist requires two-factor authentication for your account, MistHelper prompts for a verification code. For more about `--login`, see the [command line reference](documentation/cli-reference.md#flags).

## Where

MistHelper runs as a container on your own machine or your own server. It reaches the Mist Cloud API over HTTPS. It writes each output file to `data/`.

With an API token, MistHelper sends the token to Mist over HTTPS. Keep the token in your local `.env` file, which Git ignores.

## When

Use MistHelper for one of these tasks.

| You need | Start at |
|----------|----------|
| The full organization in a CSV file or a database | [Menu reference](documentation/menu_reference.md) |
| The same export on a schedule | [Command line reference](documentation/cli-reference.md) |
| A record of a site before a firmware upgrade and after it | [Upgrade capture portal](documentation/upgrade_capture_portal.md) |
| A feed for Prometheus, Grafana, or an SNMP poller | [Operator guide](documentation/operator-guide.md) |
| A command run across many devices over SSH | [SSH guide](documentation/SSH_GUIDE.md) |

## Run as a container

The container is the supported way to run MistHelper. Before you start, install Podman.

### Step 1: Get the files

```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

### Step 2: Set your credentials

```powershell
cp documentation\sample.env .env
```

Open `.env`. Set `MIST_HOST` to your Mist cloud name, such as `api.mist.com`. To use an API token, set `MIST_APITOKEN` to your token. MistHelper sends the token to Mist over HTTPS. Interactive `--login` does not require an API token.

To create an API token, open <https://manage.mist.com>. Open Organization. Then, open API Tokens. Create a token.

Warning: The `.env` file can hold your Mist API token. Git ignores this file. Do not commit this file. Do not paste its contents into an issue. A leaked token gives access to your Mist organization.

### Step 3: Let the data folder accept writes

On Windows and on macOS, skip this step. The container runtime runs in a virtual machine, and the shared folder accepts writes.

On Linux with rootless Podman, change the owner of `data` to the container user. The container user is `misthelper` with UID 1000.

```bash
podman unshare chown -R 1000:1000 data
```

### Step 4: Start the stack

```powershell
podman compose up -d
```

This command starts three containers: `misthelper-app`, `misthelper-arangodb`, and `misthelper-redis`.

On Windows, use `podman-compose` as the compose provider. The default provider sends the bind mount as a Windows path, and the `misthelper` service then refuses to start.

```powershell
.venv\Scripts\python.exe -m pip install podman-compose
$env:PODMAN_COMPOSE_PROVIDER = "podman-compose.exe"
```

Read the [container deployment page](documentation/container-deployment.md) to keep this variable in all shells.

### Step 5: Check the stack

```powershell
podman ps
curl http://127.0.0.1:8055/ready
```

The list shows three containers. When all checks pass, the ready address returns code 200 and the status `ready`.

### Step 6: Open the menu

```powershell
podman exec -it misthelper-app python MistHelper.py
```

Type the number of an operation. The tool asks for each value that it needs. To use your email and password, add `--login` to the end of the command.

Read the [operator guide](documentation/operator-guide.md) for the portals, SSH access, the metrics gateway, and the output paths.

## Documentation

| Page | What it holds |
|------|---------------|
| [Container deployment](documentation/container-deployment.md) | The other deployment methods and the rules that keep your data safe |
| [Security and safety](documentation/security.md) | Credential rules, log redaction, and destructive operation rules |
| [NOC runbooks](documentation/noc-runbooks) | Task guides for the operations center |
| [Development setup](documentation/development-setup.md) | How to run the code from a source checkout |
| [Contributing](documentation/contributing.md) | The branch workflow, the labels, and the review rules |
| [Contributor map for `MistHelper.py`](documentation/CONTRIBUTING-MistHelper.md) | The stable symbols and the packages that guide entry-point changes |
| [Release-note fragments](changelog.d/README.md) | The file that each change adds for its release note |
| [API notes](documentation/api) | The Mist API specification and the endpoint notes |
| [Quality gates](documentation/quality-gates.md) | The checks that each pull request runs |
| [Writing guide](documentation/ASD-STE100_writing-guide.md) | The Simplified Technical English rules for each document |
| [Architecture](documentation/architecture.md) | The package layout, the diagrams, and the decomposition record |
| [Changelog](CHANGELOG.md) | The version history |

The [wiki](https://github.com/jmorrison-juniper/MistHelper/wiki) holds the same subjects in a browsable form. Its source is in `documentation/wiki/`. Read the published wiki, because its page links work only there.

## License

The [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license](LICENSE) (CC-BY-NC-SA-4.0) covers MistHelper.
