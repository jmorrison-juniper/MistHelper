# Feature Specification: RADIUS API Failure Test Assertion

**Feature Branch**: `fix/4798-radius-api-failure-test-assertion` (fallback route only, see decision D-1)

**Record**: `specs\numbered\0\0\1\2\3\1\4\3\4798-radius-api-failure-test-assertion`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4798, "Test failure: RADIUS API failure test has no assertion"

**Input**: Issue #4798. The fixture repair for issue #4797 selects the WLAN RADIUS test module for the required test-quality gate. The target test has no assertion. The gate reports one new finding.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assert the contained failure message (Priority: P1)

The target test calls the WLAN RADIUS timer write with a failing API call. The production code catches the error. It then prints a failure line for the operator. The target test must check that line.

**Why this priority**: The required test-quality gate rejects the candidate until the target test has an assertion. The gate blocks PR #4208, which carries the fixture repair for issue #4797.

**Independent Test**: Run the target test node. It passes with the assertion. It fails when the production print line is removed.

**Acceptance Scenarios**:

1. **Given** the production error branch prints the failure line, **When** the target test runs, **Then** the test passes.
2. **Given** the production error branch prints no failure line, **When** the target test runs, **Then** the test fails with an assertion error.
3. **Given** the assertion commit is on the branch, **When** the scoped test-quality gate runs, **Then** it prints `gate: 0 new findings vs baseline` and exits 0.

---

### User Story 2 - Keep the change to one test module (Priority: P2)

The owner states that the baseline must remain unchanged. The owner also states that no production change is necessary. The change must touch only the test module.

**Why this priority**: A wider change adds review work. It also risks changes in behavior that the issue does not cover.

**Independent Test**: List the files that the assertion commit changes. Only the test module appears.

**Acceptance Scenarios**:

1. **Given** the assertion commit, **When** git lists its changed files, **Then** only `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` appears.
2. **Given** the branch, **When** the test-quality gate reads the baseline, **Then** the baseline file content matches `main`.

### Edge Cases

- What happens when the production failure line changes its text? The target test fails. This is intended. The text is an operator contract. See `design\contracts\operator-failure-message.md`.
- What happens when the production code logs the failure but prints nothing? The target test fails. The operator reads stdout only.
- What happens when a line shift occurs above the target test and the assertion is absent? The gate reports a new finding. The baseline key includes the line number. See analysis item A-1.
- What happens when PR #4208 closes without merge? Use the fallback route in decision D-1.
- What happens when the full-suite check reports new findings in another module? Stop and report. Do not change the baseline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The target test MUST assert that stdout contains `Error applying changes: no route`.
- **FR-002**: The target test MUST read stdout through the `capsys` fixture.
- **FR-003**: The target test MUST fail when the production error branch stops printing the failure line.
- **FR-004**: The test-quality gate MUST report zero new findings for the test module on the committed branch.
- **FR-005**: The file `.github/test-quality-baseline.json` MUST keep the content that `main` holds.
- **FR-006**: This issue MUST NOT change production code or the `fake_mh` fixture.
- **FR-007**: Each new or changed line MUST carry an inline `# WHY:` comment and stay within 120 columns.
- **FR-008**: Each applicable local gate MUST pass. Each gate that does not apply MUST state its reason.
- **FR-009**: The fix MUST reach `main` through one open pull request. No second open pull request may change the test module.
- **FR-010**: Each code claim in the record MUST cite a remote path, ref, blob SHA, and line, or list the claim as unverified.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The change edits one assertion. It sends no REST request and opens no WebSocket transport. The target test replaces the mistapi call `updateSiteWlan` with a double. The production call uses the mistapi method at `src/foundation/support/refactors/wlanradius_timer_manager.py` line 742 (research RC-10). The Mist API operation is PUT `/api/v1/sites/{site_id}/wlans/{wlan_id}` (`documentation\api\INDEX.md` line 1928, operation `updateSiteWlan`).

### Key Entities *(include if feature involves data)*

- **Target test**: The function `test_an_api_failure_is_contained` in class `TestApplyChangesDispatch`. Line 694 on `main`.
- **Test-quality finding**: One analyzer result. It has a category, a rule ID, a file path, a line number, and an explanation. These five fields form the natural key.
- **Baseline entry**: One accepted finding in `.github/test-quality-baseline.json`. See `design\data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The scoped test-quality gate prints `gate: 0 new findings vs baseline` and exits 0 on the committed branch.
- **SC-002**: The test module run reports zero failed tests and zero errors.
- **SC-003**: The target test fails in each mutation run. The target test passes after each revert.
- **SC-004**: The assertion commit lists one changed file, the test module.

## Assumptions

- A-1: GitHub `main` holds the same test module as the local checkout. The blob SHAs match (research section 4).
- A-2: The issue log came from fixture repair commit `1f4843c`. The log line 707 matches that commit (research RC-09).
- A-3: The owner direction in the issue comment stays current. The owner keeps issue #4798 open until PR #4208 merges.
- A-4: The `.venv` tools match the pins in `requirements-dev.txt`. This record does not run them. See research section 7.

## Out of Scope

- Fixture teardown for `fake_mh`. Issue #4797 owns that change.
- Any write, prune, or rewrite of `.github/test-quality-baseline.json`.
- The config key `weak_no_assertions`. See analysis item A-6.
- Production code in `src/foundation/support/refactors/wlanradius_timer_manager.py`.
- The mistapi version statements. See analysis item A-7.
- The merge of PR #4208 and its draft state. The owner decides these steps.

## Clarifications

### Session 2026-11-26

- Q: Should this issue open a new pull request? A: No. PR #4208 already carries the assertion commit. AGENTS.md line 245 bars a second open pull request for one file.
- Q: Which assertion form fits? A: A substring check on `capsys` output. It matches `test_a_failed_write_is_reported` (research RC-04).
- Q: Does the baseline change? A: No. The issue body requires an unchanged baseline. Repository instructions forbid a rewrite that hides a finding (research RC-33).
- Q: Does production code change? A: No. The issue body states that no production change is necessary.
