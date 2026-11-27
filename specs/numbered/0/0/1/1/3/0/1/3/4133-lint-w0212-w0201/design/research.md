# Research: Lint repair for W0212 and W0201 findings

Each decision lists the choice, the reason, and the other options. Remote evidence rows (RC) match the remote verification table below and the `remote_checks` array in `4133-STATUS.json`.

## Method

1. Issue facts. `gh issue view 4133` returned the title, body, labels, state, dates, and six comments. The body cites commit 61505c611 and branch `3519-juniper-rma-correlation`.
2. Linked work. `gh pr list --search 4133` returned PR #2693 only. Its body contains "0.4133 percent", so it does not link to this issue. Issue comments name PR #4607. The record also reads PRs #4856 and #4857, which touched `MistHelper.py` in related lint work. The open pull requests are seven in total, and none touches `MistHelper.py` or the test file.
3. Existing record. A recursive search of `specs\` found no folder named `4133-*`. The route folder `specs\numbered\0\0\1\1\3\0\1` does not exist. The folder `specs\numbered\0\0\1\1\3` already holds four children.
4. Remote truth. One recursive tree read of `main` returned 11,404 entries, and the tree is not truncated. The blobs of the two named files were read through `git/blobs`. The SHA-1 recomputed from the decoded bytes matched each blob SHA. Commit, branch, path, and PR reads used `gh api` and `gh pr view`. Local read-only git commands confirmed that the local HEAD f03c6c9b3 equals remote `main`, and that the local blobs equal the remote blobs.
5. Lint evidence. Pylint did not run, because rule 2 prohibits linters. A read-only Python `ast` walk ran on the decoded blobs instead. The walk follows the pylint 4.1.4 source (rows RC-33 and RC-34). It treats `self` or `cls` as allowed only when the name equals the first parameter of the enclosing method, and that method is not static. Results on blob c6df4393 (commit 0d881744): 7 W0212 in `MistHelper.py` and 2 W0212 in the test file. Results on blob 98d78284 (main): 0 W0212 in `MistHelper.py` and 2 W0212 in the test file. The W0201 check reports 0 findings on both blobs. The owner run reported the same counts on 0d881744.
6. Required reading. The record read `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates in full. The reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` provided the spec, plan, tasks, research, and requirements checklist. The other nine reference files were listed only. The record read `documentation/development-setup.md` for lines 1 to 120, and `documentation/quality-gates.md` for lines 1 to 200. The record read the headings of `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`. Those three files cover layout, container runs, and operator output, and the change touches none of them.
7. Skills. No skill was loaded. The issue concerns Python lint. It involves no Podman behavior and no Juniper device behavior.
8. Mist API and mistapi. Not applicable. The change makes no Mist call. The record makes no claim about the Mist OpenAPI file or the mistapi package.

## Decisions

### D-1 Use remote main as the source of finding truth

- Decision: Evaluate findings on remote `main`. Use blob 98d78284 for `MistHelper.py` and blob d9b4d79e for the test file. Keep the issue line numbers as history only.
- Rationale: The brief ranks GitHub `main` above local search. The issue line numbers come from commit 61505c611, which GitHub does not return (RC-09). The owner run at 0d881744 predates the current blobs (RC-08, RC-11, RC-12).
- Alternatives considered: (a) Keep the issue line numbers. Rejected: the cited commit is absent, and the lines do not match main. (b) Keep the owner run at 0d881744. Rejected: `main` changed both files after that run.
- Risk: The walk is not pylint. Mitigation: T-LOCAL-GATES runs the pylint command with pylint 4.1.4.
- Human decision required: no.

### D-2 Leave MistHelper.py unchanged

- Decision: Make no edit to `MistHelper.py`. Keep the three `_uv_*` attributes in the helper `_initialize_dependency_tracking`, which starts at line 1373. `__init__` calls that helper at line 1349.
- Rationale: Pylint 4.1.4 reports no W0201 for those attributes. It applies the W0201 rule per attribute. A store in a method that a defining method calls makes pylint skip every store of that attribute. The rule sits in `_check_attribute_defined_outside_init` (lines 1326 to 1413) with `_called_in_methods` (line 457). The W0212 sites were already removed by commit aa8d12e90 (RC-05 to RC-07). Moving the attributes would edit a hot file for no lint gain. Copilot-instructions line 293 names `MistHelper.py` as a hot file.
- Alternatives considered: (a) Move the three declarations into `__init__`, as the issue text describes. Rejected: no finding changes, and the edit touches a hot file. (b) Leave the findings open. Rejected: the issue requires zero findings.
- Risk: The issue text reads as "declared in `__init__`". A reviewer may read the deviation as incomplete. Mitigation: the spec and analysis item 4 state the deviation.
- Human decision required: no.

### D-3 Route the test through the public dispatch and add no suppression

- Decision: Replace the two protected calls with calls through `MistHelper.dispatch_main_mode` (line 8232). Replace four collaborators with monkeypatch doubles. The collaborators are `ConfigUtils.get_cached_or_prompted_org_id`, `EnvironmentUtils.is_running_in_container`, `InputUtils.safe_input`, and `MistHelper.echo`.
- Rationale: Dispatch is public. It reaches the same handlers through the interactive loop (lines 7966 to 8036). The issue accepts a public member as the fix. The file keeps every test name, so the symbol check passes.
- Alternatives considered: (a) Rename the three module-level handlers to public names. Rejected: the symbol check reports a removed module-level name. A retained alias is a compatibility shim, which AGENTS.md forbids in its code quality section. (b) Add `# pylint: disable=protected-access` to each line. Rejected: AGENTS.md and constitution Principle III forbid suppression of a legitimate finding. (c) Reach the handlers through `getattr`. Rejected: that hides the coupling and evades the linter. (d) Keep the calls. Rejected: the issue requires zero findings.
- Risk: The tests grow by four patches and one import. Mitigation: monkeypatch restores each value, and the assertions stay exact.
- Human decision required: no.

### D-4 Add one changelog fragment

- Decision: Add `changelog.d/issue-4133-lint-w0212-w0201.md` with one `Changed` bullet.
- Rationale: Constitution line 409 requires one fragment for each change. The constitution governance section names it the authoritative source. The fragment README exempts internal-only changes (rule 4), and copilot-instructions line 451 requires a fragment only for a user-visible change. Both documents conflict with the constitution. The constitution governs.
- Alternatives considered: (a) Add no fragment and state the reason in the pull request body, as README rule 4 allows. Rejected: the constitution has priority. (b) Use the `pr-` name form from the README. Rejected: the pull request does not exist yet. The README names the file by issue in that case.
- Risk: A reviewer may consider the fragment unnecessary. The fragment is part of the same reversible commit.
- Human decision required: no.

### D-5 Start T-PR only after orchestrator authorization

- Decision: T-PR and T-MERGE wait for the orchestrator authorization. The file ownership block ended on 2026-11-13. The publication hold stays in force until the authorization.
- Rationale: PR #4607 merged on 2026-11-13 and changed `MistHelper.py` (RC-13). Issue comments dated 2026-11-10 state that the publication hold and the merge hold remain in place. Brief section 4 gives the orchestrator the merge authorization. The hold is a release gate, not one of the human categories in brief section 6.
- Alternatives considered: (a) Publish now. Rejected: the publication hold has no release. (b) Keep the ownership block. Rejected: the merge ended it.
- Risk: The work waits. Mitigation: T-LOCAL-GATES runs before the hold, so no further work follows the authorization.
- Human decision required: no.

### D-6 Run the test-quality gate and change no baseline

- Decision: Run the test-quality gate with `--changed-from origin/main`. Stop on any new finding. Leave `.github/test-quality-baseline.json` unchanged.
- Rationale: The baseline has no entry for the test file (RC-25). The analyzer flags a module only through names that the test calls through its module alias. It reads the bodies of those called functions (`missing_failure_mode.py` lines 318 to 340). The planned body of `dispatch_main_mode` names none of the four HTTP modules (lines 42 and 361 to 378 define the check). Quality-gates documentation requires a documented reason for each baseline entry. Warning: a baseline edit here hides a finding, and the hidden finding ships with no report.
- Alternatives considered: (a) Add the test file to the baseline. Rejected: that hides a finding. (b) Publish the owner candidate. Rejected: issue comments dated 2026-11-10 report two new HTTP findings for that candidate under the released analyzer.
- Risk: The gate may still report a finding. Mitigation: stop, file a new issue, and leave the baseline unchanged.
- Human decision required: no.

### D-7 Change the scope label of the issue

- Decision: Remove the `MistHelper.py` label from issue 4133. Keep `lint` and `tests`. Add `in-progress` only when T-PR starts.
- Rationale: After the change, the issue touches only the test file and the fragment. Copilot-instructions lines 431 to 450 require a scope label that matches the work.
- Alternatives considered: Keep both scope labels. Rejected: the label describes a file that the change does not touch.
- Risk: The orchestrator may keep the original label. The label change is reversible.
- Human decision required: no.

## Remote Verification Table

| ID | Claim | Path | Ref | Blob or object | Result | Line |
|---|---|---|---|---|---|---|
| RC-01 | `MistHelper.py` exists on main. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 0 |
| RC-02 | The menu metadata test exists on main. | `tests/unit/test_menu_entry_metadata.py` | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 0 |
| RC-03 | The test calls the protected invalid-selection handler. | `tests/unit/test_menu_entry_metadata.py` | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 84 |
| RC-04 | The test calls the protected empty-input handler. | `tests/unit/test_menu_entry_metadata.py` | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 93 |
| RC-05 | The protected `select_msps` call is absent. The public call is at line 4790. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 4790 |
| RC-06 | The protected `deferred_init_done` store is absent. The public store is at line 7576. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 7576 |
| RC-07 | Commit aa8d12e90 is on GitHub and changed `MistHelper.py`. | `MistHelper.py` | aa8d12e90fd68b5b22a44471b0606443e6ab9338 | not applicable (commit) | present | 0 |
| RC-08 | Commit 0d881744 is on GitHub. | commit | 0d881744310dc2c1b1be8b47b5b5402504029062 | not applicable (commit) | present | 0 |
| RC-09 | Commit 61505c611 cited by the issue is on GitHub. | commit | 61505c611 | not applicable (commit) | absent | 0 |
| RC-10 | Branch `3519-juniper-rma-correlation` cited by the issue is on GitHub. | branch | 3519-juniper-rma-correlation | not applicable (branch) | absent | 0 |
| RC-11 | `MistHelper.py` at 0d881744 equals main, as the issue comment states. | `MistHelper.py` | 0d881744310dc2c1b1be8b47b5b5402504029062 | c6df4393483ef7b5c25e945f73dd8126ce0fa8b4 | stale | 0 |
| RC-12 | The test file at 0d881744 equals main, as the issue comment states. | `tests/unit/test_menu_entry_metadata.py` | 0d881744310dc2c1b1be8b47b5b5402504029062 | 02119600a5f4ca1f63aaa68355258cfe22833584 | stale | 0 |
| RC-13 | PR #4607 merged and changed `MistHelper.py`. | `MistHelper.py` | pull request 4607 | not applicable (pull request) | present | 0 |
| RC-14 | The route folder `specs/numbered/0/0/1/1/3/0/1` is absent. | `specs/numbered/0/0/1/1/3/0/1` | main | not applicable (folder) | absent | 0 |
| RC-15 | The route parent `specs/numbered/0/0/1/1/3` holds four children. | `specs/numbered/0/0/1/1/3` | main | not applicable (folder) | present | 0 |
| RC-16 | The reference record `spec.md` exists. | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-17 | The repository instructions hold the local gates table at line 50. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-18 | The constitution requires one fragment for each change. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-19 | The CI `MYPY_PATHS` value omits the tests tree. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-20 | The CI `PYDOCSTYLE_PATHS` value omits the tests tree. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-21 | The CI `INTERROGATE_PATHS` value omits the tests tree. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-22 | The CI pylint source path defaults to `src/`. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| RC-23 | `pyproject.toml` pins pylint 4.1.4. | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 117 |
| RC-24 | The pylint disable list in `pyproject.toml` omits W0201 and W0212. | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 594 |
| RC-25 | The test-quality baseline has no entry for the test file. | `.github/test-quality-baseline.json` | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| RC-26 | The test-quality configuration file exists. | `.github/test-quality-config.toml` | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RC-27 | The test-quality preflight guard exists. | `tests/guardrails/local_test_quality_loop/test_guidance.py` | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-28 | The changelog fragment guard exists. | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-29 | The changelog fragment rules exist. | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-30 | The development requirements file exists and pins the analyzer. | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 0 |
| RC-31 | The STE linter configuration exists. | `.ste-linter.toml` | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-32 | The route script defines base 5 at line 17. | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-33 | Installed pylint 4.1.4 applies the per-attribute W0201 rule. | `.venv\Lib\site-packages\pylint\checkers\classes\class_checker.py` | installed package | not applicable (installed package, not in repository tree) | present | 1326 |
| RC-34 | Installed pylint 4.1.4 checks protected names in assignment targets. | `.venv\Lib\site-packages\pylint\checkers\classes\class_checker.py` | installed package | not applicable (installed package, not in repository tree) | present | 2081 |
| RC-35 | Installed analyzer treats `mistapi`, `requests`, `httpx`, and `aiohttp` as HTTP clients. | `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py` | installed package | not applicable (installed package, not in repository tree) | present | 42 |
| RC-36 | Installed analyzer reads only the bodies of functions that a test calls through a module alias. | `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py` | installed package | not applicable (installed package, not in repository tree) | present | 331 |

| RC-37 | CI `VULTURE_PATHS` value omits the tests tree. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |

Row count: 37 rows. The `remote_checks` array in `4133-STATUS.json` also holds 37 rows.

## Sources

Local files read (read only):

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `.specify/templates/` (four files).
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\` (reference record).
- `documentation\development-setup.md`, `documentation\quality-gates.md`, `documentation\architecture.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`.
- `MistHelper.py` at lines 462, 1346 to 1395, 1473 to 1481, 1545 to 1562, 1349, 3658, 4790 to 4791, 5735 to 5736, 7576, 7592, 7966 to 8064, 8232 to 8256, and 8276.
- `tests\unit\test_menu_entry_metadata.py` (full file).
- `.github\workflows\ci.yml` at lines 78, 93, 101, 104, 107, 122, 123, and 127.
- `changelog.d\README.md`, `pyproject.toml` (lines 117, 564 to 594), `.specify\scripts\powershell\spec-route.ps1` (lines 4 to 34).
- Installed pylint source (read only): `.venv\Lib\site-packages\pylint\checkers\classes\class_checker.py`, lines 457 to 485, 946 to 952, and 1326 to 1413.
- The same pylint file, read only, also at lines 1938 to 1952, 2066 to 2084, 2116 to 2200, and 2654 to 2680.
- Installed analyzer source (read only): `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py`, lines 36 to 46, 318 to 340, 355 to 400, and 42 to 44.

GitHub sources (read only, through `gh`):

- Issue #4133 with its six comments.
- PRs #4607, #2693, #4856, and #4857.
- Issues #4131, #4136, #2711, #2746, and #4702.
- Commits aa8d12e90, 0d881744, and 61505c611. Branch `3519-juniper-rma-correlation`.

URLs fetched with `web_fetch`: none. No external source supports a claim in this record.

## Unverified

1. Pylint did not run in this record, because rule 2 prohibits linters. The W0212 and W0201 results come from the AST walk and from the pylint 4.1.4 source. The quickstart pylint command must run in T-LOCAL-GATES.
2. The test-quality analyzer result for the planned test is unknown until T-LOCAL-GATES runs the gate.
3. The owner candidate test and the analyzer candidate are outside the repository. This run has no path to them. Their content is unverified, and the record does not use them.
4. Local commit 61505c611 exists as a local object. This record did not compare its content with the issue line numbers. The commit counts as absent, because GitHub does not return it (RC-09).
5. The complete default list of `exclude-protected` was read only in part (`class_checker.py` lines 946 to 952). The two flagged names, `_handle_interactive_invalid_selection` and `_handle_interactive_empty_input`, do not appear in the displayed part. An unseen default name can only remove a finding, not add one.
6. Whether the publication hold ends is unknown. The orchestrator decides that point (D-5).

## Human Decisions

None. No decision in this record falls in the human categories of brief section 6. Each decision names its reason and its alternatives.
