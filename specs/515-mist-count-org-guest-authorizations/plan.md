# Implementation Plan: countOrgGuestAuthorizations Menu Item

**Branch**: `515-mist-count-org-guest-authorizations` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/515-mist-count-org-guest-authorizations/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/guests/count` (operationId `countOrgGuestAuthorizations`)
to return distinct-attribute count breakdowns of authorized guests for an organization
over a configurable time window. The menu item prompts the user via `safe_input()` for
the `org_id`, an optional `distinct` field (default `ssid`), and an optional duration
(default `1d`), invokes `mistapi.api.v1.orgs.guests.count.countOrgGuestAuthorizations()`,
flattens the `results` array into one row per distinct value with the count plus the
captured time-window metadata, and persists the rows through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (composite primary key on `org_id`, `distinct`,
`value`, `start`, `end`) so SQLite upserts cleanly on repeated runs across overlapping
time windows. The new operation is proposed as menu number **96** -- the next
available slot at the upper edge of the Interactive Safe / safe-org-exports cluster
(60-96) immediately before the Resource Intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) excludes
proposed menu 96, so this item participates in the default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request returns a fully aggregated `results` array
in <=5 seconds for typical orgs (the endpoint is server-side aggregated and
non-paginated in the SDK contract -- the `limit` query parameter caps the result set
size). The adaptive delay system (`delay_metrics.json` + `tuning_data.json`) continues
to govern back-off; no special tuning is needed for this lightweight endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); valid `distinct` field values from the published Mist API enum only.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`GuestAuthorizationExportUtils` class (or a new `GuestAuthorizationCountUtils` class
if the existing class would exceed the 5-Item Rule on method count -- decided at
implementation time), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
CSV/SQLite table (`org_guest_authorization_counts`), one menu registration entry,
one README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_guest_authorization_counts()`
  stays under 25 lines, takes <=4 parameters (`self`, `org_id`, `distinct`,
  `duration`), and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten results -> DataExporter call). Hierarchy is unchanged: one new method on
  one existing class. No new packages, modules, or top-level constants are
  introduced. The flatten step is a single list comprehension; if it grows past 5
  lines during implementation, it is extracted to a private `_flatten_count_rows()`
  helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `GuestAuthorizationExportUtils` class (the class that already owns the related
  `searchOrgGuestAuthorization` and `listSiteAllGuestAuthorizations` exports). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`count_row`, `distinct_field`, `window_start`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_guest_count:org_id"`,
  `"org_guest_count:distinct"`, `"org_guest_count:duration"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. `org_id` is
  validated against the Mist UUID shape and `distinct` is validated against the
  allowed enum (`ssid`, `wlan_id`, `auth_method`) before the API call; on validation
  failure the method logs a warning and returns early. API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  countOrgGuestAuthorizations` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container
  -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching guest authorization counts for org %s
  distinct=%s duration=%s"); `DEBUG` after the call with summary counts
  ("countOrgGuestAuthorizations returned %d distinct buckets total=%d"); `WARNING`
  on 404 / empty payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  guest-authorization menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with the result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten with the flattened-row count,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/515-mist-count-org-guest-authorizations/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_guest_authorizations.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on GuestAuthorizationExportUtils class + PK
                         # strategy entry + menu 96 registration. No new modules; the
                         # single-file monolith is preserved.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry describing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `GuestAuthorizationExportUtils` class in
`MistHelper.py` (the same class that owns the other org/site guest-authorization
exports). The menu number proposal is **96**, chosen because it is the last free slot
in the 60-96 Interactive Safe cluster, immediately above the existing
guest-authorization listings and immediately below the Resource Intensive block
(97-101). The full menu list will be re-verified at task generation time; if 96
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert against the
  existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `GuestAuthorizationExportUtils`. No wrappers introduced. The flatten helper, if
  promoted out of the inline comprehension, is added as a private method on the same
  class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation and `distinct` enum validation happen
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the Phase 1 design are
  ASCII-only with `%s` formatting and never include the API token or full request
  URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validation, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.