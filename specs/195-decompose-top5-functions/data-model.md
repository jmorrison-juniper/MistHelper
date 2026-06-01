# Data Model: Decompose Top-5 Complex Functions

## Entity: RefactorTargetFunction

| Field | Type | Description | Validation |
| - | - | - | - |
| `name` | string | Target function name | Must be one of the 5 scoped targets |
| `source_path` | string | Current file path (`MistHelper.py`) | Non-empty |
| `source_line` | integer | Baseline declaration line | `>0` |
| `baseline_cc` | integer | Baseline complexity | `>=1` |
| `target_cc` | integer | Required max complexity | Must be `<=10` |
| `owner_module` | string | New module path under `src/` | Must start with `src/` |
| `status` | enum | Migration lifecycle | `legacy`,`dual-path`,`delegated`,`legacy-removed`,`verified` |

## Entity: CompatibilityContract

| Field | Type | Description | Validation |
| - | - | - | - |
| `menu_id` | string | Existing menu operation ID | Must remain unchanged |
| `entry_symbol` | string | Public callable used today | Must remain callable |
| `prompt_signature` | array[string] | Ordered key prompts/messages | Must match baseline snapshot |
| `output_artifacts` | array[string] | Expected files/tables/export names | Must match baseline naming/schema |
| `side_effects` | array[string] | API calls, capture starts, checkpoint writes | Must remain equivalent |

## Entity: VerificationEvidence

| Field | Type | Description | Validation |
| - | - | - | - |
| `radon_report` | object | Complexity output for `MistHelper.py` + `src/` | Must show all target entrypoints `<=10` |
| `quality_gate_results` | object | py_compile/ruff/black/test outputs | All gates green |
| `parity_test_results` | object | Targeted parity test outputs | 100% pass |
| `timestamp_utc` | datetime | Evidence generation time | ISO-8601 UTC |

## Entity: RiskControlPolicy

| Field | Type | Description | Validation |
| - | - | - | - |
| `safe_input_enforced` | bool | Uses `safe_input` for interactive/destructive flows | Must be true |
| `secrets_redacted` | bool | Logs avoid secrets/tokens/passwords | Must be true |
| `rollback_path_defined` | bool | Facade fallback path available | Must be true until final verification |
| `api_call_budget_regression` | bool | No API call increase in WAN override optimized flow | Must be true |

## Relationships

- `RefactorTargetFunction` **must satisfy** one `CompatibilityContract`.
- `RefactorTargetFunction` **must produce** one `VerificationEvidence` bundle before marked `verified`.
- `RiskControlPolicy` **applies to** all target functions.

## State Transitions

`legacy -> dual-path -> delegated -> legacy-removed -> verified`

Transition guards:

1. `legacy -> dual-path`: extracted module exists with tests.
2. `dual-path -> delegated`: parity checks pass for target.
3. `delegated -> legacy-removed`: rollback confidence accepted and tests green.
4. `legacy-removed -> verified`: all validation gates pass, including radon thresholds.
