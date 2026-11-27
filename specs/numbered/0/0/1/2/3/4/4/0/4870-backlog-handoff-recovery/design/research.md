# Research: Backlog Handoff Recovery

## Scope

This research checks each claim that the handoff for issue 4870 names. It also checks each claim that this record depends on. GitHub main is the truth order. The local checkout HEAD equals main (R-77), and each cited local file equals its main blob (R-78). The checks ran on 2026-11-26 at about 18:57 UTC.

## Linked work

The search for PRs that name 4870 returned two PRs. PR 4874 is linked. It is merged as 1982b7e84, it closes issue 4869, and its files include the route sibling record for issue 4869 (R-06, R-38). PR 2323 is an unrelated dependency PR. Its body links to issue 4870 of the HypothesisWorks/hypothesis repository, which is a different repository, so the record does not link it.

## Existing record check

The search found no folder that starts with `4870-`. The local `specs` tree has no such folder (TST-18). The remote tree of main has no path that contains `4870` (R-32). The record starts without a legacy record, so no reuse check is needed.

## Method notes

- The `git/trees/main` response has a `sha` field that carries the commit SHA of main. The root tree of that commit is `5f0c0ace8fbec6b46555f16d0b32b9d28907adf2`.
- Issue and PR list queries use a limit of 5000 for all states. The open issue query uses a limit of 1000.
- Contents calls decode the base64 text in PowerShell. Line numbers start at 1.
- One row records one claim. A row with several paths lists them in path order.
- A line value of 0 means that the claim has no file line.

## Remote verification table

The table has 79 rows. The STATUS file lists the same 79 checks.

| ID | Claim | Path or object | Ref | Blob or SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main head commit is f03c6c9b3 | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-02 | Main holds 2535 commits, eight ahead of 1982b7e84 | compare endpoint, base 1982b7e84 and head main | main | 1982b7e8412160f81cb19e8113d784a65b7853b9 | present | 0 |
| R-03 | The workflow name is Quality Gates | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| R-04 | Quality Gates run 45774119357 completed with success on head f03c6c9b3 | gh run list, workflow Quality Gates, branch main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-05 | PR 4884 merged as 00d9a16e9 from head 8d17e27e4 and closes issue 4883 | pulls/4884 | main | 00d9a16e998b0cb5e10b6ed77da0fa909670d64f | present | 0 |
| R-06 | PR 4874 merged as 1982b7e84 from head 94df2b015 and closes issue 4869 | pulls/4874 | main | 1982b7e8412160f81cb19e8113d784a65b7853b9 | present | 0 |
| R-07 | Issues 4883 and 4869 are CLOSED | issues/4883 and issues/4869 | main | n/a | present | 0 |
| R-08 | Issue 4762 is OPEN after its reopening, but handoff section 10 says CLOSED | issues/4762 | main | n/a | stale | 0 |
| R-09 | Issue 4867 is CLOSED by PR 4871, but the inventory lists it as open | issues/4867 | main | n/a | stale | 0 |
| R-10 | 166 issues are OPEN, and 40 open issues are not in the inventory | issues with state open | main | n/a | stale | 0 |
| R-11 | The 127 inventory rows match GitHub titles and label sets, and 126 rows are OPEN | issues with state all, comment 0 | main | n/a | partial | 0 |
| R-12 | Seven PRs are OPEN: 4886, 4887, 4888, 4889, 4890, 4813, and 4208 | pulls with state open | main | n/a | stale | 0 |
| R-13 | PR 4813 is an OPEN draft, BEHIND, and closes issue 4776 | pulls/4813 | main | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | present | 0 |
| R-14 | PR 4208 is an OPEN draft, DIRTY, and closes issue 4200 | pulls/4208 | main | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| R-15 | PR 4806 merged as 05cafda76 at 2026-11-21 18:54:40 UTC | pulls/4806 | main | 05cafda7670aec41e5952abe5c3866b7e8026bfb | present | 0 |
| R-16 | The 31 merge commits in handoff sections 7 and 8 match their rows | pulls/number for 31 rows | main | n/a | present | 0 |
| R-17 | Ten other claimed states match. CLOSED: 3726, 4536, 4584, 4737, 3699, 4838, 4858, and 4714. OPEN: 4759 and 4774. | issues/number | main | n/a | present | 0 |
| R-18 | Issues 4837, 4863, 4868, and 4873 are OPEN | issues/number | main | n/a | present | 0 |
| R-19 | Issues 4721 and 4722, the fix-now candidates, are OPEN | issues/number | main | n/a | present | 0 |
| R-20 | Issues 4717, 4718, and 4730 have no acceptance text in their bodies | issues/number body | main | n/a | present | 0 |
| R-21 | Held-by numbers 4322, 4358, 4493, and 4799 to 4820 include 19 PRs (18 merged and 4813 OPEN) and 6 issues | pulls and issues | main | n/a | partial | 0 |
| R-22 | PR 4831 is CLOSED unmerged, and branch fix/4826-dash-pytest-hooks has head 725510a3 | pulls/4831 and branch fix/4826-dash-pytest-hooks | main | 725510a3237623e6c5a0653aea14263f4e51a94e | present | 0 |
| R-23 | Candidate commit 47c37f05c exists on GitHub | commits/47c37f05c | main | 47c37f05c16fef8d6593ba4c7f648e5086bb55c3 | present | 0 |
| R-24 | 63 refs exist under recovery/, and six MistHelper refs end in -wip-20261122 | git/matching-refs/heads/recovery/ | main | n/a | present | 0 |
| R-25 | The seven recovery branches named in handoff section 11 exist without a suffix | git/matching-refs/heads/recovery/ | main | n/a | present | 0 |
| R-26 | 169 archive/ tags exist, and the 47 new tags of comment 3 are not named | git/matching-refs/tags/archive/ | main | n/a | partial | 0 |
| R-27 | The 127 tip rows map to 44 distinct commits, and all 44 resolve | commits/sha for 44 SHAs | main | n/a | present | 0 |
| R-28 | Quality-gate issues 4891 to 4908 are OPEN for PRs 4886, 4888, 4889, and 4890 | issues with state open | main | n/a | present | 0 |
| R-29 | Dependabot PR 4886 proposes the devtools pin 2239e7bd in reusable-auto-merge.yml | pulls/4886 | main | 9e70001433bae97055b6bbe2825a345c0674273e | present | 0 |
| R-30 | The required labels exist: in-progress, chore, docs, needs-human-review, auto-merge, and quality-gate | gh label list | main | n/a | present | 0 |
| R-31 | The gh CLI supports the head guard flag match-head-commit on pr merge | gh pr merge --help | local | n/a | present | 0 |
| R-32 | No legacy record folder starts with 4870 on main or in the local specs tree | git/trees/main recursive and local specs | main | n/a | absent | 0 |
| R-33 | The feature pointer equals its value before PR 4846, which is parent commit e707ea05b | .specify/feature.json | main | b86bcad085666bd0aeb3ac2244c914908dc7fa70 | present | 2 |
| R-34 | Resolve-SpecFeaturePath routes numbered records under specs/numbered with base 5 and width 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-35 | create-new-feature.ps1 persists the feature pointer after it resolves the route | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 228 |
| R-36 | Save-FeatureJson writes .specify/feature.json | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 118 |
| R-37 | The reference record spec.md exists for issue 4920 | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-38 | The route sibling record spec.md exists for issue 4869 | specs/numbered/0/0/1/2/3/4/3/4/4869-speckit-1-4-3-upgrade/spec.md | main | 169130e5a966cdbce2f86aa276b6fd324219f6e9 | present | 0 |
| R-39 | The layout guard test and its baseline file exist | tests/guardrails/test_process_folder_structure.py and tests/guardrails/process_folder_baseline.json | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5, f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-40 | The route contract test exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| R-41 | The four Spec Kit templates exist | .specify/templates/spec-template.md, plan-template.md, tasks-template.md, and checklist-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2, 1a54553bd85cbef2178aa55efbeeb0c1942ffdde, 7e5170324d41a6736c498d6b9fc83651f31d0778, 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-42 | container-build.yml installs uv==0.13.9 on line 92 | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 92 |
| R-43 | The dev extra in pyproject.toml pins uv==0.13.9 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 101 |
| R-44 | The guard reads the uv pin and checks the container workflow | tests/guardrails/test_container_build_trigger.py | main | 48c4e62b67df372e2f26a900d3b4df3f47a8a612 | present | 85 |
| R-45 | The container-build.yml path filters list no spec or documentation Markdown path | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| R-46 | pyproject.toml pins misthelper-devtools to 2239e7bd | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 123 |
| R-47 | requirements-dev.txt pins misthelper-devtools to 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R-48 | uv.lock records misthelper-devtools at rev 2239e7bd | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1586 |
| R-49 | ci.yml lines 681 and 1317 pin misthelper-devtools to 79a5e459, annotated with v0.6.4 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | partial | 681 |
| R-50 | auto-merge.yml line 61 pins misthelper-devtools to d63a1204, and line 85 pins 79a5e459 | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | partial | 61 |
| R-51 | Six more workflows pin misthelper-devtools to 79a5e459 | close-linked-issues.yml:50, codeql.yml:41, container-build.yml:111, release.yml:85, ste-lint.yml:42, and stranded-branch-report.yml:47 | main | 42a085ac6240518b028862c290ec9502a5b13b2a, 2ef072fbddd473f841c5877f4d89b7c7760aeaf0, 737325976de75e90aa4526ab1cf2978782e648ce, e81c05798c7609344d2d59b94114d7d9f76263be, abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f, 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 50 |
| R-52 | Tag v0.6.4 of misthelper-devtools resolves to 79a5e459, and 2239e7bd is five commits ahead of it | misthelper-devtools git/ref/tags/v0.6.4 and compare | misthelper-devtools main | 79a5e45970e876f1656d69520d9635cea1aa25ef | partial | 0 |
| R-53 | misthelper-devtools PR 95 merged as 2239e7bd | misthelper-devtools pulls/95 | misthelper-devtools main | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | present | 0 |
| R-54 | pyproject.toml sets the mistapi floor at 0.64.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R-55 | copilot-instructions.md sets the mistapi floor at 0.64.0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| R-56 | The requirements.txt header gives the uv export command | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 2 |
| R-57 | The writing gate grades each Markdown file at a score of 80 | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 280 |
| R-58 | The merge queue section keeps the serialized merge until the owner verifies queue operation | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 116 |
| R-59 | The container document warns that down with -v removes production store volumes | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 50 |
| R-60 | copilot-instructions.md states that a removed volume is not recoverable | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 348 |
| R-61 | copilot-instructions.md records the issue 1893 token incident | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 546 |
| R-62 | copilot-instructions.md requires numbered routes for new records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-63 | The constitution defines the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-64 | The constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-65 | AGENTS.md requires each Markdown file to pass the STE gate | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R-66 | AGENTS.md forbids system prune and volume prune on a shared host | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 169 |
| R-67 | ci.yml runs the SpecKit task audit as an advisory job | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| R-68 | The STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R-69 | The pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| R-70 | The changelog fragment rule exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R-71 | The container policy guard exists | tests/guardrails/test_container_policy_docs.py | main | 1b842c302e52bcb43a95e4a2aed2366a93d94909 | present | 0 |
| R-72 | The PR title, STE, and CodeQL workflows exist | .github/workflows/pull-request-title.yml, ste-lint.yml, and codeql.yml | main | 6b161b5a7dd71a0f0c9c0f38b750a7322ae8704e, abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f, 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 0 |
| R-73 | org_export_utils.py logs an error and skips the invites export when listOrgInvites is missing | src/operations/exporting/export/org_export_utils.py | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 726 |
| R-74 | The installed mistapi 0.64.1 has no listOrgInvites in its 288 Python files | .venv\Lib\site-packages\mistapi (local SDK) | local | n/a | absent | 0 |
| R-75 | The resume path appends rows to an existing device-event CSV | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 306 |
| R-76 | The two device-event unit test modules exist | tests/unit/test_device_events_52w_exporter.py and tests/unit/test_device_events_52w_exporter_extended.py | main | de5aa5a82d9824bcc0dc158c49846923e828cd0b, 2361f5b0048d7834f63b8c360066a35344484f23 | present | 0 |
| R-77 | The local clone HEAD equals main | git rev-parse HEAD | local | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-78 | 26 cited local files equal their main blobs | git hash-object and git/trees/main | local | n/a | present | 0 |
| R-79 | Menu 97 in MistHelper.py binds the 52-week device-event export handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5229 |

## Decisions

The user gave full decision authority on 2026-11-21 (comment 3). The decisions below use that authority. Four decisions need a human because they fall under the categories in brief section 6. Each other decision has a reason and a risk.

| ID | Topic | Decision | Alternatives considered | Reason | Risk | Human decision |
| - | - | - | - | - | - | - |
| D-1 | Feature pointer | Keep the value of blob b86bcad0. Route records with Resolve-SpecFeaturePath only. | Run create-new-feature.ps1, which writes the pointer at line 228 (rejected). Hand-edit the pointer (rejected, because it drifts). | PR 4884 restored the value, and main matches the parent blob (R-33). | Spec-route scripts changed after the handoff (PR 4909), and issue 4910 reports lost hardening. | No |
| D-2 | Staging hold | Keep PR 4813 as a draft under the staging hold. Record the acceptance of PR 4806 as unverified. Ask a human for credentials or a hold decision (H-1). | Waive the hold (rejected, because the user requires acceptance). Revert PR 4806 (rejected, because no failure evidence exists). | The handoff states that the user requires staging acceptance, and the credentials are absent. | Staging code can stay unverified in production. | HUMAN-DECISION-REQUIRED (H-1) |
| D-3 | Shallow clone | Treat the unshallow as complete. Main holds 2535 commits. | Run git fetch --unshallow again (rejected, because it is done). | Local HEAD equals main (R-77), and the count matches the handoff at its snapshot (R-02). | The coordinator laptop can still be shallow (U-01). | No |
| D-4 | Recovery refs | Keep all 63 recovery refs and all archive tags. Review each ref in task T028 before any copy or delete. | Delete the six wip refs (rejected, because the work is unreviewed). Merge a recovery ref (rejected, because the handoff forbids it). | The handoff requires review before use. | The refs stay on origin, and the count can grow. | No |
| D-5 | Triage order | Start with issues 4721 and 4722 in one branch. Then triage 4837, 4863, 4868, and the 37 open issues outside the inventory. Then apply census categories. | Start with the oldest issue (rejected, because no value evidence exists). Start with the Dependabot PRs (rejected, because their gates need triage first). | Handoff section 15 names the fix-now candidates first. | Main already appends rows on resume (R-75), so the fix may need a test first. | No |
| D-6 | Dependabot PRs 4886 to 4890 | Do not merge a PR while a gate fails. Refresh each PR with the section 5 steps after its gate issue is triaged. | Merge after a rebase (rejected, because gates are red). Close all five (rejected, because the updates return). | Four PRs have failing gate issues (R-28). | Security updates wait longer. | No |
| D-7 | Devtools pins | Move the ten workflow uses lines to 2239e7bd in one change. Keep the three Python pins at 2239e7bd. | Move the Python pins back to v0.6.4 (rejected, because it loses five commits and Dependabot targets 2239e7bd). Keep the drift (rejected, because the handoff requires one devtools change). | Dependabot PR 4886 already targets 2239e7bd (R-29). | CI gate behavior changes across five commits. | No |
| D-8 | mistapi floor | Treat pyproject.toml line 29 as the pin of record. Correct the instruction file in a documentation change. | Lower the pin to 0.64.0 (rejected, because the installed SDK is 0.64.1). Keep the stale text (rejected, because it misstates the pin). | The installed SDK is 0.64.1 (R-54). | Two sources disagree until the documentation change lands. | No |
| D-9 | Hold phrases | A PR body that contains "do not merge", "held for", "hold stands", or "staging hold" as whole words stops the merge. | No phrase rule (rejected, because the handoff requires a check). A label rule (rejected, because the handoff defines no such label). | The handoff names a hold check but gives no phrases. | A normal sentence can match. A reviewer decides each match. | No |
| D-10 | Account identity | Before each GitHub write, run gh api user and stop unless the login is jmorrison-juniper. | Clear GH_TOKEN and GITHUB_TOKEN for each command (rejected, because this session needs the account token). Skip the check (rejected, because of incident 1893). | The handoff records a push under the wrong identity (R-61). | One extra API call for each write. | No |
| D-11 | Local-only claims | Mark the coordinator-laptop claims as unverified. Check them on that host in task T036. | Assume them true (rejected, because no evidence exists). Run host commands from this checkout (rejected, because the host differs). | Brief rule 5 states that local-only evidence does not prove committed code. | The claims stay open until task T036. | No |
| D-12 | Cisco converter licensing | Write no license or legal text. The owner decides licensing for issue 4635 before dependent specs proceed. | Write a license position (rejected, because it is legal text). Proceed without a decision (rejected, because issue 4224 depends on it). | The inventory names the licensing decision for issue 4635. | Converter specs wait. | HUMAN-DECISION-REQUIRED (H-2) |
| D-13 | PR 4208 | Keep the draft. The owner decides whether to continue or close. Recommended option: keep the draft until the acceptance blockers clear. | Close now (rejected, because the owner asks for a draft). Merge after a rebase (rejected, because the state is DIRTY). | Product priority belongs to the owner. | The draft branch becomes stale. | HUMAN-DECISION-REQUIRED (H-3) |
| D-14 | Secret file | Keep the .env file in worktree live-deploy-aa0762d until the owner names a destination. | Copy it into main (rejected, because secrets must not enter the repository). Remove the worktree (rejected, because it deletes the only copy). | Credential handling needs an owner instruction. | The worktree stays on the laptop. | HUMAN-DECISION-REQUIRED (H-4) |
| D-15 | Issue 4826 | Wait for upstream Dash. Do not merge the -p no:dash workaround. | Merge PR 4831 (rejected, because it closed unmerged after a test broke). Add another local workaround (rejected, because no evidence supports it). | PR 4831 closed unmerged (R-22). | The issue stays open for a long time. | No |
| D-16 | Issue 3400 lock file | Keep uv.lock tracked. Derive both requirements exports from it. The owner confirms closure. | Remove the lock file (rejected, because the gate reads it). Keep the question open (rejected, because the handoff needs a decision). | uv.lock is tracked on main (R-48). | The owner can choose another contract. | No |
| D-17 | Issue 1794 scope | Use the three preserved slices from the census as the first scope. Order them by the smallest diff. | Scope all 412 handlers now (rejected, because it is too large). Wait for a new census (rejected, because it delays the work). | The handoff names three preserved slices. | The census is not verified (U-05). | No |
| D-18 | Issues 4847 and 4849 | Align the site and webhook exporters with the FAILED result of issue 4860. | Keep the success messages (rejected, because a failed write reads as success). Leave the question open (rejected, because the handoff asks for it). | The operator reads the menu result. | A changed message can affect scripts that parse it. | No |
| D-19 | Issue 4762 | Keep it open. Correct section 10 of the body. | Close it again (rejected, because decision 3 reopened it). | The live state is OPEN (R-08). | None. | No |
| D-20 | Record location | Use the route and the slug backlog-handoff-recovery. Change no other record. | Use a timestamp route (rejected, because issue records use numbered routes). Use another slug (rejected, because this slug fits). | The route logic in Resolve-SpecFeaturePath gives this route for 4870 (R-34). Task T009 confirms the logic. | None. | No |
| D-21 | Handoff location | Keep the handoff as a GitHub issue. Put updates in issue comments and the body. Add no shared index file to the repository. | Add a repository index (rejected, because AGENTS forbids shared records on work branches). | The AGENTS rule for shared records (R-65 and the Git flow section). | Two places hold state until the body update. | No |
| D-22 | Scope | Only MistHelper is in scope. The vmm-topology-automation repository and the other repositories stay with their sessions. | Clean vmm-topology-automation now (rejected, because a session is busy there). | Comment 5 says to leave vmm-topology-automation to its session. | None for this record. | No |

## Named claim counts

- Named issues: 151. Of these, 127 are open and 24 are closed. The numbers are in the `related_issues` array of the STATUS file.
- Named PRs: 36. Of these, 2 are open, 33 are merged, and 1 is closed unmerged.
- Inventory: 127 rows. Of these, 126 are open. Issue 4867 is closed.
- Open issues on 2026-11-26: 166. These are the 126 open inventory rows and 40 issues outside the inventory. The 40 outside issues are 4870, 4762, 4873, and 37 other issues. The 37 other issues have numbers from 4877 to 4945. The highest inventory number is 4868.
- Cross-repo tokens: comment 2 names juniper-agent-skills PRs 823 and 825. MistHelper issue 825 and PR 823 are unrelated, so the record excludes them.
- Link pattern for each issue: https://github.com/jmorrison-juniper/MistHelper/issues/NUMBER. The link pattern for each PR uses /pull/NUMBER.

## Sources

- Handoff issue 4870, body and comments 0 to 5. Read with gh issue view on 2026-11-26. URL: https://github.com/jmorrison-juniper/MistHelper/issues/4870
- Repository files on main. Each source has a blob SHA in the remote table.
- Local SDK: `.venv\Lib\site-packages\mistapi` with dist-info `mistapi-0.64.1.dist-info`. The search covered 288 Python files.
- gh CLI help text: `gh pr merge --help`, read on the local machine.
- Repository rules: AGENTS.md (R-65 and R-66), `.github/copilot-instructions.md` (R-55, R-60, R-61, R-62), and `.specify/memory/constitution.md` (R-63 and R-64).
- The reference record 4920 was read for its shape. Its file list, its heading structure, and its design folder were read by search. Its content was not copied.
- Documents read because a claim depends on them: documentation/quality-gates.md (R-57 and R-58), documentation/container-deployment.md (R-59), and changelog.d/README.md (R-70).
- Documents not read because no claim depends on them: documentation/architecture.md, documentation/development-setup.md, and documentation/operator-guide.md. The change touches no architecture, setup, or operator behavior.
- No web source was fetched. The record makes no Mist endpoint claim, so the Mist OpenAPI files were not read.

## Skills

No local skill was loaded. No local skill covers the handoff rules. The container rules come from repository documents (R-59 and R-60).

## Unverified

| ID | Claim | Reason |
| - | - | - |
| U-01 | The coordinator laptop holds 670 local branches, 78 worktrees, 47 local-only tags, and the stash counts in handoff sections 12 and 14 and comments 2 and 3. | The coordinator clone is on another host. No host command ran in this session. |
| U-02 | The secret scan of the new commits and the recovery snapshots found 0 hits (comment 3). | The scan ran on the coordinator host. No scan ran in this session. |
| U-03 | The Podman volumes named in comment 3 exist, and each keeps its data. | Container host state. Brief rule 2 bars container commands. |
| U-04 | The spec-route tests fail 41 tests without pwsh (handoff section 6). | The tests do not run in this session (brief rule 2). |
| U-05 | The census categories from 2026-11-18 and the census file. | The census is not in the repository or on GitHub. |
| U-06 | Quality Gates was green at 260f4bcf (handoff section 14). | The three latest runs cover heads f03c6c9b3, ccff03e05, and 4e81b2a4a. The historical run was not listed. The current head is verified (R-04). |
| U-07 | Dependabot does not refresh uv.lock (handoff section 5). | The Dependabot behavior was not tested. The procedure is applied as written. |
| U-08 | The 47 archive tags named in comment 3 exist. | Comment 3 does not list their names (R-26). |
| U-09 | The 138 local tags already on origin match the commit of their local copies. | The local tag list is not on GitHub. |
| U-10 | The content of each recovery branch is unfinished work as the handoff states. | Branch review is task T028. This record does not review code content. |
| U-11 | The owner statement for PR 4208 and its acceptance blockers (handoff section 9). | The owner statement is not GitHub evidence. The PR state is verified (R-14). |
| U-12 | The session state of vmm-topology-automation (comment 5). | It is another repository and host. It is out of scope (D-22). |
| U-13 | The user gave full decision authority on 2026-11-21 (comment 3). | This is a user statement, not a GitHub fact. The record treats it as an assumption. |
| U-14 | Commit 1982b7e84 held 2527 commits at its merge. | The count is derived from R-02 by subtraction, so the record does not claim a direct check. |
| U-15 | Recovery branches exist in fiber-planner-copilot, juniper-agent-skills, and misthelper-devtools (comment 3). | Those repositories were not checked. |
| U-16 | PRs 4322, 4358, and 4493 hold the 13 old local commits (comment 3). | Commit membership in each PR was not checked. Only the PR states are verified (R-21). |
