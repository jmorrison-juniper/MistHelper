# Research: C0103 naming exceptions in MistHelper.py

This research uses remote `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` as the truth source. Each cited file has the same blob on the local checkout.

## Decisions

**D-1. Keep the file name `MistHelper.py`. Allow the module name through `module-rgx`.**

- Alternatives: (a) rename to `mist_helper.py`. (b) add a pragma on line 1. (c) disable `invalid-name` for the whole repository.
- Chosen: option (d), a `module-rgx` rule under `[tool.pylint.basic]`. The rule accepts `MistHelper` and snake_case names.
- Reason: The gate table runs `python -m py_compile MistHelper.py` (remote row 36) and `python MistHelper.py --test` (row 37). The file is the entry point (row 40). A rename changes each command and each import. Line 1 is a shebang line (row 1). A pragma there would change the line that the operating system reads. Option (c) hides every future finding.
- Risk: The rule accepts the literal name `MistHelper` for any module. Only one module uses that name.

**D-2. Keep the 23 flagged module-level names. Add one reviewed pragma to each flagged line.**

- Alternatives: (a) rename each name to UPPER_CASE and update every caller. (b) add a `good-names-rgxs` rule. (c) set `const-naming-style` to `any`.
- Chosen: one pragma per flagged line.
- Reason: The Symbols gate fails on any lost or added name (row 65 prints the clean result only when no name changes). The optional-name table refers to twelve of these names by string key (row 28). Tests read `MistHelper.success` (row 30). Options (b) and (c) change the check for every module.
- Risk: A pragma can hide a later finding on the same line. Each pragma carries a reason. The guard fixes the pragma count at 24.

**D-3. Keep the `SSHClient` method name on `SSHFallback`. Add one pragma to its `def` line.**

- Alternatives: (a) rename the method to `ssh_client`. (b) build the fallback from a namespace object.
- Chosen: one pragma on line 2345.
- Reason: The fallback stands in for the `paramiko` module, so its method name must match the paramiko attribute name (rows 12 and 18). A renamed method raises `AttributeError` for the same call. The install guidance in the method body (lines 2346 to 2348, same blob as remote) is then lost. Option (b) hides the pattern without fixing the cause.
- Risk: The fallback keeps a naming style that pylint rejects.

**D-4. Leave `web_portal/services/operation.py` unchanged.**

- Alternatives: (a) remove the duplicate placeholder again. (b) rename `PARAMETER_REGISTRY`.
- Chosen: no change.
- Reason: PR #4662 merged at commit `a71078c3e96dd46dd9a10b64fb5e7654a6fc895b` (rows 26, 27, 54). The file has one assignment, at line 915. The local blob equals the remote blob. The scan found no other naming candidate in the file.
- Risk: None known.

**D-5. Add three guard cases to `tests/guardrails/test_src_public_symbol_preservation.py`.**

- Alternatives: (a) a new file, `tests/guardrails/test_pylint_c0103_gate.py`. (b) a new nested package under `tests/guardrails`. (c) `tests/guardrails/test_ci_gate_triggers.py`.
- Chosen: the existing file. The edit adds no child to the folder.
- Reason: Constitution Principle I (line 38) forbids a new direct child under a noncompliant parent. `tests/guardrails` holds 79 children. Option (b) adds a child to the same parent. Option (c) tests CI triggers, which does not match the subject. The chosen file tests symbol preservation, which is close to the guard subject.
- Risk: A reviewer may see lint cases in a symbol file. The docstring of each case names its subject.

**D-6. Add one changelog fragment.**

- Alternatives: (a) add no fragment, under rule 4 of the changelog README (row 46). (b) add one fragment, under the constitution rule (row 42).
- Chosen: one fragment, `changelog.d/issue-4130-c0103-invalid-names.md`.
- Reason: The constitution supersedes other practice documents when they conflict (governance section). The constitution says each change MUST add one fragment (row 42).
- Risk: The fragment describes an internal change. The follow-up in D-8 can correct the README.

**D-7. Keep the CI pylint scope at `src/`.**

- Alternatives: (a) extend the CI pylint job to `MistHelper.py`. (b) add the guard to CI only.
- Chosen: leave CI unchanged. The guard runs in the test suite.
- Reason: CI pylint runs on `SRC_PATH` (row 45). Extending it exposes 25 findings at once and changes a workflow file, which is out of scope. The guardrail tests run in the full test command, so the two named files stay checked.
- Risk: CI does not check other `MistHelper.py` names. Decision D-8 covers the wider work.

**D-8. File a follow-up issue for the deferred renames and the fallback redesign.**

- Alternatives: (a) file no issue. (b) add the redesign to this pull request.
- Chosen: one follow-up issue (task T012).
- Reason: Constitution Security Findings section (row 41) says a fix that needs more than a trivial change needs a tracked issue. The rename needs a design for the string-keyed bootstrap (row 28).
- Risk: The follow-up can stall. The 24 pragmas stay until it lands.

**D-9. Proceed now.**

- Alternatives: (a) wait for a pending pull request. (b) stop the work.
- Chosen: proceed.
- Reason: The overlap check on 2026-11-26 found no open pull request that changes `MistHelper.py`, `pyproject.toml`, or the guardrail host file (row 56). PR #4607 merged on 2026-11-13 (row 55).
- Risk: A new pull request can open before the merge. Task T-PR repeats the check.

**D-10. Add no local-gate row for the guard.**

- Alternatives: (a) add a row to the Local gates table in `.github/copilot-instructions.md`.
- Chosen: no row. The guard runs inside the existing test command.
- Reason: `.github/copilot-instructions.md` line 275 says the guard `tests/guardrails/test_move_module_guidance.py` compares documented commands with active CI jobs (row 66). A new row can make that guard fail.
- Risk: A reader may not find the guard. The task list and the quickstart name it.

Human decisions: none. Each decision above lies within the repository rules and the scope of the issue.

## Table 1: Predicted C0103 messages in MistHelper.py

Source key: `checker.py` means `.venv\Lib\site-packages\pylint\checkers\base\name_checker\checker.py` (pylint 4.1.4). `node_classes.py` means `.venv\Lib\site-packages\astroid\nodes\node_classes.py`.

| # | Line | Name | Scope | Predicted rule | Basis |
| - | - | - | - | - | - |
| 1 | 1 | `MistHelper` | Module | Module name must match snake_case | `visit_module` checks the module name (checker.py line 379). The default module style is snake_case (naming_style.py line 122). |
| 2 | 182 | `DatabaseConfig` | Module | Constant name must match UPPER_CASE | Assigned `None` in an except handler after a try-body assignment. astroid treats the pair as exclusive (node_classes.py line 117), so the constant branch applies (checker.py lines 453 to 600). |
| 3 | 183 | `configure_db_logging` | Module | Constant name must match UPPER_CASE | Same exclusive pair as row 2. |
| 4 | 184 | `DatabaseRouter` | Module | Constant name must match UPPER_CASE | Same exclusive pair as row 2. |
| 5 | 1082 | `np` | Module | Constant name must match UPPER_CASE | Same exclusive pair with the try-body assignment at line 1080. Line 1080 has a module type, so it is exempt. |
| 6 | 1096 | `SequenceMatcher` | Module | Constant name must match UPPER_CASE | Same exclusive pair with line 1094. |
| 7 | 1114 | `requests` | Module | Constant name must match UPPER_CASE | Single `None` assignment. No handler and no reassignment, so the default constant branch applies. |
| 8 | 1117 | `urllib3` | Module | Constant name must match UPPER_CASE | Single `None` assignment. |
| 9 | 1123 | `_has_pyte` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1126. Value `True`. |
| 10 | 1125 | `pyte` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1122. Line 1122 has a module type, so only line 1125 fails. |
| 11 | 1126 | `_has_pyte` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1123. Value `False`. |
| 12 | 1135 | `paramiko` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1131. |
| 13 | 1136 | `SSHClient` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1132. The name also fails snake_case. |
| 14 | 1137 | `RejectPolicy` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1133. |
| 15 | 1150 | `fuzz` | Module | Constant name must match UPPER_CASE | Exclusive pair with line 1148. |
| 16 | 1172 | `_raw_page_limit_env` | Module | Constant name must match UPPER_CASE | Single string assignment inside an `if` block. |
| 17 | 1174 | `_parsed_limit` | Module | Constant name must match UPPER_CASE | Single integer assignment inside an `if` block. |
| 18 | 2345 | `SSHClient` | Method of `SSHFallback` | Method name must match snake_case | `visit_functiondef` checks method names (checker.py line 420). The default method style is snake_case (naming_style.py line 126). |
| 19 | 2458 | `_early_log_dir` | Module | Constant name must match UPPER_CASE | Single string assignment. |
| 20 | 2460 | `_early_console_level` | Module | Constant name must match UPPER_CASE | Single assignment of `logging.INFO`. astroid infers an integer constant. Inference dependent. |
| 21 | 2461 | `_early_file_level` | Module | Constant name must match UPPER_CASE | Same as row 20. Inference dependent. |
| 22 | 2463 | `_early_rotation_settings` | Module | Constant name must match UPPER_CASE | Single `None` assignment. |
| 23 | 2474 | `import_manager` | Module | Constant name must match UPPER_CASE | `cast(GlobalImportManager, None)`. astroid infers a `cast` call as its second argument (brain_typing.py lines 415 to 418), which is `None`. |
| 24 | 2475 | `_initialize_imports_now` | Module | Constant name must match UPPER_CASE | Single `False` assignment. |
| 25 | 2479 | `success` | Module | Constant name must match UPPER_CASE | Single `False` assignment inside an `else` block. |

Predicted clean lines: 18 and 98 (`version_str`, reassigned, snake_case). 19 and 101 (`required_str`, reassigned, snake_case). 22 (`warning_msg`, a non-constant value). 96 (`logger`, a call result). 178 to 180 (class and function inference). 1080 and 1122 (module-type imports). 1098 and 1102 (`mistapi`, assigned outside the try body, snake_case). 1131 to 1133 (inferred module, uninferable, or class). 1143 and 2471 (redefined imports, checked for disallowed names only). 1148 (module-type import). 2442, 2445, 2459, 2462, and 2464 (non-constant values). 2480 (dictionary). 2530 and annotation-only names (no value).

`operation.py`: the scan predicts zero findings. The module scope holds 17 assignments. Only `logger` is lowercase, and it is a call result. `PARAMETER_REGISTRY` is assigned once.

## Table 2: Remote verification

Result values are `present` or `absent`. Ref `main` means remote `main` at `f03c6c9b`. Ref `local-venv` means a file in the local `.venv`, which is not tracked by git. The line for a whole-file claim is `0`.

| # | Claim | Path | Ref | Blob or object | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Module name appears at line 1 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1 |
| 2 | DatabaseConfig assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 182 |
| 3 | configure_db_logging assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 183 |
| 4 | DatabaseRouter assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 184 |
| 5 | np assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1082 |
| 6 | SequenceMatcher assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1096 |
| 7 | requests assigned None in globals guard | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1114 |
| 8 | urllib3 assigned None in globals guard | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1117 |
| 9 | _has_pyte assigned True in try body | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1123 |
| 10 | pyte assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1125 |
| 11 | _has_pyte assigned False in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1126 |
| 12 | paramiko assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1135 |
| 13 | SSHClient assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1136 |
| 14 | RejectPolicy assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1137 |
| 15 | fuzz assigned None in except handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1150 |
| 16 | _raw_page_limit_env assigned a string in globals guard | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1172 |
| 17 | _parsed_limit assigned an integer in globals guard | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1174 |
| 18 | SSHClient method defined in class SSHFallback | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2345 |
| 19 | _early_log_dir assigned a string | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2458 |
| 20 | _early_console_level assigned logging.INFO | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2460 |
| 21 | _early_file_level assigned logging.INFO | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2461 |
| 22 | _early_rotation_settings assigned None | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2463 |
| 23 | import_manager assigned through cast with None | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2474 |
| 24 | _initialize_imports_now assigned False | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2475 |
| 25 | success assigned False in else block | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2479 |
| 26 | PARAMETER_REGISTRY assigned once, placeholder removed | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 915 |
| 27 | PR #4662 merge commit exists on main | web_portal/services/operation.py | a71078c3e96dd46dd9a10b64fb5e7654a6fc895b | none | present | 0 |
| 28 | Optional-name table binds names by string key | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 237 |
| 29 | Hoist table binds numpy as np by name | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2208 |
| 30 | Test reads MistHelper.success | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py | main | 69e663203101a7cb911693fed6e0378120061910 | present | 101 |
| 31 | Test reads the cli_shell_manager _has_pyte flag | tests/unit/ssh/test_cli_shell_manager.py | main | 02417ebfa5604269dbfac5462b92ca0fd4c7abe5 | present | 82 |
| 32 | Entry-point code writes MistHelper._raw_page_limit_env | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 325 |
| 33 | Data directory checker reads _early_log_dir | src/foundation/support/refactors/data_directory_checker.py | main | 0c7b7ed264ed4c56a1e613a75967dcdbd0d9f6d2 | present | 37 |
| 34 | Rule to annotate a verified false positive | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 151 |
| 35 | Rule against compatibility shims | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 87 |
| 36 | Compile gate names MistHelper.py | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| 37 | Safe sweep gate runs MistHelper.py --test | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 63 |
| 38 | Symbols gate rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| 39 | Hot file rule for MistHelper.py | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 295 |
| 40 | MistHelper.py is the entry point | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 155 |
| 41 | Security findings: fix over suppress | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| 42 | Each change adds one changelog fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 43 | pylint is pinned to 4.1.4 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 117 |
| 44 | pylint basic section exists | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 596 |
| 45 | CI pylint runs on SRC_PATH | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| 46 | Changelog rule 4 allows no fragment for an internal change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 47 | Route base is 5, and the default width is 8 (line 7) | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 48 | No issue 4130 route folder exists yet | specs/numbered/0/0/1/1/3/0/1/0 | main | none | absent | 0 |
| 49 | No legacy 4130 record folder exists | specs | main | none | absent | 0 |
| 50 | Reference record 4920 has the expected shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| 51 | Issue comment commit 3964d21d exists | MistHelper.py | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | none | present | 0 |
| 52 | Issue body commit 61505c611 exists | MistHelper.py | 61505c611 | none | absent | 0 |
| 53 | PR #4661 is closed without merge | web_portal/services/operation.py | pr-4661 | none | present | 0 |
| 54 | PR #4662 is merged | web_portal/services/operation.py | pr-4662 | none | present | 0 |
| 55 | PR #4607 is merged and changed MistHelper.py | MistHelper.py | pr-4607 | none | present | 0 |
| 56 | No open pull request changes MistHelper.py | MistHelper.py | main | none | absent | 0 |
| 57 | Guardrail host file exists | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 0 |
| 58 | pylint visit_assignname branch logic | .venv\Lib\site-packages\pylint\checkers\base\name_checker\checker.py | local-venv | not tracked | present | 453 |
| 59 | pylint redefined-import exemption | .venv\Lib\site-packages\pylint\checkers\base\name_checker\checker.py | local-venv | not tracked | present | 95 |
| 60 | pylint reads the module regex option module_rgx | .venv\Lib\site-packages\pylint\checkers\base\name_checker\checker.py | local-venv | not tracked | present | 366 |
| 61 | pylint default naming styles | .venv\Lib\site-packages\pylint\checkers\base\name_checker\naming_style.py | local-venv | not tracked | present | 122 |
| 62 | astroid treats try body and handler as exclusive | .venv\Lib\site-packages\astroid\nodes\node_classes.py | local-venv | not tracked | present | 117 |
| 63 | astroid ExceptHandler.catch returns True without a filter | .venv\Lib\site-packages\astroid\nodes\node_classes.py | local-venv | not tracked | present | 2669 |
| 64 | astroid infers a cast call as its second argument | .venv\Lib\site-packages\astroid\brain\brain_typing.py | local-venv | not tracked | present | 415 |
| 65 | symbol-diff prints the clean result when no name changes | .venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py | local-venv | not tracked | present | 126 |
| 66 | Move-module guard compares documented commands with CI jobs | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 275 |

## Sources

- Remote GitHub reads, read only. Issue #4130 (view). PRs #4607, #4661, and #4662 (`gh pr view`). Commits `a71078c3`, `3964d21d`, and `61505c611` (`gh api`). Trees and contents at `ref=main` (`gh api`). Open-PR overlap checks (`gh pr list`).
- Local repository, read only. Each cited file has the same blob on the local checkout as on remote `main`. Files: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/templates/` (spec, plan, tasks, checklist), `.specify/scripts/powershell/spec-route.ps1`, `changelog.d/README.md`, `pyproject.toml`, `.github/workflows/ci.yml`, `documentation/quality-gates.md` (line 169), `documentation/development-setup.md` (lines 236 to 241), `MistHelper.py`, and `web_portal/services/operation.py`.
- Local third-party source, read only, not tracked by git: pylint 4.1.4 name checker files, astroid files, and `misthelper_devtools` 0.6.4 `symbol_diff/comparator.py`.
- Local scan: a short Python script read from standard input parsed `MistHelper.py` and `web_portal/services/operation.py` with the `ast` module. The script did not import or run repository code.
- Web sources: none. No URL was fetched.
- Skills: none loaded. No listed skill covers pylint naming or C0103.

## Unverified

1. The full pylint 4.1.4 output for `MistHelper.py`. Reason: rule 2 forbids running pylint in this phase. Table 1 predicts the output from source logic. Task T002 records it.
2. Rows 20 and 21 of Table 1 need astroid inference of `logging.INFO`. Reason: inference was not executed.
3. Ruff exempts a trailing pragma comment from E501 when the code before it fits the limit. Reason: ruff was not run. Task T-LOCAL-GATES verifies it.
4. pylint 4.1.4 applies the `module-rgx` value from `pyproject.toml`. Reason: pylint was not run. Task T009 verifies it.
5. No other C0103 message exists in either file. Reason: the scan covered assignments, defs, classes, and arguments, but pylint was not run.
6. The line content at commit `3964d21d` was not fetched. The predicted list uses current `main` only.
7. CI results for the new pull request. Reason: no pull request exists yet.
8. The follow-up issue number. Reason: task T012 has not run.
