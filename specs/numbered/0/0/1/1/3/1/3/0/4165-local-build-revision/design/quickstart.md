# Validate local build revisions

Use the worktree virtual environment and PowerShell 7.
Add the PowerShell executable directory to `PATH` before the execution tests.

```sh
.venv/bin/python -m pytest -q tests/contract/packaging
.venv/bin/python -m ruff check tests/contract/packaging/test_compose_local_revision.py
.venv/bin/python -m black --check tests/contract/packaging/test_compose_local_revision.py
```

The tests must cover clean and dirty builds, revision-read failures, environment restoration, and clean-image comparisons.
They must not start a container or contact the remote repository.
The existing stale-build and build-overlay contracts must continue to pass.

For an operator build, use `scripts/compose.ps1 build`.
After container recreation, use `scripts/compose.ps1 check-revision`.
A clean current label succeeds. A dirty label reports uncommitted content and fails.
