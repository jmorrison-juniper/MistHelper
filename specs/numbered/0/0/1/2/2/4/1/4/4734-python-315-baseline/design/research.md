# Research: Python 3.15 Baseline

## Decision: Use the latest stable Python 3.15 release

The Python 3.15 series is stable. Python.org lists Python 3.15.2 as the current release and gives its release date as October 25, 2026.

**Rationale**: The request sets Python 3.15 as the minimum. A stable patch release supports production validation.

**Alternatives considered**: Python 3.15.0 is superseded. A release candidate is not suitable for production support.

**Source**: [Python 3.15.2 release](https://www.python.org/downloads/release/python-3152/)

## Decision: Use the official Python 3.15 container image

The Docker Hub API lists active `library/python` tags named `3.15-slim` and `3.15.2-slim`. Both report active Linux architecture images.

**Rationale**: The project already uses the official slim Python image. The new tag exists and supports the product container workflow.

**Alternatives considered**: Keep the Python 3.13 image, which conflicts with the new minimum. Build a custom image, which adds maintenance work.

**Source**: [Official Python 3.15-slim image tag](https://hub.docker.com/v2/repositories/library/python/tags/3.15-slim)

## Decision: Run the bootstrap with Python 3.15

`scripts/bootstrap_worktree.py` creates `.venv` with `venv.EnvBuilder`. The new environment uses the interpreter that launches the bootstrap. The setup command must therefore select Python 3.15 before it runs the script.

**Rationale**: The current bootstrap does not select a Python version itself. Explicit interpreter selection prevents a Python 3.13 process from creating an unsupported environment.

**Alternatives considered**: Let the host's default `python` select the environment. This can create an environment below the required minimum.

## Decision: Keep dependency files synchronized and preserve markers

The staged `requirements.txt` change includes three package updates but removes platform markers. Generate the export from the resolved lock after dependency-file ownership clears.

**Rationale**: The lock remains the source for platform-specific dependency resolution. A generated export must retain markers.

**Alternatives considered**: Copy the staged export as-is. That would lose platform-specific constraints and create drift from the lock.

## Decision: Use Microsoft C++ Build Tools for Windows source builds

The Python 3.15.2 sync reached `python-crfsuite==0.9.12`, which has no CPython 3.15 Windows wheel and needs a C++ compiler. The address parser has a heuristic fallback, but removing its package would reduce parsing accuracy.

**Rationale**: Build the native dependency and preserve the current address parser behavior.

**Alternatives considered**: Remove the optional parser package, which changes address parsing behavior. Wait for an upstream wheel, which delays Python 3.15 validation.

## Decision: Preserve worktree environments and pull request ownership

Eleven registered worktrees contain `.venv` directories. This feature preserves environments outside its worktree. Its Python 3.15.2 environment is incomplete because dependency installation stopped at the native package build.

**Rationale**: Other worktrees may support active tasks. Editing files owned by open pull requests can discard or conflict with separate changes.

**Alternatives considered**: Delete all worktree environments or edit overlapping dependency files immediately. Both actions can disrupt independent work.
