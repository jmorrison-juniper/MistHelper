# Research: Entry-point test quality for HTTP status scope

## Decisions

### D-1 Repair with test edits only in this repository

- **Chosen**: Delete the duplicate argument test in `test_main_entrypoint.py`. Keep the rules, the baseline, and `src/` unchanged until the analyzer fix pins.
- **Alternatives**:
  1. Move the `ApplicationBootstrap` import out of the class body. Rejected. It hides a tool defect inside production code.
  2. Add HTTP 4xx and 5xx fixtures to the help tests. Rejected. The issue forbids artificial HTTP tests, and the help path sends no HTTP request.
  3. Accept the findings in the baseline. Rejected. The issue forbids a baseline change for this repair.
  4. Move the logging tests to a new module. Rejected. The finding moves with them, and the gate reports it as new.
- **Reason**: Only the analyzer fix can remove the false positive without changing rules or production code (RC-32 to RC-34). The repository change stays small and visible.
- **Risk**: Three modules keep their debt until the analyzer fix pins. Tasks T004 to T007 record the debt.
- **Recommended**: Yes.
- **Human decision required**: No.

### D-2 Fix the analyzer in misthelper-devtools

- **Chosen**: Change the analyzer in `misthelper-devtools`. Pin the fixed commit in this repository.
- **Alternatives**:
  1. Add `path_globs` entries under `[exclusions]` in `.github/test-quality-config.toml` (RC-66). Rejected. It skips files, so the findings disappear without a fix. The issue forbids disabling rules.
  2. Copy the analyzer into this repository. Rejected. Two copies of one tool drift apart.
  3. Change the analyzer in its owner repository. Chosen.
- **Reason**: The defect sits in the owner repository's code (RC-32 to RC-34). The pin already points to that repository (RC-28).
- **Risk**: The repair depends on another repository and its owner. Tasks T004 and T005 track the dependency.
- **Recommended**: Yes.
- **Human decision required**: No.

### D-3 Delete the duplicate argument test

- **Chosen**: Delete `test_empty_argument_list_reaches_normal_startup` (RC-12, lines 158 to 166).
- **Alternatives**:
  1. Convert the test to `MainEntrypoint.run`. Rejected. The help file already covers the same input (lines 51 to 69). A conversion repeats the case.
  2. Keep the test. Rejected. The test keeps an argument test on the bootstrap class, which the issue removes.
- **Reason**: Both tests send the same parser input, the program name only. Both expect the same `RuntimeError` from the startup stub and the same single call.
- **Risk**: A later change could separate the two cases. Task T001 verifies the surviving case before the deletion (T003).
- **Recommended**: Yes.
- **Human decision required**: No.

### D-4 Refresh stale entries with `--write-baseline` after the pin

- **Chosen**: After the pin, run `--write-baseline` on the full suite. Accept removed lines only.
- **Alternatives**:
  1. Run `--prune-baseline`. Rejected. It removes entries for absent files only (RC-37, RC-38). The two stale entries name a present file.
  2. Edit the baseline by hand. Rejected. A hand edit can hide a new finding.
  3. Keep the stale entries. Rejected. Known stale entries stay in the file for no reason.
- **Reason**: `--write-baseline` writes the current findings (RC-39). The diff then shows each removed and added entry.
- **Risk**: The fixed analyzer can change other entries. Task T007 stops on each added line (risk R-2).
- **Recommended**: Yes.
- **Human decision required**: No.

### D-5 Keep the issue open until the pin and the refresh merge

- **Chosen**: The final pull request body contains `Closes #4828`. The earlier pull request 4833 used `Refs`.
- **Alternatives**:
  1. Close the issue now. Rejected. The analyzer defect remains, and pull request 4833 states that the issue stays open.
  2. Keep `Refs` in the final pull request. Rejected. The issue would stay open after its last defect is gone.
- **Reason**: The issue names the analyzer fix as the remaining step. The pull request template holds the Linked Spec Issue field (RC-48). Principle IV step 7 requires the issue closure (RC-59).
- **Risk**: The issue waits on another repository. Task T004 and the blocker report track it.
- **Recommended**: Yes.
- **Human decision required**: No.

### D-6 Pin the analyzer in three files together

- **Chosen**: Change `pyproject.toml` (RC-29), regenerate `uv.lock` (RC-30), and regenerate `requirements-dev.txt` (RC-28).
- **Alternatives**:
  1. Change only `requirements-dev.txt`. Rejected. The CI job `dependency_lock` checks the lock (RC-25), and a mismatched file can fail that check (Unverified U-06).
  2. Edit `uv.lock` by hand. Rejected. A hand edit can break the lock checksums.
- **Reason**: The three files name the same commit in the same change. Dependabot pull request 4888 changes the same export file (RC-49).
- **Risk**: The regeneration can change other packages. Task T006 reviews the `uv.lock` diff.
- **Recommended**: Yes.
- **Human decision required**: No.

### D-7 Apply Principle IV steps 10 to 12 after the merge

- **Chosen**: After the merge, wait for `container-build.yml`, check the revision label, and check the deployment health.
- **Alternatives**:
  1. Skip the steps as a test-only change. Rejected. The workflow triggers on `pyproject.toml` and `uv.lock` (RC-41).
  2. Skip the steps and record a reason. Rejected. The trigger fires, so no reason applies.
- **Reason**: The constitution requires the steps for each change (RC-59). The trigger confirms that the change reaches the build.
- **Risk**: The deployment step needs an authorized operator. The orchestrator authorizes it (T-MERGE).
- **Recommended**: Yes.
- **Human decision required**: No.

### D-8 Record two interface contracts

- **Chosen**: Record `design\contracts\cli-entrypoint.md` and `design\contracts\test-quality-gate.md`.
- **Alternatives**:
  1. Omit the contracts. Rejected. The help behavior and the gate output are interfaces that the tests check.
  2. Record one contract. Rejected. The two interfaces change for different reasons.
- **Reason**: The entry-point contract from record 4758 states the help-test rule (RC-43). The gate output lines define the success measure (SC-001).
- **Risk**: Contracts can drift from the tests. Each contract cites the test lines it describes.
- **Recommended**: Yes.
- **Human decision required**: No.

## Remote Verification

Result values: `present`, `absent`, `stale`, `partial`. Line `0` means that no matching line exists. Local rows name the installed package. Their blob SHA is not applicable.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Help test on main imports MainEntrypoint and no bootstrap class | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py | main | a7c8cb9187f36163360a8805b9548ac402adc961 | present | 14 |
| RC-02 | Help test at revision 838046104 imports ApplicationBootstrap | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py | 838046104f606c008b034e0176ccd34ddf44a5f9 | 3abb63b0ced4bd73c858882bfad652bbec661d20 | present | 14 |
| RC-03 | Help test at commit 2a6a5844 has no bootstrap import | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py | 2a6a5844698aeb180fea353e0243034890774565 | fd602858ed44e3e603f05f562ca61f7ae0119d47 | absent | 0 |
| RC-04 | Commit aa8d12e9 set the help test to its current blob | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py | aa8d12e90fd68b5b22a44471b0606443e6ab9338 | a7c8cb9187f36163360a8805b9548ac402adc961 | present | 14 |
| RC-05 | Reject-flag test on main imports MainEntrypoint and no bootstrap class | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py | main | f23fe1c0b84872e42115f70e66020865cb2e0506 | present | 14 |
| RC-06 | Reject-flag test at revision 838046104 imports ApplicationBootstrap | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py | 838046104f606c008b034e0176ccd34ddf44a5f9 | ab6a7213bb173d6b00b9b3525b762edb0e347eb9 | present | 15 |
| RC-07 | Merge commit 7a4780e8 holds a reject-flag test that imports MainEntrypoint only | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py | 7a4780e87e45bea6074747963e9f0ec922eb5957 | ee2e419694e866c070908747f71abefcb0574209 | present | 14 |
| RC-08 | main_entrypoint.py defines class ApplicationBootstrap | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 107 |
| RC-09 | ApplicationBootstrap._install_log_sanitizer imports mistapi.__logger.LogSanitizer | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 222 |
| RC-10 | MainEntrypoint.run is the CLI entry point | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 400 |
| RC-11 | test_main_entrypoint.py imports ApplicationBootstrap | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py | main | 69e663203101a7cb911693fed6e0378120061910 | present | 31 |
| RC-12 | test_main_entrypoint.py builds ApplicationBootstrap with empty argv for a parser test | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py | main | 69e663203101a7cb911693fed6e0378120061910 | present | 162 |
| RC-13 | test_app_context_session_state.py imports ApplicationBootstrap | tests/unit/refactors/test_app_context_session_state.py | main | 6f28712d03b99e60b4405fcef3d95d823efb13f0 | present | 23 |
| RC-14 | test_fast_mode_small_seams.py imports ApplicationBootstrap | tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py | main | 64bddd7813edf4f436f99db362f32aaea2625be1 | present | 38 |
| RC-15 | Baseline holds a missing_fm_http_4xx entry for test_main_entrypoint.py | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 3156 |
| RC-16 | Baseline holds a missing_fm_http_4xx entry for test_app_context_session_state.py | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 3068 |
| RC-17 | Baseline holds a missing_fm_http_4xx entry for test_fast_mode_small_seams.py | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 3134 |
| RC-18 | Baseline holds a stale missing_fm_http_4xx entry for test_reject_unsupported_flag_variants.py | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | stale | 3189 |
| RC-19 | Baseline holds a stale missing_fm_http_5xx entry for test_reject_unsupported_flag_variants.py | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | stale | 3200 |
| RC-20 | Baseline holds no entry for the help test file | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| RC-21 | Test-quality config enables missing_http_4xx | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 29 |
| RC-22 | Test-quality config enables missing_http_5xx | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 30 |
| RC-23 | ci.yml runs the analyzer on the changed test scope for pull requests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 630 |
| RC-24 | ci.yml MYPY_PATHS lists source and entry files and no test path | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-25 | ci.yml dependency_lock job runs uv lock --check | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-26 | Test quality gate check succeeded on main head f03c6c9b | .github/workflows/ci.yml | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| RC-27 | ci.yml pins shared misthelper-devtools workflows at 79a5e459 (v0.6.4) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 681 |
| RC-28 | requirements-dev.txt pins misthelper-devtools at 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-29 | pyproject.toml pins misthelper-devtools at 2239e7bd | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 123 |
| RC-30 | uv.lock locks misthelper-devtools at 2239e7bd | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1586 |
| RC-31 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-32 | Analyzer inspects the whole class body for a class symbol | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 327 |
| RC-33 | Analyzer lists mistapi among the HTTP status modules | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 42 |
| RC-34 | Analyzer maps a from-import of a listed module root to HTTP status risk | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 374 |
| RC-35 | Analyzer emits missing_fm_http_4xx | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 708 |
| RC-36 | Analyzer emits missing_fm_http_5xx | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 717 |
| RC-37 | Analyzer baseline marks entries for unscanned paths as stale | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 160 |
| RC-38 | Analyzer --prune-baseline drops only the stale entries | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 352 |
| RC-39 | Analyzer --write-baseline replaces the baseline with the current findings | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 311 |
| RC-40 | quality-gates.md limits prune to deleted test files and warns about --roots | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 29 |
| RC-41 | container-build.yml runs on a push to main that changes pyproject.toml | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 12 |
| RC-42 | wsgi.py starts the web bootstrap through ApplicationBootstrap | wsgi.py | main | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 32 |
| RC-43 | Entry-point contract in record 4758 says help tests use the real parser | specs/numbered/0/0/1/2/3/0/1/3/4758-strict-pyright-repairs/design/contracts/entrypoint.md | main | 70a4a73d9dedb670c4b1144415f0ea9efee39e19 | present | 10 |
| RC-44 | spec-route.ps1 sets base 5 for numbered route digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-45 | Constitution requires managed roots and the base-5 route for numbered records | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-46 | Preflight guard reads the copilot-instructions guide and three test-quality inputs | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 18 |
| RC-47 | copilot-instructions defines the test quality ratchet procedure | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-48 | Pull request template holds the Linked Spec Issue field | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 3 |
| RC-49 | Open pull request 4888 head changes requirements-dev.txt | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 197 |
| RC-50 | Installed misthelper-devtools 0.6.4 records commit 2239e7bd | .venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json | installed package (local) | not applicable: installed package metadata | present | 1 |
| RC-51 | Installed mistapi 0.64.1 defines class LogSanitizer | .venv\Lib\site-packages\mistapi\__logger.py | installed mistapi 0.64.1 (local) | not applicable: installed package file | present | 202 |
| RC-52 | Analyzer baseline keys include category, rule ID, file path, line number, and explanation | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 6 |
| RC-53 | ci.yml ruff job runs ruff check . | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| RC-54 | AGENTS.md Issue first: claim the issue with the in-progress label and add type and scope labels | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| RC-55 | AGENTS.md Branch: branch name, worktree, branch from main, and force-with-lease push | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 192 |
| RC-56 | AGENTS.md Commit: Conventional Commits format with a Closes line | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 208 |
| RC-57 | AGENTS.md Pull request: one change, Closes in the body, auto-merge label after green checks | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-58 | AGENTS.md Merge: squash merge, delete the branch, no push after the merge | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 233 |
| RC-59 | Constitution Principle IV steps 7 (issue closure) and 10 to 12 (container build, revision label, deploy) | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| RC-60 | Constitution Testing: py_compile of MistHelper.py must pass before every commit | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 370 |
| RC-61 | Constitution Complexity-Driven SpecKit Escalation: a spec for three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| RC-62 | copilot-instructions Language and environment: Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |
| RC-63 | copilot-instructions Local gates table of commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-64 | copilot-instructions Git and GitHub: a user-visible change adds a changelog fragment | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-65 | copilot-instructions Move a module: guardrail command table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 261 |
| RC-66 | Config [exclusions] table holds path_globs that skip matched files | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 62 |

The table holds 66 rows. Each row matches one entry in `STATUS.json` `remote_checks`, in the same order.

## Sources

### Repository files checked by blob SHA

The local copies of these files match the GitHub blob SHA. Their local line numbers equal the remote line numbers. Method: `git hash-object --no-filters` on each local file, compared with the tree of `main`.

- `AGENTS.md` (44a9afff), `.github/copilot-instructions.md` (f1ec2a46), `.specify/memory/constitution.md` (4584997a), `documentation/quality-gates.md` (6776d334), `.github/workflows/ci.yml` (d51efbc1), `.github/test-quality-config.toml` (d0c88405), `.github/test-quality-baseline.json` (512da22b), `requirements-dev.txt` (9a528bfe), `requirements.txt` (50fe63d4), `src/foundation/support/refactors/main_entrypoint.py` (1402beb8), `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py` (a7c8cb91), `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` (f23fe1c0), `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` (69e66320), `tests/unit/refactors/test_app_context_session_state.py` (6f28712d), `tests/guardrails/local_test_quality_loop/test_guidance.py` (1f49b5fe), `.github/PULL_REQUEST_TEMPLATE.md` (ed03e8f3).
- `.specify/scripts/powershell/spec-route.ps1` does not match. Its local hash is 671e0b4e, and the `main` blob is 37293a25. The rows use the remote copy.

### Remote reads (GitHub, read-only)

- Issue #4828: open, labels `bug` and `tests`, no comments, created 2026-11-18T03:51:12Z.
- Pull request #4833: merged 2026-11-19T06:49:59Z. Merge commit `7a4780e87e45bea6074747963e9f0ec922eb5957`. It changed one file, `test_reject_unsupported_flag_variants.py` (+28, -12). Its check `Test quality ratchet (gate)` succeeded.
- Commit `aa8d12e90fd68b5b22a44471b0606443e6ab9338` (pull request #4853, 2026-11-19T23:48:58Z, "fix: resolve strict Pyright diagnostics"). It changed the help test (+85, -137), `main_entrypoint.py` (+12, -13), `test_main_entrypoint.py` (+89, -28), `test_run_interactive_test.py` (+5, -5), `test_app_context_session_state.py` (+132, -2), the reject-flag test (+1, -1), and record 4758.
- Commit `2a6a5844698aeb180fea353e0243034890774565` (2026-11-13). It is the last earlier commit that changed the help test on `main`.
- Commit `838046104f606c008b034e0176ccd34ddf44a5f9` (2026-11-18, "fix(types): remove verified unused private startup code"). The compare call against `main` reports `diverged`. `main` holds 42 commits that the revision lacks, and the revision holds 4 commits that `main` lacks.
- Issue #4758: closed 2026-11-19T23:49:00Z. Labels `bug`, `MistHelper.py`, and `in-progress`.
- Check runs on commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`: `Test quality ratchet (gate)` succeeded at 07:18:05Z. `Ruff (lint)`, `Black (format check)`, `mypy (strict)`, and the pytest coverage shards also succeeded.
- Open pull requests: seven. Pull request 4888 (head `e86098cdc2b189d217805b3b4060ef609cbc37af`, branch `dependabot/pip/mando-0.8.2`) changes `requirements-dev.txt`.
- Code search for `ApplicationBootstrap` returned 18 paths. The paths include the three modules in RC-11, RC-13, and RC-14, `wsgi.py` (RC-42), and record files that mention the class (Unverified U-09).
- Issue search in `jmorrison-juniper/misthelper-devtools` for "failure mode class body", "MissingFailureModeDetector", and "4828" returned no results (Unverified U-04).
- Repository tree of `misthelper-devtools` at `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (411 entries). The commit message is "fix(test-quality): scan full gate scope when changed tests are excluded (#95)".

### Installed packages (local, read-only)

- `.venv\Lib\site-packages\mistapi\__logger.py`: class `LogSanitizer(logging.Filter)` at line 202 (RC-51).
- `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json`: `commit_id` 2239e7bd (RC-50).
- Installed `mistapi-0.64.1.dist-info` confirms version 0.64.1.

### Shape-only references

- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`: spec 240 lines, plan 153, tasks 190, analysis 148, `design\research.md` 98, `design\checklists\requirements.md` 29. Only the file shape and section depth were copied.
- Spec Kit templates `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`: headings only.
- Other documents read for applicability: `documentation\development-setup.md`, `documentation\architecture.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`. No claim in this record depends on them.
- Mist API documents: not used. This issue makes no Mist API claim. The OpenAPI file and endpoint lists were not needed.

### Web and skills

- No URL was fetched with `web_fetch`.
- No skill was loaded. The issue has no Podman question and no Juniper device question.

## Unverified

- **U-01**: The analyzer did not run on `main` or on the issue revision. Reason: the brief bars running gates. Findings rest on RC-01 to RC-07, RC-11 to RC-14, and RC-32 to RC-36.
- **U-02**: The analyzer fix may not clear all three modules. Reason: no fix exists yet.
- **U-03**: The gate output in the issue body was not reproduced. Reason: the brief bars running gates. RC-02 and RC-06 confirm the imports at that revision only.
- **U-04**: No misthelper-devtools issue covers the defect. Reason: three searches found none. A different wording can hide an issue.
- **U-05**: The container build, the revision label, and the deployment after the merge are unverified. Reason: no pipeline has run. T-MERGE covers them.
- **U-06**: The output of `uv lock` and `uv export` for the pin change is unverified. Reason: `uv` was not run. The effect of a mismatched file on RC-25 is inferred.
- **U-07**: The final content of pull request 4888 is unverified. Reason: the pull request is open and may change.
- **U-08**: The fixture folder `src/misthelper_devtools/test_quality_analyzer/fixtures/good/` is inferred. Reason: the installed layout suggests it. The repository tree was not read for that folder.
- **U-09**: The code search may lag or miss files. Reason: the search index has no completeness guarantee.
- **U-10**: The behavior of mistapi outside `__logger.py` is unverified. Reason: only the `LogSanitizer` class (RC-51) was read. The analyzer rule (RC-34) treats the whole `mistapi` root as HTTP risk.
