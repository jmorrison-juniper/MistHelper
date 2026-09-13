# Wave 1 Baseline Snapshot (2026-05-15)

## Scope
- Target file: `MistHelper.py`
- Wave: `192-compliance-decomposition-wave1`

## Measurable Baseline
- Raw `input(` usage in `MistHelper.py`: **33 matches**
- `InputUtils.safe_input(` usage in `MistHelper.py`: **95 matches**

## Raw `input(` locations
- 2271, 11903, 11958, 12043, 12270, 15962, 17350, 17664, 17709, 17775, 17823, 17833, 17842, 17860, 17869, 17878, 21456, 21813, 21825, 21848, 21946, 21994, 22603, 22623, 22661, 23869, 23994, 24297, 24471, 25618, 25810, 28241, 31695

## Diagnostics Baseline
Pre-existing static analysis/type diagnostics exist in `MistHelper.py` and are out-of-scope for Wave 1 unless directly touched by this tranche.

## Gate policy for this wave
After each tranche:
1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py`
3. `python -m black --check MistHelper.py`
4. `python -m mypy src --config-file pyproject.toml`
5. `pytest --cov=src --cov-fail-under=90`
6. `python MistHelper.py --test`
