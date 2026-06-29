# Implementation Plan: countOrgInventory Menu Item

**Branch**: `516-mist-count-org-inventory` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/516-mist-count-org-inventory/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/inventory/count` (operationId `countOrgInventory`) to
retrieve grouped device counts from the organization inventory bucketed by a chosen
distinct attribute (model, type, site_id, hw_rev, etc.). The menu item prompts the user
for an `org_id` via `safe_input()`, a required `distinct` field (free-text with a
suggested-values hint), an optional inventory `type` filter (`ap`, `switch`, `gateway`,
or empty for all), and an optional `limit` override (defaults to the Mist API default of
100). It calls the `mistapi` SDK once, flattens the response envelope (`distinct`,
`start`, `end`, `limit`, `total`) plus each entry of the `results` array into one row
per bucket, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **59** -- the next available slot at the tail of
the Safe Org Exports / Misc cluster (range 1-59), sitting adjacent to the existing
inventory exports at 8-14 in spirit while staying inside the safe block boundary
immediately before the Interactive Safe range at 60.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. No new dependency required.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 59 sits inside the default test sweep range and is the last entry of the safe
sweep before the heavy 60-72 block.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. Path handling uses `os.path.join` / `pathlib.Path` for
cross-platform safety.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI; no web UI changes.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
inventories (the count endpoint is server-aggregated -- response payload is bounded by
`limit`, default 100 buckets). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining; PK strategy registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` before first write.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`InventoryExportUtils` class (or whichever class currently owns
`getOrgInventory` exports -- confirmed at implementation time via `grep "def
export_org_inventory" MistHelper.py`; if no such class exists the method joins
`OrgExportUtils`, the generic safe-org-export host). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new SQLite table
(`org_inventory_count`). One menu registration entry. One README operation-count bump.
One CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_inventory_count()` stays under 25
  lines, takes <=5 parameters (`self`, `org_id`, `distinct_field`, `type_filter`,
  `limit`), and contains <=5 logical blocks (prompt -> validate -> API call -> flatten
  -> DataExporter call). Hierarchy is unchanged: one new method on an existing class. No
  new packages, modules, or top-level constants are introduced. The flatten step is one
  comprehension; if it grows past 5 lines during implementation it is extracted to a
  private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing inventory
  export class (`InventoryExportUtils` or the equivalent host class for adjacent
  inventory operations 8-14). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`distinct_field`, `type_filter`, `bucket_row`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_inventory_count:org_id"`,
  `"org_inventory_count:distinct"`, `"org_inventory_count:type"`,
  `"org_inventory_count:limit"`) so SSH / container EOF exits cleanly with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Org ID is validated against the Mist UUID
  shape before the API call; on validation failure the method logs a warning and returns
  early. The `limit` input is cast to int with a try/except that logs a warning and
  falls back to the API default of 100 on parse failure. API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 59 countOrgInventory` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching inventory count for org %s distinct=%s
  type=%s"); `DEBUG` after the call with summary counts ("Inventory count: total=%d
  buckets=%d distinct=%s"); `WARNING` on 404 / empty results; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing inventory export cluster) get comments added
  in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each prompt and before the SDK call, `logging.debug(...)` after the SDK call
  with the bucket count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with the row count, `logging.info(...)` before the DataExporter write. The
  DataExporter call already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/516-mist-count-org-inventory/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_inventory.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on InventoryExportUtils class + PK strategy entry +
                         # menu 59 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59
                         # addition
data/                    # Runtime output target (existing dir). No schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing inventory-export class in `MistHelper.py` (the same class that
owns the related `getOrgInventory` exports used by menus 12, 17, 21, 22, 25, 61, 90, 99,
100, 110 per the enriched doc cross-reference). The menu number proposal is **59**,
chosen because the constitution's Safe Org Exports band is 1-59 and 59 is the next
contiguous integer below the Interactive Safe band that begins at 60. The number is
provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the latest
allocated menu integer and 59 is shifted forward into the misc / interactive cluster if
a conflict exists.

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
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the inventory-export class.
  No wrappers introduced. The flatten helper, if extracted, is a private method on the
  same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. Numeric coercion for `limit` is
  guarded by try/except with a logged fallback.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. Log message text enumerated in
  Principle V section above is reflected verbatim in the quickstart skeleton.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
