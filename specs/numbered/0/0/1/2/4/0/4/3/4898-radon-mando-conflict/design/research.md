# Research: Radon Job Mando Pin Conflict

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human.

### D-1: Close PR #4888 without a merge. Keep mando 0.7.1 on main.

- **Alternatives considered**: (a) Keep the bump and upgrade radon. (b) Keep the bump and replace radon with another complexity tool. (c) Keep the bump and relax the pip resolution, for example with a legacy resolver or `--no-deps`. (d) Close the pull request and keep the pin at 0.7.1.
- **Chosen**: (d).
- **Reason**: PyPI lists radon 6.0.1 as the latest release, and it requires mando below 0.8 (R-51). Option (a) therefore has no release to use. Option (b) changes the complexity tool contract and the local gates table (R-39, R-40). Option (c) hides a real conflict and breaks the reproducible lock. Main already holds mando 0.7.1 (R-09, R-16) and passes the radon job (R-08).
- **Risk**: Dependabot raises the bump again. D-2 reduces that risk.

### D-2: Add a pip ignore rule for mando at `>=0.8.0`.

- **Alternatives considered**: (a) No rule. (b) Disable the pip ecosystem. (c) Use `update-types`. (d) Use `versions: [">=0.8.0"]`.
- **Chosen**: (d).
- **Reason**: Without a rule, each weekly run raises the same failing proposal (R-18). Disabling the pip ecosystem also stops every other pip update. The `update-types` key names semantic levels, but the radon limit is a version range (R-51). The `versions` key takes a range, and the github/docs source documents the `>=` form (R-53). The Dependabot config reader parses the key (R-54).
- **Risk**: The rule also blocks a later mando 0.8 security fix. The spec edge cases name that case, and a maintainer reviews it by hand.

### D-3: Put the four tests in the existing guard file.

- **Alternatives considered**: (a) A new file in `tests/guardrails`. (b) A new subfolder under `tests/guardrails`. (c) A new file in another test folder. (d) Extend `tests/guardrails/test_dependency_lock_file.py`.
- **Chosen**: (d).
- **Reason**: The folder `tests/guardrails` holds 79 direct children (R-23). Principle I forbids a new direct child in a noncompliant parent (R-28), so options (a) and (b) fail. Option (c) splits the dependency guards across two places. The chosen file already reads the requirements files and the lock (R-20).
- **Risk**: The module covers a second subject. The docstring gets one sentence that names it.

### D-4: Keep the radon command and the complexity rule unchanged.

- **Alternatives considered**: (a) Raise the limit above 10. (b) Remove the install-before-gate order. (c) Keep both.
- **Chosen**: (c).
- **Reason**: A higher limit weakens the gate (R-40). The guard test requires the install before the gate (R-22). The conflict is an install problem, and the complexity result is not in doubt.
- **Risk**: None for this change. FR-009 keeps the rule fixed.

### D-5: Change no requirements or lock file.

- **Alternatives considered**: (a) Regenerate `uv.lock` for the current pins. (b) Add an explicit `mando<0.8` line to `requirements-dev.txt`.
- **Chosen**: No change.
- **Reason**: Main already holds consistent pins (R-09, R-10, R-16, R-17). Option (b) adds a second source of the same constraint, and the ignore rule already covers the risk.
- **Risk**: A future maintainer edits a pin by hand. The radon pin test catches that edit.

### D-6: Add one changelog fragment, which overrides the internal-only exemption.

- **Alternatives considered**: (a) Skip the fragment and state the reason in the PR body, as the changelog README allows (R-34). (b) Add one fragment, as the constitution requires (R-29).
- **Chosen**: (b).
- **Reason**: The constitution sets a stricter rule for this repository. The AGENTS rules allow the repository file to make a rule stricter (`AGENTS.md`, How the two files fit together). The fragment names the effect for the operator: the radon job installs again.
- **Risk**: A release note for an internal fix. The bullet stays short and plain. Orchestrator action: align the README and the constitution (`analysis.md`, A-06).

### D-7: Deliver one PR on `fix/4898-radon-mando-conflict` with labels bug, ci, tests, and in-progress.

- **Alternatives considered**: (a) Two PRs, one for the rule and one for the tests. (b) A `chore/` branch name.
- **Chosen**: One PR on the `fix/` branch name.
- **Reason**: The rule and the tests protect one decision. Two PRs need two full pipeline runs. The `fix` type matches the failure (R-31). The constitution requires a type label and a scope label, and a status label while work runs (R-32). The status label goes on the issue before the branch exists (R-35).
- **Risk**: None known.

### D-8: Close sibling issues #4891 through #4905 only when the orchestrator authorizes it.

- **Alternatives considered**: (a) Close them now. (b) Leave them open. (c) Close them after PR #4888 closes, with orchestrator approval.
- **Chosen**: (c).
- **Reason**: PR #4888 stays open until T-MERGE. The sibling issues describe its state. Closing them early hides an open failure. Leaving them open leaves stale issues for the next operator.
- **Risk**: The sibling issues stay open for a short period.

## Remote Verification

Ref `main` means commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. That commit is the main head at verification time (R-08 run headSha). Blob or tree SHAs are full 40-character values. `none` means the path is absent. `n/a` marks a source that is not a Git blob.

| # | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Radon job key and display name `Radon (complexity)` on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 531 |
| R-02 | Radon job install step runs `pip install -r requirements-dev.txt` on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 543 |
| R-03 | Radon job complexity command pipes radon output to `complexity-gate --max 10` on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 549 |
| R-04 | The tested merge commit holds the same `ci.yml` blob | .github/workflows/ci.yml | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 543 |
| R-05 | Job 137336719006 failed at the install step in run 45064243269 | .github/workflows/ci.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 543 |
| R-06 | Job 137336719006 log shows `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2` and `radon 6.0.1 depends on mando<0.8 and >=0.6` | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| R-07 | Logs of jobs 137338084785, 137338442288, and 137336719241 show the same resolution conflict | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| R-08 | Run 45774119357 on main: job 139753527500 succeeded, with the complexity step | .github/workflows/ci.yml | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 549 |
| R-09 | Main pins `mando==0.7.1`, with the comment `# via radon` on line 180 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| R-10 | Main pins `radon==6.0.1`, with the comment `# via misthelper` on line 366 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| R-11 | PR #4888 head pins `mando==0.8.2`, and PR #4888 changes only this file | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| R-12 | The merge commit tested by run 45064243269 holds `mando==0.8.2` | requirements-dev.txt | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| R-13 | Commit 5bb4b385 exists, with parents 00d9a16e and e86098cd | commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | tree 38314c25a56caeeaf0ce01777caa00014bd7cb32 | present | 0 |
| R-14 | The dev extra of pyproject.toml pins `radon==6.0.1` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| R-15 | `requirements.txt` holds no mando or radon pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| R-16 | `uv.lock` locks mando at version 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| R-17 | `uv.lock` locks radon at version 6.0.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2428 |
| R-18 | The pip entry of Dependabot has a weekly schedule and no ignore rule | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| R-19 | The npm entry of Dependabot uses an `ignore` block with dependency-name and update-types | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| R-20 | `test_lock_satisfies_every_requirement` reads the requirements files and compares them with `uv.lock` | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| R-21 | `DeclarationParity.is_direct` accepts only `misthelper` annotations | tests/guardrails/test_dependency_declaration_parity.py | main | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 55 |
| R-22 | The radon job contract test requires the install command before the gate | tests/guardrails/test_complexity_gate_limit.py | main | 7e15fc70d292e52c134841f3c17aa3e7135a3749 | present | 102 |
| R-23 | The folder `tests/guardrails` holds 79 direct children | tests/guardrails | main | n/a (directory) | present | 0 |
| R-24 | The planned changelog fragment path is absent on main | changelog.d/issue-4898-radon-mando-conflict.md | main | none | absent | 0 |
| R-25 | No path under `specs` contains 4898 on main | specs | main | none | absent | 0 |
| R-26 | The route folder `specs/numbered/0/0/1/2/4/0/4/3` holds no child on main | specs/numbered/0/0/1/2/4/0/4/3 | main | none | absent | 0 |
| R-27 | `spec-route.ps1` sets base 5 and joins the numbered route | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-28 | Constitution Principle I, the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-29 | Constitution Documentation section: each change MUST add one unique fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-30 | Constitution escalation applies to changes that touch three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 431 |
| R-31 | Constitution branch pattern `fix/<issue-number>-<slug>` | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 479 |
| R-32 | Constitution: each issue and PR MUST have type, scope, and status labels | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 489 |
| R-33 | Constitution: the auto-merge label is added only after all checks pass | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 524 |
| R-34 | The changelog README exempts internal-only changes from a fragment | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-35 | AGENTS.md: claim the issue with the `in-progress` label before the branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| R-36 | AGENTS.md: the PR body writes `Closes #<issue>` | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R-37 | AGENTS.md: a preservation proof is recorded before an unmerged PR closes | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| R-38 | AGENTS.md: Dependabot keeps the dependencies current | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 316 |
| R-39 | The Local gates table in copilot-instructions lists the Lint row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| R-40 | The radon row of quality-gates maps to `complexity-gate --max 10` | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 59 |
| R-41 | The spec template has the section User Scenarios and Testing | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 11 |
| R-42 | The plan template has the section Constitution Check | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 44 |
| R-43 | The tasks template has the Format line | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| R-44 | The checklist template has a title line with the checklist type | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R-45 | Reference record 4920 spec.md uses the User Scenarios and Testing heading | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 26 |
| R-46 | Reference record 4920 plan.md uses the Constitution Check heading | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 37 |
| R-47 | Reference record 4920 tasks.md uses phase headings | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 19 |
| R-48 | `requirements-dev.txt` pins `packaging==26.3` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 228 |
| R-49 | `requirements-dev.txt` pins `pyyaml==6.0.4` | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| R-50 | `pyproject.toml` sets `requires-python` to `>=3.15` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-51 | PyPI lists radon 6.0.1 as the latest release, and it requires `mando (<0.8,>=0.6)` | https://pypi.org/pypi/radon/json | PyPI JSON (info.version 6.0.1) | n/a (JSON API) | present | 0 |
| R-52 | Local radon 6.0.1 metadata lists `Requires-Dist: mando (<0.8,>=0.6)` | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local .venv (read-only) | n/a (local file) | present | 31 |
| R-53 | github/docs at commit df6faa25 shows `versions: [ ">=1.0.0" ]` in its ignore examples | content/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/controlling-dependencies-updated.md | df6faa250dc425fa137d270c967e6a74f12103a7 | a346a21d13fb8fa9390e6a097a1d73c383a1edb0 | present | 97 |
| R-54 | dependabot-core at commit 04b22f42 parses the `versions` key of each ignore condition | common/lib/dependabot/config/file.rb | 04b22f427c0342b5751350812f8a80c498ee0b9b | 4395c50a1d308fa194968f65cc16ac23e4716377 | present | 112 |
| R-55 | The folder `changelog.d` holds 335 direct children | changelog.d | main | n/a (directory) | present | 0 |

Count: 55 rows. The STATUS file `remote_checks` array and `summary.md` repeat this count.

## Sources

### Remote GitHub reads (read-only GET requests)

- Issue #4898: `gh issue view 4898 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments`. Facts: title, body, labels bug, ci, and quality-gate, state OPEN, no comments.
- PR #4888: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json files,body,state,mergedAt,headRefName,statusCheckRollup`. Facts: head `e86098cd`, base `main`, one changed file.
- PRs that reference 4898: `gh pr list --search "4898"` returned an empty list.
- Run 45064243269 (Quality Gates, event pull_request): job list, job steps, and failed-step logs for jobs 137336719006, 137338084785, 137338442288, and 137336719241.
- Run 45774119357 (Quality Gates on main): job list with the Radon job.
- Git trees: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree holds 11404 entries and no truncation.
- Blobs: `gh api repos/jmorrison-juniper/MistHelper/git/blobs/9a528bfe03a10f7bc903f5768ef26de765bbff43`, one blob SHA for each file.
- Contents: `gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main"`, one path and ref for each file.
- Commit 5bb4b385: `gh api repos/jmorrison-juniper/MistHelper/commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`.
- Closed issues #4690 and #4655 (`gh issue view`). Issue #4690 holds the earlier install conflict.
- Quality gate issues: `gh issue list --label quality-gate`, read-only.

### Local files (read-only, no execution)

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `changelog.d/README.md` were read in full or in ranges.
- `.specify/templates/*.md` and `.specify/scripts/powershell/spec-route.ps1` were read. The script was not run.
- `documentation/quality-gates.md` was read for the radon row.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` was read for the radon requirement (R-52).

### Upstream URLs

- https://pypi.org/pypi/radon/json was fetched with `web_fetch` in two parts. The JSON holds the `info` block with `version` 6.0.1 and `requires_dist` with `mando (<0.8,>=0.6)`.
- https://github.com/github/docs/blob/df6faa250dc425fa137d270c967e6a74f12103a7/content/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/controlling-dependencies-updated.md was read through `gh api "repos/github/docs/contents/content/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/controlling-dependencies-updated.md?ref=df6faa250dc425fa137d270c967e6a74f12103a7"`. Lines 91 to 98 hold the `>=1.0.0` example.
- https://github.com/dependabot/dependabot-core/blob/04b22f427c0342b5751350812f8a80c498ee0b9b/common/lib/dependabot/config/file.rb was read through `gh api` at the same commit. Lines 107 to 116 hold `ignore_conditions`.
- The `semantic_code_search` tool located the two upstream paths. The claims cite the fetched content, not the search snippets.

### Local-only evidence (not counted in the remote table)

- The shared checkout is at `main`, commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (`git rev-parse`).
- `git status --porcelain` lists five modified files outside this change: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`. This record cites none of them.

## Skills and Out-of-Scope Sources

- No skill was loaded. The issue concerns Python dependency resolution and a GitHub Actions workflow. The brief names Podman and Juniper skill categories, and neither applies.
- Mist API: not applicable. The issue names no Mist endpoint, and the OpenAPI file does not affect the radon job.
- SDK (`mistapi`): not applicable. The issue names no `mistapi` function.

## Unverified

- U-01: The live Dependabot documentation page at docs.github.com could not be fetched. `web_fetch` refused the address. The github/docs source at commit df6faa25 replaces it (R-53). The source may differ from the live page.
- U-02: The github/docs excerpt does not state whether an ignore rule applies to security updates. The record treats that case as a review item (spec edge cases).
- U-03: The CI result for the fix branch is a future event. T-REMOTE-CI records it.
- U-04: The pip install with the fix branch did not run in this phase. The brief forbids installs in this phase. T-LOCAL-GATES runs the install in the fix worktree.
- U-05: The complexity result on the PR #4888 head is unknown. Run 45064243269 skipped the complexity step. Main passes (R-08).
- U-06: The resolver error text was read in four logs (R-06, R-07). The step names show install failures in 26 of 28 failed jobs. The other 22 logs were not read.
- U-07: The native Windows checks on PR #4888 come from other workflows. They were not examined.
- U-08: PRs #4886, #4889, and #4890 and their issues #4906 through #4908 were not examined.
- U-09: The effect of the ignore rule on the next weekly Dependabot run is a future event (SC-004).
