# Implementation Plan: GetOrgAssetFilter Menu Item

**Branch**: `600-mist-get-org-asset-filter` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/600-mist-get-org-asset-filter/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` (operationId
`getOrgAssetFilter`) to retrieve the configuration of a single BLE Asset Filter object
belonging to a Mist organization. The menu item prompts the user for an `org_id` and an
`assetfilter_id` via `safe_input()`, invokes
`mistapi.api.v1.orgs.asset_filters.getOrgAssetFilter()`, and persists the single returned
JSON object through `DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the natural UUID `id` so that repeated runs
upsert cleanly into SQLite. The new operation is proposed as menu number **97** -- the
next free slot inside the Safe Org Exports cluster (1-59 / 60-96) immediately adjacent
to the existing org-level retrieval operations and below the resource-intensive block at
97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to the Mist Cloud), `requests` (transitive HTTP transport), and
`python-dotenv` (for loading `MIST_HOST` and `MIST_API_TOKEN` from `.env`). No new
runtime dependencies are introduced by this feature.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. The SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/` next to the
existing exports; the polyglot ArangoDB + Redis containers handle the graph + cache
backend when configured.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using a known `org_id` and `assetfilter_id` from `.env`. Local
quality gates are `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, and `python -m black --check MistHelper.py`. The
heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected because the new
menu number 97 falls inside that skip range; the test harness will skip it automatically
the same way it already skips 96-101, so the new operation is validated by an explicit
`python MistHelper.py --menu 97` invocation rather than by the broad `--test` sweep.
**Target Platform**: Windows 11 + venv for local development, plus the Podman Linux
container image `ghcr.io/jmorrison-juniper/misthelper:latest` for production and the SSH
gateway on port 2200. Both environments must work without code change.
**Project Type**: Single-file CLI monolith (`MistHelper.py`, approximately 28,000 lines)
with an optional Gunicorn web UI on port 8055. This feature lives entirely inside the
CLI path; no web UI work is required.
**Performance Goals**: A single non-paginated GET completes in <=5 seconds for a typical
asset-filter document (the response is a single JSON object well under 4 KB). The
adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off and retry; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging (no Unicode or emoji in log lines); every prompt
goes through `safe_input()` with an explicit `context=` string; the API token is never
logged; all output is written under `data/`; all paths are joined with `os.path.join` /
`pathlib.Path` so Windows and Linux both work.
**Scale/Scope**: One new public menu method (approximately 20 lines) added to the
existing `OrgAssetFilterExportUtils` class (a new sibling class to other BLE / asset
export utilities in `MistHelper.py`; introduced because no existing class already owns
the BLE asset-filter domain), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one
new SQLite table (`org_asset_filter`), one new menu registration entry, one README
operation-count bump, and one CHANGELOG line. No new third-party dependencies, no new
top-level modules, and no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_asset_filter()` stays under 25
  lines, takes `self`, `org_id`, and `assetfilter_id` (3 parameters, well under the
  5-parameter ceiling), and contains 5 logical blocks: validate inputs -> log start ->
  invoke SDK -> log result -> hand off to `DataExporter`. Hierarchy is unchanged: a new
  class file is NOT introduced; a new class is declared inline within the existing
  monolith next to other org export utilities. No new packages, modules, or top-level
  constants are created. No nested helpers exceed 5 lines.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `OrgAssetFilterExportUtils` class that owns the BLE asset-filter domain in
  `MistHelper.py`. The class is declared alongside existing export utility classes
  (`LicenseExportUtils`, `WebSocketManager`, etc.). No standalone wrapper function is
  introduced; the menu dispatch in the main loop instantiates the class and calls the
  method directly. Variable names use full words (`asset_filter_id`,
  `asset_filter_record`); no single-letter identifiers are used. Introducing the new
  class is justified because no existing class owns the BLE asset-filter domain and
  hanging the method on an unrelated class would violate the cohesion intent of
  Principle II.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_asset_filter:org_id"` and
  `"org_asset_filter:assetfilter_id"`) so SSH and container EOF conditions exit cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Both `org_id` and `assetfilter_id`
  are validated against the Mist UUID shape before the SDK call; on validation failure
  the method logs a warning and returns early. The API token is loaded from `.env`
  through the existing `mistapi.APISession` and is never logged or echoed.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard deployment pipeline runs without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with the message
  `version YY.MM.DD.HH.MM - add menu 97 getOrgAssetFilter` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs the validate-then-build sequence ->
  `gh run watch <id>` until green -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> `podman stop misthelper ; podman rm
  misthelper` -> re-run the standard `podman run` command from
  `.github/copilot-instructions.md` -> `podman ps` confirms the container is up.

### Principle V: Observability & Logging

- **STATUS: PASS** -- Every log call uses ASCII characters only and `%s` / `%d` style
  formatting. `INFO` is emitted before the SDK call ("Fetching asset filter %s for org
  %s"), `DEBUG` is emitted after the call with a short result summary ("Asset filter
  retrieved: name=%s disabled=%s"), `WARNING` is emitted on 404 or empty payload,
  and `logging.exception` captures any unexpected error with a full traceback. No
  secrets, tokens, full request URLs, or PII are written to logs.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `OrgAssetFilterExportUtils` class shell, the new `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary entry, and the new menu registration line carries an inline comment
  explaining *why* the line exists, not just what it does. Blank lines, closing
  parentheses, decorators, and pure type-annotation lines are exempt per the
  constitution. Any adjacent uncommented lines that the patch touches in the surrounding
  menu cluster receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.debug(...)` after each
  prompt confirming the captured value (with the value redacted to its last 4 chars if
  it is a UUID), `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after the SDK call with the result name/disabled flag,
  `logging.info(...)` before the `DataExporter` write, and `logging.debug(...)` after
  the write reporting the row count. The DataExporter's own per-backend log lines are
  not duplicated.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table below
intentionally remains empty.

## Project Structure

### Documentation (this feature)

```text
specs/600-mist-get-org-asset-filter/
|-- plan.md                          # This file
|-- research.md                      # Phase 0 - SDK signature, PK, naming, menu number, prompts
|-- data-model.md                    # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md                    # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_asset_filter.md      # Phase 1 - HTTP + SDK contract
`-- tasks.md                         # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py                # New OrgAssetFilterExportUtils class with one method
                             # export_org_asset_filter(), one new PK strategy entry,
                             # and one new menu registration for op 97. No new modules.
README.md                    # Operation count bump and a new row in the menu table
                             # for operation 97 (getOrgAssetFilter).
CHANGELOG.md                 # New "version YY.MM.DD.HH.MM" entry summarizing the menu
                             # 97 addition.
data/                        # Runtime output target (existing dir). The new SQLite
                             # table org_asset_filter is created on first run by
                             # DataExporter. CSV output filename is
                             # org_asset_filter.csv.
documentation/api/orgs/
  GET_orgs_org_id_assetfilters_assetfilter_id.md   # Source-of-truth for this contract.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a public
method on a newly declared `OrgAssetFilterExportUtils` class inside `MistHelper.py`. The
proposed menu number is **97**. Menu numbers 1-59 and 60-96 are the Safe Org Exports
cluster; 97-101 currently hold resource-intensive operations. Operation 97 is the next
sequential slot adjacent to the org-level retrieval cluster and shares its safety
profile (read-only, low cost). The final menu number is re-verified at task generation
time; if 97 is taken by an in-flight feature branch at merge time, the next free integer
in the same cluster is used. The DataExporter call uses `api_function_name=
"getOrgAssetFilter"` so it can look up the registered PK strategy and apply
`INSERT OR REPLACE` semantics against the natural UUID primary key.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions are required at the Pre-Phase 0 gate. The table is
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
and the contract under `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, 3 parameters, and 5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insertion is a single dictionary literal.
- **Principle II (Class-Based)**: PASS -- All new work lives on the new
  `OrgAssetFilterExportUtils` class. No wrappers are introduced.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements documented in the design
  are ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, SDK call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce the task breakdown.
