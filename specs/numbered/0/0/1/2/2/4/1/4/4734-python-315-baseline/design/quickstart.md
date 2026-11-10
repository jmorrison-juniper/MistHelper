# Quickstart: Python 3.15 Validation

## Prerequisites

- Install UV 0.13.7 or newer.
- Use stable Python 3.15.2.
- On Windows, install Microsoft C++ Build Tools with the C++ workload to build `python-crfsuite`.
- Run these commands from a MistHelper worktree.

## Create the environment

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py --recreate
.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Verify the runtime and command

```powershell
python --version
python MistHelper.py --help
```

Expect Python 3.15.2 or newer. Expect the command to exit with status zero and display the usage information.

## Run focused checks

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py tests/unit/container/test_build_files_match.py
python -m pytest tests/unit/scripts/test_browser_driver_bootstrap.py
```

Run the Mist Ops Platform tests from `mist-ops-platform` with its documented coverage command.
