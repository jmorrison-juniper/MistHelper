# Feature Specification: Dash pytest plugin marker warning

**Feature Branch**: `chore/4826-dash-pytest-hook-warning` (planned)

**Created**: 2026-11-26

**Status**: Specified

**Input**: GitHub issue #4826, "Test compatibility: Dash pytest_addhooks uses deprecated pytest configuration". Labels: `chore` and `tests`.

## Clarifications

### Session 2026-11-26

- **Q**: Does the interim change close issue #4826? **A**: No. The owner keeps the issue open until upstream Dash migrates. The pull request uses `Refs #4826`. Source: remote check RC-57.
- **Q**: Which Dash version does the repository pin? **A**: Dash 4.5.1. The issue body says 4.5.0, which is stale. Source: remote checks RC-09 and RC-10.
- **Q**: Which upstream change counts as the fix? **A**: Upstream `dev` uses `@pytest.hookimpl(tryfirst=True)` at plugin line 104. The first Dash release that contains that line is the upgrade trigger. Source: remote checks RC-48, RC-49, and RC-52.
- **Q**: Does the upstream fix remove the `pytest11` entry point? **A**: No. Upstream `dev` keeps the entry point at `setup.py` line 54. Source: remote check RC-51.
- **Q**: May the repository suppress the warning or disable the plugin? **A**: No. The issue says do not suppress the warning. The owner observed a changed test result with `-p no:dash`. Source: issue body and remote check RC-57.
- **Q**: Does the warning block the current focused test result? **A**: The issue body says that it does not. This record runs no test, so the statement stays unverified.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the Dash warning visible (Priority: P1)

A test engineer runs the unit and integration tests in the locked environment. The Dash pytest plugin stays loaded. The PytestRemovedIn10Warning stays in the warnings summary. Each test result matches the result from before this change.

**Why this priority**: A suppressed warning hides a known upstream defect. PR #4831 showed that disabling the plugin changes a test result.

**Independent Test**: Run the unit test file named in the issue. Confirm that the warning summary appears and that the tests pass.

**Acceptance Scenarios**:

1. **Given** the locked environment, **When** the engineer runs `tests/unit/refactors/test_app_context_session_state.py`, **Then** the summary shows PytestRemovedIn10Warning and no test fails.
2. **Given** the root pytest configuration, **When** the policy check reads it, **Then** the policy check reports no violation.

---

### User Story 2 - Reject a suppression change (Priority: P1)

A reviewer receives a change that adds `-p no:dash` or a warning filter for the removed-in-10 category. The policy tests fail. Each failure names the rule that the change breaks.

**Why this priority**: The earlier attempt in PR #4831 used `-p no:dash`. Its pytest gate failed, as issue #4832 records.

**Independent Test**: Run the policy tests with synthetic settings. Each forbidden entry returns exactly one violation.

**Acceptance Scenarios**:

1. **Given** addopts that contain `-p no:dash`, **When** the policy check runs, **Then** the policy check returns one violation.
2. **Given** a filter entry `ignore::pytest.PytestRemovedIn10Warning` or `ignore::DeprecationWarning`, **When** the policy check runs, **Then** the policy check returns one violation for that entry.

---

### User Story 3 - Upgrade Dash after the upstream fix (Priority: P2)

A maintainer finds a Dash release that contains the decorator fix at plugin line 104. The maintainer changes the Dash pins in one upgrade change. The warning gate passes with the warning raised to an error.

**Why this priority**: The upgrade removes the defect at its source. It needs an upstream release, so it runs after the interim change.

**Independent Test**: Run the warning gate command from the quickstart after the pin change. Exit code 0 proves that the warning no longer occurs.

**Acceptance Scenarios**:

1. **Given** a Dash release after 4.5.1 with `pytest.hookimpl` at line 104, **When** the warning gate runs, **Then** it exits with code 0.
2. **Given** the upgrade change, **When** a reviewer reads the diff, **Then** the diff changes only the pins, the lock file, and the known-warning section.

---

### User Story 4 - Read the cause of the warning (Priority: P2)

A junior engineer sees the warning in a local run. The development setup guide names the warning, its cause, the upstream state, the forbidden shortcuts, and the upgrade trigger.

**Why this priority**: Engineers must not disable the plugin by reflex. The guide gives the reason.

**Independent Test**: Read the known-warning section. Confirm that each required term appears.

**Acceptance Scenarios**:

1. **Given** the known-warning section, **When** an engineer reads it, **Then** the section names PytestRemovedIn10Warning, issue #4826, and Dash 4.5.1.

---

### Edge Cases

- A Dash release contains the fix and also changes hook specifications. The upgrade change runs the full unit and integration suites before review.
- Another plugin emits PytestRemovedIn10Warning. The warning gate fails for a cause outside Dash. The engineer reads the module named in the warning before changing a pin.
- An engineer installs the `dash[testing]` extra. The plugin then registers more hook specifications and options. The warning gate runs again before review.
- An engineer raises pytest to version 10. The old-style marker can fail at plugin load. The exact pin `pytest==9.2.0` blocks an accidental change.
- An engineer copies the sibling filter `ignore::DeprecationWarning` into the root configuration. Policy test 3 rejects the entry.
- The preserved branch `fix/4826-dash-pytest-hooks` returns to review. Its `-p no:dash` change fails policy test 2.
- A Windows engineer copies a Linux command. The quickstart gives the Windows form and the Linux form.
- Open pull request #4888 changes `requirements-dev.txt`. The upgrade change waits for that pull request to merge, or it rebases after the merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The test run MUST keep the Dash pytest plugin loaded. The repository MUST NOT add `-p no:dash` to pytest addopts.
- **FR-002**: The repository MUST NOT add a warning filter that ignores PytestRemovedIn10Warning or a base category of that warning.
- **FR-003**: The policy check MUST fail when `[tool.pytest.ini_options]` is missing from `pyproject.toml`.
- **FR-004**: The developer documentation MUST name the warning, its upstream cause, its upstream state, the forbidden shortcuts, and the upgrade trigger.
- **FR-005**: The interim change MUST NOT change `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, or `uv.lock`.
- **FR-006**: The upgrade change MUST pass the warning gate with exit code 0. The integration journey test MUST also pass.
- **FR-007**: The change MUST NOT reuse, force-push, or delete branch `fix/4826-dash-pytest-hooks`. It MUST NOT reopen or merge PR #4831.
- **FR-008**: The interim pull request body MUST contain `Refs #4826`. It MUST NOT contain `Closes #4826`.

### Key Entities *(include if feature involves data)*

Not applicable: this change stores no data. It adds one policy check class and one documentation section.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The policy test functions collect 6 cases. All 6 cases pass in the interim run.
- **SC-002**: Each synthetic rejection case returns exactly one violation. This result proves that the policy check can fail.
- **SC-003**: Before the upgrade, the unit test run prints the PytestRemovedIn10Warning summary and exits with code 0. The evidence appears in the pull request.
- **SC-004**: After the upgrade, the warning gate exits with code 0. The integration journey test passes.
- **SC-005**: The interim diff lists no change to `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, or `uv.lock`.
- **SC-006**: The changed Markdown file scores 80 or above in the STE gate.

## Assumptions

- The local checkout at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` equals remote `main`. Remote check RC-62 supports this.
- The locked environment uses Python 3.15, Dash 4.5.1, and pytest 9.2.0.
- No Dash release newer than 4.5.1 exists on 2026-11-26. Remote checks RC-53 and RC-54 support this.
- The owner observation in the issue comment is correct. This record runs no tests, so the observation stays unverified.
- A manifest owner handles dependency changes. The implementer coordinates through issue #4826 before the upgrade change.
- Test runs happen in the implementation phase. This record runs no tests, builds, or linters.

## Out of Scope

- Replacing, forking, or vendoring the Dash pytest plugin.
- Changing the pytest version or the Dash pin in the interim change.
- Changing `mist-ops-platform` or its pytest configuration.
- Changing product code under `src/` or `MistHelper.py`.
- Deleting branch `fix/4826-dash-pytest-hooks` or changing PR #4831.
- Fixing issue #4731, which covers Dash module isolation in map callback tests.
- Any Mist Cloud request or mistapi change.
