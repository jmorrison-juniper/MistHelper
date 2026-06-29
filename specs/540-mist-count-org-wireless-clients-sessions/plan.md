# Implementation Plan: countOrgWirelessClientsSessions Menu Item

**Branch**: `540-mist-count-org-wireless-clients-sessions` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/540-mist-count-org-wireless-clients-sessions/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/clients/sessions/count` (operationId
`countOrgWirelessClientsSessions`) to return per-attribute aggregate counts of
wireless client sessions for an organization. The menu item prompts the user for
`org_id` (defaulting to `MIST_ORG_ID` from `.env`) and an optional `distinct`
attribute plus time window using `safe_input()`, invokes the `mistapi` SDK,
flattens the `results` array into one row per distinct bucket (plus a single
summary row capturing `distinct`, `start`, `end`, `limit`, `total`), and writes
output via `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all stay in sync. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (already pre-staged in the catalog at line
~4582 -- this plan reuses it verbatim). The new operation is proposed as menu
number **195**, the next free integer beyond the current 1-194 range, sitting
adjacent to the existing safe-org client/count exporters.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and `MIST_ORG_ID` from
`.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; the polyglot ArangoDB + Redis container backend receives identical
rows for graph/cache writes.
**Testing**: `python MistHelper.py --test` exercises the menu item
non-interactively using `MIST_ORG_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list
(14, 18, 63-65, 90-100) is unchanged; menu 195 is read-only and remains in the
default sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production /
SSH-on-2200. Both targets must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
orgs across a 1-day window. The endpoint is server-aggregated (count, not
search), so no pagination loop is required at the default `limit=100`; the
response is bounded by the cardinality of the chosen `distinct` attribute.
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt with an
explicit `context=` label; no secrets in logs; all output under `data/`;
Windows-safe path joining (`os.path.join` / `pathlib.Path`); the
`limit` parameter is clamped to a sensible upper bound (default 1000) before
being passed to the SDK.
**Scale/Scope**: One new public method (~22 lines) on the existing
`OrgClientSecurityExporter` class (which already owns the related
`searchOrgWirelessClients` / `countOrgWirelessClients` exports), one reuse of
the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES["countOrgWirelessClientsSessions"]`
entry, one new pair of SQLite tables
(`count_org_wireless_clients_sessions_summary` and
`count_org_wireless_clients_sessions_results`), one menu registration entry,
one README operation-count bump (194 -> 195), one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method
  `export_count_org_wireless_clients_sessions()` stays under 25 lines and takes
  <=4 parameters (`self`, `org_id`, `distinct`, `duration`). It contains <=5
  logical blocks (prompt -> validate -> API call -> flatten -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. Any
  helper that grows past 5 lines is extracted to a private method on the same
  class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behaviour is added as a method on the existing
  `OrgClientSecurityExporter` class (MistHelper.py line 11267), the same class
  that already exports `searchOrgWirelessClients` and `countOrgWirelessClients`.
  No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`session_count_row`, `distinct_attribute`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"count_wireless_sessions:org_id"`,
  `"count_wireless_sessions:distinct"`,
  `"count_wireless_sessions:duration"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. The `org_id` is
  validated against the Mist UUID shape before the SDK call; on validation
  failure the method logs a warning and returns early. The API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- The standard pipeline applies without modification:
  `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with `version YY.MM.DD.HH.MM - add menu 195 countOrgWirelessClientsSessions`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting wireless client sessions
  for org %s distinct=%s duration=%s"); `DEBUG` after the call with summary
  counts ("Count response: total=%d buckets=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the reused PK
  strategy dictionary entry, and the menu registration line carries an inline
  comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing
  wireless-client count cluster) receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before
  write, `logging.debug(...)` after write. The `DataExporter` call already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/540-mist-count-org-wireless-clients-sessions/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_wireless_clients_sessions.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgClientSecurityExporter class
                         # + reuse of existing ENDPOINT_PRIMARY_KEY_STRATEGIES entry
                         # + menu 195 registration. No new modules.
README.md                # Operation count bump 194 -> 195 + new row in the menu table
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarising menu 195 addition
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the two new SQLite tables on first run.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgClientSecurityExporter` class in
`MistHelper.py` (the same class that already owns
`searchOrgWirelessClients` and `countOrgWirelessClients` exports). The menu
number proposal is **195** -- one above the current top of 194 -- placing it
immediately after the existing destructive-operations block while keeping all
new safe read-only exports above that block. The full menu list will be
re-verified at task generation time; if 195 collides with an in-flight feature
branch, the next free integer is selected.

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
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks.
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` already contains the required entry; no
  new top-level constant is added.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgClientSecurityExporter`. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token. Logging
  records the `distinct` attribute and the bucket count, not raw bucket keys
  (which could contain client identifiers).
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, validate,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
