# Feature Specification: Webhook config test isolation

**Feature Branch**: `fix/4730-webhook-env-isolation` (merged by PR #4843). The follow-up uses a new branch (T-PR).

**Created**: 2026-11-26

**Status**: Verified on main. Follow-up open.

**Input**: Issue #4730: "Test failure: webhook config test depends on WEBHOOK_ENABLED". The test `test_the_factory_stores_an_empty_secret_when_the_variable_is_absent` assumed that `WEBHOOK_ENABLED` is unset. It failed when the environment set `WEBHOOK_ENABLED=false`.

## Clarifications

### Session 2026-11-26

- Q: Does the defect still need a code change? -> A: No product change is needed. PR #4843 merged the one-line repair on 2026-11-19. Remote check R-01 shows that the main blob is `bcf0ad12319281ea484e98bba65ff2d544f6b8d3`.
- Q: Why does issue #4730 remain open? -> A: PR #4843 links the issue with `Refs #4730`. The pull request has no closing keyword, so no automatic close ran. The orchestrator closes the issue (D-2).
- Q: Does the merged repair meet the constitution? -> A: Not yet. The touched test function has no inline comments. Principle VI is non-negotiable. A comment-only follow-up repairs this gap (D-3).
- Q: Does the follow-up need a changelog fragment? -> A: No. The internal-only rule in `changelog.d/README.md` applies. The changelog guard requires no fragment for each change (D-4).
- Q: Do other tests depend on the default of `WEBHOOK_ENABLED`? -> A: No. The sibling tests set the variable themselves (R-13, R-14, R-15).
- Q: Does any decision need a human? -> A: No. No decision falls in the four categories in the brief. The human count is zero.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the webhook config test in any environment (Priority: P1)

A maintainer runs the test with `WEBHOOK_ENABLED=false` set. The maintainer runs it again with the variable unset. The test passes in both states. The test sets its own precondition. It does not read the caller's value.

**Why this priority**: An ambient value makes the test fail in a maintainer's shell. The failure blocks the quality gate.

**Independent Test**: Run the single test with `WEBHOOK_ENABLED=false`. Run it again with the variable unset. Each run reports one passed test.

**Acceptance Scenarios**:

1. **Given** `WEBHOOK_ENABLED=false` and no `WEBHOOK_SECRET`, **When** the test runs, **Then** it reports one passed test.
2. **Given** `WEBHOOK_ENABLED` is unset and no `WEBHOOK_SECRET`, **When** the test runs, **Then** it reports one passed test.

---

### User Story 2 - Confirm that the merged repair changed one line (Priority: P1)

A reviewer confirms that the merged repair changed one test file by one added line. The reviewer reads the remote blob, the pull request file list, and the ancestry of the merge commit.

**Why this priority**: The issue requests no production change. A wider change can hide a regression.

**Independent Test**: Read the tree entry, the pull request file list, and the compare status of merge commit `15da34506`. Each result matches R-01, R-08, and R-09.

**Acceptance Scenarios**:

1. **Given** PR #4843, **When** the reviewer reads its file list, **Then** one file appears with `+1 -0`.
2. **Given** `main`, **When** the reviewer reads the test file blob, **Then** the blob is `bcf0ad12319281ea484e98bba65ff2d544f6b8d3`.

---

### User Story 3 - Read each code line of the touched test function (Priority: P2)

A junior engineer reads lines 229 to 240 of the test file. Each non-exempt code line has an inline comment. The comment explains the purpose of the line.

**Why this priority**: Principle VI is non-negotiable. The merged repair omits the comments.

**Independent Test**: Read lines 229 to 240 on the follow-up branch. Run the symbol gate on the file.

**Acceptance Scenarios**:

1. **Given** the follow-up branch, **When** a reviewer reads lines 229 to 240, **Then** each of the 8 code lines has an inline comment.
2. **Given** the follow-up branch, **When** the symbol gate runs, **Then** it reports `no module-level name changed`.

---

### User Story 4 - Close the issue with the correct evidence (Priority: P2)

The orchestrator closes issue #4730 after step A of the local gates passes. The closing comment names PR #4843 and merge commit `15da34506`. The `in-progress` label is removed.

**Why this priority**: The open issue shows a false state for `main`.

**Independent Test**: Read the issue state and labels with the `gh` command in quickstart Q-6.

**Acceptance Scenarios**:

1. **Given** step A passes, **When** the orchestrator closes the issue, **Then** the state is CLOSED and no `in-progress` label remains.

### Edge Cases

- A value such as `TRUE` in the environment reaches production code. The code lowers the case and compares with `true` (R-11). The test does not cover that value. The precondition removes the variable, so the test does not read it.
- A future test loads `.env` after the precondition runs. That test can set `WEBHOOK_ENABLED` again. The unit conftest does not register `WEBHOOK_ENABLED` (R-16). Verification check TC-003 detects a regression.
- A future change of the production default from `true` to `false` fails the test at line 240. Verification check TC-004 proves this failure.
- A `WEBHOOK_SECRET` value in the shell does not change the result. The test removes the name at line 233.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The test function MUST remove `WEBHOOK_ENABLED` from the environment before it calls the factory loader.
- **FR-002**: The test function MUST remove `WEBHOOK_SECRET` from the environment before it calls the factory loader.
- **FR-003**: The test function MUST pass when the environment sets `WEBHOOK_ENABLED` to `false`.
- **FR-004**: The test function MUST pass when the environment does not set `WEBHOOK_ENABLED`.
- **FR-005**: The repair MUST change no production file and no other test file.
- **FR-006**: The test function MUST keep its assertions for the default state of the receiver.
- **FR-007**: The test function MUST fail when the production default changes from `true` to `false`.
- **FR-008**: Each non-exempt code line of the touched test function MUST carry an inline comment.
- **FR-009**: The follow-up MUST change comments only. It MUST NOT change any code token.
- **FR-010**: The record MUST use the route `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation`.
- **FR-011**: Issue #4730 MUST close, and its `in-progress` label MUST be removed, after step A passes.
- **FR-012**: The follow-up commit MUST run normal commit hooks. It MUST NOT bypass hooks or override signing.
- **FR-013**: The follow-up pull request MUST add no changelog fragment and MUST state the internal-only reason in its body.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: the repair makes no Mist Cloud request. The changed test uses a recording router and the Flask test client. The test file imports no `mistapi` module (R-34).

### Key Entities *(include if feature involves data)*

- **Environment variable `WEBHOOK_ENABLED`**: A process setting. The factory loader reads it with the default `true` (R-11). The test removes it.
- **Environment variable `WEBHOOK_SECRET`**: A process secret. This record names it only. The test removes it.
- **Flask config key `WEBHOOK_ENABLED`**: A Boolean value. The factory loader writes it at `web_portal/app.py` line 132.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The test passes with `WEBHOOK_ENABLED` unset and with `WEBHOOK_ENABLED=false`. Checks: TC-001, TC-002, and remote check R-21.
- **SC-002**: The merged repair adds one line to one file. Check: R-09.
- **SC-003**: The touched test function has an inline comment on 8 of 8 non-exempt code lines. Check: TC-008.
- **SC-004**: The lint, format, compile, symbol, and test quality gates report no new finding. Checks: TC-006, TC-009, and TC-014.
- **SC-005**: Issue #4730 shows state CLOSED and no `in-progress` label. Check: TC-011.

## Assumptions

- The main tip is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` at authoring time (R-38).
- The Quality Gates run 45774119357 tests the code at `f03c6c9` (R-21).
- The verification worktree uses the bootstrap steps in `.github/copilot-instructions.md` lines 25 to 33 (R-22 and the same blob).
- Python 3.15 or newer is the runtime. The rule appears in `.github/copilot-instructions.md` lines 18 to 24.

## Out of Scope

- Any change to `_load_webhook_config`, the webhook route, or the signature check.
- Support for `X-Mist-Signature-v2` (analysis item A-6).
- Sibling test isolation issues #4728, #4731, #4797, and #4492 (analysis item A-7).
- Principle IV steps 11 and 12, the image revision check and the deploy (complexity item CT-1).
- Changes to `.github/test-quality-baseline.json` or `tests/guardrails/process_folder_baseline.json`.
