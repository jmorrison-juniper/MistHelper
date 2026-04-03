# Tasks: CI Quality Gates Triage

Order is dependency-aware. Each task is small and actionable.

1. reproduce/001 - Reproduce failing CI locally
   - Description: Create a local Python 3.13 virtualenv, install CI tooling unpinned, and run the matrix checks (ruff, mypy, pytest, bandit, pip-audit, diagram-lint). Capture exact errors, timings, and where failures occur.
   - Output: reproduction log, timing measurements, failing command outputs saved to artifacts/repro-local.txt

2. triage/002 - Increase timeout and add version logging (apply patch)
   - Description: Update .github/workflows/ci.yml to increase timeout-minutes to 20 and add steps to print installed tool versions after the install step.
   - Output: small patch applied to a feature branch (or patch diff in specs/), CI run with diagnostic logs.
   - Depends on: reproduce/001

3. triage/003 - Pin tool versions in CI (non-invasive)
   - Description: Change the pip install command in .github/workflows/ci.yml to install pinned minimal dev-tool versions (ruff, mypy, bandit, pip-audit, pytest). Add a retry loop (3 attempts) for pip install.
   - Output: updated workflow/patch, CI runs stabilize.
   - Depends on: triage/002

4. triage/004 - Add pip cache to workflows
   - Description: Add actions/cache@v4 or actions/cache@v3 usage for pip cache (cache pip wheels/wheels directory) to speed installs and reduce network dependency.
   - Output: caching step in workflow and reduced install times.
   - Depends on: triage/003

5. triage/005 - Create requirements-dev.txt or constraints file for CI
   - Description: Generate requirements-dev.txt with pinned tool versions used by CI. Use this file in the workflow install step to ensure deterministic installs.
   - Output: specs/ or repo file requirements-dev.txt with pinned versions; update workflow to install from it.
   - Depends on: triage/003

6. triage/006 - Run CI dry-run on GitHub (branch) and monitor
   - Description: Push branch with changes and run CI; collect 3 consecutive successful runs or log failures.
   - Output: CI run links, logs, and analysis notes.
   - Depends on: triage/004 and triage/005

7. triage/007 - Consolidate installs (optional improvement)
   - Description: If CI still slow, consolidate install steps across matrix or create a prepared job that installs tooling once and reuses it for matrix checks.
   - Output: workflow refactor or single job with multiple checks.
   - Depends on: triage/006

8. triage/008 - Add canary scheduled job for tool upgrades
   - Description: Add scheduled workflow that runs with the newest tool versions against a canary branch to detect future regressions before pin upgrades.
   - Output: scheduled job in .github/workflows/canary.yml

9. docs/009 - Document local reproduction and CI expectations
   - Description: Add README section or docs/ci.md describing how to run checks locally and the pinned tool versions used by CI.
   - Output: docs/ci.md or update README.md

10. monitor/010 - Post-deploy monitoring
    - Description: After merge, monitor runs for 72 hours (or next N PRs) and record any failures; revert or incrementally relax pins if safe.
    - Output: monitoring notes and follow-up tasks if regressions observed.


---

Each task should be created as a short-lived branch and small PR for review. Prioritize triage/002 and triage/003 to restore stability quickly.
