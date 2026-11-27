# Research: Windows Bash Guardrail Skips

The remote `main` head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local HEAD matches it. Each remote check uses ref `main` unless its row names a commit.

Method: One recursive `gh api` tree call on `main` returned `truncated` false. It confirmed the presence and blob SHA of each claimed path. Module bodies came from the blob endpoint. Local `git hash-object` output matched each remote blob SHA, so the local line numbers match `main`.

## Findings

- F-1 (count): The issue reports 10 browser failures. The browser module holds 11 shell cases (RC-04 to RC-09). The None case passes when bash runs. Lines 146 and 147 accept any non-zero exit and any non-empty stderr. Line 153 runs only for the None case. This explanation derives from code (unverified U-2).
- F-2 (browser cause): Line 63 starts `bash` inside the helper method `execute` (line 57, RC-02). The helper passes a quoted Windows interpreter path as the command. Bash returns 127. Line 80 asserts `returncode == 0`, which matches the issue text `assert 127 == 0`.
- F-3 (SNMP cause): Line 95 starts `/bin/bash` (RC-15). Windows has no `/bin/bash` path. Python raises `FileNotFoundError` with `WinError 2`, which matches the issue text.
- F-4 (precedent): `tests/guardrails/test_dependency_lock_workflow.py` line 110 skips its bash step on `win32` with a reason (RC-21).
- F-5 (CI): The `pytest_coverage_shards` job runs on `ubuntu-latest` (RC-22). Its test paths include `tests/guardrails` (RC-23). The `playwright_shards` job holds the three steps that the browser module reads (RC-24 to RC-26).
- F-6 (pytest output): In verbose mode, `_pytest/terminal.py` line 684 and line 685 print the reason of each skipped case (RC-57). The code after line 684 trims the reason when verbosity is below 2. The short summary groups skips by path, line, and reason in `_folded_skips` (lines 1612 to 1640). The default folds the summary (RC-59). The unfolded form prints the full reason (RC-58).
- F-7 (audit rule): The guard proof audit test rejects an unconditional module-level skip (RC-52). It allows a conditional `skipif` (RC-53).
- F-8 (route): The number 4877 equals `124002` in base 5. Padded to eight digits, it equals `00124002`, which is the route value in the request. The radix code spans lines 4 to 33 of `spec-route.ps1` (RC-43). The route folder is absent on `main` (RC-44). The reference number 4920 equals `124140` in base 5, padded to `00124140`. Its folder path matches that route (RC-45).
- F-9 (legacy record): No folder under `specs/` starts with `4877-`. The draft folder for 4877 was empty before this run. No legacy record exists.
- F-10 (linked PRs): PR #4880 is merged. It merged on 2026-11-22T00:47:48Z from head `fix/4876-bootstrap-uv-index`. It closes issue #4876 and names issue #4877 three times as a tracked item. It changed `documentation/development-setup.md`, `scripts/bootstrap_worktree.ps1`, `scripts/bootstrap_worktree.py`, and three test files under `tests/`. Its check rollup holds only SUCCESS and SKIPPED conclusions. PR #3655 is merged. It matched the search through an external HypothesisWorks issue number 4877. It is not linked. It changed `requirements-dev.txt`.
- F-11 (reproduction commit): Commit `23379f0e075557cd5c0761a79f23ad8d3583e296` dates from 2026-11-21T21:39:15Z. Its message reads `chore(deps): refresh and pin project dependencies (#4871)`. The commit exists on `main` (RC-54). It holds the same blob SHAs as `main` for both modules (RC-55 and RC-56).
- F-12 (issue facts): Issue #4877 is open. It carries the labels `bug` and `test`. It was created on 2026-11-21T23:33:36Z and has no comments. It expects each guardrail to run on Windows or to skip with a stated reason and a count. Its acceptance criteria require each test to run on Windows or to skip with a named reason. They also require the skip count in the report. Reproduction: Windows 11 Enterprise 10.0.26200 with PowerShell 7, commit `23379f0e0` on `main`, and `python -m pytest tests/guardrails` in a worktree with the locked environment.
- F-13 (scope boundary): Issue #4878 is open and carries the labels `bug` and `test`. It lists three other Windows guardrail failures: a symlink privilege error, a path separator mismatch, and a path form mismatch. None involves bash.
- F-14 (remote read method): The `contents` endpoint with `?ref=main` returned HTTP 404 for the two module paths. The cause was not found. The blob endpoint returned the same content for the tree SHA. The browser blob measures 9535 bytes. The local file measures 9535 bytes.
- F-15 (guard inputs): The changelog guard requires an allowed name form (line 39). It also requires a heading, a bullet, and a change type word (lines 185 to 197). The container policy guard reads code blocks in `development-setup.md` for volume removal (lines 152 to 200 of the guard). The new section holds only a pytest command, so both guards pass.
- F-16 (instruction conflict): `changelog.d/README.md` line 58 allows no fragment for an internal change (RC-37). The constitution line 409 requires one fragment for each change (RC-39). The repository guide line 451 requires a fragment for a change that a user sees (RC-33). The constitution is the stricter rule.
- F-17 (pipeline trigger): `container-build.yml` runs on a push to `main` only when a listed path changes (RC-28, lines 6 to 19). The list holds product paths and one OpenAPI document. This change touches none of them.
- F-18 (type scope): `ci.yml` line 93 sets `MYPY_PATHS` without a tests path (RC-27). Lines 101, 104, and 107 do the same for Vulture, Pydocstyle, and Interrogate.

## Decisions

### D-1 Skip shell cases on a Windows host with a named reason

- Alternatives: run the cases through Git Bash, port the harness to Python, or mark each case as an expected failure. Another alternative runs the cases in a Linux container through `scripts/compose.ps1`.
- Chosen: Option (skip). Apply the POSIX shell mark with a named reason.
- Reason: Issue #4877 accepts a named skip. Ubuntu CI runs every case (RC-22 and RC-23). Git Bash and WSL map Windows paths differently, and `/bin/bash` has no Windows form (RC-15). A Python port tests a copy of the script and not the workflow script. A container run adds naming and runner work without new evidence. An expected failure reports a result that is not a skip and hides the count.
- Risk: A Windows host loses local coverage of the mirror script. Ubuntu CI keeps that coverage.

### D-2 Select the skip by the platform value win32

- Alternatives: `shutil.which("bash") is None`, or a probe that runs `bash --version` during collection.
- Chosen: `sys.platform == "win32"`.
- Reason: On Windows, `bash` can resolve to Git Bash or to the WSL launcher. The two resolve paths differently, so a lookup could select a case that still fails. The SNMP case also needs `/bin/bash`, which Windows lacks. A probe starts a process during collection. The platform value is fixed and cheap. The repository already uses this form (RC-21).
- Risk: A Windows host with a working POSIX shell still skips. D-1 accepts that result.

### D-3 Attach one constant per module to each shell case

- Alternatives: a module-level `pytestmark`, a shared helper module under `tests/guardrails/`, or a `conftest.py` hook.
- Chosen: One constant per module. Apply the constant as a decorator to each shell case.
- Reason: The guard proof audit rejects an unconditional module-level skip (RC-52). A module-level conditional mark would also skip the 11 non-shell cases. A shared helper module adds a file and an import path for two uses. No `conftest.py` exists in `tests/guardrails` (RC-61), so a hook would add a new file for one marker.
- Risk: A future module needs its own constant. This risk is accepted.

### D-4 Use pytest defaults and document the `-rs` command

- Alternatives: add `-rs` to `addopts` in `pyproject.toml`, or add a `pytest_terminal_summary` hook in a new conftest file.
- Chosen: No configuration change. The verbose output prints each reason (RC-57). The short summary with `-rs` prints each folded reason with its count (RC-58 and RC-59). The documentation gives the command.
- Reason: The default summary already prints the skip count. A repository-wide `-rs` changes the output of every run, and `pyproject.toml` holds the current options (RC-60). A hook adds code for output that pytest already prints.
- Risk: Verbose reasons trim to the terminal width (unverified U-5). The documented `-rs` command shows the full reason.

### D-5 Keep the None-case assertion and file a follow-up issue

- Alternatives: tighten the None-case assertion now, or remove the None case.
- Chosen: Keep the assertion. The orchestrator files a follow-up issue.
- Reason: AGENTS.md limits each issue to one subject (RC-30). The weak assertion does not block the Windows skip result. Tightening it would change a Linux assertion that the issue does not name.
- Risk: A host where bash runs can report the None case as passed without running the mirror logic.

Caution: The false pass remains until the follow-up issue merges.

### D-6 Add no repository-wide guard in this change

- Alternatives: an AST guard that fails when a guardrail module starts bash without the mark, or a text search guard in `tests/guardrails`.
- Chosen: No new guard. The pull request body names the follow-up item.
- Reason: A new guard adds a mechanism and its own tests. The issue names two modules. The guard proof audit already checks skip statements in guard modules (RC-52 and RC-53).
- Risk: A new shell case without the mark fails on Windows until the follow-up merges.

### D-7 Add one changelog fragment

- Alternatives: no fragment, with the reason in the pull request body, or one fragment.
- Chosen: One fragment named `issue-4877-windows-bash-guardrails.md`.
- Reason: The constitution requires one fragment for each change (RC-39). The README allows no fragment only for an internal change (RC-37), and the constitution is the stricter rule. The name follows the issue form (RC-38 and RC-42). The guard accepts a heading and a bullet that names a change type.
- Risk: A reviewer can ask for no fragment. The fragment has no release effect until the release coordinator moves it.

### D-8 Document the Windows result in development-setup.md only

- Alternatives: `documentation/quality-gates.md`, or `.github/copilot-instructions.md`.
- Chosen: `documentation/development-setup.md`.
- Reason: The change affects a Windows local run. `quality-gates.md` describes the CI jobs (RC-34), and the CI jobs do not change (RC-22). The repository guide is read by many guards, so it is not the place for a setup note.
- Risk: PR #4880 changed the same file (F-10). The implementer rebases before the edit.

### D-9 Record constitution steps 10 to 12 as not triggered

- Alternatives: run `workflow_dispatch` for `container-build.yml` to force an image, or omit the steps from the record.
- Chosen: Record that no build runs. The path filter is the evidence (RC-28), and T-MERGE records it.
- Reason: Constitution step 10 (RC-40) waits for a build that the path filter excludes for this change. A forced build spends runner minutes without a product change, which `AGENTS.md` discourages. Omitting the steps would hide the decision.
- Risk: A reviewer can require the forced build. The orchestrator makes that call.

### D-10 Comment and log only the new lines

- Alternatives: (a) add comments and action logs to each touched function body.
- Chosen: Each new executable line carries an inline comment. These lines are the import, the constant, and each argument line of the constant. Decorator lines stay unchanged, and the function bodies do not change.
- Reason: Constitution Principles VI and VII (RC-65) and the `AGENTS.md` inline comment rule (RC-66) govern generated code, and this change generates no function body. The repository exempts decorators (RC-66). Editing six function bodies would widen the diff beyond the issue.
- Risk: A reviewer can read a decorator as a change to the function. The reviewer decides during review.

## Remote Verification

Each row records one check. The row count is 68, and it matches `STATUS.json` and `summary.md`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Browser test module exists and imports pytest and PyYAML | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 10 |
| RC-02 | Browser helper starts bash for the mirror script | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 63 |
| RC-03 | Browser module reads the CI workflow file | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 13 |
| RC-04 | Shell case test_setup_removes_only_the_slow_route_and_preserves_a_backup is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 71 |
| RC-05 | Shell case test_setup_accepts_layout_variations_and_preserves_other_bytes is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 92 |
| RC-06 | Shell case test_missing_azure_mirror_is_a_safe_no_op is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 111 |
| RC-07 | Shell case test_invalid_mirror_configuration_fails_without_a_write with 7 cases is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 140 |
| RC-08 | None case asserts only a non-zero exit and a non-empty stderr before its None-only branch | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 146 |
| RC-09 | Shell case test_a_failed_backup_prevents_the_mirror_rewrite is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 156 |
| RC-10 | Non-shell case test_browser_setup_preserves_the_installer_contract is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 66 |
| RC-11 | Non-shell case test_wan_performance_evidence_upload_keeps_its_shard_and_path is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 169 |
| RC-12 | Non-shell case test_a_weaker_browser_installation_contract_fails with 6 cases is defined | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 179 |
| RC-13 | Browser module has no skip mark on main | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | absent | 0 |
| RC-14 | SNMP test module exists and imports subprocess at line 12 | tests/guardrails/test_snmp_base_oid_defaults.py | main | c04297ce81c9c9f005a54fa655354c064138a3b9 | present | 12 |
| RC-15 | Shell case test_shell_overrides with 9 cases starts /bin/bash | tests/guardrails/test_snmp_base_oid_defaults.py | main | c04297ce81c9c9f005a54fa655354c064138a3b9 | present | 95 |
| RC-16 | Non-shell tests test_defaults_match and test_mismatches_fail are defined with 3 cases | tests/guardrails/test_snmp_base_oid_defaults.py | main | c04297ce81c9c9f005a54fa655354c064138a3b9 | present | 53 |
| RC-17 | SNMP module imports DEFAULT_BASE_OID from the responder module | tests/guardrails/test_snmp_base_oid_defaults.py | main | c04297ce81c9c9f005a54fa655354c064138a3b9 | present | 17 |
| RC-18 | SNMP module has no skip mark on main | tests/guardrails/test_snmp_base_oid_defaults.py | main | c04297ce81c9c9f005a54fa655354c064138a3b9 | absent | 0 |
| RC-19 | Container start script assigns the METRICS_SNMP_BASE_OID default | container/scripts/start.sh | main | 3b138807883a8a8785bac7d8c9b7f9a79458ed0c | present | 270 |
| RC-20 | Responder default DEFAULT_BASE_OID equals the start script default | src/interfaces/monitoring/metrics_gateway/snmp.py | main | 6861023495ac0edf1326f64395995aa8eb030997 | present | 52 |
| RC-21 | Lock workflow test already skips its bash case on win32 | tests/guardrails/test_dependency_lock_workflow.py | main | e529b5c8dc2ce363c670a42595070135fac230c4 | present | 110 |
| RC-22 | Guardrail tests run in pytest_coverage_shards on ubuntu-latest | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 248 |
| RC-23 | Coverage shard test paths include tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-24 | CI step Prepare Ubuntu package mirrors exists and the browser module reads it | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 842 |
| RC-25 | CI step Download the browser exists and the browser module reads it | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 883 |
| RC-26 | CI step Run E2E smoke tests exists and the browser module reads it | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 888 |
| RC-27 | CI scope variables omit tests: MYPY_PATHS at line 93, VULTURE_PATHS at line 101, PYDOCSTYLE_PATHS at line 104, and INTERROGATE_PATHS at line 107 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-28 | Container build push trigger paths exclude tests and documentation | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| RC-29 | AGENTS rule: a guard must prove it can fail and print the cause of a skip | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 142 |
| RC-30 | AGENTS rule: one issue holds one subject | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 185 |
| RC-31 | AGENTS rule: each Markdown file passes the STE gate | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-32 | Repository guide: test command row in the Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-33 | Repository guide: a change that a user sees adds one fragment | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-34 | Quality gates: the browser gate can report a skip as a pass | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 74 |
| RC-35 | Development setup: section Run the browser tests exists as context for the new section | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 262 |
| RC-36 | Development setup: section Never install this project exists as the insertion point | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 339 |
| RC-37 | Changelog README: no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-38 | Changelog README: the issue fragment name form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-39 | Constitution: each change MUST add one fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-40 | Constitution Principle IV step 10: wait for the main build | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| RC-41 | Constitution: local development uses Windows 11 with a venv | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 363 |
| RC-42 | Changelog guard: the issue fragment name rule and slug rule | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-43 | Route radix base is 5, and the numbered route uses a fixed width | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-44 | Route folder specs/numbered/0/0/1/2/4/0/0/2 is absent on main | specs/numbered/0/0/1/2/4/0/0/2 | main | none | absent | 0 |
| RC-45 | Reference record spec.md exists as the shape reference | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-46 | Reference record checklist exists as the shape reference | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 1 |
| RC-47 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-48 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-49 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-50 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-51 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-52 | Guard proof audit test: an unconditional module-level skip is rejected | tests/guardrails/test_guard_proof_audit.py | main | 5f1d7561da51a6ae524ba80b37d5ea86a1e023bc | present | 21 |
| RC-53 | Guard proof audit test: a conditional skipif is allowed | tests/guardrails/test_guard_proof_audit.py | main | 5f1d7561da51a6ae524ba80b37d5ea86a1e023bc | present | 50 |
| RC-54 | Reproduction commit 23379f0e0 exists on main | commits/23379f0e075557cd5c0761a79f23ad8d3583e296 | 23379f0e075557cd5c0761a79f23ad8d3583e296 | not-applicable-commit | present | 0 |
| RC-55 | Browser module blob at commit 23379f0e0 equals main | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | 23379f0e075557cd5c0761a79f23ad8d3583e296 | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 0 |
| RC-56 | SNMP module blob at commit 23379f0e0 equals main | tests/guardrails/test_snmp_base_oid_defaults.py | 23379f0e075557cd5c0761a79f23ad8d3583e296 | c04297ce81c9c9f005a54fa655354c064138a3b9 | present | 0 |
| RC-57 | Pytest verbose output prints the reason of each skipped case | .venv\Lib\site-packages\_pytest\terminal.py | local-venv | not-in-repository | present | 684 |
| RC-58 | Pytest short summary lists skip reasons in the unfolded form | .venv\Lib\site-packages\_pytest\terminal.py | local-venv | not-in-repository | present | 1387 |
| RC-59 | Pytest folds skip reasons by default | .venv\Lib\site-packages\_pytest\terminal.py | local-venv | not-in-repository | present | 171 |
| RC-60 | Pyproject pytest addopts is -v --tb=short without -rs | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 523 |
| RC-61 | No guardrails conftest exists on main | tests/guardrails/conftest.py | main | none | absent | 0 |
| RC-62 | STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-63 | Test quality configuration exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RC-64 | Test quality baseline exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RC-65 | Constitution headings for Principles I to VII and the Technology, Development Workflow, Escalation, and Git sections exist at lines 38, 91, 113, 143, 182, 204, 235, 274, 337, 420, and 453 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-66 | AGENTS section Inline comments starts at line 97 and exempts decorators | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| RC-67 | Pyproject sets a line length of 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 559 |
| RC-68 | Development setup Requirements section lists Python 3.15 or newer | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 9 |

## Sources

- Local repository files, identical to `main` by blob SHA. The Remote Verification table names each file and its blob SHA.
- Local third-party source: `.venv\Lib\site-packages\_pytest\terminal.py`, the pytest package in the local `.venv`.
- Reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for shape only.
- GitHub reads: issue #4877, issue #4876, and issue #4878 through `gh issue view`. PR #4880 and PR #3655 through `gh pr view`. Commit `23379f0e0` through `gh api`.
- Web URLs fetched: none. No local source required a web lookup.
- Skills loaded: none. No listed skill covers pytest, Windows shell behavior, or Spec Kit records.

## Unverified

- U-1: The Windows counts derive from the decorators and parameter lists. They are 11 passed and 20 skipped for the two modules. The Ubuntu count of 31 passed also derives from the lists. The spec agent did not execute either count, because the brief bars test runs.
- U-2: The None case passes on a host where bash runs. The claim derives from lines 146, 147, and 153 of the browser module. It was not executed.
- U-3: The issue reports that the same 19 tests fail on a pristine `origin/main` export. The spec agent cannot check that export, because the brief bars checkouts.
- U-4: The reporter bash build is Git Bash or WSL. The issue text shows only the `/bin/bash:` prefix.
- U-5: The verbose reason trims at the reporter terminal width. The width is unknown, and no run was executed.
- U-6: The test quality analyzer treats the new decorator without a finding. The spec agent did not run the gate.
- U-7: The Ubuntu job log lists no skipped case for the two modules. No CI run exists for this change yet.
- U-8: The eleven non-shell cases pass on a Windows host. The claim derives from the issue count of 19 failures (10 browser and 9 SNMP), and no run was executed.
