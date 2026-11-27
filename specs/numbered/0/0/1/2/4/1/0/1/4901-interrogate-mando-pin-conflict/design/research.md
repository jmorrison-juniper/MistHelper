# Research: Interrogate Gate Failure on PR #4888

Each decision names the chosen option, the rejected options, the reason, and the risk. Remote facts come from GitHub reads of `jmorrison-juniper/MistHelper`. Each identifier from RV-01 to RV-69 matches one row of the remote verification table. CI run facts come from GitHub reads of workflow runs and appear under Sources.

## Decision summary

| ID | Decision | Alternatives rejected | Reason | Risk | Human decision |
|----|----------|-----------------------|--------|------|----------------|
| D-1 | Keep `mando` 0.7.1 on `main`. Add a Dependabot ignore rule for `mando` 0.8 and later. | Merge the bump with a newer radon. Force `mando` 0.8 with an override. Remove radon. Leave PR #4888 open. | The smallest reversible change. No newer radon release is known. It matches the held-pin policy. | Dependabot may reject the syntax (U-1). | No |
| D-2 | Close PR #4888 after the fix merges, with a preservation proof. | Push a revert to the Dependabot branch. Recreate the PR with a comment. Leave it open. | Closing removes the failing check from the open list. The proof keeps the evidence. | Closing hides the PR. Reopening restores it. | No |
| D-3 | Write the rule as `versions: [">= 0.8"]`. | `versions: ["0.8.x"]`. `update-types: ["version-update:semver-minor"]`. | The range covers 0.8 and later. It keeps the 0.7 patch line open. | The range must follow the pip pattern. | No |
| D-4 | Add three cases to `TestDependabotPolicy`. Update the snapshot in the same change. | A new test file. No test. | The class already reads the file. The repository requires a contract test for each workflow value. | Snapshot drift. The whole-policy test fails on drift. | No |
| D-5 | Keep `.github/workflows/ci.yml` unchanged. | Install only `interrogate` in the job. Add a `pip check` step. | The job steps are correct. The cause is the pin, not the job. | The same conflict class can return. | No |
| D-6 | Add one fragment named `issue-4901-interrogate-mando-pin-conflict.md`. | Add no fragment under the README internal-change rule. | The constitution requires one fragment for each change. | The README and the constitution conflict (A-3). | No |
| D-7 | Name the 14 sibling issues with `Refs` only. | `Closes` for each sibling. New issues for each gate. | The gate workflow closes each sibling issue after its gate passes. | The closure is unverified (U-6). | No |
| D-8 | Dispatch `container-build.yml` by hand after the merge. Then verify and deploy. | Skip constitution steps 10 to 12. Defer them to a later release. | The constitution forbids skipped steps. | The image content is unverified (U-4). | No |

## R1. Failing check, failing step, and failing rule

- **Decision**: The failing check is `Interrogate (docstring coverage)`. The failing step is `Run pip install -r requirements-dev.txt`. The failing rule is the pip resolver rule that rejects `mando==0.8.2` with `radon==6.0.1`.
- **Evidence**: Run 45064243269 (workflow "Quality Gates", event `pull_request`, head `e86098cdc2b189d217805b3b4060ef609cbc37af`, conclusion `failure`). Job 137336719025 has conclusion `failure`. Its failed step is `Run pip install -r requirements-dev.txt`. The full job log has 605 lines. These lines appear in the job log:
  - `2026-11-22T20:06:27.4036410Z ##[group]Run pip install -r requirements-dev.txt`
  - `2026-11-22T20:06:31.3528193Z Collecting mando==0.8.2 (from -r requirements-dev.txt (line 179))`
  - `2026-11-22T20:06:35.6378156Z ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.`
  - `2026-11-22T20:06:35.6380215Z     radon 6.0.1 depends on mando<0.8 and >=0.6`
  - `2026-11-22T20:06:35.6382585Z ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts`
  - `2026-11-22T20:06:36.0276169Z ##[error]Process completed with exit code 1.`
- The job log holds zero `RESULT:` lines, so the interrogate command never started.
- Native Windows runs 45064235051 (job 137336693688, "Native Windows timeout budget") and 45064235097 (job 137336693895, "Native Windows audit report") show the same resolver lines. Each run holds one `ResolutionImpossible` line in its failed-step log.
- **Rationale**: The brief requires the exact check and rule. The log order shows that the install failed before the docstring command ran.
- **Risk**: Naming only the check hides the resolver cause. The record names the step and the rule too.

## R2. Root cause and scope

- **Decision**: One changed line causes the failure. PR #4888 changes `requirements-dev.txt` line 179 from `mando==0.7.1` to `mando==0.8.2`. The PR changes that one file, with one addition and one deletion.
- **Evidence**: The PR head holds `mando==0.8.2` at line 179 (RV-05). `main` holds `mando==0.7.1` at line 179 (RV-01). The file header states that uv generates the file (RV-03). Radon 6.0.1 requires `mando (<0.8,>=0.6)` in its installed metadata (RV-64). The lock file `uv.lock` keeps `mando` 0.7.1 at line 1301 (RV-06). The PR does not change `uv.lock`, so the lock and the export disagree.
- **Scope**: Run 45064243269 has 33 jobs. Five jobs succeed. Twenty-eight jobs fail. Twenty-six failed jobs print the resolver message. Two failed jobs fail in aggregator steps. Job `pytest (coverage gate)` (137338980629) fails in step `Verify dependency lock job` with `##[error]The dependency lock job finished with failure.`. Job `E2E smoke tests` (137339065340) fails in step `Verify E2E shards`.
- **Trace**: The path runs from the Dependabot pip stream to PR #4888, then to the Quality Gates workflow, then to the `interrogate` job, then to its pip install step (RV-16, RV-08, RV-10).
- **Rationale**: One line explains 26 of 28 failed jobs. The aggregator failures follow from failed upstream jobs.
- **Risk**: A failed job may hide a second cause. T-REMOTE-CI checks each failed job on the fix head.

## R3. Main baseline

- **Decision**: `main` needs no pin change. The fix belongs in the update policy.
- **Evidence**: The `main` head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Run 45774119357 (workflow "Quality Gates", head `f03c6c9`) has conclusion `success`. Its job `Interrogate (docstring coverage)` (139753527432) has conclusion `success`. Its log line at `2026-11-26T07:17:45.4549233Z` reads `RESULT: PASSED (minimum: 90.0%, actual: 99.7%)`. The `requirements-dev.txt` blob at `f03c6c9` equals the blob on `main` (RV-01). Branch protection on `main` reports `strict` set to true. Its required contexts include `Interrogate (docstring coverage)`. The quality gates document describes the same branch protection section (RV-31).
- **Rationale**: The failure appears only on the PR head, so the fix must change the update policy, not the pin.
- **Risk**: The docstring value on the fix head is unverified (U-2).

## R4. Options for the fix (D-1)

- **Options**:
  - A. Keep `mando` 0.7.1 and ignore `mando` 0.8 and later. Chosen.
  - B. Merge the bump and use a newer radon that accepts `mando` 0.8. Rejected. PyPI lists radon 6.0.1 as the latest release at fetch time (RV-66). No compatible release is known (U-3).
  - C. Merge the bump with a forced `mando` 0.8. Rejected. Radon declares `<0.8`, so a forced pin contradicts its declared support. Compatibility of the radon command line with `mando` 0.8 is unverified.
  - D. Remove radon and rewrite its job and its complexity command. Rejected. The scope exceeds the failure.
  - E. Leave PR #4888 open. Rejected. Its required check stays red.
- **Reason for option A**: It changes one policy file. It keeps the pin policy that `ci.yml` names for held dev tools (RV-15). It follows the npm ignore rule that already explains its reason (RV-18).
- **Risk**: Dependabot may reject the rule (U-1). A later radon release requires removing the rule (Caution in spec Edge Cases).

## R5. Dependabot ignore syntax (D-3)

- **Decision**: Write `versions: [">= 0.8"]` under `dependency-name: "mando"` in the pip stream.
- **Evidence**: The Dependabot options reference describes the `versions` option of `ignore` (RV-63). It states that ranges use the standard pattern of the package manager. Pip uses PEP 440 specifiers. The local `packaging` module documents `>=` as a PEP 440 operator (RV-65). The pinned `packaging` version is 26.3 at `requirements-dev.txt` line 228 (RV-04).
- **Alternatives rejected**: `versions: ["0.8.x"]` misses 0.9 and later releases. `update-types: ["version-update:semver-minor"]` blocks every minor release of `mando`, which is broader than the conflict.
- **Reason**: The range covers 0.8 and later releases. It leaves the 0.7 patch line open.
- **Risk**: Dependabot may reject the syntax. The check in T-MERGE and the next weekly run detect a rejection (U-1).

## R6. Handling PR #4888 (D-2)

- **Decision**: Close PR #4888 without a merge after the fix merges. Write a closing comment with a preservation proof.
- **Proof content**: The comment names the merged fix pull request. It names the head commit `e86098cdc2b189d217805b3b4060ef609cbc37af`. It names the blob SHA of `main` `requirements-dev.txt` (RV-01).
- **Alternatives rejected**:
  - Push a revert to the Dependabot branch. Rejected because the parallel-agent rules forbid a push to a branch another agent owns (RV-46).
  - Recreate the PR with a Dependabot comment. Rejected because the recreated PR fails again before the ignore rule exists.
  - Leave the PR open. Rejected because the required check stays red.
- **Reason**: The closing comment keeps the reason for the rejected bump. The merged fix keeps the policy.
- Caution: Closing a pull request hides it. Reopen the pull request if the closure is wrong.
- Warning: Do not push to `dependabot/pip/mando-0.8.2`. Dependabot owns that branch.
- Caution: Deleting the branch removes its name. Record commit `e86098c` in the closing comment before the deletion.
- **Risk**: The closing step must wait for the merge. A closure before the merge leaves no open record of the rejected bump.

## R7. Test design and snapshot (D-4)

- **Decision**: Add three parametrized cases to class `TestDependabotPolicy`. Update `POLICY_SNAPSHOTS["dependabot"]` in the same change.
- **Evidence**: The class reads `.github/dependabot.yml` through `yaml.safe_load` in its fixture (RV-22). It asserts that the complete policy equals the snapshot (RV-21). The snapshot holds the pip stream at line 23 (RV-20). A new key in the pip stream therefore fails the equality test until the snapshot changes.
- **Logging**: The class fixture logs before and after the read (RV-22). The new cases follow the same pattern, as constitution Principle VII requires (RV-54).
- **Inline comments**: Each new line carries an inline comment, as constitution Principle VI requires (RV-53).
- **Repository rule**: The repository requires a test that can fail (RV-43). It also requires a contract test for each workflow value that a future edit can remove (RV-48).
- **Alternatives rejected**: A new test file duplicates the policy reader and adds a file. No test leaves the rule without a guard.
- **Reason**: The existing class already guards the file. The cases fail before the rule exists.
- **Risk**: The snapshot can drift from the file. The whole-policy assertion fails on any drift.

## R8. CI job unchanged (D-5)

- **Decision**: Keep `.github/workflows/ci.yml` unchanged. The interrogate job defines its install step (RV-10) and its docstring command (RV-11).
- **Alternatives rejected**: Installing only `interrogate` in the job bypasses the pinned file and can hide a future conflict. A `pip check` step adds a step and leaves the cause in place.
- **Reason**: The job steps are correct. The cause sits in the pin, and the policy change removes that cause.
- **Risk**: The same conflict class can return with another pin. The ignore rule and the export guard (RV-59) reduce that risk.

## R9. Changelog fragment (D-6)

- **Decision**: Add `changelog.d/issue-4901-interrogate-mando-pin-conflict.md`.
- **Evidence**: The constitution requires one fragment for each change (RV-55). The fragment README allows no fragment for an internal change (RV-28). The README names a file form for an issue that has no pull request (RV-29). The copilot instructions name fragments for user-visible changes (RV-39).
- **Reason**: The constitution is the stronger statement for this repository. The README form gives the name.
- **Name rule**: The file name stays fixed after the pull request opens, so the diff shows no rename.
- **Risk**: A reviewer may read the fragment as unnecessary. Analysis A-3 records the conflict.

## R10. Sibling issues (D-7)

- **Evidence**: The sync job opened 15 issues from run 45064243269. Issues #4891 to #4905 carry the suffix `(PR #4888)`. The mapping from issue to job is below. Issue #4894 maps to job `pytest (coverage gate)` by title and is listed as unverified (U-5).

| Issue | Gate title | Job | Job ID | Failed step |
|-------|-----------|-----|--------|-------------|
| #4891 | `ruff` | Ruff (lint) | 137336719229 | Run pip install -r requirements-dev.txt |
| #4892 | `black` | Black (format check) | 137339161296 | Run pip install -r requirements-dev.txt |
| #4893 | `mypy` | mypy (strict) | 137338084785 | Install dependencies |
| #4894 | `pytest` | pytest (coverage gate) | 137338980629 | Verify dependency lock job |
| #4895 | `bandit` | Bandit (security) | 137336719159 | Run pip install -r requirements-dev.txt |
| #4896 | `pip_audit` | pip-audit (CVE scan) | 137338084755 | Run pip install -r requirements-dev.txt |
| #4897 | `pylint` | Pylint (score gate) | 137338442217 | Install dependencies |
| #4898 | `radon` | Radon (complexity) | 137336719006 | Run pip install -r requirements-dev.txt |
| #4899 | `vulture` | Vulture (dead code) | 137336718674 | Run pip install -r requirements-dev.txt |
| #4900 | `pydocstyle` | pydocstyle (docstring style) | 137336719204 | Run pip install -r requirements-dev.txt |
| #4901 | `interrogate` | Interrogate (docstring coverage) | 137336719025 | Run pip install -r requirements-dev.txt |
| #4902 | `test_quality_gate` | Test quality ratchet (gate) | 137336719038 | Run pip install -r requirements-dev.txt |
| #4903 | `dependency_lock` | Dependency lock and exports | 137336719111 | Run pip install -r requirements-dev.txt |
| #4904 | `codeql_register_check` | CodeQL verdict register check | 137336719141 | Run python -m pip install -r requirements-dev.txt |
| #4905 | `upgrade_portal_journeys` | Upgrade portal journeys | 137339161249 | Install dependencies |

- **Decision**: Name the 14 sibling issues with `Refs` in the pull request body. Do not close them by hand.
- **Evidence for closure**: The quality gates document says that a later pull request run closes its issue (RV-32). A run on `main` closes it after the pull request closes.
- **Alternatives rejected**: `Closes` lines for all siblings risk closing issues that a later run must reopen. New issues duplicate the existing ones.
- **Risk**: The automatic closure is unverified (U-6).

## R11. Post-merge pipeline (D-8)

- **Evidence**: Constitution Principle IV requires steps 10 to 12 after the merge (RV-50). Step 10 waits for the main build (RV-51). Step 11 verifies the revision label (RV-52). Step 12 deploys the approved image. The container build workflow runs on a push to `main` that changes a product file, or on a manual dispatch (RV-40). This change edits no product file, so the build needs a manual dispatch.
- **Procedure**: The revision check follows the container deployment guide (RV-61). The update procedure follows the same guide (RV-60).
- **Decision**: After the merge, dispatch `container-build.yml` by hand on `main`. Verify the revision label. Then update and deploy the stack by the guide.
- **Alternatives rejected**: Skipping steps 10 to 12 breaks the constitution rule that no step is skipped (RV-50). Deferring them to a later release leaves `main` unverified.
- **Risk**: The image content is unverified (U-4).

## R12. Route for the record folder

- **Decision**: Keep the route `0/0/1/2/4/1/0/1` from the brief.
- **Evidence**: The route helper converts the number with base 5 and pads it to eight digits (RV-24, RV-25). The test helper uses the same algorithm (RV-23). The number 4901 in base 5 is `124101`. Padded to eight digits, it is `00124101`, which maps to `0/0/1/2/4/1/0/1`.
- **Five-children check**: On `main`, the folder `specs/numbered/0/0/1/2/4/1` holds one child, `4` (RV-27 shows the sibling record path). The record adds the child `0`, so the folder then holds two children. The folder `specs/numbered/0/0/1/2/4/1/0` is absent on `main` (RV-26), so it holds one child after the change.
- **Risk**: None known.

## R13. Legacy record and prior work

- **Decision**: No legacy record exists for issue 4901.
- **Evidence**: A recursive search of `specs` for folders named `4901-*` returns none. A glob for `specs/numbered/**/4901-*` returns none. The pull request search for `4901` returns an empty list. The open pull request search for `radon` or `mando` returns PR #4888 and PR #4208. The files of PR #4208 were not read (U-7). Seven pull requests are open in total.
- **Consequence**: The record counts show `found` set to false and zero for the other counts.

## R14. Skills and Mist scope

- **Decision**: No skill is loaded, and no Mist endpoint is read.
- **Reason**: The issue concerns a dependency resolver and a Dependabot policy. It involves no Podman, Juniper device, or Mist API behavior. No Mist claim appears in this record.

## Remote verification

Each row checks one claim. The table holds 69 rows. The count matches `remote_checks` in the STATUS file and the count in the summary.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RV-01 | `main` pins `mando==0.7.1` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RV-02 | `main` pins `radon==6.0.1` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RV-03 | `main` header states that uv generates the file | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 1 |
| RV-04 | `main` pins `packaging==26.3` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 228 |
| RV-05 | PR head pins `mando==0.8.2` | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RV-06 | `uv.lock` locks `mando` 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RV-07 | `uv.lock` locks `radon` 6.0.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2428 |
| RV-08 | The `interrogate` job is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 586 |
| RV-09 | The job name is `Interrogate (docstring coverage)` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 587 |
| RV-10 | The job installs `requirements-dev.txt` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 598 |
| RV-11 | The job runs `interrogate` with `--fail-under` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 600 |
| RV-12 | `INTERROGATE_PATHS` names the four paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RV-13 | `INTERROGATE_THRESHOLD` defaults to 90 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 123 |
| RV-14 | The dependency lock job runs `uv lock --check` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RV-15 | Pins are held so Dependabot raises reviewable pull requests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 433 |
| RV-16 | The pip update stream is defined | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 3 |
| RV-17 | The pip update stream has no ignore rule for `mando` | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 0 |
| RV-18 | The npm stream has an ignore rule with its reason | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| RV-19 | The runtime requirements file pins `mando` | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| RV-20 | The policy snapshot holds the pip stream | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 23 |
| RV-21 | The policy test asserts full snapshot equality | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RV-22 | The policy fixture logs before and after the read | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 277 |
| RV-23 | `python_route` computes the base-5 route | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 33 |
| RV-24 | The route helper uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RV-25 | The numbered route resolves under `specs\numbered` | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| RV-26 | The route folder `specs/numbered/0/0/1/2/4/1/0` exists on `main` | specs/numbered/0/0/1/2/4/1/0 | main | none: path absent | absent | 0 |
| RV-27 | The reference record holds `spec.md` | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RV-28 | The fragment README allows no fragment for an internal change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RV-29 | The fragment README names the issue form of the file | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RV-30 | The quality gates document lists the interrogate job | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 62 |
| RV-31 | The quality gates document has the branch protection section | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 220 |
| RV-32 | The quality gates document states that sibling issues close after a later run | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 161 |
| RV-33 | The copilot instructions document the Docstrings gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 71 |
| RV-34 | The copilot instructions have the Language and environment section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |
| RV-35 | The copilot instructions have the Local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RV-36 | The copilot instructions have the Test quality ratchet section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RV-37 | The copilot instructions set the type and scope label rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 438 |
| RV-38 | The copilot instructions list the four accepted PR title forms | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 507 |
| RV-39 | The copilot instructions name fragments for user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RV-40 | The copilot instructions limit the container build trigger | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RV-41 | AGENTS requires the in-progress claim before a branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| RV-42 | AGENTS names the branch form | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| RV-43 | AGENTS requires a test that can fail | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 136 |
| RV-44 | AGENTS requires a Closes line for the issue in the PR body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RV-45 | AGENTS requires the auto-merge label only after green checks | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RV-46 | AGENTS parallel-agent section starts here | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 242 |
| RV-47 | AGENTS requires a preservation proof before closure | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RV-48 | AGENTS requires a contract test for each workflow value | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 310 |
| RV-49 | The constitution has the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RV-50 | The constitution has the Full Deployment Pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RV-51 | Constitution step 10 waits for the main build | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| RV-52 | Constitution step 11 verifies the image revision | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 168 |
| RV-53 | The constitution has the Inline Comments rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RV-54 | The constitution has the Action Logging rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RV-55 | The constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RV-56 | The constitution has the complexity escalation rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| RV-57 | The Windows timeout budget workflow installs `requirements-dev.txt` | .github/workflows/windows-timeout-budget.yml | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 48 |
| RV-58 | The Windows audit report workflow installs `requirements-dev.txt` | .github/workflows/windows-audit-report.yml | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 48 |
| RV-59 | The export guard compares exports with `uv.lock` | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 1 |
| RV-60 | The container guide has the update procedure | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 222 |
| RV-61 | The container guide has the revision check procedure | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 268 |
| RV-62 | The PR template requires a failing path for each guard | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 12 |
| RV-63 | The Dependabot options reference describes `versions` ranges in the package pattern | content/code-security/reference/supply-chain-security/dependabot-options-reference.md (github/docs) | main | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 420 |
| RV-64 | Local radon 6.0.1 metadata requires `mando` below 0.8 | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local | not applicable: local file | present | 31 |
| RV-65 | Local packaging module cites PEP 440 for the `>=` operator | .venv\Lib\site-packages\packaging\specifiers.py | local | not applicable: local file | present | 84 |
| RV-66 | PyPI lists radon 6.0.1 as the latest release | https://pypi.org/project/radon/ | web | not applicable: HTTP page | present | 1 |
| RV-67 | `requirements-dev.txt` pins `pytest==9.2.0` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 325 |
| RV-68 | `requirements-dev.txt` pins `pyyaml==6.0.4` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| RV-69 | The pip update stream runs weekly | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 6 |

## Sources

- GitHub issue 4901: `gh issue view 4901 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author`. The issue is open. It has labels `bug`, `ci`, and `quality-gate`. It has no comments. Its body names commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` and run `45064243269`.
- Pull requests: `gh pr list --state all --search 4901` returns an empty list. `gh pr view 4888` shows an open pull request. Its base is `main`. Its head branch is `dependabot/pip/mando-0.8.2`. Its head is `e86098cdc2b189d217805b3b4060ef609cbc37af`. It has one commit and one changed file, `requirements-dev.txt`.
- Commit facts: `gh api repos/jmorrison-juniper/MistHelper/commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` returns a merge commit with parents `00d9a16` and `e86098c`. The job log of job 137336719025 reads `HEAD is now at 5bb4b38 Merge e86098cdc2b189d217805b3b4060ef609cbc37af into 00d9a16e998b0cb5e10b6ed77da0fa909670d64f`. The issue commit is therefore the GitHub test-merge commit of PR head `e86098c`.
- Run facts: `gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs` returns 33 jobs. `gh run view 45064243269 --log-failed` returns 20,785 lines. `gh run view 45064243269 --job 137336719025 --log` returns 605 lines.
- Native Windows runs: `gh run view 45064235051 --log-failed` and `gh run view 45064235097 --log-failed` each show the resolver lines.
- Main baseline: `gh api repos/jmorrison-juniper/MistHelper/branches/main` returns head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. `gh run view 45774119357 --job 139753527432 --log` returns the `RESULT: PASSED` line.
- Branch protection: `gh api repos/jmorrison-juniper/MistHelper/branches/main/protection/required_status_checks` returns `strict` set to true and 15 contexts, including `Interrogate (docstring coverage)`.
- Related issues: `gh issue list -R jmorrison-juniper/MistHelper --label quality-gate --state all --limit 500` returns issues #4891 to #4905 with the suffix `(PR #4888)`.
- Remote files: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` returns 11,404 entries, not truncated. Each file row in the verification table reads its blob through the contents API. For example, `gh api repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main --jq .sha` returns the blob SHA.
- Upstream Dependabot reference: `gh api repos/github/docs/contents/content/code-security/reference/supply-chain-security/dependabot-options-reference.md?ref=main`, decoded (RV-63).
- Upstream PyPI: `https://pypi.org/project/radon/` (RV-66). The page title reads `radon 6.0.1`.
- Local files: `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` (RV-64). `.venv\Lib\site-packages\packaging\specifiers.py` (RV-65). `.specify\scripts\powershell\spec-route.ps1` (local copy read for the same lines as RV-24 and RV-25).
- Local documents read: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, the four templates under `.specify\templates`, the reference record under `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, `documentation\quality-gates.md`, `documentation\development-setup.md` (search only), and `documentation\container-deployment.md` (heading search only).
- Skill tool: not used. No Podman or Juniper device behavior is in scope.

## Unverified

- U-1. Dependabot accepts `versions: [">= 0.8"]` for the pip ecosystem. Method: the options reference (RV-63) and PEP 440 (RV-65). Not observable until a weekly run after the merge. Decided at T-MERGE and the next weekly run.
- U-2. The docstring value on the fix head. Method: the same policy-only change leaves every Python module unchanged. The `main` run reports 99.7 percent (job 139753527432). The fix head run decides the value at T-REMOTE-CI.
- U-3. No radon release after 6.0.1 accepts `mando` 0.8. Method: PyPI lists 6.0.1 as the latest release at fetch time (RV-66). Future releases are not observed.
- U-4. The container image content after the merge. Method: the trigger rule (RV-40) and the manual dispatch in D-8. The Dockerfile inputs are not read, so the claim that the image is unchanged is unverified.
- U-5. Issue #4894 maps to job `pytest (coverage gate)`. Method: title match and the failed step list. The sync job code is not read.
- U-6. Sibling issues close after the gate passes. Method: the documented rule (RV-32). No closure is observed before the fix merges.
- U-7. The effect of PR #4208 on the pins. Method: the search result and its title only. Its files were not read.
