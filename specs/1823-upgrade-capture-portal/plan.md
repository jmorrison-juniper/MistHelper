# Implementation Plan: Upgrade Pre-Check and Post-Check Portal

**Branch**: `feat/1823-upgrade-capture-portal` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1823-upgrade-capture-portal/spec.md`

## Summary

The feature adds a browser application that records the state of a site before a
firmware upgrade, drives the upgrade, waits for the site to settle, records the
state again, and reports every difference between the two records.

The technical approach has five parts.

1. A new Python package at `src/upgrade_portal/` holds the application. The
   package sits outside `web_portal/`, because the repository excludes
   `web_portal/` from ruff and from mypy.
2. A new module at `src/firmware/upgrade_service.py` gives the portal a clean
   seam into the upgrade endpoints. The four existing upgrade classes hold 1271
   `print` calls and 80 `input` calls, so a web request cannot drive them.
3. A capture reads six independent call groups in parallel through
   `ConnectionPoolExecutor`. The pages inside one group stay sequential, because
   the cloud paginates with a cursor.
4. A capture document goes to ArangoDB under a natural key. The portal reads the
   key back and reports the true result, because the router can report success
   after it writes zero rows.
5. A Redis key holds the site lock. The lock survives a restart and works across
   worker processes.

## Technical Context

**Language/Version**: Python 3.13+. `pyproject.toml` requires `>=3.13` and targets
`py313`. The constitution binds the same minimum.

**Primary Dependencies**: `mistapi` 0.63.3 (installed and verified), Flask 3.x with
`flask-wtf` for cross-site request forgery protection, `redis` for the site lock,
`python-arango` through the existing `DatabaseRouter`, and `structlog` inside
`src/db` only. The plan adds no new third-party dependency. Bootstrap 5 is already
vendored under `web_portal/static/vendor/bootstrap/` and the new application
vendors its own copy.

**Storage**: ArangoDB is the primary store, through
`DataExporter.write_with_format_selection()` and `DatabaseRouter`. Two new
collections hold captures and upgrade runs. One edge collection joins them. CSV
under `data/` is the fallback. Redis holds the site lock and the run heartbeat
only. Redis never holds a capture, because every Redis JSON key expires after 7
days and FR-032a forbids an expiring path.

**Testing**: `pytest` with `pytest-cov`. Unit tests cover the pure functions.
Contract tests cover the HTTP surface with the Flask test client. Playwright
covers the browser journeys, because the specification requires a screenshot and
a trace on a failed interface test. Playwright already exists at
`pyproject.toml:78` and has no consumer today.

**Target Platform**: Linux container under Podman, plus a direct command-line
launch on Windows and Linux for a developer. Gunicorn with the `gthread` worker
class serves the container. The command-line launch uses the Flask development
server, which matches the current behavior of the existing portal.

**Project Type**: Web application inside a larger command-line application. The
browser side uses server-rendered templates and a small amount of plain
JavaScript. No build step exists and none is added.

**Performance Goals**: A Tier 2 capture of a 250-device site completes in 90
seconds or less (SC-002). A settle gate evaluates every device of one type in one
polling round of 20 seconds. A comparison page renders in 3 seconds or less
(SC-005). One upgrade run consumes at most 7.2 percent of the hourly API quota.

**Constraints**: The rate limit is 5000 API calls each hour for each token, for
each process. Every asset must load from the application itself, because the
content security policy is `'self'` only. The portal must never show, log, or
store a password value or a token value (FR-009). Every log line uses stdlib
`logging` with `%s` placeholders and ASCII characters only. Every function obeys
the Five-Item Rule: at most 5 parameters, 5 blocks, 5 operations for each block,
and 25 lines.

**Scale/Scope**: Up to 10 concurrent operators. Up to 6 sites under upgrade at the
same time, one operator for each site. A site of up to 250 devices and up to 5000
clients. About 106 functional requirements across 6 user stories. The estimated
new code is 25 modules inside `src/upgrade_portal/`, 1 module inside
`src/firmware/`, and about 14 templates.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Constitution version 1.4.0.

| Principle | Verdict | How the design complies |
| --- | --- | --- |
| I. Five-Item Rule | PASS with one tracked violation | The new package holds exactly 5 subpackages. Each subpackage holds exactly 5 modules. Every public function takes at most 5 parameters, because a request context object carries the rest. The tracked violation is the child count of `src/`, which the feature increases from an already high number. See Complexity Tracking. |
| II. Class-Based Architecture | PASS | Every unit of behavior is a class or a pure function inside a named module. No module wraps another module for the sake of a shorter import. Variable names use full words. No AI marker text appears. |
| III. Safety-First | PASS | The upgrade start requires a typed confirmation. The stop control requires the typed word `STOP` (FR-038b). The lock takeover requires the typed word `CONFIRM`. Viewing data never requires typing. Every handler validates early and returns early. No credential value reaches a log, a page, or an error message. |
| IV. Full Deployment Pipeline | PASS | The feature edits `Containerfile`, `compose.yml`, and `container/scripts/start.sh` for port 8056 in the same change. The pipeline runs unchanged. |
| V. Observability and Logging | PASS | Every log record is ASCII. Every record uses `%s` placeholders. Records carry a run identifier and a site identifier, so an operator can follow one run through a shared log. `structlog` stays inside `src/db`, as the repository already does. |
| VI. Inline Comments | PASS | The implementation phase adds a comment on each generated line that states why the line exists. This plan sets the expectation and the task list enforces it. |
| VII. Action Logging | PASS | Every action logs at info level before the action and at debug level after the action. The portal wraps every cloud call and every database write in that pair. |

Two further repository rules apply and both pass.

- **Menu registration.** The portal needs one new menu number. The next free
  number is **238**. The change adds a row to `src/utils/operation_registry.py`.
  Without that row the fail-closed guardrail breaks the build.
- **Primary key strategy.** The constitution requires a natural business key with
  a strategy declared in `ENDPOINT_PRIMARY_KEY_STRATEGIES` before any new
  operation. The change adds two `natural_pk` entries.

**Post-design re-check**: PASS. The Phase 1 design added no new violation. The
contracts confine every request handler to at most 5 parameters. The data model
uses one natural key for each collection.

## Project Structure

### Documentation (this feature)

```text
specs/1823-upgrade-capture-portal/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 index and decision record
├── research/            # Six authoritative reference documents
│   ├── capture-data-sources.md
│   ├── settle-gate-apis.md
│   ├── upgrade-reuse.md
│   ├── storage-and-locking.md
│   ├── concurrency-auth-conventions.md
│   └── web-portal.md
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── README.md
│   ├── http-api.md
│   ├── upgrade-service.md
│   ├── site-lock.md
│   └── ui-testids.md
└── tasks.md             # Phase 2 output, created by the tasks command
```

### Source code (repository root)

```text
src/upgrade_portal/               # New package. Ruff and mypy already cover src/.
├── __init__.py
├── app/                          # The web layer
│   ├── __init__.py
│   ├── factory.py                # create_app, blueprint registration, teardown
│   ├── config.py                 # CAPTURE_PORT, secret key, theme list
│   ├── security.py               # CSP, CSRF, headers, IP allow list
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py               # FR-006 .. FR-011  sign in, org pick
│   │   ├── select.py             # FR-012 .. FR-020  site pick, inventory
│   │   ├── capture.py            # FR-021 .. FR-032b capture start, status
│   │   ├── upgrade.py            # FR-033 .. FR-051, FR-038a .. FR-038i
│   │   └── review.py             # FR-064 .. FR-071, FR-084, FR-085
│   └── assets/
│       ├── templates/            # Jinja templates, one folder for each view
│       └── static/
│           ├── css/themes/magenta.css
│           ├── js/portal.js
│           └── vendor/bootstrap/
├── capture/                      # Read the site state
│   ├── __init__.py
│   ├── devices.py                # Inventory and device statistics, vc=True
│   ├── clients.py                # Wired, wireless, and guest clients
│   ├── extras.py                 # Tier 3 ports, radios, tunnels, peers, alarms
│   ├── assembly.py               # Build the capture document, compute digests
│   └── store.py                  # Write, read back, verify, list, load
├── upgrade/                      # Drive the upgrade
│   ├── __init__.py
│   ├── options.py                # Version list, target choice, body options
│   ├── driver.py                 # The run state machine and the cascade order
│   ├── gate.py                   # The settle gate rules
│   ├── events.py                 # Event key discovery and event polling
│   └── stop.py                   # FR-038a .. FR-038i stop control
├── compare/                      # Report the difference
│   ├── __init__.py
│   ├── diff.py                   # Device level comparison
│   ├── clients.py                # Client level comparison, match on mac
│   ├── statistics.py             # Counts, moved clients, roll-up
│   ├── render.py                 # View models for the templates
│   └── download.py               # CSV and JSON export
└── runtime/                      # Cross-cutting services
    ├── __init__.py
    ├── identity.py               # Per-user session registry, org scope
    ├── lock.py                   # Redis site lock, heartbeat, takeover
    ├── runs.py                   # Run records, status view, history
    ├── pools.py                  # Thread pool sizing and shutdown
    └── signals.py                # Stop request store, no file sentinel

src/firmware/upgrade_service.py   # New seam. No print. No input. Thread safe.

tests/
├── unit/upgrade_portal/          # Pure function tests
├── contract/upgrade_portal/      # HTTP contract tests, Flask test client
└── e2e/upgrade_portal/           # Playwright journeys, screenshot plus trace

wsgi_capture.py                   # New WSGI entry point for port 8056
```

Files changed outside the new package.

| File | Change |
| --- | --- |
| `src/utils/operation_registry.py` | Add menu 238 with the correct category |
| `src/refactors/endpoint_primary_key_strategies.py` | Add two `natural_pk` entries |
| `MistHelper.py` | Add the menu entry and the launcher for menu 238 |
| `Containerfile` | Add `ENV CAPTURE_PORT=8056` and extend `EXPOSE` |
| `compose.yml` | Publish port 8056 |
| `container/scripts/start.sh` | Start the second Gunicorn process |
| `pyproject.toml` | Register the new test paths only if needed |

**Structure Decision**: The feature uses a single project layout with a new
package under `src/`. The repository is one Python application with an optional
web front end, so the two-project layout does not apply.

The package sits at `src/upgrade_portal/` for one reason above all others.
`pyproject.toml:161` excludes `web_portal` from ruff, and `pyproject.toml:273-281`
exclude the same directory from mypy. Any code placed there loses both gates. The
mypy command already names `src/`, so the new package gains full coverage with no
change to any gate command. A package at the repository root would escape the
mypy target list until somebody edited the command.

The five subpackages match the five stages of the user journey: sign in and
choose, capture, upgrade, compare, and the services that support all four. That
split satisfies the Five-Item Rule at the package level and at the module level.

## Design notes that the task list depends on

### Threading model

Three layers use threads. Each layer has a different owner and a different
lifetime.

| Layer | Tool | Size | Rule |
| --- | --- | --- | --- |
| Capture collection | `ConnectionPoolExecutor` | 4 workers | One pool for each capture. The pool closes when the capture ends. |
| Settle gate polling | The same pool shape | 4 workers | One bulk org-scope call for each round covers every device. |
| Upgrade run driver | One long-lived thread for each run | 1 | The thread owns the run. No other thread writes the run record. |

Two rules protect correctness.

- The portal never calls `src/firmware/firmware_manager.py`. The module holds four
  globals at `:34-37`, and the save-and-restore blocks at `:1736` and `:1797` are
  not thread safe. Two concurrent web requests would corrupt each other.
- Concurrency belongs at the call-group level. A per-device fan-out costs about
  125 times the requests and gains nothing, because the cloud already answers a
  bulk query for the whole site.

### Cloud call rules that the code must obey

| Rule | Reason |
| --- | --- |
| Pass `type="all"` to `listSiteDevicesStats` | The default returns access points only |
| Pass `device_type` to `searchOrgDeviceEvents` | The default is `ap`, so a switch gate or a gateway gate would wait forever |
| Do not pass `type="all"` to `searchOrgDevices` | The value is not legal on that endpoint |
| Load event keys from `listDeviceEventsDefinitions` at run time | Only the access point restart event is vendor confirmed |
| Detect a reboot from a decrease in the reported uptime | A cloud timestamp against the local clock is not reliable |
| Read `current_phase`, not `phase` | The upgrade status response names the field `current_phase` |
| Treat `reboot_in_progress` as a list of MAC addresses inside `targets` | The field is not a boolean |
| Never call `getOrgSsrUpgrade` | The installed SDK builds the cancel path inside that function |

### Settle gate and cascade

The cascade runs in this order: gateway gate, then switch gate, then access point
gate, then wireless client gate. Each gate needs three signals: a reconnect event,
an uptime that decreased together with a version that changed, and then an extra
wait of 60 seconds. An access point gate waits a further 60 seconds.

### Client matching

The comparison matches a client on `mac` alone. The code strips `timestamp` from
any composite registry key before it matches, because a key that holds a timestamp
makes every row look new. A change of access point counts as its own "moved"
statistic and never as a loss. The wireless read calls both
`listSiteWirelessClientsStats` and `searchSiteWirelessClients` and joins the two
results on `mac`, because signal strength lives in the first and the random MAC
flag lives in the second.

### Progress transport

The browser polls `GET /runs/<run_id>/status` every 30 seconds. The portal does
not use server-sent events. The existing event bus caps at 10 subscribers and
holds a request thread for each open stream.

### Stop control

The cancel action exists. Research question Q1 in `research.md` records the exact
functions, files, and lines. Access points, switches, and Junos gateways cancel
through `cancelSiteDeviceUpgrade` or `cancelOrgDeviceUpgrade`. A session smart
router cancels through `cancelOrgSsrUpgrade`, which exists at organization scope
only. The portal therefore starts every session smart router upgrade at
organization scope, so that a cancel path always exists. The cloud states that the
cancel is best effort and that a device in mid-flash may still complete, which
matches FR-038c and FR-038d exactly.

### Gateway family split

`classify_gateway` reads the device record and returns one of two families. A
session smart router matches a type value of `ssr` or a model string that holds
`SSR` or `128T`. Every other gateway is a Junos gateway and rides the same site
device upgrade call that a switch rides. The repository has no Junos gateway
upgrade path today, so this is new but supported work.

### Storage and the honest write

A capture writes under the natural key `cap-{run_id_hex}-{ordinal}`. A run writes
under `run-{uuid4hex}`. Neither key holds a slash or a colon, so the key sanitizer
never rewrites them and a retry replaces the record instead of duplicating it.
After each write the portal reads the key back and compares the stored schema
version and digest. FR-031 requires the portal to verify its own write, and issue
#1824 records the router defect that makes the verification necessary.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `src/` gains a sixth or later child directory, above the Five-Item Rule limit of 5 children for each level | `src/` already holds far more than 5 children today. The feature needs one package that ruff and mypy check. Every alternative location loses a gate. | A package inside `web_portal/` loses ruff (`pyproject.toml:161`) and mypy (`pyproject.toml:273-281`). A package at the repository root escapes the mypy target list. Merging the code into an existing `src/` child would break that child's own five-module limit. |
| A second long-running server process inside the container | The existing portal owns port 8055 and one Gunicorn worker with process-level global state. The new portal cannot share that process. | A shared process would inherit the run map, the event bus subscriber map, and the module-level API session of the existing portal. Those three items already force one worker and would corrupt a second application. |
| A new module in `src/firmware/`, which raises that package above five modules | The upgrade seam must live next to the upgrade code, and it must expose no `print` and no `input`. | Reuse of the four existing classes fails. They hold 1271 `print` calls and 80 `input` calls. Reuse through the input interceptor fails, because the prompt order changes with the inventory. |

## Dependencies outside this plan

**Issue #1824 is a prerequisite for the repository, not for this feature.**
`_is_standalone_mode()` at `src/export/data_exporter.py:141` gates every polyglot
write on a container check, and `_csv_fallback` at `src/db/router.py:372-382`
returns `success=True` after it writes zero rows. FR-031 requires the portal to
verify its own database write, so this plan does not wait for the repair. The
repair still matters for every other caller. **Do not implement the repair inside
this feature.**

**Do not repair `src/db/retention.py`.** Line 100 reads an attribute named
`_database`, while the writer names the handle `self._db`. The purge therefore
never runs. That failure is harmless here, because FR-032 asks for unlimited
retention. A repair would start deleting captures.
