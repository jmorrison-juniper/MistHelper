# Quickstart: Execute serial decomposition wave 2

## 1) Preparation
1. Work from `main` with clean working state.
2. Confirm spec and plan paths:
   - `specs/193-main-decomposition-wave-2/spec.md`
   - `specs/193-main-decomposition-wave-2/plan.md`
3. Ensure test dependencies are available in the active Python environment.

## 2) Execute each decomposition phase (1..9) in exact order
For each phase:
1. Extract class/method clusters to target module paths in plan.
2. Keep `MistHelper.py` orchestration/delegator behavior stable.
3. Add/update tests for extracted scope.
4. Run validation commands:
   - `python -m py_compile MistHelper.py`
   - `python -m ruff check MistHelper.py`
   - `python -m black --check MistHelper.py`
   - `python MistHelper.py --test`
5. Run phase-specific smoke/parity checks.
6. Run import/coupling checks.
7. Record phase gate evidence and sign-off.

## 3) Hard gate rule
- If any gate fails, stop and remediate in the same phase.
- Do not start the next phase until current phase evidence is fully green.

## 4) Terminal documentation synchronization (post-phase-9)
1. Update `README.md` and `CHANGELOG.md`.
2. Update mermaid/architecture docs.
3. Synchronize GitHub wiki pages.
4. Execute completeness checklist and archive audit evidence.

## 5) Done criteria
- All 9 decomposition phases passed in order.
- No parity drift accepted.
- Documentation audit fully green.
