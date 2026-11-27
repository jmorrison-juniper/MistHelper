# Implementation Plan: Count export write results

**Branch**: `fix/4720-count-export-writer-results` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/3/4/0/4720-count-export-writer-results/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Keep the writer result in `CountExporter._persist`. When the writer returns `False` or `None`, log one error, print one failure notice, and return before the success notice. The change edits one production function, one existing test file, one operator guide paragraph, and one changelog fragment. The route `0/0/1/2/2/3/4/0` is the base-5 form of issue 4720.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` line 23 requires `>=3.15`)

**Primary Dependencies**: `mistapi` 0.64.1 (`requirements.txt` line 129). No new dependency.

**Storage**: No change. Count output stays under `data/` through `DataExporter`.

**Testing**: pytest with mocks. The regression class uses the `fake_mh` fixture, patched SDK callables, and `caplog`.

**Target Platform**: Windows 11, macOS, and Linux. The change adds no path handling.

**Project Type**: Bug fix in three existing menu operations.

**Performance Goals**: No change. The fix adds one truth-value check for each count write.

**Constraints**: `_persist` stays at 25 lines or fewer, with five logical blocks or fewer. No module-level name changes (`symbol-diff` gate).

**Scale/Scope**: 72 count operations behind three menus. One shared function changes.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Result | Reason (evidence in this plan) |
| - | - | - |
| I. Five-item rule | PASS | No new direct child under a noncompliant parent. `tests/unit/export/` holds 55 children (research row 53). `src/operations/exporting/export/` holds 49 (row 54). The plan edits existing files there only. The record nests under `specs/numbered/`, and its route parent holds three children and gains one (row 52). |
| II. Class-based | PASS | The change stays in `CountExporter`. No wrapper is added. |
| III. Safety first | PASS | Menus 235 to 237 are `interactive_safe` (row 23). The change reads no new input and adds no destructive action. |
| IV. Full pipeline | PASS | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. Publication waits for the hold to lift. |
| V. Logging | PASS | Every new string is ASCII. The failure log uses `error`. The notice uses `info`, as the other count notices do. |
| VI. Inline comments | PASS | FR-009 and the T002 acceptance statement require a comment on each changed line. |
| VII. Action logging | PASS | FR-008 requires the info line before the call and the debug line after it. The logging-order case in T001 tests it. |
| Mist transport | PASS | The change adds no SDK call. The existing count calls stay as they are (rows 4 and 59 to 61). |
| Output backends | PASS | The writer call stays the only write path (rows 12 and 13). |
| Database keys | N/A | The change adds no operation. The count strategies stay unchanged. |
| Data directory | PASS | The tests use mocks. No output file is created. |
| Security findings | N/A | The change adds no suppression and no security tool finding. |
| Documentation | PASS | FR-016 and FR-017 cover the operator guide and the changelog fragment. |
| Branch and labels | PASS | Branch `fix/4720-count-export-writer-results` (D-8). Existing labels stay (D-14). |
| Container runtime | N/A | The tests run on the host virtual environment (D-11). No container starts. |

For repository structure and generated files:

- The commit subject and the pull request title use `fix(export): report failed count writes`.
- The change adds one record under `specs/numbered/` and one fragment under `changelog.d/`.
- Product output stays under `data/`. Test output uses mocks and `caplog`.

For a feature that uses Juniper Mist Cloud:

- REST methods are unchanged. The count operations call their mistapi functions with a session and an identifier, and they page with `mistapi.get_all`.
- No owned WebSocket transport is added. SDK insufficiency contract tests do not apply.
- Failure safety is covered by FR-007 and the raised-error case. Secret redaction is unchanged, because the change adds no logged credential.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/4/0/4720-count-export-writer-results/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      count-menu-output.md
      writer-result.md
    checklists/
      requirements.md
      operator-output.md
```

### Source Code (repository root)

File change map:

| Path | Action | Purpose | Requirements |
| - | - | - | - |
| `src/operations/exporting/export/count_exporter.py` | modify | Keep the writer result in `_persist`, add the failure branch, add the info and debug lines, and update the docstring. | FR-001 to FR-011 |
| `tests/unit/export/test_count_exporter_workflows.py` | modify | Add class `TestCountWriteOutcomes` with twelve cases. | FR-012 to FR-014 |
| `documentation/operator-guide.md` | modify | Add one paragraph after line 120 for menus 235 to 237. | FR-016 |
| `changelog.d/issue-4720-count-export-writer-results.md` | add | One heading and one Fixed bullet. | FR-017 |
| `specs/numbered/0/0/1/2/2/3/4/0/4720-count-export-writer-results/` | add | The record, as drafted under `design/`. | FR-019, FR-020 |

Unchanged: `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/operations/exporting/export/data_exporter.py`, `README.md`, `requirements.txt`, `pyproject.toml`, `tests/unit/export/test_count_exporter.py`, and `tests/contract/test_export_api_function_names.py`.

## Dependencies

No new package. `mistapi` stays at 0.64.1. `pyproject.toml` line 29 and `requirements.txt` line 129 stay unchanged. Pip audit does not apply, because no dependency file changes.

## Architecture

The menu reaches the writer through this call path. Each arrow is a call in the current code.

```text
MistHelper.py menu 235, 236, or 237 (research rows 19 to 21)
  -> CountExporter.org_counts, site_counts, or msp_counts (rows 9 to 11)
  -> CountExporter._choose, then CountExporter._run (row 4)
  -> SDK count operation, then mistapi.get_all (row 4)
  -> CountExporter._persist (row 1)
  -> DataExporter.write_with_format_selection (rows 12 to 15)
```

The fix sits at the last step inside `CountExporter`. The change does not alter any step before `_persist`, and it does not alter the writer.

No file is deleted by this change.

## Implementation Outline

1. Write the regression class first. Seven of the twelve cases fail on unchanged source (T001).
2. Change `_persist` in the following order (T002):
   - Store the writer result in `written`.
   - Log the info line before the writer call.
   - On a false result, log the error, print the failure notice, and return.
   - Keep the debug line and the success notice after that branch.
3. Confirm that the existing count tests and the contract guard pass (T003).
4. Add the operator guide paragraph and the changelog fragment (T004, T005).
5. Run the symbol gate and the test-quality ratchet (T006, T007).
6. Run the applicable local gates, then commit explicit paths (T-LOCAL-GATES).
7. Rebase, push, and open the pull request only after the owner lifts the hold (T-PR).
8. Watch the 15 required contexts, then merge only after orchestrator authorization (T-REMOTE-CI, T-MERGE).

Target order inside `_persist` (behavior only, not the final code):

```text
no rows              -> info notice "No data" -> return
flatten and escape   -> info "Writing" line -> written = writer call
written is false     -> error log -> failure notice -> return
debug "persisted"    -> success notice
```

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Open pull request #4813 changes `data_exporter.py`, so the writer contract could move. | Rebase before T-PR. Read the merged writer contract. The regression tests mock the writer, so they still pin the count behavior. |
| The test-quality ratchet reports a new finding for the new class. | Give each assert a clear form. Do not rewrite the baseline to hide a finding. |
| `symbol-diff` compares with `origin/main`, which a stale clone may lack. | Run `git fetch` for `origin main` before T006. |
| An operator reads the failure notice as a partial file. | The notice says not to treat the file as complete. The operator guide paragraph repeats the rule. |
| Issue #4717 stayed open after PR #4847 merged on 2026-11-19. | T-PR puts `Closes #4720` in the pull request body. T-MERGE checks the issue state. |

Caution: opening the pull request during the hold publishes an unreviewed change. If the hold blocks the pull request, keep it closed. Closing a pull request is recoverable.

## Rollback

1. Revert the squash commit on `main` through a new pull request. Do not force-push `main`.
2. The revert removes the failure branch, the operator guide paragraph, the fragment, and the record folder in one commit.

Caution: the revert brings back the false success notice until a new fix lands.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `tests/unit/export/` holds 55 children (grandfathered, research row 53). | The count regression tests belong with the count tests. | A new file or package adds a direct child to a noncompliant parent. Principle I forbids it. |
| `src/operations/exporting/export/` holds 49 children (grandfathered, research row 54). | The fix edits one existing module. | No new module is needed, so no new child is added. |
| Separate remediation action | Both folders need compliant subfolders. | One separate issue carries the split. The split does not belong in this fix, because one concern belongs in one pull request. |

The edit to `count_exporter.py` is narrow and necessary. Principle I allows an edit to an existing child in a noncompliant parent, and the change does not add a child there.
