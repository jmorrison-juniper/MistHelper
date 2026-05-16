# Implementation Plan: Compliance/Decomposition Wave 1 (Safety Refactor, No Behavior Change)

**Branch**: `192-compliance-decomposition-wave1` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/192-compliance-decomposition-wave1/spec.md`

## Summary

Deliver Wave 1 as a strict non-breaking safety/compliance tranche plan focused on: (1) production-path safe input hardening, (2) routing/safety guardrail tests, and (3) targeted action-level logging envelopes in highest-risk touched functions. The work is sequenced into gated tranches with mandatory stop/go validation between tranches using repository-standard and user-requested quality gates.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: stdlib (`logging`, `typing`, `dataclasses` where needed), existing `InputUtils.safe_input`, `pytest`, `ruff`, `black`, `mypy`
**Storage**: N/A (no schema/storage changes in Wave 1)
**Testing**: `pytest` with coverage, existing `python MistHelper.py --test`, targeted guardrail tests
**Target Platform**: Windows 11 development + Linux container runtime
**Project Type**: CLI/menu-driven operational tool (monolithic entry + `src/` modules)
**Performance Goals**: No measurable latency regression; no additional API calls in unchanged paths
**Constraints**: Non-breaking behavior, explicit exclusion of packet-capture decomposition and global comment/log sweep
**Scale/Scope**: Wave 1 only, narrowly scoped to touched production prompt paths and high-risk functions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-Phase 0 | Post-Phase 1 | Notes |
| - | - | - | - |
| Five-Item Rule | PASS | PASS | No broad decomposition in Wave 1; plan keeps changes scoped. |
| Class-Based Architecture (No Wrappers) | PASS | PASS | Existing classes/functions remain primary structure; no wrapper-only additions planned. |
| Safety-First Input | PASS | PASS | Core objective is production-path migration to `InputUtils.safe_input(..., context=...)`. |
| Inline Comments (Non-Negotiable) | PASS | PASS | Applies during implementation for every touched executable line. |
| Action Logging (Non-Negotiable) | PASS | PASS | Restricted to highest-risk touched functions in scope. |
| Security Fix over Suppress | PASS | PASS | No suppression-first strategy allowed; issues resolved at source if introduced. |
| Full Deployment Pipeline | REQUIRED | REQUIRED | Applies after implementation/merge, outside plan artifact generation. |

**Constitution violations requiring justification**: None.

## Project Structure

### Documentation (this feature)

```text
specs/192-compliance-decomposition-wave1/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── wave1-compliance-contract.md
└── tasks.md                    # Generated later by /speckit.tasks
```

### Source Code (expected touch points)

```text
MistHelper.py                   # Production prompt paths, routing/classification touch points, targeted logging
src/                            # Type-check scope (`mypy src`) and potential helper/test-adjacent updates
tests/                          # Guardrail tests for routing/classification invariants
```

**Structure Decision**: Single-project structure retained. Wave 1 explicitly avoids broad architectural decomposition.

## Phase 0: Research Outcomes

Research is captured in [research.md](research.md) and resolves scope-critical unknowns:
- Production-path definition for Wave 1 prompt hardening
- High-risk touched function selection criteria
- Tranche sequencing and dependency rules
- Verification command set and gating semantics

## Phase 1: Design & Contracts

Design artifacts are captured in:
- [data-model.md](data-model.md)
- [contracts/wave1-compliance-contract.md](contracts/wave1-compliance-contract.md)
- [quickstart.md](quickstart.md)

Design output codifies:
- Guardrail entities and tranche evidence records
- Invariants for routing and safety classification
- Mandatory stop/go gate policy between tranches

## Phase 2: Wave 1 Tranche Execution Plan

### Tranche catalog (explicit dependencies)

| Tranche | Objective | Scope | Explicit Dependencies | Exit Criteria |
| - | - | - | - | - |
| T0 Baseline & Scope Lock | Freeze baseline behavior and identify exact Wave 1 production prompt paths | Inventory of touched prompt sites, baseline routing/safety assertions list | None | Baseline records created; no code changes yet |
| T1 Safe Input Hardening | Replace in-scope raw production `input()` with `InputUtils.safe_input(..., context=...)` | Only in-scope production prompt paths | T0 complete + approved scope list | No raw `input()` remains in in-scope paths; normal behavior unchanged |
| T2 Guardrail Tests | Add/adjust tests for entry routing and destructive classification invariants | `tests/` guardrail suites + minimal supporting code | T1 complete and gated | Guardrail tests pass and lock baseline routing/classification behavior |
| T3 Targeted Logging Envelopes | Add pre/post action logging in highest-risk touched functions only | Selected high-risk functions touched in T1/T2 | T2 complete and gated | Each selected action has before/after logs; no secret leakage |
| T4 Wave 1 Stabilization | Final non-breaking validation and evidence packaging | Cross-tranche verification only | T3 complete and gated | All final gates pass; Wave 1 marked complete |

### Inter-tranche verification gates (mandatory stop/go)

**Policy**: No tranche may start until the previous tranche’s gate set passes completely.

**Command Set CS1 (used by G1-G4)**:

1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py src tests`
3. `python -m black --check MistHelper.py src tests`
4. `python -m mypy src`
5. `python -m pytest --cov=src --cov=tests --cov-report=term-missing`
6. `python MistHelper.py --test`

| Gate ID | Runs After | Required Commands | Pass Condition | Failure Action |
| - | - | - | - | - |
| G1 | T1 | CS1 | All commands succeed (exit code 0) | Stop progression; fix tranche defects before continuing |
| G2 | T2 | CS1 | All commands succeed (exit code 0) | Stop progression; fix tranche defects before continuing |
| G3 | T3 | CS1 | All commands succeed (exit code 0) | Stop progression; fix tranche defects before continuing |
| G4 | T4 (final) | CS1 | All commands succeed (exit code 0) | Wave 1 not releasable until green |

### Non-breaking enforcement rules (Wave 1)

1. No menu renumbering, no routing redesign, and no destructive-boundary policy changes.
2. No packet-capture decomposition in this wave.
3. No full-script comment/logging sweep in this wave.
4. If any change risks behavior drift, defer to post-Wave-1 decomposition work.
5. Even with targeted logging scope, every AI-touched executable line in modified blocks must still meet project inline-comment and before/after action logging standards.

## Risk & Mitigation

| Risk | Impact | Mitigation |
| - | - | - |
| Hidden behavior drift while replacing prompts | High | Guardrail tests + tranche gate fail-fast policy |
| Over-broad logging changes | Medium | Restrict to named high-risk touched functions only |
| Tooling mismatch across environments | Medium | Use identical gate commands in every tranche and final pass |
| Scope creep into decomposition | High | Enforce explicit out-of-scope boundaries in contract and quickstart |

## Complexity Tracking

No constitution violations or complexity exceptions are required for Wave 1 planning.
