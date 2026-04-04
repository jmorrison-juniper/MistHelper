# Lint & Test Infrastructure Remediation

Problem
-------
Ruff linter warnings and errors are failing local and CI checks. The repository also has test infra/dev-dependency incompatibilities (notably hypothesis and importlib_metadata) causing test failures. MistHelper.py contains concentrated linter issues and some complex code that should be remediated in safe, reviewable chunks.

Goals
-----
1. Reduce ruff warnings/errors to a level where CI can pass with minimal config changes.
2. Phase MistHelper.py remediation into safe chunks: auto-fixable, config adjustments, and manual refactors.
3. Resolve dev-dependency compatibility and pin working dev-deps in requirements-dev.txt.
4. Add small unit tests and CI dry-run steps as verification points.

Approach
--------
Phased, low-risk-first approach:

Phase A — Auto-fix + tiny config updates (non-invasive)
- Run ruff --fix and isort on low-risk/small modules only. Commit in small batches (< 50 files per PR).
- Update ruff config (line-length) where required and add per-file ignores for third-party or legacy scripts.
- Add minimal mypy and ruff scope limits in CI so checks remain fast.

Phase B — Config adjustments (targeted)
- Add per-file/per-pattern ignores for files where auto-fixes would be noisy or risky.
- Increase line-length in ruff config to a pragmatic value (e.g., 100 or 120) for legacy modules; document this change in the repo.

Phase C — Manual refactors (safe chunks)
- Break MistHelper.py into logical sub-tasks and refactor incrementally. Start with the highest-value/lowest-risk edits (rename local variables, split long functions) and add unit tests alongside each chunk.
- Keep each PR small and focused (ideally < 50 files). Use feature branches for each chunk.

Phase D — Dev-deps and test infra
- Reproduce failing dev-dep combos locally, identify compatible versions for hypothesis and importlib_metadata, pin working versions in requirements-dev.txt, and run tests locally.
- Add a CI job that runs a dev-deps install + smoke tests (dry-run) on a matrix of Python versions used in CI.

Phase E — Verification and CI
- Add small unit tests to cover refactored code paths and to prevent regressions.
- Add CI dry-run steps to validate lint fixes before merging: a job that runs ruff in check mode and pytest in a smoke-run with minimum tests.

User Scenarios & Testing
------------------------
- Developer runs local remediation steps: runs ruff --fix on targeted files, runs pytest for smoke tests, and verifies no new failures. (Test: ruff check returns 0 on targeted files; pytest exit code 0 for smoke tests)
- CI pipeline runs lint check and smoke tests on pull requests. (Test: PR lint job passes; smoke tests pass)
- After manual refactors to MistHelper.py, unit tests assert behavior for the refactored functions.

Key Entities / Artifacts
------------------------
- MistHelper.py (primary manual-refactor target)
- requirements-dev.txt (pin dev-deps)
- .github/workflows/ci.yml (suggested CI changes)
- .ruff.toml / pyproject.toml (ruff settings)

Prioritized file list
---------------------
Files suitable for auto-fix (apply ruff --fix / isort, small commits):
- connect_mcp_example.py  # small example script
- maps_manager.py         # likely small, well-scoped module
- wsgi.py                 # small entrypoint
- scripts/* (where small utility scripts exist)
- tests/* (if any missing formatting only)

Files requiring manual refactor (split into chunks):
- MistHelper.py  # large, complex file — break into smaller tasks
- deploy/* and web_portal/*  # may require manual review; include only if touched

Assumptions
-----------
- Repo uses ruff/isort/mypy in CI; ruff config is in pyproject.toml or .ruff.toml.
- Many warnings are style or line-length related and can be addressed by config adjustments.
- Local environment can install dev-deps for testing compatibility.
- PR size constraint: keep changesets reviewable (<50 files); auto-fix batches should be limited accordingly.

Success Criteria (verifyable)
-----------------------------
- CI lint job (ruff check) passes on a representative PR after applying auto-fix + config updates.
- requirements-dev.txt pins compatible versions and local test runs succeed with pinned dev-deps.
- MistHelper.py refactors are completed in at most 3 incremental PRs, each with unit tests covering changed behavior.
- At least one small unit test is added per refactor chunk to prevent regressions.
- All changes are delivered in reviewable PRs (no PR touches >50 files unless justified and approved).

Risks & Mitigations
-------------------
- Risk: Broad auto-fixes change behavior. Mitigation: restrict auto-fix to low-risk modules; add unit tests.
- Risk: Dev-dep pinning hides future issues. Mitigation: document pinned versions and add a scheduled job to re-evaluate dev-deps periodically.

Deliverables
------------
- specs/lint-remediation/spec.md  (this file)
- specs/lint-remediation/tasks.md (actionable todo list)
- Prioritized file lists above
- Suggested CI/workflow changes described in tasks

