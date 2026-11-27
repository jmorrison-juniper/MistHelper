# Implementation Plan: Refuse a Checked Device Type With No Target Version

**Branch**: `fix/3394-multi-site-empty-version` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric record route `specs/numbered/0/0/1/0/2/0/3/4/3394-multi-site-empty-version/`. The eight base-5 digits of 3394 are 0, 0, 1, 0, 2, 0, 3, 4. The route function is at `.specify/scripts/powershell/spec-route.ps1:4-17` [RC70, RC71].

## Summary

The multi-site save drops every device of a checked device type when that type has no target version. This plan adds one refusal. The save returns HTTP 400 with the existing code `org_upgrade_options_invalid`. The text names the device type and its target version control. The check runs inside `_selected_target_rows` after the target rows are chosen. The check is a new static method on the existing class `OrgOptionRefusal`. No template, JavaScript, or documentation file changes. Tests replace the xfail test, add five contract tests, and add one browser test.

## Technical Context

- **Language/Version**: Python 3.15 or newer [RC87].
- **Primary Dependencies**: The Flask upgrade portal routes in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. The pinned mistapi 0.64.1 [RC79]. Playwright for the browser test, imported through `pytest.importorskip` [RC92].
- **Storage**: None added or changed. The plan write stays in `_write_operation` [RC30].
- **Testing**: Contract tests in `tests/contract/upgrade_portal/test_org_upgrade_routes.py` [RC51, RC53, RC54]. Browser test in `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` [RC98]. Changelog guard in `tests/guardrails/test_changelog_fragment_policy.py` [RC56].
- **Target Platform**: The Flask upgrade portal. The change runs on Windows and on Linux.
- **Project Type**: Server-side validation change with tests. No new module and no new package.
- **Performance Goals**: No added cloud request. The check reads the device view that the save already reads [RC31, RC36].
- **Constraints**: The refusal runs before the plan write [RC30] and before the browser session write [RC29]. New code follows the five-item and class rules in the Constitution Check.
- **Scale/Scope**: Three changed files and one added fragment. About 25 lines of code and about 150 lines of tests.

## Constitution Check

The gate passes for new code. Existing debt is recorded below and in the Complexity Tracking table.

| Rule | Verdict | Reason |
| - | - | - |
| I. Five-Item Rule [RC59, RC81, RC82] | Pass for new code. Existing debt recorded. | `org_upgrade.py` defines 147 top-level names [RC81]. The `upgrade` package holds 22 children [RC82]. The change adds one method to the existing `OrgOptionRefusal` class and no top-level name. It adds no child to the package. |
| II. Class-Based Architecture [RC83] | Pass | The check is a static method on an existing class. No wrapper function is added. |
| III. Safety-First [RC94] | Pass | The check runs before the plan write [RC30] and before the browser session write [RC29]. The change adds no default target version. |
| IV. Full Deployment Pipeline [RC93] | Pass as planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step in order. |
| V. Observability and Logging [RC84] | Pass as planned | The refusal text is ASCII (FR-003). Log lines hold no device address (FR-012). |
| VI. Inline Comments [RC60] | Pass as planned | FR-014 and task T011 check each changed line. |
| VII. Action Logging [RC61] | Pass as planned | FR-012 requires an info line before the check, a debug line after it, and a warning on refusal. |
| Mist Cloud REST through mistapi | Pass | No REST request is added [RC31, RC36]. |
| Mist Cloud owned transport | Not applicable | No WebSocket transport is added. |
| Operational store | Not applicable | No store changes. |
| Data directory | Pass | The change writes no product output. |
| Test containers | Not applicable | No container starts for this change. |
| File paths | Pass | The change builds no path string. |
| README update [RC62] | Pass with reason | The README has no text about the multi-site page [RC78]. No README statement becomes false. Decision D-11. |
| Release-note fragment [RC57, RC58] | Pass as planned | FR-011 and task T009. |
| Audience standard | Pass as planned | The refusal text is plain and names one control (D-5). |
| SpecKit escalation [RC63] | Pass | The change touches three files. This record exists. |
| Branch naming [RC85, RC88] | Pass | The branch is `fix/3394-multi-site-empty-version` and starts from `main`. |
| Required labels [RC86] | Pass as planned | Type `bug`. Scope `web-portal`. Status `in-progress` while the work runs. |
| Testing rules [RC90] | Pass as planned | Tests T001 to T007 come before the code change T008. Each test must fail first. |
| Secrets [RC91] | Pass | The change reads and logs no secret. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/2/0/3/4/3394-multi-site-empty-version/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      options-refusal.md
    checklists/
      requirements.md
      safety.md
```

The route parent `specs/numbered/0/0/1/0/2/0/3/` holds one child today [RC10]. The change adds one child, `4`, so the parent holds two children. The feature root holds five children, and `design/` holds five children.

### Source Code (repository root)

The change map below lists every changed path. No other path changes.

**Structure Decision**: Change one existing module and two existing test modules. Add one changelog fragment. Add no module, no package, and no top-level name (D-6).

## Change Map

| Path | Action | Change | Evidence |
| - | - | - | - |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | Modify | Add the static method `OrgOptionRefusal.require_family_versions` after `whole_number`. That function ends at line 406. Change `_selected_target_rows` at lines 775-792 so it calls the method once and then returns one result. | RC18, RC19, RC21, RC22, RC23, RC24 |
| `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | Modify | Replace the xfail test at lines 65-98 with test T001. Add tests T002 to T006 after line 98. | RC51, RC52, RC99, RC101, RC102, RC103, RC105 |
| `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` | Modify | Add test T007 inside class `TestOrganizationUpgradeBrowserFlow` at line 47, after the method that starts at line 50. | RC98, RC55, RC92 |
| `changelog.d/issue-3394-multi-site-empty-version.md` | Add | One `###` heading and one `Fixed` bullet that names issue #3394. | RC11, RC57, RC58 |

No path is deleted. No template, JavaScript file, or documentation file changes (FR-013).

## Design of the Check

The new static method on `OrgOptionRefusal` takes three inputs. The inputs are the device rows of one site, the checked device types in form order, and the planned rows from `_selected_target_rows`.

1. Map each device address in the site view to its device type.
2. Collect the checked device types that have at least one device in the site view.
3. Collect the device types of the planned rows, using the address map from step 1.
4. For each checked type in form order, skip a type with no device. Otherwise, require one planned row for it. If no row exists, log a warning and raise `ValueError` with the FR-003 text.
5. Log a debug line after the loop finishes.

The method keeps a local table from device type to two words. The table holds `ap` as "access point" and "Access points", `switch` as "switch" and "Switches", and `gateway` as "gateway" and "Gateways" [RC46]. An unlisted type uses its own name for both words.

`_selected_target_rows` keeps its two branches. The explicit branch uses the version map [RC22, RC24, RC25]. The type-wide branch uses the type field [RC23]. After either branch, the function calls the method with `view.get("targets", [])`, `selected`, and the chosen rows. Then it returns the rows. The method uses `isinstance` checks, so a non-list view value cannot raise an error [RC25].

The `ValueError` leaves `save_options` through the existing `(TypeError, ValueError, OverflowError, RuntimeError)` clause. That clause returns HTTP 400 with the code `org_upgrade_options_invalid` and the text of the error [RC28, RC17]. The save then stops before `_write_operation` [RC30] and before the browser session write [RC29].

The method has three parameters, at most five logical blocks, and at most 25 lines. Task T011 checks the complexity with `radon cc`.

## Dependencies

- No package changes. The pinned mistapi 0.64.1 stays inside `>=0.64.0,<0.65` [RC79].
- No open pull request overlaps the five changed paths. Seven open pull requests were checked on 2026-11-26. The check repeats at task T-PR.
- No open issue must land first. Issue #3393 remains open, but its code change merged in PR #4413. It is related, not a dependency.

## Risks and Mitigations

- **R1**: An operator sets every device of one type to "Do not upgrade this device" at one site, and the save is refused. Mitigation: the text names the type. The operator clears that type box for the plan.
- **R2**: The text names no site. The operator finds the site through the device tables on the page. This residual risk is accepted (D-5).
- **R3**: The browser test depends on the seeded e2e data. Mitigation: verify the seeded site and switch mapping before T007 runs. The item is listed as unverified U1 in `design/research.md`.
- **R4**: The symbol gate reports the renamed test function. Mitigation: task T010 records the reported name. The pull request explains the rename.

Warning: do not add a default target version for a checked device type that has none. A default can upgrade a switch that the operator did not choose. The issue states this risk.

## Rollback Steps

1. Revert the squash commit on `main`. The commit holds the three changed files and the fragment.
2. Confirm that the fragment leaves with the revert.

Caution: a revert restores the silent drop of a checked device type. Record the restoration in the issue and open a new issue if the defect must return to the queue.

## Complexity Tracking

Existing debt is recorded below. This change adds no debt.

| Violation (existing) | Evidence | Why this change adds no violation |
| - | - | - |
| `org_upgrade.py` defines 147 top-level names | RC81 | The new check is a method on an existing class. No top-level name is added. |
| The `upgrade` package holds 22 children | RC82 | No child is added. The check uses no new module. |

Remediation action (separate issue, not part of this change): split `org_upgrade.py` and the `upgrade` package to satisfy the five-item rule. The remediation tracks as its own incremental action.

## Mist Cloud Check

- REST calls added: none [RC31, RC36].
- The `getOrgInventory` path stays unchanged. The OpenAPI file defines that path at line 10639 [RC77]. The GET endpoint table lists the same method [RC75]. The missing-endpoint list does not name it [RC76].
- No owned WebSocket transport is added.
