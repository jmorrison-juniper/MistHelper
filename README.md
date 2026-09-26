# MistHelper

Network operations and data export for the Juniper Mist Cloud.

[![Quality Gates](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/ci.yml)
[![Container Build](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml/badge.svg)](https://github.com/jmorrison-juniper/MistHelper/actions/workflows/container-build.yml)

This page is the entry point. It tells you what MistHelper is and how to start
it as a container. Every other subject has its own page, and the
[Documentation](#documentation) map below sends you there.

## What

MistHelper is a menu-driven tool for the Juniper Mist Cloud. It reads your
organizations, your sites, your devices, and your clients, and it writes what it
finds to a file or to a database. It also runs a small set of change operations,
such as a firmware upgrade.

The tool holds 269 operations. It also serves a web portal, an upgrade capture
portal, and a metrics gateway. Read [the operator
guide](documentation/operator-guide.md) for what each part does.

## Why

The Mist web interface answers one question at a time, on one page. An operator
who must report on a whole organization, or repeat the same read every week,
cannot work that way.

MistHelper turns each of those reads into one numbered operation. One operation
returns the whole organization in a CSV file or a database table, and a
scheduled job can run the same number again tomorrow. For a firmware upgrade, it
records the state of the site before the change and after it, so you hold
evidence of what moved.

Two rules shape the whole tool. An operation that changes the cloud asks for a
typed confirmation from a person. An automated test pass never runs one.

## Who

MistHelper is for the network operations engineer who owns a Mist organization.
It also serves a network operations center that runs the same report on a
schedule, and a managed service provider that works across more than one
organization.

You need a Mist API token. You do not need to write Python.

## Where

MistHelper runs as a container on your own machine or on your own server. The
container carries Python, every dependency, the two data stores, and both
portals.

It reaches the Mist Cloud API over HTTPS. It writes every output file to
`data/`, which the container shares with your machine. Your API token stays in
your local `.env` file and never leaves your host.

## When

Use MistHelper when you need one of these.

| You need | Start at |
|----------|----------|
| The whole organization in a CSV file or a database | [Menu reference](documentation/menu_reference.md) |
| The same export on a schedule | [Command line reference](documentation/cli-reference.md) |
| A record of a site before a firmware upgrade and after it | [Upgrade capture portal](documentation/upgrade_capture_portal.md) |
| A feed for Prometheus, Grafana, or an SNMP poller | [Operator guide](documentation/operator-guide.md) |
| A command run across many devices over SSH | [SSH guide](documentation/SSH_GUIDE.md) |

## How to set it up as a container

The container is the supported way to run MistHelper.

You need a container runtime. Podman is the documented runtime for this guide.
Docker parity is tracked in issue #2721.

### Step 1: Get the files

```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

### Step 2: Set your credentials

```powershell
cp documentation\sample.env .env
```

Open `.env` and set two values:

- `MIST_APITOKEN` holds your Mist API token.
- `MIST_HOST` names your Mist cloud, such as `api.mist.com`.

To create the token, sign in to <https://manage.mist.com>, open Organization,
then API Tokens, then create a token.

Warning: `.env` holds a live credential. The repository ignores that file. Never
commit it, and never paste its contents into an issue.

### Step 3: Let the data folder accept a write

```bash
chmod -R 777 data/
```

The container runs as the user `misthelper` and not as root, so it cannot write
to a folder that refuses it.

### Step 4: Start the stack

```powershell
.\scripts\compose.ps1 up -d
```

The command starts the default profile. It includes the application, the
document store, and the site lock store.

The script needs the native provider one time:

```powershell
.venv\Scripts\python.exe -m pip install podman-compose
```

Warning: on Windows, do not run `podman compose up -d`. That command starts the
stack without its application service, so nothing answers. The helper script
above picks a provider that works. Read [the container deployment
page](documentation/container-deployment.md) for the cause and for the other
deployment methods.

### Step 5: Check it

```powershell
podman ps
curl http://127.0.0.1:8055/ready
```

Three containers answer, and the address reports a ready state.

### Step 6: Open the menu

```powershell
podman exec -it misthelper-app python MistHelper.py
```

Type the number of an operation. The tool asks for anything else that it needs.
Read [the operator guide](documentation/operator-guide.md) for the portals, the
SSH access, the metrics gateway, and the output paths.

## Documentation

Start here, then follow the group that matches your task.

### Operate

| Page | What it holds |
|------|---------------|
| [Operator guide](documentation/operator-guide.md) | The menu families, the portals, SSH access, the metrics gateway, and where the output lands |
| [Menu reference](documentation/menu_reference.md) | Every operation, its safety level, and an example. Generated from the code. |
| [Menu API endpoint map](documentation/menu-api/README.md) | The Mist API endpoints that each menu option calls |
| [Menu highlights](documentation/menu-highlights.md) | The operations that arrived most recently |
| [Command line reference](documentation/cli-reference.md) | Every flag, the two test modes, and the output paths |
| [Upgrade capture portal](documentation/upgrade_capture_portal.md) | The operator guide for the portal on port 8056 |
| [SSH guide](documentation/SSH_GUIDE.md) | Remote access on port 2200 |
| [NOC runbooks](documentation/noc-runbooks) | Task guides for the operations center |

### Deploy

| Page | What it holds |
|------|---------------|
| [Container deployment](documentation/container-deployment.md) | The other deployment methods, the proxy certificate, and the rules that keep your data safe |
| [Security and safety](documentation/security.md) | The credential rules and the destructive operation rules |

### Understand

| Page | What it holds |
|------|---------------|
| [Architecture](documentation/architecture.md) | The package layout, the diagrams, and the decomposition record |
| [Diagram suite](documentation/diagrams/README.md) | All 20 Mermaid diagram types |
| [API notes](documentation/api) | The Mist API specification and the endpoint notes |
| [Changelog](CHANGELOG.md) | The version history |

### Develop

| Page | What it holds |
|------|---------------|
| [Development setup](documentation/development-setup.md) | Run the code from a source checkout |
| [Contributing](documentation/contributing.md) | The branch workflow, the labels, and the review rules |
| [Contributor map for `MistHelper.py`](documentation/CONTRIBUTING-MistHelper.md) | The stable symbols and the packages that guide entry-point changes |
| [Quality gates](documentation/quality-gates.md) | The quality gates that every pull request runs |
| [Release-note fragments](changelog.d/README.md) | The file that each change adds for its release note |
| [Writing guide](documentation/ASD-STE100_writing-guide.md) | The Simplified Technical English rules for every document |
| [Stranded branch review](documentation/stranded-branch-review.md) | Why a cleanup never deletes a branch that has no pull request |

### Wiki

The wiki holds the same subjects in a browsable form. Start at
[the wiki home page](https://github.com/jmorrison-juniper/MistHelper/wiki).
The wiki source is in `documentation/wiki/`. Edit it there, but read it on
the wiki: its page-to-page links work only on the published wiki.

| Wiki page | What it holds |
|-----------|---------------|
| [Menu Reference](https://github.com/jmorrison-juniper/MistHelper/wiki/Menu-Reference) | Every actionable menu operation |
| [Menu API Endpoints](https://github.com/jmorrison-juniper/MistHelper/wiki/Menu-API-Endpoints) | The endpoints behind each menu option |
| [Container Setup](https://github.com/jmorrison-juniper/MistHelper/wiki/Container-Setup) | Build strategies and local usage |
| [Web Portal](https://github.com/jmorrison-juniper/MistHelper/wiki/Web-Portal) | Browser-based operations and the map viewer |
| [SSH Remote Access](https://github.com/jmorrison-juniper/MistHelper/wiki/SSH-Remote-Access) | SSH server deployment and session management |
| [Data Model](https://github.com/jmorrison-juniper/MistHelper/wiki/Data-Model) | CSV, SQLite, and polyglot output details |
| [MSP Support](https://github.com/jmorrison-juniper/MistHelper/wiki/MSP-Support) | Multi-org operations for a managed service provider |
| [Maps Manager](https://github.com/jmorrison-juniper/MistHelper/wiki/Maps-Manager) | The standalone interactive map viewer |
| [Performance](https://github.com/jmorrison-juniper/MistHelper/wiki/Performance) | Rate limiting and fast mode |
| [Troubleshooting](https://github.com/jmorrison-juniper/MistHelper/wiki/Troubleshooting) | Common issues and solutions |
| [Testing](https://github.com/jmorrison-juniper/MistHelper/wiki/Testing) | Systematic test mode and the CI pipeline |
| [Support](https://github.com/jmorrison-juniper/MistHelper/wiki/Support) | How to get help and report an issue |

## License

CC-BY-NC-SA-4.0, the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International license.
