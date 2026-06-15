# Feature Specification: Legacy Compat Shim Decomposition

**Feature Branch**: `[1002-legacy-compat-shim-decomposition]`  
**Created**: 2026-06-15  
**Status**: Draft  
**Input**: User description: "Create/update a new SpecKit feature spec in MistHelper (Python) focused on eliminating dead compatibility wrappers/shims and moving canonical behavior into proper src modules/submodules."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retire dead compatibility indirection (Priority: P1)

As a maintainer, I can remove dead legacy wrappers and shim branches so canonical behavior is owned by explicit `src` modules instead of compatibility indirection.

**Why this priority**: This directly reduces maintenance risk, hidden coupling, and test fragility in hot-path exports and menu/runtime loading.

**Independent Test**: Can be fully tested by running shim-focused unit tests plus targeted integration tests proving canonical modules execute without legacy delegates.

**Acceptance Scenarios**:

1. **Given** compatibility wrappers are inventoried, **When** migration phase actions are applied, **Then** canonical module entry points remain behavior-equivalent for existing user workflows.
2. **Given** a retired legacy symbol, **When** internal code is statically scanned, **Then** no internal callsite references the retired symbol.

---

### User Story 2 - Preserve user-facing behavior during phased migration (Priority: P2)

As an operator, I can run existing menu operations and export flows without user-visible regressions while legacy shims are decomposed in phases.

**Why this priority**: Behavior parity is required for production usage and avoids break/fix churn for junior NOC users.

**Independent Test**: Can be independently tested by menu regression runs and export parity comparisons before/after each phase.

**Acceptance Scenarios**:

1. **Given** phased migration is in progress, **When** a mapped menu action is invoked, **Then** output shape and success/failure semantics match pre-migration behavior.
2. **Given** test harness compatibility constraints, **When** temporary adapters are present, **Then** they include explicit expiry criteria and deprecation tracking.

---

### User Story 3 - Harden test suite around canonical interfaces (Priority: P3)

As a test maintainer, I can migrate tests away from alias/facade entry points to canonical module interfaces so future decomposition does not require compatibility shims.

**Why this priority**: Prevents reintroduction of legacy indirection and reduces brittle patching around dynamic facades.

**Independent Test**: Can be independently tested by updating unit tests currently asserting shim paths and proving equivalent assertions against canonical imports.

**Acceptance Scenarios**:

1. **Given** tests currently target aliases/facades, **When** migration completes, **Then** tests target canonical classes/functions in `src` packages.
2. **Given** legacy adapters with expiry dates, **When** expiry conditions are met, **Then** adapter-focused tests are removed and canonical tests remain green.

---

### Edge Cases

- What happens when third-party or local scripts import retired shim symbols directly from top-level `__init__.py`?
- How does the system handle partially migrated menu coverage where a legacy fallback currently masks missing canonical action registration?
- What happens when capture workflows rely on `run()` in tests while production code already uses `execute()`?
- How does migration proceed if export cache refresh ordering depends on `InsightMetricsUtils.export_legacy()` side effects?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a complete decomposition inventory of all legacy compatibility wrappers/shims and facade branches listed in this specification.
- **FR-002**: System MUST define canonical ownership for each inventoried behavior in explicit `src` modules/submodules and prohibit introducing a new generic helper dumping-ground module.
- **FR-003**: System MUST classify each inventoried wrapper/shim as one of: removed, replaced by direct import, or temporary adapter with an explicit expiry date and removal trigger.
- **FR-004**: System MUST migrate internal callsites from `*_legacy` functions to canonical interfaces with behavior parity.
- **FR-005**: System MUST migrate capture workflow alias usage from `run()` compatibility aliases to canonical `execute()` paths.
- **FR-006**: System MUST retire selected top-level `__getattr__` compatibility facade branches for names marked retired in this plan and replace retained behavior with direct canonical imports or scoped adapters.
- **FR-007**: System MUST remove internal reliance on legacy menu fallback behavior (`_noop_menu_action`, `_ensure_menu_coverage`) for operations covered by canonical registry paths.
- **FR-008**: System MUST migrate tests that rely on alias/facade behavior to canonical imports/entry points and keep temporary adapter tests only until adapter expiry criteria are met.
- **FR-009**: System MUST provide a compatibility/risk strategy for menu operations and test harness behavior during each migration phase.
- **FR-010**: System MUST deliver documentation and changelog updates that record removed shims, temporary adapters, expiry dates, and migration guidance.

### Decomposition Inventory (MUST-INCLUDE)

| Scope | File | Symbol/Behavior | Current Role | Decision | Target Canonical Ownership | Adapter Expiry (if applicable) |
| - | - | - | - | - | - | - |
| MistHelper.py legacy delegates | `MistHelper.py` | `get_csv_file_path_legacy` | Legacy delegate to `get_csv_file_path` | Remove wrapper; direct canonical call | `src` export/file-path owner for CSV path resolution | N/A |
| MistHelper.py legacy delegates | `MistHelper.py` | `export_const_insight_metrics_to_csv` | Legacy backward-compat export behavior | Replace with canonical export service entry point | `src/export/site_insights` canonical metric export module | 2026-09-30 (if temporary adapter needed) |
| MistHelper.py legacy delegates | `MistHelper.py` | `export_gateway_templates_to_csv_legacy` | Legacy compatibility helper | Remove wrapper; direct canonical export operation | Canonical gateway template export module in `src/export` | N/A |
| Capture alias wrappers | `src/capture/site_pcap_wait_download_workflow.py` | `run()` alias to `execute()` | Backward-compatible alias (tests) | Temporary adapter, then remove alias | `SitePcapWaitDownloadWorkflow.execute()` | 2026-08-31 |
| Capture alias wrappers | `src/capture/org_pcap_wait_download_workflow.py` | `run()` alias to `execute()` | Backward-compatible alias (tests) | Temporary adapter, then remove alias | `OrgPcapWaitDownloadWorkflow.execute()` | 2026-08-31 |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `DataProcessingUtils` | Dynamic facade branch | Retire shim branch; direct canonical import | Owning `src` data processing module | 2026-09-30 (if deprecation adapter required) |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `InsightMetricsUtils` (including `export_legacy`) | Dynamic facade + legacy export bridge | Retire legacy branch; direct canonical metric export/import | `src/export/site_insights` modules | 2026-09-30 |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `PromptUtils` | Dynamic facade branch | Replace with direct import | Canonical prompt utility module in `src` | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `EnhancedSSHRunner` | Dynamic facade branch | Replace with direct import | Canonical SSH runner module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `SiteExportUtils` | Dynamic facade branch | Retire shim branch; direct import | Site export canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `SiteClientExporter` | Dynamic facade branch | Retire shim branch; direct import | Site client export canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OrgAlarmEventExporter` | Dynamic facade branch | Retire shim branch; direct import | Org alarm/event canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OrgExportUtils` | Dynamic facade branch | Retire shim branch; direct import | Org export canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `APIDataFetcher` | Dynamic facade branch | Replace with direct import | API fetcher canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `ConfigUtils` | Dynamic facade branch | Replace with direct import | Config canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `InputUtils` | Dynamic facade branch | Replace with direct import | Input canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OperationRegistry` | Dynamic facade branch | Replace with direct import | Canonical operation registry in `src/menu` | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `WAN2MigrationManager` | Dynamic facade branch | Retire shim branch; direct import | WAN migration canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `ServicePingManager` | Dynamic facade branch | Retire shim branch; direct import | Service ping canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `TroubleshootUtils` | Dynamic facade branch | Retire shim branch; direct import | Troubleshoot canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `SSHRunnerManager` | Dynamic facade branch | Retire shim branch; direct import | SSH runner manager canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OrgTicketManager` | Dynamic facade branch | Retire shim branch; direct import | Org ticket canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `TimeUtils` | Dynamic facade branch | Replace with direct import | Time utility canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OrgInventoryExporter` | Dynamic facade branch | Retire shim branch; direct import | Org inventory export canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `__getattr__` branch: `OrgDeviceStatsExporter` | Dynamic facade branch | Retire shim branch; direct import | Org device stats canonical module | N/A |
| Top-level compatibility facade hub | `__init__.py` | `_noop_menu_action` | Legacy menu fallback placeholder | Temporary adapter while registry parity closes | Canonical menu dispatch/registry paths | 2026-08-31 |
| Top-level compatibility facade hub | `__init__.py` | `_ensure_menu_coverage` | Legacy fallback coverage patching | Temporary adapter while registry parity closes | Canonical menu dispatch/registry paths | 2026-08-31 |
| Capture package lazy facade | `src/capture/__init__.py` | Lazy `PacketCaptureManager` export via `__getattr__` | Compatibility-oriented lazy facade | Replace with explicit package export/import map (no generic facade) | `src/capture/packet_capture_manager.py` canonical import path | 2026-09-30 (if staged) |
| Legacy export shim callsites | `src/export/site_insights/site_metric_operation.py` | `InsightMetricsUtils.export_legacy()` call | Calls legacy compatibility export shim | Replace with direct canonical export/cache refresh call | `src/export/site_insights` canonical API | N/A |
| Legacy export shim callsites | `src/export/site_insights/device_metric_operation.py` | `InsightMetricsUtils.export_legacy()` call | Calls legacy compatibility export shim | Replace with direct canonical export/cache refresh call | `src/export/site_insights` canonical API | N/A |

### Migration Phases

1. **Phase 1 - Inventory lock and ownership map**
   - Freeze the decomposition inventory in this spec and map each symbol to canonical owner module.
   - Define explicit remove/direct-import/temporary-adapter status per row.
   - Establish adapter expiry tracker for only approved temporary adapters.

2. **Phase 2 - Canonical path enablement**
   - Introduce/confirm direct canonical imports for facade-backed names.
   - Implement canonical metric export path used by site/device metric operations.
   - Move callsites off `InsightMetricsUtils.export_legacy()` to canonical service methods.

3. **Phase 3 - Shim decommissioning**
   - Remove wrappers approved for immediate retirement (`*_legacy` removals, retired `__getattr__` branches).
   - Keep only temporary adapters with documented expiry and deprecation messaging.
   - Reduce menu fallback behavior to strictly transitional coverage gaps.

4. **Phase 4 - Test and menu parity closure**
   - Migrate tests from alias/facade assertions to canonical imports and methods.
   - Replace capture `run()` test usage with `execute()` and remove alias adapters after expiry gates pass.
   - Validate menu operation parity with canonical registry and remove `_noop_menu_action` / `_ensure_menu_coverage` transitional behavior.

5. **Phase 5 - Final retirement and documentation**
   - Remove all expired temporary adapters.
   - Confirm no internal callsites reference retired shim symbols.
   - Publish changelog + docs migration notes with deprecation/removal timeline and compatibility notes.

### Test Migration Strategy

- Build a shim-targeted test inventory listing tests that currently import alias/facade paths (`__getattr__` names, `run()` aliases, `export_legacy`).
- For each inventoried test, rewrite assertions against canonical module/class paths and canonical methods.
- Keep temporary adapter tests only while adapter status is active; add explicit expiry test markers tied to adapter deadline.
- Add static checks in CI to fail on new internal references to:
  - `*_legacy` symbols marked retired
  - `InsightMetricsUtils.export_legacy()`
  - Retired `__getattr__` shim branches
- Preserve behavior parity validation tests for menu operations and export output shape during phased cutover.

### Compatibility and Risk Strategy (Menu Ops + Test Harness)

- Use phased rollout with parity checkpoints after each phase.
- Maintain temporary adapters only for high-risk menu/test harness transitions and only with hard expiry dates.
- Require zero silent fallback growth: no new `_noop_menu_action` registrations except explicit transitional exceptions documented in this spec.
- Keep class-based architecture intact by assigning canonical ownership to existing/target classes in `src` modules (no new generic utility sink).
- Document rollback criteria per phase based on menu operation parity failures or test harness regressions.

### Documentation & Changelog Deliverables

- Update `README.md` sections that mention legacy compatibility behavior to canonical module paths.
- Add changelog entries to `CHANGELOG.md` for:
  - retired wrappers/shims,
  - temporary adapters with expiry dates,
  - final adapter removals.
- Add migration notes for developers/tests covering canonical import replacements for retired facades and aliases.

### Key Entities *(include if feature involves data)*

- **Legacy Compatibility Symbol**: A wrapper/alias/facade entry point retained for historical compatibility and now targeted for decomposition.
- **Canonical Module Owner**: The explicit `src` package/submodule and class/function responsible for the behavior after shim retirement.
- **Migration Decision Record**: Per-symbol decision artifact that tracks remove/direct-import/temporary-adapter status and expiry.
- **Parity Checkpoint**: Verification point ensuring menu and export behavior remains unchanged from user perspective.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of symbols in the decomposition inventory have an explicit migration decision (remove, direct import, or temporary adapter with expiry date).
- **SC-002**: 0 internal callsites reference retired `*_legacy` functions after final migration phase.
- **SC-003**: 0 internal callsites use `InsightMetricsUtils.export_legacy()` after callsite migration completes.
- **SC-004**: 0 retired `__getattr__` shim branches are referenced by internal code after retirement.
- **SC-005**: 100% of menu operations in migration scope pass parity regression checks across pre/post migration checkpoints.
- **SC-006**: 100% of tests previously depending on alias/facade paths are migrated to canonical interfaces or explicitly tracked under temporary adapter expiry.
- **SC-007**: Documentation/changelog deliverables are published in the same release window as shim retirement changes.

## Assumptions

- Existing canonical `src` modules can own migrated behavior without introducing a new generic helper aggregation module.
- Temporary adapters are acceptable only where immediate removal would break menu/test harness stability and must carry hard expiry dates.
- External consumers may exist but internal codebase references are the required acceptance baseline for this feature.
- Class-based architecture remains the governing design pattern during decomposition.
- Behavior parity is evaluated on user-visible outcomes (menu flow, export outputs, error semantics), not on identical internal call chains.
