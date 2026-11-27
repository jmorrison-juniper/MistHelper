# Implementation Plan: Site export write results

**Branch**: `fix/4717-site-export-writes` (merged) | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The writer check is on `main`. Both persistence methods log one error when the writer returns `False`. This plan covers the remaining work. The work adds inline comments to touched statements, adds offline proof, adds route proof, and closes issue #4717 through a merged pull request.

## Technical Context

- **Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.
- **Primary Dependencies**: `mistapi==0.64.1` (`requirements.txt` line 129). Repository helpers `DataExporter`, `DataProcessingUtils`, and `SourceDependencyResolver`.
- **Storage**: Writer output through `DataExporter.write_with_format_selection` to CSV or SQLite under `data/`. No schema change.
- **Testing**: pytest module `tests/unit/export/test_site_asset_and_events_exporters.py`. Local gates are in `.github/copilot-instructions.md` lines 57-74.
- **Target Platform**: Windows 11, macOS, and Linux. The product image runs in a Podman container.
- **Project Type**: Menu-driven command line tool (`MistHelper.py`) with web portals.
- **Performance Goals**: No change. The repair adds one truth-value check for each export.
- **Constraints**: Synthetic data only for verification. No Mist cloud call and no live database write.
- **Scale/Scope**: Two persistence methods, two menu entry points, one shared test module, and one record folder.

## Constitution Check

Checked on 2026-11-26 after research. The gate uses `.specify/memory/constitution.md` version 1.9.0.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule, levels | Pass with debt | The new test class has five members: one fixture and four tests. The shared test module already holds more than five top-level names. That debt is grandfathered. |
| I. Five-Item Rule, new children | Pass | No new top-level name enters the shared test module. The offline harness stays outside the repository. `tests/unit/export/` holds 55 children, so a new module there would add to a noncompliant parent. |
| I. Five-Item Rule, record layout | Pass | The record root holds five children. The `design/` folder holds five children. The route holds one child. |
| II. Class-based design | Pass | Both exporters keep their class and static methods. The repair adds no wrapper function. |
| III. Safety-first | Pass | No keyboard read and no destructive operation. Menus 213 and 214 are `interactive_safe` (`operation_registry.py` lines 281-282). Logs print filenames and counts, not secrets. |
| IV. Deployment pipeline | Open | Local gates (T-LOCAL-GATES), pull request (T-PR), remote CI (T-REMOTE-CI), and merge (T-MERGE) are open. PR #4847 passed its CI checks on the PR head. |
| V. Observability | Pass | Changed messages use ASCII text and `%s` formatting. |
| VI. Inline comments | Fail, repair planned | Six statement lines in the persistence methods and 27 statement lines in `TestSiteWriteOutcomes` lack a comment. Tasks T007 through T009 repair them. Analysis F-01 and F-02 record the lines. |
| VII. Action logging | Pass for touched blocks | The writer call has an info line before it (line 62) and an error or debug line after it (lines 67 and 69). Untouched methods are recorded in analysis F-13. |
| Technology: mistapi only | Pass | Calls use `mistapi.api.v1.sites.wxtags.getSiteApplicationList` and `mistapi.api.v1.sites.events.searchSiteSystemEvents`. No direct HTTP request exists. |
| Technology: owned transport | Not applicable | The feature has no owned WebSocket transport. |
| Technology: Podman | Pass | No container change. |
| Technology: file paths | Pass | This plan adds no path join. |
| Output backends | Pass | Both exporters keep the call to `DataExporter.write_with_format_selection`. |
| Operational store | Not applicable | The feature adds no coordination record. |
| Database keys | Pass with note | Both strategies exist in `endpoint_primary_key_strategies.py` lines 483-489 and 520-526. Analysis F-16 records the application list choice. |
| Data directory | Pass | Product output stays in the writer path under `data/`. |
| Container security and Zscaler | Not applicable | No container build or push is in scope. |
| Menu operations | Not applicable | Menus 213 and 214 already exist. No new menu is added. |
| README rule | Pass by superseding | PR #4918 removed menu text from `README.md`. `documentation/operator-guide.md` line 120 documents the behavior. Decision R-5 records the reason. |
| Release note | Pass | `changelog.d/issue-4717-site-export-writer-results.md` exists on `main`. |
| Commit and pull request title | Open | T-PR uses `docs(export): record write-result verification for issue 4717`, which the title guard accepts. |
| Issue first and labels | Pass | Issue #4717 has the `bug` and `MistHelper.py` labels and the `in-progress` label. |
| Branch naming | Pass | Merged branch `fix/4717-site-export-writes` follows `<type>/<issue>-<slug>`. T-PR uses `docs/4717-site-export-verification`. |
| Escalation to Spec Kit | Pass | The change touches three files and one record. A specification is required. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      operator-messages.md
      writer-result.md
      mist-api-calls.md
    checklists/
      requirements.md
      verification.md
      closure.md
```

### Source Code (repository root)

```text
src/operations/exporting/export/
  site_application_list_exporter.py     modify: inline comments on lines 58, 67, 68
  site_system_events_exporter.py        modify: inline comments on lines 58, 67, 68
tests/unit/export/
  test_site_asset_and_events_exporters.py   modify: inline comments on lines 337-435
test-artifacts/offline-guard/
  offline_guard.py                      create: local harness, git-ignored, not committed
```

**Structure Decision**: Use the existing modules. Add no source module and no test module. Keep the offline harness in `test-artifacts/`, which Git ignores.

## File Change Map

| Path | Action | Change | Requirement | Task |
| - | - | - | - | - |
| `src/operations/exporting/export/site_application_list_exporter.py` | Modify | Add an inline comment to lines 58, 67, and 68 in `_persist_applications`. The code does not change. | FR-010 | T007 |
| `src/operations/exporting/export/site_system_events_exporter.py` | Modify | Add an inline comment to lines 58, 67, and 68 in `_persist_system_events`. The code does not change. | FR-010 | T008 |
| `tests/unit/export/test_site_asset_and_events_exporters.py` | Modify | Add an inline comment to each of the 27 statement lines in `TestSiteWriteOutcomes`, lines 337-435. The test code does not change. | FR-010 | T009 |
| `test-artifacts/offline-guard/offline_guard.py` | Create, not committed | Pytest plugin that blocks socket, DNS, and SQLite entry points and counts each attempt. | FR-009 | T010 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/spec.md` | Modify, replace draft | This specification. | FR-001 to FR-015 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/plan.md` | Modify, replace draft | This plan. | All | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/tasks.md` | Modify, replace draft | The task list. | All | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/analysis.md` | Create | Consistency review and findings. | All | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/research.md` | Create | Decisions, remote table, and verdicts. | All | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/data-model.md` | Create | One line that states that the data model does not apply. | None | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/quickstart.md` | Create | Reproduction and verification steps. | FR-009, FR-010, FR-013 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/contracts/operator-messages.md` | Create | Operator message contract. | FR-001 to FR-006 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/contracts/writer-result.md` | Create | Writer result contract. | FR-001, FR-007 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/contracts/mist-api-calls.md` | Create | SDK and endpoint contract. | FR-008 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/checklists/requirements.md` | Modify, replace draft | Specification quality checklist. | All | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/checklists/verification.md` | Create | Verification evidence checklist. | FR-009, FR-010, FR-013 | T012 |
| `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/design/checklists/closure.md` | Create | Closure checklist. | FR-015 | T012 |

**Not changed**: `src/operations/exporting/export/data_exporter.py` (FR-008), `changelog.d/issue-4717-site-export-writer-results.md` (FR-012), `documentation/operator-guide.md` (FR-011), `README.md` (decision R-5), and `MistHelper.py` (FR-008).

## Dependencies

- No package changes. `mistapi==0.64.1` stays pinned in `requirements.txt`.
- Existing tools cover every gate: ruff, black, mypy, pytest, coverage, radon, bandit, pylint, vulture, pydocstyle, interrogate, symbol-diff, and test-quality-analyzer.
- `pwsh` (PowerShell 7) runs the route check named in T011. The route helper is `.specify/scripts/powershell/spec-route.ps1`.
- The gh CLI reads remote state for T-REMOTE-CI and T-MERGE.
- Task order: T007, T008, and T009 can run in parallel. T010 runs after T009 because both use the same test file.

## Architecture

The menu path has these steps. Each step cites its source.

```text
Menu 213 or 214 (MistHelper.py lines 4174-4189)
  -> site prompt (site_device_exporter.py line 130)
  -> mistapi SDK call (wxtags.py line 89, or events.py line 134)
  -> mistapi.get_all (__pagination.py line 39)
  -> persistence method (_persist_applications or _persist_system_events)
  -> flatten and escape (data_processing_utils.py lines 66 and 156)
  -> DataExporter.write_with_format_selection (data_exporter.py lines 153-180)
  -> writer result check (exporter lines 63-68)
       false: one error, and the method returns
       true: debug trace (line 69) and exported-count notice (line 72)
```

## Complexity Tracking

| Violation | Status | Why it exists | Simpler alternative rejected because |
| - | - | - | - |
| The shared test module holds more than five top-level names | Pre-existing, grandfathered | The module groups the site and asset exporter tests. | Splitting the module now expands the diff into a second owned scope. Decision R-12 defers it. |
| The `wired` fixture runs more than 25 lines | Pre-existing, grandfathered | It wires many collaborators in one place. | Changing the fixture expands the debt. The repair does not touch it. |
| `TestSiteWriteOutcomes` holds five members | New, compliant | One fixture and four tests. | Compliant at the limit. Adding a member would break the limit. |

**Separate remediation action**: open one issue to split `tests/unit/export/test_site_asset_and_events_exporters.py` by exporter. Cite analysis F-12.

## Risks and Mitigations

- Warning: a commit pushed to `fix/4717-site-export-writes` after its squash merge creates an orphan pull request. Mitigation: T-PR uses a new branch from `main`.
- Warning: a checkout in the OneDrive repository folder can overwrite or lock uncommitted files. Mitigation: T-PR uses a git worktree, as `AGENTS.md` requires.
- Caution: a comment-only edit can remove a closing parenthesis by mistake. Mitigation: run the pytest command in each task after each edit.
- Caution: the offline harness misses an access path it does not patch. Mitigation: list each patched entry point in `design/quickstart.md`, and run the harness self-test.
- Caution: `Resolve-SpecFeaturePath` fails under Windows PowerShell 5.1. Mitigation: T011 runs under `pwsh` version 7 only.
- Caution: the publication hold and the merge history conflict. Mitigation: decision R-8 gates T-MERGE on orchestrator authorization.
- Caution: `symbol-diff` reports added names for the test file. Mitigation: use `origin/main` as the base, which already holds the new class (analysis F-17).

## Rollback Steps

1. For comment-only changes (T007 to T009), revert the T-PR commit on its branch before merge. Run T-LOCAL-GATES again after the revert.
2. For the offline harness (T010), remove `test-artifacts/offline-guard/` by its exact path. Do not run a prune command.
3. For the record (T012), restore each draft file from commit `db06604d18` on `main` if review rejects the replacement.
4. Do not revert PR #4847. Caution: a revert restores the defect in both persistence methods.
5. For any later fix, open a new issue and branch from `main`, as `AGENTS.md` requires for a merged pull request.
