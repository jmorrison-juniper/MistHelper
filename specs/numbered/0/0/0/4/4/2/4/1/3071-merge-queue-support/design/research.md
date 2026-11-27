# Research: Merge queue rollout and acceptance

Read date: 2026-11-26. Remote reference: `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Local files match the remote blobs in the tables below. Result values are `present`, `absent`, `partial`, or `stale`. A `present` result means that the claim holds on `main`. An `absent` result means that the named item does not exist on `main`. A `stale` result means that the named text conflicts with `main`. A `partial` result means that the sources disagree.

## Decisions

### D-1 Activation boundary

- **Decision**: Keep strict up-to-date protection and the serial merge slot until owner activation. No agent changes a setting.
- **Alternatives**: (a) Activate the merge queue now. Rejected, because owner approval is required (`https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6309236843`). (b) Set `strict` to false. Rejected, because `documentation/quality-gates.md` line 229 warns against it. (c) Rely on the auto-update setting. Rejected, because the setting is already on and the race remains (U-5).
- **Rationale**: The owner chose to keep strict protection and to review before activation. The preparation exists on `main` (R-01, R-10).
- **Risk**: The serial merge slot limits throughput until activation.
- **Human decision required**: No.

### D-2 No workflow file edit

- **Decision**: This change edits no file under `.github/workflows/`.
- **Alternatives**: (a) Edit `ci.yml` to add comments or names. Rejected, because no behavior changes and the shared auto-merge workflow refuses workflow file edits (R-17). (b) Add `merge_group` to `ste-lint.yml`. Rejected, because the STE check is not a required context (R-52). (c) Add a new workflow guard. Rejected, because the guard module already covers the triggers (R-30 to R-33).
- **Rationale**: The preparation is complete. A pull request without a workflow file edit can use the shared auto-merge path (R-17, R-18).
- **Risk**: None new. Any later workflow edit needs a manual merge.
- **Human decision required**: No.

### D-3 STE workflow stays without the queue trigger

- **Decision**: Keep `ste-lint.yml` without `merge_group`. The procedure records a constraint. The trigger must exist before the owner makes the STE check required.
- **Alternatives**: (a) Add the trigger now. Rejected, because the workflow reports no required context (R-52), and the trigger spends runner minutes without a required signal. (b) Record nothing. Rejected, because a later required STE check would stall the queue.
- **Rationale**: The required contexts list holds 15 names, and `STE compliance` is not one of them (R-52). The constraint keeps a future change safe.
- **Risk**: The owner later makes the STE check required. Mitigation: the constraint text (T005).
- **Human decision required**: No.

### D-4 Documentation location

- **Decision**: The merge rule stays in `.github/copilot-instructions.md` and `documentation/quality-gates.md`. No file under `.github/instructions/` is created.
- **Alternatives**: (a) Create the absent file. Rejected, because it would add a second source that the STE gate does not lint. (b) Edit `AGENTS.md`. Rejected, because its canonical copy is in `misthelper-devtools` (R-41). (c) Keep the rule only in the record. Rejected, because contributors do not read the record.
- **Rationale**: The owner approved `documentation/quality-gates.md` as the documentation location (R-24, `https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6296715182`).
- **Risk**: The issue acceptance text still names the absent path (DF-6). The owner edits the text.
- **Human decision required**: No.

### D-5 Pull request reference

- **Decision**: The pull request body uses `Refs #3071`.
- **Alternatives**: (a) `Closes #3071`. Rejected, because the issue closes before the owner evidence exists. This breaks the owner instruction (R-25 and `https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6309236843`). (b) No issue reference. Rejected, because the link to the issue is lost.
- **Rationale**: Operational acceptance is incomplete (R-56). The constitution asks for `Closes` (R-40), but the owner rule for this issue is more specific. The brief template also names `Closes`, so this record overrides it for issue #3071 only.
- **Risk**: The coordinator rejects the body. Mitigation: the pull request body states the reason.
- **Human decision required**: No.

### D-6 Release-note fragment

- **Decision**: Add one fragment named `changelog.d/issue-3071-merge-queue-rollout.md`.
- **Alternatives**: (a) No fragment. Rejected, because the constitution requires one fragment for each change (R-65). (b) Reuse the legacy fragment. Rejected, because the legacy fragment describes the preparation.
- **Rationale**: The constitution supersedes the practice documents (constitution governance section). PR #4362 added a fragment for the same issue (R-36).
- **Risk**: Low. The fragment is one file.
- **Human decision required**: No.

### D-7 Record reuse

- **Decision**: Reuse the folder `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/`. Revise its nine files.
- **Alternatives**: (a) Create `3071-merge-queue-activation`. Rejected, because the legacy tasks T012 and T013 and the legacy evidence would split across two records. (b) Leave the legacy record unchanged. Rejected, because its stale claims (L-11, L-12, L-13, L-22) would remain.
- **Rationale**: One active record exists for each issue. The legacy record already holds task T013 (R-43).
- **Risk**: The git history of the nine files shows the revision. `analysis.md` keeps the verification of each legacy claim.
- **Human decision required**: No.

### D-8 Verification candidates and owner parameters

- **Decision**: Use two documentation-only verification candidates. Add each candidate to the merge queue by hand. Set merge limits to a minimum of one and a maximum of one. Set the status check timeout to 60 minutes. Use the `auto-merge` label only after both candidates succeed.
- **Alternatives**: (a) Batch size above one now. Rejected, because a batch mixes the evidence of several candidates (R-63 shows that limits range from 1 to 100). (b) Use the `auto-merge` label first. Rejected, because the queue behavior of `gh pr merge --auto` is unverified (U-2). (c) A timeout below 60 minutes. Rejected, because the issue comments report Quality Gates runs of about 23 minutes and up to 41 minutes (U-5), and a shorter timeout risks a false failure. (d) No timeout. Rejected, because the docs define the timeout as the wait for CI before failure (R-63).
- **Rationale**: Each candidate gives one clean result. Documentation-only candidates carry no workflow file, so the shared auto-merge path stays open (R-17). The required contexts still run, because no required workflow has a path filter (R-05).
- **Risk**: Verification takes longer. The owner may change these values. A changed value needs a revision of this record.
- **Human decision required**: No.

### D-9 Shared canceled-result handling stays external

- **Decision**: Keep the shared auto-merge workflow unchanged in this repository. The procedure treats canceled, timed-out, stale, and skipped results as unresolved. A follow-up issue in `misthelper-devtools` is recommended. This run does not create it.
- **Alternatives**: (a) Patch the shared workflow here. Rejected, because the workflow is pinned at an external commit and needs review in `misthelper-devtools`. (b) Accept the open Dependabot pin bump (PR #4886, which changes `auto-merge.yml`). Rejected for this change, because the owner decides the pin. The pull request does not touch `auto-merge.yml`.
- **Rationale**: The shared file has no handling for these conclusions (R-19). The residual risk is external.
- **Risk**: A poller reads a canceled result as passing. Mitigation: the owner reads each required result before a merge, as the procedure requires.
- **Human decision required**: No.

### D-10 Review rule before activation

- **Decision**: The owner confirms the review rule before owner step O-3. No agent changes any review setting.
- **Alternatives**: (a) Assume no review rule. Rejected, because the three reads disagree (R-53). (b) Assume one approval. Rejected, for the same reason.
- **Rationale**: Only the owner can confirm the setting. The reads cannot resolve the conflict (R-53, `https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6516090555`).
- **Risk**: Merges block or proceed in an unexpected way. Mitigation: the confirmation happens before activation.
- **Human decision required**: No.

## Remote verification

The table has 66 rows. The `remote_checks` array in `META_DIR\3071-STATUS.json` holds the same 66 rows. The `summary.md` count matches both.

| ID | Claim | Path | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | `ci.yml` declares `merge_group` with `types: [checks_requested]` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 18 |
| R-02 | `ci.yml` concurrency group keys on pull request number or ref | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 58 |
| R-03 | `ci.yml` cancels in progress only for pull request events | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 69 |
| R-04 | `ci.yml` push trigger is limited to `main` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 23 |
| R-05 | `ci.yml` has no paths filter and no branch filter under `pull_request` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 0 |
| R-06 | `ci.yml` queue checkout uses the event commit with `github.sha` as fallback | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 610 |
| R-07 | `ci.yml` contains the step `Fetch the historical performance inventory revision`, which the legacy record names as the PR #4306 repair | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 274 |
| R-08 | `ci.yml` browser evidence upload steps exist | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 910 |
| R-09 | `ci.yml` declares the 14 required job names (lines 141, 168, 202, 331, 414, 454, 504, 532, 552, 571, 587, 656, 955, 1123) | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 141 |
| R-10 | `codeql.yml` declares `merge_group` with `types: [checks_requested]` | `.github/workflows/codeql.yml` | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 11 |
| R-11 | `codeql.yml` concurrency group keys on pull request number or ref | `.github/workflows/codeql.yml` | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 27 |
| R-12 | `codeql.yml` cancels in progress only for pull request events | `.github/workflows/codeql.yml` | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 29 |
| R-13 | `codeql.yml` push trigger is limited to `main` | `.github/workflows/codeql.yml` | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 14 |
| R-14 | `ste-lint.yml` declares no `merge_group` trigger (its `pull_request` trigger is at line 26) | `.github/workflows/ste-lint.yml` | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | absent | 26 |
| R-15 | The STE file list in `ste-lint.yml` excludes `documentation/quality-gates.md` | `.github/workflows/ste-lint.yml` | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | absent | 44 |
| R-16 | `auto-merge.yml` pins `reusable-auto-merge.yml` at `d63a120487cecf750184cb178387cdc25c0a7635` | `.github/workflows/auto-merge.yml` | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 61 |
| R-17 | The shared auto-merge workflow stops a pull request that edits `.github/workflows/` | `reusable-auto-merge.yml` in `misthelper-devtools` | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 116 |
| R-18 | The shared auto-merge workflow requests auto-merge with `gh pr merge --auto` | `reusable-auto-merge.yml` in `misthelper-devtools` | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 192 |
| R-19 | The shared auto-merge workflow has no merge queue text and no handling for canceled, timed-out, or stale conclusions | `reusable-auto-merge.yml` in `misthelper-devtools` | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | absent | 0 |
| R-20 | The shared quality gate issues workflow excludes `merge_group` runs from issue changes | `reusable-quality-gate-issues.yml` in `misthelper-devtools` | 79a5e45970e876f1656d69520d9635cea1aa25ef | 9a46074e9baee83afb3405d7c51fd4e21797f17c | present | 118 |
| R-21 | The shared CodeQL workflow checks out the caller commit with no `ref` override | `reusable-codeql.yml` in `misthelper-devtools` | 79a5e45970e876f1656d69520d9635cea1aa25ef | ea8264b7e31b57cc4ed8a8f09571f288cb9345f0 | present | 81 |
| R-22 | The shared CodeQL workflow names the analysis category per language | `reusable-codeql.yml` in `misthelper-devtools` | 79a5e45970e876f1656d69520d9635cea1aa25ef | ea8264b7e31b57cc4ed8a8f09571f288cb9345f0 | present | 98 |
| R-23 | `documentation/quality-gates.md` has the heading `## Merge queue preparation and activation` | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 92 |
| R-24 | `documentation/quality-gates.md` states that the owner approved the documentation location | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 108 |
| R-25 | `documentation/quality-gates.md` requires `Refs #3071` for the preparation pull request | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 118 |
| R-26 | `.github/copilot-instructions.md` has the heading `### Serial validation and merge queues` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 483 |
| R-27 | The `ci.yml` row of the workflow table omits merge queue candidates | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 467 |
| R-28 | The `codeql.yml` row of the workflow table omits merge queue candidates | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 468 |
| R-29 | The procedure link points to the anchor `merge-queue-preparation-and-activation` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 499 |
| R-30 | `tests/guardrails/test_ci_gate_triggers.py` defines `test_merge_group_contract` for `ci.yml` and `codeql.yml` | `tests/guardrails/test_ci_gate_triggers.py` | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 131 |
| R-31 | The same module defines `test_required_check_names` for the 14 CI job names | `tests/guardrails/test_ci_gate_triggers.py` | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 201 |
| R-32 | The same module pins 10 gated jobs and audits `always()` conditions | `tests/guardrails/test_ci_gate_triggers.py` | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 368 |
| R-33 | The same module defines `test_event_concurrency_isolation` | `tests/guardrails/test_ci_gate_triggers.py` | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 377 |
| R-34 | `changelog.d/README.md` rule 4 allows no fragment for an internal-only change | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-35 | `changelog.d/` holds 335 top-level entries | `changelog.d/` (tree listing) | main | Not applicable: directory listing | present | 0 |
| R-36 | `changelog.d/issue-3071-merge-queue-support.md` exists with the heading `### Changed` | `changelog.d/issue-3071-merge-queue-support.md` | main | d88735dbdf2e32e92875c67a7f62b94c0b2d47e5 | present | 1 |
| R-37 | `.github/PULL_REQUEST_TEMPLATE.md` exists | `.github/PULL_REQUEST_TEMPLATE.md` | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| R-38 | `.ste-linter.toml` sets `min_score = 80` | `.ste-linter.toml` | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 15 |
| R-39 | `pyproject.toml` requires Python 3.15 or newer | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-40 | The constitution requires the Closes keyword with the issue number in each pull request body | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 518 |
| R-41 | `AGENTS.md` names the `misthelper-devtools` repository as the canonical copy | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 13 |
| R-42 | `.github/instructions/git-flow-multi-agent.instructions.md` is absent | `.github/instructions/git-flow-multi-agent.instructions.md` | main | Not applicable: absent path | absent | 0 |
| R-43 | The legacy record folder holds nine files | `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support` | main | 62b5e109d7c8fcff274056c077a8be461238ebe6 | present | 0 |
| R-44 | The reference record exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-45 | The legacy plan states Python 3.13 | `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/plan.md` | main | ce71576dee621ea914d8c5a5ebf508cbd9e98023 | stale | 15 |
| R-46 | The legacy task T012 is pending | `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/tasks.md` | main | 0a5ba7e00ff59ba9b64022c3c0e7c20916329ecc | stale | 47 |
| R-47 | Runs 39467257427 (Quality Gates) and 39467257440 (CodeQL Analysis) succeeded on head `93b222a5b7d6c1179bc6660f1f1777d7bf40dd57` | GitHub Actions API, `repos/jmorrison-juniper/MistHelper/actions/runs/39467257427` and `repos/jmorrison-juniper/MistHelper/actions/runs/39467257440` | 93b222a5b7d6c1179bc6660f1f1777d7bf40dd57 | Not applicable: run record | present | 0 |
| R-48 | PR #4362 merged as `00633cad3a544190a1fbf4fd1999308e91b90c4a` with its 15 required contexts successful | `https://github.com/jmorrison-juniper/MistHelper/pull/4362` | main | Not applicable: pull request | present | 0 |
| R-49 | PR #4483 merged as `0fcb6ae99eb737dd95a9569e3f5c181090e90ecb` with one failed non-required job | `https://github.com/jmorrison-juniper/MistHelper/pull/4483` | main | Not applicable: pull request | present | 0 |
| R-50 | PR #4208 changes `ci.yml` | `https://github.com/jmorrison-juniper/MistHelper/pull/4208` | main | Not applicable: open draft pull request | stale | 0 |
| R-51 | PR #4306 changed `ci.yml` and merged as `36dea20b8526702026e4e0eaf1d74280437755f0` | `https://github.com/jmorrison-juniper/MistHelper/pull/4306` | main | Not applicable: pull request | present | 0 |
| R-52 | Branch protection on `main` sets `strict` true, 15 required contexts, linear history, no force push, and no deletion | `repos/jmorrison-juniper/MistHelper/branches/main/protection` | main | Not applicable: API setting | present | 0 |
| R-53 | The review rule reads disagree: full protection null, reviews endpoint count 1, GraphQL `requiresApprovingReviews` false | `repos/jmorrison-juniper/MistHelper/branches/main/protection`, `repos/jmorrison-juniper/MistHelper/branches/main/protection/required_pull_request_reviews`, and GraphQL `branchProtectionRules` | main | Not applicable: API setting | partial | 0 |
| R-54 | The repository has zero rulesets | `repos/jmorrison-juniper/MistHelper/rulesets` | main | Not applicable: API setting | absent | 0 |
| R-55 | The merge queue for `main` is null | GraphQL `repository.mergeQueue(branch: main)` | main | Not applicable: API setting | absent | 0 |
| R-56 | Issue #3071 is open with labels `ci`, `chore`, `in-progress`, `workflow`, `priority:P1`, and `severity:high` | `https://github.com/jmorrison-juniper/MistHelper/issues/3071` | main | Not applicable: issue | present | 0 |
| R-57 | Issue #3070 is closed, so the serial merge slot is free | `https://github.com/jmorrison-juniper/MistHelper/issues/3070` | main | Not applicable: issue | present | 0 |
| R-58 | No open pull request changes `ci.yml`, `codeql.yml`, `copilot-instructions.md`, `quality-gates.md`, or the guard module. PR #4886 changes `auto-merge.yml`. | `repos/jmorrison-juniper/MistHelper/pulls` with state open (7 pull requests) | main | Not applicable: pull request list | present | 0 |
| R-59 | PRs #4498, #4513, and #4515 merged on 2026-10-30 | `https://github.com/jmorrison-juniper/MistHelper/pull/4498`, `https://github.com/jmorrison-juniper/MistHelper/pull/4513`, `https://github.com/jmorrison-juniper/MistHelper/pull/4515` | main | Not applicable: pull requests | present | 0 |
| R-60 | `main` points to commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | `repos/jmorrison-juniper/MistHelper/git/ref/heads/main` | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-61 | GitHub docs: a merge queue requires the `merge_group` event in the workflow | `https://api.github.com/repos/github/docs/contents/content/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue.md?ref=main` | main | c5555c295c2a5389d0c9acfa2c3d766b982e2cf2 | present | 32 |
| R-62 | GitHub docs: a failing queue candidate is removed from the merge queue | Same URL as R-61 | main | c5555c295c2a5389d0c9acfa2c3d766b982e2cf2 | present | 108 |
| R-63 | GitHub docs: the "Require merge queue" setting (line 53), the status check timeout (line 67), and merge limits between 1 and 100 (line 69) | Same URL as R-61 | main | c5555c295c2a5389d0c9acfa2c3d766b982e2cf2 | present | 53 |
| R-64 | GitHub docs: the `merge_group` event supports only the `checks_requested` activity type | `https://api.github.com/repos/github/docs/contents/content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md?ref=main` | main | 08dd514c351860067cffea0f9ec714f8fc964e9d | present | 436 |
| R-65 | The constitution requires one release-note fragment for each change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-66 | `documentation/contributing.md` step 6 asks for the Closes keyword with the issue number in the pull request body | `documentation/contributing.md` | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 12 |

Result counts: present 53, absent 7, stale 5, partial 1. Total 66.

## Legacy record verification

The legacy record is `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/`. It holds nine files. Each claim below comes from one of those files. The remote row column names the row in the remote table that verifies the claim.

| ID | Legacy claim (file and location) | Remote rows | Result |
| - | - | - | - |
| L-01 | Spec FR-001: both required-context workflows accept queue checks | R-01, R-10 | verified |
| L-02 | Spec FR-002: 15 required context names stay unchanged | R-09, R-52 | verified |
| L-03 | Plan: default checkout measures the queue commit | R-06, R-21 | verified |
| L-04 | Spec FR-004: queue references isolate candidates | R-02, R-11, R-33 | verified |
| L-05 | Spec FR-005: existing pull request and main validation remain | R-04, R-13 | verified |
| L-06 | Spec FR-007: preparation changes no repository setting | R-52, R-54, R-55 | verified |
| L-07 | Spec FR-008: procedure separates preparation, activation, evidence, and recovery | R-23 | verified |
| L-08 | Spec FR-009: preparation does not close #3071 | R-25, R-56 | verified |
| L-09 | Spec FR-010: browser evidence and historical fetch stay in place | R-07, R-08 | verified |
| L-10 | Spec edge case: the historical instruction path does not exist | R-42 | verified |
| L-11 | Spec edge case: another open pull request holds part of `ci.yml` | R-58 | stale |
| L-12 | Spec assumption: PR #4208 released only the `ci.yml` trigger section | R-50 | stale |
| L-13 | Plan: Python 3.13 | R-39, R-45 | stale |
| L-14 | Plan: the changelog directory exceeds five children | R-35 | verified |
| L-15 | Plan: the pinned CodeQL workflow checks out the caller commit and keeps the Python category | R-21, R-22 | verified |
| L-16 | Plan: issue synchronization excludes merge-group events | R-20 | verified |
| L-17 | Plan: the explicit quality checkout falls back to `github.sha` | R-06 | verified |
| L-18 | Tasks T005: `merge_group` added to `ci.yml` and `codeql.yml` | R-01, R-10 | verified |
| L-19 | Tasks T007: CodeQL cancellation limited to pull requests | R-12 | verified |
| L-20 | Tasks T008: procedure documented in `documentation/quality-gates.md` | R-23 | verified |
| L-21 | Tasks T009: changelog fragment added | R-36 | verified |
| L-22 | Tasks T012: pull request and coordinator review pending | R-46, R-48 | stale |
| L-23 | Tasks T013: owner activation pending | R-54, R-55 | absent |
| L-24 | Analysis: CI and CodeQL runs passed on the initial head | R-47 | verified |
| L-25 | Research: other workflows report no required context | R-09, R-52 | verified |
| L-26 | Contracts: pull request triggers have no branch filter, and push triggers stay on `main` | R-04, R-05, R-13 | verified |
| L-27 | Data model: 14 CI job names and the CodeQL context | R-09, R-52 | verified |
| L-28 | Analysis: local guardrail, Ruff, Black, mypy, Bandit, pip-audit, and ratchet results | Not applicable: local run record, not re-run | unverified (U-6) |

Result counts: verified 22, stale 4, absent 1, unverified 1. Total 28.

## Sources

### Local files on `main`

- `AGENTS.md`, read in full. Blob `44a9afffb5bd6f774973a845d27343e4e528b6ad`.
- `.github/copilot-instructions.md`, read in full (601 lines). Blob `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179`.
- `.specify/memory/constitution.md`, read in full (version 1.9.0). Blob `4584997a264c5a7ade2ca7441246e1f067083aa1`.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full.
- `.specify/scripts/powershell/spec-route.ps1`, read only. The route for number 3071 follows the function `Get-SpecRadixSegments`. The script was not run.
- `documentation/quality-gates.md`, read in full. Blob `6776d334cca5d9b43273473a06da367a65605c6d`.
- `documentation/contributing.md`, read in full. Blob `3b455b6d6730e16972540f14f7f654462b1c27bd`. Step 6 asks for the Closes keyword with the issue number in the pull request body (line 12, R-66). Step 7 names the `auto-merge` label rule (line 13). This change leaves the file unchanged, so the conflict stays recorded (DF-7).
- `changelog.d/README.md`, read in full. Blob `fcbde10e0c293390bd9df8d62a5d61f158eca384`.
- `tests/guardrails/test_ci_gate_triggers.py`, read in the ranges that the table cites. Blob `6ae30aa0f6a0ab008977b28df3ce728e3dd22411`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md`, lines 1 to 70, read for the record shape (clarifications, story layout, and requirement style). The content was not copied.
- Other `documentation/` files that were searched for merge terms (`merge_group`, merge queue, auto-merge, serial merge): `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md`. None contains those terms, so they do not apply to this issue.

### Remote files and API reads

- Repository tree: `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (11,404 entries, not truncated).
- Repository content reads: the GitHub API contents endpoint, one call for each path in the tables, with `ref=main`. The blob SHAs appear in the tables.
- Shared workflows, read through the GitHub API at pinned commits:
  - `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-auto-merge.yml?ref=d63a120487cecf750184cb178387cdc25c0a7635`
  - `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-quality-gate-issues.yml?ref=79a5e45970e876f1656d69520d9635cea1aa25ef`
  - `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-codeql.yml?ref=79a5e45970e876f1656d69520d9635cea1aa25ef`
- Branch protection and rulesets: `https://api.github.com/repos/jmorrison-juniper/MistHelper/branches/main/protection`, `https://api.github.com/repos/jmorrison-juniper/MistHelper/branches/main/protection/required_pull_request_reviews`, and `https://api.github.com/repos/jmorrison-juniper/MistHelper/rulesets`.
- GraphQL: `https://api.github.com/graphql` with `branchProtectionRules` and `repository.mergeQueue`.

### Public GitHub documentation

- `https://api.github.com/repos/github/docs/contents/content/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue.md?ref=main` (fetched through the GitHub API).
- `https://api.github.com/repos/github/docs/contents/content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md?ref=main` (fetched through the GitHub API).
- The page `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue` was requested with the web fetch tool. The tool returned a blocked-address error (WebFetchBlockedUrlError). The API copy above is the source used.

### Issue and pull request records

- Issue #3071: `https://github.com/jmorrison-juniper/MistHelper/issues/3071`. Comments cited: `issuecomment-6296715182` (2026-10-20, documentation location and reservation), `issuecomment-6309236843` (2026-10-21, owner decision), `issuecomment-6410662863` (2026-10-26, status), and `issuecomment-6516090555` (2026-10-30, review rule conflict).
- Pull requests: `https://github.com/jmorrison-juniper/MistHelper/pull/4362`, `https://github.com/jmorrison-juniper/MistHelper/pull/4483`, `https://github.com/jmorrison-juniper/MistHelper/pull/4208`, `https://github.com/jmorrison-juniper/MistHelper/pull/4306`, `https://github.com/jmorrison-juniper/MistHelper/pull/4498`, `https://github.com/jmorrison-juniper/MistHelper/pull/4513`, `https://github.com/jmorrison-juniper/MistHelper/pull/4515`, and `https://github.com/jmorrison-juniper/MistHelper/pull/4886`.

## Not applicable

- **Mist API and mistapi**: This change adds no Mist call and no SDK call. The mistapi version pin stays unchanged. The Mist OpenAPI file and the SDK source were not read.
- **Podman and containers**: This change changes no container file and starts no container. The container build does not start, because no product file changes.
- **Juniper device behavior**: Not applicable. No device behavior is in scope.
- **Skills**: No skill was loaded. No listed skill covers GitHub merge queues or CI merge gates.

## Unverified

Each item below is a claim that this record depends on, and this review could not verify it on `main`. The reason is given with each item.

- **U-1**: Required contexts with the conclusion `SKIPPED` count as passing under the merge queue. The fetched GitHub docs (R-61, R-64) do not state it. No queue is active (R-55). The procedure treats `skipped` as unresolved.
- **U-2**: `gh pr merge --auto` (R-18) adds a pull request to an active merge queue. The fetched GitHub docs do not state it (R-61 to R-64). No queue is active (R-55). Owner steps O-4 and O-5 test it.
- **U-3**: The `CodeQL` context reports on a `merge_group` commit. The context belongs to the code scanning application. No queue commit exists yet (R-55). The owner verifies it live.
- **U-4**: Canceled, timed-out, and stale required results block a merge in the shared auto-merge workflow. R-19 shows no handling for those conclusions. The runtime behavior was not tested.
- **U-5**: The merge gaps, check durations, and force-push counts in the issue comments of 2026-10-06 (for example, 21.28 minutes for the shortest gap, 23.08 minutes for the median Quality Gates run, and 9 force pushes on PR #3054). The owner reported them. This review did not re-measure them.
- **U-6**: The local results in the legacy analysis (1,060 guardrail tests, Ruff, Black, mypy, Bandit, pip-audit, and the test quality ratchet). The runs used Python 3.13.13 (R-45, R-39). This review did not re-run them.
- **U-7**: The Dependabot refresh observations in the issue comment of 2026-11-10. The owner reported them. This review did not re-measure them.
- **U-8**: The cause of the failed `ops-portal` job on PR #4483 (R-49). This review did not investigate it.
