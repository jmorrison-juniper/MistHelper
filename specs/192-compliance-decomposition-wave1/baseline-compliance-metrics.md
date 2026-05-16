# Wave 1 Baseline Compliance Metrics

## Prompt Inventory Baseline (2026-05-15)

- Raw `input(` in `MistHelper.py`: **33**
- `InputUtils.safe_input(` in `MistHelper.py`: **95**

## Wave 1 In-Scope Production Prompt Paths

This wave targets prompt paths in production code paths touched by:
- `main()` interactive menu selection
- `TroubleshootUtils.launch_interactive()` menu selection
- `SSHRunnerManager` interactive collection/confirmation paths
- `WAN2MigrationManager` selection and confirmation prompts

## Entry Routing Guardrail Matrix (baseline)

- Source: `OperationRegistry._REGISTRY`
- Core invariants:
  - option `90` category is `destructive`
  - option `29` category is `interactive_safe`
  - option `5` category is `websocket`
  - option `63` category is `resource_intensive`
  - option `158` category is `safe`

## Safety Classification Boundary Guardrails (baseline)

- `OperationRegistry.is_safe("158")` is `True`
- `OperationRegistry.is_safe("90")` is `False`
- `OperationRegistry.is_interactive_safe("29")` is `True`
- `OperationRegistry.skip_category("90")` is `destructive`

## Success Criteria Evidence Mapping

| SC | Requirement | Evidence |
| --- | --- | --- |
| SC-001 | Production-path raw prompts migrated in scope | Pending US1 updates |
| SC-002 | Routing/safety behavior preserved | Guardrail tests + G2 logs |
| SC-003 | No behavior drift in touched flows | Guardrail tests + tranche notes |
| SC-004 | Logging envelopes in selected touched functions | 5 functions with entry/exit envelopes: `TroubleshootUtils.launch_interactive`, `SSHRunnerManager._collect_missing_data`, `SSHRunnerManager._confirm_execution`, `WAN2MigrationManager._get_site_selection`, `WAN2MigrationManager._confirm_site_variable_operation`; 16 tests in `tests/guardrails/test_wave1_logging_envelopes.py` (T025/T026 all pass); `src/utils/logger_utils.py` redaction utilities; G3 PASS 2026-05-15 |
| SC-005 | Safety boundaries stable across representative IDs | `test_wave1_safety_classification_guardrails.py` results + `tranche-validation.md` boundary evidence section |
