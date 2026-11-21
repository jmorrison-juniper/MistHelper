# Dependency group validation

## Prerequisites

Use Python 3.15.2 and the requested UV release.
Run commands from this worktree only.
Do not provide production credentials to tests.

## Consistency checks

After declaration updates, regenerate the lock through UV.
Use an exact upgrade selector for stevedore and Gunicorn.
Generate both exports with these commands:

```text
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv/bin/python -m pytest -s -q tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_dependency_export.py tests/guardrails/test_dependency_declaration_parity.py
```

Expect zero dependency defects and no skipped export validation.
Run the same selection inside the isolated container when container prerequisites permit it.

## Compatibility checks

Run the repository Ruff gate with the updated tool.
Run the documented mypy selection with the updated Paramiko stubs.
Run the existing SSH, portal, and Gunicorn control-socket tests.
Record exact commands and results in the implementation analysis.

## Container smoke

Use a session-local compose override with the project compose group.
Name every new resource `misthelper-tmp-issue4811-smoke`.
Publish no port. Mount only this worktree and isolated output storage.
Do not mount another checkout, a production data folder, or an external secret.
Confirm the container starts and responds before running checks.
Remove each resource by exact name and verify absence after testing.

## Staging smoke

Run authenticated staging checks only after authorization establishes the token source and the exact staging organization.
With absent credentials, record the authenticated staging smoke as unrun.
Do not substitute another organization's successful response.
