# Feature Specification: Count export write results

**Feature Branch**: `fix/4720-count-export-writer-results`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4720: `CountExporter._persist` ignores the Boolean result from `DataExporter.write_with_format_selection`. When the writer returns `False`, the exporter still reports that the records were exported. The shared path affects organization, site, and MSP count menus 235 through 237.

## Clarifications

### Session 2026-11-26

- Q: Should the failure notice reuse the success wording? → A: No. The failure notice starts with `! Write failed for`. It never contains `records exported to`.
- Q: Which writer results count as a failure? → A: Every false value and `None`. The writer declares a Boolean result, so `None` fails the truth-value test.
- Q: Should the fix cover other exporters that ignore the writer result? → A: No. Issue #4720 covers menus 235 through 237. Other call sites need a separate audit issue.
- Q: Should the candidate patch in the issue comment be reused? → A: No. The patch is not in the repository. The change follows the repository pattern from PR #4847.
- Q: May the change publish now? → A: No. The issue owner keeps publication and merge on hold. Tasks T-PR, T-REMOTE-CI, and T-MERGE stay open.
- Q: Where do the regression tests go? → A: The existing file `tests/unit/export/test_count_exporter_workflows.py`. The folder `tests/unit/export/` holds 55 children, so a new file would break the five-item rule.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed count write as a failure (Priority: P1)

An operator runs a count operation from menu 235, 236, or 237. The writer cannot save the rows. The tool reports a failure and never reports that the records were exported.

**Why this priority**: A false success hides lost data. A NOC engineer then trusts a file that holds an incomplete result.

**Independent Test**: Run each scope entry point with a mocked writer that returns `False`. Verify that an error line names the operation and that no success notice appears.

**Acceptance Scenarios**:

1. **Given** the writer returns `False` for an organization count, **When** menu 235 runs, **Then** the tool logs an error and prints the failure notice.
2. **Given** the writer returns `None` for a site count, **When** menu 236 runs, **Then** the tool prints no success notice.
3. **Given** the writer returns `True` for an MSP count, **When** menu 237 runs, **Then** the tool prints the unchanged success notice.
4. **Given** the Mist response holds no rows, **When** the operator runs any count menu, **Then** the writer is not called and the no-data notice appears.

---

### User Story 2 - Read the failed-write rule in the operator guide and the release notes (Priority: P2)

A NOC engineer reads the operator guide for menus 235 to 237. A release reader finds the fix in the changelog.

**Why this priority**: Menus 213 and 214 already state the failed-write rule. The count menus must state the same rule, so operators learn one rule.

**Independent Test**: Read the operator guide paragraph and the changelog fragment. Verify that each one states the failed-write rule and names issue #4720.

**Acceptance Scenarios**:

1. **Given** the operator guide, **When** a reader finds menus 235 to 237, **Then** the guide says a failed write never claims success.
2. **Given** the `changelog.d/` folder, **When** a reader lists the fragments, **Then** one fragment names issue #4720 under the Fixed heading.

---

## Edge Cases

- What happens when the writer returns `None`? The truth-value test fails, and the failure path runs.
- What happens when the writer returns `True`, but the polyglot mirror drops rows? The primary result stays `True`. `DataExporter` logs a warning, and the success notice stays unchanged.
- What happens when the writer raises an exception? `_persist` does not catch it. `_run` logs the error and prints no success notice.
- What happens when a format writer fails inside `DataExporter`? `_dispatch_format_write` catches the exception and returns `False`, so production failures reach the failure path.
- What happens when the response holds no rows? The writer is not called, and the no-data notice appears.
- What happens when the operator declines the operation, or no organization, site, or MSP resolves? The existing guards return before any writer call.
- What happens when the SDK function is missing? `_resolve` returns `None`, `_run` logs the gap, and no writer call occurs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `_persist` MUST store the writer result and judge it by truth value.
- **FR-002**: On a false or `None` writer result, `_persist` MUST log one error naming the operation, row count, and filename.
- **FR-003**: On a false or `None` writer result, `_persist` MUST print one notice that starts with `! Write failed for`.
- **FR-004**: On a false or `None` writer result, `_persist` MUST NOT print the success notice.
- **FR-005**: On a true writer result, `_persist` MUST keep the success notice text unchanged.
- **FR-006**: An empty response MUST NOT call the writer and MUST keep the no-data notice.
- **FR-007**: A writer exception MUST reach `_run`, which logs the error and prints no success notice.
- **FR-008**: `_persist` MUST log an info line before the writer call and a debug line after a successful call.
- **FR-009**: Every changed or touched line in `count_exporter.py` MUST carry an inline comment that explains its purpose.
- **FR-010**: The writer call MUST keep its positional arguments and the keyword `api_function_name=operation`.
- **FR-011**: The fix MUST cover menus 235, 236, and 237, because each one reaches `_persist` through `_run`.
- **FR-012**: The regression tests MUST fail on unchanged source for false and `None` results, and pass for the other cases.
- **FR-013**: The regression tests MUST mock the writer and the SDK, and MUST NOT write files or open network connections.
- **FR-014**: The regression tests MUST live in existing files, and MUST NOT add a direct child to `tests/unit/export/`.
- **FR-015**: The change MUST NOT alter `DataExporter.write_with_format_selection`, the three count tables, or the operation registry.
- **FR-016**: `documentation/operator-guide.md` MUST state the failed-write behavior for menus 235 to 237.
- **FR-017**: The change MUST add one fragment named `changelog.d/issue-4720-count-export-writer-results.md`.
- **FR-018**: The change MUST NOT add menu text to `README.md`.
- **FR-019**: The record MUST sit at `specs\numbered\0\0\1\2\2\3\4\0\4720-count-export-writer-results`.
- **FR-020**: Each new directory MUST hold five children or fewer.
- **FR-021**: The change MUST pass each applicable local gate before the commit.
- **FR-022**: Tasks T-PR, T-REMOTE-CI, and T-MERGE MUST wait until the issue owner lifts the publication hold.
- **FR-023**: T-MERGE MUST wait for orchestrator authorization after remote CI passes.

### Mist Cloud Transport Requirements

- The feature calls no new Mist REST method. The count operations keep their current mistapi calls.
- The 72 count operations are 37 in `_ORG_OPS`, 32 in `_SITE_OPS`, and 3 in `_MSP_OPS`. The tables start at lines 51, 91, and 126 of `src/operations/exporting/export/count_exporter.py`.
- The representative SDK signature is `mistapi.api.v1.orgs.devices.countOrgDevices`, which takes a session and an organization identifier. The local OpenAPI file names the same operation at line 8462 of `documentation/mist-api-openapi31yaml.yaml`.
- The paging call uses `mistapi.get_all`, defined at line 39 of the installed SDK module `__pagination.py`.
- The feature adds no owned WebSocket transport. No SDK insufficiency contract applies.
- The existing contract tests `test_every_entry_resolves_to_a_callable` and `test_every_callable_takes_session_and_identifier` keep covering the count table.

### Key Entities

- **CountOperation**: One row of `_ORG_OPS`, `_SITE_OPS`, or `_MSP_OPS`. Its natural key is the Mist operation name.
- **WriterResult**: The value that `DataExporter.write_with_format_selection` returns. A true value means that the primary output saved.
- **CountPersistOutcome**: The result of one `_persist` call. It has four states: no rows, written, write failed, and write raised.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On unchanged source, seven of the twelve new regression cases fail, and five cases pass.
- **SC-002**: After the fix, all twelve regression cases pass with the two existing count test files.
- **SC-003**: The contract guard `tests/contract/test_export_api_function_names.py` passes.
- **SC-004**: Each applicable local gate prints its expected result in `design/quickstart.md`.
- **SC-005**: All 15 required branch-protection contexts pass on the pull request head commit.
- **SC-006**: An operator who sees a failed count write sees no success notice in the same run.

## Assumptions

- The writer reports a failed write by returning `False`. `_dispatch_format_write` catches write exceptions and returns `False` at lines 148 and 150 of `src/operations/exporting/export/data_exporter.py`.
- Tests run on the host virtual environment with Python 3.15 and `mistapi` 0.64.1.
- No open pull request changes `count_exporter.py`, the count test files, or the operator guide. The check ran on 2026-11-26.
- Open pull request #4813 changes `data_exporter.py`. This record treats that change as a risk, not as a conflict.
- The issue owner releases the publication hold with an explicit comment on issue #4720.

## Out of Scope

- The other writer call sites that ignore the result. A local search found 139 such lines in 71 files. Main was not checked for each site.
- The stale `MistHelper.py` comment at line 585, which states 70 count endpoints. The tables hold 72.
- The root-logger calls in `_resolve` and `_run`. They keep their current form.
- The `mistapi` pin text in `.github/copilot-instructions.md` line 21.
- The menu table, the three count tables, the registry categories, and the CSV output format.
- The polyglot mirror outcome. `DataExporter` owns that rule.
