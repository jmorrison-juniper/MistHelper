# Implementation Plan: Legacy Compat Shim Decomposition

**Branch**: `1002-legacy-compat-shim-decomposition` | **Date**: 2026-06-15 | **Spec**: `specs/1002-legacy-compat-shim-decomposition/spec.md`
**Input**: Feature specification from `specs/1002-legacy-compat-shim-decomposition/spec.md`

## Summary
Decompose legacy compatibility wrappers/shims and dynamic facade branches into explicit canonical ownership in existing `src` modules, using phased cutover with parity checkpoints, temporary-adapter expiry control, and static callsite guards. Scope explicitly covers MistHelper.py legacy delegates, top-level `__init__.py` shim branches/fallbacks, capture alias wrappers (`run()` -> `execute()`), and site insights callsite migration away from `InsightMetricsUtils.export_legacy()`.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: mistapi 0.59+, pytest, ruff, project-internal `src` packages  
**Storage**: File-based artifacts/logs and existing project stores (CSV/SQLite/polyglot backends)  
**Testing**: pytest unit/integration, parity regression scripts, static callsite audits  
**Target Platform**: Windows development + Linux container runtime (Podman primary)
**Project Type**: Monolithic Python CLI/service repository with modularized `src` packages  
**Performance Goals**: No observable regression in menu/export paths; parity checkpoints pass each phase  
**Constraints**: No new generic utility sink module; class-based ownership; temporary adapters must have hard expiry gates  
**Scale/Scope**: Inventory listed in `spec.md` (legacy delegates, facade branches, capture aliases, site insights callsites)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Five-Item Rule**: PASS. Plan uses bounded workstreams and existing module boundaries.
- **Class-Based Architecture (No Wrappers)**: PASS with condition. End-state removes wrappers; temporary adapters allowed only with expiry gates.
- **Safety-First Input Handling**: PASS. No new user-input flows introduced by this plan.
- **Deployment Pipeline Compliance**: PASS. Validation matrix includes quality gates and release-window docs updates.
- **Observability & Logging**: PASS. Migration keeps existing logging standards; no silent fallback growth.
- **Inline Comments Non-Negotiable**: PASS. Implementation tasks must include line-level comments where code changes occur.
- **Action Logging Non-Negotiable**: PASS. Any touched logic must log before/after actions per constitution.

## Project Structure

### Documentation (this feature)

```text
specs/1002-legacy-compat-shim-decomposition/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── shim-decomposition-contract.md
│   └── validation-matrix-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
MistHelper.py
__init__.py
src/
├── capture/
│   ├── __init__.py
│   ├── site_pcap_wait_download_workflow.py
│   └── org_pcap_wait_download_workflow.py
├── export/
│   └── site_insights/
│       ├── site_metric_operation.py
│       └── device_metric_operation.py
└── menu/

tests/
├── unit/
├── integration/
└── [static-audit checks]
```

**Structure Decision**: Single Python project with targeted modifications in existing files and no new compatibility hub.

## Architecture

### Target Architecture
- Canonical behavior remains in explicit domain modules (`src/export/site_insights`, `src/capture`, `src/menu`, existing utility owners).
- Compatibility shims/facades are either:
  - removed,
  - replaced by direct imports, or
  - retained as narrowly scoped temporary adapters with hard expiry.
- Dynamic top-level `__getattr__` usage is reduced to minimal transitional scope, then retired per matrix.

### Workstream Architecture Boundaries

1. **WS-1 MistHelper.py Legacy Delegates**
- Scope: `get_csv_file_path_legacy`, `export_const_insight_metrics_to_csv`, `export_gateway_templates_to_csv_legacy`.
- Target: direct canonical module/service entry points.
- Exit: no internal callsites to retired delegates.

1. **WS-2 `__init__.py` Shim Branches and Menu Fallbacks**
- Scope: listed `__getattr__` branches + `_noop_menu_action` + `_ensure_menu_coverage`.
- Target: explicit direct imports to canonical owners, transitional fallback removal after parity checkpoints.
- Exit: retired branches absent from internal references; fallback growth = zero.

1. **WS-3 Capture Alias Wrappers**
- Scope: `run()` aliases in site/org pcap workflows and capture package lazy facade.
- Target: `execute()` as canonical interface; adapters time-bounded to expiry.
- Exit: alias-dependent tests migrated; adapters removed when expiry gates pass.

1. **WS-4 Site Insights Callsite Migration**
- Scope: `site_metric_operation.py` and `device_metric_operation.py` calls to `InsightMetricsUtils.export_legacy()`.
- Target: direct canonical export/cache-refresh API in `src/export/site_insights`.
- Exit: zero internal `export_legacy` calls.

## Phased Execution

### Phase 0: Research and Decision Lock
- Finalize inventory decision matrix (`remove | direct_import | temporary_adapter`).
- Confirm canonical owner per inventory row.
- Confirm expiry/removal triggers for temporary adapters.

### Phase 1: Canonical Enablement
- Enable/verify direct canonical imports and owners for all targeted branches.
- Establish canonical site insights export entry points for downstream callsites.
- Prepare static audit rules for prohibited symbol usage.

### Phase 2: Core Decomposition
- Execute WS-1 and WS-4 primary migrations.
- Decommission immediate-retire wrappers and legacy export bridges.
- Preserve only approved temporary adapters.

### Phase 3: Facade and Alias Retirement
- Execute WS-2 and WS-3 retirements based on parity status.
- Restrict and retire menu fallback transitional behavior.
- Remove expired adapters and update migration inventory status.

### Phase 4: Test Migration and Parity Closure
- Migrate tests from alias/facade expectations to canonical interfaces.
- Run menu/export parity checkpoints and static audits.
- Approve rollback or progression per validation matrix outcomes.

### Phase 5: Documentation and Finalization
- Publish README and CHANGELOG entries for each retirement/removal.
- Freeze final audit evidence for SC-001..SC-007.
- Close feature when all validation matrix rows pass.

## Dependencies

### Technical Dependencies
- Existing canonical implementations in `src/export/site_insights`, `src/capture`, `src/menu`.
- Current test harness coverage around exports, capture workflows, and menu operations.
- Static search/audit capability for symbol usage detection.

### Workstream Dependencies
- WS-4 depends on canonical export interface readiness from Phase 1.
- WS-2 fallback retirement depends on parity checkpoint pass from WS-1/WS-4.
- WS-3 adapter removal depends on test migration completion and adapter expiry gates.

### Release Dependencies
- Documentation/changelog updates must ship in same release window as each migration cut.
- CI gates for lint/test/static audits must pass before phase closure.

## Risk Controls

| Risk | Impact | Control | Trigger | Mitigation |
| - | - | - | - | - |
| Hidden third-party imports of retired facade names | Runtime break outside internal code | Temporary adapters with explicit expiry + migration notes | External bug reports post-cut | Re-enable scoped adapter for one release with dated removal |
| Menu parity gaps masked by legacy fallback | Operator workflow failure | Phase checkpoint + no new fallback growth policy | Parity failure in scoped menu tests | Roll back fallback retirement for affected operation only |
| Capture alias removal breaks tests | CI instability | Staged `run()` adapter deprecation and test migration first | Failing alias-dependent tests | Delay alias removal until tests all use `execute()` |
| Export cache side effects lost in callsite migration | Data/output divergence | Baseline vs post-migration export parity diff | Output mismatch in parity suite | Restore transitional bridge and patch canonical sequence |
| Shim reintroduction during concurrent edits | Long-term architecture regression | Static audit rules for prohibited symbol references | New prohibited callsite in CI | Block merge and require canonical path change |

## Validation Matrix

| ID | Requirement/Success Criterion | Validation Type | Evidence Artifact | Phase Gate | Pass Condition |
| - | - | - | - | - | - |
| VM-01 | FR-001 / SC-001 inventory decision completeness | Inventory audit | Decision matrix report | Phase 0 exit | 100% rows classified with owner |
| VM-02 | FR-002 canonical ownership mapping | Design review + static mapping check | Ownership map artifact | Phase 1 exit | Every symbol maps to explicit canonical module |
| VM-03 | FR-003 adapter policy enforcement | Schema/rule validation | Adapter lifecycle report | Phase 1+ ongoing | All temporary adapters have expiry + trigger |
| VM-04 | FR-004 / SC-002 retired `*_legacy` callsite elimination | Static callsite audit | Audit report (`no_legacy_calls`) | Phase 3/4 exit | 0 internal matches |
| VM-05 | FR-005 capture alias migration | Unit/integration tests | Capture workflow test report | Phase 3 exit | Canonical `execute()` path green; alias policy satisfied |
| VM-06 | FR-006 / SC-004 retired `__getattr__` branch elimination | Static audit + import tests | Facade branch audit report | Phase 3/4 exit | 0 internal references to retired branches |
| VM-07 | FR-007 / SC-005 menu fallback retirement | Menu parity regression | Parity checkpoint report | Phase 4 exit | Migration-scope menu operations parity pass |
| VM-08 | FR-008 / SC-006 test migration completion | Test inventory diff | Canonical test mapping report | Phase 4 exit | Alias/facade-dependent tests migrated or approved temporary |
| VM-09 | FR-009 phased risk strategy | Governance review | Phase checkpoint log | Every phase exit | Risks evaluated; rollback criteria documented |
| VM-10 | FR-010 / SC-007 docs + changelog delivery | Documentation review | README + CHANGELOG entries | Phase 5 exit | Published in same release window |
| VM-11 | SC-003 zero `InsightMetricsUtils.export_legacy()` internal calls | Static callsite audit | Audit report (`no_export_legacy_calls`) | Phase 2/3 exit | 0 internal matches |

## Complexity Tracking

No constitution violations expected. Temporary adapters are intentional transitional controls with hard expiry and documented removal gates.
