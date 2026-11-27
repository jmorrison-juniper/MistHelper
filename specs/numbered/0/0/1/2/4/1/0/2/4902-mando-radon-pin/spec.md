# Feature Specification: Quality gate failure from the mando 0.8.2 pin

**Feature Branch**: `fix/4902-mando-radon-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4902, "CI: quality-gate `test_quality_gate` failed (PR #4888)". The issue has the labels `bug`, `ci`, and `quality-gate`. The issue has no comments.

## Issue Facts

- The issue body names pull request #4888, branch `dependabot/pip/mando-0.8.2`, commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`, and workflow run `45064243269` (research R06, R07).
- The named commit is a test-merge commit. Its message reads `Merge e86098cd into 00d9a16e`. The run head is the pull request head `e86098cd` (research R01, R07).
- Pull request #4888 changes one file, `requirements-dev.txt`. It changes one line from `mando==0.7.1` to `mando==0.8.2` (research R06, R08).
- The issue names the gate `test_quality_gate`. That is the job ID. The job display name is "Test quality ratchet (gate)" (research R12).

## Reproduction and Failing Check

Run 45064243269 concluded `failure` on head `e86098cd`. Twenty-eight of thirty-three jobs failed (research R01, R04).

The failing check is the job `test_quality_gate`. Its step `Run pip install -r requirements-dev.txt` exited with code 1 (research R02, R13).

The failing rule is a pip dependency-resolution rule. The step reports that `mando==0.8.2` conflicts with `radon 6.0.1`. It reports that `radon 6.0.1` depends on `mando<0.8,>=0.6` (research R03).

No test ran. The steps `Fetch pull request base` and `Run test quality ratchet` were skipped (research R02).

Twenty-six jobs print the same resolver error. Two more jobs fail at verify steps that read upstream results (research R04, R05).

The same workflow passed on main. The latest Quality Gates run on main succeeded at commit `f03c6c9b` (research R34). The defect is limited to pull request #4888.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop the failing mando update (Priority: P1)

Dependabot proposes mando 0.8 and later updates to the pip update stream. After this change, Dependabot holds back minor and major mando updates. The quality gate stays green.

**Why this priority**: The conflicting pin blocks 26 jobs on pull request #4888. A later pull request with the same pin fails the same way.

**Independent Test**: Run `python -m pytest tests/guardrails/test_pr_title_workflow.py`. The policy tests pass on the changed files.

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins `mando==0.7.1`, **When** the pin test runs, **Then** the test passes.
2. **Given** `requirements-dev.txt` pins `mando==0.8.2`, **When** the pin test runs, **Then** the test fails and names the radon 6.0.1 limit.
3. **Given** the pip update stream has no mando ignore rule, **When** the complete-policy test runs, **Then** the test fails.

---

### User Story 2 - Read the exact failing check and rule (Priority: P1)

An operator reproduces the failure from the CI log. The operator finds the job, the step, and the rule.

**Why this priority**: The issue asks for an exact failing check and rule. The fix cannot be checked without them.

**Independent Test**: Run the first command in `design/quickstart.md`. The output contains the three conflict lines.

**Acceptance Scenarios**:

1. **Given** run 45064243269, **When** the operator reads job 137336719038 with the failed-log option, **Then** the output names `mando==0.8.2` and `radon 6.0.1`.

---

### User Story 3 - Explain the policy change to contributors (Priority: P2)

A contributor reads the release-note fragment. The contributor learns why Dependabot no longer proposes mando minor and major updates.

**Why this priority**: The policy change alters Dependabot behavior that contributors see.

**Independent Test**: Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.

**Acceptance Scenarios**:

1. **Given** the file `changelog.d/issue-4902-mando-radon-pin.md`, **When** the fragment guard runs, **Then** the guard accepts the file name.

---

## Edge Cases

- Radon publishes a release that accepts mando 0.8. The maintainer removes the ignore rule and changes the pin test in the same pull request.
- Dependabot proposes a mando 0.7.x patch release. The ignore rule does not match a patch update, so the proposal stays allowed.
- Pull request #4888 closes before the ignore rule reaches main. Dependabot might open the same update again. Task T-MERGE closes the pull request after the merge.
- A later commit removes the mando line from `requirements-dev.txt`. The pin test fails, because the test requires the pin.
- The upstream radon source cannot be fetched. The research record lists the gap under Unverified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failing check, the failing step, and the failing rule. Each name MUST carry log or line evidence.
- **FR-002**: The change MUST keep `requirements-dev.txt`, `requirements.txt`, `uv.lock`, and `pyproject.toml` unchanged. `mando` stays at 0.7.1, and `radon` stays at 6.0.1.
- **FR-003**: The pip update stream MUST ignore `mando` updates of the types `version-update:semver-minor` and `version-update:semver-major`.
- **FR-004**: The policy tests MUST fail when `requirements-dev.txt` pins `mando` at 0.8 or later.
- **FR-005**: The change MUST add one changelog fragment named `changelog.d/issue-4902-mando-radon-pin.md`.
- **FR-006**: The change MUST add this record at `specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/`.
- **FR-007**: Each local gate that applies to the changed files MUST pass before the push.
- **FR-008**: The pull request body MUST contain `Closes #4902`. Each required check MUST pass before auto-merge starts.
- **FR-009**: Pull request #4888 MUST close without a merge only after the ignore rule reaches main. The closing comment MUST contain a preservation proof.
- **FR-010**: The agent MUST NOT enable auto-merge or close a pull request before the orchestrator authorizes the action.

### Key Entities

- **Pinned requirement**: The line `mando==<version>` in `requirements-dev.txt`. Its natural key is the package name `mando`.
- **Ignore rule**: The `ignore` entry for `mando` in the pip update stream of `.github/dependabot.yml`.
- **Quality gate job**: The job `test_quality_gate` in `.github/workflows/ci.yml`. Its natural key is the job ID.
- **Pull request #4888**: The Dependabot pull request that proposes `mando` 0.8.2.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The record cites job ID 137336719038, the step `Run pip install -r requirements-dev.txt`, and log lines 561, 565, and 574 (research R02, R03).
- **SC-002**: The policy test, the pin test, the fragment guard, and the two lock guards pass locally.
- **SC-003**: Each required check passes on the new pull request head before auto-merge starts.
- **SC-004**: The diff for `requirements-dev.txt`, `requirements.txt`, `uv.lock`, and `pyproject.toml` is empty.
- **SC-005**: Pull request #4888 shows state CLOSED after the merge. Its branch still exists when the closing comment posts.

## Assumptions

- The PyPI simple index lists every radon release. Radon 6.0.1 is the newest release (research R40).
- Dependabot applies `update-types` entries in the pip update stream. The npm entry in the same file uses that syntax (research R45). The docs check is unverified (research U-2).
- The local `.venv` matches the radon 6.0.1 release metadata (research R41).
- The new pull request uses the same job IDs and check names as main (research R12, R15).

## Out of Scope

- Replacing radon or changing the radon gate. A replacement needs its own specification.
- Upgrading mando beyond 0.7.1.
- Changing the test quality gate, its scope rules, or the export process.
- Changing job IDs or required check names.
- Changing the quality gate issue automation.

## Clarifications

### Session 2026-11-26

- Q: Is a radon release available that accepts mando 0.8? A: No. Radon 6.0.1 is the newest PyPI release, and it requires `mando<0.8,>=0.6` (research R40, R41).
- Q: Should the change keep mando 0.8.2 and drop radon? A: No. The radon gate is a documented quality gate (research R30). Dropping it changes a required gate.
- Q: Should the change add a changelog fragment? A: Yes. The constitution requires one fragment for each change (research R28). The README rule for internal changes conflicts, and the constitution governs (research R29, analysis A-5).
- Q: Should the record ship in the same pull request? A: Yes. The change touches four paths, and the specifications rule applies to three or more files (research R47).
