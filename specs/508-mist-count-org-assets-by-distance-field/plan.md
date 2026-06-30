# Implementation Plan: countOrgAssetsByDistanceField Menu Item

**Branch**: `508-mist-count-org-assets-by-distance-field` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/508-mist-count-org-assets-by-distance-field/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/assets/count` (operationId
`countOrgAssetsByDistanceField`) to return a grouped count of BLE-tracked org
assets broken down by a single distinct attribute (e.g. `map_id`, `device_name`,
`mac`). The menu item prompts the user for an `org_id` via `safe_input()`,
optionally asks for the `distinct` field and a `limit`, invokes the `mistapi`
SDK, flattens the response envelope (`distinct`, `start`, `end`, `limit`,
`total`) plus the per-bucket `results[]` array into two related output streams,
and persists the result through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive consistent output. A new
entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite
upserts on repeated runs. The new operation is proposed as menu number **91**
-- the next available slot in the Stats cluster (80-91), sitting adjacent to
the existing site/device stats operations and immediately before the
resource-intensive viewer block (92-96).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 91 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
asset counts (the endpoint is a server-side aggregate -- one HTTP call returns
a fully bucketed list bounded by `limit`, default 100). Adaptive delay metrics
in `delay_metrics.json` and `tuning_data.json` continue to govern back-off;
this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on a new
`AssetStatsExportUtils` class (no existing asset-stats class in MistHelper.py
yet -- this is the first asset-stats menu item, so a dedicated class is
created to host this operation plus future siblings
`listOrgAssets`/`searchOrgAssets`). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two new SQLite tables
(`org_assets_count_summary` and `org_assets_count_results`). One menu
registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_assets_count_by_distinct()`
  stays under 25 lines, takes <=4 parameters (`self`, `org_id`, `distinct`,
  `limit`), and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten summary + results -> DataExporter call). Hierarchy adds one new
  class at level 4 with a single public method at level 5. No new packages,
  modules, or directories. If the flatten step grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `AssetStatsExportUtils` class located alongside other `*ExportUtils` classes
  in `MistHelper.py`. A dedicated class is justified because asset stats is a
  new functional domain (BLE-tracked assets, not network devices); future
  spec-driven additions (`listOrgAssets`, `searchOrgAssets`,
  `getOrgAssetsCounts` by other distinct fields) will land on the same class.
  No standalone wrapper function is introduced. Menu dispatch references the
  class method directly. Variable names use full words (`distinct_field`,
  `count_row`, `bucket_count`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_assets_count:org_id"`,
  `"org_assets_count:distinct"`, `"org_assets_count:limit"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Org ID is validated against the Mist UUID shape before the API
  call; `limit` is coerced to int with a sane default (100) on parse failure;
  on validation failure the method logs a warning and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `ruff check` -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 91 countOrgAssetsByDistanceField` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting org assets by distinct=%s
  for org %s"); `DEBUG` after the call with summary counts ("Asset count
  result: distinct=%s total=%d buckets=%d"); `WARNING` on 404 / empty
  `results`; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched stats menu
  cluster get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before
  write, `logging.debug(...)` after write. The DataExporter call already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/508-mist-count-org-assets-by-distance-field/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_org_assets_by_distance_field.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New AssetStatsExportUtils class with the new method,
                         # new PK strategy entry, and menu 91 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on a new `AssetStatsExportUtils` class in `MistHelper.py`.
A dedicated class is preferred over piggy-backing on an existing class because
asset stats is a previously unrepresented functional domain in MistHelper and
multiple sibling operations (`listOrgAssets`, `searchOrgAssets`,
`getSiteAssets`) are expected in follow-on specs -- having a class ready to
host them reduces churn. The menu number proposal is **91**, the next
available slot in the Stats cluster (80-91) and immediately before the viewer
block (92-96). The full menu list will be re-verified at task generation time;
if 91 collides with an in-flight feature branch, the next free integer in the
same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `AssetStatsExportUtils`. No wrappers introduced. Flatten helper, if needed,
  is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID and integer validation happen before the
  SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
