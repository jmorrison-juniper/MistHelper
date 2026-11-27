# Feature Specification: Blind Except Handler Audit (issue 1794)

**Feature Branch**: `docs/1794-blind-except-audit` (this record). Slice branches use `refactor/1794-<area>`.

**GitHub Issue**: [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794), "refactor: 412 blind except Exception handlers hide the failures they catch".

**Created**: 2026-11-26

**Status**: Draft. This record supersedes the legacy records under `specs/1794-blind-except*`.

**Input**: Issue #1794 asks for an audit of each handler that catches `Exception` or `BaseException`. The audit adds a log call where the code continues. It narrows or deletes a handler where the code allows, and it keeps a broad handler only with a stated reason. The final change enables the ruff `BLE001` rule.

**Evidence basis**: Every fact in this record cites a row of `design/research.md`. The verified commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the failure that a handler catches (Priority: P1)

A contributor writes a defect inside a guarded block. The handler catches the error and logs its type, the operation name, and a redacted message. The contributor reads the log and finds the defect.

**Why this priority**: The silent default value hides the defect. A log line at the failure point gives the first useful signal, even where the broad catch stays.

**Independent Test**: A reviewer injects a `NameError` into one changed guarded block. The reviewer runs the operation and reads one error log record that names the operation and the error type.

**Acceptance Scenarios**:

1. **Given** a kept handler, **When** the block catches an error and the program continues, **Then** the log record names the operation and the exception type.
2. **Given** a narrowed handler, **When** an unexpected error reaches the block, **Then** the error propagates instead of returning a default value.
3. **Given** a deleted handler, **When** a reviewer reads the block, **Then** the outcome row names the reason that no exception reaches the block.

---

### User Story 2 - Trust the measured baseline (Priority: P1)

A maintainer reads one written baseline. The baseline states the counts from the pinned tools, the root of each tool, and the reason for each difference.

**Why this priority**: The issue counts are stale. A wrong baseline gives a wrong scope, and a wrong scope leaves sites unaudited without a signal.

**Independent Test**: A reviewer runs the commands in `design/quickstart.md` and compares each output with the baseline.

**Acceptance Scenarios**:

1. **Given** the baseline, **When** a reviewer runs the pinned ruff command, **Then** the output matches the recorded count.
2. **Given** the baseline, **When** a reviewer reads the reconciliation, **Then** each difference between the tools has a reason.

---

### User Story 3 - Block growth until the final gate (Priority: P1)

A contributor adds a broad handler in a pull request before the final gate exists. The growth guard fails the pull request. The guard names the file and the increase.

**Why this priority**: The count grew from 412 to more than 500 while no gate reported it. Growth must stop while the audit runs.

**Independent Test**: A test adds a broad handler with an unused name to a fixture. The growth guard reports the increase and fails.

**Acceptance Scenarios**:

1. **Given** the growth guard, **When** a changed file gains a blind handler, **Then** the guard fails with the file name and both counts.
2. **Given** the final gate pull request, **When** ruff runs, **Then** each new broad handler without a re-raise or an `exc_info` log fails the lint gate.

---

### User Story 4 - Review each slice in one sitting (Priority: P2)

A reviewer opens one slice pull request. The pull request holds one cluster of at most 40 sites. The body lists each site and its outcome.

**Why this priority**: Each site needs a judgment. A large pull request gets no real review.

**Independent Test**: A reviewer counts the rows in the outcome table of any slice pull request. The count equals the number of audited sites, and the count stays at or below 40.

**Acceptance Scenarios**:

1. **Given** any slice pull request, **When** a reviewer counts the audited sites, **Then** the count stays at or below 40.
2. **Given** any slice pull request, **When** a reviewer reads the body, **Then** each row holds one outcome and one test name.

---

### Edge Cases

- A handler on a shutdown or cleanup path. Keep the broad catch, log it, and name the resource in the reason.
- A handler around a third-party call that documents no exception type. Keep the broad catch and name the library in the reason.
- A handler inside a logging filter or a formatter. Keep the broad catch with a recursion note. A filter must not log its own actions (RC-060).
- A handler that returns an empty collection or a default value without a log call. This is the highest risk. Narrow it or add a log call.
- A caller-supplied callback. Keep the broad catch, log the exception type, and state the callback contract in the reason.
- A handler that re-raises. Ruff does not flag it (RC-095). Record it as safe in the outcome table.
- A tuple that contains `Exception`. The growth guard flags it only when its bound name stays unused (RC-032).
- A held branch whose base changed. The address-normalization branch conflicts with PR #4503 (RC-073). Rebase it and check it again.
- A test file that moved. Use the current path from the table (RC-065, RC-067, RC-070, RC-074, RC-083).
- A string literal that contains `except Exception`. Ruff does not count it. The text count does (Unverified U-13).
- A `# pylint: disable=broad-exception-caught` on a changed site. Remove it when the site becomes narrowed or deleted.
- A narrowed type that changes which errors reach the operator. Read the caller, and test the new propagation path.

## Requirements *(mandatory)*

### Functional Requirements

Measurement and baseline

- **FR-001**: The implementer MUST measure the ruff BLE001 count with ruff 0.17.6 before the first slice. The implementer MUST record the default count and the count with `--ignore-noqa`.
- **FR-002**: The implementer MUST measure the pylint W0718 count with pylint 4.1.4 on the CI source root before the first slice.
- **FR-003**: The baseline MUST name the root and the exclusion list of each tool, taken from `pyproject.toml` and `.github/workflows/ci.yml`.
- **FR-004**: The baseline MUST explain each difference between the ruff count, the pylint count, and the text count, by path and reason.
- **FR-005**: The scope metric MUST be the ruff BLE001 count with `--ignore-noqa`. The pylint count and the text count are supporting values only.
- **FR-006**: The implementer MUST confirm that the growth guard runs in CI before the first slice.

Outcome policy

- **FR-007**: Each in-scope site MUST receive one outcome: `delete`, `narrow`, or `keep`.
- **FR-008**: The implementer MUST test the outcomes in this order: `delete`, then `narrow`, then `keep`. The first outcome that the code supports applies.
- **FR-009**: A `delete` outcome MUST rest on a caller read and a test that shows that no exception reaches the block.
- **FR-010**: A `narrow` outcome MUST name only operational exception types that the block can raise. A narrowed type MUST NOT include `TypeError`, `AttributeError`, `NameError`, or `AssertionError`.
- **FR-011**: A call into the mistapi REST layer MUST NOT receive a narrowed exception type for a transport fault. The handler MUST check the returned `APIResponse` instead (RC-094).
- **FR-012**: A `keep` outcome MUST keep the broad catch, MUST log the exception with exception information, and MUST carry a comment that states why the breadth is correct.
- **FR-013**: Each handler that the code continues past MUST log the exception type, the operation name, and a redacted message at error level.
- **FR-014**: A handler that passes without a log call MUST carry a keep comment. The comment MUST state why silence is correct.
- **FR-015**: A change MUST NOT add a `# noqa` directive or a type-ignore directive. A kept site that pylint flags MUST carry one inline `broad-exception-caught` disable and one reason comment.

Logging and privacy

- **FR-016**: A changed log call MUST NOT print a raw credential, a raw address, raw user input, or a raw response body. Each slice that changes a log call MUST include a redaction test with a synthetic credential. The test MUST use the real handler chain (RC-061).

Slices and pull requests

- **FR-017**: Each slice pull request MUST audit at most 40 sites. All audited sites MUST belong to one slice in `plan.md`.
- **FR-018**: Each slice pull request body MUST contain one outcome row for each audited site.
- **FR-019**: Slices MUST land one at a time in the order of `plan.md`. Each slice MUST lower the count of each changed file in `.github/blind-exception-handler-baseline.json`. A slice MUST NOT raise a count.
- **FR-020**: Each slice MUST rebase onto current main before publication. Each slice MUST run its affected gates again after the rebase.
- **FR-021**: Each narrowed site MUST have one test for the operational path and one test that shows that a programming error propagates. Each kept site with a changed log call MUST have one redaction test.

Final gate

- **FR-022**: The final pull request MUST add `BLE001` to the ruff select list in `pyproject.toml`. It MUST keep `RUF100`.
- **FR-023**: The final pull request MUST remove `W0718` from the pylint disable list. It MUST rewrite the comment at lines 588 to 593 that records the 493-site count.
- **FR-024**: The changes in FR-022 and FR-023 MUST land in one pull request.
- **FR-025**: The final pull request MUST keep the `extend-exclude` list unchanged.
- **FR-026**: The growth guard MUST stay in place until the final pull request. The final pull request MUST update the stored-baseline test in the same change, because that test requires at least one baseline entry.

Coordination and preservation

- **FR-027**: A held local commit MUST NOT publish until its owner rebases it onto current main. Its owning slice MUST pass the checks for the files that the commit changes.
- **FR-028**: The implementer MUST NOT delete a branch or a commit that holds unmerged work. A merged replacement must prove preservation first.
- **FR-029**: Each new slice cluster MUST have its own issue that names #1794. A slice pull request MUST refer to #1794 with a reference keyword and MUST NOT close it.
- **FR-030**: This record MUST supersede the legacy records under `specs/1794-blind-except*`. The legacy records MUST NOT be deleted.
- **FR-031**: New record folders MUST stay under the managed numbered route `specs/numbered/0/0/0/2/4/1/3/4/`. Each directory MUST hold five children or fewer.

Scope and tests

- **FR-032**: Each excluded tree (`mist-ops-platform/`, `web_portal/`, `scripts/`, and `src/interfaces/visualization/maps/`) MUST receive one follow-up issue that states its count.
- **FR-033**: Test files inside the ruff scope MUST follow the same outcome policy as production code.

Documentation and style

- **FR-034**: Each changed Markdown file MUST follow the Simplified Technical English rules. Each file MUST score 80 or higher in the STE gate.
- **FR-035**: Each slice MUST add one changelog fragment that follows `changelog.d/README.md` (RC-025).
- **FR-036**: Each changed Python line MUST carry an inline comment that explains its purpose.
- **FR-037**: Each slice MUST run each local gate in the repository gates table that applies to its changed files before publication.

Versions

- **FR-038**: Changes MUST target Python 3.15 (RC-005). Changes MUST call Mist REST endpoints through mistapi methods only.

### Key Entities

- **Blind handler**: A `try` block whose `except` clause names `Exception` or `BaseException`, and whose bound name never appears in the handler body (RC-032).
- **Outcome row**: One audited site with its file, enclosing function, outcome, exception types after the change, log call, test name, and reason for a keep (`contracts/outcome-table.md`).
- **Slice**: One cluster of at most 40 candidate sites from `plan.md`, with one pull request and one changelog fragment.
- **Baseline entry**: A repository path with a positive integer count of accepted blind handlers (RC-033).
- **Held commit**: A local or remote commit that holds unmerged work, not reachable from main (RC-104, RC-106, and RC-112 to RC-125).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The baseline states the pinned ruff count, the `--ignore-noqa` count, the pylint count, and each reconciliation reason. (FR-001 to FR-005)
- **SC-002**: `ruff check . --select BLE001 --ignore-noqa --statistics` reports zero findings after the last slice.
- **SC-003**: The outcome table of each slice has one row for each audited site and no blank outcome.
- **SC-004**: Each keep site carries a reason comment. A search of the changed lines proves it, and a reviewer confirms each reason in review.
- **SC-005**: Each handler that the code continues past logs the exception type. The redaction and log tests prove it.
- **SC-006**: The changes add zero `# noqa` directives.
- **SC-007**: No slice pull request audits more than 40 sites.
- **SC-008**: The final `pyproject.toml` selects `BLE001`, keeps `RUF100`, and no longer disables `W0718`.
- **SC-009**: A new broad handler with an unused name fails the growth guard. The guard test proves it.
- **SC-010**: Each slice keeps the unit pass count that T001 records. The pylint score stays at 9.5 or above.
- **SC-011**: Each held commit has a merged replacement, or a remote branch with a preservation note, before its local branch is removed.
- **SC-012**: Four excluded-tree follow-up issues exist, and each names its count.

## Out of Scope

- Publishing a held local commit without a rebase (FR-027).
- Changing the `extend-exclude` list or adding ignore rules (FR-025, D-8).
- Fixing the separate defects in issues #4709, #4712, #4713, #4717, #4721, #4746, and #4818 inside this audit. Each keeps its own issue.
- Changing mistapi behavior, menu operations, output formats, or log levels. Issues #1766 and #1793 own log levels.
- Closing or reopening the child issues #2833, #2834, #2835, #2836, and #2926 (D-7).
- Deleting the legacy records under `specs/1794-blind-except*` (FR-030).
- Merging a slice that changes a destructive operation without a human review. AGENTS.md requires that review, and the auto-merge label is not allowed on those slices.

## Assumptions

- The audit uses ruff 0.17.6 and pylint 4.1.4 for its whole run (RC-007, RC-008).
- Each slice owner holds the file reservation for its files. Parallel slices do not share a file (AGENTS.md).
- mistapi stays at 0.64.1 (RC-018).
- Remote CI runs each slice gate on GitHub. The local gates cannot replace CI.
- A reviewer who did not write a keep comment confirms it in pull request review. This review step is not an agent task.

## Dependencies

- No open issue blocks the first slice. The companion #1792 and the growth guard #3070 are closed, and their work is in place (RC-032, RC-035).
- Issue #2711 owns the assertion review in `tests/unit/websocket/diagnostics/test_ping_executor.py`. The held ping branch waits for its handoff.
- Issue #3824 reserves `src/foundation/support/utils/zscaler_catalogue.py` for a later package refactor. Slice S16 waits for a file-scoped handoff.
- Issue #4709 owns the pagination status in `src/operations/exporting/export/site_other_device_events_exporter.py`. Slice S12 coordinates with it.
- Issues #4712, #4713, #4717, #4721, and #4746 own separate defects in files that slices S06, S12, S15, and S16 also change. Each owner coordinates before the slice starts.

## Clarifications

### Session 2026-11-26

- Q: Did issue #1792 land? A: Yes. RUF100 is selected in `pyproject.toml` line 209 (RC-035). No in-scope `noqa: BLE001` line remains. Sixteen such lines remain in the excluded maps tree (research.md, Local evidence).
- Q: Is the issue count of 412 valid? A: No. The last reported ruff count is 524 (issue comment 9, 2026-10-29). T001 measures the count again (FR-001).
- Q: Which Python and tool versions apply? A: Python 3.15, ruff 0.17.6, and pylint 4.1.4 (RC-005, RC-007, RC-008). The older record values are stale (RC-006).
- Q: Is the W0718 disable still present? A: Yes, at line 594 of `pyproject.toml`, not line 475 (RC-002).
- Q: Does the growth guard exist and run? A: Yes. The guard and its baseline are on main (RC-032, RC-033), and the CI shards include `tests/guardrails` (RC-017).
- Q: Are the child issues still open? A: No. They closed between 2026-09-17 and 2026-10-30 (research.md, GitHub state). The legacy records treat them as open. New cluster issues replace them (D-7).
- Q: Do the held commits exist on GitHub? A: Yes, as commit objects (RC-104, RC-106, and RC-112 to RC-125). None is an ancestor of main, so none is merged (research.md, Local evidence).
- Q: Is `RuntimeError` the right narrow type for the firmware resolver? A: No. The mistapi REST wrapper catches transport faults and returns an `APIResponse`. It raises `RuntimeError` only inside token rotation, and the wrapper catches that case (RC-093, RC-094). See D-4.
- Q: Does the CI pylint gate read `MistHelper.py`? A: No. It reads `SRC_PATH`, which is `src/` (RC-013, RC-014).
- Q: Do the legacy records describe the current code? A: No. Sixteen existing-record claims are stale and one is absent (analysis.md, A-1 to A-24).
