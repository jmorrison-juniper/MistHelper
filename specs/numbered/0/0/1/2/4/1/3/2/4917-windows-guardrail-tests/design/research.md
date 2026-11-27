# Research: Windows guardrail test failures

Each decision names the chosen option, the other options, the reason, and the risk. Remote facts come from `gh api` reads of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (2026-11-26T07:15:01Z). The remote tree has 11,404 entries, and GitHub reports it as not truncated.

## Existing record

No legacy record exists. No folder under `specs\` starts with `4917-` in the local checkout. The remote tree has no `4917-` path either (RC-39). The route folder `specs\numbered\0\0\1\2\4\1\3\2` is absent on `main` (RC-38).

The route `0/0/1/2/4/1/3/2` is the result of `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1` (RC-20). The capacity guard in `Assert-SpecFeatureDestination` rejects a new child under a parent that holds five children (RC-45). On this route, `specs\numbered\0\0\1\2\4\1` holds one child. The parent `specs\numbered\0\0\1\2` holds five children, but its route child `4` already exists, so the guard passes.

## Linked work

- Issue #4917 is open. It has the labels `bug` and `tests`, no comment, and one body. It was created on 2026-11-24T19:57:58Z.
- PR #4918 merged on 2026-11-24T21:30:17Z. It closes issue #4916. Its body names issue #4917 as the tracker for the 23 failures.
- Issue #4916 is closed.
- Seven pull requests are open: #4886, #4887, #4888, #4889, #4890, #4813, and #4208. None changes a path in the file set of this record. Source: `gh pr list --state open --json files`.

## D-1. Skip the Bash cases on Windows

- **Decision**: Skip the 11 browser execution cases and the 9 SNMP shell-override cases on Windows. Each skip prints a reason. Ubuntu CI remains the proof for these 20 cases.
- **Alternatives considered**:
  - Find Git Bash from the `git` executable and pass POSIX path text into the test. The browser test inserts a path into a Python heredoc inside the CI step (RC-15). This option needs a Windows run to prove the path handling, and this phase cannot run tests.
  - Run the Python body of the CI step without Bash. This option removes the shell step that the test exists to prove.
- **Rationale**: Ubuntu CI runs `tests/guardrails` (RC-13). The browser test reads the Ubuntu mirror step (RC-15). The repository already skips one Bash-based guard on Windows with a reason (RC-08).
- **Risk**: The Windows workstation cannot prove these 20 cases. Ubuntu CI proves them on each pull request.

## D-2. Resolve uv beside the running interpreter

- **Decision**: In `DependencyExport.find_uv`, check PATH first. If PATH has no `uv`, check the environment folder of the running interpreter. Keep the failure when neither lookup finds `uv`.
- **Alternatives considered**:
  - Activate `.venv` or add `uv` to PATH on the Windows workstation only. The guard stays strict, but each run needs that setup step.
  - Skip with a cause, as `test_dependency_lock_file.py` does (RC-09). The export guard exists to prevent a silent pass, so a skip weakens it.
  - Import the bootstrap lookup from `scripts\bootstrap_worktree.py` (RC-22). That file holds 805 lines, and a test would import its internals.
- **Rationale**: The local environment folder holds `.venv\Scripts\uv.exe`, and `.venv\Lib\site-packages\uv-0.13.9.dist-info` exists. `requirements-dev.txt` pins `uv==0.13.9` (RC-21). CI installs that file before the export guard (RC-14). The fallback keeps the PATH precedence, so the CI lookup does not change.
- **Risk**: A different uv on PATH still wins. Mitigation: the CI job and this environment folder use the same pin.

## D-3. Skip the symlink case only for the privilege error

- **Decision**: Catch `OSError` where the symlink is created in `test_unsafe_feature_selection_fails` (RC-07). Skip only when `winerror` equals 1314. Re-raise every other error.
- **Alternatives considered**:
  - Fail when the privilege is absent. The Windows workstation then stays red for a workstation setting.
  - Create a directory junction with `mklink /J`. A junction changes the fixture kind, and no test in this record proves that the route script rejects a junction the same way.
  - Skip on every Windows workstation. This option hides the proof on workstations where links work.
- **Rationale**: The issue reports `[WinError 1314] A required privilege is not held by the client` for this account (issue #4917 body). The precise skip keeps the proof where links work, and it still reports every other failure.
- **Risk**: The Windows workstation does not run this proof. Ubuntu CI runs it (RC-13).

## D-4. Compare the Git root as a path object

- **Decision**: In `test_git_ignores_poisoned_locations`, compare `Path(repository.git("rev-parse", "--show-toplevel"))` with `repository.root.resolve()` (RC-10).
- **Alternatives considered**:
  - Compare `.as_posix()` text on both sides. This option works, but it keeps a text comparison.
  - Normalize the output inside `FixtureRepository.git`. That change alters a shared helper.
- **Rationale**: On Windows, `Path` equality compares normalized lowercase text. Local source `Lib\pathlib\__init__.py` lines 199 to 207 defines `_str_normcase`. One expression covers separators and case.
- **Risk**: None known. A different repository root still fails the test.

## D-5. Print analytics paths in POSIX form

- **Decision**: Build the missing-root message from `as_posix()` paths (RC-11, line 75). Match `missing_root.as_posix()` in the regex at line 177.
- **Alternatives considered**:
  - Keep the list `repr` and escape the doubled backslashes in the regex. The CI log keeps the doubled backslashes.
  - Assert only the directory name. The test would lose the path proof that its name states.
- **Rationale**: The message holds `repr` text with doubled backslashes (RC-11). The same file already prints POSIX paths in its other messages (local lines 82, 129, and 141, with a blob SHA equal to remote). Local search shows one producer of this message text in `tests\`.
- **Risk**: The message format changes for this one guard only.

## D-6. Add no Windows CI job

- **Decision**: Add no Windows job in this change. File a follow-up issue for Windows coverage of the guardrail tests.
- **Alternatives considered**:
  - Add a `windows-latest` job that runs `tests/guardrails`. Every CI job runs on `ubuntu-latest` (RC-12). A new job adds CI time and a status that the owner must review.
  - File a follow-up issue. This option is chosen.
- **Rationale**: One issue holds one concern (AGENTS.md, Issue-first rules). `gh api` reports the repository as public, so minutes do not decide this choice.
- **Risk**: A Windows-only guard regression reaches `main` unseen by CI. Mitigation: the local Windows gate in T-LOCAL-GATES and the follow-up issue.

## D-7. Place the note in the setup guide

- **Decision**: Add `### Guardrail tests on Windows` under `## Step 4: Check the setup` (RC-24), before `## Work on a change`.
- **Alternatives considered**:
  - Add the note to `documentation/quality-gates.md`. That file describes the CI gates, not the workstation setup.
  - Add a new document under `documentation/`. This option adds a child to that folder and splits one fact across files.
  - Add no note. The guide then describes a Windows run that no longer matches the tests.
- **Rationale**: Step 4 is the first check a Windows workstation user runs. The note refers to the uv search order that `documentation/development-setup.md` already states (RC-23). AGENTS.md requires same-change documentation updates (RC-36, line 338).
- **Risk**: The note drifts when a skip changes. Mitigation: the note names each test file, and T-LOCAL-GATES runs the container policy guard (RC-25).

## D-8. Add one changelog fragment

- **Decision**: Add `changelog.d/issue-4917-windows-guardrail-tests.md` with one `###` heading and one `Fixed` bullet.
- **Alternatives considered**:
  - Add no fragment. The repository instructions require a fragment only for a change that a user sees (RC-33).
  - Add the fragment. This option is chosen. The constitution requires one fragment for each change (RC-30).
- **Rationale**: The constitution governs this repository. The file name matches the `ISSUE_NAME` pattern in `tests\guardrails\test_changelog_fragment_policy.py` line 39 (RC-48). The process-record exception allows a unique child under `changelog.d/` (RC-32).
- **Risk**: A reviewer may read a test-only fragment as noise. The constitution requires the fragment, so the change keeps it.

## D-9. Record Principle IV steps 10 and 11 as not triggered

- **Decision**: Record that the main image build does not run for this change. T-MERGE checks the merged commit on `main` with `gh api`.
- **Alternatives considered**:
  - Dispatch `container-build.yml` after the merge. The build publishes an image with the same product code.
  - Record the non-trigger and check the merged commit. This option is chosen.
- **Rationale**: The push trigger does not list `tests/`, `changelog.d/`, or `documentation/development-setup.md` (RC-19). This change touches tests, one setup note, and one fragment.
- **Risk**: A reviewer may expect an image build. The plan records this reason in its constitution check.

## D-10. Edit six existing test files and add no module

- **Decision**: Change six existing test files. Add no helper module and no new test file under `tests\guardrails`.
- **Alternatives considered**:
  - Add a shared skip helper under `tests\guardrails\`. That folder holds 79 tracked children (RC-40). The constitution forbids a new direct child in a noncompliant parent (RC-31).
  - Add a shared helper module under `tests\support\`. Only two files need the skip logic, and the three skip conditions differ in form.
- **Rationale**: Each change is small and differs by file. A new module would add structure without shared logic.
- **Risk**: Two skip reasons repeat in two files. The repetition is accepted.

## Remote verification

The table lists each remote check. The count is 48 rows. The same 48 checks appear in `remote_checks` of `META_DIR\4917-STATUS.json`. A blob SHA of `none (tree listing)` marks a fact derived from the recursive tree.

| ID | Claim | Path | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- |
| RC-01 | Browser test helper runs `bash` through `subprocess.run` | `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` | `c888d9b8a54fee953fb5db98660a63f44ccfa1c6` | present | 63 |
| RC-02 | Five browser test functions call `execute`, starting at `test_setup_removes_only_the_slow_route_and_preserves_a_backup` | `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` | `c888d9b8a54fee953fb5db98660a63f44ccfa1c6` | present | 71 |
| RC-03 | YAML-only browser contract test exists and does not run Bash | `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` | `c888d9b8a54fee953fb5db98660a63f44ccfa1c6` | present | 66 |
| RC-04 | SNMP shell-override test runs `/bin/bash` | `tests/guardrails/test_snmp_base_oid_defaults.py` | `c04297ce81c9c9f005a54fa655354c064138a3b9` | present | 95 |
| RC-05 | Export guard finds uv with `shutil.which("uv")` only | `tests/guardrails/test_dependency_export.py` | `a2a3e279dbfefb5292923d745cffa4ea4c66654d` | present | 41 |
| RC-06 | Missing-uv test patches `shutil.which` with a one-argument lambda | `tests/guardrails/test_dependency_export.py` | `a2a3e279dbfefb5292923d745cffa4ea4c66654d` | present | 135 |
| RC-07 | Symlink fixture calls `symlink_to` without privilege handling | `tests/guardrails/test_spec_route_contract.py` | `b174399ad5f23f4844dc442954bf203be07342f3` | present | 296 |
| RC-08 | Precedent: a Bash step skips on Windows with a stated reason | `tests/guardrails/test_dependency_lock_workflow.py` | `e529b5c8dc2ce363c670a42595070135fac230c4` | present | 110 |
| RC-09 | Precedent: a missing uv skips with the cause printed | `tests/guardrails/test_dependency_lock_file.py` | `1e398e42c443073ae7df64984e3da298df345395` | present | 82 |
| RC-10 | Git root is compared with the text of `str(Path)` | `tests/guardrails/local_test_quality_loop/test_scope.py` | `2c3645416c5c96cd6d1a788221a1ce04376ef447` | present | 643 |
| RC-11 | Missing-root message uses a list `repr`, and the regex uses a raw path | `tests/guardrails/test_analytics_package_structure.py` | `ee79f1f39ecf1621f7e303aa452979091d2922b4` | present | 75 |
| RC-12 | All 27 CI runner lines name `ubuntu-latest` | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 142 |
| RC-13 | The Ubuntu shard at lines 248 to 255 passes `tests/guardrails` to pytest | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 255 |
| RC-14 | CI installs `requirements-dev.txt` before the export guard runs | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 650 |
| RC-15 | CI runs the Ubuntu mirror step as a Bash heredoc | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 842 |
| RC-16 | `MYPY_PATHS` names no path under `tests/` | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 93 |
| RC-17 | Windows timeout workflow runs one guard file on `windows-latest` | `.github/workflows/windows-timeout-budget.yml` | `1caf671d77b9a4462a7cd06aa4c3fe481023aaa0` | present | 61 |
| RC-18 | Windows audit workflow runs two e2e tests on `windows-latest` | `.github/workflows/windows-audit-report.yml` | `2d4e608b038dbe20f522bd296f707126a0ad37bb` | present | 62 |
| RC-19 | Container build push trigger does not list `tests/`, `changelog.d/`, or the setup guide | `.github/workflows/container-build.yml` | `737325976de75e90aa4526ab1cf2978782e648ce` | present | 6 |
| RC-20 | Spec route resolver computes the numbered route from base-5 segments | `.specify/scripts/powershell/spec-route.ps1` | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 34 |
| RC-21 | Development requirements pin `uv==0.13.9` | `requirements-dev.txt` | `9a528bfe03a10f7bc903f5768ef26de765bbff43` | present | 470 |
| RC-22 | Bootstrap finds uv on PATH and then in per-user folders | `scripts/bootstrap_worktree.py` | `e16515ffa789cca7d0bdd7e9789898588e5f1312` | present | 300 |
| RC-23 | Setup guide states the uv search order | `documentation/development-setup.md` | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 57 |
| RC-24 | Setup guide has the Step 4 heading where the new note goes | `documentation/development-setup.md` | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 168 |
| RC-25 | Container policy guard reads the setup guide | `tests/guardrails/test_container_policy_docs.py` | `1b842c302e52bcb43a95e4a2aed2366a93d94909` | present | 63 |
| RC-26 | Container start script holds the SNMP default assignment | `container/scripts/start.sh` | `3b138807883a8a8785bac7d8c9b7f9a79458ed0c` | present | 270 |
| RC-27 | Ruff and Black line length is 120 | `pyproject.toml` | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | present | 202 |
| RC-28 | Constitution requires an inline comment on each line of generated code | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 206 |
| RC-29 | Constitution Principle IV defines the full deployment pipeline | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 143 |
| RC-30 | Constitution requires one release note fragment for each change | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 409 |
| RC-31 | Constitution forbids a new direct child in a noncompliant parent | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 42 |
| RC-32 | Constitution exception permits a unique record under `changelog.d/` | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 46 |
| RC-33 | Repository instructions name the fragment rule for a change that a user sees | `.github/copilot-instructions.md` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 451 |
| RC-34 | Windows full-suite command includes `tests\guardrails` | `.github/copilot-instructions.md` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 88 |
| RC-35 | AGENTS.md rule: a guard that skips prints the cause | `AGENTS.md` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 142 |
| RC-36 | AGENTS.md rules: same-change documentation updates and the STE gate for each Markdown file | `AGENTS.md` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 338 |
| RC-37 | AGENTS.md limits: 20 words for an instruction and 25 words for a description | `AGENTS.md` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 48 |
| RC-38 | Route folder `specs/numbered/0/0/1/2/4/1/3/2` has no entries on `main` | `specs/numbered/0/0/1/2/4/1/3/2` | none (tree listing) | absent | 0 |
| RC-39 | No record folder whose name starts with `4917-` exists on `main` | `specs` | none (tree listing) | absent | 0 |
| RC-40 | `tests/guardrails` holds 79 tracked direct children on `main` | `tests/guardrails` | none (tree listing) | present | 0 |
| RC-41 | Constitution Principle VII requires a log line before and after each action | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 237 |
| RC-42 | Repository gates table starts at the `## Local gates` heading | `.github/copilot-instructions.md` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 50 |
| RC-43 | Test quality ratchet procedure is a named section with a required check | `.github/copilot-instructions.md` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 95 |
| RC-44 | Constitution file paths rule: use `pathlib` or `os.path.join`, and keep Windows compatibility | `.specify/memory/constitution.md` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 310 |
| RC-45 | Route capacity guard rejects a new child under a parent that holds five children | `.specify/scripts/powershell/spec-route.ps1` | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 93 |
| RC-46 | AGENTS.md rule: claim the issue with `in-progress` and branch from `main` only | `AGENTS.md` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 187 |
| RC-47 | CI path variables for the lint, complexity, and documentation gates name no changed file (`RADON_PATHS` at line 99 names six paths, and `SRC_PATH`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` at lines 78, 101, 104, and 107 name `src` and product modules) | `.github/workflows/ci.yml` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 99 |
| RC-48 | Changelog fragment policy accepts issue fragments named `issue-<number>-<slug>.md` | `tests/guardrails/test_changelog_fragment_policy.py` | `dbd5e8776797f12536b3bc2bd613143b85f3fc4a` | present | 39 |

## Local-only evidence

These facts come from local reads. They do not prove that code is committed, so they support environment facts only.

- `.venv\Scripts\uv.exe` exists, and `.venv\Lib\site-packages\uv-0.13.9.dist-info` exists.
- `tests\guardrails` holds 80 direct children locally. The extra child is the untracked `__pycache__` folder.
- The local index blob SHA equals the remote blob SHA for 19 cited files. Those files are the six guard files, `test_changelog_fragment_policy.py`, `development-setup.md`, `AGENTS.md`, `copilot-instructions.md`, `constitution.md`, four workflow files, `requirements-dev.txt`, `bootstrap_worktree.py`, `start.sh`, and `pyproject.toml`.
- The local stdlib `Lib\shutil.py` line 1571 defines `which(cmd, mode, path=None)`. The directory is `C:\Users\jmorrison\AppData\Roaming\uv\python\cpython-3.15.2-windows-x86_64-none\Lib`.
- The local stdlib `Lib\pathlib\__init__.py` lines 199 to 207 define `_str_normcase` for Windows path comparison.
- Local `.venv\Lib\site-packages\misthelper_devtools\guard_proof_audit.py` lines 219 to 225 reject an unconditional module-level or all-test skip. Lines 258 to 259 state that `skipif` is environmental and allowed. Runtime `pytest.skip` calls inside a test body are outside that check.

## Sources

- Issue #4917 body, labels, state, and comment count: `gh issue view 4917 -R jmorrison-juniper/MistHelper`.
- PR #4918 body, merge state, and file list: `gh pr view 4918 -R jmorrison-juniper/MistHelper`.
- Issue #4916 state: `gh issue view 4916 -R jmorrison-juniper/MistHelper`, which reports CLOSED.
- Open pull request file overlap: `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,files`.
- Governing files, read in full: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`.
- Templates, read in full: `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- Reference record shape only: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. The record holds 14 files and three folders.
- Guides read for this issue: `documentation\quality-gates.md` and `documentation\development-setup.md`.
- Guides checked for applicability and not changed: `documentation\architecture.md` (headings only), `documentation\container-deployment.md` (headings only), and `documentation\operator-guide.md` (headings only). This change alters no runtime, container, or operator behavior.
- Microsoft Learn page on Developer Mode: `https://learn.microsoft.com/en-us/windows/advanced-settings/developer-mode`. The read portion states that enabling Developer Mode requires administrator access. It does not state a symbolic link privilege.
- The `mistapi` package: not used. This change makes no SDK claim.
- Skills: none loaded. No Podman or Juniper behavior is in scope.

## Unverified

- U-1: The issue states that the same 23 tests fail on `origin/main`. This record does not run the tests, so the claim is not reproduced.
- U-2: The issue does not give the SNMP failure text. The inference that `/bin/bash` causes the failure comes from RC-04 and needs a Windows run to confirm.
- U-3: This account lacks the symbolic link privilege. The issue reports it. This record does not check the privilege.
- U-4: Windows `uv export` may write the output path with backslashes in its header. `DependencyExport.render` depends on the same text. This record does not confirm the header form.
- U-5: Developer Mode grants the symbolic link privilege. The read portion of the Microsoft page does not say so, so this record makes no such claim.
- U-6: The PATH of the Windows workstation lacks `uv`. The issue reports it. This record does not read the process environment.
- U-7: The result of `test-quality-analyzer` for the changed tests. This record does not run the analyzer.
- U-8: The expected counts in `quickstart.md` are predictions. They come from the issue baseline and the parameter counts. A Windows run confirms them.
