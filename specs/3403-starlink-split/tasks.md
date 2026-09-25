# Tasks: Move the Starlink dashboard to its own repository

**Issue**: #3403 | **Plan**: [plan.md](plan.md)

## Phase 1: Prepare

- [x] T001 Claim issue #3320, and open pull request #3405 with the repair of
  the ratchet test. The ratchet then reads a green gate on `main`.

## Phase 2: The new repository

- [x] T002 Run `git-filter-repo` on a new clone with the four Starlink paths.
  The result held 12 commits.
- [x] T003 Add the README, the license, the requirements files, the pytest and
  ruff settings, the submodule pin, and the CI workflow.
- [x] T004 Create the public repository `jmorrison-juniper/starlink-dashboard`,
  and push the history. The first CI run, 36196308243, passed.
- [x] T005 Clone the repository with its submodule, and follow the README. The
  install, `pip check`, the protocol build, the import test, ruff, and pytest
  passed. Pytest gave 11 passed.

## Phase 3: The MistHelper change

- [x] T006 Delete `starlink_dashboard.py` and its test.
- [x] T007 Edit `ci.yml`, `pyproject.toml`, `quality_gate_exclusions.json`,
  `.dockerignore`, `.gitignore`, the compliance analyzer, and two tests.
- [x] T008 Add the release note under `changelog.d/`.
- [x] T009 Run every local gate: ruff, black, mypy, radon, vulture,
  pydocstyle, interrogate, bandit, the STE lint, the changed tests, and the
  test quality gate. All passed. The full ratchet checked 880 files and gave
  `gate: 0 new findings vs baseline`.
- [x] T010 Rebase onto `main` after pull request #3405 merges, and open pull
  request #3407.
- [x] T011 The first CI run failed three tests of the performance catalog
  guard. Remove the 2 inventory rows and the 4 hook rows of the catalog, and
  count its three summaries again. The guard and
  `tests/test_performance_monitoring.py` gave 78 passed.
- [ ] T012 Merge pull request #3407 after every check passes.

## Phase 4: Finish

- [ ] T013 Move the ignored `starlink-api-reference/` folder from the main
  checkout to a backup location. Then fast-forward the main checkout.
