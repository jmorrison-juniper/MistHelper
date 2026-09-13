# Implementation Plan: GetGatewayDefaultConfig Menu Item

**Branch**: `579-mist-get-gateway-default-config` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/579-mist-get-gateway-default-config/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/const/default_gateway_config` (operationId `getGatewayDefaultConfig`) to
retrieve the factory-default gateway configuration template Mist hands to a freshly
adopted SRX or SSR device for a given hardware model (and optional HA flavor). The menu
method prompts the user via `safe_input()` for the required `model` query parameter and
the optional `ha` flag, invokes the `mistapi` SDK, flattens the deeply nested JSON
response into a single summary row (with the verbatim JSON blob preserved in a `config_json`
column for round-trip fidelity), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
keyed on the operationId with a composite primary key of `(model, ha_flag)` so that
repeated runs upsert cleanly without duplicates. The new operation is proposed as menu
number **58** -- the next available slot in the Misc Safe Org Exports cluster (56-59) and
thematically adjacent to the existing gateway-template exporter at menu 26.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known gateway model from `.env` (default `srx320`). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated and returns a single JSON object of a few KB per call. Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`). The endpoint is global (not org-scoped) so no `org_id` is consumed --
this is a constants/reference lookup.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`GatewayExportUtils` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
SQLite table (`default_gateway_config`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_default_gateway_config()` stays under
  25 lines, takes <=3 parameters (`self`, `model`, `ha`), and contains <=5 logical
  blocks (prompt-model -> prompt-ha -> API call -> flatten -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. The flatten step is a single dict
  comprehension; if it grows past 5 lines during implementation, it is extracted to a
  private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `GatewayExportUtils` class (the same class that owns the related `templates` export
  at menu 26 per the doc note in
  `documentation/api/constants/GET_const_default_gateway_config.md`). No standalone
  wrapper function is introduced. The menu dispatch in the main loop references the
  class method directly. Variable names use full words (`gateway_model`,
  `ha_requested`, `config_blob`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"default_gateway_config:model"`,
  `"default_gateway_config:ha"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET) against a constants
  surface, so no typed destructive-confirmation gate is required. The `model` input is
  normalized to lowercase and validated against a non-empty string before the API
  call; on validation failure the method logs a `WARNING` and returns early. The API
  token comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58
  getGatewayDefaultConfig` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching default gateway config for model %s
  ha=%s"); `DEBUG` after the call with summary counts ("Default config sections:
  port_config_keys=%d networks=%d service_policies=%d"); `WARNING` on 404 / empty
  payload ("No default config returned for model %s"); `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing `GatewayExportUtils` cluster) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each `safe_input()` prompt, `logging.info(...)` before the SDK call, the call
  itself, `logging.debug(...)` after with a result count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/579-mist-get-gateway-default-config/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_gateway_default_config.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on GatewayExportUtils class + PK strategy + menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `GatewayExportUtils` class in `MistHelper.py` (the same
class identified in the enriched per-endpoint doc as the owner of gateway-template
exports at menu 26). The menu number proposal is **58**, chosen because operations
1-59 are the Safe Org Exports range and 56-59 is the Misc subrange (per
`.github/copilot-instructions.md` menu-category table) -- a constants-style read-only
lookup is a natural fit. Slot 58 is far away from the destructive cluster (154-194)
and far from the resource-intensive block (97-101, 153). The full menu list will be
re-verified at task generation time; if 58 collides with an in-flight feature branch,
the next free integer in the same cluster (57 or 59) is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `GatewayExportUtils`. No
  wrappers introduced. Any flattening helper, if needed, is added as a private method
  on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only against a constants/reference surface, with no destructive side effect.
  `safe_input()` is the documented prompt path for both `model` and `ha`. Empty-model
  validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
