# Implementation Plan: countOrgDevices Menu Item

**Branch**: `514-mist-count-org-devices` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/514-mist-count-org-devices/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/devices/count` (operationId `countOrgDevices`) to retrieve
distinct-attribute counts of devices in an organization. The menu item prompts the user
for an `org_id` and the `distinct` grouping field (model, type, version, hostname, mac,
site_id, etc.) via `safe_input()`, optionally collects the supplemental query filters
defined by the OpenAPI contract (site_id, model, type, version, mac, hostname, ip,
mxtunnel_status, mxedge_id, lldp_*, start/end/duration, limit), invokes the `mistapi`
SDK (`mistapi.api.v1.orgs.devices.countOrgDevices`), flattens the wrapper envelope into a
header row plus one row per `results[]` entry, and persists the data through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **58** -- the next free slot in the Misc Safe Org
Exports cluster (56-59), sitting adjacent to other org-level summary exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the org_id supplied through `.env` (`MIST_ORG_ID`). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The default test sweep covers item 58; the
heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=3 seconds for typical orgs (the
endpoint is server-aggregated and returns a small array even for fleets of thousands of
devices). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off; no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); response envelope must be flattened into a stable schema even when the
`additionalProperties` keys vary by `distinct` choice.
**Scale/Scope**: One new public menu method (~22 lines) on the existing org-device
export class in `MistHelper.py` (proposed: `OrgDeviceExportUtils`; the exact class name
is verified at implementation time -- if no class currently owns the org-device count /
search cluster the new method is hosted on the class that already owns
`searchOrgDevices`), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new
CSV/SQLite tables (`org_devices_count_summary` and `org_devices_count_results`), one
menu registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_devices_count()` stays under 25
  lines, takes <=4 parameters (`self`, `org_id`, `distinct`, `filters`), and contains
  <=5 logical blocks (prompt -> validate -> API call -> flatten -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. No new packages, modules,
  or top-level constants are introduced. The `filters` argument is a single dict that
  forwards optional query params to the SDK, keeping the parameter count low even though
  the endpoint exposes many filters. If the flatten step grows past 5 lines during
  implementation it is extracted to a private helper `_flatten_count_envelope()` on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing org-device
  export class (proposed `OrgDeviceExportUtils`; verified at implementation against the
  class that already owns `searchOrgDevices` / `listOrgDevices`). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`distinct_field`, `count_result_row`,
  `filter_kwargs`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_devices_count:org_id"`, `"org_devices_count:distinct"`,
  `"org_devices_count:filters"`) so SSH / container EOF exits cleanly with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET) so no typed
  destructive-confirmation gate is required. Org ID is validated against the Mist UUID
  shape before the API call; on validation failure the method logs a warning and returns
  early. API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 countOrgDevices` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting org devices for org %s grouped by %s");
  `DEBUG` after the call with summary counts ("Count envelope: distinct=%s total=%d
  results=%d"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with
  full traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing org-device export menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/514-mist-count-org-devices/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_org_devices.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgDeviceExportUtils class + PK strategy +
                         # menu 58 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing org-device export class in `MistHelper.py` (proposed
`OrgDeviceExportUtils`; the actual host class is the one that already owns
`searchOrgDevices` / `listOrgDevices`, verified at implementation time). The menu number
proposal is **58**, chosen because operations 56-59 are the Misc Safe Org Exports
cluster and 58 is the next free slot below the interactive cluster starting at 60. The
full menu list is re-verified at task generation time; if 58 collides with an in-flight
feature branch the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion. The two flattened tables share a `run_id` foreign
  key keeping the data model shallow.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgDeviceExportUtils`
  (or whichever class currently owns `searchOrgDevices`). No wrappers introduced.
  Flattening helpers, if needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or distinct filter values that
  could leak hostnames in error logs (filter values are summarized as counts, not
  echoed verbatim above INFO level).
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
