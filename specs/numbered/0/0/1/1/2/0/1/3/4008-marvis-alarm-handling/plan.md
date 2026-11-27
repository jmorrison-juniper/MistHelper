# Implementation Plan: Isolate Marvis Alarm Handling Modules

**Branch**: `chore/4008-marvis-alarm-handling` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. Omit `design/contracts/`, because no contract applies. See the Contracts section.

## Summary

Move two Marvis alarm modules into the child package `alarm_handling`. Update each active import, each test patch target, and each active documentation path to the canonical module. Add one structure test and two symbol-guard mappings. Remove the stale nested-ratchet entry. The move keeps behavior and module-level names unchanged.

## Technical Context

**Language/Version**: Python 3.15 or newer. See research R30.

**Primary Dependencies**: `mistapi` 0.64.1, the only Mist REST interface. The copilot instructions pin `>=0.64.0,<0.65`. The installed version is 0.64.1. See research R30 and R60.

**Storage**: No change. The alarm join reads Mist data in memory. The export writers are not edited.

**Testing**: Focused pytest modules, the pytest guardrails, and the local gates in `design/quickstart.md`.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python command-line tool with a web dashboard.

**Performance Goals**: No change. The move adds no request, loop, or cache.

**Constraints**: No behavior change. No alias or shim at an old path. No new Mist API call.

**Scale/Scope**: Two modules move, one package file is added, and 16 repository files change. Two generated files change only when their content changes. The record holds 13 requirements and 17 tasks.

## Constitution Check

*Gate: must pass before implementation. Re-check after the move.*

| Rule | Verdict | Reason |
| - | - | - |
| I. Five-Item Rule, directory children | Pass | The actions package holds five children and `alarm_handling` holds two after the move. See research R01 and R04. |
| I. Five-Item Rule, route parents | Pass | Each route parent holds five children or fewer. The route reuses existing child `2` at depth five. See research R64. |
| I. Five-Item Rule, function limits in touched modules | Fail, pre-existing | `_send_batches` holds 28 lines, and `apply` holds 29 lines. The limit is 25 lines (research R88). The move keeps the text. See the touched-debt table. |
| I. Five-Item Rule, module top-level names | Fail, pre-existing | `acknowledgement.py` holds 7 names, `alarms.py` holds 6, and `operation.py` holds 25. The limit is 5 (research E-6). The move adds no name. |
| II. Class-based architecture, no wrappers | Pass | The change adds no wrapper function and no alias module. See research R78 and D-1. |
| III. Safety-first | Pass | The acknowledge confirmation and the batch size stay unchanged. See research R79. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the numbered steps (research R80). Publication waits. See FR-011. |
| V. ASCII logging | Pass | Neither moved module holds a non-ASCII line. See research R81 and E-7. |
| VI. Inline comments | Pass | The moved modules keep their WHY comments (research R82). The new `alarm_handling/__init__.py` holds one docstring line and no executable line. |
| VII. Action logging | Pass | The log statements in the moved modules do not change (research R83). |
| Mist SDK as sole REST interface | Pass | No HTTP call is added (research R84). See research R08, R09, R58, and R59. |
| Podman and test containers | Not applicable | The change starts no container (research R85 and R86). |
| Data directory and output backends | Not applicable | The change alters no export path, column, or write (research R87). |
| Release notes | Pass | One fragment names issue 4008. See research R35 and D-7. |
| Documentation | Pass | The active documentation row changes. See research R17. |
| Audience standard | Pass | No user-facing text changes (research R89). |
| SpecKit escalation | Pass | The change touches more than three files and two classes, so this record exists (research R90). |
| Multi-agent Git | Pass with hold | A fresh branch starts from main in a new worktree (research R91). Publication waits for PR #4208. See FR-011 and D-3. |

## Architecture

The actions package holds six direct modules before the move. After the move it holds five children: four modules and one package.

```text
src/mist/intelligence/marvis/actions/
  __init__.py            docstring names alarm_handling (edit)
  client.py              unchanged, all Mist API calls
  model.py               unchanged, record builder and catalogs
  operation.py           import lines change (edit)
  selection.py           unchanged, filter answers and prompts
  alarm_handling/
    __init__.py          docstring only (new)
    acknowledgement.py   moved, content unchanged
    alarms.py            moved, content unchanged
```

The call path stays the same. Menu 270 enters `MarvisActionsOperation` in `operation.py`. The export calls `MarvisAlarmJoin.apply` at `operation.py` line 619 (research R07). The resolve workflow imports the acknowledger from `alarm_handling/acknowledgement.py` (research R05). Both moved modules receive the client in their constructors (research R97 and R98). The client makes the Mist API calls (research R08 and R09).

## File-by-file change map

| Path | Action | Lines or scope | Requirement |
| - | - | - | - |
| `src/mist/intelligence/marvis/actions/acknowledgement.py` | Rename to `alarm_handling/acknowledgement.py` | Content unchanged. Blob `765c01070ebdf0d79580af464441f9f44e3c34fb`. | FR-001, FR-004 |
| `src/mist/intelligence/marvis/actions/alarms.py` | Rename to `alarm_handling/alarms.py` | Content unchanged. Blob `c61405c839212c6c64c5cbd8c07cd2e582cd4287`. | FR-001, FR-004 |
| `src/mist/intelligence/marvis/actions/alarm_handling/__init__.py` | Add | One docstring line. No re-export. | FR-001, FR-002 |
| `src/mist/intelligence/marvis/actions/operation.py` | Modify | Lines 51 and 57 (research R05, R06). | FR-003 |
| `src/mist/intelligence/marvis/actions/__init__.py` | Modify | Docstring lines 4 to 7 name the alarm modules (research R70). | FR-003 |
| `tests/unit/marvis/actions/test_acknowledgement.py` | Modify | Line 7 import and lines 30, 43, and 58 patch targets (research R10 and R11). | FR-003 |
| `tests/unit/marvis/actions/test_alarms.py` | Modify | Lines 18 and 19 (research R12 and R13). | FR-003 |
| `tests/unit/marvis/actions/test_operation.py` | Modify | Line 20 (research R14). | FR-003 |
| `tests/unit/marvis/actions/test_model.py` | Modify | Line 15 (research R15). | FR-003 |
| `tests/unit/marvis/actions/test_properties.py` | Modify | Line 25 (research R16). | FR-003 |
| `tests/guardrails/test_src_domain_structure.py` | Modify | Add one test before line 120 (research R66). | FR-002, FR-010 |
| `tests/guardrails/test_src_public_symbol_preservation.py` | Modify, held by PR #4208 | Add two `MODULE_PATHS` entries after line 36 (research R20 and R65). | FR-004, FR-011 |
| `tests/guardrails/nested_package_baseline.json` | Modify | Delete lines 91 to 95 (research R18). | FR-008 |
| `tests/guardrails/test_nested_package_structure.py` | Modify | Line 177 expected message (research R19). | FR-008 |
| `documentation/marvis-actions-api-endpoints.md` | Modify | Line 1329 path (research R17). | FR-006 |
| `changelog.d/issue-4008-marvis-alarm-handling.md` | Add | One heading and one Changed bullet. | FR-009 |
| `documentation/menu-api/interactive-safe.md` | Regenerate only if content changes | Expected unchanged. The row cites `client.py` (research R63). | FR-007 |
| `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` | Regenerate only if content changes | Expected unchanged, because it repeats the same client rows. | FR-007 |

## Touched existing violations

| File | Construct | Measured | Limit | Remediation |
| - | - | - | - | - |
| `acknowledgement.py` | `_send_batches`, lines 72 to 99 | 28 lines | 25 lines | Remediation child issue under #3824 |
| `alarms.py` | `apply`, lines 193 to 221 | 29 lines | 25 lines | Remediation child issue under #3824 |
| `acknowledgement.py` | Module top-level names: 2 classes, 1 logger, 4 constants | 7 names | 5 | Remediation child issue under #3824 |
| `alarms.py` | Module top-level names: 2 classes, 1 logger, 3 constants | 6 names | 5 | Remediation child issue under #3824 |
| `operation.py` | Module top-level names: 6 classes, 1 logger, and the constants and functions | 25 names | 5 | Remediation child issue under #3824 |

The remediation child issue is filed before the pull request, and the pull request body names it (task T-PR). The debt rows change no code in this move.

Method: a function spans from its `def` line to its last statement line. Top-level names are classes, functions, and module-level assignments. Imports are not counted. Local blobs equal the main blobs (research R02, R03, and R05), so the same lines apply on main.

### Function and parameter counts of the moved modules

| Module | Functions | Maximum parameters, excluding `self` or `cls` | Functions over 25 lines | Maximum logical blocks |
| - | - | - | - | - |
| `acknowledgement.py` | 6 | 3 in `__init__` | 1, `_send_batches` at 28 lines | 3 in `_send_batches` |
| `alarms.py` | 10 | 3 in `_keep` | 1, `apply` at 29 lines | 3 in `_seen` |

The limit of five operations per statement block is not counted. No local gate reports it. See the Unverified list in research.

## Dependencies

- `mistapi` 0.64.1 is installed. The move changes no dependency (research R60).
- PR #4208 is open and holds the symbol guard file (research R44).
- PRs #4557 and #4607 are merged. They changed guard files and Marvis action tests on main. The fresh branch starts from current main, so it includes those changes (research Linked work).
- Parent issue #3824 receives the remediation child issue for the touched debt.

## Logger and class module path change

Both moved modules call `logging.getLogger(__name__)` (research R71 and R72). Their logger names change from `src.mist.intelligence.marvis.actions.alarms` to `src.mist.intelligence.marvis.actions.alarm_handling.alarms`, and the acknowledgement module changes the same way. The class `__module__` values change too. The move-a-module section of the copilot instructions names the gates that apply (research R29). The pull request body repeats the change (FR-005). No test, config, or log filter names the old logger (research E-3).

## Risks and mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The symbol guard file stays held by PR #4208 | Publication stalls | Wait for the release or a file-scoped handoff (FR-011, T002, T010). |
| A call site keeps an old import path | An import fails at run time | Run the import smoke check, the old-path search, and the focused tests (T004, T008). |
| The nested ratchet counts untracked files | The ratchet reports a false failure | Stage the moved files by explicit path before the ratchet run (T011). |
| The expected ratchet message is stale | The guard fails | Run the ratchet and update the message to 32 and 235 (T011). |
| A rebase drops a mapping in the held guard file | A module loses its symbol proof | Caution: compare the held file with main after each rebase. |
| Unrelated edits sit in the shared checkout | Wrong files reach the pull request | Use a new worktree (T001). Never stage the five unrelated files. |
| The 1,000 batch-size comment is not confirmed | Documentation claim is wrong | Make no edit to the comment. The claim stays listed as Unverified. |

## Rollback steps

1. Before publication, remove the worktree and delete the local branch. The archive branches keep the candidate content.
2. After publication and before merge, close the pull request without merging. Keep the branch as an archive.
3. After merge, open a new pull request that reverts the squash commit.

Warning: a force push to `main` removes commits that other agents depend on. Do not force-push `main`.

## Contracts

Not applicable: the change alters no menu, no command-line option, no output column, and no API request or response shape. The folder `design/contracts/` is omitted for that reason.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
      structure.md
      publication.md
```

### Source Code (repository root)

The source layout appears in the Architecture section. The test layout is unchanged except for the five test modules listed in the change map.
