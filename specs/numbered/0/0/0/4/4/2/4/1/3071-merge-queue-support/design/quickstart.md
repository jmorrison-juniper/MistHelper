# Quickstart: Merge queue rollout and acceptance

Use PowerShell from the repository root. Each `gh` command in this file needs the preamble below. The preamble sets the host and copies the account token from the environment. It prints no value.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

The expected values below hold on 2026-11-26. A later reader compares the live value with the expected value and records the difference.

## 1. Read-only baseline and review rule

Read the `main` commit. Expect `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq '.object.sha'
```

Read branch protection. Expect `strict` true, 15 required contexts, and `required_pull_request_reviews` null.

```powershell
gh api repos/jmorrison-juniper/MistHelper/branches/main/protection --jq '{strict: .required_status_checks.strict, contexts: [.required_status_checks.checks[].context], required_pull_request_reviews: .required_pull_request_reviews}'
```

Read the reviews endpoint. Expect `1` on 2026-11-26. This value conflicts with the full protection read (R-53).

```powershell
gh api repos/jmorrison-juniper/MistHelper/branches/main/protection/required_pull_request_reviews --jq '.required_approving_review_count'
```

Read the GraphQL rule. Expect `requiresApprovingReviews` false on 2026-11-26 (R-53).

```powershell
gh api graphql -f query='query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { branchProtectionRules(first: 5) { nodes { pattern requiresApprovingReviews requiredApprovingReviewCount requiresStrictStatusChecks } } } }' -F owner=jmorrison-juniper -F name=MistHelper
```

Count rulesets. Expect `0`.

```powershell
gh api repos/jmorrison-juniper/MistHelper/rulesets --jq 'length'
```

Read the merge queue for `main`. Expect `"mergeQueue":null` before owner step O-3 (R-55).

```powershell
gh api graphql -f query='query($owner: String!, $name: String!, $branch: String!) { repository(owner: $owner, name: $name) { mergeQueue(branch: $branch) { id } } }' -F owner=jmorrison-juniper -F name=MistHelper -F branch=main
```

Confirm that the shared trigger exists on `main`. Expect the blob `d51efbc13c0f0a2076680030ed8be7ef7cf64523` for `ci.yml` and `2ef072fbddd473f841c5877f4d89b7c7760aeaf0` for `codeql.yml` (R-01, R-10).

```powershell
gh api 'repos/jmorrison-juniper/MistHelper/contents/.github/workflows/ci.yml?ref=main' --jq '.sha'
gh api 'repos/jmorrison-juniper/MistHelper/contents/.github/workflows/codeql.yml?ref=main' --jq '.sha'
```

Confirm that the absent instruction path stays absent. Expect no output (R-42).

```powershell
gh api 'repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1' | ConvertFrom-Json | ForEach-Object { $_.tree } | Where-Object { $_.path -eq '.github/instructions/git-flow-multi-agent.instructions.md' }
```

## 2. Guard check for the documentation change

Run the new guard method before T004. Expect one failed test. The `ci.yml` row at line 467 omits the candidate text (R-27).

```powershell
python -m pytest tests/guardrails/test_ci_gate_triggers.py -k queue_docs -q
```

Run the same command after T004. Expect one passed test.

## 3. Local gates

Run the gates in T-LOCAL-GATES in this order. Record each command and its result in the pull request body.

```powershell
python -m pytest tests/guardrails/test_ci_gate_triggers.py -q
python -m pytest tests/guardrails -q
python -m ruff check .
python -m black --check .
radon cc tests/guardrails/test_ci_gate_triggers.py -j | complexity-gate --max 10
bandit -c pyproject.toml -r . -q
symbol-diff --base origin/main tests/guardrails/test_ci_gate_triggers.py
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/spec.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/plan.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/tasks.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/analysis.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/research.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/data-model.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/quickstart.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/contracts/workflows.md specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/checklists/requirements.md
markdown-link-check .github/copilot-instructions.md documentation/quality-gates.md
git diff --check
git diff --name-only origin/main -- .github/workflows
```

The last command must print no path (FR-010).

## 4. Owner verification after owner step O-3

Read the merge queue runs on the candidate branch. Expect a `merge_group` event for each required workflow.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --json databaseId,event,headBranch,headSha,conclusion,status --limit 10
gh run list -R jmorrison-juniper/MistHelper --workflow codeql.yml --json databaseId,event,headBranch,headSha,conclusion,status --limit 10
```

Read the check runs on the newest `merge_group` run of `ci.yml`. Expect each of the 15 required contexts to report `success`. Treat `cancelled`, `timed_out`, `stale`, `skipped`, and a missing context as unresolved.

```powershell
$queueRuns = gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --json event,headSha | ConvertFrom-Json
$queueSha = ($queueRuns | Where-Object { $_.event -eq 'merge_group' } | Select-Object -First 1).headSha
gh api "repos/jmorrison-juniper/MistHelper/commits/$queueSha/check-runs" | ConvertFrom-Json | ForEach-Object { $_.check_runs } | ForEach-Object { "$($_.name) $($_.conclusion)" }
```

The first two lines select the commit of the newest queue run. The third line prints one row for each check run on that commit.

Read the merged pull request. Set `$candidateNumber` to the pull request number of the candidate that the owner added to the queue.

```powershell
gh pr view $candidateNumber -R jmorrison-juniper/MistHelper --json state,mergedAt,mergeCommit
```

Read the main run that follows the merge.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --branch main --limit 3 --json databaseId,headSha,conclusion,status
```

## 5. Evidence comment template

The owner posts one comment on issue #3071 for each verification candidate. Each field holds an observed value.

```text
Verification candidate: pull request number, title, and head commit SHA
Queue commit SHA: observed value
merge_group runs: run IDs for ci.yml and codeql.yml, with conclusions
Required contexts on the queue commit: each name with its conclusion (15 names)
Merge commit SHA: observed value
Main run ID after the merge: observed value, with conclusion
Recorded time (UTC, ISO 8601): observed value
```
