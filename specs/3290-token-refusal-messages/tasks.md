# Tasks: Token Refusal Messages

**Issue**: [MistHelper #3290](https://github.com/jmorrison-juniper/MistHelper/issues/3290)

**Inputs**: [spec.md](spec.md), [plan.md](plan.md), and [requirements.md](checklists/requirements.md).

## Setup

- [x] T001 Verify issue ownership, the authenticated account, the initial base, and every live open pull request file list.
  Reserve only the ten paths in `plan.md`.
  Claim evidence: issue comment `5936353120`.
  Existing test reservation: issue comment `5936593776`.

- [x] T002 Complete the specification, plan, and tasks under `specs/3290-token-refusal-messages/`.
  Preserve the existing app-managed branch and all shared metadata.

- [x] T003 Restore the missing worktree environment with the unchanged bootstrap and Python 3.13.13.
  Confirm the existing offline auth suite before new assertions.
  Baseline evidence: 89 auth tests passed.

## Test-First Repair

- [x] T004 [US1] [US2] [US3] Add bounded unit and route contracts in the two issue-owned `test_token_refusal_messages.py` files.
  Pin literal messages for every refusal path in JSON and HTML.
  Check guard order, privacy, provider messages, and accepted tokens with offline stand-ins.

- [x] T005 [US1] [US2] Add the three real browser scenarios in `tests/e2e/upgrade_portal/test_token_refusal_messages.py`.
  Preserve normal empty-token client validation.
  Use a native form submission for the server empty-field response.
  Keep the existing isolated harness and token-free server evidence.

- [x] T006 Record genuine red message assertions before changing `src/interfaces/portals/upgrade_portal/app/routes/auth.py`.
  Require working fixtures and actual route responses.
  Red evidence: 46 message failures and 14 passing unit/route cases.
  Real Chromium evidence: two message failures and one unchanged client-validation pass.
  Production source remained unchanged for both runs.

- [x] T007 [US1] [US2] Select two fixed safe messages at the four existing refusal returns in `auth.py`.
  Update only the obsolete message expectation and comment in `tests/unit/upgrade_portal/test_auth.py`.
  Add `changelog.d/issue-3290-token-refusal.md`.
  Preserve every unrelated source behavior.

## Verification

- [x] T008 [US1] [US2] [US3] Run the selected auth unit and route suites.
  Require green exact-message and privacy assertions.
  Measure 100 percent coverage of changed executable production lines.
  Green evidence: 149 tests passed, 88.27 percent module coverage, and six covered changed executable lines.

- [x] T009 [US1] [US2] [US3] Run the three new Chromium scenarios and the existing accepted-token journey.
  Require no skipped scenarios, no credential exposure, and verified isolated server cleanup.
  Browser evidence: 13 tests passed with no skipped cases or leaked live runs.

- [x] T010 Run configured full Ruff, Black, and Bandit checks, plus the exact CI mypy scope.
  Run the unchanged configured test-quality ratchet for the changed tests.
  Gate evidence: Black checked 2,003 files, mypy checked 663 source files, and the ratchet checked 272 test files.
  Ruff and Bandit found no issue. The ratchet found no new finding.

- [x] T011 Run the runtime dependency audit, Markdown links, and STE checks.
  Record exact results and name missing capabilities or bounded audit limitations.
  The strict hashed runtime audit checked 105 dependencies with no skipped record or known vulnerability.
  The installed audit includes 160 records and cannot audit the Git-only `misthelper-devtools` package on PyPI.
  Markdown links cover five files with no broken target.

  The configured STE heuristic threshold passes. Dictionary grading remains unavailable, with partial word-list coverage.

- [x] T012 Run read-only SpecKit analysis across the issue-owned artifacts.
  Resolve inconsistent requirements and prepare only the reserved files for the local commit.
  The analysis maps all 17 requirements to tasks and finds no functional defect.
  `plan.md` records the four literal constitution variances and the applicable authorization boundaries.

## Publication Boundary

The caller owns the final local commit and parent handoff after these tasks.
Use the required Conventional Commit message and Copilot trailer.
Report the clean prepared HEAD and exact validation results.
Queue position 13 follows issue #3310.
Do not push, create a pull request, start a workflow, or merge before explicit parent release.
