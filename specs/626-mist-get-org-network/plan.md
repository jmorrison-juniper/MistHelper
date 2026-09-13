# Implementation Plan: GetOrgNetwork Menu Item

**Branch**: `626-mist-get-org-network` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/626-mist-get-org-network/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/networks/{network_id}` (operationId `getOrgNetwork`) to
retrieve the full configuration of a single organization-level Network (subnet / VLAN /
routing definition) by its UUID. The new menu item prompts the user for `org_id` and
`network_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the nested response
(nested objects for `internal_access`, `internet_access`, `multicast`, `tenants`,
`vpn_access`, and their sub-maps) into one row per parent Network plus per-key rows for
the `additionalProperties` maps (destination NAT, static NAT, multicast groups, tenants,
VPN accesses), and persists results through `DataExporter.write_with_format_selection()`
so CSV, SQLite, and ArangoDB+Redis backends stay consistent. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly in SQLite. The new
operation is proposed as menu number **58** -- the next available slot inside the Safe
Org Exports Config/Admin band (42-50) plus the adjacent Misc band (56-59), positioned so
it sits close to the existing `listOrgNetworks` (menu 4) list operation for operator
discoverability.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints
require 3.13 or newer; the project pins CPython features such as PEP 695 type aliases
and the improved traceback formatter).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transitive HTTP transport); `python-dotenv`
(loads `.env` for `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land under `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend on production nodes.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode using `MIST_ORG_ID` and a probe network UUID discovered from a prior
`listOrgNetworks` run. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected -- menu 58 sits
inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200; both
must work without source change. Path handling uses `pathlib.Path` / `os.path.join`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on 8055. This feature is CLI-only.
**Performance Goals**: Single GET completes in <=5 seconds for a typical Network object
(the endpoint is non-paginated; the response is a single JSON object usually well under
16 KB). Adaptive delay metrics in `delay_metrics.json` / `tuning_data.json` continue to
govern back-off; this endpoint is light enough that no per-endpoint tuning is needed.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining; inline comments on every
executable line; before/after action logging on every meaningful step.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`NetworkExportUtils`-style class -- specifically the class that already owns
`listOrgNetworks` output (see Project Structure -> Source Code below). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (`getOrgNetwork`), plus up to five new normalized child
tables for the `additionalProperties` maps (`org_network_destination_nat`,
`org_network_static_nat`, `org_network_multicast_groups`, `org_network_tenants`,
`org_network_vpn_access`), one menu registration line, one README menu-table row, one
CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_network()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `network_id`), and contains <=5 logical blocks
  (prompt org_id -> prompt network_id -> API call -> flatten -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. The nested-map flatteners
  (destination NAT, static NAT, multicast groups, tenants, VPN access) are extracted as
  private helpers on the same class so each stays under 25 lines with <=5 blocks. No new
  packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the same class that owns
  `listOrgNetworks` (canonically the `OrgConfigExportUtils` / networks-owning class in
  `MistHelper.py`; the exact class name is confirmed at task time via `grep -n
  "def.*listOrgNetworks" MistHelper.py`). If no natural home exists, the method attaches
  to `OrgExportUtils` -- never a standalone wrapper function. Menu dispatch references
  the class method directly. Variable names use full words (`network_row`,
  `destination_nat_rows`, `vpn_access_rows`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both prompts use `safe_input()` with explicit `context=` strings
  (`"org_network:org_id"`, `"org_network:network_id"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. Both UUIDs are validated by the existing
  `is_valid_uuid()` helper before the API call; on failure the method logs `WARNING` and
  returns early. The endpoint is strictly read-only (HTTP GET); no typed
  destructive-confirmation gate is needed. API token comes from `.env` via
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgNetwork` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting. `INFO` is
  emitted before the API call ("Fetching network %s for org %s"); `DEBUG` after the call
  with a shape summary ("Network name=%s subnet=%s vlan_id=%s tenants=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No API token, request URL query string, or full auth header
  value is ever logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the flatten helpers, the
  new PK strategy dict entry, and the menu registration line will carry an inline
  comment that explains *why* the line exists, not merely what it does. Blank lines,
  bare closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing networks-export cluster)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each prompt, `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a summary, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten with row counts per child map,
  `logging.info(...)` before each `DataExporter.write_with_format_selection()` call.
  The DataExporter emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/626-mist-get-org-network/
- plan.md                    # This file
- research.md                # Phase 0 -- SDK signature, PK strategy, naming, menu placement, prompts
- data-model.md              # Phase 1 -- response entities + DDL + PK registration
- quickstart.md              # Phase 1 -- local run + .env + quality gates
- contracts/
    - get_org_network.md     # Phase 1 -- full HTTP + SDK contract
- tasks.md                   # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py                # New method on the networks-owning class + PK strategy entry
                             # + menu 58 registration. No new modules; same single-file
                             # monolith. Extends the class that already owns
                             # `listOrgNetworks` export (confirmed at task time via
                             # `grep -n "listOrgNetworks" MistHelper.py`).
README.md                    # Operation count bump + new row in the menu table for op 58
CHANGELOG.md                 # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
data/                        # Runtime output target (existing dir). No schema migration
                             # beyond the new SQLite tables created on first write by
                             # DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing networks-export class in `MistHelper.py` (the class that owns
`listOrgNetworks`). No new class is introduced; no wrapper function is introduced. The
menu number proposal is **58**, chosen because operations 42-50 (Config/Admin) and 56-59
(Misc) inside the 1-59 Safe Org Exports block are the natural home for a single-object
read of a config resource. Menu 58 is well below the resource-intensive block at
96-101 and the destructive block at 154-194. If 58 collides with an in-flight feature
branch at task time, the next free integer inside the same Safe Org Exports cluster is
used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. Each map-flattener helper
  stays under 25 lines. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single insert
  in the existing dict literal -- no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing networks-owning
  class. Flatten helpers are private methods on the same class. No wrappers introduced.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only with no destructive side effect. `safe_input()` handles both prompts.
  Both UUIDs validated before any SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline documented
  in `.github/copilot-instructions.md`.
- **Principle V (Observability)**: PASS -- Every log statement in the design is
  ASCII-only, uses `%s` formatting, and never includes the API token.
- **Principle VI (Inline Comments)**: PASS -- The `quickstart.md` skeleton demonstrates
  the required comment density on every executable line, including the new PK strategy
  entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The `quickstart.md` skeleton enumerates
  before/after log pairs for every meaningful action (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
