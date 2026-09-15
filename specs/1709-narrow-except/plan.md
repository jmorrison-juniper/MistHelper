# Implementation Plan: Narrow broad exception handlers

## Summary

Narrow the group 1 handlers in `MistHelper.py`. Keep the deliberate safety nets
that protect startup, the test harness, the TUI, and the operator menu. Add
traceback logging where the code continues after a caught exception.

## Technical Context

- **Language**: Python 3.13.
- **Primary file**: `MistHelper.py`.
- **Tests**: `pytest` with hermetic unit tests.
- **Release note**: One fragment under `changelog.d/`.

## Block Count

| Group | Count | Treatment |
| - | -: | - |
| Narrow it | 19 | Catch specific exception classes and test catch and escape behavior. |
| Keep it, and justify it | 5 | Keep broad catches with same-line reason comments. |
| Keep it, but repair it | 5 | Add traceback logging and keep fail-open behavior where required. |

## Implementation Steps

1. Add traceback logging to the seven handlers that logged nothing.
2. Add stop pass-through arms to each remaining broad safety net.
3. Narrow handlers with known exception surfaces.
4. Add hermetic tests for narrowed handlers.
5. Run the required local gates before the commit.

## Risk Controls

- Keep `_check_and_upgrade_package` fail-open. A transient package tool failure
  must not stop MistHelper startup.
- Do not edit `src\refactors\` or `src\config\`.
- Do not add suppression comments to `MistHelper.py`.
- Do not edit `CHANGELOG.md` on the feature branch.

## Validation

Run these commands from the worktree.

```powershell
rtk python -m py_compile MistHelper.py
rtk python -m ruff check .
rtk python -m black --check .
rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk python -m tools.symbol_diff --base origin/main MistHelper.py
rtk python -c "import MistHelper"
rtk python -c "import wsgi"
rtk grep -n "type: ignore\|noqa\|nosec\|pylint: disable" MistHelper.py
rtk python -m pytest tests/guardrails tests/unit/refactors -q
```
