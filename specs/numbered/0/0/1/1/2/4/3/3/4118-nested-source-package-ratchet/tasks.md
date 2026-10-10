# Tasks: Nested Source Package Ratchet

## Ordered Tasks

- [ ] Add the baseline with all 36 current violations. Remediation issue `3824` covers export, and remediation issue `4168` covers the RMA packages.
- [ ] Add the tracked-path measurement and exact ratchet guard.
- [ ] Add failure proofs for new, increased, unknown, missing, malformed, stale, and excess cases.
- [ ] Run focused pytest, Ruff, Black, and the test-quality gate.
- [ ] Update `.github/copilot-instructions.md` after PR #4124 releases or transfers ownership.
- [ ] Commit the nonconflicting implementation and create a draft pull request.

## Acceptance Checks

- [ ] The guard reports 170 directories, 36 violations, and 243 total excess.
- [ ] The guard does not use `__init__.py` to discover directories.
- [ ] The active baseline path set matches the measured violation set.
- [ ] Every baseline entry has a positive remediation issue number.
- [ ] The instruction-file blocker is recorded in the pull request.
