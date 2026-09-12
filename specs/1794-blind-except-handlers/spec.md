# Feature Specification: Blind Except Handler Audit

**Feature Branch**: `docs/1792-1796-lint-debt-specs` (specification only). The implementation branch is `refactor/1794-blind-except`.

**GitHub Issue**: [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794) — "refactor: 412 blind except Exception handlers hide the failures they catch"

**Created**: 2026-08-06

**Status**: Specification only. No code change exists yet.

**Input**: Audit every handler that catches the base `Exception` class. Separate the handler that protects the operator from the handler that hides a defect. Add the `BLE001` rule to the ruff `select` list after the last slice lands.

---

## Background

A handler that catches `Exception` catches every error. It catches the error that the author expected. It also catches a name error, a type error, and an attribute error that the author never considered. The handler then returns a default value, and the defect disappears.

Ruff reports each site under rule `BLE001`, which is named `blind-except`.

### This work is not a blanket rewrite

The project already studied this pattern once. The comment at `pyproject.toml` line 475 records the result.

```toml
# W0613 (unused-argument) and W0718 (broad-exception-caught) remain disabled
# repo-wide; narrowing them is tracked as separate #887 follow-up slices --
# ... and W0718 has 493 sites where broad `except Exception:` blocks
# are intentional in cleanup/error handlers. Each needs a per-site audit.
disable = ["C0114", "C0115", "C0116", "W0613", "W0718"]
```

That comment states two facts. The team counted 493 sites. The team judged the sites intentional in cleanup handlers and error handlers.

This specification accepts the first fact and tests the second one. A cleanup handler that runs on a shutdown path has a real reason for the broad catch. A data export handler that returns an empty list has no such reason, because a name error there produces a silent empty report.

The work therefore audits each site and records one of three outcomes. It does not rewrite every site to a narrow type.

### Why no gate reports this today

The ruff `select` list in `pyproject.toml` line 164 reads as follows.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G"]
```

`BLE001` belongs to the `BLE` family. That family sits outside the `select` list. Pylint reports the same pattern under rule `W0718`, and the project disables that rule. No gate reports the pattern today.

### Measured baseline

A maintainer measured the counts on 2026-08-06 at commit `08a75d2` with ruff 0.16.0.

```powershell
.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics
.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --statistics
```

| Command | `BLE001` count | Files |
| - | - | - |
| Default. Ruff reads each `# noqa` directive. | 412 | 122 |
| With `--ignore-noqa`. Ruff skips each directive. | 500 | 161 |
| Pylint `W0718`, recorded in `pyproject.toml` | 493 | not recorded |

Both ruff counts match the values in issue #1794 exactly.

### The true count is 500, not 412

The 88-site difference is the most important number in this specification.

Those 88 lines carry a `# noqa: BLE001` directive **and** hold a real blind handler. The directive changes nothing today, because ruff does not select `BLE001`. The directive starts to work on the day the team selects the rule. Ruff then hides 88 real results, and a team that clears 412 sites believes the work is complete.

Issue [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) removes those inert directives. That work must land before this one starts.

### The remaining gap of 7 sites

Ruff reports 500 with `--ignore-noqa`. Pylint recorded 493. The gap is 7.

The two tools read different roots. Pylint reads `MistHelper.py` and `src` only. Ruff reads the whole repository, and its `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`. Ruff therefore reports 8 sites in `starlink_dashboard.py` that pylint never reads.

The first task of this work reconciles the two counts and records the reason for each difference. A wrong baseline produces a wrong scope.

### The counts for each area, with the directives removed

| Area | Count with `--ignore-noqa` | Count by default |
| - | - | - |
| src/export | 94 | 75 |
| src/firmware | 62 | 58 |
| src/refactors | 43 | 38 |
| src/device | 34 | 28 |
| MistHelper.py | 33 | 33 |
| src/ssh | 32 | 14 |
| src/gateway | 24 | 22 |
| src/site | 18 | 8 |
| src/db | 17 | 17 |
| src/api | 16 | 16 |
| src/utils | 14 | 12 |
| src/websocket | 14 | 11 |
| src/ui | 12 | 12 |
| src/analytics | 10 | 6 |

The `src/ssh` area shows the largest hidden count. 18 of its 32 sites carry an inert directive today.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the failure that a handler catches (Priority: P1)

A contributor writes a defect inside a guarded block. The handler catches the error, logs it with the exception detail, and the log names the file and the error type. The contributor reads the log and finds the defect.

**Why this priority**: This story delivers the whole value. A handler that logs the error stops the silent data loss, even where the broad catch stays in place.

**Independent Test**: A reviewer injects a `NameError` into a guarded block. The reviewer runs the operation and reads a log record that names the error type and the module.

**Acceptance Scenarios**:

1. **Given** a handler that the audit keeps, **When** the block catches an error and the program continues, **Then** the code logs the error with the exception detail.
2. **Given** a handler that the audit keeps, **When** a reader opens the source, **Then** a comment states why the broad catch is correct at that site.
3. **Given** a handler that the audit narrows, **When** an unexpected error reaches the block, **Then** the error propagates instead of returning a default value.
4. **Given** a handler that the audit deletes, **When** a reviewer reads the block, **Then** the reviewer confirms that no exception can reach it.

---

### User Story 2 - Trust the baseline before the first edit (Priority: P1)

A maintainer reads one written record. The record states the true count, states the reason for every difference between the two tools, and names the roots that each tool reads.

**Why this priority**: This story shares the P1 rank. A wrong baseline produces a wrong scope, and a wrong scope leaves sites unaudited without any signal.

**Independent Test**: A reviewer reads the record and reproduces every count in it with the stated commands.

**Acceptance Scenarios**:

1. **Given** the written record, **When** a reviewer runs the stated ruff command, **Then** the output matches the recorded count.
2. **Given** the written record, **When** a reviewer runs the stated pylint command, **Then** the output matches the recorded count.
3. **Given** the written record, **When** a reviewer reads the reconciliation, **Then** the record explains each site in the difference between the two tools.
4. **Given** the written record, **When** a reviewer checks the order, **Then** the record states that issue #1792 lands first.

---

### User Story 3 - Land the audit in slices that a reviewer can read (Priority: P2)

A reviewer opens one pull request. The pull request holds one area and states the outcome for each site in that area.

**Why this priority**: This story protects the review quality. Each site needs a judgment, not a mechanical edit, so a large pull request receives no real review.

**Independent Test**: A reviewer counts the sites in any slice pull request. The count stays at or below 40.

**Acceptance Scenarios**:

1. **Given** any slice pull request, **When** a reviewer counts the audited sites, **Then** the count stays at or below 40.
2. **Given** any slice pull request, **When** a reviewer reads the body, **Then** the body records the outcome for each site.
3. **Given** any slice pull request, **When** CI runs the gate set, **Then** every gate stays green and the unit test suite keeps its pass count.

---

### Edge Cases

- A handler sits on a shutdown path or a cleanup path. A raised error there can leave a resource open or can hide the first error. The broad catch is correct, and the audit keeps it with a comment.
- A handler sits inside a logging filter. A log call from that block can re-enter the filter and can recurse without end. Specification `1032-bandit-severity-gate` already records this case for `src/utils/logger_utils.py`.
- A handler wraps a third-party call that documents no exception type. A narrow type would miss an error that the library adds in a later release. The audit keeps the broad catch and states the library name.
- A handler catches `Exception` and then re-raises. That site loses nothing, so the audit records it as safe with a short comment.
- A handler returns an empty list or an empty dictionary. A caller then reports zero rows and reports no error. This is the highest risk category, and the audit must narrow or log every one of these sites.
- The `starlink_dashboard.py` file holds 8 sites that pylint never reads. Those sites still need an audit, because ruff reads them.
- Issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709) asks the same question for `MistHelper.py` alone. That file holds 33 of the sites. The two efforts must not edit the same lines at the same time.
- The bandit rule `B110`, which is named `try_except_pass`, reports a near neighbor. Specification `1032-bandit-severity-gate` covered 7 of those sites and closed them.

---

## Requirements *(mandatory)*

### Reconciliation requirements

- **FR-001**: The implementer MUST record the ruff count, the ruff count with `--ignore-noqa`, and the pylint `W0718` count before any edit.
- **FR-002**: The record MUST name the root that each tool reads and MUST name the exclusion list that each tool applies.
- **FR-003**: The record MUST explain every site in the difference between the two counts. A site with no explanation blocks the first slice.
- **FR-004**: The implementer MUST NOT start any edit before issue #1792 lands. That work removes the 88 inert directives.
- **FR-005**: The scope MUST use the count with `--ignore-noqa`, not the default count.

### Audit requirements

- **FR-006**: Each site MUST receive one recorded outcome. The outcome MUST be `delete`, `narrow`, or `keep`.
- **FR-007**: A `delete` outcome MUST show that no exception can reach the block.
- **FR-008**: A `narrow` outcome MUST name the specific exception class or classes that the block expects.
- **FR-009**: A `keep` outcome MUST carry a source comment that states why the breadth is correct at that site. A bare `keep` is forbidden.
- **FR-010**: The implementer MUST select the outcome in this order. First, delete the handler. Second, narrow the exception type. Third, keep the broad catch with a stated reason.
- **FR-011**: A handler that the code continues past MUST log the exception. The log call MUST include the exception detail.
- **FR-012**: A handler MUST NOT pass in silence. A `pass` with no log needs a `keep` comment that states why silence is correct.
- **FR-013**: The implementer MUST NOT add a `# noqa: BLE001` directive to any site. A `keep` outcome uses a plain comment, not a suppression.

### Slice requirements

- **FR-014**: Each pull request MUST hold one area from the area table.
- **FR-015**: Each pull request MUST audit at most 40 sites.
- **FR-016**: An area above 40 sites MUST split into two or more pull requests by file.
- **FR-017**: The slices MUST land from the smallest area to the largest area.
- **FR-018**: Each pull request body MUST record the outcome for each audited site.

### Gate requirements

- **FR-019**: The ruff `select` list in `pyproject.toml` MUST hold `BLE001` after the last slice lands.
- **FR-020**: The pylint `disable` list in `pyproject.toml` MUST NOT hold `W0718` after the last slice lands.
- **FR-021**: The two configuration changes MUST land in the same pull request, so that no window opens in which one tool reports and the other does not.
- **FR-022**: The comment at `pyproject.toml` line 471 MUST change, because it records a count and a judgment that this work replaces.

### Quality requirements

- **FR-023**: Every quality gate MUST stay green for each slice. The unit test suite MUST keep its pass count.
- **FR-024**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md`.
- **FR-025**: Every changed Python line MUST carry an inline comment that explains why the line exists.

### Key Entities

- **Blind handler**: A `try` block whose `except` clause names the base `Exception` class or names no class at all.
- **Inert directive**: A `# noqa: BLE001` comment that hides nothing today, because the `select` list does not hold the rule.
- **Audit outcome**: The recorded decision for one site. The value is `delete`, `narrow`, or `keep`.
- **Silent handler**: A handler that catches an error, returns a default value, and writes no log record. This is the pattern that the work targets first.

---

## Outcome policy by handler shape

The table states the default outcome for each shape. A reviewer may choose a different outcome for one site. The reviewer must then record the reason in the pull request.

| Handler shape | Default outcome | Escalate when |
| - | - | - |
| The block returns an empty collection or a default value and writes no log | Narrow the type and add a log call | The caller cannot act on the error. Then keep the broad catch and add a log call with a stated reason. |
| The block re-raises after a log call | Keep with a comment | The narrow type is obvious from one line above. Then narrow the type. |
| The block runs on a shutdown path or a cleanup path | Keep with a comment that names the resource | The block can run on a normal path. Then narrow the type. |
| The block wraps a third-party call with no documented exception type | Keep with a comment that names the library | The library documents its exception types. Then narrow the type. |
| The block sits inside a logging filter, a handler, or a formatter | Keep with a comment that states the recursion risk | Never. A log call from that block can recurse without end. |
| The block holds `pass` and nothing else | Narrow the type and add a debug log | Silence is correct, such as a best-effort close. Then keep with a stated reason. |
| The block catches an error that the code above cannot raise | Delete the handler | The call chain can raise it through a deeper frame. Then narrow the type. |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A written record states the ruff count, the ruff count with `--ignore-noqa`, and the pylint count, and explains every difference between them.
- **SC-002**: `ruff check . --select BLE001 --ignore-noqa` reports zero results and exits with code 0.
- **SC-003**: The count of sites without a recorded outcome is zero.
- **SC-004**: Every site with a `keep` outcome carries a source comment that states the reason.
- **SC-005**: Every handler that the code continues past logs the exception detail.
- **SC-006**: The count of `# noqa: BLE001` directives that this work adds is zero.
- **SC-007**: No slice pull request audits more than 40 sites.
- **SC-008**: The ruff `select` list holds `BLE001` and the pylint `disable` list does not hold `W0718`.
- **SC-009**: A pull request that adds one blind handler fails the CI lint gate.
- **SC-010**: Every quality gate stays green for every slice. The unit test suite keeps its pass count and adds no new failure.
- **SC-011**: A reviewer who did not write the change reads any `keep` comment and states the reason in under one minute, without help from the author.

---

## Non-Goals

- **NG-001**: This work does not add any lint suppression. It adds no `# noqa: BLE001` directive and adds no rule to the ruff `ignore` list. Requirement FR-013 states the rule. The whole point is a repair, not a hidden result.
- **NG-002**: This work does not rewrite every site to a narrow type. The audit keeps a broad catch where the breadth is correct.
- **NG-003**: This work does not restore the pylint `W0718` disable entry under another name.
- **NG-004**: This work does not change the behavior that the test suite covers. A narrowed type must not turn a caught error into a new crash on a covered path.
- **NG-005**: This work does not remove the inert `# noqa: BLE001` directives. Issue #1792 owns that scope.
- **NG-006**: This work does not resolve issue #1709 in full. That issue covers `MistHelper.py`, which holds 33 sites.
- **NG-007**: This work does not change the ruff `extend-exclude` list. The four excluded paths keep their handlers.
- **NG-008**: This work does not add a new bandit suppression. Specification `1032-bandit-severity-gate` already closed the 7 `B110` sites.
- **NG-009**: This work does not add `BLE` rules other than `BLE001` to the `select` list.

---

## Assumptions

- Issue #1792 lands before this work starts. Without it, the gate hides 88 sites.
- The ruff version stays at 0.16.0 during this work. A version change can move the count.
- The 500 count reflects the branch tip at commit `08a75d2`. The implementer must measure the count again before each slice.
- The recorded pylint count of 493 reflects an older tree. The implementer must measure it again, because the tree changed since that comment.
- Most of the 500 sites receive a `keep` outcome. The team judged them intentional once already. The value of this work is the log call and the stated reason, not a mass rewrite.
- A reviewer can judge 40 sites in one sitting. A larger pull request receives no real review.

---

## Dependencies

- Issue [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) must land first. It removes the 88 inert directives that hide real sites.
- Issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709) covers the 33 sites in `MistHelper.py`. Land it first or fold it into the `MistHelper.py` slice.
- Issue [#887](https://github.com/jmorrison-juniper/MistHelper/issues/887) disabled `W0718` and recorded the 493-site count. This work reverses that decision.
- Specification `1032-bandit-severity-gate` closed 7 `B110` sites, which are near neighbors of this pattern.
- The Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` govern all prose in this work.
