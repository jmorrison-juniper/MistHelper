# Quickstart: Executing Wave 1 Tranches with Verification Gates

**Feature**: `specs/192-compliance-decomposition-wave1`

## Prerequisites

- Activate project virtual environment.
- Confirm workspace root is `MistHelper`.
- Keep Wave 1 scope to non-breaking safety/compliance changes only.

## Tranche Flow

1. **T0 Baseline & Scope Lock**
   - Identify exact in-scope production prompt paths.
   - Capture baseline routing/classification expectations.

2. **T1 Safe Input Hardening**
   - Migrate only in-scope production prompt reads to `InputUtils.safe_input(..., context=...)`.
   - Do not alter user-visible successful-flow behavior.

3. **T2 Guardrail Tests**
   - Add or update tests for entry routing invariants.
   - Add or update tests for destructive classification invariants.

4. **T3 Targeted Logging Envelopes**
   - Add before/after action logs in selected highest-risk touched functions only.

5. **T4 Stabilization**
   - Final pass to confirm no behavior drift and complete tranche evidence.

## Mandatory Gate Commands (run after each tranche)

```text
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src tests
python -m black --check MistHelper.py src tests
python -m mypy src
python -m pytest --cov=src --cov=tests --cov-report=term-missing
python MistHelper.py --test
```

## Recommended Gate Runner

Use the Wave 1 script runner to execute the tranche gate set in order and fail fast on the first error:

```text
powershell -ExecutionPolicy Bypass -File scripts/wave1/run_wave1_gate.ps1 -GateName G1
```

The gate runner command list must remain in strict parity with the CS1 list above.

## Stop/Go Rule

- **Go**: Proceed only when all six commands pass.
- **Stop**: Any failure blocks next tranche work until fixed and re-validated.

## Scope Boundary Verification (G4 only)

Before recording G4 as PASS, run the scope boundary verification script to confirm
Wave 1 bounded-decomposition constraints were not violated:

```text
python scripts/wave1/verify_wave1_scope_boundaries.py
```

This script checks:

1. No new packet-capture decomposition files added to `src/capture/`.
2. `menu_actions` key count has not dropped below the Wave 1 baseline.
3. All Wave-1-touched classes remain accessible in `MistHelper`.
4. `bounded-decomposition-checklist.md` evidence document is present.

The script exits 0 (PASS) or 1 (FAIL with violation details). It must pass before
appending the G4 record to `tranche-validation.md`.

Guardrail test equivalents are in `tests/guardrails/test_wave1_scope_boundaries.py`
(run automatically as part of the CS1 `pytest` step).

## Evidence Requirements

- Record each gate run in `tranche-validation.md` with command outcomes and UTC timestamp.
- Record explicit SC-005 boundary-stability evidence from guardrail suite results (not just generic gate pass/fail).
- Record scope boundary verification output in the G4 gate entry.

## Scope Safety Checklist

- [ ] No packet-capture decomposition changes introduced.
- [ ] No global script-wide logging/comment sweep introduced.
- [ ] No menu renumbering/routing redesign introduced.
- [ ] Destructive-boundary behavior remains unchanged.
- [ ] Wave 1 remains non-breaking by guardrail evidence.
- [ ] `verify_wave1_scope_boundaries.py` exits 0 (G4 only).

## Wave 1 Completion Handoff (T040)

Wave 1 is complete when all four gates have PASS records in `tranche-validation.md`.

**Status**: G1 PASS 2026-05-15 / G2 PASS 2026-05-15 / G3 PASS 2026-05-15 / G4 PASS 2026-05-18.

**Guardrail test inventory** (all must pass on `main` before Wave 2 begins):

| File | Tests | Covers |
| --- | --- | --- |
| `tests/guardrails/test_wave1_entry_routing_guardrails.py` | 2 | SC-002 routing baseline |
| `tests/guardrails/test_wave1_safety_classification_guardrails.py` | 3 | SC-005 boundary stability |
| `tests/guardrails/test_wave1_safe_input_paths.py` | 6 | SC-001 safe_input migration |
| `tests/guardrails/test_wave1_logging_envelopes.py` | 16 | SC-004 logging envelopes |
| `tests/guardrails/test_wave1_gate_runner.py` | 7 | Gate runner structure |
| `tests/guardrails/test_wave1_scope_boundaries.py` | 6 | SC-005 scope boundary audit |

**Wave 2 prerequisites**:

- All 40 guardrail tests pass on `main`.
- `baseline-compliance-metrics.md` SC-001..SC-005 evidence complete.
- New spec created for Wave 2 scope under `specs/`.
- New `bounded-decomposition-checklist.md` scoped to Wave 2 changes.
