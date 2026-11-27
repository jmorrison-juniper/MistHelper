# Quickstart: Early dependency check without half-removed packages

This file holds the reproduction steps, the test cases, the manual Windows check, and the verification commands for issue #4930.

## Prerequisites

- Windows 11 with PowerShell, in the repository root.
- A virtual environment built by the repository bootstrap, which runs `uv sync --locked --extra dev`.
- The branch `fix/4930-early-dependency-updater`, created from `main`.

Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

## Reproduction on main (before the change)

1. Confirm that `DISABLE_AUTO_INSTALL` is not set.

   ```powershell
   $env:DISABLE_AUTO_INSTALL
   ```

2. Install a release of numpy that differs from the pin on line 139 of `requirements.txt`. The pin is `numpy==2.5.5`. This step changes the environment, and the repair command in step 6 restores it.

   ```powershell
   python -m pip install "numpy==2.5.4"
   ```

3. Start the tool, then read the early-check records in `data\script.log`.

   ```powershell
   python MistHelper.py --version
   ```

4. Expected result on `main`: the probe imports numpy before the upgrade (`dependency_check.py` line 178). The upgrade then runs in the same process. A locked file can stop the uninstall step.
5. Confirm the RECORD state of each changed package.

   ```powershell
   python -m pip show -f numpy
   ```

6. Repair the environment. Close each process that uses the environment first, then run the repair command.

   ```powershell
   uv sync --locked --extra dev
   ```

## Expected result after the change

- A drift of five packages or fewer: each in-process change writes a snapshot record, then an upgrade record, then a result record. Each package keeps its RECORD file after the run.
- A loaded package with drift: the log holds one warning that names the repair command, and no upgrade record for that package.
- A drift of more than five packages: the log holds one error that names the repair command, and no in-process change record.
- `DISABLE_AUTO_INSTALL=true`: the log holds the disabled record, and no metadata read occurs.

The record texts are in `design/contracts/startup-messages.md`.

## Test cases

Each case belongs to one of the test files named in `tasks.md`. Each case names its requirement. Cases TC-01 to TC-11 fail on `main` for the reason that they name. TC-12 passes on `main` and after the change. TC-13 passes when the pins match `uv.lock`.

| Case | Kind | Requirement | Scenario |
| - | - | - | - |
| TC-01 | Unit | FR-001, SC-001 | A package with a version mismatch and a module in `sys.modules` receives no installer call. A warning names the repair command. |
| TC-02 | Unit | FR-002 | A fake `__import__` hook records zero calls while the presence of each requirement is read. |
| TC-03 | Unit | FR-003 | A package with no RECORD file receives no installer call, and a warning names the repair command. |
| TC-04 | Edge | FR-003 | A RECORD file that lists a missing file marks the package as broken. |
| TC-05 | Unit | FR-005, FR-006, SC-002 | Six drifted packages produce zero installer calls and one error record that names the repair command. |
| TC-06 | Boundary | FR-005 | Five drifted packages proceed to the in-process changes. |
| TC-07 | Unit | FR-004, SC-003 | A fake installer removes a RECORD file and returns a failure code. The removed file exists again after the run. |
| TC-08 | Edge | FR-004 | A snapshot capture failure skips the upgrade and writes error record M-06. |
| TC-09 | Edge | FR-004, FR-006 | A restore failure writes error record M-11, which names the snapshot path and the repair command. |
| TC-10 | Integration | FR-002, FR-004 | A real temporary folder holds a fake package with RECORD metadata. The real `importlib.metadata` reads it, and a failing fake installer leaves all files restored. |
| TC-11 | Unit | FR-007 | Each in-process change writes an info record before the change and a debug record after it, in that order. |
| TC-12 | Regression | FR-008 | `DISABLE_AUTO_INSTALL=true` returns after the disabled record, before any metadata read. |
| TC-13 | Guard | FR-009 | Each pin in `requirements.txt` equals the version of the same package in `uv.lock`. The case prints the number of pins that it checked. |

## Manual Windows check (SC-004)

1. Reproduce the drift with five or fewer packages, as in the reproduction steps.
2. Start the tool with the change in place.
3. Run `python -m pip show -f` on each package named in the drift records, and confirm that each one lists its RECORD file.
4. Record the command output in the pull request body.

This check exists because CI runs on `ubuntu-latest` (`.github/workflows/ci.yml` line 142).

## Verification commands

Run each command from the repository root. Read `MYPY_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` from `.github/workflows/ci.yml` before you run the matching command.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py
python -m pytest tests/bootstrap/test_dependency_check_venv_guard.py
python -m pytest tests/unit/config/standalone/foundation/runtime/startup/test_dependency_check.py
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src/foundation/runtime/bootstrap -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/foundation/runtime/bootstrap -q
pylint src/ --fail-under=9.5
vulture $VULTURE_PATHS --min-confidence 70
pydocstyle $PYDOCSTYLE_PATHS
interrogate $INTERROGATE_PATHS --fail-under 90
symbol-diff --base origin/main MistHelper.py
symbol-diff --base origin/main src/foundation/runtime/bootstrap/dependency_check.py
symbol-diff --base origin/main src/foundation/runtime/bootstrap/package_installer.py
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python MistHelper.py --test
```

The test quality gate uses the command in the Test quality ratchet section of `.github/copilot-instructions.md`. Run it after the local commit, with `--changed-from "origin/main"`. Its result must show `gate: 0 new findings vs baseline`.

The full-suite shards use the two `pytest-chunks` commands in the Local gates section of `.github/copilot-instructions.md`. Run both commands on Windows, because the unit shard takes about 1,200 seconds.

Not applicable to this change:

- The menu reference gate, because no menu changes.
- The dependency audit, `pip-audit -r requirements.txt`, because `requirements.txt` does not change.
- The Ops portal and Ops platform gates, because those trees do not change.

## Cleanup

This change starts no container. Do not run `podman system prune` or `podman volume prune` on the shared host. Delete the folders named `misthelper-pkg-snapshot-*` in the system temporary folder only after each restore is verified.
