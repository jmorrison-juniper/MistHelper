# Compatibility Contract: Top-5 Function Decomposition

This contract defines non-negotiable behavior invariants during refactor.

## Contract A: Menu and CLI stability

| Contract Item | Requirement |
| - | - |
| Menu IDs | Must remain unchanged for affected operations |
| Menu labels | Must remain unchanged |
| CLI invocation semantics | Must remain unchanged |
| Entry symbols in `MistHelper.py` | Must remain callable and compatible |

## Contract B: Prompt and workflow parity

| Contract Item | Requirement |
| - | - |
| Prompt sequence | Equivalent order and wording for operator-critical prompts |
| Cancellation paths | Same cancellation semantics and early returns |
| Confirmation behavior | Same safe input/confirmation semantics where applicable |

## Contract C: Output and side-effect parity

| Contract Item | Requirement |
| - | - |
| Output filenames/table names | Must remain unchanged unless explicitly versioned |
| Output schema/keys | Must remain backward compatible |
| Side effects | Equivalent API calls, capture control, checkpoint lifecycle |

## Contract D: Maintainability gates

| Contract Item | Requirement |
| - | - |
| Cyclomatic complexity | Each target entrypoint/responsibility boundary <= 10 |
| Thin-wrapper ban | Extracted modules must contain business logic, not pass-through wrappers |
| Logging/safety standards | Preserve redaction and safe-input patterns |

## Verification Matrix

| Target | Required Verification |
| - | - |
| `_early_dependency_check` | Unit tests + radon <= 10 + no install behavior regression |
| `start_org_packet_capture` | Integration parity + prompt snapshot + radon <= 10 |
| `_execute_site_capture_loop` | Loop behavior tests + interrupt tests + radon <= 10 |
| `device_events_52w` | Streaming/checkpoint tests + schema parity + radon <= 10 |
| `with_wan_overrides` | Report parity + API minimization checks + radon <= 10 |

## Final Verification Links

| Evidence | Location |
| - | - |
| Baseline complexity snapshot | `../evidence/baseline_cc_report.md` |
| Final complexity report | `../evidence/final_cc_report.md` |
| Quality-gate outputs | `../evidence/quality_gates.md` |
| Targeted parity/regression tests | `../evidence/test_results.md` |
| FR-011..FR-016 completion matrix | `../evidence/verification_bundle.md` |
