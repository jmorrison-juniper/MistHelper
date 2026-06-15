# Contract: Validation Matrix for Shim Decomposition

## Scope
Covers verification requirements mapped to FR-001..FR-010 and SC-001..SC-007.

## Matrix Dimensions
- **Rows**: Requirements and success criteria.
- **Columns**: Test type, evidence artifact, pass threshold, phase gate, rollback action.

## Required Matrix Rows
- Inventory completeness (FR-001, SC-001)
- Canonical ownership assignment (FR-002)
- Decision classification + adapter expiry enforcement (FR-003)
- Legacy callsite migration (`*_legacy`) (FR-004, SC-002)
- Capture `run()` to `execute()` migration (FR-005)
- `__init__.py` `__getattr__` retirement (FR-006, SC-004)
- Menu fallback retirement (`_noop_menu_action`, `_ensure_menu_coverage`) (FR-007, SC-005)
- Test migration to canonical interfaces (FR-008, SC-006)
- Phase risk controls + rollback criteria (FR-009)
- Docs/changelog delivery (FR-010, SC-007)
- Site insights `export_legacy` elimination (SC-003)

## Acceptance Rule
A phase may close only when all rows tagged to that phase are `PASS` with evidence links.

## Evidence Format
Each row MUST include:
- `evidence_id`
- `artifact_path`
- `executed_at`
- `owner`
- `status`
- `notes`
