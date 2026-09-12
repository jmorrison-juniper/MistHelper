# Handoff — SNMP responder and Observium native sensors

Written 2026-09-05. No branch. Every commit landed straight on `main`
(single-agent session, no PR). Read this before you touch SNMP, the
Observium container, or `container/observium/`.

## Current state — this works right now

All four containers run and are healthy: `misthelper-app`,
`misthelper-observium`, `misthelper-arangodb`, `misthelper-redis`. Start them
with `.\scripts\compose.ps1 --profile monitoring up -d`. Never use bare
`podman compose` (see `container-deployment.md` for why).

Real Mist Cloud data flows end to end, with zero manual steps after
`compose up`:

1. MistHelper's SNMP responder (`--metrics-snmp`, invoked by `snmpd` through
   `pass_persist`) answers on UDP port 1161 with live data from org
   "Morrison House": 144 sites, 13 devices, 6 SLE (service level expectation)
   rows.
2. `MISTHELPER-MIB.mib` is installed in Observium and Net-SNMP resolves every
   name in it (`snmptranslate`, `snmpwalk -m MISTHELPER-MIB` both work).
3. Observium has `misthelper-app` as device ID 6, discovered and polling on
   a normal cycle (`poller.php` takes 40-65 seconds for the whole device,
   well inside a 300-second cycle).
4. **1349 native Observium sensors**, not just raw SNMP values reachable by
   hand:
   - Gauge: 1315 (org scalars, site counts, device counts)
   - Age: 14 (device uptime, org scrape age)
   - Quality Factor: 6 (SLE ratios — coverage, roaming, throughput, etc.)
   - Status: 13 (device up/down, colored red when down, `alert` event)
5. Survives a full `compose down` + `compose up` with no manual step. Every
   init script is idempotent (checked by re-running the cycle twice this
   session).

Read `agents.md` / `.github/copilot-instructions.md` for the project-wide
rules this work follows (STE writing, inline comments, action logging,
5-item rule, git-flow-multi-agent). Nothing here overrides those.

## Root causes fixed, in order

Each one blocked the next. Fix them in this order if you ever have to redo
this from scratch.

1. **`snmpd` was never installed.** `Containerfile` listed `ca-certificates
   openssh-server sudo` only. `start.sh` tried to run `/usr/sbin/snmpd`,
   found nothing, and failed silently. Fixed: added `snmpd snmp` to the
   `apt-get install` line (the `snmp` package adds `snmpget`/`snmpwalk` for
   diagnostics inside the container).
2. **compose.yml pulled the stale registry image.** `image:
   ghcr.io/jmorrison-juniper/misthelper:latest` skipped the `build:` section
   entirely, so the fix in step 1 never reached a running container. Fixed:
   changed to `image: misthelper:local` with `build:` active, so `compose up`
   always builds fresh from the local `Containerfile`.

   **This is a real, unresolved tension.** The pre-existing comment on that
   line said the registry image is "the one CI builds and tests," and
   pinning to a local build risks drifting from what CI validates. See
   "Open question 1" below. Do not silently keep either choice — ask.
3. **SNMP env vars were never set.** `compose.yml` referenced
   `${SNMP_BASE_OID:-...}` etc. with defaults, but nothing in `.env` set them,
   so `snmpd.conf` got the fallback OID
   (`.1.3.6.1.4.1.11.2147483646`, the upstream `mist_library` OID), not the
   one this repo's MIB actually uses. Fixed: added to `.env`:
   ```
   SNMP_PORT=1161
   SNMP_COMMUNITY=misthelper
   SNMP_BASE_OID=.1.3.6.1.4.1.8072.9999.9999
   METRICS_SNMP_BASE_OID=.1.3.6.1.4.1.8072.9999.9999
   ```
   **Warning: `deploy/.env.example` still shows the OLD OID
   (`.1.3.6.1.4.1.11.2147483646`) as its commented-out example default.** A
   deployer who copies that file verbatim gets a responder that answers on
   the wrong subtree, and `MISTHELPER-MIB.mib` will not resolve any of it.
   Fix `deploy/.env.example` before the next deploy. Not done this session.
4. **`mistapi.ApiSession()` does not exist.** The real class is
   `mistapi.APISession` (capital `API`). This raised `AttributeError` on
   every single `pass_persist` invocation — the responder crashed before it
   could answer `PING`, so `snmpd` killed the child and net-snmp fell back to
   `No Such Instance` for the whole subtree. The process kept respawning
   every 3-5 seconds; that is the tell if you see it again. Fixed: both
   `_run_metrics_snmp` and `_launch_metrics_gateway` in `MistHelper.py` now
   call `MistSessionInitializer.initialize()`
   (`src/refactors/initialize_mist_session.py`) — the same seam every other
   MistHelper entry point uses. It handles retries, rate limiting, and the
   legacy `Session()` fallback, and it writes the authenticated session to
   the module-level `apisession` global that `build_cache()` reads.
5. **Observium's base image disables all MIB loading by default.** Ships
   `mibs :` and a commented-out `mibdirs` line in `/etc/snmp/snmp.conf`
   (Debian's own license-driven default — see the comment already in the
   file). `MISTHELPER-MIB.mib` imports `SNMPv2-SMI`/`SNMPv2-TC`, so without a
   fix, `snmptranslate`/`snmpwalk -m MISTHELPER-MIB` failed with "Cannot
   adopt OID" for every single entry, even though the IETF set Observium
   already bundles at `/opt/observium/mibs/rfc` was sitting right there.
   Fixed: `container/observium/10-fix-mib-search-path.sh`, mounted into
   `/etc/my_init.d/`, rewrites `snmp.conf` on every start (`mibs +ALL` plus
   the real `mibdirs` list). Idempotent via a marker line.
6. **Observium has no built-in way to show a custom vendor MIB.** Its `/os/`
   and `/mibs/` pages are driven by a closed, pre-compiled catalog
   (`includes/definitions/definitions.dat`, ~797 vendor types) that only
   Observium's own build process extends. The one Community Edition
   feature for this ("Custom OID," `docs.observium.org/customoid/`) is
   Subscription Edition only and absent from this image. Fixed: found the CE
   equivalent, "static sensors" (`docs.observium.org/statics/`) — discovery
   code for it already ships in CE, unconditionally, and an operator turns
   it on via `config.php`. Wrote `container/observium/20-add-mist-static-sensors.sh`
   to append that block automatically, looked up by hostname (not a hard
   device ID, so a device delete/re-add needs no manual edit).
7. **PHP-side MIB table walks silently returned nothing, even after fix 5.**
   Every Observium PHP helper that resolves a MIB by name
   (`snmpwalk_cache_oid()`, `snmp_walk()`) builds its own net-snmp `-M` flag
   via `snmp_mib2mibdirs($mib)`, reading `$config['mibs'][$mib]['mib_dir']`
   — a **separate** mechanism from the `/etc/snmp/snmp.conf` `mibdirs` line
   fix 5 wrote. `-M` **replaces** net-snmp's whole search path instead of
   adding to it, so a bare CLI `snmpwalk -m MISTHELPER-MIB` kept working (it
   still reads `snmp.conf`) while every PHP table walk returned an empty
   string. This one cost the most debugging time. Fixed: added
   `$config['mibs']['MISTHELPER-MIB']['mib_dir'] = 'mibs';` to the same
   `20-add-mist-static-sensors.sh` script (the literal string `'mibs'` is
   `mib_dirs()`'s own token for "the bare mib directory root").
8. **`mysqli_connect('localhost', ...)` tried a Unix socket, not TCP.** This
   image's MariaDB has no socket file, TCP-only on `127.0.0.1`. A
   diagnostic script hit "Connection refused"/"No such file or directory"
   even though Observium's own framework connects fine (it forces TCP
   internally, a detail not exposed to a raw `mysqli_connect()` call). Fixed
   by normalizing `'localhost'` to `'127.0.0.1'` before connecting, inside
   the sensor-registration script (only place this repo makes a raw mysqli
   connection outside Observium's own code).
9. **`discover_status_ng()` needs the literal MIB name `'STATIC'`, not the
   real MIB name, to find a custom status-state map.**
   `get_states_definition()` (`includes/entities/status.inc.php`) only
   checks `$config['status']['static_states'][$type]` on the exact `'STATIC'`
   fast path — the same path the documented static-status feature uses.
   Passing `'MISTHELPER-MIB'` sent it to the standard MIB-derived lookup,
   which found nothing, and the status silently never got created (no
   error, just zero rows). Fixed in
   `container/observium/discovery-sensors-unix.inc.php`.

## How the pieces actually fit together

```
Mist Cloud API
     |
     v  (MistSessionInitializer, mistapi.APISession)
MistHelper.py --metrics-snmp   (subprocess, spawned by snmpd's pass_persist)
     |  build_cache() -> MetricsCache -> SnmpPassPersistResponder
     v  answers PING / get / getnext on stdin/stdout
snmpd (udp:1161, agentAddress from SNMP_PORT env var)
     |
     v  SNMP v2c, community "misthelper"
Observium poller (poller.php, on its own schedule)
     |
     +-- Org scalars (9 of them) --------> config.php "static sensors"
     |     (container/observium/20-add-mist-static-sensors.sh)
     |
     +-- Site / Device / SLE tables -----> discovery.php table walk
           (container/observium/discovery-sensors-unix.inc.php,
            mounted at includes/discovery/sensors/unix.inc.php,
            runs for every Linux/Unix device -- guarded by a probe
            snmpget so other devices are skipped cheaply)
     |
     v
Observium sensors / status tables --> Health tab (Gauge / Age /
Quality Factor / Status sub-tabs), RRD graphs, alert coloring
```

The org scalars (fixed count, 9 columns) use the **static** mechanism
because a fixed list never drifts. The three tables (site count changes
when a NOC adds a site, device count changes when Mist retires a device)
use **discovery-time table walk** instead, because a static list would go
stale. No polling-side PHP file exists for the table sensors —
`includes/polling/sensors.inc.php` already replays every sensor's own
stored OID generically, whichever mechanism discovered it.

## Files actually part of this work

```
Containerfile                                        (snmpd + snmp packages)
MistHelper.py                                         (MistSessionInitializer fix, both call sites)
compose.yml                                           (local build+image, SNMP env vars, 3 my_init.d mounts, MIB mount rw)
.env                                                   (git-ignored -- SNMP_PORT/SNMP_COMMUNITY/SNMP_BASE_OID/METRICS_SNMP_BASE_OID)
container/observium/10-fix-mib-search-path.sh          (new)
container/observium/20-add-mist-static-sensors.sh      (new)
container/observium/discovery-sensors-unix.inc.php     (new)
```

**Warning: some early commits this session are noisy.** `e16e3d36` and
`df9291ea` swept in unrelated files from a concurrent agent's work on
feature 1823 (upgrade capture portal) because an early `git add -A` was too
broad before a narrower staging habit took hold. Those files are not part
of this thread. Use `git show <hash> -- <path>` for a clean look at one
file, not a bare `git show <hash> --stat`, if you need to audit exactly
what a given commit touched.

Commits, in order: `e16e3d36`, `626d975c`, `df9291ea`, `d3d006c8`,
`2759a0f4`, `4dbafabb`.

## Verification commands — run these to re-prove the state above

All assume `misthelper-app` reports as device ID 6 in Observium. Check the
real ID first if in doubt:
```powershell
podman exec misthelper-observium bash -c 'cd /opt/observium && php -r "
require(\"config.php\");
$link = mysqli_connect(\"127.0.0.1\", $config[\"db_user\"], $config[\"db_pass\"], $config[\"db_name\"]);
$r = mysqli_query($link, \"SELECT device_id, hostname, status FROM devices WHERE hostname=\\\"misthelper-app\\\"\");
print_r(mysqli_fetch_assoc($r));
"'
```

**SNMP responder answers with real data:**
```powershell
podman exec misthelper-app bash -c 'MIBS= snmpget -v 2c -c misthelper localhost:1161 .1.3.6.1.4.1.8072.9999.9999.1.1.0'
# Expect: iso.3.6.1.4.1.8072.9999.9999.1.1.0 = STRING: "Morrison House"
```

**MIB name resolution works inside Observium:**
```powershell
podman exec misthelper-observium bash -c 'snmpget -v2c -c misthelper -m MISTHELPER-MIB misthelper-app:1161 .1.3.6.1.4.1.8072.9999.9999.1.1.0'
# Expect: MISTHELPER-MIB::mistOrgInfo.0 = STRING: Morrison House
```

**Sensor counts match what this file claims (adjust device_id if not 6):**
```powershell
podman exec misthelper-observium bash -c 'cd /opt/observium && php -r "
require(\"config.php\");
$link = mysqli_connect(\"127.0.0.1\", $config[\"db_user\"], $config[\"db_pass\"], $config[\"db_name\"]);
$r = mysqli_query($link, \"SELECT sensor_class, COUNT(*) cnt FROM sensors WHERE device_id=6 AND sensor_deleted=0 GROUP BY sensor_class\");
while ($row = mysqli_fetch_assoc($r)) { echo $row[\"sensor_class\"] . \"=\" . $row[\"cnt\"] . \" \"; }
echo \"\n\";
$r2 = mysqli_query($link, \"SELECT COUNT(*) cnt FROM status WHERE device_id=6\");
echo \"status=\" . mysqli_fetch_assoc($r2)[\"cnt\"] . \"\n\";
"'
# Expect: age=14 gauge=1315 quality_factor=6 voltage=1  (plus) status=13
# The one voltage sensor is LM-SENSORS-MIB, unrelated to this work.
```

**Full re-discovery and re-poll (use if numbers above do not match):**
```powershell
podman exec misthelper-observium bash -c 'cd /opt/observium && php discovery.php -h misthelper-app -m sensors'
podman exec misthelper-observium bash -c 'cd /opt/observium && php poller.php -h misthelper-app'
```

**Init scripts ran clean on last start (no error, no permission fault):**
```powershell
podman logs misthelper-observium 2>&1 | Select-String "MIB-PATH|MIST-SENSORS|Read-only|chown"
# Expect exactly two lines, no "Read-only" or "chown" text:
#   [MIB-PATH] Rewrote /etc/snmp/snmp.conf: ...
#   [MIST-SENSORS] Appended the Mist static sensor block ... (first start)
#     -- or --
#   [MIST-SENSORS] .../config.php already carries the Mist static sensors. Nothing to do. (later starts)
```

**Web UI reachable (allow 90-130 seconds after a full container recreation
before this returns 200 -- see the MariaDB timing note below):**
```powershell
podman exec misthelper-observium bash -c 'curl -s -o /dev/null -w "HTTP_STATUS:%{http_code}\n" http://localhost:8668/'
```

## Still owed

1. **Fix `deploy/.env.example`'s stale SNMP_BASE_OID default.** See root
   cause 3 above. This is a real trap for the next deployer.
2. **`Dockerfile` (the Docker path, as opposed to `Containerfile` for
   Podman) has `snmpd` but not the `snmp` package.** A Docker-built image
   would run the responder fine, but a NOC engineer inside that container
   would have no `snmpget`/`snmpwalk` for diagnostics. Minor, but a real gap
   between the two build paths that are supposed to be equivalent.
3. **The stale `container/config/snmpd.conf` reference file.** Not used by
   the running system (`start.sh` generates its own `snmpd.conf` dynamically
   at every start), but it still exists in the repo and could mislead
   someone who finds it before finding `start.sh`. Decide: delete it, or add
   a comment saying it is not live.
4. **Real sub-tab grouping inside "Gauge" was not achieved.** The user
   asked for it. What exists instead: every sensor's description is
   prefixed with its row label (`Site X:`, `Device Y:`, `Mist ...`), and
   clicking Observium's own sortable "Description" column header
   (`.../metric=gauge/view=details/sort=descr/`) clusters them
   alphabetically as a side effect. That is a real workaround, not a true
   grouped view. If the user wants actual collapsible categories, that
   needs a change to Observium's own health-tab template code (a much
   bigger, more invasive change than anything else in this file), or moving
   more classes out of Gauge the way `status` and `quality_factor` already
   were.
5. **No automated test covers any of this.** Every check this session was
   a live, manual `podman exec` verification against the running stack.
   Nothing here runs in CI. If this work needs to survive a container
   image rebuild in six months, it needs at least a smoke test.

## Open questions for the user — do not decide alone

1. **Should `misthelper-app` build locally in `compose.yml` permanently, or
   go back to pulling the registry image?** Root cause 2 above. The
   registry image (as of this session) has no `snmpd`, so a plain
   `git pull` + `compose up` on another machine would silently lose SNMP
   support unless that image is rebuilt and pushed through
   `container-build.yml` first. Ask whether to (a) trigger that workflow
   now so the registry catches up, then revert `compose.yml` to
   `image: ghcr.io/...`, or (b) keep the local build permanently and accept
   the drift-from-CI risk the original comment warned about.
2. **Should the pending SpecKit MIB-generator tasks (see next section) run
   before or after any more work on this thread?** They are a separate,
   already-scoped body of work with their own handoff file.

## Separate, unrelated backlog — do not conflate with this thread

The session's todo tracker also holds 8 pending items, `p1-setup` through
`p8-gates`, all belonging to a **different** SpecKit feature: a Python
module that ingests the Mist OpenAPI spec and generates
`MISTHELPER-MIB.mib` automatically (so a future Mist API release does not
need a hand-edited MIB). That feature has its own dedicated handoff file
already, written before this thread started:

**`HANDOFF-mib-generator.md`**, in this same `files/` folder.

Read that file, not this one, before touching `src/mib_generator/`,
`data/mib_generator/`, or the generator's tests. Checkpoints 4 through 7 in
this session (`004-auto-generating-snmp-mibs-from.md` through
`007-completing-snmp-integration-wi.md`) cover that thread's history. The
`MISTHELPER-MIB.mib` this SNMP/Observium thread relies on was produced by
that generator, so the two threads share one output file but are otherwise
independent bodies of work.

## Environment facts that cost time — read before you repeat the mistakes

- **Shell scripts mounted into the container must use LF line endings.**
  A CRLF-saved `.sh` file breaks its own shebang inside the container (the
  interpreter reads `\r\n` as part of the interpreter name) and `my_init`
  reports exit status 127 ("command not found") in a restart loop. Every
  file under `container/observium/` in this session needed an explicit LF
  conversion after editing on Windows. Verify with:
  ```powershell
  $bytes = [System.IO.File]::ReadAllBytes("path\to\file.sh")
  ($bytes | Where-Object { $_ -eq 13 }).Count   # Must be 0
  ```
- **A file bind-mounted under `/opt/observium` must not be `:ro`.**
  `firstrun.sh` (the base image's own init script) runs
  `chown nobody:users -R /opt/observium` on every start. A read-only mount
  there fails that one file with "Read-only file system" every single
  boot — harmless to content (chown only touches ownership), but noisy and
  worth avoiding. Both the MIB file and the new discovery `.inc.php` file
  are mounted read-write for this reason.
- **This Observium image's MariaDB takes noticeably long to become ready
  after a full container recreation** — about 90-130 seconds, spent fixing
  file permissions on the database directory before `mysqld` even starts.
  A `curl` or `mysqli_connect` probe run too early gets "Connection
  refused," which looks like a real fault but is just a timing race. Wait
  and retry before concluding something is actually broken.
- **Podman's internal DNS (`aardvark-dns`) accumulates stale `A` records**
  across repeated container recreations of the same service name during a
  debugging session (`getent hosts misthelper-app` returned three
  different IPs at one point, only one of them current). A normal
  single-recreate deployment will not see this; it only showed up because
  this session recreated `misthelper-app` many times in a row. `snmpget`
  by hostname still worked despite the stale records (net-snmp tries every
  resolved address), so this never actually blocked anything, but do not
  be alarmed if you see it.
- **`podman inspect <container> --format '{{...}}'` chokes on a
  hyphenated key** like `misthelper-network` inside a Go template
  (`bad character U+002D '-'`). Use `--format '{{range
  .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'` instead of trying to
  index the map by name directly.

## The user's earlier question, now fully answered

Before this thread, the user asked whether the MIB was loaded into
Observium. The honest answer, now proven both ways:

- The MIB **file** was always correctly installed and Net-SNMP tools
  always parsed it once the search-path fix (root cause 5) landed.
- It never showed up on Observium's own `/os/` or `/mibs/` catalog pages,
  because those pages list only Observium's own closed, pre-compiled
  vendor set — no amount of file placement changes that.
- Every stat the checked-in metric catalog (`src/metrics_gateway/catalog.py`)
  actually defines now shows up as a genuine, native Observium sensor with
  real polled values, RRD graphs, and correct alert coloring. That gap is
  closed as far as the catalog goes.

## Scheduled run — 2026-09-05

Implemented issue #1893 on branch `fix/1893-bootstrap-github-account`.
Commit `7e850faf` is pushed to origin. The branch uses worktree
`C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-1893-github-account`.

The worktree bootstrap now writes the repository-local Git credential username
for `jmorrison-juniper` and reports configuration failures. Tests cover both
the successful and failed Git configuration paths. The bootstrap guidance now
states how `GH_TOKEN` and `GITHUB_TOKEN` can override the stored account.

Validation passed:

- `tests/unit/bootstrap/test_github_account_checker.py`
- `tests/unit/bootstrap/test_pip_index_probe.py`
- `ruff check` for changed Python files
- `black --check` for changed Python files

Issue #1893 received the session summary comment. No pull request was opened.
The existing untracked SpecKit context files remain in the main worktree.

Session Summary

Issues Reviewed: 6
Issues Created: 0
Issues Updated: 1
Tests Added: 2
Coverage Improvement: targeted bootstrap account paths
Bugs Fixed: 1
Security Findings: 0
PRs Generated: 0 (blocked by policy)

Remaining High Priority Work:

- Review and merge `fix/1893-bootstrap-github-account` when repository policy permits.
- Resolve issue #2272, which still documents the compose rebuild and image provenance risk.
