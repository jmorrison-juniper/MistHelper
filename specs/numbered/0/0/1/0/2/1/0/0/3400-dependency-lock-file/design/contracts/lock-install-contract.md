# Contract: Lock Install Interface

**Scope**: The commands and files that install Python packages or check the lock. The output is the exit status, the log lines, and the guard counts. No output columns apply.

## Commands

| Caller | Command | Inputs | Pass condition | Failure behavior |
|---|---|---|---|---|
| Worktree bootstrap | `uv sync --locked --extra dev` (`scripts/bootstrap_worktree.py` line 466) | `pyproject.toml`, `uv.lock` | The environment matches the lock | The bootstrap stops with the locked sync message. |
| Bootstrap uv install | `python -m pip install --user uv==0.13.9`, replacing the unpinned command at line 457, after T011 | None | uv 0.13.9 is available outside `.venv` | The bootstrap stops before the sync. |
| CI job install | `python -m pip install uv==0.13.9`, then `uv sync --locked --extra dev --no-install-project`, then the `.venv/bin` path appended to `GITHUB_PATH` | `pyproject.toml`, `uv.lock` | Later steps resolve `python` to the `.venv` interpreter | The job fails, and the aggregator job reports the failure. |
| Lock gate | `uv lock --check` | `pyproject.toml`, `uv.lock` | Exit status 0 | A nonzero exit status fails the `dependency_lock` job. |
| Export guard | `python -m pytest -s -q tests/guardrails/test_dependency_export.py` (`.github/workflows/ci.yml` line 650) | Both exports and `uv.lock` | Each export equals the lock output | The guard fails and names the regeneration command after T023. |
| Runtime export | `uv export --locked --no-hashes --no-emit-project --output-file requirements.txt` | `uv.lock` | `requirements.txt` | The export guard fails on drift. |
| Development export | `uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt` | `uv.lock` | `requirements-dev.txt` | The export guard fails on drift. |
| Root image install | `UV_PROJECT_ENVIRONMENT=/opt/misthelper-venv uv sync --locked --no-install-project` in the image build | `pyproject.toml`, `uv.lock` | The runtime venv exists | The image build fails. No image is tagged. |
| Image freeze check | `python -m pip freeze` inside the built image, compared with the runtime export | The image and `requirements.txt` | Zero differences | The workflow step fails. |
| Ops install | `uv sync --locked` in `mist-ops-platform/`, with flags that follow the ops project layout (U-D) | `mist-ops-platform/pyproject.toml`, `mist-ops-platform/uv.lock` | The ops venv exists | The container build fails. |
| Ops lock gate | `uv lock --check` in `mist-ops-platform/` | The ops declarations and the ops lock | Exit status 0 | A nonzero exit status fails the check. |

## Rules

1. Every uv command runs with uv 0.13.9 (FR-015).
2. No install command writes the lock. Only a maintainer runs `uv lock` after a declaration changes.
3. Exit status 0 means pass. Any other status means fail.
4. Each guard prints the count of files, records, or cases that it examined. A guard that cannot read its input fails (AGENTS.md, Tests section).
5. A pull request that edits an export without the lock fails the export guard until a maintainer regenerates the export.
