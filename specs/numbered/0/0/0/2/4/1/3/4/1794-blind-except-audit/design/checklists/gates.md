# Checklist: gate readiness

**Purpose**: Track each local gate that the changes must pass before publication.
**Created**: 2026-11-26
**Feature**: [quickstart.md](../quickstart.md)

Each item is open until the implementer runs the command in `design/quickstart.md` and records the result in the pull request body. The record does not run the gates (repository rule 2).

## Baseline gates (T001 to T007)

- [ ] CHK001 Ruff BLE001 counts recorded with ruff 0.17.6 (Q-2, Q-3). Open: run at T001.
- [ ] CHK002 Pylint W0718 count recorded with pylint 4.1.4 (Q-7). Open: run at T001.
- [ ] CHK003 Growth guard test passes (Q-13). Open: run at T003.
- [ ] CHK004 Excluded-tree counts recorded (Q-10). Open: run at T005.

## Slice gates (T008 to T030)

- [ ] CHK005 Lint, format, and types pass for each slice (Q-6). Open: run at T-LOCAL-GATES.
- [ ] CHK006 Tests for each slice pass (Q-6, changed test files). Open: run per slice.
- [ ] CHK007 Each slice reduces its baseline counts (Q-14). Open: run per slice.
- [ ] CHK008 Each slice adds no noqa directive (Q-12). Open: run per slice.
- [ ] CHK009 Each slice rebases onto main before publication (Q-23). Open: run per slice.

## Final gate (T031)

- [ ] CHK010 Final ruff zero count (Q-5). Open: run at T031.
- [ ] CHK011 Final pyproject configuration matches `design/contracts/gate-configuration.md` (Q-15). Open: run at T031.
- [ ] CHK012 Pylint score is 9.5 or higher (Q-16). Open: run at T031 before merge.
- [ ] CHK013 Full coverage and CI shards pass on the remote run (T-REMOTE-CI). Open: run after the pull request opens.

## Publication

- [ ] CHK014 Style gate passes for each changed Markdown file (Q-21). Open: run at T-LOCAL-GATES.
- [ ] CHK015 Pull request body holds the keywords and the outcome rows (Q-19). Open: run at T-PR.
- [ ] CHK016 Held commits keep their preservation state (Q-17). Open: run at T035.
