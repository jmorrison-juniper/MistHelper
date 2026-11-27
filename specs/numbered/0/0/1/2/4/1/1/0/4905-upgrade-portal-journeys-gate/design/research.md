# Research: Upgrade Portal Journeys Gate on PR 4888

**Issue**: 4905. **Record**: `specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate`. **Evidence date**: 2026-11-26.

## Summary

The journeys gate failed in its install step on PR 4888. No test ran. Pip found no version set that holds `radon==6.0.1` and `mando==0.8.2`. Main passes the same gate. The newest radon release still requires `mando` below 0.8. The fix blocks the mando 0.8 bump, keeps mando at 0.7.1, and closes PR 4888 after authorization.

## Decisions

Each decision names its alternatives, the chosen option, the reason, and the risk. No decision needs a human marker.

### D-1 Keep mando at 0.7.1 on main

- Option A: keep mando at 0.7.1 and block mando 0.8 in Dependabot. Chosen.
- Option B: upgrade radon to a release that accepts mando 0.8. Rejected. No such release exists. The newest release, 6.0.1, requires `mando (<0.8,>=0.6)` (R-64, R-65, R-66).
- Option C: replace radon with another complexity tool. Rejected. The radon command feeds the complexity gate (R-47), so the change exceeds one issue.
- Option D: re-lock with mando 0.8.2 through uv. Rejected. The resolver finds no solution while radon 6.0.1 is pinned (R-62).
- Reason: Option A keeps radon and every gate unchanged.
- Risk: mando stays on the 0.7 line. The package is a dev-only transitive pin (R-06, R-09). Pip-audit reads only `requirements.txt`. Unverified item U-5 covers the 0.8.2 release.

### D-2 Block mando 0.8 and later in the pip update stream

- Option A: add an `ignore` entry with `dependency-name: "mando"` and `versions: [">=0.8"]` to the pip update stream. Chosen.
- Option B: add an `ignore` entry with `update-types: ["version-update:semver-minor"]`. Rejected. The update type names a release level, not the boundary that radon sets. The version range states the same boundary as radon (R-66).
- Option C: take no action. Rejected. Dependabot proposes each newer release that the pip update stream allows. Ignored versions are filtered out only when an entry names them (R-70).
- Option D: disable the pip update stream. Rejected. The repository rule forbids disabling update streams (R-42), and the pip update stream serves every other pip pin.
- Reason: Option A blocks only the versions that radon rejects, and the pip update stream stays active.
- Risk: The pip range form is unverified (U-1). Mitigation: check the first pip update run after the merge.

### D-3 Extend the policy guard

- Option A: add the entry to the policy snapshot and add three test cases. Chosen.
- Option B: change the snapshot only. Rejected. No test then proves that removing or widening the entry fails.
- Option C: change nothing in the guard. Rejected. The policy test compares the whole file with the snapshot (R-15), so the new entry fails CI without a snapshot change.
- Reason: The guard already protects every field of the file. The new field needs the same protection.
- Risk: The snapshot and the file must match exactly. The guard reports each mismatch.

### D-4 Close PR 4888 after the fix merges

- Option A: leave PR 4888 open. Rejected. The PR cannot pass in any form (R-62, analysis A-1 and A-6). An open PR keeps the failing gates visible with no path to green. This option follows the literal text of R-42.
- Option B: push a revert to `dependabot/pip/mando-0.8.2`. Rejected. The PR body states that Dependabot maintains the PR only when nobody alters it (R-61).
- Option C: comment `@dependabot ignore this minor version` on PR 4888. Rejected. Dependabot closes the PR and stores the ignore in its own service state. The repository entry in D-2 keeps the decision visible and reviewable.
- Option D: close PR 4888 after the fix merges, with orchestrator authorization. Chosen.
- Reason: The closure is reversible, and the branch survives. The preservation rule (R-49) is met by the surviving remote branch and its commit.
- Risk: R-42 says `Do not close update pull requests`. This record reads that rule inside its section, `Pull request titles` (R-41). The rule concerns title failures. Authorization is required before closure (U-2). Caution: `gh pr reopen 4888` reverses the closure.

### D-5 Add one changelog fragment

- Option A: add no fragment. Rejected. The internal-only rule in the fragment README (R-36) yields to the constitution. The constitution requires one fragment for each change (R-38) and supersedes other practice documents (R-39).
- Option B: add `changelog.d/issue-4905-upgrade-portal-journeys-gate.md` with one `Changed` bullet. Chosen.
- Reason: The constitution is authoritative for MistHelper rules, so the fragment is required.
- Risk: A reviewer may see the fragment as low value. The bullet names issue 4905 and states the Dependabot change.

### D-6 Commit the record and the fix in one pull request

- Option A: one pull request holds the record and the fix. Chosen.
- Option B: one pull request for the record, then one for the fix. Rejected. The rule `One pull request holds one change` (R-48) groups both under one concern, and the record documents that change.
- Reason: Reviewers read the decision next to the diff.
- Risk: The diff holds several Markdown files. The STE gate reads each file (R-50).

## Evidence

### E-1 Failing check, job, step, and rule

- The issue body names the gate, PR 4888, branch `dependabot/pip/mando-0.8.2`, commit `5bb4b385`, and run 45064243269. It asks the reader to review the run. The issue has no comments (R-71).
- The check `Upgrade portal journeys` belongs to workflow `Quality Gates` (R-17). Its job key is `upgrade_portal_journeys` (R-19).
- Run 45064243269 and job 137339161249 concluded failure. Step 4, `Install dependencies`, failed. Steps 5 and 6 were skipped. Step 7, `Upload upgrade portal journey evidence`, failed (R-62).
- The job log shows the pip error at 2026-11-22T20:15:36Z. Pip reports `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`. Then it reports `radon 6.0.1 depends on mando<0.8 and >=0.6`, and `ResolutionImpossible`. The job exits with code 1.
- The failing rule is pip dependency resolution. No test assertion failed. The harness command (R-21) did not start.
- The upload step reports `No files were found with the provided path: test-artifacts/upgrade-portal-journeys/`. The harness creates that folder only after it starts (R-34). The upload failure follows from the install failure.

### E-2 Scope on the same head

- Run 45064243269 has 28 failed jobs. Twenty-six job logs contain `ResolutionImpossible`. Two jobs fail as aggregators. Job `pytest (coverage gate)` reports `The dependency lock job finished with failure` (R-18). Job `E2E smoke tests` reports `The E2E shards finished with failure`.
- Runs 45064235051 (`Native Windows timeout budget`) and 45064235097 (`Windows audit report`) fail with the same `ResolutionImpossible` text on head `e86098c`.
- Sibling gate issues 4891 to 4904 come from PR 4888 (R-72). Their titles name gates whose jobs failed in the same run. Issue 4894 names the `pytest` gate. That gate is the aggregator in R-18.

### E-3 Commit identity

- The issue cites commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`. GitHub created this merge commit for the pull request. Its parents are base commit `00d9a16e998b0cb5e10b6ed77da0fa909670d64f` and PR head `e86098cdc2b189d217805b3b4060ef609cbc37af` (R-59).
- The run and the failed job report head SHA `e86098cdc2b189d217805b3b4060ef609cbc37af` (R-62). Its message is `chore: bump mando from 0.7.1 to 0.8.2` (R-58).
- The remote branch `dependabot/pip/mando-0.8.2` points to `e86098c` (R-60).
- The record names both SHAs. The PR head is the commit that Dependabot created.

### E-4 Main passes the same gate

- Run 45774119357 on main head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` concluded success for 33 jobs. Job 139759629406, `Upgrade portal journeys`, is one of them (R-63).
- On main, the install step resolves with mando 0.7.1 (R-01, R-02).

### E-5 Dependency chain

- `requirements-dev.txt` is generated by `uv export --locked` (R-03). Line 179 pins mando 0.7.1 on main (R-01). Line 365 pins radon 6.0.1 (R-02).
- `pyproject.toml` line 118 pins radon 6.0.1 in the dev extra (R-07). `uv.lock` records mando 0.7.1 (R-08) and records radon as a dependent of mando (R-09).
- PR head line 179 changes to mando 0.8.2 (R-04). Line 365 stays at radon 6.0.1 (R-05). The PR changes only `requirements-dev.txt` (R-90). It changes no lock file and no `pyproject.toml`.
- The installed radon metadata, line 31, states `Requires-Dist: mando (<0.8,>=0.6)` (R-66). PyPI lists the same requirement (R-64).

### E-6 Gate code that reads the same files

- The `dependency_lock` job installs `requirements-dev.txt` (R-24), checks the lock (R-25), and runs the export guard (R-26).
- The export guard runs `uv export --locked` (R-31). Its test fails when a checked-in export differs from the lock output (R-32).
- Consequence: an edit to `requirements-dev.txt` without a lock change fails the export guard, even when pip resolves. Analysis item A-6 records this.

### E-7 Journeys guard test

- `tests/guardrails/test_upgrade_portal_journey_ci.py` checks the job name, the needs, the bounds, the command, the artifact, and the issue sync (R-27, R-29). It reads the workflow text and does not run pip. It cannot detect a resolver failure (analysis item A-7).
- It forbids a service container for the job (R-30). The job keeps its simulated cloud boundary.

### E-8 Policy guard for Dependabot

- `POLICY_SNAPSHOTS["dependabot"]` starts at line 20 (R-12). The npm ignore sits at line 51 (R-13). `TestDependabotPolicy` starts at line 271 (R-14).
- The whole-policy equality assertion sits at line 295 (R-15). The mutation list holds the npm ignore removal at line 317 (R-16).

### E-9 Changelog and constitution

- The constitution requires one fragment for each change (R-38). It states that it supersedes other practice documents (R-39).
- The fragment README names the issue form (R-35). Its rule 4 allows no fragment for an internal-only change (R-36). The fragment guard accepts the issue form (R-37).
- The instruction file says that a user-visible change adds one fragment (R-40).

### E-10 Closure and preservation

- The instruction file states `Do not close update pull requests or disable update streams.` (R-42). The sentence sits under `Pull request titles` (R-41).
- AGENTS requires one preservation proof in the closing comment. The surviving remote branch and its commit count as proof (R-49).
- The PR 4888 body states that Dependabot resolves conflicts unless someone alters the PR (R-61).

### E-11 Record route for 4905

- `spec-route.ps1` uses base 5 and eight digits (R-51). Its numeric branch resolves through `Resolve-SpecFeaturePath` (R-52).
- 4905 equals 1 x 5^5 + 2 x 5^4 + 4 x 5^3 + 1 x 5^2 + 1 x 5^1.
- The eight base-5 digits are 0, 0, 1, 2, 4, 1, 1, 0. These digits match the ROUTE value.
- The reference record 4920 follows the same rule. Its digits are 0, 0, 1, 2, 4, 1, 4, 0 (R-55).
- No folder for 4905 and no route leaf for 4905 exist on main (R-56, R-57). A local search of `specs\` for folders that start with `4905-` found none. The record therefore has no legacy record to verify or reuse.

### E-12 Applicability of other sources

- Skills: none loaded. The issue has no Podman question and no Juniper device question.
- Mist API OpenAPI file and the mistapi SDK: not applicable. The journeys harness uses a simulated cloud boundary (R-30). This change makes no Mist API call.
- `documentation/development-setup.md` line 137 installs both requirement files in one command (R-74). The same resolver error appears in that command for the PR head. Quickstart uses this command as the optional local reproduction.
- `documentation/quality-gates.md` has no row for the journeys gate (R-75). That gap predates this issue (analysis item A-9). This record does not change that file.
- `documentation/architecture.md` line 167 describes `requirements-dev.txt` as development tools (R-76). No change is needed.
- `documentation/container-deployment.md` and `documentation/operator-guide.md`: not applicable. The journeys gate runs on a GitHub-hosted runner, and this change starts no container. This change changes no operator-visible output.

## Remote verification table

Rows R-64 and R-65 check PyPI. Row R-66 checks installed package metadata in the local `.venv`. Rows R-67 to R-70 check GitHub source files that the upstream projects publish. Rows R-77 to R-90 check the local gates table, the gate path lists, the test dependency, and the pull request files. Count: 90 rows.

| ID | Claim | Source (path or URL) | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main pins mando 0.7.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| R-02 | Main pins radon 6.0.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| R-03 | The file header says `uv export` generates it | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 1 |
| R-04 | PR head sets mando 0.8.2 | requirements-dev.txt | dependabot/pip/mando-0.8.2 | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| R-05 | PR head keeps radon 6.0.1 | requirements-dev.txt | dependabot/pip/mando-0.8.2 | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| R-06 | requirements.txt has no mando pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| R-07 | pyproject.toml pins radon 6.0.1 in the dev extra | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| R-08 | uv.lock records mando 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| R-09 | uv.lock records radon as a dependent of mando | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| R-10 | The pip update stream has no ignore list | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| R-11 | The npm update stream ignores typescript major updates | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 80 |
| R-12 | The policy snapshot holds the Dependabot mapping | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 20 |
| R-13 | The policy snapshot holds only the npm ignore | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 51 |
| R-14 | The class `TestDependabotPolicy` starts | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 271 |
| R-15 | The policy test compares the whole file with the snapshot | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| R-16 | The mutation list removes the npm ignore | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 317 |
| R-17 | The CI workflow name is `Quality Gates` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| R-18 | The pytest coverage gate job key and name | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 330 |
| R-19 | The journeys gate key and display name | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 972 |
| R-20 | The journeys gate installs requirements-dev.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 991 |
| R-21 | The journeys gate runs the harness with one worker | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 995 |
| R-22 | The journeys gate uploads the evidence folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1001 |
| R-23 | The issue sync job waits for the journeys gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1312 |
| R-24 | The dependency lock job installs requirements-dev.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 646 |
| R-25 | The dependency lock job checks the lock | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| R-26 | The dependency lock job runs the export guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| R-27 | The journeys guard fixes the job key and the command | tests/guardrails/test_upgrade_portal_journey_ci.py | main | ef3209d59b78f4897de21521245d9a3e86c1d553 | present | 16 |
| R-28 | The journeys guard names the install command strings | tests/guardrails/test_upgrade_portal_journey_ci.py | main | ef3209d59b78f4897de21521245d9a3e86c1d553 | present | 46 |
| R-29 | The journeys guard requires 15 checked rules | tests/guardrails/test_upgrade_portal_journey_ci.py | main | ef3209d59b78f4897de21521245d9a3e86c1d553 | present | 105 |
| R-30 | The journeys guard forbids service containers for the job | tests/guardrails/test_upgrade_portal_journey_ci.py | main | ef3209d59b78f4897de21521245d9a3e86c1d553 | present | 37 |
| R-31 | The export guard runs `uv export --locked` | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 55 |
| R-32 | The export guard test asserts export parity | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| R-33 | The evidence folder path is set | tests/e2e/upgrade_portal/journeys/evidence.py | main | 2cd8a1ea0422b823b75ccba8cec270f1441dd769 | present | 27 |
| R-34 | The harness creates the evidence folder when it starts | tests/e2e/upgrade_portal/journeys/run_journeys.py | main | 3d94625e383afa5423a34042a1d4707aee35fc04 | present | 193 |
| R-35 | The fragment README names the issue form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R-36 | The fragment README rule 4 allows no fragment for internal changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-37 | The fragment guard accepts the issue form | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-38 | The constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-39 | The constitution supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| R-40 | The instruction file says a user-visible change adds one fragment | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-41 | The instruction file has the heading `Pull request titles` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| R-42 | The instruction file forbids closing update pull requests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| R-43 | The local gates table has the Tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-44 | The local gates table has the Full tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 62 |
| R-45 | The local gates list has the guardrails pytest-chunks command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 88 |
| R-46 | The local gates table has the STE row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-47 | The local gates table has the Complexity row that uses radon | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 66 |
| R-48 | AGENTS states that one pull request holds one change | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 223 |
| R-49 | AGENTS requires a preservation proof before closing an unmerged pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| R-50 | AGENTS requires each Markdown file to pass the STE gate | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R-51 | The route script uses base 5 with width 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R-52 | The route script defines `Resolve-SpecFeaturePath` | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-53 | The route contract test file exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 45 |
| R-54 | The pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| R-55 | The reference record 4920 exists at its route | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-56 | No record folder for 4905 exists on main | specs/ (any path that contains 4905) | main | not applicable | absent | 0 |
| R-57 | The route leaf for 4905 does not exist on main | specs/numbered/0/0/1/2/4/1/1/ | main | not applicable | absent | 0 |
| R-58 | PR head commit `e86098c` exists | commit e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| R-59 | Merge commit `5bb4b385` exists with the base and head parents | commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | present | 0 |
| R-60 | PR 4888 is open on head `e86098c` | pull request 4888 | dependabot/pip/mando-0.8.2 | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| R-61 | PR 4888 body says Dependabot maintains the PR unless altered | pull request 4888 | dependabot/pip/mando-0.8.2 | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| R-62 | Step 4, `Install dependencies`, failed in job 137339161249 | job 137339161249 of run 45064243269 | e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 4 |
| R-63 | Main job 139759629406 concluded success | job 139759629406 of run 45774119357 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-64 | PyPI lists radon 6.0.1 with `mando (<0.8,>=0.6)` | https://pypi.org/pypi/radon/json (field `info.requires_dist`) | not applicable | not applicable | present | 0 |
| R-65 | PyPI lists radon 6.0.1 as the newest release | https://pypi.org/pypi/radon/json (field `info.version`) | not applicable | not applicable | present | 0 |
| R-66 | Installed radon 6.0.1 metadata requires mando below 0.8 | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | not applicable | not applicable | present | 31 |
| R-67 | The dependabot-core spec uses a version requirement in an ignore condition | https://github.com/dependabot/dependabot-core/blob/04b22f427c0342b5751350812f8a80c498ee0b9b/updater/spec/dependabot/updater_spec.rb | 04b22f427c0342b5751350812f8a80c498ee0b9b | 602d90a81284006d04918c61799fdf88d8f13aad | present | 415 |
| R-68 | The GitHub docs say a range uses the package manager pattern | https://github.com/github/docs/blob/df6faa250dc425fa137d270c967e6a74f12103a7/content/code-security/reference/supply-chain-security/dependabot-options-reference.md | df6faa250dc425fa137d270c967e6a74f12103a7 | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 420 |
| R-69 | The GitHub docs give no pip example for `versions` | https://github.com/github/docs/blob/df6faa250dc425fa137d270c967e6a74f12103a7/content/code-security/reference/supply-chain-security/dependabot-options-reference.md | df6faa250dc425fa137d270c967e6a74f12103a7 | 7a170f73f940ed043c828c028ba705b8f5c72847 | absent | 0 |
| R-70 | The GitHub docs say ignored versions are filtered out | https://github.com/github/docs/blob/df6faa250dc425fa137d270c967e6a74f12103a7/content/code-security/reference/supply-chain-security/dependabot-options-reference.md | df6faa250dc425fa137d270c967e6a74f12103a7 | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 399 |
| R-71 | Issue 4905 is open with labels bug, ci, and quality-gate | GitHub issue 4905 | main | not applicable | present | 0 |
| R-72 | Sibling issues 4891 to 4904 are open gate issues from PR 4888 | GitHub issues 4891 to 4904 | main | not applicable | present | 0 |
| R-73 | Only PR 4888 changes mando or radon among the open PRs | GitHub open pull requests | main | not applicable | present | 0 |
| R-74 | The development setup guide installs both requirement files in one command | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |
| R-75 | The quality gates guide has no row for the journeys gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | absent | 0 |
| R-76 | The architecture guide describes requirements-dev.txt as development tools | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 167 |
| R-77 | The local gates table has the Lint row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| R-78 | The local gates table has the Format row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| R-79 | The mypy path list names no test folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-80 | The local gates table has the Test quality row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| R-81 | The local gates table has the Security lint row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| R-82 | The CI bandit job scans the whole repository | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R-83 | The local gates table has the Dependency audit row for requirements.txt only | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 68 |
| R-84 | The local gates table has the Symbols row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-85 | The radon path list names no guardrail test folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R-86 | The vulture path list names no guardrail test folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-87 | The pydocstyle path list names no test folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-88 | The interrogate path list names no test folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-89 | The pinned `packaging` library is available for the new behavior test | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 228 |
| R-90 | PR 4888 changes only requirements-dev.txt | pull request 4888 files | dependabot/pip/mando-0.8.2 | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |

## Sources

Local repository files, read at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (the main head). Each cited claim has a row in the remote table:
- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (shape only, no content copied)
- `documentation/development-setup.md`, `documentation/quality-gates.md`, `documentation/architecture.md`
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` (installed package metadata, local only)

Upstream sources, fetched on 2026-11-26:
- https://pypi.org/pypi/radon/json, fetched with `web_fetch`. Fields `info.version` and `info.requires_dist`.
- https://github.com/github/docs/blob/df6faa250dc425fa137d270c967e6a74f12103a7/content/code-security/reference/supply-chain-security/dependabot-options-reference.md, fetched with the GitHub contents API at ref `df6faa250dc425fa137d270c967e6a74f12103a7`, lines 387 to 430.
- https://github.com/dependabot/dependabot-core/blob/04b22f427c0342b5751350812f8a80c498ee0b9b/updater/spec/dependabot/updater_spec.rb, fetched with the GitHub contents API at ref `04b22f427c0342b5751350812f8a80c498ee0b9b`, lines 394 to 428.

Skills: none loaded. The issue has no Podman question and no Juniper device question.

## Unverified

- U-1: Dependabot accepts `versions: [">=0.8"]` in a pip ignore entry. Reason: the GitHub docs give no pip example (R-69). The dependabot-core evidence uses `>= 1` in another ecosystem test (R-67). Check: the first pip update run after the merge.
- U-2: The orchestrator authorizes closing PR 4888. Reason: this is an orchestrator decision, outside research. Check: T-MERGE.
- U-3: The journeys gate and the other failed gates pass on the fix pull request. Reason: no gate ran during research. Check: T-REMOTE-CI.
- U-4: `uv lock --check` passes on the fix branch. Reason: no command ran during research. The fix changes no lock file. Check: the dependency lock job in T-REMOTE-CI (R-25).
- U-5: The mando 0.8.2 release notes and security advisories. Reason: not reviewed. The package is dev-only and absent from `requirements.txt` (R-06).
