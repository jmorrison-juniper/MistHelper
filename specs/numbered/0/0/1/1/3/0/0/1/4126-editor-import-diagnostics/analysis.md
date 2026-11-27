# Specification Analysis Report: Editor Import Diagnostics

This report checks the specification, the plan, the tasks, and the remote code against each other. Row IDs such as R03 refer to `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A-01 | Defect in issue data | HIGH | Issue #4126 file list. `MistHelper.py` lines 895 to 912. | Ten of the 27 listed paths moved from the retired `org/juniper_rma` folder under `src` to `src/operations/exporting/juniper_rma/`. No path under the old prefix exists on `main`. The tests and `MistHelper.py` import the new paths (rows R03 to R12, R28, R37). | The record uses the current paths (decision D-7). The issue body stays unchanged until the owner edits it. |
| A-02 | Defect in issue data | HIGH | Issue #4126 cited lines. `MistHelper.py`. | Eight cited lines do not match `main`. Line 3384 holds no `requests.adapters` import. The mistapi devices import moved to lines 3633 and 7904 (rows R29 to R36). | The live check uses the current files and not the old line numbers. |
| A-03 | Gap in local gates | MEDIUM | `.github/copilot-instructions.md` Local gates table, lines 50 to 74. | No gate row checks E0401 or E0611. The Code quality row checks only the score (line 69). | The acceptance checks use the terminal command as supporting evidence. A separate issue should add a gate for these codes. |
| A-04 | Gap in CI | MEDIUM | `pyproject.toml` line 565. `pylint/lint/run.py` lines 259 to 268 (row R81). `.github/workflows/ci.yml` line 529 (row R56). | The repository sets `fail-under = 9.5` and sets no `fail-on` key. The score check exits zero at or above the threshold. Messages E0401 and E0611 do not fail CI alone. | Out of scope for this change. A separate issue should add the gate. |
| A-05 | Risk in setup doc | MEDIUM | `documentation/development-setup.md` lines 213 to 226 (row R48). `.vscode\settings.json` line 30 (row R89). Extension `package.nls.json` (row R87). | The setup section sets `pylint.path` and does not mention `pylint.importStrategy`. The local settings set `fromEnvironment`. The extension description says `pylint.path` may be ignored in that mode. | The live check records the Pylint command from the output (FR-003). A new change amends the doc if the output confirms the conflict. |
| A-06 | Imprecise comment | LOW | Issue comment `IC_kwDOQltU8c8AAAABdmyM_w` (2026-10-20). | The comment says Pylint adds its working directory to `sys.path`. Pylint removes it (row R79). The repository `init-hook` adds it back (row R51). | The setup doc at line 200 is correct. The record states the exact mechanism. |
| A-07 | Rule conflict | LOW | Pull request template in the brief and `Closes #N` rule. Issue comment `IC_kwDOQltU8c8AAAABkdn4vA` (2026-11-09). Merge commit message of pull request #4322. | The default template requires `Closes #N`. The owner requires the issue to stay open. The merge commit message says the issue must remain open. | Decision D-6 uses `Refs #4126`. Caution: a closing keyword closes the issue at merge. |
| A-08 | Stale label | LOW | Issue #4126 labels. | `needs-investigation` no longer describes the state. The root cause is documented in `design/research.md`. | Remove the label (decision D-9). Keep `in-progress`. |
| A-09 | Rule conflict | LOW | `.specify/memory/constitution.md` Branch Naming. `AGENTS.md` Branch section. | `AGENTS.md` allows the type `docs`. The constitution lists `fix`, `feat`, and `chore` only. The constitution overrides the other guides. | Use the branch prefix `chore/` (decision D-11). |
| A-10 | Name collision risk | LOW | `changelog.d/issue-4126-editor-import-worktree.md` (row R50). | Pull request #4322 already uses the prefix `issue-4126`. | The new fragment uses the name `issue-4126-editor-import-spec.md` (decision D-10). |
| A-11 | Local state | LOW | Local `.vscode\settings.json` (rows R88 and R89). Git ignores `.vscode/` (row R53). | The local settings omit the documented `pylint.path` and `pylint.interpreter` keys. The file is local and git-ignored. | This is not a repository defect. Each worktree needs its own settings during the live check. |
| A-12 | Unresolved item | HIGH | Live editor check. Issue comment `IC_kwDOQltU8c8AAAABhemIow` (2026-10-31). | The live check did not run. The comment reports a missing macOS Screen Recording permission. | Task T010 stays open. The issue stays open (decision D-6). |
| A-13 | Unverified claim | MEDIUM | Diagnostic counts on `main`. | This agent runs no analyzer. The Quality Gates run on `main` at the pinned commit succeeded (row R91). That result does not prove editor diagnostics. | The live check and the terminal check decide the result. |
| A-14 | Unverified claim | LOW | `${interpreter}` token in `pylint.path` (row R86). | The token appears in the extension bundle. Its runtime behavior is not run. | The live check records the Pylint command used. |

## Coverage Summary

| Requirement | Tasks | Acceptance checks | Notes |
| - | - | - | - |
| FR-001 | T008 | AT-03 | Root check |
| FR-002 | T008, T010 | AT-01, AT-03 | Interpreter check |
| FR-003 | T008, T010 | AT-01, AT-03 | Pylint command source |
| FR-004 | T009, T010 | AT-01, AT-02 | Zero diagnostics |
| FR-005 | T010 | AT-01 | Evidence fields |
| FR-006 | T002 | AT-04 | Path map |
| FR-007 | T003 | AT-05 | Cited lines |
| FR-008 | T001, T004 | AT-06 | Setup claims |
| FR-009 | T-LOCAL-GATES | AT-09 | No source change |
| FR-010 | T-PR, T011, T-MERGE | AT-08 | Closure hold |
| FR-011 | T009 | AT-02 | Terminal result is not live evidence |
| FR-012 | T-LOCAL-GATES | STE gate | Markdown style |
| FR-013 | T005, T007 | AT-10 | Changelog fragment |
| FR-014 | T-PR | AT-07 | Secrets and paths |
| FR-015 | T010 | AT-01 | Permission boundary |
| FR-016 | T006 | AT-11 | Route and five-children rule |
| FR-017 | T011, T-MERGE | AT-08 | Labels |

Each requirement has at least one task and one acceptance check. The STE gate is the local gate for FR-012.

## Consistency Checks

- The plan and the tasks name the same eleven changed files.
- The route in `spec.md`, `plan.md`, and `tasks.md` matches the route that the route script computes for issue 4126 (row R67).
- The remote check count in `design/research.md`, in the status file, and in the summary is 91.
- The decisions in `design/research.md`, in the status file, and in the summary are 11.
- The spec names no placeholder token. Each task names exact paths or the worktree.

## Unresolved Items

- U-1: The live editor check has not run. Blocked by the permission gap in A-12.
- U-2: The current diagnostic counts on `main` are unknown. Only the live check and the terminal check can answer this.
- U-3: The precedence between `pylint.path` and `pylint.importStrategy` set to `fromEnvironment` is unknown (A-05).
- U-4: The STE score of each changed file is not measured. T-LOCAL-GATES measures it.
- U-5: The owner editor versions may differ from the versions on the reviewed machine.

## Recommended Follow-Up Issues

These items are outside this change. Each item needs its own issue under the repository rules.

- F-1: Add a CI gate that fails on E0401 or E0611 in `src/` (findings A-03 and A-04).
- F-2: Amend `documentation/development-setup.md` for `pylint.importStrategy`, only when the live check confirms the conflict (finding A-05).
