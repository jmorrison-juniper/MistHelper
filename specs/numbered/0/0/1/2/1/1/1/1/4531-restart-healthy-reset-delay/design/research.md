# Research: Restart healthy reset test repair

## Method

The review used read-only GitHub commands and local reads. Truth order for code claims is GitHub main, read through the contents and tree APIs. Local files supported reading only. Two local files differ from main, so this record cites no local value for them. No build, test, linter, or repository script ran. Skill used: `debug-live`, for its symptom-to-origin method only. Live debugging needs test execution, which the brief forbids.

## Documents reviewed

- `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`: read in full.
- The spec, plan, tasks, and checklist templates under `.specify/templates/`: read in full. The record follows their headings.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`: file list read. Its shape is copied. Its content is not copied.
- `documentation/quality-gates.md`: the writing gate section and the gates table (remote lines 277 to 292). Applies to the STE check of the record.
- `documentation/development-setup.md`: the Python version and the bootstrap command (remote lines 29, 32, and 52). Applies to the quickstart.
- `documentation/container-deployment.md`: targeted search. The Podman restart policy at line 118 concerns the container, not the session loop. The change adds no container. Not applicable.
- `documentation/operator-guide.md`: targeted search. No restart control is documented for the session loop. Not applicable.
- `documentation/architecture.md`: targeted search for restart, healthy, and session script terms. No match. Not applicable.
- Mist API documents (`documentation/mist-api-openapi31yaml.yaml`, `MIST_API_GET_ENDPOINTS.md`, and `MIST_API_MISSING_ENDPOINTS.md`): not applicable. No Mist API call is in the issue path.
- The pinned `mistapi` package under `.venv\Lib\site-packages\mistapi`: not applicable. The record makes no SDK claim.
- Skill `debug-live`: loaded. Used for the symptom-to-origin method only.

## Issue facts

Source: `gh issue view 4531` (read-only JSON).

- Title: "Test failure: restart healthy reset reports an unexpected delay". State: OPEN. Author: `jmorrison-juniper`. Created 2026-10-30T15:08:49Z. Updated 2026-11-08T10:28:06Z.
- Labels: `bug`, `tests`, `needs-human-review`. The `in-progress` label is absent now.
- Failing test: `tests/unit/container/output_defaults/test_session.py::TestSessionRestarts::test_actual_restart_controls_match_base[plan2-controls2-expected2]`.
- Line of the failure in the baseline file: line 283 (`assert result == expected, observation.output`). Baseline is commit `d30ef1690e9c00698e0e462f54de793c7a2093b9`.
- Observed tuple: `(0, 5, [1, 2, 1, 1])`. Expected tuple: `(0, 5, [1, 2, 1, 2])`.
- Environment in the issue: macOS, Python 3.13.13, pytest 9.1.1. The issue calls it a local run.
- Complete unit run: `1 failed, 29921 passed, 25 skipped, 5 warnings in 811.74s`. Baseline complete run: `29916 passed, 25 skipped, 5 warnings in 822.29s`. Second complete run on the final cache candidate: `29922 passed, 25 skipped, 5 warnings in 823.02s`. Isolated class run: `4 passed in 36.81s`.
- Comments: 2026-10-30 (final candidate), 2026-10-31 (test file reservation), and 2026-11-06 (PR 4555 merged, cause unverified, keep open).
- Issue log file `files/unit-post.log` is outside the repository. Its SHA-256 values are not verified.

## Linked work

Source: `gh pr list --search 4531`, `gh pr view 4555`, `gh api` commit checks.

- PR 4555, "test(container): control restart health timing": state MERGED, merged 2026-11-05T11:21:09Z. Head branch `jmorrison-juniper-restart-healthy-reset`. Head `c82fda202bbec59ea0f28a7ffa1a11789d0c91a9`. Merge commit `02ffc4ac1ad65f5018a93b548fc65bc70a445d40`. One file changed: `tests/unit/container/output_defaults/test_session.py`, +95 and -2.
- Merge commit membership: the compare API reports status `ahead` for the merge commit against main, with 124 commits ahead and 0 behind. The merge commit is in main.
- Head checks on `c82fda20`: 30 check runs. 22 succeeded and 8 were skipped. No check failed.
- Main head: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Main run 45774119357 (Quality Gates, manual dispatch) succeeded. Its log (lines 44821 to 44828) shows the eight restart cases with status PASSED.
- Baseline commit `d30ef1690e9c00698e0e462f54de793c7a2093b9` (2026-10-30T13:51:30Z) has three plan rows and no regression functions.
- Cache commits `4202f0265fc4eaf3b0697a3ef620c912f06f75fa` (parent baseline) and `b068614e4ca0d6828d711bdc876b1092de87bef7` (parent 4202f026) exist as commit objects. Both diverge from main: `compare` returns status `diverged`, 155 ahead, with 1 and 2 behind. Neither commit is in main.
- PR 4555 states that a controlled fourth-launch stall reproduced `[1, 2, 1, 1]` on unchanged main source. That statement is from the PR body. This agent did not run it.

## CI reproduction

Commands (read-only): `gh run list --status failure --limit 200`, then `gh run view` with `--log-failed` for each failed run created on or after 2026-10-26T00:00Z. A second pass covered runs created before 2026-10-30T13:50Z.

- Failed runs in the window: 167.
- Runs that contain restart case lines: 16. Of these, 10 are after the merge and 6 are before it.
- Restart case lines with status FAILED: 0. Every restart case line in the 16 runs reads PASSED.
- Other failures in the same runs: netcool runbook smoke test (run 45767339705), `test_contract.py::TestSourceContract::test_live_sources_require_option_two` (run 45459366990), uv locked sync and bootstrap tests (run 44963576593), and `test_standalone.py` router tests (run 44787166785).
- Post-merge runs with restart lines: 45767339705, 45459366990, 44963576593, 44787166785, 44605882058, 43360197751, 42897007918, 42887670002, 42514811481, 42181849465.
- Pre-merge runs with restart lines: 41345234865, 41203400241, 41155632796, 41086069697, 40692675966, 40273046994.

Result: The failure did not reproduce in any scanned CI run. The complete failure block exists only in the issue body. Scope limit: the scan covered failed runs only. A failed restart case always fails its run, so no failed case can hide in a passed run.

## Root cause analysis

1. **Symptom**: The issue log shows launch 4 as `Attempt 1 of 3` with `Next start in 1 seconds`. The expected line is `Attempt 2 of 3` with `Next start in 2 seconds`. The failed-start count and the restart delay reset at launch 4.
2. **Mechanism in the session script**: `RUN_START_SECONDS=$SECONDS` (line 133) and `RUN_SECONDS=$(( SECONDS - RUN_START_SECONDS ))` (line 141) give the measured duration. A launch is a healthy run when `RUN_SECONDS` is at least `MIN_HEALTHY_SECONDS` (line 150). The healthy branch sets `FAILED_STARTS=0` and restores `RESTART_DELAY` (lines 151 and 152).
3. **Baseline test design**: Plan2 sets the healthy threshold to 2 seconds (baseline line 257). The recorder sleeps the planned duration in real time (`session.py` line 67). Launch 4 plans 0.0 seconds (plan row at remote line 292). Its real duration is interpreter start-up and recorder work only.
4. **Arithmetic**: If `SECONDS` gives whole seconds (unverified, U-2), a difference of two readings is less than one second away from the real interval. A reading of 2 therefore requires a real interval longer than 1 second. Under load, launch 4 can exceed 1 second. Launch 4 then counts as healthy, which resets the count and the delay. That reproduces `[1, 2, 1, 1]`.
5. **Evidence for the mechanism**: The issue log shows the reset at launch 4 (step 1). PR 4555 reports that a controlled 2-second stall reproduced the same tuple on unchanged source. The stall regression at remote line 357 adds 2 seconds to launch 4, so the arithmetic predicts that result. The isolated class passed. A lower load keeps launch times below one second, which fits an intermittent result.
6. **Status**: Probable mechanism. The original run recorded no launch timing (U-1). The controlled clock in PR 4555 removes real launch time from the decision, so this mechanism cannot change the current test result.
7. **Environment note**: The issue used Python 3.13.13 and pytest 9.1.1. The repository requires Python 3.15 and pins pytest 9.2.0 (remote lines 23 and 325).

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Human decisions: none. No decision falls in the four categories of brief section 6.

### D-1 Keep the controlled clock

- Alternatives: (a) Restore real elapsed time with a larger threshold. (b) Measure sub-second time in the session script. (c) Keep the controlled clock from PR 4555.
- Chosen: (c).
- Reason: The decision then depends on planned values only. Real timing changes with machine load.
- Risk: The fixture depends on the text of lines 133 and 141. Mitigation: the exact tuple and launch-count assertions (remote lines 344 to 346) fail on a mismatch.

### D-2 Make no production change

- Alternatives: (a) Change the session script to use sub-second health timing. (b) Raise the default healthy threshold. (c) Make no production change.
- Chosen: (c).
- Reason: Issue 4531 records the test failure only. The default threshold of 30 seconds limits the whole-second effect to about one second. A production change needs its own issue.
- Risk: A run longer than 29 real seconds can count as healthy (analysis A9). Record it for later review.

### D-3 State the cause as probable and unverified

- Alternatives: (a) Mark the cause verified. (b) Run a load experiment on the baseline file. (c) Record a probable mechanism and list each unverified part.
- Chosen: (c).
- Reason: The original run recorded no launch timing, so no experiment proves that run's cause. The controlled clock already removes the input from the decision.
- Risk: A different cause may exist. Mitigation: the Unverified list and CI results after the merge.

### D-4 Repair the logging and comment gaps

- Alternatives: (a) Leave the merged code as is. (b) File a separate issue. (c) Repair the gaps in this change.
- Chosen: (c).
- Reason: Principles VI and VII are non-negotiable. The gaps come from the PR 4555 additions. The repair changes no behavior.
- Risk: A comment inside the fixture changes the bash source. Mitigation: T005 adds comments after statements only and reruns the restart class.

### D-5 Keep six members in the restart class

- Alternatives: (a) Move the fixture into the shared helper. (b) Move the fixture to a new module in `output_defaults`. (c) Keep the class and record the violation.
- Chosen: (c).
- Reason: FR-007 forbids a change to the shared helper. A new module makes `output_defaults` hold six children.
- Risk: The class grows further. Mitigation: remediation R-1 in plan.md.

### D-6 Mark Principle IV steps 10 to 12 as not applicable

- Alternatives: (a) Dispatch the container build and deploy the image. (b) Skip the steps with no record. (c) Record the steps as not applicable, with a check.
- Chosen: (c).
- Reason: The container build paths list product files only (remote lines 6 to 19). No product file changes, so the image content stays the same.
- Risk: A reviewer may read the constitution literally. Mitigation: T-MERGE checks that no build run starts for the merge commit.

### D-7 Add no changelog fragment

- Alternatives: (a) Add a fragment named for the issue. (b) Add a fragment named for the pull request. (c) Add no fragment and state the reason in the pull request body.
- Chosen: (c).
- Reason: The change is internal. `changelog.d/README.md` line 58 says to add no fragment for an internal-only change and to state the reason.
- Risk: None known.

### D-8 Use the fix branch and the test commit type

- Alternatives: (a) Use a `docs` branch for the record. (b) Use a `fix` branch for the issue. (c) Use a `chore` branch.
- Chosen: (b). Branch `fix/4531-restart-healthy-reset-delay`. Commit type `test` with scope `container`.
- Reason: The constitution's branch rule lists `fix`, `feat`, and `chore`. The change repairs a failing test. The title check accepts the `test` type.
- Risk: The record adds a documentation change to a test branch. The commit message states both changes.

### D-9 Wait for human review before merge

- Alternatives: (a) Enable auto-merge after CI passes. (b) Wait for a human approval. (c) Close the issue without a merge.
- Chosen: (b).
- Reason: The issue carries `needs-human-review`. The label states that a human must review before merge.
- Risk: The merge waits. Mitigation: T-MERGE defines the approval step.

### D-10 Verify on the pinned environment

- Alternatives: (a) Reproduce on Python 3.13.13 and pytest 9.1.1. (b) Use Python 3.15.2 and pytest 9.2.0. (c) Use only the CI result.
- Chosen: (b).
- Reason: `pyproject.toml` line 23 requires Python 3.15. `requirements-dev.txt` line 325 pins pytest 9.2.0. The issue environment lies outside the supported set.
- Risk: Differences between 3.13 and 3.15 go unchecked. The issue environment stays unverified (U-7).

## Remote verification table

Row count: 33. The same 33 checks appear in `META_DIR\4531-STATUS.json` under `remote_checks`. Result words follow the brief: present, absent, partial, or stale. Line 0 means a presence check on the blob or the commit only.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | PR 4555 merged the restart test repair on main | tests/unit/container/output_defaults/test_session.py | main | 4c4bc48bd5071c438fd7d02a5cbb8caacb02a313 | present | 234 |
| R02 | Merge commit 02ffc4ac is in main (compare ahead 124, behind 0) | commit 02ffc4ac1ad65f5018a93b548fc65bc70a445d40 | main | 02ffc4ac1ad65f5018a93b548fc65bc70a445d40 | present | 0 |
| R03 | Baseline has the failing assertion at line 283 | tests/unit/container/output_defaults/test_session.py | d30ef1690e9c00698e0e462f54de793c7a2093b9 | 06035d6562229fdee16df22b9ebc14685cf1622d | present | 283 |
| R04 | Main head is f03c6c9b36d612a48d7b9652998c2fd87dd777ca | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R05 | Main run 45774119357 log shows eight restart cases passed | CI log for tests/unit/container/output_defaults/test_session.py | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 44821 |
| R06 | PR 4555 head has 30 check runs, 22 success and 8 skipped | PR 4555 check runs | c82fda202bbec59ea0f28a7ffa1a11789d0c91a9 | c82fda202bbec59ea0f28a7ffa1a11789d0c91a9 | present | 0 |
| R07 | Session script unchanged on main | container/scripts/misthelper-session.sh | main | 599d5753b35981e60085d0c4342dacf0e484ec3b | present | 133 |
| R08 | Session script unchanged at baseline | container/scripts/misthelper-session.sh | d30ef1690e9c00698e0e462f54de793c7a2093b9 | 599d5753b35981e60085d0c4342dacf0e484ec3b | present | 133 |
| R09 | Healthy threshold default is 30 seconds | container/scripts/misthelper-session.sh | main | 599d5753b35981e60085d0c4342dacf0e484ec3b | present | 32 |
| R10 | Recorder sleeps the planned duration in real time | tests/unit/container/output_defaults/session.py | main | c7cc9cd037cd5c3595e5decafaefca54d5826111 | present | 67 |
| R11 | Shared helper differs from baseline in one import path and one comment | tests/unit/container/output_defaults/session.py | d30ef1690e9c00698e0e462f54de793c7a2093b9 | 26c6346649e3521f35c7be1a4949a7042a17c5ee | partial | 21 |
| R12 | Relocated import target exists on main | tests/unit/prod_readiness/operations/exporting/container/build_support/bash_support.py | main | 56f8e5d51942d20c874167c04773f1970197034a | present | 0 |
| R13 | Old import target is absent on main | tests/unit/container/bash_support.py | main | none | absent | 0 |
| R14 | Pinned pytest is 9.2.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 325 |
| R15 | Project requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R16 | CI root-units shard exists, and CI uses Python 3.15 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 262 |
| R17 | CI mypy paths exclude the tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R18 | Container build paths list product files only | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| R19 | AGENTS rule for a test that fails only in a full run | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 138 |
| R20 | Local gates table in the repository instructions | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R21 | Constitution Principles VI and VII are non-negotiable | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R22 | Constitution five-child limit for each hierarchy level | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R23 | Numeric route uses eight base-5 digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R24 | Reference record shape exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R25 | No legacy record for issue 4531 exists | specs folder names that start with 4531 | main | none | absent | 0 |
| R26 | Cache commit 4202f026 is not in main | commit 4202f0265fc4eaf3b0697a3ef620c912f06f75fa | main | 4202f0265fc4eaf3b0697a3ef620c912f06f75fa | partial | 0 |
| R27 | Cache commit b068614e is not in main | commit b068614e4ca0d6828d711bdc876b1092de87bef7 | main | b068614e4ca0d6828d711bdc876b1092de87bef7 | partial | 0 |
| R28 | Changelog rule for internal-only changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R29 | Contract base copy compares a stored hash | tests/unit/container/output_defaults/contract.py | main | 1ee466a95dfda332a7fe536adad61d230bd53c11 | present | 227 |
| R30 | Stall regression injects a delay on the fourth launch | tests/unit/container/output_defaults/test_session.py | main | 4c4bc48bd5071c438fd7d02a5cbb8caacb02a313 | present | 357 |
| R31 | PR template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| R32 | STE gate command form | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| R33 | Bootstrap script exists | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |

Notes on the table: R03 and R08 use the baseline commit as the ref. R11 is partial because the behavior is unchanged, but one import path differs from baseline. R26 and R27 are partial because the commits exist as objects but are not in main.

## Sources

- GitHub issue: https://github.com/jmorrison-juniper/MistHelper/issues/4531
- GitHub pull request: https://github.com/jmorrison-juniper/MistHelper/pull/4555
- Main CI run with restart cases: https://github.com/jmorrison-juniper/MistHelper/actions/runs/45774119357
- PR head CI run (Quality Gates): https://github.com/jmorrison-juniper/MistHelper/actions/runs/42015562235
- Remote files on main, read through the contents API with ref main: the paths listed in the table above.
- Local reads for context only: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four templates under `.specify/templates/`, and the reference record under `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`.
- Attempted URL with no content: https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html (transport failure). The alternate page https://www.gnu.org/software/bash/manual/bash.html also failed.
- Mist API documents (`documentation/mist-api-openapi31yaml.yaml`, `MIST_API_GET_ENDPOINTS.md`, `MIST_API_MISSING_ENDPOINTS.md`): not applicable. The issue path makes no Mist API call. The test harness imports no mistapi module.
- The pinned `mistapi` package in `.venv\Lib\site-packages\mistapi`: not applicable for the same reason. No SDK claim appears in this record.

## Unverified

- **U-1 Original launch timing.** The original run recorded no timing. Reason: the issue log has no timing data, and the audit session log is outside this repository.
- **U-2 Whole-second `SECONDS`.** The Bash manual could not be fetched. Reason: a transport failure. The test author assumes whole seconds (remote line 265).
- **U-3 Original load and scheduler state.** Reason: the issue states that scheduler activity was not recorded.
- **U-4 Stall reproduction.** The PR 4555 statement that a controlled stall reproduced `[1, 2, 1, 1]` was not re-run. Reason: running tests is forbidden for this agent.
- **U-5 Local results in the issue and the PR.** The counts from the issue and PR 4555 were not repeated. Reason: running tests is forbidden. The CI results on main and the PR head replace them.
- **U-6 Mypy errors in the test file.** PR 4555 reports errors at lines 47, 50, and 83. Reason: mypy did not run, and the configured paths exclude tests.
- **U-7 Issue environment.** The results from Python 3.13.13 and pytest 9.1.1 were not reproduced. Reason: the environment is outside the supported set (D-10).
- **U-8 Audit log hashes.** The SHA-256 values for `files/unit-post.log` and `files/unit-final.log` were not checked. Reason: the files are outside this repository.
