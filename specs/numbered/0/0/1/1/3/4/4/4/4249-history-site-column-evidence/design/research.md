# Research: History Site Column Failure Evidence

Each decision names the alternatives, the chosen option, the reason, and the risk. Each code claim cites a path and a line. Each remote claim cites the `main` blob or commit that the remote check read on 2026-11-26. Each local file matched its remote blob byte for byte, so local line numbers equal remote line numbers.

## Issue Facts

- **Title**: `Test failure: test_the_history_of_one_site_shows_no_site_column`. State OPEN. Created 2026-10-16 08:49:33 UTC. Updated 2026-11-08 20:43:33 UTC. Author `jmorrison-juniper`.
- **Labels**: `bug`, `needs-investigation`, `tests`.
- **Reproduction steps in the issue**: Read run 38860502112, job 116842182317, commit `351871c4345405cdd035b043b046f046f192ddc1` (the merge of #4242), and log line 1252.
- **Error text in the issue**: `tests/e2e/upgrade_portal/test_history_site_column_journey.py::test_the_history_of_one_site_shows_no_site_column[chromium] FAILED [  6%]`.
- **Data the issue reports as absent**: No traceback, no assertion message, no E2E artifact, no screenshot, and no trace. The issue states that the job limit canceled the job at 59 percent with 530 outcomes. Each claim is checked in R1.
- **Contrary evidence in the issue**: The same test passed in run 38870153718 (PR #4248). It passed in the E2E run of PR #4242 before its merge (U-1). It passed in an isolated container run at `e4487cd` (U-2).
- **Owner comment of 2026-10-25**: The exact Chromium selector passed on `main` at `9991d30a187e5d215462eefac60a09a57e5f99e5` with `1 passed in 4.00s` (U-4). The artifact endpoint returned HTTP 404 (U-3). The current route, model, and template omit the Site column when a site ID exists (RC-09 to RC-12). No safe repair was established, so no code changed. The issue stays open.
- **Legacy record search**: A read-only search of `specs/` found no folder whose name starts with `4249-`. The route folder `specs/numbered/0/0/1/1/3/4/4/4` did not exist. No legacy record exists, so the reuse check does not apply.
- **Owner comment of 2026-11-08**: No new failure evidence exists. The root cause stays unverified.

## Linked Pull Requests

Read with `gh pr list` and `gh pr view` on 2026-11-26. No branch was checked out.

| Number | Title | State | Merged | Head branch | Link basis | Result |
|---|---|---|---|---|---|---|
| #4251 | fix(ci): run the E2E suite in parallel shards | MERGED | 2026-10-16 09:19:14 UTC | fix/4250-shard-e2e | Search hit for the issue number | Its merge commit is on `main` (RC-61). It holds the shard layout (RC-19, RC-20). |
| #650 | refactor: _maps_wizard compliance D/64.0 -> A+/100.0 | MERGED | 2026-07-04 08:21:21 UTC | refactor/compliance-009-_maps_wizard | Search hit only. Its body contains the text "4249 tests". | Not linked. No relation to this issue. |
| #4248 | fix(tests): let the context owner close upgrade portal pages | MERGED | 2026-10-16 09:44:32 UTC | fix/4247-page-fixture-close | Named by the issue as the PR of run 38870153718 | Its merge commit is on `main` (RC-62). The run ran `e4487cd`. The PR head now reads `07edd50`. |
| #4242 | fix(export): complete SDK count catalog | MERGED | 2026-10-16 06:18:50 UTC | Not read | Named by the issue as the merge of the failing run | The failing run head `351871c` is on `main` (RC-58). |

## R1. Reproduce the failure from the CI logs

- **Decision**: Read the job log of job 116842182317 in run 38860502112 with `gh run view 38860502112 --job 116842182317 --log`. Filter the output for the test name and the outcome words.
- **Rationale**: The test step ended as `cancelled`, not as `failure`. The `--log-failed` view therefore printed zero lines. The job log holds the full output of the job.
- **Alternatives considered**:
  - `gh run view --log-failed`: rejected. It printed no line for this run.
  - Download the run artifacts: rejected. The run uploaded no E2E artifact. It uploaded five coverage and exclusion artifacts.
  - Rerun the job: rejected. A rerun is a write action, and the brief allows GitHub reads only.
- **Risk**: A GitHub log can expire. A later read can differ from this read (U-8).

Evidence, read on 2026-11-26:

| Fact | Value |
|---|---|
| Run conclusion | `cancelled`. Event `push`. Branch `main`. Head `351871c4345405cdd035b043b046f046f192ddc1`. Created 2026-10-16 06:18:53 UTC. |
| E2E job conclusion | `cancelled`, job 116842182317 |
| Step `Run E2E smoke tests` | `cancelled` |
| Job log size | 1910 lines |
| FAILED outcome lines | 1. Log line 1252, time 06:25:04.0868835. |
| Neighboring PASSED lines | Line 1251 at 06:25:03.2861665. Line 1253 at 06:25:04.7789567. |
| Lines with `AssertionError`, `Traceback`, or `short test summary` | 0 for each text |
| Last PASSED line | Line 1770, time 06:41:23.6326204, progress 59 percent |
| Cancel line | Line 1771, time 06:43:07.7560595 |
| Silence before the cancel | 104.12 seconds. The issue states 107 seconds. |
| Gap from line 1251 to line 1252 | 0.80 seconds |
| Outcome lines | 530 with the loose pattern. 527 with the node-id pattern. The issue states 530. |
| Run artifacts | Five: `coverage-root-units`, `coverage-upgrade-contracts`, `coverage-upgrade-units`, `coverage-root-and-contracts`, and `quality-exclusion-drift`. None is an E2E artifact. |
| Later run 38870153718 (branch `fix/4247-page-fixture-close`, head `e4487cd7cb1661666e7c7f815d50655c05d7fb95`) | Job 116873064875 passed the same test at log line 1264 (`[  6%]`) before the job was canceled. |

## R2. Timing excludes most candidate statements

- **Decision**: Do not name one failing statement. Record two candidate statements and the check that decides between them.
- **Rationale**:
  1. The failed line follows the previous PASSED line by 0.80 seconds (R1).
  2. Playwright assertions retry until their timeout. The default timeout is 5 seconds (RC-70). A failing wait therefore lasts at least 5 seconds.
  3. After the page opens, two statements in the test have no wait. They are line 283, `assert save_screenshot(page, "history-one-site.png").exists()`, and line 284, `assert header_names(page) == ONE_SITE_HEADERS` (RC-03, RC-04).
  4. Lines 285 and 286 wait for their conditions (RC-05, RC-06). A failure there takes at least 5 seconds.
  5. The `open_history` helper waits for the table at line 121 (RC-08). A failure there also takes at least 5 seconds.
  6. A quick navigation error could also fail the test. The adjacent tests passed on the same server in the same job. That result points away from a server fault.
- **Alternatives considered**: Blame the page-close hang of issue #4247. Rejected for this failure, because the silence starts 16 minutes after the failed line (R3).
- **Risk**: The argument assumes that the log time marks the end of the call phase of each test (U-10).

## R3. Candidate causes and the check that decides each

| ID | Candidate | Fits the timing | Contradicting evidence | Check that decides it |
|---|---|---|---|---|
| CS-1 | Screenshot protocol failure at line 283 | Yes. A failed screenshot raises at once. | None found. The repository names this flake in its helper and its unit test (RC-17, RC-18). | A retained trace shows a failed screenshot action. Or a traceback names line 283 with a Playwright error. |
| CS-2 | Header list mismatch at line 284 | Yes. The check runs without a wait. | The route turns the Site column off for any non-empty `site_id` (RC-09, RC-10, RC-11). | A failure screenshot shows a Site header. Or the traceback prints the header list. |
| H-3 | Page-close hang of issue #4247 | No, for this line. The silence starts 16 minutes after the failed line. | The silence follows the last PASSED line at 06:41:23, not the failed line at 06:25:04. | Not needed for this line. It can explain a cancel. |
| H-4 | Missing seed row for the one-site page | No. A missing row waits at line 286, after line 284. | The seed comment says no other journey reads the site (RC-16). | Not needed for this line. |

## R4. Keep the evidence path (decision D-2)

- **Decision**: Guard the existing diagnostics upload with a guard test. Do not add a traceback hook.
- **Rationale**: The workflow already keeps the shard log, the phase trail, and the browser output folder after a failed or canceled shard (RC-21 to RC-26). Pytest-playwright keeps a failure screenshot and a trace for each failed test (RC-66, RC-67). No test detects a removal of these rules (RC-34). The guard fills that gap.
- **Gap that remains**: Pytest prints failure details in its terminal summary (RC-68). A canceled run therefore has no traceback text in its shard log. The trace and the failure screenshot remain.
- **Alternatives considered**:
  - No change: rejected. A removal of the upload would pass every check.
  - Guard the upload step: chosen. It covers FR-001 to FR-004 with one class and two test functions.
  - Add a hook that prints each failure when it occurs: deferred. The hook needs shared code in `tests/e2e/upgrade_portal/conftest.py`, a large shared file (RC-15). It could also need a new plugin module, which breaks the five-item rule in its folder. The retained evidence already covers CS-1 and CS-2.
  - Pass `--instafail` to pytest: rejected. The pinned pytest in `.venv` has no such option (RC-69).
  - Upload `test-artifacts/upgrade-portal-journeys/`: rejected. That folder holds the journey screenshots of every test. The failure screenshot already covers this test.
  - Retry the test, or raise its timeout: rejected. A retry hides a recurring fault from the run result. A timeout change does not address a failure that took 0.8 seconds.
- **Risk**: A canceled run keeps no traceback text. FR-007 and the gate page state the limit. The follow-up issue can add a hook if the limit blocks a diagnosis.

## R5. Place the guard in the existing file (decision D-3)

- **Decision**: Add class `EvidenceUploadAudit` and two test functions to `tests/guardrails/test_e2e_shard_partition.py`.
- **Rationale**: `tests/guardrails` holds 79 direct entries on `main` (RC-36). The five-item rule forbids a new direct child in a noncompliant folder (RC-47). `ShardPartitionAudit` holds six methods (RC-35). A new method would add to a class that is already over the limit.
- **Alternatives considered**:
  - A new file in `tests/guardrails`: rejected. It breaks the five-item rule.
  - A method on `ShardPartitionAudit`: rejected. It adds to a noncompliant class.
  - A new test folder: rejected. It adds a child to `tests/`.
- **Risk**: The module already holds more top-level names than the limit. The change adds three names. The plan records the debt (`plan.md`, Complexity Tracking).

## R6. Document the diagnostics artifact in the gate page (decision D-4)

- **Decision**: Name the artifact in the `playwright` row of `documentation/quality-gates.md` (line 68, RC-38). Add one paragraph after the warning at line 86.
- **Rationale**: The gate page defines the browser gate. It already warns that the browser gate can report a false pass (RC-39).
- **Alternatives considered**: Add the text to `documentation/development-setup.md`, which gives the local run command (RC-40). Rejected as the primary location, because the gate page defines the gate. A pointer from the setup page is optional and out of scope.
- **Other documents read**:
  - `documentation/container-deployment.md` defines the test container policy (RC-41). This feature starts no container, so no change applies.
  - `documentation/architecture.md` places the upgrade capture portal on port 8056 (RC-42). This feature changes no portal behavior, so no change applies.
  - `documentation/operator-guide.md` describes no history Site column. A search found no match. No change applies.

## R7. The closing keyword and the follow-up issue (decision D-5)

- **Decision**: Keep `Closes #4249` in the commit body and the pull request body, as the brief requires. Before the merge, open a follow-up issue for the root cause. Label it `bug`, `needs-investigation`, and `tests`.
- **Rationale**: The brief requires the closing keyword. The owner comments keep the issue open until the root cause or a retained failure is available (`spec.md`, Clarifications). The follow-up issue keeps the root cause tracked after the merge closes #4249.
- **Alternatives considered**:
  - `Refs #4249` in the body: rejected. The brief names the required body text.
  - No follow-up issue: rejected. The root cause would lose its tracking item.
- **Risk**: The merge closes an issue that the owner wanted open. Tasks T-FOLLOW and T-MERGE mitigate the risk. The orchestrator authorizes the merge after the follow-up issue exists.

## R8. The changelog fragment (decision D-6)

- **Decision**: Add `changelog.d/issue-4249-history-site-column-evidence.md`.
- **Rationale**: The constitution requires one unique fragment for each change (RC-50). The changelog README exempts internal-only changes (RC-44). The constitution governs when two documents conflict (RC-51). The file name follows the README rule for an issue without a pull request (RC-43) and the guard patterns (RC-45, RC-46).
- **Alternatives considered**: No fragment, as the README exemption allows. Rejected, because the constitution governs.
- **Risk**: A reader can treat the fragment as a user-facing change. The bullet names the change as internal, under the `Changed` type.

## R9. Product code and test logic (decision D-1)

- **Decision**: Change no product code, no test assertion, no timeout, and no retry.
- **Rationale**: At the request URL, the route and the template match the test. The route turns the Site column off for a non-empty `site_id` (RC-09 to RC-12). No root cause is verified. A change without a verified cause can hide the fault. The workflow already keeps the evidence (R4).
- **Alternatives considered**:
  - Change the screenshot to `full_page=False`: rejected. It alters the evidence, and the cause is unknown.
  - Add a longer wait: rejected. The failure took 0.8 seconds.
  - Remove the screenshot call: rejected. The call is part of the evidence.
- **Risk**: The flaky failure can recur until its cause is known. R4 and R7 mitigate the risk.

## R10. Gate applicability

- **Applies**: The compile, lint, format, and pytest commands for the guard file. Also `bandit`, `symbol-diff`, the test-quality ratchet, and the STE gate. The citation check is the `citation_lint` row of `documentation/quality-gates.md`.
- **Not applicable**: mypy (RC-29), radon (RC-30), vulture, pydocstyle, and interrogate (RC-31). Coverage, the menu reference, the ops portal, and the ops platform have no related change.

## R11. Reference shape

The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` gave the layout, the heading depth, and the decision format. Only its headings were read. No content was copied.

## Remote Verification

The remote checks read the `main` tree, the contents API, the commit compare API, and the pull request API on 2026-11-26. The root tree of `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. It holds 11404 entries and is not truncated. Each third-party file was read locally with read-only views. Each row below has the same order as the `remote_checks` array in `4249-STATUS.json`.

| ID | Claim | Path or source | Ref | Blob or commit | Result | Line |
|---|---|---|---|---|---|---|
| RC-01 | The failing test is defined | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 280 |
| RC-02 | The one-site path uses the seed site | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 43 |
| RC-03 | The screenshot assertion runs before the header compare | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 283 |
| RC-04 | The header assertion requires the nine one-site headers | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 284 |
| RC-05 | The site-cell check waits for zero matches | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 285 |
| RC-06 | The row check waits for the one-site row | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 286 |
| RC-07 | The screenshot helper calls page.screenshot with full_page set to true | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 105 |
| RC-08 | The open_history helper waits for the table | tests/e2e/upgrade_portal/test_history_site_column_journey.py | main | 3c8c934235cc6d37aa1caa63e0e2ddab45400ad6 | present | 121 |
| RC-09 | The route reads site_id from the query string | src/interfaces/portals/upgrade_portal/app/routes/review.py | main | b26716b474e1ac6f7fa69257e08258eab254021a | present | 2134 |
| RC-10 | The route passes site_id to HistoryCaptureColumns | src/interfaces/portals/upgrade_portal/app/routes/review.py | main | b26716b474e1ac6f7fa69257e08258eab254021a | present | 2154 |
| RC-11 | shows_site_column is true only when site_id is empty | src/interfaces/portals/upgrade_portal/app/routes/review.py | main | b26716b474e1ac6f7fa69257e08258eab254021a | present | 1771 |
| RC-12 | The template shows the Site header only when shows_site_column is set | src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html | main | 5772982da0371724d0b51d1c93a5271f2d9237cd | present | 511 |
| RC-13 | The contract test asserts that the one-site table has no Site header | tests/contract/upgrade_portal/test_history_routes.py | main | 6c20d269b81551930119a385355ecef73066e947 | present | 1103 |
| RC-14 | The unit test keeps the one-site column values | tests/unit/upgrade_portal/test_issue_3486_history_site_column.py | main | 4872b19fd882d73b4681a0c1fc11a1dba4384074 | present | 300 |
| RC-15 | The page fixture installs the screenshot retry | tests/e2e/upgrade_portal/conftest.py | main | d14fda9f0a4cf69dc3c1ec60efa5adb863b73840 | present | 2930 |
| RC-16 | The seed site comment says no other journey reads the site | tests/e2e/upgrade_portal/conftest.py | main | d14fda9f0a4cf69dc3c1ec60efa5adb863b73840 | present | 475 |
| RC-17 | The retry helper retries once after the Chromium message | tests/e2e/upgrade_portal/screenshot.py | main | 81c01d6a329918e0cf952be642f84d66f2903449 | present | 20 |
| RC-18 | A unit test covers the Chromium retry message | tests/unit/upgrade_portal/test_journey_evidence.py | main | a4c26e89aad053754840554f2c2a5bc868255af3 | present | 17 |
| RC-19 | The shard job limit is 20 minutes | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 782 |
| RC-20 | The upgrade-portal shard row runs tests/e2e/upgrade_portal, in rows at lines 793 to 797 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 793 |
| RC-21 | The shard pytest command keeps the timeout, screenshot, trace, and output options | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 909 |
| RC-22 | The shard pytest output passes through tee to the shard log | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 909 |
| RC-23 | The diagnostics upload runs after a failure or a cancel | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 939 |
| RC-24 | The diagnostics artifact name starts with e2e-diagnostics | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 942 |
| RC-25 | The diagnostics artifact keeps the browser output folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 946 |
| RC-26 | The diagnostics artifact keeps the phase trail | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 945 |
| RC-27 | The diagnostics upload warns when no file exists | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 947 |
| RC-28 | The required check name is E2E smoke tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 955 |
| RC-29 | MYPY_PATHS excludes the tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 93 |
| RC-30 | RADON_PATHS excludes the guard file | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 99 |
| RC-31 | VULTURE_PATHS, PYDOCSTYLE_PATHS, and INTERROGATE_PATHS exclude the tests folder, at lines 101 to 107 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 101 |
| RC-32 | The guard holds class ShardPartitionAudit | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 35 |
| RC-33 | The guard pins the pytest options of the shard command | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 24 |
| RC-34 | The guard has no check of the diagnostics upload | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | absent | 0 |
| RC-35 | The class ShardPartitionAudit holds six methods, the first at line 39 | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 39 |
| RC-36 | The tests/guardrails folder holds 79 direct entries | root tree of main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-37 | The tests/e2e/upgrade_portal folder holds 68 direct entries | root tree of main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-38 | The quality gate page defines the playwright gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 68 |
| RC-39 | The gate page warns that the browser gate can report a false pass | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 74 |
| RC-40 | The development setup runs the browser tests with pytest | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 268 |
| RC-41 | The container policy has a section for test and debug containers | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-42 | The architecture page places the upgrade capture portal on port 8056 | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 243 |
| RC-43 | The changelog README names the file rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| RC-44 | The changelog README exempts internal-only changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-45 | The changelog guard allows the issue name pattern | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 38 |
| RC-46 | The changelog guard allows five change types | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| RC-47 | The constitution holds the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-48 | The constitution holds the inline comment rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-49 | The constitution holds the action logging rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-50 | The constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-51 | The constitution is the authoritative source for MistHelper | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 528 |
| RC-52 | The copilot instructions hold the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-53 | The copilot instructions hold the test quality ratchet | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-54 | AGENTS requires each test to be able to fail | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| RC-55 | The spec route uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-56 | requirements-dev pins pytest-playwright 0.10.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 333 |
| RC-57 | requirements-dev pins pytest-timeout 2.4.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 335 |
| RC-58 | Commit 351871c is an ancestor of main | commit | main | 351871c4345405cdd035b043b046f046f192ddc1 | present | 0 |
| RC-59 | Commit e4487cd7 is not on main | commit | main | e4487cd7cb1661666e7c7f815d50655c05d7fb95 | absent | 0 |
| RC-60 | Commit 9991d30a is an ancestor of main | commit | main | 9991d30a187e5d215462eefac60a09a57e5f99e5 | present | 0 |
| RC-61 | The merge commit of PR 4251 is an ancestor of main | commit | main | 0f42cdea6e96b4e5a416e413562a6101aa4f8e37 | present | 0 |
| RC-62 | The merge commit of PR 4248 is an ancestor of main | commit | main | 87e7f5a55922ef0c8a3c631af80f67d575c163d2 | present | 0 |
| RC-63 | pytest-playwright defines the output option | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local .venv | not applicable | present | 762 |
| RC-64 | pytest-playwright defines the tracing option | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local .venv | not applicable | present | 767 |
| RC-65 | pytest-playwright defines the screenshot option | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local .venv | not applicable | present | 779 |
| RC-66 | pytest-playwright takes a failure screenshot only for a failed test | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local .venv | not applicable | present | 879 |
| RC-67 | pytest-playwright keeps a trace only for a failed test under retain-on-failure | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local .venv | not applicable | present | 895 |
| RC-68 | Pytest prints failure details in the terminal summary | .venv\Lib\site-packages\_pytest\terminal.py | local .venv | not applicable | present | 1037 |
| RC-69 | The pinned pytest has no instafail option | .venv\Lib\site-packages\_pytest | local .venv | not applicable | absent | 0 |
| RC-70 | The Playwright assertion timeout is 5 seconds by default | https://playwright.dev/python/docs/test-assertions | fetched 2026-11-26 | not applicable | present | 0 |

## Sources

| Source | Path or URL | Used for |
|---|---|---|
| Issue #4249 and its comments | GitHub issue, read with `gh issue view` | Symptoms, owner comments, and labels |
| Run 38860502112, job 116842182317 | GitHub Actions log, read with `gh run view` | Log evidence (R1) |
| Run 38870153718, job 116873064875 | GitHub Actions log, read with `gh run view` | Later pass (R1) |
| PR #4251, PR #4248, PR #4242 | GitHub pull requests, read with `gh pr view` | Shard change and page-close fix |
| PR #650 | GitHub pull request, search hit only | Not linked. It matched the text "4249" only. |
| Issues #3486, #4247, #4250 | GitHub issues, read with `gh issue view` | Related work |
| tests/e2e/upgrade_portal/test_history_site_column_journey.py | Local read. Blob matches `main`. | Failing test (RC-01 to RC-08) |
| src/interfaces/portals/upgrade_portal/app/routes/review.py | Local read. Blob matches `main`. | Route and columns (RC-09 to RC-11) |
| src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html | Local read. Blob matches `main`. | Template guard (RC-12) |
| tests/contract/upgrade_portal/test_history_routes.py | Local read. Blob matches `main`. | Contract test (RC-13) |
| tests/unit/upgrade_portal/test_issue_3486_history_site_column.py | Local read. Blob matches `main`. | Unit test (RC-14) |
| tests/e2e/upgrade_portal/conftest.py | Local read. Blob matches `main`. | Page fixture and seed data (RC-15, RC-16) |
| tests/e2e/upgrade_portal/screenshot.py | Local read. Blob matches `main`. | Screenshot retry (RC-17) |
| tests/unit/upgrade_portal/test_journey_evidence.py | Local read. Blob matches `main`. | Retry message test (RC-18) |
| .github/workflows/ci.yml | Local read. Blob matches `main`. | Shard job and diagnostics (RC-19 to RC-31) |
| tests/guardrails/test_e2e_shard_partition.py | Local read. Blob matches `main`. | Guard class and options (RC-32 to RC-35) |
| documentation/quality-gates.md | Local read. Blob matches `main`. | Gate page (RC-38, RC-39) |
| documentation/development-setup.md | Local read. Blob matches `main`. | Browser test command (RC-40) |
| documentation/container-deployment.md | Local read. Blob matches `main`. | Container policy (RC-41) |
| documentation/architecture.md | Local read. Blob matches `main`. | Portal port (RC-42) |
| changelog.d/README.md | Local read. Blob matches `main`. | Fragment rules (RC-43, RC-44) |
| tests/guardrails/test_changelog_fragment_policy.py | Local read. Blob matches `main`. | Guard patterns (RC-45, RC-46) |
| .specify/memory/constitution.md | Local read. Blob matches `main`. | Rules (RC-47 to RC-51) |
| .github/copilot-instructions.md | Local read. Blob matches `main`. | Local gates and ratchet (RC-52, RC-53) |
| AGENTS.md | Local read. Blob matches `main`. | Test rule (RC-54) |
| .specify/scripts/powershell/spec-route.ps1 | Local read. Blob matches `main`. | Route rule (RC-55) |
| requirements-dev.txt | Local read. Blob matches `main`. | Pins (RC-56, RC-57) |
| .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | Local read of a third-party file | Option names and failure rules (RC-63 to RC-67) |
| .venv\Lib\site-packages\_pytest\terminal.py | Local read of a third-party file | Failure summary (RC-68) |
| .venv\Lib\site-packages\_pytest | Local search of a third-party folder | Absence of `--instafail` (RC-69) |
| https://playwright.dev/python/docs/test-assertions | Fetched 2026-11-26 | Default assertion timeout (RC-70) |
| specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | Local read of headings only | Record shape. No content was copied. |
| .specify/templates (four templates) | Local read | Record headings |
| documentation/operator-guide.md | Local search | No history Site column text (R6) |

## Unverified

| ID | Item | Reason |
|---|---|---|
| U-1 | The issue states that the history test passed in the E2E run of PR #4242 before its merge. | No run log was read. |
| U-2 | The issue states that a full isolated container run at commit `e4487cd` passed with 922 passed and 51 skipped. | No log was read. |
| U-3 | The issue states that the issue artifact endpoint returned HTTP 404. | The endpoint was not called in this phase. |
| U-4 | The owner comment of 2026-10-25 shows `1 passed in 4.00s` for a local run at `9991d30`. | The comment is the only source. No log exists on GitHub. |
| U-5 | Whether other journeys write rows for the seed site `e2e-stored-poll-site`. | The conftest comment says no other journey reads the site. Writes were not searched. |
| U-6 | The writer of `test-artifacts/e2e-phase-trail.jsonl`. | The writer was not read. |
| U-7 | Whether CS-1 or CS-2 caused the failure in run 38860502112. | The log holds no assertion text. No artifact of that run exists. |
| U-8 | The retention period of GitHub logs and artifacts. | The upload step sets no retention (`ci.yml` lines 939 to 947). The repository and account settings were not read. |
| U-9 | The Playwright expect default in the pinned package. | The fetched docs state 5 seconds (RC-70). The local package files searched did not show the default. |
| U-10 | The exact moment when pytest prints each outcome line. | The timing argument in R2 assumes the print follows the call phase. The reporting code was not read. |
| U-11 | Whether the next failed run keeps a failure screenshot and a trace. | The next run is outside this record. |

## Skills and API Scope

- No skill was loaded. The brief allows a skill for Podman or Juniper device questions. This feature asks neither. The `debug-live` skill needs live debugging, which this phase does not allow.
- This record makes no Mist API or mistapi claim. The Mist API reference files, the OpenAPI file, and the pinned mistapi package were not read, because this feature changes no Mist call. No OpenAPI or SDK citation applies.
