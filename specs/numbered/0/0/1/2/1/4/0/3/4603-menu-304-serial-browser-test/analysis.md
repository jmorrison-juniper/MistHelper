# Specification Analysis Report: Menu 304 serial number browser test

## Findings

### Consistency across spec, plan, tasks, and remote code

Each functional requirement maps to at least one task and at least one test or check.

| Requirement | Task | Test or check |
| - | - | - |
| FR-001 | T001 | TC-1 collection (`--collect-only`) |
| FR-002 | T002 | TC-1 and TC-2 |
| FR-003 | T002 | TC-1 |
| FR-004 | T003 | TC-2 |
| FR-005 | T003 | TC-2 |
| FR-006 | T002 | TC-1 |
| FR-007 | T002 | TC-1 |
| FR-008 | T002 and T-LOCAL-GATES | Symbols gate |
| FR-009 | T002, T003, and T004 | Review of each changed line (checklist item CHK-009) |
| FR-010 | T006 | Matrix: 20 runs under combination D |
| FR-011 | T001 | Research R7, and the record check in brief step 8 |
| FR-012 | T005 | Changelog guard |
| FR-013 | T007 | Trigger check in T006 |
| FR-014 | T-LOCAL-GATES | Shard guard |
| FR-015 | T004 | TC-2 |

The plan, the tasks, and the research table agree on the file list, the test names, and the gate commands. The remote table has 67 rows, and `STATUS.json` lists the same 67 checks.

### Defects in existing work

- **DEF-1 (test helper, confirmed by code reading).** The predicate `PARAMETER_LOADING_HIDDEN_JS` returns true when `#parameterLoading` is hidden or absent (`tests/e2e/web_portal/test_juniper_menus_browser.py` line 52). The helper waits on it after the click (line 186). The wait can pass before a request starts. Evidence: research R3 and R8, and `web_portal/static/js/operations.js` line 278.
- **DEF-2 (test helper).** The fixed 500 ms sleep at line 187 hides timing races. It also adds time to every selection. Evidence: research RV-05.
- **DEF-3 (failure message).** The assertion at line 323 reports only the locator and the timeout. The log cannot show whether the parameter request started. Evidence: research R2.
- **DEF-4 (issue comment, not code).** The issue says PR #4358 owns the browser test and `pyproject.toml`. PR #4358 changed the browser test file. Its file list does not include `pyproject.toml`. Evidence: research R4.
- **DEF-5 (issue comment, stale).** A comment names Dash 4.5.0 and Playwright 1.64.1 as the versions of current main. Main pins Dash 4.5.1 and Playwright 1.65.2 (RV-29, RV-31). Evidence: research U-6.

### Conflicts and drift

- **CON-1 (changelog rules).** The constitution requires one fragment for each change. `changelog.d/README.md` line 58 excludes internal-only changes. The constitution governs (decision D-5). A separate issue can align the two documents.
- **CON-2 (mistapi pin text).** The brief and `.github/copilot-instructions.md` line 21 state `mistapi>=0.64.0,<0.65`. `pyproject.toml` line 29 states `>=0.64.1,<0.65`, and the installed package is 0.64.1 (RV-67). This record uses the value on main. Documentation drift needs a separate issue.
- **CON-3 (CI Python version).** The default `PYTHON_VERSION` changed from `'3.13'` to `'3.15'` in commit `8dd9998f1` on 2026-11-10 (research R7). The failing run used Python 3.13.18. The matrix treats Python as a variable.
- **CON-4 (dependency ranges).** At the failing head, `requirements.txt` pinned `dash>=4.4.1,<5`, a range. Dash 4.5.0 installed. Main now pins exact versions (RV-29, RV-30). Exact pins prevent this drift.

### Discrepancies in the brief

- The brief states the mistapi pin as `>=0.64.0,<0.65`. Main states `>=0.64.1,<0.65` (CON-2).
- The task message gives the ROUTE for this record as `specs\numbered\0\0\1\2\1\4\0\3`. The route algorithm in `.specify/scripts/powershell/spec-route.ps1` (lines 17 and 34) gives digits 0, 0, 1, 2, 1, 4, 0, 3 for issue 4603. The route matches. The route folder is absent on main (RV-53).

## Unresolved Items

1. **Root cause.** Hypotheses H1 to H5 in research R8 remain open. The matrix (T006) and the repair trigger (T007) decide them.
2. **Frequency.** One failure occurred in three completed web-portal runs on the branch (research R7). None of the 15 newest main runs failed. The frequency on main is unknown beyond that sample.
3. **Diagnostic artifact.** Artifact `e2e-diagnostics-web-portal` exists, but its contents were not read. The owner reports HTTP 403 on both download methods (research U-2).
4. **Unguarded writes.** `showSelectedPanel` writes `#selectedOpTitle` without a guard (`web_portal/static/js/operations.js` line 250). `clearExecutionPanel` writes several elements the same way. If one throws, the request never starts. The page error capture in T003 tests this candidate.
5. **Open overlap.** PR #4888 changes `requirements-dev.txt`. A future pin change must wait until that PR merges, or it must coordinate with the PR owner.

## Exceptions to the Local Gates Rule

Tasks T-PR, T-REMOTE-CI, and T-MERGE name GitHub commands as verification. The local gates table has no remote check. Each task states this exception in its text.

## Candidate Separate Issues

This record does not file them. Each one needs its own issue, as AGENTS requires.

1. Align the mistapi pin text in `.github/copilot-instructions.md` and in the brief with `pyproject.toml` (CON-2).
2. Split `tests/e2e/web_portal/` (33 children) and `tests/e2e/` (6 children) into domain folders (plan Complexity Tracking).
3. Resolve the changelog rule conflict between the constitution and `changelog.d/README.md` (CON-1).
4. If T007 starts, report the product cause as its own issue, if it concerns another menu or another page.

## Constitution Alignment

All seven principles pass, with the steps listed in `plan.md`. The Complexity Tracking table records the grandfathered folder debt. This change adds no new violation.

## Metrics

- Requirements: 15 (FR-001 to FR-015).
- Test cases: 2 (TC-1 changed, TC-2 new).
- Tasks: 11 (T001 to T007, plus T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Decisions: 9 (D-1 to D-9). Human decisions: 0.
- Remote checks: 67. Each row cites a blob SHA on `main`. Two rows cite a reason instead of a blob (an absent folder, and the local mistapi file).
- Matrix runs: 60 (20 for combination A, 10 for combination B, 10 for combination C, and 20 for combination D).

## Convergence After Implementation

After T002 to T004, the test module holds 19 tests. After T006, the record gains a results section. After T007 or the stop rule, the record states the outcome. The analysis then closes each open item in the unresolved list.
