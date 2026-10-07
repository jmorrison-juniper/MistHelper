# Tasks: ordered single-site firmware phases

- Issue: #4020
- Plan: `plan.md` in this directory

Each task below is complete. The state column records the proof.

## Plan order

| ID | Task | State |
| - | - | - |
| T001 | Add `DEVICE_TYPE_GATEWAY` and `PLAN_FAMILY_ORDER` to `upgrade_service.py` | Done |
| T002 | Add the pure `_family_rank(device_type)` function | Done |
| T003 | Add `_ordered_groups(groups)` with a stable sort | Done |
| T004 | Read `_ordered_groups(groups)` inside `plan_upgrade` | Done |
| T005 | Add `TestCanonicalPlanOrder` to `test_upgrade_service_plan.py` | Done, 41 passed |
| T006 | Update `test_splits_by_device_type` to the canonical order | Done |

## Per-phase submitter

| ID | Task | State |
| - | - | - |
| T007 | Add `PLAN_PHASE_BY_DEVICE_TYPE` and `plan_phase(plan)` | Done |
| T008 | Replace `submit` with `submit_phase` in `CloudUpgradeSubmitter` | Done |
| T009 | Add `_send_phase`, which stops at the first refused row | Done |
| T010 | Make `_keep` append, so an accepted row survives a later failure | Done |
| T011 | Add `PHASE_REFUSED_REASON` | Done |
| T031 | Reject empty, unknown, and mixed-family plans before a cloud write | Done |
| T035 | Persist each accepted row before the next plan of the phase | Done |
| T036 | Check the durable stop request before every plan | Done |
| T039 | Add the narrow `append_accepted_upgrade` store operation | Done |
| T040 | Preserve every concurrent stop during accepted-row persistence | Done |
| T043 | Add the narrow `apply_stop_request` store operation | Done |
| T044 | Add the run-scoped `RunDispatchGate` with stop precedence | Done |
| T045 | Hold the gate across the stop check, the call, and the row | Done |
| T049 | Close the gap between the stop check and the gate acquisition | Done |
| T050 | Write each dispatch refusal inside the gate through a narrow mutation | Done |
| T051 | Move a run to `stopping` through a narrow state transition | Done |
| T052 | Record the lost post-check of a stopped run | Done |

## Interleaved cascade

| ID | Task | State |
| - | - | - |
| T012 | Change the `UpgradeSubmitter` protocol to `submit_phase` | Done |
| T013 | Replace `_submit` with `_submit_phase` | Done |
| T014 | Add `_enter_running`, which guards the repeated advance | Done |
| T015 | Add `_block_phase` and `PHASE_BLOCKED_NOTE` | Done |
| T016 | Rewrite `_cascade` to send inside each phase | Done |
| T017 | Call `_cascade` only from `run` | Done |
| T032 | Keep submission refusal inside the cascade and reach `_finish` | Done |

## Tests

| ID | Task | State |
| - | - | - |
| T018 | Rewrite `test_wiring_submitter.py` for the new shape | Done, 18 passed |
| T019 | Hold the red proof `calls == ["gateways"]` | Done |
| T020 | Record the deliberate replacement of the defect-asserting test | Done |
| T021 | Add `TestPhaseSubmission` to `test_upgrade_driver.py` | Done, 99 passed |
| T022 | Update the submitter doubles of the other three modules | Done |
| T033 | Prove refused later phases become terminal and keep post-check evidence | Done |
| T034 | Prove unroutable plans fail with zero cloud writes | Done |
| T037 | Prove a stop between two version groups blocks the second write | Done |
| T038 | Prove the driver uses the normal `stopped` finalization path | Done |
| T041 | Pause accepted-row persistence while the real stop path writes | Done |
| T042 | Prove memory and document stores mutate only accepted rows | Done |
| T046 | Prove the inverse stop order keeps the stop and the accepted row | Done |
| T047 | Prove a stop that wins the gate causes zero cloud calls | Done |
| T048 | Prove a dispatch that wins the gate completes before the stop | Done |
| T053 | Prove a stop inside the gate acquisition gap sends no firmware | Done |
| T054 | Prove a refusal written inside the gate survives a stop | Done |
| T055 | Prove the stopping move keeps a concurrent driver write | Done |
| T056 | Prove a stopped run records a lost post-check capture | Done |

### The replaced test

The module `tests/unit/upgrade_portal/test_wiring_submitter.py` held
`TestTheSubmitterSends::test_keeps_the_group_that_worked_when_another_group_fails`.
That test asserted the defect. It allowed one refused group and then one
accepted group, and it read the run as a success.

`test_a_refused_gateway_group_sends_no_switch_firmware` replaces it. The
docstring of the new test names the replaced test and records the answer of the
code before this change.

```json
{"calls": ["gateways", "switches"], "result": true}
```

## Artifacts

| ID | Task | State |
| - | - | - |
| T023 | Write `spec.md`, `plan.md`, and `tasks.md` | Done |
| T024 | Add `changelog.d/issue-4020-ordered-single-site-firmware-phases.md` | Done |
| T025 | Comment the four issue-body corrections on #4020 | Done |

## Gates

| ID | Task | State |
| - | - | - |
| T026 | `python -m pytest tests/unit/upgrade_portal` | Recorded in the pull request |
| T027 | `python -m pytest tests/contract/upgrade_portal` | Recorded in the pull request |
| T028 | `python -m ruff check .` | Recorded in the pull request |
| T029 | `python -m black --check .` | Recorded in the pull request |
| T030 | `python -m mypy` with the paths of `ci.yml` | Recorded in the pull request |
