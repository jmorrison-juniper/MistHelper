# Data Model: Decompose Next 5 High-Complexity Functions

## Entity: RefactorTargetFunction

| Field | Type | Description | Validation |
| - | - | - | - |
| `name` | string | Original function name in `MistHelper.py` | Must be one of the five scoped targets |
| `source_path` | string | Source file path | Must equal `MistHelper.py` |
| `source_line` | integer | Function declaration line number | `>0` |
| `baseline_cc` | integer | Pre-refactor cyclomatic complexity | `>=1` |
| `target_cc` | integer | Required post-refactor ceiling | Must be `<=10` |
| `extracted_module` | string | New module under `src/` owning behavior | Must start with `src/` |
| `extracted_class` | string | Primary class owning migrated logic | Non-empty, semantic name |
| `status` | enum | Migration lifecycle status | `baseline`, `extracted`, `delegated`, `verified` |

## Entity: ModuleBoundaryContract

| Field | Type | Description | Validation |
| - | - | - | - |
| `entrypoint_symbol` | string | Existing callable kept in `MistHelper.py` | Must remain callable and signature-compatible |
| `delegation_target` | string | `src` class/method handling logic | Must resolve to implementation path |
| `responsibility_scope` | array[string] | Owned concerns (prompting, polling, shaping, etc.) | At least one non-overlapping responsibility |
| `forbidden_scope` | array[string] | Concerns intentionally out-of-scope for this boundary | Explicitly documented |

## Entity: ParityEvidenceRecord

| Field | Type | Description | Validation |
| - | - | - | - |
| `target_name` | string | Name of validated refactor target | Must map to `RefactorTargetFunction.name` |
| `prompt_parity` | boolean | Prompt order/text parity status | Must be true before `verified` |
| `output_parity` | boolean | Output schema/artifact parity status | Must be true before `verified` |
| `side_effect_parity` | boolean | API/behavior side-effect parity status | Must be true before `verified` |
| `quality_gates` | object | VC-003..VC-007 command outcomes | All required gates pass |
| `complexity_gates` | object | VC-001..VC-002 outcomes | Target function reports `<=10` |

## Entity: ImplementationConstraintAudit

| Field | Type | Description | Validation |
| - | - | - | - |
| `inline_comment_compliance` | boolean | Touched executable lines include intent comments | Must be true |
| `action_logging_compliance` | boolean | Before/after action logs exist in touched blocks | Must be true |
| `error_logging_compliance` | boolean | Error paths include contextual `logging.error` | Must be true |
| `safe_input_compliance` | boolean | Interactive paths preserve `safe_input` semantics | Must be true |

## Relationships

- `RefactorTargetFunction` **must satisfy** one `ModuleBoundaryContract`.
- `RefactorTargetFunction` **must produce** one `ParityEvidenceRecord` before status `verified`.
- `ImplementationConstraintAudit` **applies to** each migrated target and is required for final acceptance.

## State Transitions

`baseline -> extracted -> delegated -> verified`

Transition guards:

1. `baseline -> extracted`: extracted class/module exists with unit tests.
2. `extracted -> delegated`: entrypoint delegates through compatibility facade.
3. `delegated -> verified`: parity tests pass and VC-001..VC-007 all pass.
