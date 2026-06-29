# Implementation Plan: countOrgJsiAssetsAndContracts Menu Item

**Branch**: `517-mist-count-org-jsi-assets-and-contracts` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/517-mist-count-org-jsi-assets-and-contracts/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/jsi/inventory/count` (operationId
`countOrgJsiAssetsAndContracts`) to count Juniper Support Insights (JSI) inventory items
purchased under accounts linked to the organization. The menu item prompts the user for
an `org_id` via `safe_input()` (falling back to `MIST_ORG_ID` from `.env`), optionally
asks for a `distinct` grouping attribute and a `limit` (server default 100), invokes the
`mistapi` SDK call `mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts()`, and
flattens the two-tier response (one summary envelope + N bucket rows in `results[]`)
into two related tables. Output is persisted through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent data. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly against the natural
JSI grouping key. The new operation is proposed as menu number **96** -- the next
available slot in the Safe Org Exports cluster (51-95), immediately adjacent to the
existing license/JSI-adjacent exports and ahead of the resource-intensive block at
97-101. The final integer is re-verified at `/speckit.tasks` time against any in-flight
feature branches.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to the Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for
`.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend (per spec 188). Two new tables are
created on first run: `org_jsi_inventory_count_summary` and
`org_jsi_inventory_count_results`.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using `MIST_ORG_ID` from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 96 sits at the upper edge of the safe-export sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is a
server-side aggregate (returns a small JSON object with one envelope plus a bounded
`results[]` of <=`limit` buckets, default 100), so it is light on the wire and on the
Mist back-end. The adaptive delay metrics in `delay_metrics.json` / `tuning_data.json`
continue to govern rate-limit back-off; no per-endpoint tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token from
`.env` never logged; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule on the new method.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`InventoryExportUtils` class (the closest semantic owner -- it already holds inventory
counts and searches for the org and JSI-adjacent endpoints); one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`; two new SQLite tables; one menu registration entry;
one README operation-count bump; one CHANGELOG line. No new dependencies, no new
modules, no new directories. If a dedicated JSI class does not yet exist and a sibling
JSI endpoint is added under the same PR, a new `JsiExportUtils` class may be introduced
instead -- decision deferred to task time to avoid speculative class creation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_jsi_inventory_count()` stays under 25 lines, takes <=4 parameters
  (`self`, `org_id`, `distinct`, `limit`), and contains <=5 logical blocks
  (prompt -> validate -> SDK call -> flatten (summary + results) -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. The flatten step is a single
  comprehension over `payload["results"]`; if it grows past 5 lines during
  implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `InventoryExportUtils` class (the same class that owns `getOrgInventory`,
  `getOrgInventoryCount`, and the inventory search exports). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names are full words (`distinct_field`, `bucket_row`,
  `summary_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_jsi_inventory_count:org_id"`,
  `"org_jsi_inventory_count:distinct"`, `"org_jsi_inventory_count:limit"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET, no body, no destructive effect), so no typed destructive-
  confirmation gate is required. Org ID is validated against the Mist UUID shape
  before the API call; on validation failure the method logs a warning and returns
  early. The optional `limit` is clamped to a sane range (1..1000) before being sent.
  The API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 countOrgJsiAssetsAndContracts`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Counting JSI inventory for org %s distinct=%s
  limit=%s"); `DEBUG` after the call with summary counts ("JSI count: total=%d
  buckets=%d"); `WARNING` on 404 / 400 (no Juniper account linked) / empty payload;
  `ERROR` on unexpected exception with full traceback via `logging.exception`. No
  secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing inventory-export menu cluster) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with the bucket count, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten, `logging.info(...)` before write, `logging.debug(...)` after write.
  The `DataExporter` call already emits its own per-backend log lines; the new method
  does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/517-mist-count-org-jsi-assets-and-contracts/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_jsi_assets_and_contracts.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on InventoryExportUtils class + PK strategy +
                         # menu 96 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables created on first run
                         # by DataExporter)
documentation/api/orgs/GET_orgs_org_id_jsi_inventory_count.md  # Source of truth for
                         # contract; referenced by contracts/ and research.md.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `InventoryExportUtils` class in `MistHelper.py` (the same
class that owns `getOrgInventory` and `getOrgInventoryCount`). If, at task-generation
time, more JSI endpoints are being added in parallel and the cluster would exceed the
5-Item Rule on `InventoryExportUtils`, a dedicated `JsiExportUtils` class is created
instead -- without wrappers. The menu number proposal is **96**, chosen because
operations 51-95 are the Safe Org Exports / Org-License / SLE / inventory cluster and
96 is the next slot below the resource-intensive block at 97-101. The full menu list
will be re-verified at task generation time; if 96 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_org_jsi_assets_and_contracts.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `InventoryExportUtils` (or
  `JsiExportUtils` if the JSI cluster grows). No wrappers introduced. Flattening
  helpers, if needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call; `limit` is clamped to 1..1000.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
