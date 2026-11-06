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

## Local verification on 2026-11-06

The preserved implementation commit is `c80f23510a679985f9892ee59f0c181a8cdaa953`.
The isolated branch restores it as `65a857ccd4a6e8a9359ff3e885fbc1065d3cd7a7`.
The #4208 owner granted a scoped handover of `deploy/.env.example`.
The owner will preserve both the revision metadata and WAN entries during reconciliation.
The handover is recorded in [issue #4165](https://github.com/jmorrison-juniper/MistHelper/issues/4165#issuecomment-6681814996).

The initial test command found no pytest installation.
`python3 scripts/bootstrap_worktree.py` completed the locked environment setup.
PowerShell 7.6.9 was downloaded to session storage, and its published SHA-256 checksum matched.
The execution commands used that directory in `PATH`.

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/contract/packaging` | 78 passed, including all 28 local-revision execution cases |
| `.venv/bin/python -m ruff check tests/contract/packaging/test_compose_local_revision.py` | All checks passed |
| `.venv/bin/python -m black --check tests/contract/packaging/test_compose_local_revision.py` | One file unchanged |
| `.venv/bin/python -m mypy tests/contract/packaging/test_compose_local_revision.py --config-file pyproject.toml` | No issues in one source file |
| `.venv/bin/pydocstyle tests/contract/packaging/test_compose_local_revision.py` | No violations |
| `.venv/bin/python -m pytest -q tests/guardrails/test_container_policy_docs.py tests/guardrails/test_compose_naming_policy.py tests/guardrails/test_compose_database_settings.py tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_container_build_trigger.py tests/guardrails/test_spec_route_contract.py` | 108 passed, one skipped |
| `.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | One passed, four required inputs read |
| `.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | 1,236 files checked, zero new findings |
| `git diff --check` | No errors |

The changelog diff guard requires a pull request event, which explains the one skipped test.
The first guardrail run lacked PowerShell in `PATH`. The corrected run passed.
STE checks passed for the deployment guide, release note, and all seven specification files.
The initial STE command supplied a directory. The corrected command supplied each Markdown file.
No container started, and no production operation ran.
The coordinator must assign the serial slot before a rebase, push, pull request, or merge.
