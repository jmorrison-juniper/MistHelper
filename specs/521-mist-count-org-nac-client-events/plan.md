# Implementation Plan: countOrgNacClientEvents Menu Item

**Branch**: `521-mist-count-org-nac-client-events` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/521-mist-count-org-nac-client-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/nac_clients/events/count` (operationId
`countOrgNacClientEvents`) to retrieve the count of NAC (802.1X / RADIUS) client
events grouped by a caller-selected distinct attribute (event `type`, `nas_vendor`,
`vlan`, etc.) over a bounded time window. The menu method prompts for `org_id`,
`distinct`, optional `type` filter, and a time window (`start` / `end` or
`duration`) -- all via `safe_input()` -- invokes the
`mistapi.api.v1.orgs.nac_clients.events.count.countOrgNacClientEvents()` SDK call,
flattens the `results` array (each item carries a `count` plus the value of the
distinct attribute) into one row per group, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the operationId so SQLite re-runs upsert
cleanly. The new operation is proposed as menu number **195** -- the next sequential
slot after the current safe range ceiling at 194, keeping the operation outside the
destructive band 154-194 and adjacent to existing NAC search / count endpoints in
the read-only catalog.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
selected at startup.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 195 sits outside the documented
skip list (14, 18, 63-65, 90-100) so it is automatically swept by `--test`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
NAC event counts. The endpoint returns one aggregated payload (no per-event
pagination required for counts); response size is bounded by the `limit` query
parameter (default 100). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing NAC
client export class (or, if absent, on the catch-all `OrgClientExportUtils`
holder used for adjacent NAC operations -- final class choice confirmed during
task generation by grepping `nac_client` in `MistHelper.py`). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
`org_nac_client_events_count`. One menu registration entry. One README operation
count bump (194 -> 195). One CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_nac_client_events_count()` stays under 25 lines, takes <=5
  parameters (`self`, `org_id`, `distinct`, `event_type`, `time_window`), and
  contains <=5 logical blocks (prompts -> validate window -> SDK call ->
  flatten `results` -> DataExporter call). Hierarchy unchanged: one new method
  on an existing class. No new packages, modules, or top-level constants are
  introduced. The flattener is a single comprehension; if it exceeds 5 lines
  during implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  NAC-client export class (sibling of `searchOrgNacClients` /
  `countOrgNacClients`). No standalone wrapper function is introduced. The menu
  dispatch references the class method directly. Variable names use full words
  (`distinct_field`, `event_type_filter`, `time_window_spec`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings
  (`"nac_client_events_count:org_id"`,
  `"nac_client_events_count:distinct"`,
  `"nac_client_events_count:type"`,
  `"nac_client_events_count:duration"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. Org ID is validated
  against the Mist UUID shape before the SDK call; `distinct` is validated
  against an allow-list (`type`, `nas_vendor`, `vlan`, `ssid`, `port_type`,
  `auth_type`) before being forwarded. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `ruff check` -> `black --check` -> commit with `version YY.MM.DD.HH.MM -
  add menu 195 countOrgNacClientEvents` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching NAC client event counts for
  org %s grouped by %s window=%s"); `DEBUG` after the call with summary counts
  ("NAC event count: total=%d groups=%d limit=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or query strings containing
  credentials are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing NAC export menu cluster) get comments added in the same PR per the
  "edit-block-comments" rule.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before prompt collection, `logging.debug(...)` after
  prompts with the resolved window; `logging.info(...)` before the SDK call,
  the call itself, `logging.debug(...)` after with result counts;
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with
  row count; `logging.info(...)` before write, the `DataExporter` call emits
  its own per-backend log lines so the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/521-mist-count-org-nac-client-events/
| - plan.md              # This file
| - research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
| - data-model.md        # Phase 1 - response entities + DDL + PK registration
| - quickstart.md        # Phase 1 - local run + .env + quality gates
| - contracts/
|     | - count_org_nac_client_events.md   # Phase 1 - HTTP + SDK contract
| - tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the existing NAC client export class
                         # (sibling of searchOrgNacClients / countOrgNacClients),
                         # new ENDPOINT_PRIMARY_KEY_STRATEGIES entry, menu 195
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump (194 -> 195) and new row in the
                         # menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195
data/                    # Runtime output target (existing dir); first run creates
                         # the new SQLite table org_nac_client_events_count via
                         # DataExporter -- no manual migration required
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing NAC-client export class in `MistHelper.py`
(the same class that owns `searchOrgNacClients` and `countOrgNacClients`). If
that class name differs from the assumed `OrgClientExportUtils` when grep is
run during task generation, the method is placed on the class that owns the
nearest sibling NAC export -- never as a top-level wrapper function. The menu
number proposal is **195**, chosen because the documented current range is
1-194 and 195 is the next sequential safe slot above the destructive band
(154-194). If 195 collides with an in-flight feature branch at task generation,
the next free integer above 195 is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing NAC
  client export class. No wrappers introduced. Flatten helper, if needed, is a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID and distinct allow-list validation happen
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompts, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
