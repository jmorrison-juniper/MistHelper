# Data Model: Compliance/Decomposition Wave 1

**Feature**: `specs/192-compliance-decomposition-wave1`
**Date**: 2026-05-15

## Entities

### ProductionPromptPath

Represents an in-scope user-input path that must be EOF-safe in Wave 1.

| Field | Type | Description |
| - | - | - |
| `path_id` | `str` | Stable identifier for the prompt location |
| `location` | `str` | File/function location (e.g., `MistHelper.py::<function>`) |
| `context_label` | `str` | Required context string for `InputUtils.safe_input` |
| `baseline_behavior` | `str` | Expected pre-wave behavior summary |
| `wave1_status` | `str` | `pending`/`migrated`/`verified` |

### EntryRoutingGuardrail

Captures invariant mappings from menu/input selection to operation handler.

| Field | Type | Description |
| - | - | - |
| `selection_key` | `str` | Menu or entry selection key |
| `expected_handler` | `str` | Handler/function expected to execute |
| `source_reference` | `str` | Reference test or baseline proof |
| `verification_status` | `str` | `pending`/`pass`/`fail` |

### SafetyClassificationGuardrail

Represents destructive/non-destructive classification invariants.

| Field | Type | Description |
| - | - | - |
| `operation_id` | `int` | Operation number |
| `expected_classification` | `str` | `destructive` or `non-destructive` |
| `requires_confirmation` | `bool` | Whether explicit safety flow is required |
| `verification_status` | `str` | `pending`/`pass`/`fail` |

### HighRiskTouchedFunction

Declares function-level observability requirements for Wave 1 logging.

| Field | Type | Description |
| - | - | - |
| `function_name` | `str` | Function selected for targeted logging |
| `risk_reason` | `str` | Why it is high risk (routing/safety/branch orchestration) |
| `pre_action_log_required` | `bool` | Must emit before-action log |
| `post_action_log_required` | `bool` | Must emit after-action summary log |
| `secret_exposure_check` | `str` | `required` (always true for Wave 1) |

### TrancheValidationRecord

Tracks gate evidence required before progression.

| Field | Type | Description |
| - | - | - |
| `tranche_id` | `str` | `T1`, `T2`, `T3`, `T4` |
| `gate_id` | `str` | `G1`, `G2`, `G3`, `G4` |
| `commands` | `list[str]` | Exact command list executed |
| `timestamp_utc` | `str` | ISO-8601 UTC execution timestamp |
| `result` | `str` | `pass` or `fail` |
| `blocking_defect_refs` | `list[str]` | Issue/test references when failed |

## Relationships

```text
ProductionPromptPath (1..N) -> validated by -> TrancheValidationRecord (T1+)
EntryRoutingGuardrail (1..N) -> verified by -> tests + TrancheValidationRecord (T2+)
SafetyClassificationGuardrail (1..N) -> verified by -> tests + TrancheValidationRecord (T2+)
HighRiskTouchedFunction (1..N) -> validated by -> TrancheValidationRecord (T3+)
```

## State Transitions

### ProductionPromptPath State

`pending -> migrated -> verified`

- `pending -> migrated`: raw production `input()` replaced with `InputUtils.safe_input(..., context=...)`.
- `migrated -> verified`: tranche gate and behavior checks pass.

### TrancheValidationRecord State

`scheduled -> running -> pass|fail`

- `pass`: enables next tranche.
- `fail`: blocks tranche progression until corrected and re-run.

## Validation Rules

| Entity | Rule | Failure Handling |
| - | - | - |
| ProductionPromptPath | `context_label` must be non-empty | Reject migration entry for that path |
| EntryRoutingGuardrail | `expected_handler` must map to a real callable target | Fail guardrail test |
| SafetyClassificationGuardrail | `expected_classification` must match baseline policy | Fail guardrail test |
| HighRiskTouchedFunction | Must include both pre and post log envelope expectations | Block logging completion for tranche |
| TrancheValidationRecord | All six required commands must be present and pass | Block next tranche |
