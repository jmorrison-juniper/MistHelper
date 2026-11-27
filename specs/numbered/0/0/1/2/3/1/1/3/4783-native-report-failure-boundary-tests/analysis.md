# Analysis: Native Report Failure-Boundary Tests

## Scope of Review

This review compares `spec.md`, `plan.md`, `tasks.md`, and the design files with the remote and local evidence in `design/research.md`. It covers the defects in the existing chain, the unresolved items, and the structure and style of this record.

## Requirement Traceability

| Requirement | Tasks | Planned test or check | Evidence | Status |
| - | - | - | - | - |
| FR-001 | T003, T004 | Empty raw reply, both formats | R17, R18 | partial |
| FR-002 | T003, T004 | Same cases, `b""` at the decoder | R17, R18, R22 | partial |
| FR-003 | T003, T006 | Normalizer cause assertion | R18, R37 | partial |
| FR-004 | T005 | Report malformed JSON, one failed source | R16 | partial |
| FR-005 | T004 | Report empty refusal, no file | R17 | partial |
| FR-006 | T002, T004, T005 | Source-driving helper and raw decoder | R33 to R35 | partial |
| FR-007 | T007 | Contracts `is True` assertion | R19 | partial |
| FR-008 | T-LOCAL-GATES, T-REMOTE-CI | Both analyzer scopes | R06, R07 | open |
| FR-009 | T012, T-LOCAL-GATES | Blob SHA check | R04, R05 | open |
| FR-010 | T012 | Source path check on the fix commit | R21 | open |
| FR-011 | T002, T007, T008 | `git grep ReportRun` returns no line | R16 | absent |
| FR-012 | T010 | Line and parameter count | none (new code) | open |
| FR-013 | T010 | Manual review of changed lines | none (new code) | open |
| FR-014 | T001, T-PR, T-MERGE | GitHub reads and decision D-2 | R28 to R31 | absent |
| FR-015 | T009, T-PR | Changelog fragment policy test | none (new file) | absent |
| FR-016 | T011 | Follow-up text | R15, R35 | open |

Each FR has at least one task and at least one check. The planned pytest cases total seven. They match `plan.md`.

## Findings in Existing Work

- **F-1: Marker-only empty bytes.** At the chain tip, `test_normalization.py` line 83 and `test_report.py` line 85 decode `b""` to an empty string (R17, R18). The detector sees the marker. No boundary is exercised. Resolution: T003 and T004, decision D-3.
- **F-2: Precondition outside the coverage source.** `test_report.py` line 96 at the chain tip checks that the malformed text fails as JSON. The test calls `ReportRun.create`, so the check is not in the coverage source. Resolution: T005 and decision D-4. The precondition stays as fixture validation.
- **F-3: Class staticmethod invisible to the detector.** `ReportRun` at line 37 holds the only setup path. The detector bridges only module-level helpers (R35). Resolution: T002, decisions D-1 and D-5.
- **F-4: Stale issue text.** The #4773 body names PR #4607 as the current owner of `MistHelper.py`. PR #4607 merged on 2026-11-13. The owner of #4773 should update the text. This record makes no change to #4773.
- **F-5: Two names for one rule.** The emitted rule is `weak_bare_assert` (R41). The settings key is `weak_bare_truthy` (R42). Both names are correct for their roles. The record uses each name in its own role.
- **F-6: Six children in the test folder.** `tests/unit/websocket_streams/web/hardware/` holds six children on the chain (R15). Constitution Principle I allows five. The chain adds the sixth child. Resolution: FR-016 follow-up. This change does not fix it.
- **F-7: Commits not on GitHub.** The issue comment cites commits `58ab484` and `07cf3ee`. GitHub does not return them (R28 to R31). The issue thus rests on local-only evidence. Resolution: T001 and decision D-2.
- **F-8: Base far behind main.** The chain base is 73 commits behind main. Main changed `documentation/operator-guide.md` after the base, and the chain also changes that file. Resolution: T-PR rebases in a worktree, and T-LOCAL-GATES reruns after the rebase.
- **F-9: Unverified owner figures.** The owner comment reports 358 passing tests and 93.98 percent hardware coverage. This record does not verify them (U11).

## Consistency Checks

- **Spec and plan.** FR-011 matches the file map in `plan.md`, which renames the class in three files.
- **Plan and tasks.** The seven planned cases map to T003, T004, and T005. T006 keeps the chain-tip cause assertion, and it adds no case.
- **Tasks and quickstart.** T-LOCAL-GATES names the order in `quickstart.md` Scenario 4. The order matches the list in that scenario.
- **Research and spec.** Each row number that `spec.md` and `plan.md` cite exists in the table of `research.md`.
- **Constitution and plan.** The plan's constitution table lists Principles I to VII. Principle I records the six-child folder as a recorded failure, as Principle I requires for touched violations.
- **Fragment rule.** `copilot-instructions.md` limits the changelog fragment to user-visible changes. The constitution requires one fragment per change. The constitution controls, because it names itself the authority over the repository rules. The record follows the constitution and adds the fragment (FR-015).
- **Branch naming.** The issue carries the `bug` label, so the branch type is `fix`. `AGENTS.md` allows a more precise commit type. The commit uses `test(websocket)`.
- **Verification commands.** Tasks T001, T009, T011, T012, T-PR, T-REMOTE-CI, and T-MERGE use a remote read or a command outside the local gate table. Each task names its command, and the reason is in the task.

## Structure and Style Review

- **Child limits.** The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`. The `design` folder holds four children. The `checklists` folder holds two children.
- **Forbidden markers.** The record holds no unfinished-marker word, no ellipsis, and no Latin abbreviation. A search of every file returned zero matches.
- **Style.** The record uses no semicolon in prose and no contraction. It uses no Latin abbreviation. No prose sentence exceeds 25 words.

## Unresolved Items

- **UI-1: Chain landing decision.** Decision D-2 needs the human owner. The recommended option is one pull request that closes #4783 and refers to #4773.
- **UI-2: Analyzer blind spot.** The detector does not bridge class-level helpers (R35). The owner must file a follow-up in `misthelper-devtools`. This run cannot create issues (U10).
- **UI-3: Six-child folder.** The owner must track the move of one module into a nested package, under FR-016.
- **UI-4: Principle IV exception.** The pull request body must name the steps 10 to 12 exception (R46).
- **UI-5: Analyzer result.** The analyzer did not run. The gate result comes from T-LOCAL-GATES (U1).

## Metrics

- Requirements: 16.
- Tasks: 12 in phases 1 to 3, and 4 final tasks, for 16 in total.
- Planned pytest cases: 7.
- Remote verification rows: 46.
- Decisions: 6. Human decisions: 1.

## Follow-Up Actions

- **A-1 (owner).** File a follow-up in `misthelper-devtools` for class-level helper bridges.
- **A-2 (owner).** File a follow-up issue to move one module out of the six-child test folder.
- **A-3 (implementer).** Rebase the chain onto main in a worktree, and rerun T-LOCAL-GATES.
