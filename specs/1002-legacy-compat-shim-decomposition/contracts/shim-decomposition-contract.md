# Contract: Legacy Shim Decomposition Governance

## Purpose
Define enforceable migration contract for compatibility shim retirement and canonical ownership cutover.

## Contract Type
Internal architecture and migration governance contract.

## Contract Inputs
- Decomposition inventory rows from `spec.md`.
- Decision classification (`remove | direct_import | temporary_adapter`).
- Adapter expiry/removal triggers.
- Phase parity checkpoints.

## Contract Rules
1. Every inventory row MUST map to exactly one canonical owner module/class.
2. Every inventory row MUST have exactly one migration decision.
3. Temporary adapters MUST include:
   - hard expiry date,
   - removal trigger,
   - owner,
   - phase exit gate.
4. Retired symbols MUST NOT appear in internal callsite scans after designated phase.
5. Menu fallback symbols (`_noop_menu_action`, `_ensure_menu_coverage`) may exist only during transitional phases and MUST have explicit retirement checkpoints.
6. Site insights migration MUST eliminate internal `InsightMetricsUtils.export_legacy()` usage.

## Required Verification Outputs
- Decision matrix completeness report.
- Static callsite audit report.
- Phase parity checkpoint report.
- Adapter lifecycle status report.
- Docs/changelog publication checklist.

## Failure Conditions
- Missing decision for any inventory symbol.
- Temporary adapter without expiry/removal trigger.
- Prohibited symbol found in callsite audit after retirement phase.
- Parity checkpoint failure without rollback decision.
- Docs/changelog missing for completed phase changes.
