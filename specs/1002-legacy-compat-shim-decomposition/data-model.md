# Data Model: Legacy Compat Shim Decomposition

## Entity: LegacyCompatibilitySymbol
- **Description**: One row from decomposition inventory representing a wrapper/shim/alias/facade branch or fallback behavior.
- **Fields**:
  - `symbol_id` (string, required): Stable key, e.g. `MistHelper.get_csv_file_path_legacy`.
  - `scope` (enum, required): `misthelper_legacy_delegate | init_facade_branch | capture_alias | menu_fallback | site_insights_callsite | capture_lazy_facade`.
  - `file_path` (string, required): Repository-relative source file.
  - `symbol_name` (string, required): Function/method/branch name.
  - `current_role` (string, required): Existing compatibility role.
  - `canonical_owner` (string, required): Target module/class/method owner.
  - `decision` (enum, required): `remove | direct_import | temporary_adapter`.
  - `adapter_expiry` (date, nullable): Required when `decision=temporary_adapter`.
  - `removal_trigger` (string, nullable): Required when `decision=temporary_adapter`.
  - `status` (enum, required): `planned | enabled_canonical | decommissioned | retired`.

## Entity: MigrationDecisionRecord
- **Description**: Governance record for each symbol migration decision.
- **Fields**:
  - `symbol_id` (string, required, FK -> LegacyCompatibilitySymbol.symbol_id)
  - `decision_owner` (string, required)
  - `decision_date` (date, required)
  - `decision_rationale` (string, required)
  - `parity_checkpoint_id` (string, nullable, FK -> ParityCheckpoint.checkpoint_id)
  - `rollback_criteria` (string, required)
  - `notes` (string, nullable)

## Entity: ParityCheckpoint
- **Description**: Verification snapshot for phased migration.
- **Fields**:
  - `checkpoint_id` (string, required): e.g. `phase2-canonical-enable`.
  - `phase` (enum, required): `phase1 | phase2 | phase3 | phase4 | phase5`.
  - `menu_scope` (string, required): Covered menu operations and registries.
  - `export_scope` (string, required): Covered export paths in migration.
  - `result` (enum, required): `pass | fail`.
  - `failed_cases` (array[string], nullable)
  - `executed_at` (datetime, required)

## Entity: AdapterLifecycle
- **Description**: Tracks temporary adapter introduction/removal gates.
- **Fields**:
  - `adapter_id` (string, required): e.g. `capture.site.run_alias`.
  - `symbol_id` (string, required, FK -> LegacyCompatibilitySymbol.symbol_id)
  - `introduced_in_phase` (enum, required)
  - `expiry_date` (date, required)
  - `removal_gate` (string, required): Objective signal (tests green + no callsites).
  - `current_state` (enum, required): `active | expired_pending_removal | removed`.

## Entity: InternalCallsiteAudit
- **Description**: Static analysis output for prohibited references.
- **Fields**:
  - `audit_id` (string, required)
  - `run_date` (datetime, required)
  - `rule_name` (string, required): e.g. `no_export_legacy_calls`.
  - `target_pattern` (string, required)
  - `matches` (array[object], required): Each match has file, line, snippet.
  - `status` (enum, required): `pass | fail`.

## Validation Rules
- Every `LegacyCompatibilitySymbol` MUST have exactly one `MigrationDecisionRecord` (SC-001).
- `decision=temporary_adapter` requires non-null `adapter_expiry` and `removal_trigger` (FR-003).
- `decision in {remove, direct_import}` requires null `adapter_expiry`.
- `ParityCheckpoint.result` MUST be `pass` before advancing to next phase.
- `InternalCallsiteAudit` rules for retired `*_legacy`, `InsightMetricsUtils.export_legacy()`, and retired `__getattr__` branches MUST be `pass` by final phase (SC-002/SC-003/SC-004).

## State Transitions
- Symbol lifecycle:
  - `planned -> enabled_canonical -> decommissioned -> retired`
- Adapter lifecycle:
  - `active -> expired_pending_removal -> removed`
- Phase advancement:
  - Allowed only when current phase checkpoint `result=pass`.
