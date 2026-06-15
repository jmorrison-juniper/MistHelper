# Implementation Plan: Org Async Claim Menu Operations (mistapi 0.63.0)

**Branch**: `1001-site-marvis-config-actions` | **Date**: 2026-06-12 | **Spec**: `specs/203-org-async-claims/spec.md`
**Input**: Feature specification from `specs/203-org-async-claims/spec.md`

## Summary

Add three new org-level menu operations in `MistHelper.py` for mistapi 0.63.0 async-claim workflows: (1) list async claims (safe export), (2) create async claim (destructive + typed confirmation), and (3) get async claim status by claim ID (safe export). The implementation will reuse existing MistHelper patterns: `safe_input()` validation, `_confirm_destructive()` confirmation gate, `DataExporter.save_data_to_output(..., api_function_name=...)` persistence, and `ENDPOINT_PRIMARY_KEY_STRATEGIES` upsert-safe identity rules.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: `mistapi` (0.63.0 target), built-in logging/argparse, existing MistHelper helpers (`safe_input`, `flatten_nested_fields_in_list`, `DataExporter`)  
**Storage**: CSV exports in `data/` and optional SQLite writes through existing `DataExporter` pipeline  
**Testing**: `pytest` (`tests/unit` and targeted integration parity tests) + existing `--test`/`--testinteractive` harness behavior  
**Target Platform**: Windows dev + Linux container runtime (Podman primary)  
**Project Type**: Python CLI monolith (menu-driven operations in `MistHelper.py`)  
**Performance Goals**: List/status operations complete in standard Mist API response time; no long-running polling loop introduced  
**Constraints**: Preserve non-destructive default test profile; create operation must never execute without exact typed confirmation; follow existing logging/safety conventions  
**Scale/Scope**: 3 new menu operations (operation count 207→210 in docs/spec), PK strategy additions, tests + docs updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule | PASS | No new directories beyond feature docs/contracts; implementation phase limited to existing files/patterns. |
| Class-Based/No Wrapper Regression | PASS | No architectural wrapper changes planned; new functions follow current menu function style. |
| Safety-First Input Handling | PASS | Claim ID and payload inputs use `safe_input`; create path uses strict typed confirmation. |
| Deployment/Quality Gates Awareness | PASS | Plan includes required lint/test/doc updates; no code deployment in this phase. |
| Observability & Logging | PASS | Pre/post action logging required around API calls and exports. |
| Inline Comments & Action Logging Standards | PASS | Implementation tasks explicitly require non-negotiable comment/log coverage for touched blocks. |
| SpecKit Escalation Requirement | PASS | Feature adds new menu/API integration and destructive operation, correctly handled via SpecKit artifacts. |

**Post-Design Re-check**: PASS. Phase 1 artifacts fully resolve clarifications; no constitutional violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/203-org-async-claims/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── menu-operations-contract.md
└── tasks.md               # generated later by /speckit.tasks
```

### Source Code (repository root)

```text
MistHelper.py                         # Add menus 208/209/210 + handlers + PK mappings
README.md                             # Operation count + menu table updates
CHANGELOG.md                          # Versioned entry for async claim support
tests/unit/                           # New tests for success/validation/error paths
tests/integration/                    # Optional targeted compatibility test update
```

**Structure Decision**: Keep feature implementation inside existing monolith/menu architecture to preserve operational consistency and reduce risk for junior NOC maintainers.

## Phase 0: Research Plan (completed)

Resolved all open clarification items:

1. **Endpoint contract mapping**: validated org async claim endpoints and status endpoint shape from project docs and upstream notes.
2. **Menu numbering strategy**: reserve operations 208–210 directly after existing 207 to satisfy FR-012.
3. **Destructive gating pattern**: reuse `_confirm_destructive("CREATE", ...)` + early-return semantics.
4. **Persistence identity strategy**: define endpoint PK strategies for list/create/status outputs to avoid duplicates.
5. **Default test safety**: ensure create operation is excluded from default `--test` destructive-safe profile.

Research output written to `specs/203-org-async-claims/research.md`.

## Phase 1: Design & Contracts (completed)

1. **Data model** documented in `data-model.md` (records, requests, state transitions, validations).
2. **Interface contracts** documented in `contracts/menu-operations-contract.md` for menu actions and API mapping.
3. **Operator quickstart** created in `quickstart.md` for implementation/verification flow.
4. **Agent context pointer** updated in `.github/copilot-instructions.md` between SPECKIT markers to this feature plan.

## Phase 2 Preview (for /speckit.tasks)

- Add handlers for:
  - `list_org_async_claims()` (safe export)
  - `create_org_async_claim()` (destructive)
  - `get_org_async_claim_status()` (safe export)
- Wire menu entries 208/209/210 in `menu_actions` with descriptions and safety labels.
- Add PK strategies in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- Update `run_systematic_test()` skip maps for destructive create operation.
- Add/adjust tests for success, validation failure, and API errors.
- Update docs (`README.md`, `CHANGELOG.md`) for operation count and release note.

## Complexity Tracking

No constitutional violations requiring exception.
