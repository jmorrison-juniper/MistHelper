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
- [ ] T009 Run every local gate: ruff, black, mypy, radon, vulture,
  interrogate, the STE lint, the changed tests, and the test quality gate.
- [ ] T010 Rebase onto `main` after pull request #3405 merges. Open the pull
  request, and merge it after every check passes.

## Phase 4: Finish

- [ ] T011 Move the ignored `starlink-api-reference/` folder from the main
  checkout to a backup location. Then fast-forward the main checkout.
