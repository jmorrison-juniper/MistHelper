# Research: RADIUS API Failure Test Assertion

## 1. Issue Facts

Source: `gh issue view 4798` on 2026-11-26. Repository `jmorrison-juniper/MistHelper`.

- **Title**: "Test failure: RADIUS API failure test has no assertion".
- **State**: OPEN. Created 2026-11-15T04:15:08Z. Updated 2026-11-16T02:13:41Z. Author `jmorrison-juniper`.
- **Labels**: `bug`, `tests`, `in-progress`.
- **Requirement 1**: "The test should verify that the operator receives the contained failure message."
- **Requirement 2**: "No production code change is necessary."
- **Requirement 3**: "The baseline must remain unchanged."
- **Requirement 4**: "The correction needs one assertion for the existing failure output."
- **Environment**: "Local (Linux/Mac). Python 3.15.2."
- **Candidate**: Local review candidate `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693` for #4208. Base `2a6a5844698aeb180fea353e0243034890774565`.
- **Reproduction step**: Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` on the candidate.
- **Error text** (verbatim):

```text
detector_metric: WeakAssertionDetector.inspected_modules=17
gate_scope: 17 files checked, 2 findings checked
test_quality_analyzer: 2 findings (0/0/2/0), 2 skipped, 0 parse errors
gate: 1 new findings vs baseline
gate_new: weak_zero_assertions tests/unit/refactors/test_wlanradius_timer_manager_paths.py:707 Test function 'test_an_api_failure_is_contained' contains no assertions.
```

- **Comment** (owner, `OWNER` association, 2026-11-16T02:13:41Z): The repair is in open PR #4208 at head `843be63bc837513b4442dae69da9f0db922e0ed1`. The test asserts that captured output contains "Error applying changes: no route". Keep the issue open until the candidate merges. No second agent or overlapping PR is needed for this file.
- **Comment count**: One comment in total.

## 2. Linked Work and Existing Record

- **PR #4208** (`gh pr view 4208`): OPEN and unmerged. Title "feat(web-portal): integrate WAN performance dashboards". Head `843be63bc837513b4442dae69da9f0db922e0ed1`. Base `main`. Branch `jmorrison-juniper-4200-migrate-mistwanperformance`. `isDraft` true. `mergeStateStatus` DIRTY. `reviewDecision` empty. 82 changed files. The test module shows +17 -3 across the PR, which includes the fixture repair.
- **PR #4208 body**: "Refs #4200, #4793, #4794, #4795, #4797, and #4798. This PR does not close #4200."
- **PR #4208 checks at head**: 52 checks. 42 SUCCESS. 10 SKIPPED. No failure. `Test quality ratchet (gate)` reports SUCCESS. `Ruff (lint)`, `Black (format check)`, `Bandit (security)`, `mypy (strict)`, and `Conventional Commits PR title` report SUCCESS.
- **Open PR overlap** (`gh pr list --state open`): 7 open PRs. Only PR #4208 lists `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`. No other open PR lists `.github/test-quality*` or `src/foundation/support/refactors/wlanradius_timer_manager.py`.
- **Issue #4797** (`gh issue view 4797`): OPEN. Title "Test failure: resolver host persists after WLAN RADIUS fixture". Labels `bug`, `tests`, `in-progress`. The body says the fixture binds the shared resolver and does not restore the previous host. It asks for a teardown restore, not a production change.
- **Commits** (one `gh api` call per commit): `2a6a5844698aeb180fea353e0243034890774565` at 2026-11-13T19:33:49Z, "refactor(tests): organize verified unit-test domain groups". `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693` at 2026-11-15T04:13:11Z, "test: restore the WLAN RADIUS fixture resolver host". `843be63bc837513b4442dae69da9f0db922e0ed1` at 2026-11-15T04:15:27Z, "test: verify the contained RADIUS failure message".
- **Compare** of commit `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693` with commit `843be63bc837513b4442dae69da9f0db922e0ed1`: status ahead. `ahead_by` 1. `behind_by` 0. One changed file, the test module, with +2 -1.
- **Existing record**: None. Glob `specs\**\4798-*` finds no match. A recursive directory search for `4798-*` finds no match. The remote tree query finds no path that contains `4798` (RC-52). The route folder `specs\numbered\0\0\1\2\3\1\4\3` is absent locally and on `main` (RC-51). The legacy-record steps therefore do not apply.
- **Remote tree**: One recursive call on `main` returned 11404 entries. `truncated` is false.

## 3. Remote Verification Table

Each row is one check. The table has 62 rows. `main` is the default branch. `local-venv` means a file in the local `.venv`, checked with `git hash-object` (a read-only hash). Line 0 means a file-level check. "Approximate scan" counts `assert` statements, `pytest.raises` calls, and `.assert_*` calls in each test body. It approximates the analyzer rule. It does not run the analyzer.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Test module exists on main at the issue path | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 0 |
| RC-02 | Main defines test_an_api_failure_is_contained with no assert in its body | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 694 |
| RC-03 | Main fixture fake_mh binds the shared resolver and yields with no restore | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 45 |
| RC-04 | Main sibling test test_a_failed_write_is_reported uses a split header and asserts captured stdout | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 723 |
| RC-05 | Approximate scan finds no other test function without an assert on main | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 0 |
| RC-06 | Assertion commit defines the target test with capsys at line 707 and asserts stdout at line 712, with no comment on lines 707, 710, or 712 | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 75b4bdc1abe393be8eadf50b0cbe299f23cfa458 | present | 712 |
| RC-07 | Commit 843be63 follows 1f4843c by one commit and changes only the test module, +2 -1 | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 75b4bdc1abe393be8eadf50b0cbe299f23cfa458 | present | 0 |
| RC-08 | Approximate scan finds no test function without an assert at 843be63 | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 75b4bdc1abe393be8eadf50b0cbe299f23cfa458 | present | 0 |
| RC-09 | Fixture repair 1f4843c defines the target test at line 707 with no assert | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 1f4843c20c43832ca6a85a7a26d31e4b2a5c9693 | 285a24dcdf432de42a77a786119c17b09edc3448 | present | 707 |
| RC-10 | Production _update_site_wlan at line 736 calls mistapi updateSiteWlan at line 742 | src/foundation/support/refactors/wlanradius_timer_manager.py | main | ede241d76d4cc0787b210fe0addbfc03a33edfe4 | present | 742 |
| RC-11 | Production _apply_changes at line 718 catches Exception at line 732, prints the failure line at line 733, and logs with logging.exception at line 734 | src/foundation/support/refactors/wlanradius_timer_manager.py | main | ede241d76d4cc0787b210fe0addbfc03a33edfe4 | present | 732 |
| RC-12 | Production class WLANRadiusTimerManager is the menu 148 entry | src/foundation/support/refactors/wlanradius_timer_manager.py | main | ede241d76d4cc0787b210fe0addbfc03a33edfe4 | present | 30 |
| RC-13 | MistHelper.py maps menu 148 to WLANRadiusTimerManager().manage() | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5120 |
| RC-14 | Baseline entry for the target test has line_number 694 and rule_id weak_zero_assertions | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 694 |
| RC-15 | Baseline holds nine entries for the test module | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RC-16 | Baseline holds 733 entries in total | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RC-17 | Config uses the key weak_no_assertions | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 24 |
| RC-18 | misthelper-devtools emits the rule weak_zero_assertions | src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 954ff75110492c221efba929f200225ac6415f54 | present | 245 |
| RC-19 | misthelper-devtools baseline key is the five-tuple that includes line_number | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 55 |
| RC-20 | misthelper-devtools gate counts new findings and exits 1 above zero | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 235 |
| RC-21 | misthelper-devtools stale check covers absent files only | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 156 |
| RC-22 | requirements-dev.txt pins misthelper-devtools to commit 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-23 | CI job test_quality_gate starts at line 602 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| RC-24 | CI job name is Test quality ratchet (gate) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 603 |
| RC-25 | CI pull request scope passes --changed-from origin/BASE_REF | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 630 |
| RC-26 | CI MYPY_PATHS lists product roots and no tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-27 | CI VULTURE_PATHS lists product roots and no tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-28 | CI PYDOCSTYLE_PATHS lists product roots and no tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-29 | CI INTERROGATE_PATHS lists product roots and no tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-30 | Quality-gates guide says the job gives both files to each analyzer run | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 23 |
| RC-31 | Local gates table row Test quality names the baseline gate result | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| RC-32 | Required check procedure begins after the local commit | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 124 |
| RC-33 | Repository forbids a baseline rewrite that hides a new finding | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 150 |
| RC-34 | Full-suite check requires zero new findings before push | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 149 |
| RC-35 | Unit shard measured at 1179.3 seconds | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 83 |
| RC-36 | Fragment rule applies to changes that a user sees | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-37 | Repository instructions give the mistapi pin as at least 0.64.0 and below 0.65 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-38 | pyproject.toml pins mistapi at least 0.64.1 and below 0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-39 | pyproject.toml sets the ruff line length to 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| RC-40 | pyproject.toml sets the black line length to 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 559 |
| RC-41 | Constitution requires an inline comment on each line of generated code | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 206 |
| RC-42 | Constitution requires action logging for each meaningful action | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 237 |
| RC-43 | Constitution states mistapi 0.59 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RC-44 | AGENTS.md bars a second open pull request that changes one file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 245 |
| RC-45 | AGENTS.md branch rule uses the type and issue form | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| RC-46 | AGENTS.md asks for Closes in the pull request body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-47 | AGENTS.md defines an action as an external request, file output, database operation, data transform, or operator question | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 107 |
| RC-48 | spec-route.ps1 uses base 5 for the numeric route | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-49 | spec-route.ps1 defines Resolve-SpecFeaturePath | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RC-50 | Test-quality guard file exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-51 | Route folder for issue 4798 is absent | specs/numbered/0/0/1/2/3/1/4/3 | main | none (no tree entry) | absent | 0 |
| RC-52 | No path in the tree contains 4798 | specs | main | none (no tree entry) | absent | 0 |
| RC-53 | Reference record spec file exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-54 | Installed mistapi 0.64.1 defines updateSiteWlan | .venv\Lib\site-packages\mistapi\api\v1\sites\wlans.py (local-venv) | local-venv | 45f2572e4e3b23ee8e4df9a7a061abef2423dcd4 | present | 184 |
| RC-55 | Installed mistapi metadata reads version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA (local-venv) | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 0 |
| RC-56 | Local gates table defines the Compile row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| RC-57 | Local gates table defines the Lint row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| RC-58 | Local gates table defines the Format row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| RC-59 | Local gates table defines the Tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-60 | Local gates table defines the Security lint row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| RC-61 | Local gates table defines the Symbols row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RC-62 | Method manage at line 90 is the menu 148 entry point and calls _apply_changes at line 106 | src/foundation/support/refactors/wlanradius_timer_manager.py | main | ede241d76d4cc0787b210fe0addbfc03a33edfe4 | present | 106 |

Method notes:

- The `main` rows came from one `gh api` contents call per file, with the query `?ref=main`. The content comes from base64 decoding.
- The devtools rows came from one `gh api` contents call per file, with the query `?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Blob SHAs for `main` came from the tree query and the contents response.
- The table rows match the `remote_checks` array in `META_DIR\4798-STATUS.json`. Both have 62 rows.

## 4. Local Evidence

- **Blob equality**: `git hash-object` (read-only) on `tests\unit\refactors\test_wlanradius_timer_manager_paths.py` returns `e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c`. That value equals the `main` blob (RC-01). The same check on `src\foundation\support\refactors\wlanradius_timer_manager.py` returns `ede241d76d4cc0787b210fe0addbfc03a33edfe4` (RC-10). Local line numbers therefore match `main` for these two files.
- **Tools in `.venv\Scripts`**: `python.exe`, `pytest.exe`, `ruff.exe`, `black.exe`, `bandit.exe`, `test-quality-analyzer.exe`, `symbol-diff.exe`, and `ste-linter.exe` exist. Their versions are unverified (U-5).
- **SDK**: The installed mistapi reads version 0.64.1 (RC-55). The package holds 288 Python files. `updateSiteWlan` is defined at `wlans.py` line 184 with the parameters `mist_session`, `site_id`, `wlan_id`, and `body` (RC-54). The production call at line 742 passes the session, the site identifier, the WLAN identifier, and the payload in that order (RC-10).
- **Mist API documentation (local)**: `documentation\mist-api-openapi31yaml.yaml` line 42486 has `operationId: updateSiteWlan`. `documentation\api\INDEX.md` line 1928 maps PUT `/api/v1/sites/{site_id}/wlans/{wlan_id}` to `updateSiteWlan`. These files support the Mist API claim in `spec.md`. The change does not alter any request.
- **Menu cross-check (local)**: `documentation\menu_reference.md` line 185 maps menu 148 to `lambda: WLANRadiusTimerManager().manage()`. This agrees with RC-13.
- **Approximate scan method**: Each `def test_*` body is checked for `assert`, `pytest.raises`, or `.assert_*`. The method handles multi-line signatures. It is not the analyzer rule. The analyzer rule `weak_zero_assertions` appears in RC-18.
- **Tool note**: The `grep` tool does not search `.venv` in this environment. SDK searches used PowerShell `Get-ChildItem` and `Select-String`.

### Affected path

The path from the menu to the API call has five steps.

1. Menu 148 maps to `WLANRadiusTimerManager().manage()` at `MistHelper.py` line 5120 (RC-13). The local menu reference agrees (`documentation\menu_reference.md` line 185).
2. `manage()` at line 90 calls `_apply_changes()` at line 106 (RC-62).
3. `_apply_changes()` at line 718 dispatches on the inheritance level inside a `try` block. Its `except Exception` branch prints the failure line at line 733 and logs at line 734 (RC-11).
4. The site-level branch calls `_update_site_wlan()` at line 736. That method calls `mistapi.api.v1.sites.wlans.updateSiteWlan` at line 742 (RC-10). The installed SDK defines that function at `wlans.py` line 184 (RC-54).
5. The target test replaces `_update_site_wlan` with a double that raises `OSError("no route")` (RC-02). The module has separate test classes for the template and organization writes. This change does not touch them.

## 5. Decisions

Each decision has alternatives, a choice, a reason, a risk, and a recommendation. No decision needs a human.

### D-1 Delivery route

- **Alternatives**: (a) Open a new pull request from `main` with the same assertion. (b) Add a follow-up commit to PR #4208. (c) Push to `main` directly.
- **Chosen**: (b).
- **Reason**: `AGENTS.md` line 245 bars a second open pull request for one file (RC-44). The owner comment says no overlapping PR is needed. Commit `843be63` already carries the assertion and changes only the test module (RC-07). Option (c) breaks Principle IV, which bars a direct push to `main`.
- **Risk**: PR #4208 is a draft with merge state DIRTY (A-2). The PR ships 82 files with the fix (A-11). The `Refs` text keeps issue #4798 open after merge (A-3).
- **Recommended**: (b), with the fallback in `tasks.md` T-PR.

### D-2 Assertion form

- **Alternatives**: (a) Substring assert on `capsys` stdout. (b) Patch `print` and assert the call. (c) Use `caplog` on the `logging.exception` call at line 734. (d) Wrap the call in `pytest.raises`.
- **Chosen**: (a).
- **Reason**: The operator reads stdout. Line 733 prints the failure line (RC-11). Option (b) couples the test to `print`. Option (c) checks a log record that the operator does not read on the console. Option (d) fails, because `_apply_changes` catches `Exception` (RC-11). The sibling test uses the same form (RC-04).
- **Risk**: The failure text becomes a contract. A wording change fails the test. This is intended. See `design\contracts\operator-failure-message.md`.
- **Recommended**: (a).

### D-3 Baseline handling

- **Alternatives**: (a) Edit the baseline line from 694 to 707. (b) Run `--write-baseline`. (c) Run `--prune-baseline`. (d) Leave the baseline unchanged.
- **Chosen**: (d).
- **Reason**: FR-005 and the issue body require the baseline to stay unchanged. Option (a) hides the line-key defect (A-1). Option (b) rewrites all 733 entries (RC-16). Option (c) drops absent file paths only (RC-21), so it does not drop obsolete findings. Repository instructions forbid a rewrite that hides a finding (RC-33).
- **Risk**: Six obsolete entries remain (A-5). The gate ignores removed findings (RC-20).
- **Recommended**: (d).

### D-4 Scope boundary

- **Alternatives**: (a) Fix the `fake_mh` teardown in this issue. (b) Change the config key in this issue. (c) Change production code in this issue.
- **Chosen**: None of the three options.
- **Reason**: The issue body states that no production change is necessary (Requirement 2). Issue #4797 owns the fixture (RC-03). The config key belongs to misthelper-devtools (A-6).
- **Risk**: None for this change. Items A-6 and A-8 stay open.
- **Recommended**: Keep the scope. Track the other items in their own issues.

### D-5 Action logging

- **Alternatives**: (a) Add `logging.info` before the mocked call and `logging.debug` after it. (b) Add no log line.
- **Chosen**: (b).
- **Reason**: `AGENTS.md` line 107 defines an action as an external request, file output, database operation, data transform, or operator question (RC-47). The target test calls a mocked method. It writes no file and sends no request. The assertion checks a result. None of these is an action under that definition.
- **Risk**: A reviewer may apply Principle VII (RC-42) more widely. The citation above answers that reading.
- **Recommended**: (b).

### D-6 Local gate set

- **Alternatives**: (a) Run the full unit shard locally. (b) Run each applicable gate row for the changed file. (c) Run every gate row.
- **Chosen**: (b).
- **Reason**: The unit shard takes 1179.3 seconds (RC-35). The CI jobs run the shards. Several rows do not apply to a test file. Type checking, dead code, and docstring rows scan product roots only (RC-26 to RC-29). Coverage, complexity, and the menu rows apply to product code or menu changes that this change lacks.
- **Risk**: A cross-test interaction appears only in the CI shards. T-REMOTE-CI covers that risk.
- **Recommended**: (b). The quickstart lists the rows that run and the reason for each row that does not.

### D-7 Header and comment layout

- **Alternatives**: (a) Keep the one-line header with no comment. (b) Keep the one-line header with a trailing comment. (c) Split the header and put the comment on the closing line.
- **Chosen**: (c).
- **Reason**: Principle VI requires an inline comment on each line of generated code (RC-41). Option (b) exceeds 120 columns, at about 145 columns. The split form matches the header of `test_a_failed_write_is_reported` in the same module (RC-04). Black keeps the split form when the joined line with its comment exceeds 120 columns. T-LOCAL-GATES confirms the result.
- **Risk**: Black may format the header differently. T-LOCAL-GATES runs `black --check`.
- **Recommended**: (c).

## 6. Sources

Local sources (read or hashed, read-only):

- `AGENTS.md`, full file (RC-44 to RC-47).
- `.github\copilot-instructions.md`, lines 1 to 473 (RC-31 to RC-37, RC-56 to RC-61).
- `.specify\memory\constitution.md`, lines 1 to 462 (RC-41 to RC-43).
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The headings in these files shape the record.
- `documentation\quality-gates.md`, full file (RC-30).
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Only headings and the file list were read, to copy the shape. Its content was not copied.
- `.specify\scripts\powershell\spec-route.ps1`, full file (RC-48 and RC-49). The route for 4798 is `0\0\1\2\3\1\4\3`. It comes from the base-5 digits of 4798.
- `documentation\menu_reference.md` line 185, `documentation\api\INDEX.md` line 1928, and `documentation\mist-api-openapi31yaml.yaml` line 42486 (Mist API claims).
- `tests\unit\refactors\test_wlanradius_timer_manager_paths.py`, lines 1 to 66 and 676 to 730. Remote lines are in RC-01 to RC-09.
- `src\foundation\support\refactors\wlanradius_timer_manager.py`, lines 716 to 740. Remote lines are in RC-10 to RC-12.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\wlans.py`, lines 184 to 200 (RC-54).

Documents reviewed by search only. They were not used as evidence:

- `documentation\architecture.md`, `documentation\development-setup.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`. None of them covers the test-quality gate for one test module, a container for this change, or an operator-facing change in this issue.
- `documentation\MIST_API_GET_ENDPOINTS.md` and `documentation\MIST_API_MISSING_ENDPOINTS.md`. The change sends no request, so endpoint coverage does not change.

Remote sources (read-only GitHub API calls through `gh`):

- Issues `4797` and `4798`.
- Pull request `4208`, the list of open PRs, and the commit checks.
- Commits `2a6a5844698aeb180fea353e0243034890774565`, `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693`, and `843be63bc837513b4442dae69da9f0db922e0ed1`.
- The compare call for commits `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693` and `843be63bc837513b4442dae69da9f0db922e0ed1`.
- The recursive tree of `main`, with one call.
- File contents on `main`, on `843be63`, on `1f4843c`, and on the devtools commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

Upstream sources: The misthelper-devtools package is read from the GitHub repository `jmorrison-juniper/misthelper-devtools` at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. No `web_fetch` call or external URL was used.

Skills: None loaded. No listed skill covers the test-quality gate or PowerShell test runs for this change.

## 7. Unverified

- **U-1**: The identity of the second in-scope finding in the candidate gate run. Reason: the issue log does not name it. The arithmetic (2 findings, 1 new) shows one matched finding.
- **U-2**: The effect of the config key `weak_no_assertions` on the emitted rule `weak_zero_assertions`. Reason: `config.py` in misthelper-devtools was not read.
- **U-3**: Local test and gate results. Reason: rule 2 forbids running tests and gates in this phase. T004, T005, T007, and T-LOCAL-GATES run them.
- **U-4**: The check state on PR #4208 after a rebase or a new push. Reason: the status rollup is a snapshot from 2026-11-26.
- **U-5**: The installed misthelper-devtools version in `.venv` equals commit `2239e7bd`. Reason: the package metadata was not read. The executable `test-quality-analyzer.exe` exists.
- **U-6**: The record passes `ste-linter` at a score of 80 or above. Reason: rule 2 forbids linter runs in this phase.
- **U-7**: The target test passes under the pinned pytest version in `.venv`. Reason: no test run occurs in this phase.
