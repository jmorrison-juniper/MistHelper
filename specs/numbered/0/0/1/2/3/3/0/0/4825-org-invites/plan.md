# Implementation Plan: Organization Invites Export Handles a Missing mistapi Function

**Branch**: `fix/4825-org-invites-followup` (new branch from GitHub main) | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record folder

**Input**: Numeric record `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/`. Route check: 4825 equals `00123300` in base 5, which fills the eight-level route.

## Summary

The guard that skips a missing function is on GitHub main from pull request #4829. The follow-up change adds the missing logs, inline comments, and return type to `_invites`. It also adds one log-order test, makes the absent-path test strict, and removes three wrong link lines from the organization invite pages. This record replaces the legacy record in place.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: mistapi 0.64.1. `requirements.txt` line 129 pins `mistapi==0.64.1`. `pyproject.toml` line 29 allows `>=0.64.1,<0.65`.

**Storage**: None on the absent path. The supported path writes `OrgInvites.csv` through the shared export, as it does today.

**Testing**: pytest. The focused file is `tests/unit/export/test_org_export_utils.py`. Guard tests check Markdown links and the process folder.

**Target Platform**: Windows 11, macOS, and Linux. The repository instructions name these platforms.

**Project Type**: Python command-line tool with web portals.

**Performance Goals**: None change.

**Constraints**: No new dependency. No direct HTTP request. No menu change. No new output column.

**Scale/Scope**: One method, two test cases, three documentation lines, and this record.

## Architecture

The absent path and the supported path meet in one static method. The follow-up change adds the INFO and DEBUG records around the shared export call.

```text
Caller (none on GitHub main)
  -> OrgExportUtils._invites
       -> getattr(mistapi.api.v1.orgs.invites, "listOrgInvites", None)
            -> None: one ERROR record, then return
            -> callable: INFO record, OrgExportUtils.export_data(api_call, data_type="invites", sort_key="email"), DEBUG record
                 -> `APIDataFetcher` with the keyword arguments, then `execute` (export_data, lines 74 to 80)
```

## Constitution Check

The results below use GitHub main at commit `f03c6c9` and the planned change. Principles VI and VII fail on main and pass after the change.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The record root holds five children. No direct child is added to a noncompliant parent. |
| I. Function limits | Pass | `_invites` stays under 25 lines and under five logical blocks after T009 and T011. |
| II. Class-based design | Pass | `_invites` stays a static method of `OrgExportUtils`. No wrapper is added. |
| III. Safety first | Pass | The change adds no input handling and no destructive operation. |
| IV. Deployment pipeline | Pass | T-LOCAL-GATES covers step 1. T-PR covers steps 2 to 7. T-REMOTE-CI covers step 8. T-MERGE covers steps 9 to 12. |
| V. ASCII logging | Pass | The new log text uses ASCII only. |
| VI. Inline comments | Fail on main, pass after T010 | GitHub main lines 727, 728, 729, 730, and 734 have no inline comment. |
| VII. Action logging | Fail on main, pass after T011 | GitHub main lines 733 to 735 have no INFO record before the shared export call and no DEBUG record after it. |
| Mist Cloud: mistapi only | Pass | No HTTP request is added. |
| Python 3.15 | Pass | `pyproject.toml` line 23. |
| Podman and compose group | Not applicable | No container runs for this change. |
| Windows paths | Pass | The change touches no path. |
| Output backends | Pass | The change keeps the shared export call. The shared export owns the output backends. The backend path is not traced in this record. |
| Primary key strategy | Pass with latent gap | The absent path writes no row. Analysis item A-3 tracks the future write path. |
| Security findings | Pass | The change adds no suppression. The existing suppression stays under decision D-7. |
| Release note | Pass | `changelog.d/issue-4825-org-invites.md` exists on GitHub main. No new fragment is added for this internal-only change. |
| README | Not applicable | No menu, command, or operator behavior changes. |
| Escalation to a spec | Pass | The change touches three or more files. This record exists. |
| Branch from main | Pass | The follow-up branch starts from GitHub main. The merged branch is not reused. |
| File overlap | Pass | Seven open pull requests touch none of the target files. The check ran on 2026-11-26. |
| Claim the issue | Open | T015 adds the `in-progress` label before the branch exists. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      invites-export.md
    checklists/
      requirements.md
      constitution.md
```

### Source Code (repository root)

File change map:

| Path | Action | Requirements | Tasks |
| - | - | - | - |
| `src/operations/exporting/export/org_export_utils.py` | Modify `_invites`, lines 717 to 735 | FR-007, FR-008, FR-009 | T009, T010, T011 |
| `tests/unit/export/test_org_export_utils.py` | Modify the absent-path test at lines 976 to 986. Add a log-order test to class `TestSimpleDelegates` | FR-002, FR-004, FR-007, FR-011 | T007, T008 |
| `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md` | Remove line 68 | FR-010 | T012 |
| `documentation/api/orgs/POST_orgs_org_id_invites.md` | Remove line 296 | FR-010 | T013 |
| `documentation/api/orgs/PUT_orgs_org_id_invites_invite_id.md` | Remove line 295 | FR-010 | T014 |
| `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/` | Replace the three legacy files. Add `analysis.md` and the `design/` files | All | T016 |
| `changelog.d/issue-4825-org-invites.md` | No change | None | None |

Files added: `analysis.md` and the `design/` folder in the record. Files deleted: none.

### Dependencies

No new dependency is added. The local gates in `.github/copilot-instructions.md` name every tool that this change uses.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A later mistapi release adds `listOrgInvites` with another contract. The supported path would run unverified. | Write a contract test before the pin moves. Decision D-1. |
| A later write path uses the default primary key strategy. | Add an entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` before the path ships. Decision D-9. |
| `_invites` has no caller. A defect in it has no operator impact. | Keep the method for now. A follow-up issue decides on removal. Decision D-3. |
| The new log lines change the test output. | The focused test file runs in T-LOCAL-GATES. |
| A future generator run rewrites a corrected page. | The generator skips pages without placeholder text. Decision D-8. |
| Warning: A push to a merged branch creates an orphan pull request. | Use the new branch name. Decision D-10. |

## Rollback Steps

1. Create a branch from GitHub main. Revert the follow-up commit on that branch. Open a pull request. The revert restores the earlier text of the three pages and the earlier `_invites` body.
2. Keep pull request #4829 in place unless the guard must go. Caution: Reverting pull request #4829 restores the `AttributeError` on the absent path.
3. Warning: Do not force-push to GitHub main. A force push rewrites history that every user shares.

## Complexity Tracking

Not applicable. No constitution rule requires a violation. The `# type: ignore[no-untyped-call]` comments were already in the module before this issue. They are existing debt. Decision D-7 tracks them, and this change adds none.
