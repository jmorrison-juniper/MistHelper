# Implementation Plan: countOrgDeviceLastConfigs Menu Item

**Branch**: `513-mist-count-org-device-last-configs`
**Date**: 2026-06-28
**Spec**: [specs/513-mist-count-org-device-last-configs/spec.md](./spec.md)
**Status**: Draft -- Phase 0 + Phase 1 complete

## Summary

Add a new safe, read-only MistHelper menu item that invokes
`mistapi.api.v1.orgs.devices.last_config.count.countOrgDeviceLastConfigs()` to
return aggregate counts of distinct fields across the org-level device
last-configuration history. The implementation extends the existing
`OrgDataExporter` class (sibling of the Menu 14 `searchOrgDeviceLastConfigs`
caller), uses `safe_input()` for every prompt, persists results through
`DataExporter.write_with_format_selection(...)`, and registers a new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` using the `auto_increment_with_unique` PK
strategy (the response is an ad-hoc aggregation that has no stable natural
key). Proposed menu number: **195** (first free slot after the current safe
org-export band; sits adjacent to Menu 14 conceptually but appends to the
sequential menu without renumbering existing operations).

## Technical Context

- **Language / Version**: Python 3.13 or newer (CPython, per repository
  `requirements.txt` and venv).
- **Primary Dependencies**: `mistapi>=0.59` (Thomas Munzer SDK), `requests`,
  `python-dotenv`, `colorama`, `tabulate`, project-local utilities in
  `MistHelper.py` (`safe_input`, `DataExporter`, `GlobalImportManager`).
- **Storage**: Multi-backend selection at runtime --
  - CSV: `data/countOrgDeviceLastConfigs_<org_id>_<UTC>.csv`
  - SQLite: `data/mist_data.db`, table
    `count_org_device_last_configs`
  - Optional polyglot: ArangoDB collection
    `count_org_device_last_configs` + Redis hot-cache key
    `mh:count_org_device_last_configs:<org_id>`
- **Testing**: `python MistHelper.py --test` (interactive smoke menu loop with
  skip-list), `python -m py_compile MistHelper.py`, `python -m ruff check
  MistHelper.py`, `python -m black --check MistHelper.py`, plus the pytest
  property/E2E suite in `tests/` once Phase 2 lands.
- **Target Platform**: Windows 11 dev host (PowerShell, venv at
  `.venv\Scripts\Activate.ps1`) and Linux container target
  `ghcr.io/jmorrison-juniper/misthelper:latest` (Podman primary, Docker
  compatible), SSH-fronted on port 2200 and web UI on port 8055.
- **Project Type**: Single Python monolith
  (`MistHelper.py` ~28K lines) with a `data/` runtime directory; no separate
  backend/frontend split.
- **Performance Goals**: A single org-level count returns in well under 2 s
  against a healthy Mist API; adaptive rate-limiter must keep the call below
  the 5000 calls/hour quota; the menu handler must not block the event loop
  beyond 60 s even with `MIST_PAGE_LIMIT=1000` paging.
- **Constraints**: No interactive `input()` outside `safe_input()`; no Unicode
  / emoji in logs; ASCII only; 5-Item Rule (max 5 params, 5 blocks, 25 lines
  per function) per `coding-standards.instructions.md`; every executable line
  needs an inline comment; every action wrapped with `logging.info(...)`
  before and `logging.debug(...)` after.
- **Scale / Scope**: Endpoint is org-wide and returns one aggregation
  document (`{distinct, results[], start, end, total, limit}`); per-org
  payload size is in the low kilobytes. The catalogue work touches one new
  menu method (~25 lines), one new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry,
  one new menu registration tuple, and one `CHANGELOG.md` line.

## Constitution Check

Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

| Principle | Verdict | Evidence |
|-----------|---------|----------|
| I. Safety-First Input Handling | **PASS** | All user prompts route through `safe_input(prompt, context="count_org_device_last_configs_<field>")`; no destructive action -- read-only GET. |
| II. Natural Business Keys / PK Strategy | **PASS** | New `ENDPOINT_PRIMARY_KEY_STRATEGIES['countOrgDeviceLastConfigs']` entry of type `auto_increment_with_unique` with unique key `(org_id, distinct, start, end)`; documented in `data-model.md`. |
| III. Multi-Backend Output via DataExporter | **PASS** | Handler calls `DataExporter.write_with_format_selection(rows, "countOrgDeviceLastConfigs", api_function_name="countOrgDeviceLastConfigs")`; no direct CSV / SQL writes. |
| IV. 5-Item Structural Discipline | **PASS** | Menu method takes 2 params (`self`, `mist_session`), uses <=5 internal blocks, body <=25 lines; helpers extracted if it grows. |
| V. ASCII-Only Logging | **PASS** | All `logging.info / debug / warning` calls use plain ASCII, no emoji, no smart quotes. |
| VI. Inline Comments on Every Executable Line (NON-NEGOTIABLE) | **PASS** | Every line of the new menu method and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry carries a trailing `# why` comment; verified in code-review checklist. |
| VII. Action Logging Before / After Every Operation (NON-NEGOTIABLE) | **PASS** | `logging.info("Counting org device last-config history for org %s distinct=%s", org_id, distinct)` precedes the SDK call; `logging.debug("Received %s results, total=%s", len(rows), payload.get('total'))` follows it. |

**Pre-Phase 0 Gate**: **PASS** -- no exceptions, no Complexity Tracking entries
needed.

## Project Structure

### Documentation tree for this feature

```
specs/513-mist-count-org-device-last-configs/
|-- spec.md                  # Feature spec (already authored, untouched here)
|-- plan.md                  # THIS file
|-- research.md              # Phase 0 decisions (created in this run)
|-- data-model.md            # Phase 1 entity & SQLite DDL (created in this run)
|-- quickstart.md            # Phase 1 dev quickstart (created in this run)
\-- contracts/
    \-- count_org_device_last_configs.md  # Phase 1 HTTP + SDK contract
```

### Source-code tree (where new code lives)

```
MistHelper.worktrees/copilot-openapi-mist-api-endpoint-cataloging/
|-- MistHelper.py
|   |-- class OrgDataExporter:                    # existing host class
|   |   \-- def menu_195_count_org_device_last_configs(self, mist_session)
|   |-- ENDPOINT_PRIMARY_KEY_STRATEGIES dict      # add 'countOrgDeviceLastConfigs' key
|   \-- MENU_REGISTRY tuple                       # register (195, 'Org -- Count device last-config history', handler)
|-- CHANGELOG.md                                  # one entry under Unreleased
\-- data/                                          # runtime output dir (gitignored)
```

**Class choice rationale**: `OrgDataExporter` already owns Menu 14
(`searchOrgDeviceLastConfigs`) and every other `orgs.devices.last_config.*`
SDK call. Hosting the count sibling in the same class keeps related methods
together, avoids a one-method class (5-Item Rule discourages it), and reuses
the class's existing `mist_session`, `safe_input`, and exporter helpers. No
new class is justified.

## Phase 0 -- Research

See [research.md](./research.md). Five research tasks resolved with explicit
Decision / Rationale / Alternatives blocks. No `NEEDS CLARIFICATION` markers
remain.

## Phase 1 -- Design & Contracts

Outputs:

- [data-model.md](./data-model.md) -- entities, SQLite DDL, and
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry.
- [quickstart.md](./quickstart.md) -- how a developer runs and verifies the
  new menu item locally.
- [contracts/count_org_device_last_configs.md](./contracts/count_org_device_last_configs.md)
  -- full HTTP + SDK contract, response schema, error handling.

### Post-Phase 1 Re-Check

- Constitution principles I-VII: all still **PASS** -- the Phase 1 artifacts
  did not introduce any wrappers, did not bypass `DataExporter`, and did not
  add any non-ASCII content.
- Spec acceptance criteria (FR-001 .. FR-005) are all addressed: handler call
  (FR-001), required path/query params (FR-002), output filename
  (FR-003), error handling (FR-004), PK-strategy registration (FR-005).
- No new third-party dependencies introduced; the SDK module is already a
  transitive of `mistapi>=0.59`.

**Post-Phase 1 Gate**: **PASS**.

## Complexity Tracking

| Exception | Justification | Mitigation |
|-----------|---------------|------------|
| _None_ | _None required -- all seven principles passed without exception._ | _n/a_ |

## Progress Tracking

- [x] Phase 0 -- Research complete (research.md)
- [x] Phase 1 -- Design & contracts complete (data-model.md, quickstart.md,
  contracts/)
- [ ] Phase 2 -- /speckit.tasks (NOT executed here; out of scope per task
  instructions)
- [ ] Phase 3 -- Implementation (future)
- [ ] Phase 4 -- Validation (future)
