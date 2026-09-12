# Implementation Plan: GetOrgAsset Menu Item

**Branch**: `599-mist-get-org-asset` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/599-mist-get-org-asset/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/assets/{asset_id}` (operationId `getOrgAsset`) to retrieve a
single BLE asset definition from an organization by its UUID. The new method prompts the
user for `org_id` and `asset_id` via `safe_input()`, validates both as Mist UUIDs,
invokes `mistapi.api.v1.orgs.assets.getOrgAsset()` once, normalizes the single-object
JSON response into a one-row list, and persists the result via
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all stay consistent. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the asset `id` (natural primary key) so
repeated runs upsert cleanly into SQLite. The new operation is proposed as menu number
**195** -- the next available integer above the existing 1-194 range, placing it directly
adjacent to the future write-side asset operations rather than inside the destructive
154-194 cluster, even though the call itself is non-destructive.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud, accessed via `mistapi.api.v1.orgs.assets.getOrgAsset`);
`requests` (transport, transitive); `python-dotenv` (for `.env` loading of `MIST_HOST` and
`MIST_API_TOKEN`); the existing internal `DataExporter`, `safe_input`, and `OrgExportUtils`
helpers in `MistHelper.py`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local fallback
is SQLite at `data/mist_data.db`; CSV files land in `data/`; the polyglot ArangoDB+Redis
container pair (per spec 188) handles graph + cache backends. A new SQLite table
`get_org_asset` is created on first run using the schema in `data-model.md`.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known `org_id` and `asset_id` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, and
`python -m black --check MistHelper.py`. The heavy / destructive skip list (14, 18,
63-65, 90-100) is unchanged; menu 195 is added with `--test` exclusion only if the
required `asset_id` is not present in `.env`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production, including SSH access on
port 2200; both must continue to work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI; no web UI
work is needed.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
explicitly non-paginated (the documentation marks it `Not paginated`), and the response
is a single JSON object, so adaptive delay (`delay_metrics.json` and `tuning_data.json`)
governs back-off only on 429 responses; no per-endpoint tuning is required.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for every prompt
with explicit `context=` strings; API token never logged; all output written under
`data/`; Windows-safe path joining via `os.path.join` / `pathlib.Path`; the new method
respects the 5-Item Rule (<=25 lines, <=5 parameters, <=5 nested blocks).
**Scale/Scope**: One new public method (~18 lines) on the existing `OrgExportUtils`
class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on `getOrgAsset`, one new
SQLite table `get_org_asset`, one menu registration entry at slot 195, one README
operation-count bump (194 -> 195) plus a new row in the menu table, and one CHANGELOG
line in `version YY.MM.DD.HH.MM` format. No new dependencies, no new modules, no new
top-level packages.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_asset()` stays under 25 lines, accepts
  <=3 parameters (`self` / `cls`, `org_id`, `asset_id`), and contains <=5 logical blocks
  (prompt collection -> UUID validation -> SDK call -> single-row normalize ->
  DataExporter call). Hierarchy depth is unchanged: one new method on an existing class.
  No new packages, modules, or top-level constants are introduced. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dict literal entry, not a new
  hierarchy level.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class, which already owns the related `_assets` (org BLE asset list)
  export. No standalone wrapper function is introduced; the menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`asset_record`, `asset_rows`, `validated_org_id`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_asset:org_id"` and `"org_asset:asset_id"`) so SSH / container
  EOF exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Both `org_id` and
  `asset_id` are validated against the Mist UUID shape before the SDK call; on
  validation failure the method logs a warning and returns early without a network call.
  The API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 195 getOrgAsset` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs validation and image build ->
  `gh run watch <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container with the documented bind mounts -> `podman ps`
  verification. No deviation from the documented seven-step flow.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call (`"Fetching asset %s for org %s"`); `DEBUG` after the call
  with the asset name and MAC (`"getOrgAsset returned name=%s mac=%s"`); `WARNING` on
  validation failure or 404 with an ASCII message; `ERROR` on unexpected exception via
  `logging.exception` so the traceback is captured once and only once. No secrets,
  tokens, or full request URLs are logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing brackets, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing
  `# -- Assets & Inventory --` cluster in the PK strategies dict) get comments added in
  the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the SDK call itself, `logging.debug(...)` after with the asset
  identifier and MAC, `logging.info(...)` before the DataExporter call,
  `logging.debug(...)` after with the row count (always 1 on success, 0 on empty
  response). The `DataExporter.write_with_format_selection` call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/599-mist-get-org-asset/
|-- spec.md               # Pre-existing feature spec (read-only input)
|-- plan.md               # This file
|-- research.md           # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md         # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md         # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_asset.md  # Phase 1 - HTTP + SDK contract
`-- tasks.md              # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py             # New method export_org_asset() on the existing OrgExportUtils
                          # class, new ENDPOINT_PRIMARY_KEY_STRATEGIES entry for
                          # `getOrgAsset`, and menu 195 registration. No new modules;
                          # same single-file monolith.
README.md                 # Operation count bump (194 -> 195) + new row in the menu table
CHANGELOG.md              # New `version YY.MM.DD.HH.MM` entry summarizing menu 195
data/                     # Runtime output target. DataExporter creates the
                          # `get_org_asset` SQLite table and `get_org_asset.csv` file on
                          # first run; no manual schema migration is required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `OrgExportUtils` class in `MistHelper.py` -- the same class that
owns the related `_assets` org-asset list export, so the new method sits beside its
peer endpoint. The menu number proposal is **195**, chosen because operations 1-194 are
already allocated per `agents.md`. The new operation is read-only and would naturally
belong in the 1-59 Safe Org Exports cluster by category, but no free slot exists there;
slot 195 reserves the next contiguous integer above the current ceiling without
displacing existing operations. The full menu list will be re-verified at task
generation time; if an in-flight feature branch claims 195 first, the next free integer
is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry is a single dict literal insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  `OrgExportUtils` class. No wrappers introduced. The single response object is
  normalized inline as a one-element list; no helper class is required.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path with explicit context strings. UUID validation happens before the SDK call so a
  malformed identifier never hits Mist Cloud.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard seven-step
  pipeline. The new method does not require any new CI matrix entry.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting; the API token and full request URL are never logged.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
