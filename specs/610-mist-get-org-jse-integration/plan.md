# Implementation Plan: GetOrgJseIntegration Menu Item

**Branch**: `610-mist-get-org-jse-integration` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/610-mist-get-org-jse-integration/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/jse/setup` (operationId `getOrgJseIntegration`)
to retrieve the Juniper Sky Enterprise (JSE) integration setup status for an
organization. The menu item prompts the user for an `org_id` via `safe_input()`
(defaulting to `MIST_ORG_ID` from `.env`), invokes the `mistapi` SDK exactly
once, normalizes the small JSON object response into a single flat row, and
persists the result through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry
is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed by `org_id` for clean
SQLite upserts on repeated runs. The new operation is proposed as menu number
**59** -- the next available slot at the tail of the Safe Org Exports cluster
(1-59) and immediately before the Interactive Safe block starting at 60.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using the org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- menu 59 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The
endpoint is non-paginated and returns a small fixed-shape JSON object
(`cloud_name`, `org_names`, `username`). No adaptive-delay tuning required
beyond the shared `delay_metrics.json` / `tuning_data.json` defaults.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`). The endpoint may legitimately return 404
when no JSE integration is configured -- MistHelper must treat that as a
clean empty result, not an error.
**Scale/Scope**: One new public menu method (~20 lines) on a new
`JseIntegrationExportUtils` class (no existing JSE class to extend), one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`org_jse_integration_setup`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_jse_integration()` stays under 25 lines, takes <=2 parameters
  (`self`, `org_id`), and contains <=5 logical blocks (prompt -> validate ->
  API call -> flatten one row -> DataExporter call). The new
  `JseIntegrationExportUtils` class introduces only one public method at
  Phase 1; if a private flatten helper is needed later it lives on the same
  class. No new packages, modules, or top-level constants are introduced.
  The `org_names` array is collapsed into a single comma-joined string
  field within the existing flatten block, keeping the output flat.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `JseIntegrationExportUtils` class. A new class is justified because no
  existing class owns Mist JSE Integration endpoints in MistHelper.py (the
  adjacent `getOrgJseInfo`, `POST .../jse/setup`, and `DELETE .../jse/setup`
  endpoints are also unimplemented, and grouping all four under one
  semantic class follows the project's pattern of one class per Mist tag).
  No standalone wrapper functions are introduced. The menu dispatch in the
  main loop references the class method directly. Variable names use full
  words (`jse_setup_row`, `org_names_joined`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings (`"org_jse_integration:org_id"`) so SSH
  / container EOF exits cleanly with code 0 and no traceback. The endpoint
  is strictly read-only (HTTP GET), so no typed destructive-confirmation
  gate is required. Org ID is validated against the Mist UUID shape via
  the existing `is_valid_uuid()` helper before the API call; on validation
  failure the method logs a warning and returns early. API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.
  A 404 from Mist is treated as "no JSE integration configured" and
  surfaces as a `WARNING` plus zero output rows -- not a traceback.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add menu 59
  getOrgJseIntegration` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Fetching JSE
  integration setup for org %s"); `DEBUG` after the call with summary
  detail ("JSE setup: cloud=%s username=%s org_count=%d"); `WARNING` on
  404 / absent JSE integration; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `JseIntegrationExportUtils` class shell, the new PK strategy dictionary
  entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched dispatch block get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the prompt, `logging.info(...)` before the
  SDK call, the call itself, `logging.debug(...)` after with a summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten
  with a count, `logging.info(...)` before write. The DataExporter call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in
the Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/610-mist-get-org-jse-integration/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_jse_integration.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New JseIntegrationExportUtils class + new method +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 59
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
documentation/api/orgs/  # GET_orgs_org_id_setting_jse_setup.md - already exists,
                         # source of truth for the contract.
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a public method on a new `JseIntegrationExportUtils` class in
`MistHelper.py`. The new class is justified by the lack of an existing JSE
owner and the presence of three sibling JSE endpoints
(`getOrgJseInfo`, `POST .../jse/setup`, `DELETE .../jse/setup`) that will
land in the same class as separate specs follow. The menu number proposal
is **59**, chosen because operations 1-59 are the Safe Org Exports
cluster and 59 is the next available slot at the tail of that block.
The full menu list will be re-verified at task generation time; if 59
collides with an in-flight feature branch, the next free integer in the
same cluster is used (the search order is 59, 58, 57 ... falling back
toward the start of the safe-export range).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `JseIntegrationExportUtils`. No wrappers introduced. Flatten logic is
  inline; if extracted later it becomes a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  404 is treated as empty result, not error.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
