# Implementation Plan: Editor Import Diagnostics

**Branch**: `chore/4126-editor-import-diagnostics` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Keep `analysis.md` and `design/` at the feature root too. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

This change adds a documentation and evidence record. The reported defect comes from the editor window and its interpreter selection. It does not come from production code. The setup section that PR #4322 merged on `main` matches the repository evidence. The remaining work is a live editor check that only the owner can run. This change adds no source change.

## Technical Context

- **Language/Version**: Python 3.15 for the repository. This change touches no Python file.
- **Primary Dependencies**: Pylint 4.1.4 (`requirements-dev.txt` line 313). mistapi 0.64.1 from the pinned range `>=0.64.0,<0.65`. Visual Studio Code with the Microsoft Python and Pylint extensions.
- **Storage**: None.
- **Testing**: Acceptance checks AT-01 to AT-11 in `tasks.md`. The STE gate measures Markdown style. No new automated test is added. See decision D-5.
- **Target Platform**: Windows 11, macOS, and Linux worktrees. The owner runs the live editor check.
- **Project Type**: Documentation and evidence record.
- **Performance Goals**: None.
- **Constraints**: No source change. Closure hold on issue #4126. Native permission needed for screen inspection on macOS.
- **Scale/Scope**: 27 affected files, 534 issue diagnostics, 10 moved files, 8 cited lines.

## Constitution Check

*Gate: passed before research and again after design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The route uses digit folders only. Each directory holds five children or fewer. The feature root holds five children. Rows R71 to R73 record the route checks. |
| II. Class-Based Architecture | Pass | The change adds no code. |
| III. Safety-First | Pass | The change adds no input handling and no destructive operation. Secrets stay out of the record (FR-014). |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow the pipeline. The change pushes no commit to `main`. |
| V. Observability and Logging | Pass | The change adds no code and no log. Evidence rows use ASCII text. |
| VI. Inline Comments | Pass | The change adds no code. The change adds Markdown only. |
| VII. Action Logging | Pass | The change adds no code. |
| Technology constraints | Pass | No mistapi call, no UV dependency change, no container start, no path change, no data directory change, and no operational store. |
| Documentation rules | Pass | `documentation/development-setup.md` stays unchanged (decision D-3). The STE gate covers each changed Markdown file (T-LOCAL-GATES). |
| Release notes | Pass | One fragment `changelog.d/issue-4126-editor-import-spec.md` is added (T007, decision D-10). |
| Complexity escalation | Pass | A specification is required because the change touches three or more files. This record is that specification. |
| Branch naming | Pass | `chore/4126-editor-import-diagnostics` follows the constitution list of `fix`, `feat`, and `chore` (decision D-11). |
| Required labels | Pass | `lint`, `docs`, and `in-progress` are present. `needs-investigation` is removed (decision D-9). |
| Test rule | Pass with reason | The change adds no code, so no unit or integration test applies. Acceptance checks cover each requirement (decision D-5). |
| Mist Cloud transport | Not applicable | The change makes no Mist REST or WebSocket call. The SDK check covers an import path and a function signature only (row R75). |

## Architecture

The import diagnostic follows this path in the editor and in Pylint:

```text
Editor window folder -> Pylint extension working directory (pylint.cwd)
  -> pylint entry point removes the working directory (pylint __init__.py lines 69 to 95)
  -> repository init-hook adds the working directory to sys.path (pyproject.toml line 566)
  -> src.* imports resolve under the window folder

Selected interpreter -> Pylint command (pylint.path or pylint.importStrategy)
  -> third-party imports, such as mistapi and requests, resolve in that environment
```

The fix belongs to the window setup. The repository keeps its `init-hook` and its Pylint settings unchanged (decision D-2).

## File-by-File Change Map

| Repository path | Action | Purpose |
| - | - | - |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/spec.md` | Add | Specification |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/plan.md` | Add | This plan |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/tasks.md` | Add | Ordered tasks and acceptance checks |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/analysis.md` | Add | Consistency review and findings |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/research.md` | Add | Decisions, remote verification table, sources, and unverified items |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/data-model.md` | Add | Affected file and evidence row model |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/quickstart.md` | Add | Reproduction and verification steps |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/contracts/editor-evidence.md` | Add | Evidence output columns |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/checklists/requirements.md` | Add | Specification quality checklist |
| `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/design/checklists/live-check.md` | Add | Live check checklist |
| `changelog.d/issue-4126-editor-import-spec.md` | Add | Changelog fragment |

Modify: none. Delete: none. `documentation/development-setup.md` stays unchanged.

## Dependencies

No package is added or changed. Existing pins stay in place: pylint 4.1.4 and mistapi 0.64.1. The worktree bootstrap uses UV with Python 3.15.2.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The owner editor uses other extension versions. | Each evidence row records the versions (contract `design/contracts/editor-evidence.md`). |
| The `pylint.importStrategy` setting causes `pylint.path` to be ignored. | The evidence row records the Pylint command from the output (FR-003). A new change amends the doc when the output confirms the conflict. |
| The issue file list stays stale. | The record uses the current path list (decision D-7). |
| A closing keyword closes the issue at merge. | The pull request uses `Refs #4126` (decision D-6). Check AT-08 reads the body. |
| The native permission is missing. | The live check stops and reports the missing permission (FR-015). |
| CI passes while E0401 or E0611 messages remain. | The score gate accepts them (rows R56 and R81). The analysis recommends a separate issue (finding A-04). |
| The Markdown fails the STE gate. | Repair the text and run T-LOCAL-GATES again. |

## Rollback

Revert the squash commit through a new pull request. The change alters no runtime behavior, no data, and no settings. The revert removes the record folder and the changelog fragment.

## Contracts

The record contains one contract file, `design/contracts/editor-evidence.md`. No CLI, menu, API, or portal contract applies to this change.

## Complexity Tracking

No constitution violation exists. No grandfathered debt is touched. The directory `specs/numbered/0/0/1/1` already holds five children (row R72). The record adds no child to that directory.
