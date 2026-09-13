# Implementation Plan: countSiteDevices Menu Item

**Branch**: `549-mist-count-site-devices` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/549-mist-count-site-devices/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/devices/count` (operationId `countSiteDevices`) to return
the number of devices at a site, optionally bucketed by a `distinct` grouping field
(e.g. `model`, `version`, `hostname`, `mxedge_id`, `lldp_system_name`). The menu method
prompts the user for `site_id` and the optional `distinct` field via `safe_input()`,
invokes the `mistapi` SDK call `mistapi.api.v1.sites.devices.count.countSiteDevices()`,
flattens the count-result envelope (`{distinct, start, end, limit, total, results: [...]}`)
into one row per bucket, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **72** -- the next available slot inside the
60-72 Site Devices interactive-safe cluster, adjacent to the existing `listSiteDevices`
and per-site device-stats exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(loads `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_SITE_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. One new SQLite table
`site_devices_count` is created on first write.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the default site from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 72 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
environments must work without code change. Paths use `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI; no web UI
changes are required.
**Performance Goals**: Single GET request completes in <=5 seconds for typical sites
(the response is small even with hundreds of distinct buckets, capped by `limit`,
default 100). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this endpoint is light enough that no endpoint-specific
tuning is required.
**Constraints**: ASCII-only logging (no Unicode/emoji); `safe_input()` for every
prompt with explicit `context=` tag; no secrets in logs; all output under `data/`;
Windows-safe path joining; the SDK call respects the gotcha documented in the enriched
doc (defaults to APs only unless filtered).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteDeviceExportUtils` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
one new SQLite table (`site_devices_count`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_devices_count()` stays under
  25 lines, takes <=4 parameters (`self`, `site_id`, `distinct_field`, `limit`), and
  contains <=5 logical blocks (prompt site_id -> prompt distinct -> API call ->
  flatten results -> DataExporter call). Hierarchy is unchanged: one new method on
  an existing class. No new packages, modules, or top-level constants are introduced.
  If the flattener grows past 5 lines during implementation, it is extracted to a
  private helper `_flatten_count_results()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteDeviceExportUtils` class (the same class that owns the related
  `listSiteDevices` and site-level device-stats exports). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`distinct_field`, `bucket_row`,
  `result_envelope`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_devices_count:site_id"`,
  `"site_devices_count:distinct"`, `"site_devices_count:limit"`) so SSH / container
  EOF exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET) so no typed destructive-confirmation gate is required. The `site_id`
  is validated against the Mist UUID shape via `is_valid_uuid()` before the API call;
  on validation failure the method logs `WARNING` and returns early. API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 72 countSiteDevices` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting devices for site %s distinct=%s");
  `DEBUG` after the call with summary counts ("Count result: total=%d buckets=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline `#` comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched site-devices menu
  cluster get comments added in the same PR (per the "edit the whole block" rule).

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, the prompt itself, `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a bucket
  count, `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/549-mist-count-site-devices/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_devices.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteDeviceExportUtils class +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 72
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 72
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 72 addition
data/                    # Runtime output target (existing dir); first run creates the
                         # new SQLite table site_devices_count via DataExporter DDL
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteDeviceExportUtils` class in `MistHelper.py` (the
same class that already owns `listSiteDevices` and the per-site device-stats
exporters). The menu number proposal is **72**, chosen because operations 60-72 are
the Site Devices interactive-safe cluster (per the menu category table in
`.github/copilot-instructions.md`) and 72 is the next contiguous integer at the top
of that cluster, sitting safely below the Insights block (73-79). The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the latest
allocated menu integer and 72 is shifted forward if a conflict exists with an
in-flight feature branch.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_devices.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteDeviceExportUtils`. No wrappers introduced. The flattening helper, if
  needed, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
