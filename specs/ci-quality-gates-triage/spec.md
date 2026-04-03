# CI Quality Gates Triage

## Problem statement

Quality Gates workflow (GitHub Actions: .github/workflows/ci.yml) has been failing across multiple recent runs. Failures are observed across different matrix checks (ruff, mypy, pytest, bandit, pip-audit, diagram-lint) and across different PRs and pushes. The failures are intermittent but recurring and are preventing merges and releases.

## Evidence

- Workflow: .github/workflows/ci.yml (Quality Gates)
- Matrix checks: ruff, mypy, pytest, bandit, pip-audit, diagram-lint
- Short job timeout (timeout-minutes: 5) and unpinned tool installs performed per-matrix run
- CI installs dev tools by running unpinned `pip install ruff mypy ...` in each matrix run

## Root-cause hypotheses (prioritized)

1) Unpinned tool upgrades cause behavioral/regression failures (High likelihood)
   - CI installs latest versions of linters/type-checkers each run; upstream releases (ruff, mypy, bandit, pip-audit) can introduce stricter checks or breaking changes.
   - Symptoms: sudden new type/mypy errors, linter rule changes, or pip-audit semantic changes.
   - Mitigation: Pin tool versions (use versions matching repo dev tooling or minimally-compatible versions) and retain a controlled upgrade path.

2) Job timeout and repeated per-matrix installs cause flakiness/timeouts (High likelihood)
   - timeout-minutes set to 5 is insufficient for installing dependencies + running checks, especially on network hiccups.
   - Installing the same tooling repeatedly across matrix variations increases job duration and probability of transient network failures.
   - Mitigation: Increase timeout, cache pip packages, or centralize install step so work not repeated unnecessarily.

3) Network transient failures when installing packages (Medium likelihood)
   - Pip installs occasionally fail due to GitHub runner network issues or PyPI problems; lack of retry logic causes immediate job failure.
   - Mitigation: Add retry logic to pip installs and add caching to reduce network dependence.

4) Pip-audit or CVE checks causing hard failures due to new vulnerability discoveries (Lower likelihood)
   - pip-audit may fail the job if a new CVE is found (unless explicitly ignored). The workflow currently ignores CVE-2026-4539 only.
   - Mitigation: Pin dependency versions and run pip-audit against a known lockfile or constraints file; add acceptable-ignore list and staged remediation.

5) Incompatible Python version/resolution on ubuntu-latest runner (Low likelihood)
   - setup-python requested 3.13; some actions or tools may not yet provide wheels for that platform leading to build/install issues.
   - Mitigation: Confirm runner support for 3.13 or use a supported minor version until ecosystem support is confirmed.

## Chosen remediation approach (phased, low-risk first)

Phase A — Non-invasive, high-impact (apply immediately)
- Pin CLI/tool versions in the workflow install step to minimal compatible versions (ruff, mypy, bandit, pip-audit, pytest). Use the versions referenced or implied by pyproject.toml dev extras as starting points.
- Increase job timeout to 20 minutes to avoid spurious timeouts during install/run.
- Add simple retry loop around pip install (3 attempts) and log installed versions (ruff --version, mypy --version, bandit --version, pip-audit --version) for triage.
- Add actions/cache for pip to reduce install time and network dependence.

Phase B — Medium risk / reliability improvements
- Consolidate repeated installs across matrix runs: either run a single setup job that prepares a virtual environment and reuses it, or change matrix to group related checks to reduce repeated installs.
- Add a requirements-dev.txt or constraints file with pinned versions for CI, and install from it.

Phase C — Longer-term
- Adopt wheel/cache artifacts or reusable runner images with preinstalled CI tooling.
- Add periodic scheduled runs to test new tool versions before upgrading pins (canary job).

## Reproduce locally (notes)

Steps to reproduce a Quality Gates run locally (approximate):

1. On a machine with Python 3.13 (match CI):
   - python -m venv .venv && .venv\Scripts\Activate
   - python -m pip install --upgrade pip
2. Install tools used in CI (unpinned):
   - pip install -r requirements.txt
   - pip install ruff mypy pytest pytest-cov bandit pip-audit
3. Run the checks that fail in CI (examples):
   - ruff check MistHelper.py tests/ && ruff format --check MistHelper.py tests/
   - mypy MistHelper.py
   - pytest tests/unit/ -v
   - bandit -r MistHelper.py -c pyproject.toml
   - pip-audit -r requirements.txt --ignore-vuln CVE-2026-4539

Notes:
- To reproduce network problems, run the install commands repeatedly or in a constrained network.
- To reproduce pip-audit findings, consider generating a constraints file with `pip freeze` from an environment matching CI.

## Assumptions

- The failures are not caused by business-logic bugs in MistHelper (tests can fail but multiple unrelated matrix checks failing or sudden linter/type errors point to CI tool changes or environment flakiness).
- The repo prefers conservative, non-invasive fixes first (pin versions, add retries, increase timeout).

## Success criteria

- CI Quality Gates pass on main for a follow-up commit (after remediation) for at least 3 consecutive runs.
- Instability rate reduced to <1 failure per 100 runs due to CI tooling (operational target).
- Tool versions used in CI are recorded and deterministic (pinned or installed from constraints file).

## Deliverables

- This spec (specs/ci-quality-gates-triage/spec.md)
- Task list (specs/ci-quality-gates-triage/tasks.md)
- Minimal patch proposal with pinned-tool changes and timeout increase (specs/ci-quality-gates-triage/patch.diff)
- Operator checklist for rollout (specs/ci-quality-gates-triage/checklists/requirements.md)


---

Spec prepared by automation: CI triage
