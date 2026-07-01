# Implementation Plan: GetOrgSiteGroup Menu Item

**Branch**: `640-mist-get-org-site-group` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/640-mist-get-org-site-group/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}` (operationId `getOrgSiteGroup`)
to retrieve one specific site group -- the container object used for bulk template
assignment across multiple sites. The menu item prompts the user for `org_id` (from
`.env` `MIST_ORG_ID` when present) and `sitegroup_id` via `safe_input()`, invokes
`mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup()`, flattens the single-object
response (with the `site_ids` array preserved as a delimited string for CSV / SQLite
parity), and persists the row through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` under a `natural_pk` strategy keyed on `id` so
repeated runs upsert cleanly. The new operation is proposed as menu number **95** --
the next available slot inside the Safe Org Exports / templates cluster (menu range
37-59 for templates, extending to 95 in the safe-exports block), sitting adjacent to
existing site-group and template read operations.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`
from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and a probe `sitegroup_id` from `.env`.
Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
Heavy / destructive skip list (14, 18, 63-65, 90-100, 154-194) is unaffected --
new item 95 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port
2200; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The
endpoint returns exactly one JSON object (no pagination), so response
processing is constant-time. Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off but no special tuning is
required for this endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs (API token loaded via `.env`, never echoed); all output rooted
under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`);
UUID shape validated before the SDK call to prevent avoidable 404s.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgTemplateExportUtils` class (same class that owns the existing sitegroup /
sitetemplate read operations). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new SQLite table `org_site_groups`.
One menu registration entry. One README operation-count bump. One CHANGELOG
line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_site_group()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `sitegroup_id`), and
  contains <=5 logical blocks (validate inputs -> API call -> flatten row ->
  DataExporter write -> return). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are
  introduced. The single flattening block converts `site_ids: [uuid, uuid,
  ...]` to a `;`-delimited string in one comprehension.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgTemplateExportUtils` class (the class that owns the related
  `listOrgSiteGroups`, `getOrgSiteTemplate`, and adjacent template read
  operations). No standalone wrapper function is introduced. The menu dispatch
  in the main loop references the class method directly. Variable names use
  full words (`site_group_row`, `flattened_site_ids`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_site_group:org_id"`,
  `"org_site_group:sitegroup_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so
  no typed destructive-confirmation gate is required. Both UUIDs are
  validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 95 GetOrgSiteGroup` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching site group %s for org %s");
  `DEBUG` after the call with the row summary ("Site group name=%s
  site_count=%d"); `WARNING` on 404 or empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens,
  or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any adjacent uncommented lines inside the touched menu-cluster
  block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result summary, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten with the row count,
  `logging.info(...)` before write. `DataExporter` already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/640-mist-get-org-site-group/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_site_group.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgTemplateExportUtils class + PK
                         # strategy entry + menu 95 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing op 95
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgTemplateExportUtils` class in
`MistHelper.py` (same class that owns other org-template and sitegroup read
exports). The menu number proposal is **95**, chosen because the safe
org-export cluster runs 51-95 and 95 is the next free slot below the
resource-intensive block starting at 96. The full menu list is re-verified at
task generation time; if 95 collides with an in-flight feature branch, the
next free integer in the same cluster is used (research.md documents the
fallback policy).

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion. The `site_ids`
  flatten stays as a single comprehension.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgTemplateExportUtils`. No wrappers introduced. If a private
  `_flatten_site_group_row` helper is needed for readability it is added as
  a private method on the same class rather than a module-level function.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only, use `%s` formatting, and never include the API token or the
  raw URL with embedded IDs.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
