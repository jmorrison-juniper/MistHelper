# Operator guide

This page holds the day-to-day operator content that the `README.md` file
carried before issue #3428. The README is now the entry point that answers what
MistHelper is and how to start the container. This page tells you what to do
next.

Read [the container deployment page](container-deployment.md) first if the stack
does not start.

## The menu

The tool holds **269 operations**, numbered 1 to 270 with one gap at 152. Menu 0
is Exit. Read [the menu reference](menu_reference.md) for the full list, which is
generated from the code.

Menu 259 runs no-identifier Mist get and list endpoints from a prompt. Menu
260 runs org-scoped endpoints. Menu 261 runs site-scoped endpoints. Menu 262
runs MSP-scoped endpoints. Together they cover 152 unique simple endpoint
operations from issue #1807.

Menus 263 through 268 run the remaining read-only endpoint families. They group
SLE, map, site detail, org detail, MSP detail, and other endpoints by prompt
flow. Menus 259 through 268 each map to the Mist API endpoint families named in
[the menu API endpoint map](menu-api/README.md).

Menu 270 exports the Marvis Actions of an organization to a CSV file and to the
database. You can filter the actions by category and by subcategory. Mode 1
exports every action. Mode 2 exports the open actions, and mode 4 exports the
closed actions. Each exported row also holds the status, the resolve time, and
the acknowledge values of its Marvis alarm.

Mode 3 marks the open actions of the selected topics as resolved, with a
resolution code and a comment. Mode 3 sends no request until you type `RESOLVE`
and the action count. Read
[the Marvis Actions API endpoint report](marvis-actions-api-endpoints.md)
for every API call that the menu makes.

## What MistHelper does

| Area | What you get |
|------|--------------|
| Export | Device inventory, site data, client sessions, events, alarms, and statistics |
| Search | Any org-scoped or site-scoped Mist search endpoint, from a prompt |
| Output | CSV files, a SQLite database, or ArangoDB with Redis |
| Devices | SSH command runs, packet captures, and configuration reads |
| Upgrades | A firmware upgrade with a capture of the site state before it and after it |
| Portals | A web portal on port 8055, and an upgrade capture portal on port 8056 |
| Monitoring | A metrics gateway on port 8057 that serves Prometheus and SNMP |

Two rules shape the whole tool. An operation that changes the cloud asks for a
typed confirmation from a person. An automated test pass never runs one.

## Start a container for a test or a debug session

A container that you start for a test, for a debug session, or for an
end-to-end run follows four rules.

1. Start it inside the compose group with `.\scripts\compose.ps1`. Never start
   a one-off container with a bare `podman run`.
2. Name it for the issue or the pull request that it serves. Use the format
   `misthelper-tmp-<issue|pr><number>-<slug>`.
3. Publish a port in the range 9600 through 9699. Never publish a production
   local port. Read `../compose.yml` for the current production ports.
4. Remove the container, its volume, and its network when the test ends.

Read [the container deployment page](container-deployment.md) for the full
policy and the cleanup commands. The cleanup proof must show no
`misthelper-tmp-` containers or volumes.

## Use

### Open the menu

```powershell
podman exec -it misthelper-app python MistHelper.py
```

Type the number of an operation. The tool asks for anything else that it needs.

### Run one operation

```powershell
podman exec misthelper-app python MistHelper.py -M 11
```

`-M 11` exports the organization inventory. Any menu number works there, which
suits a scheduled job. Read [the command line
reference](cli-reference.md) for every flag.

### Run the global wired client report

Menu 90 builds the global wired client report. It asks for optional MAC and
manufacturer filters. It writes the same matched records to the normal export
path and to `data\GlobalWiredClientReport_summary.json`.

Deployment verification for issue #993 ran on 2026-09-14 UTC. The operator
pulled `ghcr.io/jmorrison-juniper/misthelper:latest`, restarted
`misthelper-app` with `.\scripts\compose.ps1 up -d --no-deps misthelper`, and
checked the web readiness endpoint. `podman ps` reported `misthelper-app` as
running from the latest image. `http://127.0.0.1:8055/ready` returned 200.

### Reach the tool over SSH

The container runs an SSH server on port 2200. A connection opens the menu at
once and reaches no shell.

```powershell
ssh -p 2200 misthelper@127.0.0.1
```

Read [the SSH guide](SSH_GUIDE.md) for the setup.

### Open a portal

| Portal | Address | Purpose |
|--------|---------|---------|
| Web portal | <http://127.0.0.1:8055/> | Browse the data that the tool collected |
| Upgrade capture portal | <http://127.0.0.1:8056/> | Record a site before a firmware upgrade and after it, then read what changed |

In the upgrade capture portal, a capture is one record of site state and not a
packet capture. Read [the portal
guide](upgrade_capture_portal.md).

The upgrade capture portal shows stale runs with a `Stale` badge and a
last-update age. The server owns the stale decision.

Bulk actions start with an authoritative server preview. The preview returns
the visible run list, counts, and required phrase. For cancel, type
`CANCEL <run-count> RUNS`. For retry, type `RETRY <run-count> RUNS`.

Use bulk cancel for pre-cloud runs. Use bulk retry for final failed, stopped,
or cancelled runs. The run page also includes reconciliation for eligible stale
runs. It sends no firmware, stop, or cancel request to Mist.

Read [the portal guide](upgrade_capture_portal.md) for the full
operator flow and deployment rules.

### Watch the network from a monitoring system

Menu 241 starts a metrics gateway on port 8057. The gateway reads your
organization on a timer and holds the last reading, so a monitoring system polls
the gateway and never polls Mist Cloud. Your Mist token stays in `.env`.

```powershell
podman exec misthelper-app python MistHelper.py --metrics-gateway
```

The gateway serves the same reading two ways.

| Path | Address | Reads |
|------|---------|-------|
| Prometheus | <http://127.0.0.1:8057/metrics> | Prometheus, Grafana, Zabbix, LibreNMS, Icinga |
| SNMP | Net-SNMP `pass_persist` | Any SNMP poller |

Prometheus is the path to choose. It needs no MIB and no registered enterprise
number, and it binds an unprivileged port.

The container starts Net-SNMP on UDP port 1161. Choose a community string and
set `SNMP_COMMUNITY` in `.env`. Choose a base OID under an enterprise number
that you own.

```powershell
.\scripts\compose.ps1 up -d
snmpwalk -v2c -c <community> -On 127.0.0.1:1161 .1.3.6.1.4.1.8072.9999.9999
```

| Setting | Default | Meaning |
|---------|---------|---------|
| `METRICS_ORG_ID` | unset | The organization to report. The menu asks when this is unset |
| `METRICS_PORT` | `8057` | The listen port |
| `METRICS_HOST` | `127.0.0.1` | The bind address. A container takes every address |
| `METRICS_REFRESH_SECONDS` | `900` | The age at which a reading becomes stale. The floor is 60 |
| `METRICS_SITE_IDS` | unset | A comma list of sites. Unset reports every site |
| `METRICS_SNMP_BASE_OID` | `.1.3.6.1.4.1.8072.9999.9999` | The base OID that the responder serves |
| `SNMP_BASE_OID` | `.1.3.6.1.4.1.8072.9999.9999` | The base OID that `snmpd.conf` names |
| `SNMP_PORT` | `1161` | The UDP listen port |
| `SNMP_COMMUNITY` | `misthelper` | The read-only SNMP community |

Warning: `SNMP_BASE_OID` and `METRICS_SNMP_BASE_OID` must hold the same value.
`snmpd` routes a request by the first value, and the responder answers by the
second. Two different values make every read return `No Such Instance`.

Warning: The gateway asks for no password. Keep the default loopback bind unless
a reverse proxy holds the access control.

Read `mist_scrape_success` and `mist_scrape_age_seconds` in your alarm rules. A
failed read of Mist Cloud keeps the last good reading, so those two values are
how you tell a stale reading from a real outage.

#### Read the metrics by name

The file `mibs/MISTHELPER-MIB.mib` gives every number a name. Load
it into your monitoring system to see `mistOrgSites` in place of
`.1.3.6.1.4.1.8072.9999.9999.1.2.0`.

The MIB describes four groups.

| Group | OID below the base | Source endpoint |
|-------|--------------------|-----------------|
| Organization scalars | `.1.<column>.0` | `getOrgStats` |
| Site table | `.2.1.<column>.<row>` | `listOrgSiteStats` |
| Device table | `.3.1.<column>.<row>` | `listOrgDevicesStats` |
| Expectation table | `.4.1.<column>.<row>` | The `sle` array of `getOrgStats` |

Column 99 of each table repeats the row identity. Read it to learn which site,
device, or expectation a row describes.

Warning: a row number is a position, not a permanent key. The gateway sorts the
rows on every read of Mist Cloud. An alarm that names a row number can move to
another device. Match on column 99 instead.

Caution: the default branch `.1.3.6.1.4.1.8072.9999.9999` sits below the
Net-SNMP experimental number. Request a registered branch before you use this
MIB outside your own network.

#### Add the gateway to Observium

Observium is an SNMP monitoring system. The compose file carries it behind a
profile, so it starts only when you ask for it.

```powershell
.\scripts\compose.ps1 --profile monitoring up -d
```

The command starts Observium on <http://127.0.0.1:8668>. Sign in with the user
`observium` and the password `observium`, then change that password. The compose
file mounts the MIB into the container, so no operator copies a file.

Add the gateway as a device in the Observium web interface.

| Field | Value |
|-------|-------|
| Hostname | `misthelper-app` |
| Port | `1161` |
| Transport | `udp` |
| SNMP version | `v2c` |
| Community | The value of `SNMP_COMMUNITY` |

Turn on **Skip ICMP**, because the container answers no ping.

Confirm the reading first, if the device does not add:

```powershell
podman exec misthelper-observium snmpget -v2c -c misthelper -t 20 misthelper-app:1161 .1.3.6.1.4.1.8072.9999.9999.1.2.0
```

The first read returns `No Such Instance`. `snmpd` starts the responder when it
routes that first request, and the responder then reads Mist Cloud in the
background. It answers at once and never makes a poller wait. Read again about
one minute after the first read.

If every read times out, the container cannot reach Mist Cloud. Read the
container log for the line that starts with `[DNS]`.

### Find your output

The tool writes every file under `data/`, which the container shares with your
machine.

| Output | Place |
|--------|-------|
| CSV files | `data/` |
| SQLite database | `data/mist_data.db` |
| Runtime log | `data/script.log` |
