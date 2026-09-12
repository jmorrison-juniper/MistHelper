# Implementation Plan: countSiteWirelessClientEvents Menu Item

**Branch**: `567-mist-count-site-wireless-client-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/567-mist-count-site-wireless-client-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/clients/events/count` (operationId
`countSiteWirelessClientEvents`) to return the count of wireless client events at a site,
grouped by a caller-supplied `distinct` attribute (for example `type`, `ssid`, `ap`,
`band`, `proto`, `wlan_id`) and optionally narrowed by event filters (type, reason_code,
ssid, ap, proto, band, wlan_id) and a time window (`start` / `end` / `duration`). The
menu prompts the operator with `safe_input()` for `site_id` and the optional grouping /
filter parameters, calls the `mistapi` SDK exactly once per scope, flattens the response
into one summary row (envelope metadata) plus N detail rows (one per group bucket), and
persists everything through `DataExporter.write_with_format_selection()` so CSV, SQLite,
and ArangoDB+Redis backends stay consistent. A new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registers the composite primary key for clean SQLite
upserts on repeated runs. The new operation is proposed as menu number **78** -- the
next available slot in the Insights cluster (73-79), sitting adjacent to existing
site-level event and SLE viewers.

## Technical Context

**Language/Version**: Python 3.13+ (per Constitution Technology & Compatibility
Constraints; this is also the version pinned in the Podman container image).

**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK
`tmunzer/mistapi_python` -- the only permitted interface to Mist Cloud); `requests`
(transport, transitive via `mistapi`); `python-dotenv` for loading `MIST_HOST` and
`MIST_API_TOKEN` from `.env`. No new third-party packages are introduced by this
feature.

**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`. The
local default backend is SQLite at `data/mist_data.db`; CSV files land in `data/`; the
polyglot ArangoDB+Redis pair receives identical rows when configured. Two new SQLite
tables are created on first run: `site_wireless_client_events_count_summary` (one row
per query) and `site_wireless_client_events_count_results` (one row per bucket).

**Testing**: `python MistHelper.py --test` is the non-interactive smoke driver. The new
menu item lands at number 78 which is well inside the default test sweep range (the
skip list is 14, 18, 63-65, 90-100). Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. CI gates additionally run mypy, pytest with >=70% coverage, Hypothesis,
Bandit, pip-audit, CodeQL.

**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and the SSH-on-2200
remote-access path. Both targets must work without code change; path joining uses
`os.path.join` / `pathlib.Path`.

**Project Type**: CLI tool. Single-file monolith `MistHelper.py` (~28K lines) with an
optional Gunicorn web UI on port 8055. This feature is purely CLI.

**Performance Goals**: A single GET request to the count endpoint completes in <=5
seconds for typical site event volumes. The endpoint supports pagination via `limit` /
`page`; the implementation defaults to `DEFAULT_API_PAGE_LIMIT=1000` and continues until
the API reports the final page. Adaptive delay metrics (`delay_metrics.json` /
`tuning_data.json`) govern back-off without code change; this endpoint is light enough
that no endpoint-specific tuning entry is required.

**Constraints**: ASCII-only logging (no Unicode or emoji); `safe_input()` for every
`input()` call; no secrets in logs (the API token never leaves `.env` / process memory);
all output under `data/`; Windows-safe path joining; the new public method must obey
the 5-Item Rule (<=25 lines, <=5 params, <=5 nesting blocks).

**Scale/Scope**: One new public menu method (`export_site_wireless_client_events_count`)
on the existing site-scoped wireless export class (the same class that already owns the
adjacent `searchSiteWirelessClients` and related event search operations); one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; two new SQLite tables; one menu
registration entry; one README operation-count bump; one CHANGELOG line. No new
dependencies, no new modules, no new top-level directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_site_wireless_client_events_count()` stays
  under 25 lines, takes <=5 parameters (`self`, `site_id`, `distinct`, `filters_dict`,
  `time_window_dict` where the two dicts collapse the optional query parameters into a
  single object each), and contains <=5 logical blocks (prompt -> validate -> paginated
  API call -> flatten summary + bucket rows -> DataExporter call). Hierarchy is
  unchanged: one new method on an existing class. The two flattener bodies are inlined
  comprehensions; if either grows past 5 lines during implementation they are extracted
  to private helpers on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The behavior is added as a method on the existing
  site-clients-wireless export class (the same class that already exposes the search
  variants of this endpoint family). No standalone wrapper function is introduced. The
  menu dispatch references the class method directly. Variable names use full words
  (`bucket_row`, `summary_row`, `distinct_field`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_site_wireless_client_events:site_id"`,
  `"count_site_wireless_client_events:distinct"`, etc.) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. The `site_id` is validated
  against the Mist UUID shape before the SDK call; on validation failure the method
  logs a warning and returns early. The API token is loaded by the existing
  `mistapi.APISession` from `.env` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 78 countSiteWirelessClientEvents`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls are ASCII text with `%s` style formatting. `INFO`
  is emitted before the SDK call ("Fetching wireless client event count for site %s
  distinct=%s"); `DEBUG` after the call with bucket counts ("count_results: total=%d
  buckets=%d"); `WARNING` on 404 or empty payload; `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the new menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  site-wireless-clients menu cluster) receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten, `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/567-mist-count-site-wireless-client-events/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_site_wireless_client_events.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-clients-wireless export class +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 78 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 78
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 78 add
data/                    # Runtime output target (existing dir; the two new SQLite
                         # tables are created on first run by DataExporter)
documentation/api/sites/GET_sites_site_id_clients_events_count.md
                         # Enriched OpenAPI source for this endpoint; read-only ground
                         # truth for Phase 0 research
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing site-clients-wireless export class in `MistHelper.py`
(the same class that owns the related event-search operations). The menu number
proposal is **78**, chosen because operations 73-79 are the Insights cluster (site SLE
and event analytics), and 78 is the next available slot before the resource-intensive
block at 80-91. The full menu list is re-verified at task generation time; if 78
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_site_wireless_client_events.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion. The composite primary key
  (`site_id`, `distinct`, `bucket_key`, `start`, `end`) has 5 columns -- exactly at the
  limit, not over.
- **Principle II (Class-Based)**: PASS -- All new behavior lives on the existing
  site-clients-wireless export class. No wrappers, no module-level helpers. Flattening
  helpers if needed are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract
  (`contracts/count_site_wireless_client_events.md`) confirms the endpoint is GET only,
  with no destructive side effect. `safe_input()` is the documented prompt path. UUID
  validation runs before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the quickstart are
  ASCII-only with `%s` formatting and never include the API token, the bearer header,
  or the full request URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, paginated SDK
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
