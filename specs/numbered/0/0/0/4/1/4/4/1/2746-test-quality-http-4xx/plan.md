# Implementation Plan: HTTP 4xx Test-Quality Findings

**Branch**: `test/2746-http-4xx-baseline` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record route `specs/numbered/0/0/0/4/1/4/4/1/2746-test-quality-http-4xx/`.

## Summary

The working set is the 38 `missing_fm_http_4xx` baseline entries on main. Evidence splits them into three classes. Class B entries leave the baseline after a complete report omits them. Class A and class C entries stay until an upstream analyzer release removes them. No new test function is planned.

## Technical Context

- **Language/Version**: Python test code. The repository runs pytest on this code.
- **Primary Dependencies**: The `test-quality-analyzer` command from misthelper-devtools at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Also pytest, ruff, and black. Evidence: `requirements-dev.txt:197` (RC-13) and `direct_url.json:1` (RC-80).
- **Storage**: A JSON baseline at `.github/test-quality-baseline.json` (RC-16).
- **Testing**: The analyzer gate (RC-08), the TestLiveGuides preflight (RC-15), and the guardrail tests.
- **Project Type**: Test-suite governance change in an existing repository.
- **Performance Goals**: Not applicable. The change alters no runtime path.
- **Constraints**: No production behavior change. No opt-in marker. No exclusion.
- **Scale/Scope**: 733 baseline entries, of which 38 are `missing_fm_http_4xx` entries (RC-16).

## Constitution Check

Each rule has a result and a reason. Sources: `.specify/memory/constitution.md` (RC-17) and `.github/copilot-instructions.md` (RC-04, RC-05, RC-06).

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one folder under the route. The route holds one child. The change edits one existing baseline file. |
| II. Class-based architecture | Pass | The change adds no Python code and no function. |
| III. Safety-first | Pass | The change adds no input prompt, no destructive operation, and no secret. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE apply. No task pushes to main. |
| V. Observability | Pass | The change adds no log statement. The record uses ASCII text. |
| VI. Inline comments | Pass | The change adds no Python line. |
| VII. Action logging | Pass | The change adds no product action. |
| Mist Cloud REST access | Pass | The change adds no REST request. No new test calls mistapi. |
| Owned WebSocket transport | Pass | Not applicable. The change owns no transport. |
| Container runtime | Pass | Not applicable. No container starts. |
| Data directory | Pass | No output goes to `data/`. Analyzer reports go to a folder outside the repository. |
| Spec Kit route | Pass | The base-5 digits of 2746 are 41441. Padded to eight digits, the route is 00041441. This matches ROUTE. |
| Test-quality ratchet | Pass | The change adds no test module and no bare assert. Baseline edits remove class B entries only. |
| Conventional Commit title | Pass | Pull request one uses `test(quality): remove unmatched HTTP 4xx baseline entries`. |

## Architecture

The change follows one pipeline:

1. Confirm the baseline and the pin (T001).
2. Run the complete report with the pinned analyzer (T002).
3. Record the class of each entry with evidence (T003).
4. Remove class B entries absent from the complete report (T004).
5. Repair class A and class C findings upstream (T005).
6. Bump the pin and remove the cleared entries (T006).
7. Verify the class C test modules and add a test only for a real gap (T007).
8. Run the local gates, open the pull request, watch CI, and merge (final tasks).

## File-by-File Change Map

| Action | Path | Task | Reason |
| - | - | - | - |
| Add | `specs/numbered/0/0/0/4/1/4/4/1/2746-test-quality-http-4xx/` | T-PR | The record folder. It holds five children or fewer. |
| Modify | `.github/test-quality-baseline.json` | T004 | Remove class B entries absent from the complete report. |
| Modify | `.github/test-quality-baseline.json` | T006 | Remove class A and class C entries absent from the released analyzer report. |
| Modify | `requirements-dev.txt` | T006 | Line 197 changes to the released commit. |
| No change | The 38 test modules listed in `design/research.md` rows RC-35 to RC-72 | None | No test change is planned. |
| No change | `src/` and `mist-ops-platform/` | None | No product change is planned. |
| External | `misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` in jmorrison-juniper/misthelper-devtools | T005 | Upstream repair. It is not in this repository. |

## Contracts

Omitted. This change alters no CLI, menu, API, or report output contract. The record has no `design/contracts/` folder.

## Data Model

See `design/data-model.md`. The data model defines the baseline entry, the finding, the test module, and the upstream dependency.

## Dependencies

- A misthelper-devtools release that carries the applicability repairs. Task T005 owns it. Issue #67 is open.
- A complete report from the pinned analyzer. Task T002 owns it.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A removal hides a real defect. | Remove an entry only when a complete report omits its finding. Check the diff. |
| `--write-baseline` accepts a new finding. | Use it only after the gate reports zero new findings and every removed entry is a class B entry. Otherwise remove entries by exact key. |
| The complete report differs from this record. | Task T003 updates the class table before task T004. |
| The upstream release is late. | Pull request one proceeds without class A and class C changes. Those entries stay in the baseline and the gate passes. |
| A line-keyed entry changes identity. | Append any new test code at the end of a file. No test edit is planned. |

## Rollback Steps

1. Preserve the branch with a recovery branch or a tag. Then close pull request one without merge.
2. In the feature worktree only, run `git restore --source=origin/main -- .github/test-quality-baseline.json`.
3. Remove the record folder from the branch with a revert commit. Keep the draft copy in the session files folder.
