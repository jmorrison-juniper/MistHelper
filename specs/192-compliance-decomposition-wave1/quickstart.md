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

## Evidence Requirements

- Record each gate run in `tranche-validation.md` with command outcomes and UTC timestamp.
- Record explicit SC-005 boundary-stability evidence from guardrail suite results (not just generic gate pass/fail).

## Scope Safety Checklist

- [ ] No packet-capture decomposition changes introduced.
- [ ] No global script-wide logging/comment sweep introduced.
- [ ] No menu renumbering/routing redesign introduced.
- [ ] Destructive-boundary behavior remains unchanged.
- [ ] Wave 1 remains non-breaking by guardrail evidence.
