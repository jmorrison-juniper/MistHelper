# Lint Remediation Tasks

Order matters; perform tasks in small commits and create separate branches for each major change.

1. [lint-auto-fix] Apply auto-fixes on low-risk files
   - Scope: connect_mcp_example.py, maps_manager.py, wsgi.py, scripts/*
   - Commands (local): ruff --fix <files>; isort <files>
   - Commit convention: chore(lint): auto-fix <module>

2. [lint-misthelper-chunk-1] MistHelper.py — chunk 1 (low-risk refactors)
   - Identify smallest functions / constants to extract
   - Add unit tests for extracted pieces
   - Keep PR < 50 files

3. [lint-misthelper-chunk-2] MistHelper.py — chunk 2 (next refactor)
   - Continue extraction and add tests
   - Address ruff warnings that require code changes

4. [lint-dev-deps] Resolve dev-dependency compatibility
   - Reproduce failures locally (install matrix if needed)
   - Find compatible versions for hypothesis and importlib_metadata
   - Update requirements-dev.txt and document rationale
   - Run full test suite locally

5. [lint-ci-updates] CI/workflow changes (dry-run + scope)
   - Add a lint:dry-run job to CI that runs ruff in check mode on the changed files
   - Limit mypy scope (exclude heavy modules) and document scope in workflow
   - Ensure jobs fail fast and provide actionable output

6. [lint-verify-ci] Add verification tests and CI dry-run steps
   - Add small unit tests created during refactors
   - Add a smoke pytest job in CI that runs a subset of tests to validate changes
   - Gate merging on lint + smoke jobs

