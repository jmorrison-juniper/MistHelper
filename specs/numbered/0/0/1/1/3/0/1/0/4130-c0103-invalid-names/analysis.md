# Analysis: C0103 naming exceptions in MistHelper.py

This review checks the spec, plan, tasks, research, and remote code against each other. It lists the defects that the review found in existing work, and the items that remain open.

## Consistency Review

| Check | Result | Note |
| - | - | - |
| Spec requirements to plan | Consistent | FR-003 to FR-006 match the file change map in `plan.md`. FR-009 matches the changelog fragment path. |
| Plan file map to tasks | Consistent | `MistHelper.py` maps to T005 to T007. `pyproject.toml` maps to T004. The guardrail file maps to T003 and T010. The fragment maps to T008. The record maps to T011. `web_portal/services/operation.py` maps to T001. |
| Predicted findings to pragmas | Consistent | Table 1 in `design/research.md` lists 25 predicted messages. They map to 24 pragmas and one module-name rule. |
| Research to remote checks | Consistent | `design/research.md` Table 2 and `remote_checks` in the STATUS file both list 66 rows. The summary states the same count. |
| Tasks to gates | Consistent | Each task names one command from the local gates table. The C0103 check is an extra check, because the table has no C0103 row. |
| Five-Item rule to test placement | Resolved | `tests/guardrails` holds 79 children, so a new file there breaks the rule. Decision D-5 adds the cases to an existing file. |
| Symbol gate to issue guidance | Resolved | The issue says to rename public names after a caller search. The symbol gate fails on any lost name. Decision D-2 keeps the names. |
| Constitution fragment rule to changelog README | Resolved | `changelog.d/README.md` line 58 says to add no fragment for an internal change. The constitution says each change MUST add a fragment. The constitution is the higher rule, so decision D-6 adds the fragment. |
| Constitution security rule to pragmas | Recorded exception | The rule covers security tool findings. Decisions D-2 and D-3 record the exception, and decision D-8 tracks the root-cause work. |

## Defects in Existing Work

1. **Stale line numbers in the issue.** The issue body lists lines from commit `61505c611`. That commit is absent on the remote. The 2026-11-09 comment lists lines from commit `3964d21d`. PR #4607 changed `MistHelper.py` on 2026-11-13, so both lists are stale. The current line list is in `design/research.md`, Table 1.
2. **Stale finding count.** The issue reports 29 findings. PR #4662 reports 27 remaining findings. The 2026-11-09 comment reports 26. The current predicted count is 25.
3. **Version mismatch in the issue.** The issue comment reports pylint 4.1.3. `pyproject.toml` line 117 pins pylint 4.1.4.
4. **CI does not check `MistHelper.py` for C0103.** `.github/workflows/ci.yml` line 529 runs pylint on `SRC_PATH`, and line 78 sets `SRC_PATH` to `src/`. The guard test closes this gap for the two named files (decision D-7).
5. **Rule conflict in `changelog.d/README.md`.** Rule 4 at line 58 conflicts with the constitution. The constitution supersedes it, because its governance section names it the authoritative source. A follow-up should correct the README.
6. **Legacy private globals.** `MistHelper.py` keeps several legacy names. Comments such as "Preserve private module names" (line 2457) describe them. `AGENTS.md` lines 87 and 88 forbid compatibility shims. A follow-up should remove them.
7. **Unused flag.** `_has_pyte` at lines 1123 and 1126 has no reader in `MistHelper.py`. The module `src/operations/execution/ssh/cli_shell_manager.py` defines its own `_has_pyte`. A follow-up should remove the MistHelper copy.
8. **Test host folder is over the limit.** `tests/guardrails` holds 79 children. This is grandfathered debt. The change adds no child to it.

## Unresolved Items

- The actual pylint output for `MistHelper.py` is not known. Task T002 records it, and task T009 reconciles it.
- The pragmas for lines 2460 and 2461 need astroid to infer `logging.INFO`. Task T009 removes either pragma if pylint reports no finding.
- Ruff must accept the trailing pragmas on long lines. Task T-LOCAL-GATES confirms it.
- The module-name rule must take effect. Task T009 confirms it.
- The follow-up issue number is not known until task T012 runs.
