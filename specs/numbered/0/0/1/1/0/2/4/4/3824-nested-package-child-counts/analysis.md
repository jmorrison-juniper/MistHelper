# Analysis: Nested Source Package Child Counts

## Scope of Review

This review compares `spec.md`, `plan.md`, and `tasks.md` with remote main at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. It also compares them with the legacy records and the issue comments. Each remote fact cites a check ID from `design\research.md`.

## Consistency Checks

| Check | Result | Evidence |
| - | - | - |
| The measured totals in the spec match the guard. | Consistent. Totals are 190 directories, 33 violations, and 236 excess. | C-04, C-09 |
| The inventory rows in `tasks.md` match the measured violations. | Consistent. Each of the 33 violating directories has one row. | C-51 to C-83, T029 to T053 |
| The wave 1 arithmetic matches the ratchet sequence. | Consistent. Wave 1 removes 8 violations and 23 excess, leaving 25 violations and 213 excess. | `plan.md` ratchet sequence |
| The task count matches the record. | Consistent. `tasks.md` holds 57 tasks. | T001 to T057 |
| The issue acceptance criterion matches the ratchet. | Not consistent. The issue asks for a violation count reduction. The guard enforces total excess. | Decision D-1 |
| The baseline matches the measured counts. | Consistent. Each of the 33 entries matches its count. | C-08 |

## Defects in Existing Work

- **A-01: Legacy audit plan states Python 3.13.** The plan names Python 3.13 as the target. The constitution requires Python 3.15. Source: C-33 and C-11. Status: stale. This record does not edit the legacy plan.
- **A-02: Legacy audit spec mixes branches and totals.** The header names `refactor/3824-websocket-catalog-structure`. That branch belongs to pull request 4557, not to the audit slice. The spec also states 34 violations and 237 excess. The current measure is 33 and 236. Source: C-34, C-04, C-09, C-24. Status: stale.
- **A-03: Legacy audit test paths moved.** The legacy record and pull request 4552 name `tests/unit/audit/`. That path is absent on remote main. The three files now sit under `tests/unit/marvis/mist/access/audit/`. Source: C-29 and C-30. Status: absent. The cause is not verified. Source: U-10.
- **A-04: Legacy DB writers plan states Python 3.13.** Source: C-35 and C-11. Status: stale.
- **A-05: Nested gate row names the wrong guard.** The Local gates row for the nested source package gate runs `tests/guardrails/test_move_module_guidance.py`. That test checks the guidance text. The ratchet runs in `tests/guardrails/test_nested_package_structure.py`. Source: C-12 and C-13. Status: partial. Task T004 repairs it.
- **A-06: A closing keyword closed the umbrella issue.** The issue comment dated 2026-10-31 states that the automation closed issue 3824 after pull request 4552 merged. A slice pull request must use `Refs #3824`. Decision D-11 records this rule.
- **A-07: Issue comments carry stale measures.** The comments name 36 violations at commit `f4ee1cee`, 34 violations and 237 excess before pull requests 4552 and 4557, and 180 directories at the head of pull request 4557. Remote main has 33 violations, 236 excess, and 190 directories. Source: C-09. This record uses C-09.
- **A-08: Issue comment 12 proposes a move with a near-full target.** The target `src/mist/resources/org` holds four counted children. The move fills its last slot. Source: C-42. Task T017 stops the slice if the target holds five children.
- **A-09: Issue 4168 names the export folder.** The baseline assigns the export folder to issue 3824. The title of issue 4168 names the export folder too. Source: C-48 and the baseline. Hold H-7 records the overlap.
- **A-10: Issue 4011 stays open after pull request 4552.** Issue 4011 covers isolation of audit renderer modules. Pull request 4552 moved the renderer. This record does not close issue 4011. The issue owner decides its closure.
- **A-11: Root file `junk/diag_rbo.py` is tracked.** Pull request 4552 added the file at the repository root. The file sits outside `src/`. Its import lines are not verified. Source: U-2.

## Unresolved Items

| Item | Blocks | Release condition |
| - | - | - |
| Open pull request 4208 | W3-03, the refactors directory | Pull request 4208 merges or closes. |
| Open pull request 4813 | W3-14, the export folder | Pull request 4813 merges or closes. |
| Issue 1794 reservation | W3-01, `zscaler_catalogue.py` | Issue 1794 integrates the audit or transfers the file in writing. |
| Issue 4009 overlap | W2-09, metrics gateway | Issue 4009 closes or transfers the work in writing. |
| Issue 4168 ownership | W3-14, the export folder, and T052 to T053 | The owner of issue 4168 confirms the ownership split. |
| Issue 4142 test moves | Test paths in every slice | Each slice re-derives its test paths with `git grep` at its start. |

## Metrics

- Violations: 33 at the measured base, 25 after wave 1, 2 after waves 2 and 3.
- Excess: 236 at the measured base, 213 after wave 1, 3 after waves 2 and 3.
- Tasks: 57. Requirements: 14. Decisions: 11. Human decisions: 0.
