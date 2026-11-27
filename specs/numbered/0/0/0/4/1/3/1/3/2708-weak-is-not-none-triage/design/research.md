# Research: Test quality: triage weak_is_not_none findings

Each decision lists the chosen option, the other options, the reason, and the risk. Each remote claim has one row in the remote verification table. The table holds 139 rows. The same count appears in `META_DIR\2708-STATUS.json` and in the summary.

## Method

The baseline `.github/test-quality-baseline.json` on main has blob `512da22b0769e8343a4b5b734c507d6aa3969ac6`. It holds 733 entries in total. It holds 84 entries for `weak_is_not_none`. The gate compares findings against this file. A green `ci.yml` run on main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` indicates that the gate passed at that commit. The job-level result was not checked.

For each of the 84 entries, the per-line check reads the file body from main with `gh api contents`. The check decodes the base64 text. It reads the baseline line.

- If the line holds an `assert` statement with `is not None`, the result is present. An inline comment or message is allowed.
- Otherwise the check searches 60 lines above and below. A match at another line gives moved. No match gives stale.

Result: 65 present and 19 stale. The check finds no moved entry. The rule misses multi-line asserts and other forms. The analyzer run decides the final result (task T001).

## Decisions

### D-1. Scope source

- **Decision**: Use the 84 baseline entries on main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- **Alternatives**: The 67-entry report of 2026-11-10 (stale). A new analyzer run in this session (rule 2 forbids it).
- **Rationale**: The 2026-11-10 report names 13 paths that moved (absent on main). The baseline is the list that the gate compares. The `ci.yml` run on main succeeded at `f03c6c9b` (2026-11-26T07:16:40Z). The local report is untracked (remote tree row for `test_quality_analyzer_output/report.json` is absent).
- **Risk**: The baseline may hold stale entries. The per-line check found 19. Task T001 gives the analyzer count.
- **Human decision**: No.

### D-2. Repair method

- **Decision**: Replace each weak guard in place with one exact check on the same line. Keep the line count of the file.
- **Alternatives**: Delete the weak line. Accept the finding in the baseline. Rewrite the test.
- **Rationale**: The analyzer identity includes the line number (installed `baseline.py` lines 5 to 6 and 48 to 55). Deleting a line moves each later finding in the file. Accepting findings widens the gate, which the issue forbids.
- **Risk**: The replacement check must be correct. FR-004 requires one controlled failing run for each repair.
- **Human decision**: No.

### D-3. Redundant guards

- **Decision**: A redundant guard (category S) gets the same in-place replacement as other repairs. The guard is not deleted.
- **Alternatives**: Delete the redundant guard. Keep the guard unchanged.
- **Rationale**: Issue comments report that a later exact check already rejects the wrong value (comments dated 2026-11-10T03:11:21Z to 2026-11-10T04:38:19Z). An in-place replacement keeps the line count. A deletion would shift the file.
- **Risk**: The replacement must keep the later check. The guard must not weaken it.
- **Human decision**: No.

### D-4. No analyzer, config, or exclusion change in this repository

- **Decision**: Make no change to the analyzer, its config, its exclusions, or its markers in this repository. File the key mismatch upstream (task T018).
- **Alternatives**: Rename the config key here. Disable the rule. Patch the installed package.
- **Rationale**: The analyzer is an external pinned package (`requirements-dev.txt` line 197). Disabling a rule removes scope. The issue records that failure (comment dated 2026-09-18T04:27:52Z, which cites PR #2734 and issue #2736). The installed package is not a repository file.
- **Risk**: The key mismatch may change the gate result. Task T001 shows the actual result.
- **Human decision**: No.

### D-5. Holds for reserved files

- **Decision**: Do not edit a file that an open issue or pull request reserves. Tasks T011 to T014 stay open until the owner releases the file.
- **Alternatives**: Edit now and resolve the conflict later. Take over the reservation.
- **Rationale**: `AGENTS.md` line 244 requires an overlap check before work starts. Line 246 requires a declared file set. Two open changes to one file conflict.
- **Risk**: The holds delay the reduction for 11 entries.
- **Human decision**: No.

### D-6. Preserved candidates are evidence only

- **Decision**: Treat each local and archived candidate as evidence. Derive each repair again from main. Do not push to an archived branch.
- **Alternatives**: Cherry-pick the archived commit. Reuse a candidate blob. Open a pull request from an archived branch.
- **Rationale**: `AGENTS.md` line 254 forbids pushes to a branch another agent owns. Seven candidate blobs and one candidate commit are absent from GitHub (rows 36 and 43 to 49). The candidate for `fd7896f` repeats a repair that PR #3783 already merged (row 35 and the recovery branch row 42).
- **Risk**: Re-derivation takes more work per file.
- **Human decision**: No.

### D-7. Baseline update

- **Decision**: Update the baseline only with `test-quality-analyzer --write-baseline`, without `--roots`. Review the diff before each push.
- **Alternatives**: Edit the JSON by hand. Use `--prune-baseline`.
- **Rationale**: `documentation/quality-gates.md` line 36 documents the write command. Line 41 forbids `--roots`. The prune command removes entries only for deleted files, so it cannot remove repaired entries. Hand edits to a 370 KB file risk a broken identity.
- **Risk**: The write command rewrites all entries. The reviewer must confirm each changed entry.
- **Human decision**: No.

### D-8. Documented analyzer command

- **Decision**: Use the documented gate command. Do not use `python -m tools.test_quality_analyzer`.
- **Alternatives**: Add a `tools/` module that wraps the analyzer.
- **Rationale**: No `tools/` folder exists on main (analysis A-1). A wrapper would duplicate the package.
- **Risk**: The issue text stays stale. This record does not edit the issue (brief rule 5 forbids GitHub edits in this session).
- **Human decision**: No.

### D-9. Closing keywords

- **Decision**: Each slice gets its own child issue, created before its branch. The slice pull request closes that child issue and contains `Part of #2708`. The final slice also closes `#2708`.
- **Alternatives**: Use `Closes #2708` in every slice. This closed the issue on 2026-10-22. Use `Part of #2708` alone. This breaks the constitution PR rule.
- **Rationale**: The constitution PR checklist requires a closing reference in each pull request (constitution line 519, row 136). A child issue meets that rule and keeps `#2708` open. The claim and label rules apply to each child issue (constitution lines 487 and 500, rows 138 and 139).
- **Risk**: Eight child issues exist. The owner closes each one when its pull request merges.
- **Human decision**: No.

### D-10. Serial slices

- **Decision**: Merge one slice at a time. Rebase and rerun the required checks after each merge.
- **Alternatives**: Merge slices in parallel with auto-merge.
- **Rationale**: `.github/copilot-instructions.md` line 483 requires one serial merge slot until a queue is active. Each slice edits the baseline JSON (risk R-2).
- **Risk**: Eight slices take eight merge cycles.
- **Human decision**: No.

### D-11. Container steps do not apply

- **Decision**: Steps 10 to 12 of Principle IV do not apply to this change. The change does not trigger `container-build.yml`.
- **Alternatives**: Run the container build for each slice.
- **Rationale**: `.github/workflows/container-build.yml` line 6 starts its path filter. Lines 7 to 19 list product paths. The test paths are not in that list.
- **Risk**: A later slice could add a product file. Task T-MERGE checks the changed file list before merge.
- **Human decision**: No.

### D-12. No changelog fragment

- **Decision**: Add no changelog fragment. The change is internal and test-only.
- **Alternatives**: Add `issue-2708-weak-is-not-none-triage.md`.
- **Rationale**: `changelog.d/README.md` line 58 exempts an internal-only change. Constitution line 409 requires one fragment for each change. Analysis item A-12 lists the conflict for maintainer review.
- **Risk**: A maintainer may reject the choice. The pull request body states the reason.
- **Human decision**: No.

### D-13. Local gates for each slice

- **Decision**: Run compile, lint, format, the changed test file, Bandit, and `symbol-diff` for each slice. Run the mist-ops-platform correctness selector for its files. Run the test quality preflight, the changed-scope gate, and the full gate. Record each skipped gate and its reason.
- **Alternatives**: Run the full pytest chunks in each slice.
- **Rationale**: The changed-file gates cover the change. `ci.yml` line 93 excludes tests from the type gate. Line 101 excludes tests from the dead-code gate. The full suite runs in CI in the `pytest_coverage_shards` job.
- **Risk**: The full suite can find a failure that the changed-file tests miss. CI reports it.
- **Human decision**: No.

### D-14. Compose-gated test

- **Decision**: Repair the compose test (task T015) only after a run with `COMPOSE_TEST=1` and running services. A skipped run does not count as a pass.
- **Alternatives**: Repair the test by static review. Accept the finding.
- **Rationale**: `tests/integration/test_compose_deploy.py` line 16 reads `COMPOSE_TEST`. Line 23 skips the class without it. Local view of the same blob shows line 36 as the weak guard, and the remote check matches that line (row 81). Test containers must follow the compose naming policy in `.github/copilot-instructions.md`.
- **Risk**: The task may wait for a compose run.
- **Human decision**: No.

### D-15. Guard and document files stay unchanged

- **Decision**: Do not edit `.github/copilot-instructions.md`, `documentation/quality-gates.md`, `AGENTS.md`, or the constitution in this campaign.
- **Alternatives**: Update the documents to the new counts.
- **Rationale**: `tests/guardrails/local_test_quality_loop/test_guidance.py` line 18 reads the copilot instructions. A document edit can break that guard. The counts belong in the baseline.
- **Risk**: The documents describe the older count until a later change updates them.
- **Human decision**: No.

### D-16. Credential session hold

- **Decision**: HUMAN-DECISION-REQUIRED. Do not repair `tests/contract/upgrade_portal/test_no_credential_leak.py` lines 633 and 657 until a human decides the session credential design in issue #3714. The decision belongs to credential policy.
- **Alternatives**: Repair the lines now. Remove the file from the campaign.
- **Rationale**: Issue #3714 is open. A comment dated 2026-11-10T04:53:27Z says the security design remains blocked on human review. The same test file appears in that design. A repair now could fit a test to a design that changes.
- **Risk**: Two baseline entries stay open for longer.
- **Human decision**: Yes. Credential policy.

## Remote verification table

Rows 1 to 34 hold document, configuration, and local package checks. Rows 35 to 51 hold commit, branch, and blob checks. Rows 52 to 135 hold the 84 baseline entries. Rows 136 to 139 hold four constitution checks. The `Ref` column names the GitHub ref. The value `local-venv` marks a local installed file.

| # | Claim | Path | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | AGENTS: PR body closes the issue | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| 2 | AGENTS: check open PRs for file overlap | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 244 |
| 3 | AGENTS: declare the file set before an edit | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 246 |
| 4 | AGENTS: no push to another agent branch | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 254 |
| 5 | AGENTS: a test must be able to fail | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 136 |
| 6 | AGENTS: specification for three or more files | AGENTS.md | main | 44a9affb5bd6f774973a845d27343e4e528b6ad | present | 348 |
| 7 | Copilot instructions: test quality ratchet section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| 8 | Copilot instructions: baseline must not hide a finding | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 150 |
| 9 | Copilot instructions: a user-visible change adds a fragment | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| 10 | Copilot instructions: container build trigger row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| 11 | Copilot instructions: serial validation and merge queues | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 483 |
| 12 | Constitution: Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 13 | Constitution: managed specs roots | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| 14 | Constitution: Principle IV deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| 15 | Constitution: Principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| 16 | Constitution: Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| 17 | Constitution: one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 18 | Quality gates: write-baseline keeps current findings only | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 36 |
| 19 | Quality gates: do not add the roots option | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 41 |
| 20 | Changelog README: no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 21 | Analyzer config: rule key weak_assert_not_none | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 21 |
| 22 | Baseline: first weak_is_not_none entry | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 10 |
| 23 | CI: MYPY_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 24 | CI: VULTURE_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 25 | CI: test quality gate command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| 26 | CI: ops platform correctness selector | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1272 |
| 27 | Container build: path filter excludes tests | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| 28 | Analyzer pin in requirements-dev | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| 29 | Spec route width of eight digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 30 | Test guidance guard reads copilot instructions | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 18 |
| 31 | Installed analyzer rule weak_is_not_none | .venv/Lib/site-packages/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py | local-venv | not applicable (local file) | present | 310 |
| 32 | Installed analyzer config key list | .venv/Lib/site-packages/misthelper_devtools/test_quality_analyzer/config.py | local-venv | not applicable (local file) | present | 31 |
| 33 | Installed analyzer baseline identity | .venv/Lib/site-packages/misthelper_devtools/test_quality_analyzer/baseline.py | local-venv | not applicable (local file) | present | 48 |
| 34 | Installed mistapi version 0.64.1 | .venv/Lib/site-packages/mistapi-0.64.1.dist-info | local-venv | not applicable (local folder) | present | 0 |
| 35 | Commit fd7896f: local test_api_result repair, on GitHub, not on main | (commit object) | main | fd7896f326ecd25d673fa919330afde008e1803d | partial | 0 |
| 36 | Commit cbf9c52: local device utility repair | (commit object) | main | cbf9c5241b9e69368622b266e01e883ed055db5d | absent | 0 |
| 37 | Commit 8e67300: local API contract repair, on GitHub, not on main | (commit object) | main | 8e67300160731232298e307d29531bf3e0c4e28f | partial | 0 |
| 38 | Commit de809907: head of archive branch jmorrison-juniper-api-contract-test-repair | (commit object) | archive/laptop-20261121/jmorrison-juniper-api-contract-test-repair | de809907ca89e576ff11fa3fb7d123cc6b7e8ecc | partial | 0 |
| 39 | Commit 2238c75: local E2 repair, on GitHub, not on main | (commit object) | main | 2238c75f9c1a84ce67c9190ba180a12c724190d8 | partial | 0 |
| 40 | Commit d3a1483: head of archive branch jmorrison-juniper-weak-assertion-follow-up | (commit object) | archive/laptop-20261121/jmorrison-juniper-weak-assertion-follow-up | d3a1483d7a9d966c8d5b476682fdf14765d4b88d | partial | 0 |
| 41 | Commit b750783: PR #4396 merge, ancestor of main | (commit object) | main | b750783c361724a378e160236af94b3659bd345a | present | 0 |
| 42 | Branch recovery/2708-handoff-20261004: one commit, one file, api_result only | refs/heads/recovery/2708-handoff-20261004 | main | f195788a090d6ace8f2f320dc1f96a413876e2c4 | partial | 0 |
| 43 | Candidate blob: sentinel repair (absent on GitHub) | tests/unit/websocket/polling/test_message_router.py | main (object) | d92499a42ba5c9b2ec940156957601e732052043 | absent | 0 |
| 44 | Candidate blob: smoke repair (absent on GitHub) | mist-ops-platform/tests/integration/test_e2e_smoke.py | main (object) | d19f2684e3e6171d846dd5bc4649e665e02f9538 | absent | 0 |
| 45 | Candidate blob: retry-run repair (absent on GitHub) | tests/integration/upgrade_portal/run_controls/test_actions.py | main (object) | e165e68bf0e099eac9a4cb5446f059af5d3efba1 | absent | 0 |
| 46 | Candidate blob: profile repair (absent on GitHub) | tests/unit/site/address_audit/test_ui_geocoder_profile_cleanup.py | main (object) | 06755cf64eef0f5a85aa5d245f2fe942092b2088 | absent | 0 |
| 47 | Candidate blob: credential repair (absent on GitHub) | tests/contract/upgrade_portal/test_no_credential_leak.py | main (object) | 9ffad21cf6b9a1ecf27e2cf43b62dcb2b97358b1 | absent | 0 |
| 48 | Candidate blob: comparator repair (absent on GitHub) | tests/unit/test_csv_comparator.py | main (object) | 5cddd34e58a73e20f062ab3a98900a9f21bde39e | absent | 0 |
| 49 | Candidate blob: inventory repair (absent on GitHub) | tests/unit/inventory/test_org_device_inventory_msp.py | main (object) | 841d9397b48a13138dea65278a6f76ced8e904d1 | absent | 0 |
| 50 | Candidate blob: E2 repair (on GitHub, not on main) | tests/maps/test_viewer_callbacks_wave_e2.py | main (object) | 8385ed828332c7338271d35bf10573eae720785b | partial | 0 |
| 51 | Candidate blob: device test repair (on GitHub, not on main) | tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py | main (object) | cd471d933954032388114597a68861e7441350e2 | partial | 0 |
| 52 | F-01 weak guard, category RC | mist-ops-platform/tests/contract/test_api_contracts.py | main | a19de742436d648ac71a35db900acf1b47f5bdaf | present | 66 |
| 53 | F-02 weak guard, category RC | mist-ops-platform/tests/contract/test_api_contracts.py | main | a19de742436d648ac71a35db900acf1b47f5bdaf | present | 151 |
| 54 | F-03 weak guard, category RC | mist-ops-platform/tests/integration/test_e2e_smoke.py | main | c6b3946b56eb16667ad836710d60c623ec847080 | present | 26 |
| 55 | F-04 weak guard, category RC | mist-ops-platform/tests/integration/test_e2e_smoke.py | main | c6b3946b56eb16667ad836710d60c623ec847080 | present | 27 |
| 56 | F-05 weak guard, category RC | mist-ops-platform/tests/integration/test_e2e_smoke.py | main | c6b3946b56eb16667ad836710d60c623ec847080 | present | 32 |
| 57 | F-06 weak guard, category RC | mist-ops-platform/tests/integration/test_e2e_smoke.py | main | c6b3946b56eb16667ad836710d60c623ec847080 | present | 55 |
| 58 | F-07 stale entry, category X | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | stale | 155 |
| 59 | F-08 stale entry, category X | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | stale | 366 |
| 60 | F-09 weak guard, category S | mist-ops-platform/tests/unit/api/test_token_refresh_route.py | main | 2392ec703f317aca30b5e92a163456ee0fd6f70e | present | 64 |
| 61 | F-10 stale entry, category X (PR #3783) | mist-ops-platform/tests/unit/mist/test_api_result.py | main | 330fa9e3c13c32e7ed9685a489d0c5bace1f006d | stale | 59 |
| 62 | F-11 weak guard, category S | mist-ops-platform/tests/unit/mist/test_deploy_calls.py | main | 960fc86551d594bddbd3b494101d29e685e06741 | present | 90 |
| 63 | F-12 weak guard, category S | mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py | main | 861cf202545ad90217196966d63446ca6578de64 | present | 39 |
| 64 | F-13 weak guard, category S | mist-ops-platform/tests/unit/mist/test_firmware.py | main | 107932a8748dc6555c3974fcd5ec736b68856db6 | present | 123 |
| 65 | F-14 weak guard, category H | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 36 |
| 66 | F-15 weak guard, category H | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 49 |
| 67 | F-16 weak guard, category H | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 59 |
| 68 | F-17 weak guard, category H | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 69 |
| 69 | F-18 weak guard, category S | mist-ops-platform/tests/unit/mist/test_response_consumers.py | main | d2005bf863db60bddb7ffc878f8482648460f3de | present | 82 |
| 70 | F-19 weak guard, category S | mist-ops-platform/tests/unit/shared/test_session_store.py | main | 59e39d0ca5d9667375b39ffa066ff116c03e2c00 | present | 64 |
| 71 | F-20 weak guard, category S | mist-ops-platform/tests/unit/worker/checks/test_post_checks.py | main | 01afc8eda60c10a1458980b585fd050d4322e986 | present | 155 |
| 72 | F-21 weak guard, category S | tests/contract/test_mib_matches_catalog.py | main | 626f8103c7cf1f6f906ec9cf31822330e6da6335 | present | 122 |
| 73 | F-22 weak guard, category S | tests/contract/upgrade_portal/test_capture_start_returns_lock_grant.py | main | 8f8fc66246860cefc11c7c0a2ffac0a3bbbe3323 | present | 463 |
| 74 | F-23 weak guard, category S | tests/contract/upgrade_portal/test_capture_start.py | main | 1f20d03529ea9bd7bbcf9030edc3f8f3b14e46bb | present | 762 |
| 75 | F-24 weak guard, category H | tests/contract/upgrade_portal/test_no_credential_leak.py | main | ac90c47c89d7e0114bfb8d74817c914cbc7e3432 | present | 633 |
| 76 | F-25 weak guard, category H | tests/contract/upgrade_portal/test_no_credential_leak.py | main | ac90c47c89d7e0114bfb8d74817c914cbc7e3432 | present | 657 |
| 77 | F-26 weak guard, category S | tests/contract/upgrade_portal/test_org_scope.py | main | 0799dfcd3f260d5322173d66e5e38d9d568679f1 | present | 691 |
| 78 | F-27 weak guard, category S | tests/contract/upgrade_portal/test_org_scope.py | main | 0799dfcd3f260d5322173d66e5e38d9d568679f1 | present | 708 |
| 79 | F-28 stale entry, category X | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | stale | 120 |
| 80 | F-29 weak guard, category S | tests/integration/test_aggregate_upgrade_flow.py | main | fd3968a5465fcb67b748bad3a59e1aa75335440f | present | 124 |
| 81 | F-30 weak guard, category U | tests/integration/test_compose_deploy.py | main | 2e62d01038114b938544af3342c0354958931d8b | present | 36 |
| 82 | F-31 weak guard, category S | tests/integration/upgrade_portal/run_controls/test_actions.py | main | b134d25762bc426765473424742a9c069c403cf4 | present | 106 |
| 83 | F-32 weak guard, category S | tests/integration/upgrade_portal/run_controls/test_actions.py | main | b134d25762bc426765473424742a9c069c403cf4 | present | 192 |
| 84 | F-33 weak guard, category RC | tests/integration/upgrade_portal/run_controls/test_actions.py | main | b134d25762bc426765473424742a9c069c403cf4 | present | 210 |
| 85 | F-34 weak guard, category S | tests/maps/test_browser_opener.py | main | b31003a60c110b3afd4912453f73ac527542e49b | present | 202 |
| 86 | F-35 weak guard, category S | tests/maps/test_plotly_heatmap_renderer.py | main | 38f2d8e69ef16207330dc42feb6470076a280ad3 | present | 42 |
| 87 | F-36 weak guard, category S | tests/maps/test_plotly_heatmap_renderer.py | main | 38f2d8e69ef16207330dc42feb6470076a280ad3 | present | 53 |
| 88 | F-37 stale entry, category X | tests/maps/test_plotly_heatmap_renderer.py | main | 38f2d8e69ef16207330dc42feb6470076a280ad3 | stale | 68 |
| 89 | F-38 stale entry, category X (PR #4393) | tests/maps/test_plotly_map_figure_builder.py | main | a3678a0d84d85a9635920fe8967ecd6f7f247381 | stale | 70 |
| 90 | F-39 weak guard, category H | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 134 |
| 91 | F-40 weak guard, category H | tests/maps/test_viewer_callbacks_wave_a.py | main | 2f1d3052d95b10edebc6113f9c7e9b49a306a2ab | present | 181 |
| 92 | F-41 weak guard, category H | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 174 |
| 93 | F-42 weak guard, category H | tests/maps/test_viewer_callbacks_wave_e2.py | main | 7f666fae76e434af46570c962c04187f10b3b610 | present | 178 |
| 94 | F-43 weak guard, category S | tests/test_audit_analyzer.py | main | 2d2a0799cd3bd04008270c1b4131fe442516d1b8 | present | 98 |
| 95 | F-44 stale entry, category X (PR #4396) | tests/unit/config/foundation/support/refactors/network/clients/test_service_ping_launcher.py | main | d1e9b243feba2e9cc74d3fb5efdc34aa25ba2612 | stale | 84 |
| 96 | F-45 weak guard, category S | tests/unit/config/foundation/support/refactors/network/launchers/test_maps_manager_launcher.py | main | 2998488ea0979b62203e3fb37de18832920773a2 | present | 76 |
| 97 | F-46 weak guard, category U | tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py | main | 59b34859534a48cd85f9f119bf8fb958b66a55ef | present | 96 |
| 98 | F-47 weak guard, category S | tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py | main | 79cafab3dabcbbada53b5e9486aa8cfae76edee9 | present | 113 |
| 99 | F-48 weak guard, category R | tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py | main | 79cafab3dabcbbada53b5e9486aa8cfae76edee9 | present | 125 |
| 100 | F-49 stale entry, category X | tests/unit/config/standalone/foundation/persistence/database/test_retention.py | main | 70cbdb571a07fea004d39eef951ff3146c4f3568 | stale | 184 |
| 101 | F-50 stale entry, category X (PR #4344) | tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py | main | 9ac5ebcb426fe672f4a70a53f7be3a3e49db408e | stale | 51 |
| 102 | F-51 weak guard, category R | tests/unit/config/standalone/foundation/persistence/redis/test_redis_writer.py | main | 5c6326e3cea9c7f6925513859d01ce87e08b9653 | present | 55 |
| 103 | F-52 stale entry, category X | tests/unit/config/standalone/foundation/support/quality/imports/test_no_mistapi_stub_leak.py | main | 96b2c082798b59b50bd02e05c3f6082a2e633bca | stale | 26 |
| 104 | F-53 weak guard, category S | tests/unit/device/test_ap_profile_migration_manager.py | main | f31646171a466941e68b9b6b93b8c25bd44a3005 | present | 245 |
| 105 | F-54 weak guard, category H | tests/unit/inventory/test_org_device_inventory_msp.py | main | 44475247c7b7182468ecad7cc69ab2fdd611a677 | present | 342 |
| 106 | F-55 weak guard, category S | tests/unit/marvis/mist/resources/site/test_site_config_manager.py | main | 87a5f7424d3cf9079bb5b365c0c1e1dadac91659 | present | 63 |
| 107 | F-56 weak guard, category S | tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py | main | 24e3bf5bcef4d511588150c0bf1ee0f468e70aa4 | present | 493 |
| 108 | F-57 weak guard, category R | tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py | main | 24e3bf5bcef4d511588150c0bf1ee0f468e70aa4 | present | 546 |
| 109 | F-58 weak guard, category RC | tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py | main | 49e163216abf3b99c6514d12d2cc04c7ff69d7c5 | present | 231 |
| 110 | F-59 weak guard, category R | tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py | main | 18eeaa25b5817699088e2c53b52f58c807d55ec5 | present | 1389 |
| 111 | F-60 weak guard, category R | tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py | main | 18eeaa25b5817699088e2c53b52f58c807d55ec5 | present | 1398 |
| 112 | F-61 stale entry, category X | tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py | main | c2581f5e6fa0346386885ea7423f74a254a23d55 | stale | 373 |
| 113 | F-62 stale entry, category X | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | stale | 373 |
| 114 | F-63 stale entry, category X | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | stale | 387 |
| 115 | F-64 stale entry, category X (PR #4400) | tests/unit/refactors/test_tui_launcher.py | main | 270a3763c08dd737c9430b83f3abef68e28228c0 | stale | 31 |
| 116 | F-65 stale entry, category X | tests/unit/site/address_audit/test_audit_engine.py | main | 56631ee995808bf4665cb3b0793361c7f9f753d9 | stale | 353 |
| 117 | F-66 weak guard, category RC | tests/unit/site/address_audit/test_ui_geocoder_profile_cleanup.py | main | 371f52327a24221f7b3fce375b8a7f19361dc37b | present | 64 |
| 118 | F-67 weak guard, category S | tests/unit/ssh/config/test_env_loader_wave9.py | main | 9c19bd2c8b52e772497c83531bb73aa7f602d9f1 | present | 340 |
| 119 | F-68 weak guard, category S | tests/unit/ssh/test_ssh_runner_manager_extended.py | main | 9e981be65315b57cc6959ce8d15802734c971232 | present | 215 |
| 120 | F-69 weak guard, category RC | tests/unit/test_csv_comparator.py | main | 2875ac538c3927609662e2a24aa718b4cf34ba9b | present | 145 |
| 121 | F-70 weak guard, category RC | tests/unit/test_csv_comparator.py | main | 2875ac538c3927609662e2a24aa718b4cf34ba9b | present | 147 |
| 122 | F-71 stale entry, category X | tests/unit/ui/test_function_executor.py | main | 65ae106ce107f43cc49545d5d12a0730a476f4ec | stale | 65 |
| 123 | F-72 weak guard, category S | tests/unit/ui/test_results_grid_builder.py | main | fabb7f8bb7a4e1b8f5711ba423e00e492f04a672 | present | 131 |
| 124 | F-73 weak guard, category S | tests/unit/upgrade_portal/test_confirm_warning.py | main | b07230b5cd5de3f814593ad6495724e41c13d787 | present | 241 |
| 125 | F-74 weak guard, category S | tests/unit/upgrade_portal/test_inventory_address.py | main | 5b529a439b6c48c62de2ce52cd6ec89bbff9ece9 | present | 196 |
| 126 | F-75 weak guard, category S | tests/unit/upgrade_portal/test_lock_record_empty_run.py | main | e420c39c82d687a8f0ae2fa7d95b984e5d6c3ac8 | present | 179 |
| 127 | F-76 weak guard, category S | tests/unit/upgrade_portal/test_run_adopts_precheck.py | main | b39194daefaa1b4729c92bdc8a2a3588c82673ac | present | 145 |
| 128 | F-77 weak guard, category S | tests/unit/upgrade_portal/test_runs/test_actions.py | main | b51eda4281979ff7465e43bce6e14c567f1f64d1 | present | 395 |
| 129 | F-78 stale entry, category X | tests/unit/upgrade_portal/test_signals.py | main | 5ad385292b701c4c17e066d5bbb4adb1cbc2a10f | stale | 431 |
| 130 | F-79 weak guard, category S | tests/unit/upgrade_portal/test_stale_statistics.py | main | 81052bad65ed6c4fdeb75e7aa5caf6dbee47d1fe | present | 241 |
| 131 | F-80 weak guard, category S | tests/unit/upgrade_portal/test_stale_statistics.py | main | 81052bad65ed6c4fdeb75e7aa5caf6dbee47d1fe | present | 253 |
| 132 | F-81 stale entry, category X | tests/unit/websocket/polling/test_completion_detector.py | main | 0495d79a3e315c02f9a98f4b0f426bf548ba85ae | stale | 606 |
| 133 | F-82 weak guard, category RC | tests/unit/websocket/polling/test_message_router.py | main | 321245e5be30155e8e4fb920041dd60787c67678 | present | 480 |
| 134 | F-83 stale entry, category X (PR #4373) | tests/unit/websocket/polling/test_result_combiner.py | main | e552e9cbfec19b3dc70f37c135eb79eaf4df1c91 | stale | 114 |
| 135 | F-84 weak guard, category S | tests/unit/websocket/test_manager_thread_join.py | main | 20b029de5e5b568f22731e2a309f3b74331ef6ad | present | 90 |
| 136 | Constitution: PR checklist requires a closing reference | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 519 |
| 137 | Constitution: Principles VI and VII are review gates | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 553 |
| 138 | Constitution: claim the issue with in-progress before a branch | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 500 |
| 139 | Constitution: required type, scope, and status labels | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 487 |

Category key: S is a redundant guard. RC is a guard with a candidate. R is a confirmed gap with no candidate. H is a held guard. U is an unclassified guard. X is a stale entry.

## Sources

- Issue #2708 body and 64 comments. Read with `gh issue view 2708 -R jmorrison-juniper/MistHelper`. Comment indexes 0 to 63. Dates are UTC.
- Pull request and issue states with `gh pr list`, `gh pr view`, and `gh issue view`. Open pull request files with `gh api repos/jmorrison-juniper/MistHelper/pulls/<number>/files`.
- Remote tree with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree holds 11,404 entries. The flag `truncated` is false.
- Remote file bodies with `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`. Each body is decoded from base64.
- Local read-only copy of the repository. Path `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`. Its `HEAD` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Five sampled blobs match the remote blobs.
- Installed analyzer. Path `.venv\Lib\site-packages\misthelper_devtools` (version 0.6.4).
- Untracked local analyzer output. Path `test_quality_analyzer_output\report.json` (generated 2026-11-10). The remote tree has no such path.
- No URL was fetched. The `web_fetch` tool was not used.
- Skills: none loaded. No listed skill covers test-quality triage. Podman and Juniper device skills do not apply.
- Required reading read in full: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates.
- Read in full or in part: `documentation/quality-gates.md`, `changelog.d/README.md`, and `.specify/scripts/powershell/spec-route.ps1`. The reference record was read by heading and by its first 40 lines of `design/research.md`.
- Keyword search only: `documentation/development-setup.md` (lines 40, 268 to 317, and 370), `documentation/container-deployment.md` (lines 141 and 155), and `documentation/architecture.md`. The search found no test-layout rule in `architecture.md`.
- Not read: `documentation/operator-guide.md` (no operator-visible change), and the Mist API OpenAPI file and endpoint documents (no endpoint behavior is in scope).

## Unverified

1. The analyzer count on main. The analyzer did not run, because rule 2 forbids repository scripts. Task T001 decides it.
2. The cause of 11 stale entries that no merged pull request explains. These are F-07, F-08, F-28, F-37, F-49, F-52, F-61, F-62, F-63, F-65, and F-78.
3. The installed analyzer commit. The folder `misthelper_devtools_0.6.4.dist-info` has no `direct_url.json`. The pin is `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
4. The effect of the config key `weak_assert_not_none` on the emitted ID `weak_is_not_none`. The analyzer did not run.
5. The archive branch that holds commits `fd7896f`, `8e67300`, and `2238c75`. The commit objects exist. The containing branch was not found.
6. The branch that holds `registry_validation.py` in the preserved #2746 work. The claim comes from a comment dated 2026-11-10T16:46:44Z.
7. The compose test. It runs only with `COMPOSE_TEST=1` and running services. No run happened.
8. The redundancy claims in the comments. The controls were not run again in this session.
9. Weak guards outside the baseline. No full-tree scan ran. The `ci.yml` run on main succeeded, which suggests the baseline matches main.
10. Multi-line assert forms. The per-line check reads a single line only.
