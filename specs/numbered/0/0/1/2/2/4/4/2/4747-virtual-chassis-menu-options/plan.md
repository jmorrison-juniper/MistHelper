# Implementation Plan: Virtual Chassis Menu Guidance

**Branch**: `fix/4747-virtual-chassis-menu-options` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification route `specs/numbered/0/0/1/2/2/4/4/2/4747-virtual-chassis-menu-options/`. The route digits are base-5 digits of 4747, padded to eight digits (RC-53).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`.

## Summary

Three printed lines name the wrong menus. Thirteen more module lines and two root test lines name stale menus. This plan replaces each stale number with the registered number. It adds four offline tests first and confirms that they fail. Then it changes the text only. No API call, confirmation, registry category, or menu entry changes.

## Technical Context

- **Language/Version**: Python 3.15 or newer (RC-64, RC-72).
- **Primary Dependencies**: mistapi 0.64.1, within the pin `>=0.64.0,<0.65` (RC-88). No dependency changes.
- **Storage**: Not applicable. The change writes no data.
- **Testing**: pytest, with the commands in `design/quickstart.md` and the local gates table (RC-60).
- **Target Platform**: Windows 11 local development, macOS, and Linux (RC-65).
- **Project Type**: Command-line menu application. `MistHelper.py` holds the menu table (RC-20).
- **Performance Goals**: Not applicable. The change alters printed text only.
- **Constraints**: The module keeps its line count. Tests run offline. Printed output stays ASCII (RC-69).
- **Scale/Scope**: Three modified repository files and one added changelog fragment.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule (RC-66) | Pass with grandfathered debt | The change adds no child at any level. The module already declares more than five top-level names (RC-18). `VirtualChassisManager` already holds more than five methods (RC-19). Both debts are recorded in Complexity Tracking. The new test methods stay in classes with five or fewer members (D-3). |
| Principle II, class-based design | Pass | The change adds no function. The four tests are methods in existing test classes. |
| Principle III, safety-first (RC-67) | Pass | The typed `CONVERT` checks at lines 380 and 868 stay unchanged (RC-16, RC-17). The new tests call no API. |
| Principle IV, full deployment pipeline (RC-68) | Pass by plan | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE carry each pipeline step. Their proof arrives in those tasks. |
| Principle V, ASCII output (RC-69) | Pass | Every new string uses ASCII characters only. |
| Principle VI, inline comments (RC-70) | Pass | Each changed executable line keeps its WHY comment. Each new test line carries a comment. |
| Principle VII, action logging (RC-71) | Pass with reason | The changed usage-note helper prints text. It performs none of the actions that Principle VII lists. The conversion success helper keeps its existing audit log. |
| Technology constraints (RC-72) | Pass | The change adds no dependency and uses no new language feature. |
| Mist Cloud transport | Not applicable | The change adds no request and changes no request (spec, Mist Cloud section). |
| Output backends, operational store, export boundary, database keys, data directory | Not applicable | The change exports no data and writes no product output. |
| Container runtime and test containers (RC-76) | Not applicable | The change starts no container. All tests run on the host. |
| Destructive operations (registry rows RC-34 and RC-35) | Pass | Menus 161 and 162 keep the destructive category. No menu operation is added or removed. |
| Documentation (README for behavior changes) | Pass | The change alters printed guidance only. The README has no virtual chassis menu text (RC-78). The changelog fragment is added (FR-011). |
| Multi-agent git workflow (AGENTS.md) | Pass by plan | The issue exists. T001 adds the `in-progress` label. The branch is `fix/4747-virtual-chassis-menu-options`. The commit and pull request titles use Conventional Commits. The pull request body contains `Closes #4747`. |
| Labels | Pass | The issue has the type label `bug` and the scope label `MistHelper.py`. T001 adds `in-progress`. |
| Specification escalation (constitution Speckit section) | Pass | The change touches three files. This record is the required specification. |

## Architecture

The three affected paths start in `MistHelper.py` and call `VirtualChassisManager`.

1. **Single conversion, menu 161.** The menu entry at `MistHelper.py` line 5369 (RC-25) launches the single conversion. The execute helper calls the convert endpoint at `virtual_chassis.py` line 477 (RC-14), then calls the response handler at line 480 (RC-13). The response handler returns at line 496 on an HTTP or detail error (RC-89). Otherwise it prints the rollback guidance through the success helper defined at line 533 (RC-11).
2. **Bulk conversion, menu 162.** The menu entry at line 5377 (RC-26) launches the bulk conversion. The API helper calls the convert endpoint at line 588 (RC-15). That helper does not call the success helper.
3. **Status check, menu 14.** The menu entry at line 5387 (RC-27) launches the status check. The check calls the usage-note helper at line 250 (RC-12). The helper prints the menu 161 and 162 notes at lines 420 and 421 (RC-06, RC-07).

The registry (RC-30 to RC-36) and the menu table (RC-22 to RC-27) are the source of truth for every menu number that the guidance prints.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/4/2/4747-virtual-chassis-menu-options/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      vc-menu-guidance.md
    checklists/
      requirements.md
      safety.md
```

### Source Code change map (repository root)

| Action | Path | Change |
| - | - | - |
| Modify | `src/mist/resources/device/virtual_chassis.py` | Replace the menu numbers in three printed lines (lines 420, 421, 540) and in the WHY comments of lines 420 and 421. Replace the stale numbers in 13 comment or docstring lines (7, 81, 82, 83, 84, 96, 111, 116, 135, 153, 182, 206, 231). Each change replaces one line, so the line count stays the same. |
| Modify | `tests/unit/test_virtual_chassis.py` | Add `import re` and `from pathlib import Path` to the import block. Add three methods to `TestCheckStatus` (RC-39) and one method to `TestHandleConversionResponse` (RC-40). |
| Modify | `tests/test_virtual_chassis.py` | Replace `option 92` with `menu 161` in the docstring (line 1) and in the comment (line 9) (RC-44, RC-45). |
| Add | `changelog.d/issue-4747-virtual-chassis-menu-options.md` | One fragment with one `###` heading and one `Fixed` bullet that names issue #4747 and the old and new numbers. |

Unchanged paths: `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `CHANGELOG.md`, `documentation/menu-api/`, `documentation/wiki/`, `documentation/menu_reference.md`, and every `specs/` folder except this record.

## Dependencies

- mistapi 0.64.1 in the local `.venv` (RC-86 to RC-88). No change.
- pytest and the gate tools that `tasks.md` names.
- The `misthelper-devtools` tools `symbol-diff`, `ste-linter`, `test-quality-analyzer`, and `complexity-gate` (RC-62, RC-63).
- The venv interpreter `.venv\Scripts\python.exe` for local commands (RC-74).

## Implementation Outline

1. T001 confirms the anchors and checks for file overlap. No edit occurs.
2. T002 adds the four tests and runs them. All four must fail on the unchanged source.
3. T003 changes the three printed lines and their two WHY comments. The status and success tests then pass.
4. T004 changes the 13 comment and docstring lines. The static test then passes for the module.
5. T005 changes the two root test lines. The static test then passes for the root test.
6. T006 adds the changelog fragment.
7. T-LOCAL-GATES runs each applicable gate. T-PR, T-REMOTE-CI, and T-MERGE follow after authorization.

## Complexity Tracking

| Violation | Status | Why Needed | Simpler Alternative Rejected Because | Remediation |
| - | - | - | - | - |
| `virtual_chassis.py` declares more than five top-level names, starting at line 38 (RC-18) | Grandfathered. The change edits text only. | The module predates this change. | Splitting the module changes operator imports and the line numbers in test names. | A separate issue splits the status and conversion helpers into compliant modules. |
| `VirtualChassisManager` holds more than five members, starting at line 102 (RC-19) | Grandfathered. The change adds no member. | The class predates this change. | A split inside this issue widens the change beyond the defect. | The same separate issue. |
| The unit test module declares more than five test classes, starting at line 116 (RC-43) | Grandfathered. The change adds no class. | The layout predates this change. | A new class or module adds a child to a noncompliant parent (D-3). | A separate issue splits the test module by domain. |

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Operators follow the old numbers from saved reports. | The changelog names both numbers. The spec states the Caution (D-1). |
| Importing `MistHelper` at module level changes the mistapi stub order. | The registry test imports `MistHelper` inside the method (D-4). The guard test already imports `MistHelper` at module level (RC-46). |
| The static regex gives a false result. | The pattern requires a menu or option word followed by 92, 93, or 94 within 20 characters. The test runs red before the fix and green after it (D-13). |
| A line insertion above line 184 shifts the line numbers in test names (RC-42). | Each edit replaces one line. The diff shows equal added and deleted line counts for `virtual_chassis.py`. |
| Generated menu pages drift. | T-LOCAL-GATES runs the menu reference commands. The generator reads `MistHelper.py` and the registry, and the scanner reads no comments (D-9, RC-80, RC-81). |
| Another open pull request changes a target file. | T001 repeats the overlap check. Research found no overlap (RC-51). |
| The pull request merges without human review. | The `auto-merge` label stays off (D-11). |
| A test starts a destructive path. | The tests call output helpers only. Neither helper calls the API (FR-008). |
| The changelog fragment breaks the style rule. | The STE gate checks the fragment in T006. |
| The test classes exceed five members. | Counts are checked in T002. `TestCheckStatus` reaches five and `TestHandleConversionResponse` reaches four (D-3). |
| Bulk operators expect rollback guidance. | This issue does not add it. The gap is recorded for a separate issue (D-14). |

## Rollback Steps

1. Before merge, close the pull request, push a recovery branch if the work must survive, and delete the `fix/4747-virtual-chassis-menu-options` branch.
2. After merge, do not push to the merged branch. Open a new issue, branch from `main`, and revert the commit (AGENTS.md, Merge section).
3. The change writes no data and changes no state. A revert restores the old printed numbers and needs no data recovery.
