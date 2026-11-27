# Research: Pin the verified auto-merge commit

This file records each decision, each remote check, each source, and each claim that stays unverified. Each remote check row is also one entry in `remote_checks` of the STATUS file.

## Decisions

### D-1 Accept the Dependabot update to 2239e7b

- Alternatives: (a) keep d63a120 and close pull request 4886. (b) accept 2239e7b after a blob check.
- Chosen: (b).
- Reason: The reusable workflow blob SHA is `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` at both commits (rows R-14 and R-15). The compare shows no change to that file (row R-16). The file calls GitHub CLI commands, and no keyword scan found a devtools script call (U-7).
- Risk: Each later pin needs its own blob check. A missed check can admit an unreviewed upstream change.
- Human decision: No.

### D-2 Move the verified commit with the pin, as a literal value

- Alternatives: (a) read the expected pin from the workflow file inside the guard. (b) move the literal constant with the pin in one commit.
- Chosen: (b).
- Reason: Option (a) compares the workflow with itself, so the guard cannot fail. The precedent commit 11569e461 changed both values together (rows R-36 and R-37).
- Risk: A reviewer may treat equality as proof of safety. Decision D-9 and analysis item A-4 address this risk.
- Human decision: No.

### D-3 Deliver through a new branch from main, as a replacement pull request

- Alternatives: (a) push a commit to the Dependabot branch. (b) stack a branch on the Dependabot branch. (c) open a new branch from main.
- Chosen: (c).
- Reason: `AGENTS.md` section "Parallel agents and shared state" forbids a push to a branch that another agent owns. Section "Branch" requires a branch from main only, and it forbids stacking. Main now names commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Risk: Two open pull requests change the same line until pull request 4886 closes (D-7).
- Human decision: No.

### D-4 Add no new test case

- Alternatives: (a) add a negative control test for `shared_call_problems`. (b) add a test that reads the blob SHA from GitHub during CI. (c) add no test.
- Chosen: (c).
- Reason: Test TP-07 fails on a pin mismatch, as the failed run 45064239338 shows. Option (b) needs network access in CI. Option (a) restates the equality check.
- Risk: A later guard edit can remove the literal comparison. FR-004 forbids that edit.
- Human decision: No.

### D-5 Add no changelog fragment

- Alternatives: (a) add `changelog.d/issue-4906-auto-merge-verified-pin.md`. (b) add no fragment and state the reason in the pull request body.
- Chosen: (b).
- Reason: `changelog.d/README.md` rule 4 at line 58 allows no fragment for an internal-only change. No product user sees this change.
- Risk: None material.
- Human decision: No.

### D-6 Commit the spec record in the replacement pull request

- Alternatives: (a) open a separate pull request for the record. (b) keep the record and the change in one pull request.
- Chosen: (b).
- Reason: The record explains the change. One pull request keeps both together. The route guard runs in the same CI shard (`.github/workflows/ci.yml` line 255).
- Risk: The record repeats the old commit SHA as history. The record names the SHA only as history.
- Human decision: No.

### D-7 Close pull request 4886 after the replacement merges

- Alternatives: (a) close it now. (b) close it after the replacement merges, with a preservation comment. (c) leave it open.
- Chosen: (b).
- Reason: `AGENTS.md` section "Preserve work before you close an unmerged pull request" requires a preservation proof. Closing early removes the open update before a replacement exists. Leaving it open keeps a failing update in the queue.
- Risk: Dependabot may reopen the update (item U-4 in `analysis.md`).
- Human decision: No.

### D-8 Set labels: add in-progress and keep the ci scope label

- Alternatives: (a) add the `tests` scope label. (b) keep `ci` and add `in-progress`. (c) add no label.
- Chosen: (b). Labels to add: `in-progress`. Labels to remove: none.
- Reason: `.github/copilot-instructions.md` section "Git and GitHub in this repository" requires one type label and one scope label on each issue. The issue already holds `bug` and `ci`. `AGENTS.md` section "Issue first" requires the `in-progress` label before a branch.
- Risk: The scope label `ci` does not name the guard folder. The guard file sits under `tests/guardrails`. The risk is low.
- Human decision: No.

### D-9 Record the blob evidence beside the verified commit

- Alternatives: (a) keep the evidence only in the pull request body. (b) add comment lines to the guard file beside the constant.
- Chosen: (b).
- Reason: `AGENTS.md` section "Documentation" asks for one location for each technical fact. The guard file is the one place that holds the verified commit.
- Risk: A later edit can separate the comment from the value. The guard fails when the pin changes, so the mismatch stays visible.
- Human decision: No.

## Remote Verification

Each row is one check. The blob SHA is the git blob of the file at the ref. Line numbers come from the content at that ref. Local files cited with line numbers have the same blob SHA as main.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Pull request 4886 head pins the reusable workflow to 2239e7b | `.github/workflows/auto-merge.yml` | `9e70001433bae97055b6bbe2825a345c0674273e` | `722925341108e8a273dc27abe287682f2c0d7512` | present | 61 |
| R-02 | Main pins the reusable workflow to d63a120 | `.github/workflows/auto-merge.yml` | main | `9d26134dd84cf50008a17fd878772102ce355983` | present | 61 |
| R-03 | Main sets the verified commit to d63a120 | `tests/guardrails/test_auto_merge_issue_close.py` | main | `54dfdc345dcd492a7df80fc243cf36a354b4556a` | present | 46 |
| R-04 | Main asserts that the pin equals the verified commit | `tests/guardrails/test_auto_merge_issue_close.py` | main | `54dfdc345dcd492a7df80fc243cf36a354b4556a` | present | 145 |
| R-05 | The root-and-contracts shard runs tests in `tests/guardrails` | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 255 |
| R-06 | The shard step named Run tests with coverage exists | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 304 |
| R-07 | The gate job is named pytest (coverage gate) | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 331 |
| R-08 | The gate step named Verify coverage shards exists | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 356 |
| R-09 | Bandit scans the repository root | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 451 |
| R-10 | The citation lint scans src and tests | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 702 |
| R-11 | The SpecKit task audit is advisory | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 750 |
| R-12 | The test-quality analyzer gate command is in CI | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 632 |
| R-13 | Ruff line length is 120 columns | `pyproject.toml` | main | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | present | 202 |
| R-14 | The reusable workflow at d63a120 has the blob SHA below | `.github/workflows/reusable-auto-merge.yml` in misthelper-devtools | `d63a120487cecf750184cb178387cdc25c0a7635` | `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` | present | 49 |
| R-15 | The reusable workflow at 2239e7b has the same blob SHA | `.github/workflows/reusable-auto-merge.yml` in misthelper-devtools | `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` | `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` | present | 49 |
| R-16 | The compare from d63a120 to 2239e7b changes no reusable workflow file | `.github/workflows/reusable-auto-merge.yml` in misthelper-devtools | compare from `d63a120487cecf750184cb178387cdc25c0a7635` to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` | `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` | present | 0 |
| R-17 | Constitution Principle I states the base-5 route | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 57 |
| R-18 | The copilot instructions state the route rule | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 159 |
| R-19 | The route script sets the base to 5 | `.specify/scripts/powershell/spec-route.ps1` | main | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 17 |
| R-20 | The route script joins the numbered route | `.specify/scripts/powershell/spec-route.ps1` | main | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 51 |
| R-21 | The route test checks the numbered route for a feature number | `tests/guardrails/test_spec_route_contract.py` | main | `b174399ad5f23f4844dc442954bf203be07342f3` | present | 478 |
| R-22 | The process folder guard limits each managed group to five children | `tests/guardrails/test_process_folder_structure.py` | main | `f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5` | present | 34 |
| R-23 | The baseline lists numbered as a managed root | `tests/guardrails/process_folder_baseline.json` | main | `f3eb8a7b6c62f3154ac6fa867a8948504818798b` | present | 7 |
| R-24 | The changelog rule allows no fragment for an internal-only change | `changelog.d/README.md` | main | `fcbde10e0c293390bd9df8d62a5d61f158eca384` | present | 58 |
| R-25 | AGENTS requires an inline comment on each executable line | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 99 |
| R-26 | AGENTS requires a preservation proof before a close | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 271 |
| R-27 | AGENTS defines the writing style | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 40 |
| R-28 | The spec template exists | `.specify/templates/spec-template.md` | main | `083ef123c7a2e56e21f3062173fb003258f927e2` | present | 0 |
| R-29 | The plan template exists | `.specify/templates/plan-template.md` | main | `1a54553bd85cbef2178aa55efbeeb0c1942ffdde` | present | 0 |
| R-30 | The tasks template exists | `.specify/templates/tasks-template.md` | main | `7e5170324d41a6736c498d6b9fc83651f31d0778` | present | 0 |
| R-31 | The checklist template exists | `.specify/templates/checklist-template.md` | main | `806657da09d1058823923e346a323b633114971a` | present | 0 |
| R-32 | The reference record spec file exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | `83b950279e45704943ad6942d23c8fc99cced492` | present | 0 |
| R-33 | The reference record research file exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | `2e4aaa714e56fff7f96a2af9e686e9f5c06224a7` | present | 0 |
| R-34 | The route folder for issue 4906 is absent | `specs/numbered/0/0/1/2/4/1/1/1` | main | none | absent | 0 |
| R-35 | No record for issue 4906 exists under specs | `specs` | main | none | absent | 0 |
| R-36 | The precedent commit set the pin to d63a120 | `.github/workflows/auto-merge.yml` | `11569e461fc6f025e502d54bf00b40213fae9654` | `9d26134dd84cf50008a17fd878772102ce355983` | present | 61 |
| R-37 | The precedent commit set the verified commit to d63a120 | `tests/guardrails/test_auto_merge_issue_close.py` | `11569e461fc6f025e502d54bf00b40213fae9654` | `54dfdc345dcd492a7df80fc243cf36a354b4556a` | present | 46 |
| R-38 | The quality gate issues come from the shared workflow call | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 1317 |
| R-39 | The worktree bootstrap commands are in the copilot instructions | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 28 |
| R-40 | A new worktree holds no `.venv`, so the bootstrap runs in each new worktree | `documentation/development-setup.md` | main | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 37 |
| R-41 | The test-quality analyzer procedure command is in the copilot instructions | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 127 |
| R-42 | The worktree naming convention is in the development setup guide | `documentation/development-setup.md` | main | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 181 |
| R-43 | AGENTS requires removal of the branch and the worktree after a merge | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 236 |
| R-44 | The container build runs on a push that changes a product file | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 473 |
| R-45 | The guard requires a full 40-character commit SHA in FULL_COMMIT | `tests/guardrails/test_auto_merge_issue_close.py` | main | `54dfdc345dcd492a7df80fc243cf36a354b4556a` | present | 45 |
| R-46 | The baseline test asserts 792 legacy entries | `tests/guardrails/test_process_folder_structure.py` | main | `f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5` | present | 136 |
| R-47 | The specs folder on main holds 795 direct entries, three of them managed roots (tree SHA) | `specs` | main | `224f0aa74b2ed841dadf30dc5a20d55adb0d388b` | present | 0 |
| R-48 | The baseline lists 792 grandfathered legacy entries | `tests/guardrails/process_folder_baseline.json` | main | `f3eb8a7b6c62f3154ac6fa867a8948504818798b` | present | 10 |

Row count: 48.

## Sources

### Repository (read only, local paths)

- `AGENTS.md`: full read, 353 lines. Lines 40, 99, 221 to 236, and 271 are cited.
- `.github/copilot-instructions.md`: full read, 600 lines. Lines 28 to 30, 50, 127 to 145, 159 to 162, 473, 501, and 540 are cited. Section "Git and GitHub in this repository" is cited by name.
- `.specify/memory/constitution.md`: full read, 562 lines. Lines 57 to 59 and 410 are cited.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`: full read.
- `.specify/scripts/powershell/spec-route.ps1`: lines 4 to 51 are cited.
- `.github/workflows/auto-merge.yml`: lines 53 and 61 are cited.
- `.github/workflows/ci.yml`: lines 9, 108, 242 to 255, 304 to 311, 330 to 331, 356, 375, 451, 632, 702, 750, 1293, and 1317 are cited.
- `tests/guardrails/test_auto_merge_issue_close.py`: lines 37 to 46, 132 to 145, and the 17 test functions are cited.
- `tests/guardrails/test_process_folder_structure.py`: lines 15 to 16, 27 to 34, 133 to 135, and 208 to 210 are cited.
- `tests/guardrails/test_spec_route_contract.py`: lines 15 and 464 to 478 are cited.
- `tests/guardrails/process_folder_baseline.json`: lines 4 to 10 are cited.
- `changelog.d/README.md`: lines 3 and 58 are cited.
- `pyproject.toml`: lines 201 to 202 and 558 to 559 are cited.
- `documentation/development-setup.md`: lines 32 and 37 (bootstrap for each new worktree) and line 181 (worktree naming) are cited. Read with grep and line views.
- `documentation/quality-gates.md`: read with grep for the auto-merge and pin terms. The record cites no line in this file.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`: the heading shape of `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and the design files was read. The content was not copied.

### Remote (GitHub, GET requests only, fetched with `gh`)

- Run and jobs: `https://github.com/jmorrison-juniper/MistHelper/actions/runs/45064239338`, read with `gh run view` and `--log-failed`.
- Issue fields: `https://api.github.com/repos/jmorrison-juniper/MistHelper/issues/4906`, read with `gh issue view`.
- Pull request fields: `https://api.github.com/repos/jmorrison-juniper/MistHelper/pulls/4886`, read with `gh pr view 4886`.
- Full tree: `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree holds 11404 entries, and the response is not truncated. Its direct entries under `specs/` number 795, and three managed roots are present: `live`, `numbered`, and `skills`. The `indexes` root is absent.
- Baseline content: `https://api.github.com/repos/jmorrison-juniper/MistHelper/contents/tests/guardrails/process_folder_baseline.json?ref=main`. The list `grandfathered_legacy_children` holds 792 entries.
- Contents: `https://api.github.com/repos/jmorrison-juniper/MistHelper/contents/.github/workflows/auto-merge.yml?ref=main`, and the same path at refs `9e70001433bae97055b6bbe2825a345c0674273e` and `11569e461fc6f025e502d54bf00b40213fae9654`.
- Contents: `https://api.github.com/repos/jmorrison-juniper/MistHelper/contents/tests/guardrails/test_auto_merge_issue_close.py?ref=main`, and the same path at ref `11569e461fc6f025e502d54bf00b40213fae9654`.
- Commits: `https://api.github.com/repos/jmorrison-juniper/MistHelper/commits/725fe5e79eb01eee742f5da0794bd53461be60a2`, `https://api.github.com/repos/jmorrison-juniper/MistHelper/commits/9e70001433bae97055b6bbe2825a345c0674273e`, `https://api.github.com/repos/jmorrison-juniper/MistHelper/commits/main`, and `https://api.github.com/repos/jmorrison-juniper/MistHelper/commits/11569e461fc6f025e502d54bf00b40213fae9654`.
- Upstream compare: the compare endpoint of `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/` with basehead `d63a120487cecf750184cb178387cdc25c0a7635` followed by `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` in three-dot form.
- Upstream contents: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-auto-merge.yml?ref=d63a120487cecf750184cb178387cdc25c0a7635`, and the same path at ref `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Upstream check runs: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/commits/2239e7bd468fd27e40c43f2b87fcd35a2e49672b/check-runs`. Every listed check reports success.
- Upstream commit: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/commits/d63a120487cecf750184cb178387cdc25c0a7635`. The commit message is "fix(auto-merge): dispatch after confirmed workflow-token merges (#87)".
- Related searches: `gh issue list` and `gh pr list` with the terms `reusable-auto-merge` and `verified`. Related closed items are issue 3487 and issue 3450. Related merged items are pull requests 4567, 4605, 4669, and 4815.

## Unverified

- U-1. The upstream test files at 2239e7b were not read. Their `tests` check reports success, but the file contents were not inspected. The record needs only the reusable workflow.
- U-5. Commit 725fe5e is a merge commit. Its two parents show this, but the Actions event definition for the commit SHA was not fetched. The record infers the relation from the parents.
- U-6. No remote code search ran for the old commit across the repository. A working tree search found the old commit at two lines only: `.github/workflows/auto-merge.yml` line 61 and the guard file line 46.
- U-7. A keyword scan of the 504-line reusable workflow found GitHub CLI calls and no pip, python, or checkout step. The scan did not parse the file fully.
- U-8. No local gate or test ran in this session. The rules of this session forbid build, test, and lint runs.
- U-9. No hosted run of the replacement pull request exists yet.

## Skills and Mist API

No skill was loaded. The change involves no Podman, container, Juniper device, or Mist API behavior.

The record makes no Mist API or mistapi claim. The mistapi package was not read.
