# Quickstart: Validate Stale Build Protection

## Prerequisites

- Use the bootstrapped Python environment.
- Use a Git checkout with an `origin` remote.
- Do not run a live container build during this check.

## Validate the contract

Run the focused contract tests:

```powershell
python -m pytest tests/contract/packaging/test_compose_rebuild_warning.py
```

Expected result: all compose build contract tests pass.

## Check the operator commands

For a current checkout, run:

```powershell
.\scripts\compose.ps1 build
```

Expected result: the helper uses the existing published image name.

For a stale checkout that needs a local test image, run:

```powershell
.\scripts\compose.ps1 build --allow-stale
```

Expected result: the helper reports the behind count and uses `misthelper:local`.
