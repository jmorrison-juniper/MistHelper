# Dev-deps: Hypothesis / pytest compatibility triage

## Short name
1-hypothesis-compat

## Problem
When running pytest under Python 3.13, the Hypothesis plugin import path crashes at plugin load time with:

AttributeError: 'EntryPoints' object has no attribute 'get'

This appears to be caused by Hypothesis calling importlib_metadata.entry_points().get("hypothesis", []) which assumes entry_points() returns a mapping with .get(), whereas in newer stdlib importlib.metadata (and newer backports) entry_points() returns an EntryPoints object that does not implement .get(). The crash prevents pytest from running any tests when the plugin is auto-loaded.

Evidence: data/pytest_devdeps_run.txt and data/dev-deps-hypothesis-compat.txt in this repository.

## Goal
Triage the exact combinations of Python / Hypothesis / importlib-metadata / pytest that reproduce the failure, propose a minimal pinned requirements-dev.txt that avoids the incompatibility while keeping deps reasonably recent, and if pinning alone is insufficient propose a minimal workaround (patch or runtime shim) and CI changes to prevent regressions.

## Approach
1. Reproduce the failure in isolated virtualenvs across a version matrix:
   - Python: 3.11, 3.12, 3.13 (where available on CI/runners)
   - Hypothesis: 5.x (latest 5), 6.x (several recent micro versions)
   - importlib-metadata (backport): 4.x, 5.x (and absence of backport to rely on stdlib)
   - pytest: 8.x, 9.x

2. For each combination:
   - Create an isolated virtualenv
   - Install a minimal requirements-dev subset that brings in the target hypothesis/importlib-metadata/pytest versions (pin only those for test)
   - Run: pytest -q (and pytest -q -p no:hypothesis to confirm harness works)
   - Capture stdout/stderr and exit code

3. Analyse outputs to find minimal set of pins that avoid the crash. Preference order for solutions:
   A. Remove or avoid installing an incompatible importlib-metadata backport; rely on stdlib on Python >=3.8
   B. Upgrade Hypothesis to a release that uses the current importlib.metadata API correctly
   C. If (A/B) not possible, pin importlib-metadata to a compatible version
   D. As last resort, apply a minimal compatibility shim in test bootstrap or monkeypatch Hypothesis entry_points handling prior to import (document and upstream)

4. Produce:
   - Proposed requirements-dev.txt (pinned) that resolves the issue for CI and local dev
   - Minimal patch / workaround if pinning insufficient
   - CI workflow snippet to run an isolated dev-deps check job that installs requirements-dev.txt and runs a smoke pytest command with plugin auto-load (and once with -p no:hypothesis as control)

## Matrix (planned)
- Pythons: 3.11, 3.12, 3.13
- Hypothesis versions: latest 5.x, 6.0, 6.latest (two samples: earliest 6 and latest 6 recommended by maintainers)
- importlib-metadata (backport) versions: not-installed, 4.12.0, 5.2.0
- pytest versions: 8.2.x, 9.0.x

This yields a manageable matrix of ~36 combinations; prioritize combinations that match our current CI and developer environments.

## Preliminary findings (from repository evidence)
- The error shows Hypothesis calling importlib_metadata.entry_points().get(...) and failing with AttributeError on Python 3.13 where stdlib importlib.metadata returns EntryPoints without .get(). This strongly suggests either Hypothesis version(s) in use expect the older importlib-metadata API or a backport is present that changes runtime return value shape.
- Quick mitigation: run pytest with Hypothesis plugin disabled (pytest -p no:hypothesis) or set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 in CI as a temporary bypass.

## [NEEDS CLARIFICATION: 1]
Context: Which CI runners and Python versions are available to run the matrix (e.g., does CI provide 3.13 images)?
Why: Availability affects whether the spec must include building and testing Python 3.13 locally or only on certain CI providers.

## User scenarios & testing
- Developer runs `tox -e dev` or `pip install -r requirements-dev.txt` then `pytest` and the test harness starts without plugin import-time crashes.
- CI job installs requirements-dev.txt in an isolated environment and runs `pytest -q` successfully; a control run with `pytest -q -p no:hypothesis` must also succeed.

## Functional requirements (testable)
1. Reproduction steps for each matrix cell produce a captured log and pass/fail indicator.
2. The recommended requirements-dev.txt must allow `pip install -r requirements-dev.txt` to succeed and `pytest -q` to run without the plugin crash on Python versions in scope.
3. If a patch is proposed, it must include a unit/integration test demonstrating pytest runs with plugin auto-load and the patch applied.
4. CI workflow patch must run in a fresh environment and fail the pipeline if pytest crashes during plugin loading.

## Success criteria
- Matrix reproduction documented with exact combinations that reproduce the crash
- A requirements-dev.txt that, when installed, prevents the crash on supported Python versions (documentation and verification logs included)
- CI workflow snippet merged that runs the dev-deps smoke test on at least one runner with Python 3.12 (and 3.13 when available)

## Key entities
- Python interpreter versions
- Hypothesis package versions
- importlib-metadata package versions (backport)
- pytest package versions

## Assumptions
- CI can run at least Python 3.11 and 3.12; 3.13 may be available but must be confirmed. (See [NEEDS CLARIFICATION: 1])
- The repository test matrix is small enough to run in CI parallel jobs; otherwise tests can be sampled.

## Next steps
Follow the tasks in tasks.md to execute the matrix, capture results, propose pins, prepare patch if needed, and draft CI workflow update.


---

*Spec created from user request and repository evidence.*
