# Implementation Plan: GetOrgLicensesSummary Menu Item

**Branch**: `612-mist-get-org-licenses-summary` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/612-mist-get-org-licenses-summary/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/licenses` (operationId `getOrgLicensesSummary`) to
retrieve the full license picture for an organization: the active license
subscriptions (`licenses[]`), per-type entitlement counts (`entitled`,
`fully_loaded`, `summary`, `usages` maps), and any amendment records
(`amendments[]`). The new menu method prompts the user for the org UUID via
`safe_input()` (defaulting to `MIST_ORG_ID` from `.env`), invokes
`mistapi.api.v1.orgs.licenses.getOrgLicensesSummary()`, flattens the multi-array
multi-map response into four logical row sets (`org_licenses_subscriptions`,
`org_licenses_amendments`, `org_licenses_summary_counts`,
`org_licenses_usage_counts`), and persists each through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all stay consistent. A new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
governs clean SQLite upserts on repeated runs. The new operation is proposed as
menu number **96** -- the next available slot adjacent to the existing
license/license-by-site cluster and before the resource-intensive block.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`,
`MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
Four new tables created on first run (one per row set).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The new item sits inside the default
test sweep range (skip list 14, 18, 63-65, 90-100 is unaffected by 96 because
96 is within the safe-cluster end; if 96 collides with a freshly merged feature
the next free integer in the same cluster is used).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
org. The endpoint is non-paginated -- the full license object is returned in
one response. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough
that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); inline comments on every executable line;
action logging before and after every meaningful step.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`LicenseExportUtils` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
four new SQLite tables created automatically by `DataExporter`, one menu
registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_licenses_summary()` stays
  under 25 lines, takes <=2 parameters (`self`, `org_id`), and contains <=5
  logical blocks (prompt -> API call -> flatten the four row sets -> per-set
  DataExporter calls -> summary log). Hierarchy is unchanged: one new method on
  an existing class. No new packages, modules, or top-level constants are
  introduced. Each of the four flatteners is a single comprehension; if any
  grows past 5 lines during implementation, it is extracted to a private helper
  on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `LicenseExportUtils` class (same class that owns
  `getOrgLicensesBySite` and the related claim-status export). No standalone
  wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`subscription_row`, `amendment_row`, `summary_count`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` string (`"org_licenses_summary:org_id"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Org ID is validated against the Mist UUID shape before the API
  call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgLicensesSummary` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman
  pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching license summary for org
  %s"); `DEBUG` after the call with counts ("License summary: subs=%d
  amendments=%d entitled_types=%d usage_types=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing license-export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with result counts, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before each
  write, `logging.debug(...)` after each write. The DataExporter call already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/612-mist-get-org-licenses-summary/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_licenses_summary.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on LicenseExportUtils class + PK strategy + menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir). DataExporter creates the
                         # four new SQLite tables on first run; no manual migration.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `LicenseExportUtils` class in
`MistHelper.py` (the same class that owns the other org-licenses exports). The
menu number proposal is **96**, chosen because operations 51-95 are the Safe
Org Exports / Org-License / SLE cluster and 96 is the next available slot at
the boundary with the resource-intensive 97-101 block. The full menu list will
be re-verified at task generation time; if 96 collides with an in-flight
feature branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `LicenseExportUtils`. No wrappers introduced. Flattening helpers, if needed,
  are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, each of the four exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
