# Research: Compliance/Decomposition Wave 1 (Safety Refactor)

**Feature**: `specs/192-compliance-decomposition-wave1`
**Date**: 2026-05-15

## R1: What qualifies as a production prompt path in Wave 1?

**Decision**: A Wave-1 production prompt path is any prompt reachable during normal operator workflow in interactive, SSH, or container sessions and directly tied to user menu/operation progression.

**Rationale**: This aligns with FR-001 and avoids broad edits in internal/developer-only prompts.

**Alternatives considered**:
- Convert every `input()` in the repository in Wave 1 — rejected as scope expansion and higher behavior risk.
- Defer prompt hardening to a future wave — rejected because safety hardening is Wave 1 core value.

## R2: How should tranches be sequenced for minimal risk?

**Decision**: Use a five-step sequence: T0 baseline/scope lock, T1 safe input migration, T2 guardrail tests, T3 targeted logging envelopes, T4 stabilization.

**Rationale**: This order de-risks behavior changes by locking invariants before adding observability refinements.

**Alternatives considered**:
- Logging first, then input migration — rejected because logging on unstable behavior can mask regressions.
- Single large tranche — rejected due to weak rollback isolation.

## R3: Which quality gates are mandatory between tranches?

**Decision**: Mandatory inter-tranche gate set:
1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py src tests`
3. `python -m black --check MistHelper.py src tests`
4. `python -m mypy src`
5. `python -m pytest --cov=src --cov=tests --cov-report=term-missing`
6. `python MistHelper.py --test`

**Rationale**: Includes both repository-standard checks and the user-requested explicit `mypy src`, pytest coverage, and MistHelper integrated tests.

**Alternatives considered**:
- Use only one test system (`pytest` or `MistHelper --test`) — rejected because each catches different regressions.
- Skip formatting/type checks between tranches — rejected due to higher merge risk.

## R4: How to identify highest-risk touched functions for targeted logging?

**Decision**: Highest-risk touched functions are those that (a) control operation routing/safety decisions, (b) mediate prompt-driven branching, or (c) orchestrate destructive/non-destructive flow boundaries in touched code.

**Rationale**: These functions provide maximum triage value per added log line while staying inside Wave 1 scope.

**Alternatives considered**:
- Add logging to all touched functions — rejected as near-global sweep behavior.
- Add no new logs in Wave 1 — rejected; FR-004 requires targeted envelopes.

## R5: How to enforce non-breaking scope boundaries?

**Decision**: Add explicit contractual constraints: no menu renumbering, no routing redesign, no destructive-boundary policy changes, no packet-capture decomposition, and no global comment/log sweep.

**Rationale**: Prevents decomposition or behavior redesign from leaking into safety hardening.

**Alternatives considered**:
- Leave boundaries implicit in plan text — rejected as insufficiently enforceable for tranche reviews.
