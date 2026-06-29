# Implementation Plan: countOrgNacClients Menu Item

**Branch**: `522-mist-count-org-nac-clients` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/522-mist-count-org-nac-clients/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/nac_clients/count` (operationId `countOrgNacClients`) to
return aggregated counts of NAC (802.1X / RADIUS) clients grouped by a user-selected
`distinct` attribute (e.g. `auth_type`, `last_vlan_id`, `last_ssid`, `mdm_provider`).
The menu item prompts the user for `org_id` and a `distinct` field via `safe_input()`,
optionally collects a time-range hint (`start` / `end` / `duration`), invokes the
`mistapi` SDK, flattens the `results` array (each row carries a `count` plus dynamic
key/value attributes), and persists the rows through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all stay consistent. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **58** -- the next available slot in the Misc
Safe Org Exports cluster (56-59), adjacent to the existing org-level NAC client search
operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 58 sits in the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
MUST work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
distinct queries; the endpoint returns an aggregated payload (counts only) so it is
light. Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off; no special tuning required. Default `limit=100` is honored;
`limit` is bumped to `DEFAULT_API_PAGE_LIMIT` (1000) when the user does not specify
otherwise, consistent with adjacent count menu items.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); API token never logged.
**Scale/Scope**: One new public menu method (~22 lines) on the existing NAC-clients
export class (or a new small `NacClientCountExportUtils` class if no NAC-clients
export class is present -- see Structure Decision), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_nac_clients_count`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_nac_clients_count()` stays
  under 25 lines, takes <=4 parameters (`self`, `org_id`, `distinct_field`,
  `time_range`), and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten results -> DataExporter call). One private flatten helper is added if the
  inline comprehension exceeds 5 lines. Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  NAC-clients export class in `MistHelper.py` (the same class that owns
  `searchOrgNacClients` exports). If no such class exists today, a new
  `NacClientCountExportUtils` class is introduced -- never a standalone wrapper
  function. The menu dispatch references the class method directly. Variable names
  use full words (`distinct_field`, `count_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_nac_clients_count:org_id"`,
  `"org_nac_clients_count:distinct"`, `"org_nac_clients_count:duration"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Org ID is validated against the Mist UUID shape before the API call; the
  `distinct` field is validated against a whitelist drawn from the documented enum
  list. On validation failure the method logs a warning and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58 countOrgNacClients`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting NAC clients for org %s grouped
  by %s"); `DEBUG` after the call with summary counts ("Received %d distinct groups
  total=%d"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with
  full traceback via `logging.exception`. No secrets, tokens, or full request URLs
  are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing NAC-clients export cluster) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/522-mist-count-org-nac-clients/
├── plan.md                                    # This file
├── research.md                                # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md                              # Phase 1 - response entities + DDL + PK registration
├── quickstart.md                              # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_org_nac_clients.md               # Phase 1 - HTTP + SDK contract
└── tasks.md                                   # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on NAC-clients export class (or new
                         # NacClientCountExportUtils class if none exists) +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run
                         # by DataExporter)
documentation/api/orgs/GET_orgs_org_id_nac_clients_count.md  # Source of truth for the contract
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing NAC-clients export class in `MistHelper.py`. If task
generation discovers there is no current NAC-clients class (i.e. the existing
`searchOrgNacClients` and `searchOrgNacClientEvents` live on a broader Clients or
Events class), a dedicated `NacClientCountExportUtils` class is introduced rather
than reusing an unrelated class -- this preserves Principle II (Class-Based
Architecture, No Wrappers). The menu number proposal is **58**, chosen because
operations 56-59 are the Misc Safe Org Exports cluster and 58 is the next available
slot adjacent to the other NAC client search operations. The full menu list will be
re-verified at task generation time; if 58 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the NAC-clients export
  class (or a new `NacClientCountExportUtils` class if necessary). No wrappers
  introduced. Flatten helper, if needed, is added as a private method on the same
  class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation and `distinct` whitelist validation happen before
  the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
