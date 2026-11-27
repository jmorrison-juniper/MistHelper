# Quickstart: Dash module isolation for map callback tests

This quickstart gives the exact reproduction steps and the exact verification commands for issue #4731. Run each command from the root of the slice worktree. Activate the project virtual environment before you run Python. The record plans 16 test-level checks: QS-02 (4 runs), QS-03 (4 runs), QS-04 (4 runs), QS-05 to QS-07 (3 runs), and QS-13 (1 run). The red control in QS-01 and the other gates are extra evidence.

## Prerequisites

- The slice worktree starts from remote main `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (research row R01).
- The project virtual environment contains dash (research row R27).
- The owner releases the publication hold before any command that publishes a branch (FR-023).

## Collection probe

Use this probe for QS-01, QS-02, QS-03, QS-05, QS-06, and QS-07. Edit only the `MODE` line and the `FILES` line for each run. The probe runs collection only, so no test body runs. It prints whether the dash entry survives collection.

```powershell
@'
import sys
import pytest

MODE = "loaded"  # Use "loaded" or "absent" for the dash entry before collection
FILES = ["tests/maps/test_viewer_callbacks_wave_a.py"]  # Test files to collect, in this order
MISSING = object()  # Marks an absent dash entry


class DashRecorder:
    """Record the dash entry before and after test collection."""

    def __init__(self):
        self.before = MISSING  # Entry seen when collection starts
        self.after = MISSING  # Entry seen when collection finishes

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection(self, session):
        self.before = sys.modules.get("dash", MISSING)  # Capture the entry before any test module loads

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self.after = sys.modules.get("dash", MISSING)  # Capture the entry after every test module loads


if MODE == "loaded":
    import dash  # Load the real module so the loaded case has an object to keep
else:
    sys.modules.pop("dash", None)  # Remove any entry so the absent case starts clean

recorder = DashRecorder()  # Recorder shared by the collection hooks
exit_code = pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", *FILES], plugins=[recorder])  # Collect only
print("collect exit:", exit_code)  # Report the pytest exit code
print("state before collection matches mode:", (MODE == "loaded") == (recorder.before is not MISSING))  # Check the start state
print("dash entry unchanged:", recorder.before is recorder.after)  # Check the identity of the entry
from dash import Dash  # Import Dash after collection, as a later test would
print("from dash import Dash: ok")  # Report the successful import
'@ | python -
```

## QS-01 Red control on main

Purpose: Reproduce the issue before a slice changes. Run it once for each slice file, with `MODE = "loaded"` and `FILES` set to that one file.

Expected result on main for wave A, B/C, D, and E2:

- `dash entry unchanged: False`
- An `ImportError` that names `Dash` after the line `from dash import Dash`

Record each red-control result in the pull request body (FR-028). This check is not counted in the 16 planned checks.

## QS-02 Loaded-state probe for each slice (4 runs)

Set `MODE = "loaded"` and `FILES` to one slice file. Expected result after the slice change:

- `collect exit: 0`
- `state before collection matches mode: True`
- `dash entry unchanged: True`
- `from dash import Dash: ok`

Run it for wave A, wave B/C, wave D, and wave E2 (SC-001).

## QS-03 Absent-state probe for each slice (4 runs)

Set `MODE = "absent"` and `FILES` to one slice file. Expected result after the slice change:

- `collect exit: 0`
- `state before collection matches mode: True`
- `dash entry unchanged: True`
- `from dash import Dash: ok`

Run it for each slice file (SC-002).

## QS-04 Test run for each slice (4 runs)

```powershell
python -m pytest tests/maps/test_viewer_callbacks_wave_a.py
python -m pytest tests/maps/test_viewer_callbacks_wave_b_c.py
python -m pytest tests/maps/test_viewer_callbacks_wave_d.py
python -m pytest tests/maps/test_viewer_callbacks_wave_e2.py
```

Expected result: each command exits 0 and every test in the file passes.

## QS-05 Combined loaded-state probe, forward order (1 run)

Set `MODE = "loaded"` and set `FILES` to these five paths, in this order:

1. `tests/maps/test_viewer_callbacks_wave_a.py`
2. `tests/maps/test_viewer_callbacks_wave_b_c.py`
3. `tests/maps/test_viewer_callbacks_wave_d.py`
4. `tests/maps/test_viewer_callbacks_wave_e1.py`
5. `tests/maps/test_viewer_callbacks_wave_e2.py`

Expected result: `dash entry unchanged: True` and `from dash import Dash: ok` (SC-003).

## QS-06 Combined loaded-state probe, reverse order (1 run)

Use the same `MODE = "loaded"` and the same five paths in reverse order. Expected result: `dash entry unchanged: True` and `from dash import Dash: ok` (FR-020).

## QS-07 Combined absent-state probe, forward order (1 run)

Set `MODE = "absent"` and use the same five paths in forward order. Expected result: `state before collection matches mode: True` and `dash entry unchanged: True` (FR-021).

## QS-08 Lint

```powershell
python -m ruff check .
```

Expected result: `All checks passed`. This gate also rejects an unused `# noqa: E402` (rule RUF100) and a line longer than 120 characters (rule E501).

## QS-09 Format

```powershell
python -m black --check .
```

Expected result: `No file needs a change`.

## QS-10 Compile

```powershell
python -m py_compile MistHelper.py
```

Expected result: no output. The project requires this check before every commit (constitution Development Workflow).

## QS-11 Test quality

Run the required input preflight first. Then run the analyzer after the local commit exists, because `--changed-from` reads committed changes.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the preflight passes, and the analyzer prints `gate: 0 new findings vs baseline`. Do not edit `.github/test-quality-baseline.json` (FR-017, FR-019).

## QS-12 Symbols

Run once for each slice file:

```powershell
symbol-diff --base origin/main tests/maps/test_viewer_callbacks_wave_a.py
```

Expected result: `symbol_diff: no module-level name changed`, and exit code 0. Replace the file name for each slice (FR-012).

## QS-13 Directory run (1 run)

```powershell
python -m pytest tests/maps
```

Expected result: exit code 0 after the final slice merges. Run it after each slice as well, because the other unfixed files still test the leak. A failure in an unfixed file does not block the slice that is under test, but you must record it.

## QS-14 Security lint

```powershell
bandit -c pyproject.toml -r tests/maps -q
```

Expected result: no finding at any severity.

## QS-15 Launcher import check (unverified item U-1)

```powershell
@'
import sys
import src.interfaces.visualization.maps.launcher  # Import the launcher package that every wave file imports
print("dash loaded after launcher import:", "dash" in sys.modules)  # Report whether the import loaded dash
'@ | python -
```

Expected result: `dash loaded after launcher import: False`. A `True` result does not change the design. The stub still stays out of the entry after each test. Record the value in the pull request body.

## QS-16 Diff scope (1 run per pull request)

```powershell
git log --name-only --format= origin/main..HEAD
```

Run the command from the slice worktree folder. Expected result: the list holds the slice test file and one changelog fragment. The list holds no baseline file and no wave E1 file (FR-016, FR-017, FR-029, SC-007, SC-008).

## Gates that do not apply to this change

- Types (mypy): The CI path variable names `src/` and root modules, not tests (research row R31).
- Docstrings (pydocstyle and interrogate), dead code (vulture), and complexity (radon): The CI path variables exclude tests (research row R31).
- Code quality (pylint) and coverage: The gates measure the `src/` package. This change edits no `src/` file (research rows R30 and R33).
- Menu reference, safe sweep, ops portal, and ops platform: No menu, operation, or portal file changes.
- Dependency audit: No requirements file changes.
- Container: No image change. The container build ignores changes under `tests/` (research row R32).
- STE: The gate grades only the instruction files and the README (research row R33). This change edits none of them.

## Reproduction steps from issue 4731

1. Import the installed dash module and keep its object.
2. In the same process, collect one affected test file with `pytest.main`. QS-01 does this.
3. Compare `sys.modules['dash']` with the kept object. QS-01 prints the result.
4. Attempt `from dash import Dash`. QS-01 prints the `ImportError`.
