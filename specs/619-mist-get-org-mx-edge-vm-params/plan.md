# Implementation Plan: GetOrgMxEdgeVmParams Menu Item

**Branch**: `619-mist-get-org-mx-edge-vm-params` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/619-mist-get-org-mx-edge-vm-params/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params` (operationId
`getOrgMxEdgeVmParams`) to retrieve the VM provisioning parameters (model SKU,
optional user-supplied name, and base64-encoded cloud-init `user_data`) for a
single virtualized Mist Edge appliance. The menu item prompts the user for an
`org_id` and an `mxedge_id` via `safe_input()`, invokes the `mistapi` SDK,
flattens the small single-object response into one row tagged with the org and
mxedge UUIDs, and persists the result through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is registered
in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls.
The new operation is proposed as menu number **91** -- the next available slot
in the Interactive Safe / MxEdge cluster, sitting adjacent to other site-level
MxEdge stats menu items and well below the Resource Intensive block at 97-101
and the Destructive block at 154-194.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (`.env` loading for `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using a known org and mxedge from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. Heavy / destructive
skip list (14, 18, 63-65, 90-100) is partially relevant: if the chosen menu
number lands inside 90-100 it is moved outside the skip range at task
generation time so the smoke test covers it.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change. Paths normalize via `os.path.join` and
`pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a
typical virtualized Mist Edge; response is a single small JSON object (three
top-level keys), not paginated. Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light
enough that no per-endpoint tuning override is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the
`user_data` field is base64-encoded cloud-init content -- it MUST NOT be logged
in full because it may contain bootstrapping credentials; only its length and a
truncated SHA-256 prefix are emitted at DEBUG. API token loaded from `.env`,
never logged. All output under `data/`. Windows-safe path joining.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`MxEdgeExportUtils` class (the class that already owns other org-level mxedge
exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV /
SQLite table (`org_mxedge_vm_params`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_mxedge_vm_params()` stays under 25 lines, takes <=3 parameters
  (`self`, `org_id`, `mxedge_id`), and contains <=5 logical blocks
  (prompt org -> prompt mxedge -> API call -> flatten one row -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. The flatten step is
  a single dict-literal expression; if it grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `MxEdgeExportUtils` class (the same class that owns
  `listOrgMxEdges`-style exports). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`vm_params_row`, `flattened_row`)
  -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_mxedge_vm_params:org_id"`,
  `"org_mxedge_vm_params:mxedge_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. Both UUIDs are
  validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a
  `WARNING` and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged. The `user_data` field (base64
  cloud-init) is treated as sensitive: it is persisted to backend storage
  (which is the user's local data sink, not a log stream) but is NEVER
  written to a `logging` call -- only its length and a truncated SHA-256
  prefix appear in DEBUG output, sufficient for audit without leaking
  bootstrap secrets.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 91 getOrgMxEdgeVmParams` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop
  / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching VM params for mxedge %s in
  org %s"); `DEBUG` after the call with a sanitized summary ("VM params:
  model=%s name=%s user_data_len=%d user_data_sha256_prefix=%s"); `WARNING`
  on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, full request URLs, or raw
  `user_data` content are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing MxEdge export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a
  sanitized result summary, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write. The
  `DataExporter` call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/619-mist-get-org-mx-edge-vm-params/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_mx_edge_vm_params.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MxEdgeExportUtils class + PK strategy +
                         # menu 91 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for
                         # op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the
                         # menu 91 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table created
                         # on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `MxEdgeExportUtils` class in `MistHelper.py`
(the same class that owns the other org-level mxedge exports). If grep at
implementation time shows the canonical class for mxedge exports is named
differently (e.g. `MxEdgeManager` or `MxEdgeExportManager`), the method is
added to that class instead -- the rule is "no new wrapper function, attach to
the existing mxedge export class". The menu number proposal is **91**, chosen
because the Interactive Safe band runs 60-96 with viewers at 92-96, putting 91
at the bottom of the Stats slice (80-91) where mxedge-stats-style menu items
already live. The number is provisional -- at `/speckit.tasks` time
`MistHelper.py` is grep'd for the latest allocated menu integer and 91 is
shifted forward if a conflict exists. If the final number lands inside the
`--test` skip range (90-100), task generation moves it out so the smoke sweep
covers it.

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
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `MxEdgeExportUtils`. No wrappers introduced. A single private flatten
  helper, if needed, is added as a method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. Both UUIDs are validated before the SDK call.
  The contract explicitly forbids logging `user_data` content.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the raw
  `user_data` payload.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
