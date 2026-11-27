# Research: W0706 try-except-raise handlers in MistHelper.py

Each decision lists the choice, the reason, the alternatives, and the risk. Row IDs such as R01 refer to the remote verification table.

## Decisions

### D-1. Delete the seven re-raise-only handler pairs

- **Decision**: Delete the seven two-line handler pairs at the main lines listed in `plan.md`. Keep each `except Exception` handler.
- **Rationale**: Each deleted handler re-raises a stop signal (R02 to R08). Each stop signal derives from `BaseException` (R65, R66). The next handler catches `Exception` only, so it never catches a stop signal.
- **Alternatives considered**:
  - Add `# pylint: disable=try-except-raise`. Rejected: `AGENTS.md` forbids suppressing a legitimate finding (R17).
  - Replace each pair with `except BaseException: raise`. Rejected: the same W0706 rule applies to that form (R67).
  - Merge each pair into the `Exception` handler with an `isinstance` check. Rejected: a larger change with more risk.
- **Risk**: A later `except BaseException` handler placed below a deleted handler catches stop signals. Test B reports bare re-raise handlers only. Reviewers must reject a broad handler that catches stop signals.

### D-2. Use main line numbers for every edit

- **Decision**: Use the line numbers from blob `98d7828479ded6bc4c83d15e0c1847171cfbfd49`. Do not use the issue line numbers.
- **Rationale**: The issue line numbers come from commit `61505c611`, which GitHub does not return (R10). The main line numbers match the current file (R01 to R08).
- **Alternatives considered**:
  - Follow the issue line numbers. Rejected: five of the eight numbers point to other code on main.
  - Search for each handler by text only. Rejected: the plan still needs line numbers for review. Each edit uses unique text and a line check.
- **Risk**: Main moves before the edit. Mitigation: T001 and T008 read each line again before the edit.

### D-3. Treat the old line 2331 handler as absent

- **Decision**: Make no edit for the old line 2331 handler.
- **Rationale**: On main, line 2331 is a docstring. The handler text does not exist in `MistHelper.py` (R09). A local search of the repository found no copy in another file.
- **Alternatives considered**:
  - Search `src/` for a moved copy and fix it under this issue. Rejected: a local search found none, and one issue holds one subject.
- **Risk**: A moved copy exists in a file that the local search did not cover. Mitigation: T002 and gate 19 run pylint on `MistHelper.py` only, so a moved copy in another file needs a separate run.

### D-4. Put the tests in the narrow-except module

- **Decision**: Add six top-level test functions to `tests/unit/test_issue_1709_narrow_except.py` (R54).
- **Rationale**: The module already tests narrowed handlers in `MistHelper.py` functions (R54, R55). The five-item rule forbids a new direct child in `tests/unit/`, which holds 50 children (R60). A new file in `tests/guardrails/` adds a child to a folder that holds 79 (R61).
- **Alternatives considered**:
  - A new file in `tests/unit/` or `tests/guardrails/`. Rejected: adds a direct child to a folder that exceeds five children.
  - Add the cases to `test_fast_mode_flag.py`. Rejected: that module covers the `--fast` flag only (R56).
- **Risk**: The module grows from 40 to 46 top-level functions. Mitigation: the plan records the grandfathered debt and a separate remediation.

### D-5. Guard the rule with an AST test

- **Decision**: Walk the AST of `MistHelper.py` and count re-raise-only handlers. Assert that the count is zero.
- **Rationale**: The AST walk runs in pytest without a second linter process. It reads the same structure that pylint reads (R67). The CI pylint job scans `src/` only (R32), so no CI check reads `MistHelper.py` for this rule.
- **Alternatives considered**:
  - Run pylint inside pytest. Rejected: slow, and it depends on a second process inside a test.
  - Add `MistHelper.py` to the CI pylint job. Rejected: a CI scope change belongs to a separate issue (D-10).
  - Search the text with a regular expression. Rejected: formatting changes break the search.
- **Risk**: The guard flags a re-raise-only handler even when a later handler catches a superclass. Accepted: no such handler exists in the seven cases, and the guard names the line for review.

### D-6. Keep the stop-path reason and add logs and comments

- **Decision**: Add the sentence "Stop signals derive from BaseException and pass this handler." to each surviving handler comment. Add an inline comment to each touched line that lacks one. Add an info line before and a debug line after each touched external call or context read (plan changes M1 to M6).
- **Rationale**: Constitution rules VI and VII (R23, R24) state that code lacking comments or action logging must not pass review.
- **Alternatives considered**:
  - Delete the handler lines only. Rejected: violates rules VI and VII.
  - Add logs to every function in the file. Rejected: broader than the touched set.
- **Risk**: More diff lines and more log output. Mitigation: Test F checks the readers, and gate 6 runs the full shards.

### D-7. Add one changelog fragment

- **Decision**: Add `changelog.d/issue-4132-w0706-try-except-raise.md` with one `Changed` bullet.
- **Rationale**: The constitution requires one fragment for each change (R25). Its governance section states that it supersedes other practice documents (R26). The changelog README rule 4 allows no fragment for an internal-only change (R49). The constitution governs the conflict.
- **Alternatives considered**:
  - No fragment. Rejected: conflicts with R25 and R26.
- **Risk**: A reviewer reads the change as internal only. Mitigation: the bullet states the exact effect and names the issue.

### D-8. Use the commit title and branch name from the rules

- **Decision**: Use the commit subject `style(MistHelper.py): remove re-raise-only except handlers`. Use the branch `chore/4132-w0706-try-except-raise`.
- **Rationale**: The constitution lists `style` as a commit type and requires a subject that the title guard accepts (R27). `AGENTS.md` names the branch pattern and allows the `chore` type (R19). The issue carries type label `lint` and scope label `MistHelper.py`.
- **Alternatives considered**:
  - `fix(MistHelper.py)` or `refactor(MistHelper.py)`. Rejected: the change alters no behavior, and the issue label is `lint`.
- **Risk**: None known. The title follows the accepted form.

### D-9. Do not add the auto-merge label

- **Decision**: Do not add the `auto-merge` label. A human reviewer approves the merge.
- **Rationale**: The issue carries `needs-human-review`. The label description reads: "A human must review this before merge. Touches a destructive operation or a safety path." `AGENTS.md` forbids the label for a change that a human must examine (R20). The change touches the stop path.
- **Alternatives considered**:
  - Add `auto-merge` after green CI. Rejected by R20 and by the label.
- **Risk**: The merge waits for a reviewer. This decision does not require a human choice of policy. It follows an existing rule.

### D-10. Keep the CI scope and the historical citations unchanged

- **Decision**: Keep the CI pylint job on `src/`. Keep historical line citations unchanged.
- **Rationale**: One issue holds one subject (R17 and the issue-first rule in `AGENTS.md`). A CI scope change belongs to a separate issue. Historical citations live in unrelated files (R45).
- **Alternatives considered**:
  - Add `MistHelper.py` to the CI pylint job. Rejected: a scope change with runtime cost.
  - Update every historical citation. Rejected: out of scope.
- **Risk**: The rule regresses in CI. Mitigation: Test B. Citations drift. Mitigation: CI `check-citations` scans `src` and `tests` (R36).

## Remote Verification

Each row records one claim. The remote file content came from `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`, decoded in memory. The tree came from `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. No file was written. `Result` is `present` when the cited path or text exists. It is `absent` when the cited path or text does not exist. `Line` is 0 for a file-level or folder-level claim.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | MistHelper.py on main is the audited file | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 0 |
| R02 | Handler 1: except (KeyboardInterrupt, SystemExit) then raise in GlobalImportManager._check_and_upgrade_package | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1820 |
| R03 | Handler 2: except (KeyboardInterrupt, SystemExit) then raise in _invoke_one_systematic_test | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6610 |
| R04 | Handler 3: except (KeyboardInterrupt, SystemExit) then raise in _fast_mode_from_global | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6654 |
| R05 | Handler 4: except (KeyboardInterrupt, SystemExit) then raise in _fast_mode_from_cli_args | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6666 |
| R06 | Handler 5: except SystemExit then raise in _run_tui_event_loop | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7811 |
| R07 | Handler 6: except SystemExit then raise in _execute_interactive_menu_action | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8094 |
| R08 | Handler 7: except SystemExit then raise in the __main__ block | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8343 |
| R09 | Issue handler at old line 2331 is absent on main (text search returns no match) | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R10 | Issue source commit 61505c611 is on GitHub (HTTP 422) | MistHelper.py | 61505c611 | none | absent | 0 |
| R11 | class GlobalImportManager starts at line 1207 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1207 |
| R12 | The __main__ try statement has a finally clause | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8368 |
| R13 | No record folder starts with 4132- on main | specs/numbered/0/0/1/1/3/0/1/2/4132-* | main | none | absent | 0 |
| R14 | Route parent folder holds no child on main | specs/numbered/0/0/1/1/3/0/1/ | main | none | absent | 0 |
| R15 | Reference record spec.md sits on route 0/0/1/2/4/1/4/0 | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R16 | Route rule uses base 5 and eight digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R17 | AGENTS.md: repair a security finding and do not suppress it | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 145 |
| R18 | AGENTS.md: writing style is Simplified Technical English | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R19 | AGENTS.md: the branch name is type, issue, and slug | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| R20 | AGENTS.md: no auto-merge label for a change that a human must examine | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| R21 | copilot-instructions.md: local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R22 | copilot-instructions.md: spec records use managed roots and the base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R23 | Constitution VI: inline comments are non-negotiable | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R24 | Constitution VII: action logging is non-negotiable | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R25 | Constitution: each change adds one release-note fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R26 | Constitution governance: it supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| R27 | Constitution IV step 4: Conventional Commit subject | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 154 |
| R28 | Constitution IV step 10: check the main build after the merge | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| R29 | Constitution IV step 12: deploy and check health | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 170 |
| R30 | Constitution IV: each release-note fragment triggers the pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 175 |
| R31 | Constitution technology: Python 3.15 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| R32 | CI pylint job scans src/ only (SRC_PATH) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| R33 | CI bandit scans the repository root | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R34 | CI radon paths include MistHelper.py | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R35 | CI diagram-refs reads MistHelper.py | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 670 |
| R36 | CI check-citations scans src and tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 702 |
| R37 | CI speckit-task-audit is advisory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| R38 | CI mypy paths include MistHelper.py | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R39 | CI vulture paths include MistHelper.py | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R40 | CI interrogate paths include MistHelper.py | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R41 | Quality-gates pylint row uses SRC_PATH | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 58 |
| R42 | Development setup documents a pylint run on MistHelper.py | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 236 |
| R43 | Operator guide documents Ctrl+C to stop a run | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 526 |
| R44 | Architecture document holds no stop or exception policy (text search, no match) | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 0 |
| R45 | Compliance report cites MistHelper.py lines as history | documentation/COMPLIANCE_REPORT.md | main | 16b10d1a5f27173f4a5df32bdcb0d5de553753be | present | 122 |
| R46 | Pylint messages-control block disables five codes, not W0706 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 594 |
| R47 | requirements-dev.txt pins pylint==4.1.4 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 313 |
| R48 | requirements.txt pins mistapi==0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R49 | Changelog README rule 4: no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R50 | Changelog README: name forms table | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| R51 | Changelog guard: SLUG rule for file names | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 37 |
| R52 | Changelog guard: five change types | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| R53 | PR template: guards state the measured count and a failing path | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 12 |
| R54 | Narrow-except test module is the test target | tests/unit/test_issue_1709_narrow_except.py | main | 313be82f01b17868eb56739c304baf5cd241048f | present | 28 |
| R55 | Narrow-except module holds 40 top-level test functions | tests/unit/test_issue_1709_narrow_except.py | main | 313be82f01b17868eb56739c304baf5cd241048f | present | 0 |
| R56 | Fast-mode reader test covers the normal path | tests/unit/config/standalone/foundation/runtime/startup/test_fast_mode_flag.py | main | 3efd4d5e20265ef01eb17b04c072077c72745658 | present | 86 |
| R57 | Systematic-test success and failure tests exist | tests/unit/export/test_issue_4714_org_licenses_status.py | main | 3af4c2857b21fdf48c3eee7619d6c1d126ccfd4b | present | 162 |
| R58 | Conftest preloads MistHelper.py and handles SystemExit at import | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | present | 173 |
| R59 | changelog.d/ holds 335 direct children | changelog.d/ | main | none | present | 0 |
| R60 | tests/unit/ holds 50 direct children | tests/unit/ | main | none | present | 0 |
| R61 | tests/guardrails/ holds 79 direct children | tests/guardrails/ | main | none | present | 0 |
| R62 | Process-folder guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| R63 | Menu metadata test exists | tests/unit/test_menu_entry_metadata.py | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 0 |
| R64 | STE configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R65 | Python docs: KeyboardInterrupt derives from BaseException | https://docs.python.org/3/builtins/exceptions.html | fetched 2026-11-26 | none | present | 0 |
| R66 | Python docs: SystemExit derives from BaseException | https://docs.python.org/3/builtins/exceptions.html | fetched 2026-11-26 | none | present | 0 |
| R67 | Pylint 4.1.4 W0706 rule: a bare raise as the first handler statement, tested by exc is None | .venv\Lib\site-packages\pylint\checkers\exceptions.py | pylint 4.1.4 (local .venv) | none | present | 534 |
| R68 | Spec templates folder exists | .specify/templates/ | main | none | present | 0 |
| R69 | Constitution: a feature branch must not edit CHANGELOG.md | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 410 |
| R70 | Caller of _check_and_upgrade_package is a GlobalImportManager method | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2033 |
| R71 | Caller of _invoke_one_systematic_test is _systematic_test_run_option | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6645 |
| R72 | Callers of _fast_mode_from_global and _fast_mode_from_cli_args are _systematic_test_resolve_fast_mode | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6675 |
| R73 | Caller of _systematic_test_run_option is the systematic test loop | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6787 |
| R74 | Caller of _run_tui_event_loop is the TUI launch code | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7731 |
| R75 | Caller of _execute_interactive_menu_action is the interactive menu loop | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7995 |

Row count: 75. The `remote_checks` array in `4132-STATUS.json` holds 75 objects in the same order.

## Call Paths

Each path runs from a launch point or a loop to a touched function. Each step cites a row.

- A method of `GlobalImportManager` calls `_check_and_upgrade_package` for the explicitly requested package (R70).
- The systematic test loop calls `_systematic_test_run_option` (R73). That function calls `_invoke_one_systematic_test` (R71).
- `_systematic_test_resolve_fast_mode` calls `_fast_mode_from_global` and `_fast_mode_from_cli_args` (R72).
- The TUI launch code calls `_run_tui_event_loop` (R74).
- The interactive menu loop calls `_execute_interactive_menu_action` (R75). That function runs the selected menu function.

Each touched function keeps its signature and its return value. Callers therefore need no change.

## Sources

- Issue 4132, read with `gh issue view 4132 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author`. The body names eight line numbers from commit `61505c611`. The labels are `quality-gates`, `lint`, `style`, `MistHelper.py`, and `needs-human-review`. One comment dated 2026-11-08 waits for PR #4607.
- `gh pr list -R jmorrison-juniper/MistHelper --state all --search 4132` returned an empty list. No linked pull request exists.
- `gh pr list --state open` returned seven open pull requests: 4890, 4889, 4888, 4887, 4886, 4813, and 4208. None changes `MistHelper.py`.
- `gh pr view 4607` returned state `MERGED`, merged at `2026-11-13T07:14:03Z`, from head branch `jmorrison-juniper-troubleshooting-core-relocation`. The pull request changed `MistHelper.py`.
- `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main` returned `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Read-only git: `rev-parse --abbrev-ref HEAD` returned `main`. `rev-parse HEAD:MistHelper.py` returned `98d7828479ded6bc4c83d15e0c1847171cfbfd49`, equal to the remote blob. `status --porcelain -- MistHelper.py` returned no output. `cat-file -t 61505c611` returned `commit`. `grep -B1` on `61505c611` listed the eight old handlers.
- Labels checked with `gh label list`: `in-progress`, `auto-merge`, `needs-human-review`, `lint`, `MistHelper.py`, and `style` exist.
- Step 3 search for a legacy record: the local glob `specs/**/4132*` returned no file, and the remote tree holds no path that contains `4132` (R13, R14). No legacy record exists to verify.
- No Python exception documentation exists in the repository. The `web_fetch` record above is the only source for the exception hierarchy.
- Local views of the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` for its shape. Read in part: `spec.md` lines 1 to 90, `tasks.md` lines 1 to 70, `design/research.md` lines 1 to 60, and `design/checklists/requirements.md` in full. Its files are `analysis.md`, `plan.md`, `spec.md`, `tasks.md`, and `design/`.
- `documentation/container-deployment.md` was not read, because this change starts no container.
- The Python docs page `https://docs.python.org/3/builtins/exceptions.html` (redirected from `library/exceptions.html`). Fetched 2026-11-26. It states that `KeyboardInterrupt` inherits from `BaseException`, and that `SystemExit` inherits from `BaseException` instead of `Exception`.
- The pylint source `.venv\Lib\site-packages\pylint\checkers\exceptions.py`, read with views. Lines 57 to 59 define `_is_raising`. Lines 532 to 540 apply the W0706 rule.
- Skills: none loaded. The change touches no Podman, container, or Juniper device behavior.
- Mist API OpenAPI files and the `mistapi` source were not read. The change calls no Mist endpoint and no SDK function.

## Unverified

1. The pylint output on main. Rule 2 forbids a linter run during this research. Expected: seven messages at lines 1820, 6610, 6654, 6666, 7811, 8094, and 8343. The basis is R67 and R02 to R08. Task T002 verifies it.
2. The column and the exact text of each pylint message. The message text is `The except handler raises immediately` (pylint 4.1.4 source, line 134). The column is not verified.
3. Whether pylint reports at the `except` line. The basis is the ExceptHandler node, and no pylint run confirmed it.
4. Test results. No test ran during this research.
5. STE scores for the new Markdown files. No linter ran during this research. R64 confirms the configuration exists.
6. Results of `python MistHelper.py --test` and the full test shards. No run occurred during this research.
7. Whether an existing test runs the SystemExit path of the `__main__` block. No test name references that block, and no test reads its handler text. The search was text-based and is not exhaustive.
8. Whether `check-citations` rejects the shifted citation in `src/foundation/support/utils/file_path_utils.py`. The CI tool did not run.
9. Whether caplog assertions in existing tests break after the added logs. No test ran during this research.
