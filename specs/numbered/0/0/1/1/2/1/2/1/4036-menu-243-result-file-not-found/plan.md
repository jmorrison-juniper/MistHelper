# Implementation Plan: Menu 243 Result File Not Found

**Branch**: `fix/4036-menu-243-preview-test` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/2/1/2/1/4036-menu-243-result-file-not-found/spec.md`.

## Summary

The reported symptom came from a two-part table route that captured nested JSON paths. Main already fixes that route and the output-list defect. This plan adds the missing end-to-end browser regression to an existing test module. It adds one changelog fragment and no product code. The live check runs after merge on the deployed container.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `pyproject.toml` requires [RC-08].

**Primary Dependencies**: Flask with Werkzeug 3.1.9 [RC-09]. The browser test uses Playwright through pytest, guarded by `pytest.importorskip` [test module line 34].

**Storage**: Output files under the data directory. No database change.

**Testing**: pytest for unit and browser tests. Chromium runs the browser test.

**Target Platform**: The Podman container on Linux and the Windows development host.

**Project Type**: Flask web portal.

**Performance Goals**: None. The change adds one test.

**Constraints**: Resolver behavior stays unchanged. The test writes only under `tmp_path`. The module keeps its existing fixtures.

**Scale/Scope**: One test function with its helpers, one changelog fragment, and this record.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I Five-item rule | Pass with recorded debt | The test joins an existing file. `tests/e2e/web_portal` holds 32 children, and `tests/unit/web_portal` holds 52 [RC-79, RC-80]. The fragment adds one child to `changelog.d`, which holds 335 [RC-56]. |
| II Class-based architecture | Pass | The helpers follow the module pattern of `free_port` and `column_values`. No product code changes. |
| III Safety first | Pass | The test writes under `tmp_path`. It sets `DATA_DIR` to that path. It runs no destructive operation. |
| IV Full pipeline | Pass with steps | Tasks T-LOCAL-GATES to T-MERGE cover the pipeline. No image build runs, because no product file changes [RC-02]. |
| V Observability | Pass | New log lines use ASCII text and `%s` formatting. |
| VI Inline comments | Fail as committed, pass after T005 | Commit `18ce4c8` lacks inline comments on most lines [research F-13]. T005 adds them. |
| VII Action logging | Fail as committed, pass after T005 | Commit `18ce4c8` logs only the fixture start [research F-13]. T005 adds logs before and after each action. |
| Technology: mistapi | Not applicable | Menu 243 makes no Mist API call [RC-39]. |
| Technology: Podman | Pass | The live check uses the deployed product container. No ephemeral test container starts. |
| Technology: file paths | Pass | The test builds paths with `pathlib.Path`. |
| Data directory | Pass | Test outputs stay under `tmp_path` [research F-12]. |
| Security | Pass | The change adds no input path and no dependency. |
| Documentation: README | Not applicable | No operator-visible behavior changes. |
| Documentation: release note | Pass | One fragment under `### Changed` [D-07]. |
| Audience | Pass | The fragment uses plain words. |
| Escalation | Pass | This record exists. The change spans more than two files. |
| Multi-agent git | Pass | One issue, one branch, one pull request. The branch uses the allowed `fix` type [RC-02]. |
| Closure keyword | Deviation, recorded | Constitution step 7 asks for the closure keyword. This plan uses `Relates to #4036` [D-04]. |

## Architecture

The menu 243 path has four stages.

1. The run writes the ledger under the data directory. The run log names the input and output paths [research F-06].
2. The output list keeps names that exist under the data directory [RC-26]. The allowlist input is excluded [RC-53].
3. The Results panel asks the preview route for the selected file [RC-29].
4. The preview route selects the file by complete path. The table branch runs only for a database directory [RC-14, RC-18]. The resolver returns the file [RC-23].

The download route calls the same resolver with the same path [RC-20].

## File Change Map

| Path | Action | Purpose |
| --- | --- | --- |
| `tests/e2e/web_portal/test_operation_results_table.py` | Modify | Add the menu 243 test, its helpers, and `RUN_TIMEOUT_MS`. Reuse `READY_TIMEOUT_MS`. Add inline comments and action logs. |
| `changelog.d/issue-4036-menu-243-preview-test.md` | Add | One fragment under `### Changed`. Rename it to `pr-<number>.md` after the pull request exists. |
| `specs/numbered/0/0/1/1/2/1/2/1/4036-menu-243-result-file-not-found/` | Add | The record folder. The orchestrator places it, and it ships with the change. |
| `web_portal/routes/data.py` | No change | The route fix is present on main [RC-14]. |
| `web_portal/services/data_browser.py` | No change | The resolver and error text are present [RC-22, RC-23, RC-24]. |
| `web_portal/services/operation.py` | No change | The output-list rule is present [RC-26]. |
| `web_portal/static/js/operation_results.js` | No change | The pending clear is present [RC-30]. |
| `src/operations/hardware/mib_generator/` | No change | Menu 243 behavior is unchanged. |
| `.specify/feature.json` | No change | Read-only work does not change it [RC-13]. |
| `specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/` | No change | The legacy record stays unchanged [D-09]. |

## Dependencies

- No new package. The test uses Playwright through pytest, as the module already does [test module line 34].
- Chromium comes from the bootstrap step in the repository instructions [RC-02].

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The browser test is slow or flaky in CI | A required check fails | Reuse `READY_TIMEOUT_MS`. Add a bounded `RUN_TIMEOUT_MS`. Run the module locally before the push. |
| The patch point changes | The test misses the handler | The handler imports the runner at call time [RC-40]. The test asserts that the ledger file exists. |
| A later Werkzeug release changes route order | The table route captures nested paths again | The test asserts HTTP 200 for the nested preview. |
| The live check finds a second cause | The symptom stays open | Mark the record blocked. Open a new issue from `main` [D-05]. |
| The closing keyword appears early | The issue closes before evidence exists | Use `Relates to #4036` [D-04]. |
| The test module grows | Review takes longer | Keep helpers short. Run the test-quality ratchet [T-LOCAL-GATES]. |
| The fragment adds a `changelog.d` child | Folder debt grows by one | Track a separate remediation action [Folder Debt]. |

## Rollback Steps

1. Revert the squash commit on `main` through a new pull request.
   Warning: Do not force-push `main`. A force push removes commits from the shared history.
2. Confirm that the browser module returns to its prior content. Run `python -m pytest tests/e2e/web_portal/test_operation_results_table.py`.
3. Remove the fragment in the same revert. The test writes only under `tmp_path`, so no data needs cleanup.

## Folder Debt and Remediation

- `specs/` holds 795 direct children [RC-57]. This record adds none, because it sits under the numeric route.
- `changelog.d/` holds 335 direct children [RC-56]. The fragment adds one.
- `tests/e2e/web_portal` holds 32 children, and `tests/unit/web_portal` holds 52 [RC-79, RC-80]. This plan adds none.
- Remediation action: open a separate maintenance issue to reduce the direct children of `changelog.d/`. This issue does not include that work.
