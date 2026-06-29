# Implementation Plan: GetMspDetails Menu Item

**Branch**: `582-mist-get-msp-details` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/582-mist-get-msp-details/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}` (operationId `getMspDetails`) to retrieve the configuration
record for a single Managed Service Provider account. The menu method prompts the user
for an `msp_id` via `safe_input()` (defaulting to the `MIST_MSP_ID` value from `.env`
when present), invokes the `mistapi` SDK, treats the flat JSON object as a single row,
and persists it through `DataExporter.write_with_format_selection()` so that CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the API-provided `id` field
(natural primary key) for clean SQLite upserts. The new operation is proposed as menu
number **95**, the next available slot in the Safe Org Exports cluster adjacent to
existing org-level MSP-related operations (menu 56 `OrgConfigExporter.msp`).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and the optional `MIST_MSP_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the MSP ID from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The default test sweep skip list (14, 18, 63-65, 90-100) leaves menu 95
inside the executed range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
must work without code change. All paths use `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature is CLI-only; no UI surface change.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical MSP
record. The endpoint is non-paginated and returns one small JSON object, so adaptive
delay tuning is unnecessary beyond the existing `delay_metrics.json` and
`tuning_data.json` defaults.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output rooted at `data/`; Windows-safe path joining; the API token loads from
`.env` via `mistapi.APISession` and is never written to stdout, log files, or audit
trails.
**Scale/Scope**: One new public menu method (~20 lines) added to an existing class
(see Structure Decision below), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one
new CSV/SQLite table (`msp_details`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new modules, dependencies, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_details()` stays under 25 lines,
  takes <=2 parameters (`self`, `msp_id`), and contains <=5 logical blocks (prompt ->
  UUID validate -> API call -> flatten single row -> DataExporter call). No new
  packages, modules, or top-level constants are introduced. Hierarchy is unchanged: one
  new method on an existing class plus one dict entry in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The behavior is added as a method on the existing
  `OrgConfigExporter` class (the same class that owns menu 56 `msp` MSP-related
  config export). No standalone wrapper function is introduced. The menu dispatch in
  the main loop references the class method directly. Variable names use full words
  (`msp_record`, `flattened_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context="msp_details:msp_id"` string so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. `msp_id` is validated against the
  Mist UUID shape via the existing `is_valid_uuid()` helper before the API call; on
  validation failure the method logs a `WARNING` and returns early. API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 95 getMspDetails` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch
  <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching MSP details for msp %s"); `DEBUG` after the
  call summarizing the returned record ("MSP details: tier=%s name=%s id=%s");
  `WARNING` on 404 or empty payload; `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, request URLs containing query strings, or
  authentication headers are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  `OrgConfigExporter` cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the prompt, `logging.info(...)` before the SDK call, the
  call itself, `logging.debug(...)` after with a one-line result summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/582-mist-get-msp-details/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   |-- get_msp_details.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgConfigExporter class + PK strategy entry +
                         # menu 95 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 95
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 95
data/                    # Runtime output target (existing dir, no migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgConfigExporter` class in `MistHelper.py` -- the same
class that already owns menu 56 `msp` MSP-related config export work, keeping all MSP
behaviors co-located. The menu number proposal is **95**, chosen because operations
1-95 are the Safe Org Exports cluster and 95 is the next available integer below the
resource-intensive block at 96-101. The number is provisional: at `/speckit.tasks`
time, `MistHelper.py` is grep'd for the latest allocated menu integer and 95 is
shifted forward by one if a conflict exists with an in-flight feature branch.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_msp_details.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single insert in an existing dict, so
  no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgConfigExporter`. No
  wrappers introduced. Any flattening helper, if needed, is added as a private method
  on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation occurs before the SDK call. 404 is handled as a logged
  warning, not a traceback.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline. The
  changeset touches only `MistHelper.py`, `README.md`, `CHANGELOG.md`.
- **Principle V (Observability)**: PASS -- All planned log statements use ASCII text,
  `%s` formatting, and never include the API token, full request URL, or `Authorization`
  header value.
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
