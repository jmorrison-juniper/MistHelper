# Research: Bound host restore for the WLAN RADIUS fixture (issue #4797)

**Scope**: Evidence for the record. Remote content from `jmorrison-juniper/MistHelper` outranks local search. Each code, test, configuration, or document claim cites a remote row (RC-nn) or a local source (S-nn).

## Summary

- Main and the candidate commit hold the same defect. The `fake_mh` fixture binds a fake host to the shared resolver and never restores it (RC-07, RC-08, RC-09).
- The fix exists in commit 1f4843c on open PR #4208. PR #4208 restores the bound host with `patch.object` (RC-06, RC-10). Main does not contain the fix.
- The issue test path and test name exist only on the PR head layout (RC-25, RC-26, RC-27, RC-29).
- Main admission does not read the shared resolver (RC-21). The visible failure from the issue is therefore a PR head layout effect.
- A static trace explains the reported error. The reproduction itself is not run (U-1).

## Issue Facts

- Issue #4797, title "Test failure: resolver host persists after WLAN RADIUS fixture". State OPEN. Labels `bug`, `tests`, `in-progress`. Created 2026-11-15T04:09:45Z. Updated the same time. Author `jmorrison-juniper`. No comments.
- Body records reconstruction candidate `2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473`, based on main `2a6a5844698aeb180fea353e0243034890774565`.
- Reporter reproduction, Linux form: `.venv/bin/python -m pytest -q tests/unit/refactors/test_wlanradius_timer_manager_paths.py tests/unit/wan_performance/test_request_admission.py::test_site_request_uses_the_selected_organization_context --tb=short --show-capture=no`.
- Reported error text: `ConnectionError: Site API request admission requires a selected organization.` Reported result: `1 failed, 169 passed, 1 warning in 6.78s`.
- Reported traceback lines: test line 230, `request_admission.py` lines 195 and 212. Remote candidate content matches these lines (RC-23, RC-25).
- Reported root-unit chunk: `1 failed`, `26141 passed`, `24 skipped`. Unverified (U-3).
- Requirement from the body: restore the fixture-owned resolver host at teardown, not production admission.
- Related review preparation: PR #4208.

## Decisions

| ID | Decision | Alternatives | Chosen option and reason | Risk | Human |
| - | - | - | - | - | - |
| D-1 | Deliver the fix through PR #4208. Open no second pull request for the fixture file while #4208 is open. | (a) Open a pull request from main now. (b) Deliver through #4208. (c) Ask the owner to split commit 1f4843c. | (b). The rule forbids a second open pull request for one file (RC-30). The fix already exists on the PR head (RC-06, RC-10). | #4797 waits for #4208 to merge or close. | false |
| D-2 | Keep the `patch.object` restore from commit 1f4843c. | (a) Manual try and finally that captures the previous host. (b) A public accessor on the shared resolver. (c) A suite-wide autouse restore fixture. | (a) is equivalent but longer. (b) changes production code, which the issue excludes. (c) widens the effect to every test. The chosen option restores on exit with no production change (RC-10, RC-13). | `patch.object` writes a private attribute. A rename raises AttributeError, so the failure stays loud. | false |
| D-3 | Add the restore tests after PR #4208 closes. Use one parametrized fixture with two cases: a sentinel host and None. | (a) Add tests now to PR #4208. (b) Add a module that imports the fixture from another module. (c) Add no restore test. | The chosen option waits for closure (gate G-1). (a) edits the open PR. (b) imports a fixture across modules. (c) leaves the defect unguarded. Teardown runs in reverse setup order (S-4). | The restore tests depend on pytest teardown order (S-4). | false |
| D-4 | Verify with the reproduction pair and both shards on the PR head before the merge. Use main node IDs after the merge. | (a) Run the pair only. (b) Run both shards only. (c) Run the pair and both shards before and after the merge. | (c). The pair shows the candidate failure and the fixed pass. The shards show that no later test fails. | Shard 1 takes about 1179 seconds (RC-65). | false |
| D-5 | Add no changelog fragment for this internal-only change. | (a) Add `issue-4797-bound-host-restore.md`. (b) Add no fragment and state the reason in the pull request. | (b). The changelog README exempts internal-only changes (RC-41). AGENTS limits fragments to user-visible changes (RC-32). | A reader of constitution line 409 may expect a fragment (A-7). | false |
| D-6 | Add action logs to the new fixture only. Leave the PR #4208 fixture unchanged. | (a) Add logs to `fake_mh` in a new commit. (b) Add no logs. (c) Add logs to the new fixture only. | (c). Principle VII applies to new code (RC-40). Changing `fake_mh` would edit the open PR #4208, which D-1 forbids. | A reviewer may request logs in `fake_mh` (U-7). | false |
| D-7 | Run the Lint, Format, Tests, Full tests, and Test quality rows. Mark other rows not applicable with a reason. | (a) Run every row. (b) Run the rows that apply. | (b). The mypy, vulture, pydocstyle, and interrogate paths exclude `tests` (RC-57). The Symbols gate belongs to module moves (RC-73). Coverage measures `src` lines, and this change alters no `src` line. | A skipped row can hide a finding in an unlisted path. The diff review in T-PR limits that risk. | false |
| D-8 | Place the record in the follow-up pull request. Do not place it in PR #4208. | (a) Place it in a separate spec pull request. (b) Place it in PR #4208. (c) Place it in the follow-up pull request. | (c). One pull request holds one change (AGENTS). Option (b) edits the open PR, and option (a) adds a third pull request. | The record merges with the follow-up. | false |
| D-9 | Choose the merge timing of PR #4208. | (a) Merge #4208 after the orchestrator authorizes it. (b) Ask the owner to split commit 1f4843c and merge that commit first. (c) Hold #4208 until the feature is ready. | Recommended: (a). The 15 required checks pass on the PR head (Linked Pull Requests). Option (b) keeps the feature separate but needs owner work. Option (c) delays the fix without a stated reason. The choice sets product priority, so a human decides. | The fix waits while the decision waits. | true |
| D-10 | Run each check in a clean worktree at the commit under test. | (a) Run checks in the current working tree. (b) Run checks in a clean worktree. | (b). The local working tree differs from HEAD for two files (Local State). Truth order places GitHub content first. Each new worktree needs the bootstrap script (RC-35, RC-64). | A worktree needs a full bootstrap and extra disk space. | false |

## Linked Pull Requests

| Item | State | Details |
| - | - | - |
| PR #4208, "feat(web-portal): integrate WAN performance dashboards" | OPEN. `mergedAt` is null. | Head `843be63bc837513b4442dae69da9f0db922e0ed1` on branch `jmorrison-juniper-4200-migrate-mistwanperformance`. 82 changed files, including the fixture file, the admission module, and the wan_performance tests. |
| Fix commit 1f4843c in PR #4208 | Present on the PR head | Changes only `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` with 15 additions and 2 deletions (RC-06). Commit message: `test: restore the WLAN RADIUS fixture resolver host` with `Refs #4797`. |
| Commit 843be63 in PR #4208 | Present on the PR head | Changes the same fixture file with 2 additions and 1 deletion for issue #4798. Commit message: `test: verify the contained RADIUS failure message` with `Refs #4798`. |
| PR #4208 body | Text | Lists `Refs #4200, #4793, #4794, #4795, #4797, and #4798`. Uses `Refs`, not `Closes`, for #4797 (analysis A-2). |
| PR #4208 status rollup | 52 entries | 42 SUCCESS and 10 SKIPPED from `statusCheckRollup`. |
| PR #4208 checks | 44 entries | `gh pr checks` lists 15 required checks. All 15 show SUCCESS and pass. `Test quality ratchet (gate)` shows SUCCESS and pass. |
| Recovery branch | Exists | `recovery/4208-fixture-isolation-843be63` points to `843be63bc837513b4442dae69da9f0db922e0ed1` (`gh api` ref read). |
| Candidate versus PR head | Ancestor | Compare reports `ahead`, 2 commits, 0 behind. The two commits are 1f4843c and 843be63 (RC-03). |
| Candidate versus main | Diverged | Main has 52 commits that the candidate lacks. The candidate has 31 commits that main lacks (RC-04). |
| Base versus main | Ancestor | Base `2a6a584` is behind main by 52 commits and 0 commits ahead (RC-01). |

Related issues, read with `gh api`:

- #4798 is OPEN. Title: `Test failure: RADIUS API failure test has no assertion`.
- #4200 is OPEN. Title: `Spec: Integrate MistWANPerformance into MistHelper portal`.

## Remote Verification

Method: `gh api` tree and contents reads for `main`, the candidate commit, and the PR head. Each body decoded from base64. Lines come from the decoded text. Result `present` means the claim holds on the named ref. Result `absent` means the path or name does not exist on the named ref.

| ID | Claim | Path or object | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Base commit is an ancestor of main | commits/2a6a5844698aeb180fea353e0243034890774565 | main | 2a6a5844698aeb180fea353e0243034890774565 | present | 0 |
| RC-02 | Candidate commit exists | commits/2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | present | 0 |
| RC-03 | Candidate commit is an ancestor of the PR head | commits/843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| RC-04 | Candidate commit is an ancestor of main | commits/2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | main | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | absent | 0 |
| RC-05 | Local HEAD equals main | commits/f03c6c9b36d612a48d7b9652998c2fd87dd777ca | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-06 | Fix commit changes only the fixture file | commits/1f4843c20c43832ca6a85a7a26d31e4b2a5c9693 | 1f4843c20c43832ca6a85a7a26d31e4b2a5c9693 | 1f4843c20c43832ca6a85a7a26d31e4b2a5c9693 | present | 0 |
| RC-07 | Main fixture defines fake_mh | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 38 |
| RC-08 | Main fake_mh binds the bound host with no restore | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 45 |
| RC-09 | Candidate fixture equals main fixture | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 45 |
| RC-10 | PR head fixture restores the bound host through patch.object | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 75b4bdc1abe393be8eadf50b0cbe299f23cfa458 | present | 46 |
| RC-11 | bind_root_module stores the bound host | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 131 |
| RC-12 | Constructor sets the bound host to None | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 127 |
| RC-13 | Setter keeps _root_module on the resolver instance | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 178 |
| RC-14 | _test_host_override compares sys.modules with the bound host | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 286 |
| RC-15 | A test host answers a context read before the active context | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 203 |
| RC-16 | The context map sends org_id to the active context | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 25 |
| RC-17 | main_entrypoint binds the host module to the shared resolver | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 375 |
| RC-18 | MistHelper.py binds itself to the shared resolver at import | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 712 |
| RC-19 | conftest.py loads MistHelper.py into sys.modules | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | present | 170 |
| RC-20 | Main admission raises the site organization error | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 108 |
| RC-21 | Main _organization does not read the shared resolver | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 102 |
| RC-22 | Candidate _organization reads the shared resolver org_id | src/interfaces/wan_performance/collection/request_admission.py | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | 4cf92ab977bb667ef0fe4e72de68994a80f1ffea | present | 210 |
| RC-23 | Candidate admission raises the site organization error | src/interfaces/wan_performance/collection/request_admission.py | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | 4cf92ab977bb667ef0fe4e72de68994a80f1ffea | present | 212 |
| RC-24 | PR head admission module equals the candidate module | src/interfaces/wan_performance/collection/request_admission.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 4cf92ab977bb667ef0fe4e72de68994a80f1ffea | present | 210 |
| RC-25 | Candidate test calls admit at line 230 under a patched active context | tests/unit/wan_performance/test_request_admission.py | 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473 | d6368eb4b2483b1ed1faa934cba10a33fb0d5d67 | present | 230 |
| RC-26 | PR head contains the issue test function | tests/unit/wan_performance/test_request_admission.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d6368eb4b2483b1ed1faa934cba10a33fb0d5d67 | present | 216 |
| RC-27 | Main lacks the issue test path | tests/unit/wan_performance/test_request_admission.py | main | none | absent | 0 |
| RC-28 | Main wan_dashboard test file defines TestRequestAdmission | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | main | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | present | 28 |
| RC-29 | Main test file lacks the issue test function name | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | main | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | absent | 0 |
| RC-30 | AGENTS forbids a second open pull request for one file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 245 |
| RC-31 | AGENTS requires repair of a test that passes alone | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 138 |
| RC-32 | AGENTS limits changelog fragments to user-visible changes | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 342 |
| RC-33 | copilot-instructions pins mistapi to the 0.64 range | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-34 | copilot-instructions defines the test quality ratchet | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-35 | copilot-instructions records the worktree bootstrap pitfall | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 542 |
| RC-36 | Constitution limits each hierarchy level to five children | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| RC-37 | Constitution requires the deployment pipeline after each code change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 145 |
| RC-38 | Constitution requires one release fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-39 | Constitution requires a file overlap check | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 503 |
| RC-40 | Constitution defines Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-41 | The changelog README exempts an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-42 | spec-route default width is 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-43 | spec-route radix base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-44 | spec-route joins numbered segments under specs/numbered | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| RC-45 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-46 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-47 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-48 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-49 | No 4797 record or route folder exists on main | specs/numbered/0/0/1/2/3/1/4/2 | main | none | absent | 0 |
| RC-50 | Route parent holds child 1, the 4796 record | specs/numbered/0/0/1/2/3/1/4/1/4796-timestamp-validation/spec.md | main | 183911ea3adc3479463baae3e2ecc0df78680429 | present | 0 |
| RC-51 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-52 | Reference record tasks exist | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-53 | Process folder baseline lists numbered as a managed root | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 7 |
| RC-54 | Process folder guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-55 | Pytest is pinned to 9.2.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 325 |
| RC-56 | Pytest collects classes named Test | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 521 |
| RC-57 | CI mypy paths exclude tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-58 | CI test quality scope uses changed test files on pull requests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 630 |
| RC-59 | CI Ruff job runs ruff check on the repository | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| RC-60 | Test quality config defines the rule set | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 16 |
| RC-61 | Test quality baseline holds nine findings for the fixture file | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 3239 |
| RC-62 | Preflight test file exists for the test quality procedure | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-63 | Quality gates document lists the test quality gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| RC-64 | Development setup documents worktree bootstrap | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 183 |
| RC-65 | Unit shard timing measured at 1179.3 seconds | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 83 |
| RC-66 | host_resolver.py is the DNS resolver, not the shared resolver | src/foundation/persistence/db/host_resolver.py | main | f188aa5ee5ba99d6472d553d40b44bb0d7f11cae | present | 214 |
| RC-67 | Constitution names mistapi 0.59 or later | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RC-68 | Constitution PR checklist requires a closing reference and rollback notes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 516 |
| RC-69 | Local gates table defines the Lint row (line 58) and the Format row (line 59) | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| RC-70 | Local gates table defines the Tests and Full tests rows | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-71 | Full tests commands define shard 1 (line 87) and shard 2 (line 88) with a 120 second test timeout | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 87 |
| RC-72 | Test quality row names the analyzer gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| RC-73 | Symbols gate belongs to module moves | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 273 |

Row count: 73. The same 73 rows appear in the `remote_checks` array of the STATUS file.

## Mechanism Trace (static)

1. conftest loads MistHelper.py into `sys.modules` before tests run (RC-19).
2. The module import binds the real module as the bound host (RC-18, RC-17, RC-11).
3. `fake_mh` replaces the bound host with a fake host and does not restore it (RC-08). Candidate and main share this defect (RC-09).
4. A later candidate test patches `SourceDependencyResolver._active_context` and admits a site request (RC-25).
5. The candidate admission reads `org_id` through the shared resolver (RC-22). The same reader exists on the PR head (RC-24).
6. The `patch.dict` context restores `sys.modules` after `fake_mh`. The real module is the `sys.modules` entry. The bound host is the fake host. The two differ (RC-14).
7. Because the two differ, the resolver treats the real module as a test host. The `org_id` read returns from that test host before it reaches the patched active context (RC-15, RC-16).
8. The read yields no organization, so the admission raises at line 212 (RC-23). This matches the reported error text.
9. The PR head restores the previous host with `patch.object` (RC-10). The two identities match again after teardown, so the patched active context answers the read.

Runtime confirmation of steps 6 to 8 is not available in this session (U-1). Main admission does not run step 5 (RC-21), so the visible failure does not reproduce on main by static reading (U-5).

## Local State

Local working tree comparison against the index (`git hash-object` and `git ls-files -s`):

| File | Worktree blob | Index blob | Equal | Used for facts |
| - | - | - | - | - |
| tests/unit/refactors/test_wlanradius_timer_manager_paths.py | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | yes | No. Remote content is used. |
| src/foundation/runtime/config/source_dependency_resolver.py | 18c0e2b88560614a4c987510032fea4946b0fc7c | 18c0e2b88560614a4c987510032fea4946b0fc7c | yes | No. Remote content is used. |
| src/interfaces/wan_performance/collection/request_admission.py | 5ee19a82c40acbaf2b6364aebd2561b31fc981da | a6064e8fadce930813f8404f85d6b0b830c68cb6 | no | No. |
| tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | 526be2c14a388c7cc62a27d3005c33f80f3bb7aa | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | no | No. |

Caution: the local working tree holds uncommitted content for two files. Its `request_admission.py` contains an organization context variable that main does not contain. Do not run a check in that working tree. Decision D-10 applies.

## Not Applicable

- **Mist API**: The change calls no Mist endpoint. The record makes no endpoint claim, so no OpenAPI file is cited.
- **mistapi SDK**: The change calls no mistapi function. The record makes no SDK claim, so no installed source file is cited.
- **Podman and containers**: The change starts no container. `documentation/container-deployment.md` and `documentation/operator-guide.md` contain no fixture, resolver, or test-host term (local keyword search, not cited for facts).
- **Podman and Juniper skills**: Not applicable to Python fixture state.

## Sources

- **S-1**: `AGENTS.md`, remote blob 44a9afffb5bd6f774973a845d27343e4e528b6ad (RC-30, RC-31, RC-32).
- **S-2**: `.github/copilot-instructions.md`, remote blob f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 (RC-33 to RC-35, RC-65, RC-69 to RC-73).
- **S-3**: `.specify/memory/constitution.md`, remote blob 4584997a264c5a7ade2ca7441246e1f067083aa1 (RC-36 to RC-40, RC-67, RC-68).
- **S-4**: Local pytest 9.2.0 source. `.venv\Lib\site-packages\_pytest\runner.py` lines 560 to 576 pop finalizers in reverse order. `.venv\Lib\site-packages\_pytest\fixtures.py` line 1306 registers a fixture finalizer on the test node.
- **S-5**: Local environment. `.venv\pyvenv.cfg` reports version 3.15.2. `.venv\Lib\site-packages\pytest-9.2.0.dist-info` exists.
- **S-6**: Local hash comparison from the Local State section.
- **S-7**: `spec-drafts\_meta\validate-drafts.ps1`, a read-only validator for drafts. Run at self-review.
- **S-8**: The orchestrator brief, `spec-brief.md` in the session files folder.
- **S-9**: GitHub read results from `gh issue view`, `gh pr view`, `gh pr checks`, `gh pr list`, `gh api` compare, commit, ref, and tree reads.
- **S-10**: Remote `documentation/development-setup.md` (RC-64) and `documentation/quality-gates.md` (RC-63).
- **S-11**: Skill `debug-live`, loaded in this session. Its root-cause checklist was applied as a static method. Its live debugger steps need a test run, which rule 2 prohibits.
- **S-12**: No `web_fetch` call was made. No web source supports a claim in this record.

## Unverified

- **U-1**: The candidate failure is a static trace. No test ran. The sub-claim that `org_id` reads as None in a fresh context is not verified.
- **U-2**: The PR head pair pass is not run in this session.
- **U-3**: The reporter shard totals are not verified. The PR body statements about test totals are not verified.
- **U-4**: Whether MistHelper.py completes its import in a test session is not verified. The conftest comments record stop cases (RC-19).
- **U-5**: Other readers of the shared resolver in the suite are not enumerated. Main admission does not read it (RC-21).
- **U-6**: A restore after a failed test body is not tested. The design relies on the context manager contract of `patch.object`.
- **U-7**: Whether Principle VII requires logs in test fixtures is a reviewer decision (A-6).
- **U-8**: Constitution line 409 and changelog README line 58 conflict (A-7). The constitution owner decides.
- **U-9**: Whether Principle IV steps 10 to 12 apply to a test-only change is an orchestrator decision (RC-37).
- **U-10**: The PR #4208 closing reference and the merge timing depend on the owner (A-2, D-9).
- **U-11**: Restore after a failed test body (U-6) and the xfail alternative were not tested. No xfail marker is planned.

## Skills Used

- `debug-live`: static root-cause checklist only (S-11).
- No Podman or Juniper skill applies to this record.
