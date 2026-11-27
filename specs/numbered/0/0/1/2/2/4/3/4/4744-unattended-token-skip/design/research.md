# Research: Unattended token skip for menu 247

## Scope and Method

- Issue facts came from `gh issue view 4744`. The issue is open, with labels `bug` and `tests`. It was created on 2026-11-10 and updated on 2026-11-17. The body and both comments were read in full.
- Linked work came from `gh pr list --search 4744`. It returned pull requests #4607 and #4358. Both are merged. Their file lists came from `gh pr view`. No branch was checked out.
- The remote tree came from one call to `git/trees/main?recursive=1`. The tree reported `truncated` as false. Paths were filtered from that tree.
- Remote bodies came from the contents API with `ref=main`, decoded from base64. Line numbers come from the decoded text. The OpenAPI file is 4,317,370 bytes. The contents API omits content above 1 MB, so the file was read through the git blobs API with its blob SHA.
- One contents call returned 404 during the first attempt. The same path returned the expected blob SHA on the next call. Later calls showed no rate limit or 403 response.
- Local files served for orientation only. The installed SDK is a local install, so its rows cite the local path with `not applicable` as the blob SHA.
- Local grep found consumers of skip categories in test files only. That result is local evidence and is not cited as proof of main.

## Existing Record Check

- A recursive search of the local `specs\` folder found no folder named `4744-*`.
- The draft folder `spec-drafts\4744` was empty before this run. `spec-drafts\_meta` held no `4744-STATUS.json` or `4744-summary.md` before this run.
- The remote tree holds no path that contains `4744` (RC-48). It holds no folder at the route (RC-47).
- Result: no legacy record exists. `existing_record.found` is false, and the counts for verified, stale, and absent are zero.

## Linked Work

| Item | State on main | Evidence | Relevance |
| - | - | - | - |
| Pull request #4607 | Merged on 2026-11-13 at 07:14:03 UTC | Head `jmorrison-juniper-troubleshooting-core-relocation`. Its file list includes `src/foundation/support/menu_testing/interactive_test_runner.py`. | The issue asks for coordination with this pull request. The coordination requirement is satisfied. Path RC-01 confirms the current runner path. |
| Pull request #4358 | Merged on 2026-11-13 at 19:33:49 UTC | Head `jmorrison-juniper-4142-test-package-deconfliction`. The issue comment of 2026-11-17 names the current test path, and RC-25 confirms it. | Test path. |
| Issue #1785 | Closed | Title: test: --testinteractive cannot run unattended, so 67 operations have no automated coverage. | Related coverage context. |
| Issue #2753 | Open | Title: chore: audit code defaults that mask missing inputs. | Related to the `allow_empty` default. Out of scope. |
| Issue #3308 | Closed | Title: Docs: the menu reference calls every interactive_safe row read-only. | Related to generated docs. No generated page changes. |
| Open pull requests | None overlap | A query of open pull requests with path filters for the runner, the exporter, the registry, `menu_testing`, the test modules, `input_utils`, the emitter, and the CLI reference returned no result. | No file conflict at the time of this review. |

## Decisions

Each decision lists its options, the chosen option, the reason, and the risk. No decision needs a human decision under brief section 6.

### D-1 Outcome of an unattended menu 247 run

- Options: (a) skip. (b) fail through the existing prompt harness path. (c) change the category of menu 247 to `interactive`, so the skip list excludes it.
- Chosen: (a) skip.
- Reason: The unattended run never supplies the token, and the issue forbids it. A skip records a known precondition. A fail turns every sweep red for a missing operator input. Option (c) changes the registry row (RC-16), and the generated menu API page (RC-37) describes that category.
- Risk: A skip-only run ends with a failure verdict (D-10). The coverage figure drops, and the summary shows the skip.

### D-2 Signal that stops an operator-only prompt

- Options: (a) a context list checked in the input provider, which raises a dedicated exception. (b) let `PromptResolutionError` skip every required prompt. (c) pass `allow_empty=False` for the token prompt and keep the fail path. (d) raise in the exporter when the token is empty.
- Chosen: (a).
- Reason: Option (b) changes the outcome of every menu whose required prompt has no rule, and that outcome is a fail today. It also hides prompt harness defects. Option (c) gives a fail, and the input seam logs a warning on the blank path (RC-21). Option (d) breaks the interactive cancel path (RC-14 and RC-28). Option (a) changes only the named context.
- Risk: The context list is hand-kept. The regression uses the real exporter handler, so drift fails the test (T001).

### D-3 Placement of the new names

- Options: (a) a new module `operator_prompt.py` in `menu_testing`. (b) constants and a class in the runner module. (c) a registry key for each menu. (d) an import of the exporter constant.
- Chosen: (a).
- Reason: The runner module already declares eight classes at module level (RC-58). A new class there adds a direct child to a noncompliant module. The registry row stays unchanged, which keeps the change out of a shared file. The runner lives in the foundation layer. The exporter lives in the operations layer and reads its host through the source dependency resolver (RC-31). An import from foundation into operations reverses that direction.
- Risk: `menu_testing` holds three children after the change, which stays within five (RC-53).

### D-4 Shape of the tally

- Options: (a) `_run_single_option` returns None for a skip, and `_run_option_loop` returns three values. (b) derive skips from the difference between interactive options and exercised options. (c) keep a runtime counter on the runner. (d) return an enum from `_run_single_option`.
- Chosen: (a).
- Reason: Option (b) counts options that the loop skips for a missing menu entry. Option (c) adds a direct child to `InteractiveTestRunner`, which already holds 42 members (RC-57 and RC-59). Option (d) changes the return types of `_emit_option_pass` and `_emit_option_fail` and their callers.
- Risk: Six test call sites change (RC-26).

### D-5 Source of the skip reason

- Options: (a) the registry skip reason through `_skip_reason_for_option`. (b) a literal in the recorder. (c) the text of the exception.
- Chosen: (a).
- Reason: The registry holds the reason (RC-16), and the helper returns a non-empty reason (RC-10, line 343). Option (a) keeps one source of truth.
- Risk: The reason text changes only when the registry changes.

### D-6 Skip category and test mode

- Options: (a) `operator_prompt` and `interactive-operator-prompt`. (b) reuse `credential_required`. (c) reuse `interactive`.
- Chosen: (a).
- Reason: `credential_required` names a missing Mist credential (RC-09, line 737). A different concept needs a different name. `interactive` hides the reason class. The repository has no production consumer of skip categories, and the local test files assert category values only.
- Risk: A telemetry consumer outside the repository might not know the new value (U-8 in the unverified list).

### D-7 Location of the regression tests

- Options: (a) the existing runner test module. (b) a new file in `tests/unit/marvis/mist/intelligence/troubleshooting/core/`. (c) the exporter test module.
- Chosen: (a).
- Reason: The `core` folder holds five children (RC-54), so option (b) makes six. Option (c) tests the runner from the exporter module.
- Risk: The test module debt stays open and is recorded in `plan.md`.

### D-8 Unchanged files

- Options: (a) leave the exporter, the registry, the menu entry, the input seam, the emitter, and the generated pages unchanged. (b) set `allow_empty=False` in the exporter. (c) edit the generated pages.
- Chosen: (a).
- Reason: Option (b) is the rejected option of D-2. The generated pages come from the generator (RC-35), and the drift job regenerates and compares them (RC-34).
- Risk: None beyond D-2.

### D-9 Documentation and release note

- Options: (a) edit the `--testinteractive` row in `documentation/cli-reference.md` and add one fragment. (b) also edit `README.md`. (c) also edit `documentation/operator-guide.md`.
- Chosen: (a).
- Reason: `README.md` holds no `--testinteractive` text (RC-38). A local search of `documentation/operator-guide.md` found no text about the menu 247 token. Option (a) covers the behavior text in one place.
- Risk: The changed row must pass the STE gate (T010).

### D-10 Verdict for a run with skips

- Options: (a) a skip does not fail a run that exercises at least one operation. A run that exercises zero operations fails. (b) any skip fails the run.
- Chosen: (a).
- Reason: Option (b) makes each sweep red without a defect. The existing verdict already fails zero-exercised runs (RC-11 and RC-12).
- Risk: The status defect A-3 remains until its follow-up.

### D-11 Log level of the skip line

- Options: (a) warning. (b) error. (c) info.
- Chosen: (a).
- Reason: The runner counts ERROR records with an observer (class at line 46, RC-58). The skip path removes the observer before it writes, so an error line would be safe. An error line still mislabels an operator-visible skip as an error. An info line hides the skip at the default level.
- Risk: None.

## Remote Verification

Each row records one check. The ref is `main` unless the row states otherwise. The count is 59. STATUS and the summary use the same count.

| ID | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| RC-01 | Runner declares the unattended input provider class. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 84 |
| RC-02 | Provider returns an empty answer for an optional prompt with no rule (allow_empty branch). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 126 |
| RC-03 | Provider raises PromptResolutionError for a required prompt with no rule. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 128 |
| RC-04 | Runner installs the provider on the input seam for one option. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 484 |
| RC-05 | Runner restores the original input seam in a finally block. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 488 |
| RC-06 | Runner writes a pass after a clean return (line 519). It catches PromptResolutionError, EOFError, and Exception at lines 597, 603, and 609. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 519 |
| RC-07 | Loop waits one second for each option (line 629) and returns a two-value tally (line 630). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 629 |
| RC-08 | Suite tallies take the skip count from the context (line 720). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 720 |
| RC-09 | Credential skip writes test_skip with category credential_required. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 737 |
| RC-10 | Registry skip reason is read only on skip-list paths through _skip_reason_for_option (defined at line 343, called at lines 378 and 414). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 378 |
| RC-11 | Verdict counts exercised operations as success plus error (line 688). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 688 |
| RC-12 | A run that exercises zero operations logs a refusal and returns failure (line 690). | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 690 |
| RC-13 | Exporter token prompt uses the context verify_self_email.token. | src/operations/exporting/export/self_account_exporter.py | 1515ce9d86ccbdb619163e88da36d5b2d1a5095f | present | 65 |
| RC-14 | Exporter returns before the SDK call when the token is empty. | src/operations/exporting/export/self_account_exporter.py | 1515ce9d86ccbdb619163e88da36d5b2d1a5095f | present | 144 |
| RC-15 | Exporter calls mistapi verifySelfEmail for the interactive path. | src/operations/exporting/export/self_account_exporter.py | 1515ce9d86ccbdb619163e88da36d5b2d1a5095f | present | 92 |
| RC-16 | Registry row 247 is interactive_safe with the skip reason at line 590. The comment at line 584 explains the row. | src/foundation/support/utils/operation_registry.py | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 590 |
| RC-17 | MistHelper.py menu 247 entry uses SelfAccountExporter.verify_email as its handler. | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4918 |
| RC-18 | MistHelper.py runner builder passes InputUtils to the runner. | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6870 |
| RC-19 | MistHelper.py imports InputUtils from the canonical module. | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2498 |
| RC-20 | Input seam safe_input defaults allow_empty to True. | src/foundation/support/utils/input_utils.py | 960c6ba244134982ec892df3a45232a157a2a853 | present | 64 |
| RC-21 | Input seam logs a warning and returns empty when allow_empty is False and the input is blank. | src/foundation/support/utils/input_utils.py | 960c6ba244134982ec892df3a45232a157a2a853 | present | 136 |
| RC-22 | Emitter emit_test_skip takes five parameters. It writes test_skip with fixed duration 0.0, a UTC timestamp, the skip reason, the skip category, and the test mode (payload at lines 167 to 175). | src/mist/intelligence/analytics/telemetry_emitter.py | 1d8044bea88864fa090989f22f60080b79a5e16f | present | 161 |
| RC-23 | Emitter summary status is pass when failed is zero, regardless of the exercised count. | src/mist/intelligence/analytics/telemetry_emitter.py | 1d8044bea88864fa090989f22f60080b79a5e16f | present | 181 |
| RC-24 | TestSummary holds total, passed, failed, skipped, elapsed, and test_mode. | src/foundation/models/dataclasses/progress_event.py | f8d908c23e8674c872b538e6e4ac61a78641b2da | present | 31 |
| RC-25 | Runner test module holds the input provider restore test. | tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py | 0f03896649a4d7a63d4c325e9661856f05a14adb | present | 448 |
| RC-26 | Runner test module unpacks two loop values at six sites (lines 418, 512, 582, 752, 780, and 813). | tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py | 0f03896649a4d7a63d4c325e9661856f05a14adb | present | 418 |
| RC-27 | Standalone runner test star-imports the runner test module. | tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py | 0b636777c154c363ddd5313afbdfa8164196c7f3 | present | 3 |
| RC-28 | Exporter test module holds the empty token cancel test. | tests/unit/export/test_self_account_exporter.py | 30d14cee1d8c162224f1156b4e95707dc889ec73 | present | 158 |
| RC-29 | Action selection test imports the provider (line 18) and reads its keyword rules (lines 535 and 536). | tests/unit/marvis/actions/test_selection.py | e11821c188e553e17ec5798ffe0c67d034a4ec92 | present | 18 |
| RC-30 | Action operation test builds the provider for menu 270. | tests/unit/marvis/actions/test_operation.py | be88636e3f63030d2dd73c8f10663e6fcacd7199 | present | 162 |
| RC-31 | Resolver reads a test host named MistHelper from sys.modules. | src/foundation/runtime/config/source_dependency_resolver.py | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 285 |
| RC-32 | Symbol guard maps the runner from its old path to menu_testing. | tests/guardrails/test_src_public_symbol_preservation.py | 08f978e755abdf643e7a6d826811401f710883f8 | present | 54 |
| RC-33 | CI sets MYPY_PATHS for the mypy gate. | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-34 | CI runs the menu_reference_drift job. | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 704 |
| RC-35 | Generator writes documentation/menu_reference.md. | scripts/generate_menu_wiki.py | f959225275536743e93bc95d37cb015865a73d53 | present | 66 |
| RC-36 | Row 60 of the CLI reference holds the --testinteractive set text. | documentation/cli-reference.md | 2c171a635ea45241626110575e4b4fe9ed3e4f71 | present | 60 |
| RC-37 | Generated menu API page holds the menu 247 section. | documentation/menu-api/interactive-safe.md | 57b580ddc1c4b9fe4971c72fb26a592764e7ac53 | present | 1201 |
| RC-38 | README holds no --testinteractive text. | README.md | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| RC-39 | Changelog rule names the issue-number file form. | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-40 | Existing fragment uses a heading at line 1 and a Changed bullet at line 3. | changelog.d/issue-4120-troubleshooting-core-relocation.md | 50b7099f894732c3b1d880ff6e6d1fd8b49584b6 | present | 1 |
| RC-41 | Changelog guard requires one change type word in each fragment (line 189). | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 189 |
| RC-42 | STE configuration file exists. | .ste-linter.toml | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-43 | OpenAPI defines GET /api/v1/self/update/verify/{token}. | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25910 |
| RC-44 | OpenAPI operationId verifySelfEmail with responses 200 to 429 (lines 25915 to 25926). | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25913 |
| RC-45 | Route rule uses base 5 (line 17) and default width 8 (line 7). | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-46 | Repository states Python 3.15 or newer. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-47 | No folder exists at the route specs/numbered/0/0/1/2/2/4/3/4 on main. | specs/numbered/0/0/1/2/2/4/3/4/ | not applicable, no tree entry | absent | 0 |
| RC-48 | No path on main contains the issue number 4744. | specs/ (paths containing 4744) | not applicable, no tree entry | absent | 0 |
| RC-49 | No runner test exists at tests/unit/troubleshooting on main. | tests/unit/troubleshooting/test_interactive_test_runner.py | not applicable, no tree entry | absent | 0 |
| RC-50 | The new module path is free on main. | src/foundation/support/menu_testing/operator_prompt.py | not applicable, no tree entry | absent | 0 |
| RC-51 | Installed SDK defines verifySelfEmail. Ref is the local install of mistapi 0.64.1. | .venv\Lib\site-packages\mistapi\api\v1\self\update.py | not applicable, local install | present | 42 |
| RC-52 | Installed SDK builds the verify URI. Ref is the local install of mistapi 0.64.1. | .venv\Lib\site-packages\mistapi\api\v1\self\update.py | not applicable, local install | present | 61 |
| RC-53 | The menu_testing folder holds two direct children on main. | src/foundation/support/menu_testing/ | not applicable, directory count from the tree | present | 0 |
| RC-54 | The runner test folder holds five direct children on main. | tests/unit/marvis/mist/intelligence/troubleshooting/core/ | not applicable, directory count from the tree | present | 0 |
| RC-55 | The code search lists the runner as the only production module that imports the provider. | repository code search for UnattendedInteractiveInputProvider | not applicable, code search result | present | 0 |
| RC-56 | Runner declares _run_single_option at line 541. The method ends at line 613, before _run_option_loop at line 615. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 541 |
| RC-57 | Runner class declares ten fields from line 159 to line 168. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 159 |
| RC-58 | Runner module declares eight classes at module level, the first at line 20. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 20 |
| RC-59 | Runner class declares 32 methods from line 170 to line 750. | src/foundation/support/menu_testing/interactive_test_runner.py | 82bcbc91c82946f41a8aa1b06c8f991dd5d73f3f | present | 170 |

## Sources

Local paths (read-only) and remote paths:

- Brief: `files\spec-brief.md`, read in full before any other step.
- Repository rules: `AGENTS.md`, `.github/copilot-instructions.md` (remote row RC-46), and `.specify/memory/constitution.md` (version 1.9.0).
- Templates: `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- Reference record shape: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Its spec, plan, tasks, analysis, and design folders set the layout only. No content was copied.
- Changelog rules: `changelog.d/README.md` (remote row RC-39) and the guard `tests/guardrails/test_changelog_fragment_policy.py` (remote row RC-41).
- SDK: `.venv\Lib\site-packages\mistapi\api\v1\self\update.py` (rows RC-51 and RC-52) and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` for the installed version.
- Mist API contract: `documentation/mist-api-openapi31yaml.yaml` (rows RC-43 and RC-44). The local copy and the remote blob have the same SHA.
- Test structure: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py` (rows RC-25 and RC-26), `tests/unit/export/test_self_account_exporter.py` (row RC-28), and `tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py` (row RC-27).
- Draft validator: `spec-drafts\_meta\validate-drafts.ps1`, run read-only during self-review.
- URLs: none fetched. The SDK docstrings cite Juniper documentation URLs. Those URLs were not fetched and are not cited.

Skills: The brief asks for a relevant local skill when one is available. This issue concerns a Python test runner and a mocked Mist SDK call. It has no Podman or Juniper device behavior. The debugging skill needs a live session, which rule 2 prohibits. No skill was loaded or cited.

## Unverified

- **U-1 Broad exception wrappers**: No whole-repository search found handlers that catch `Exception` around `safe_input`. The scope is limited to the token context. The regression covers menu 247.
- **U-2 Complexity result**: Radon was not run. The cyclomatic result for `_run_single_option` before and after the change is unknown. T-LOCAL-GATES verifies it.
- **U-3 Symbol gate result**: symbol-diff was not run. T-LOCAL-GATES verifies it.
- **U-4 Guards that read the CLI reference**: The code search returned no hit in `tests/guardrails` for `cli-reference`. The search index can lag. The guard run in T-LOCAL-GATES verifies it.
- **U-5 Name collisions**: Test names were not compared with names that the standalone module star-imports. The gate run verifies it.
- **U-6 Stub resolution**: The regression stub gives `InputUtils` to the resolver. The first test run confirms the resolution.
- **U-7 Live endpoint behavior**: The verification endpoint was not called. The issue forbids live calls. The 200 and 400 response bodies were not checked against a live response.
- **U-8 External telemetry consumers**: Consumers outside the repository are unknown.
- **U-9 Summary status for the existing no-token path**: `_finalize_without_api` was read locally but its remote lines were not decoded. The no-token path reaches the summary rule of RC-23 with zero failures.
- **U-10 CI Python version**: The CI workflow was read for MYPY_PATHS and the drift job only. The CI Python version is not verified.
- **U-11 Gate expectations**: The expected results in `design/quickstart.md` come from the local gates table of `.github/copilot-instructions.md`. The table lines were not decoded from the remote blob. Each gate result must come from the actual run.
