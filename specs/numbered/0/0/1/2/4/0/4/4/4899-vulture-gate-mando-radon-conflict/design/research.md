# Research: Vulture Gate Mando Radon Conflict (Issue 4899)

## Reproduction From CI Logs

Read-only evidence. Each fact uses a GET request or a log read as its source.

- Issue #4899 is open. The GitHub Actions bot created it on 2026-11-22 at 20:16 UTC. Labels: `bug`, `ci`, `quality-gate`. Title: `CI: quality-gate vulture failed (PR #4888)`.
- The issue body names pull request #4888, branch `dependabot/pip/mando-0.8.2`, and commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`.
- Pull request #4888 is open. It changes one file: `requirements-dev.txt`, with one addition and one deletion. Its head commit is `e86098cdc2b189d217805b3b4060ef609cbc37af`.
- A search for `4899` in pull requests returns an empty list. No pull request names this issue.
- Run 45064243269 (workflow `Quality Gates`) ran on the `pull_request` event. Its attempt number is 1, and its conclusion is failure.
- Job 137336718674 (`Vulture (dead code)`) concluded failure. Step 4, `Run pip install -r requirements-dev.txt`, failed. Step 5, `Detect dead code`, was skipped.
- The job checked out merge commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`. That commit merges `e86098cd` into base `00d9a16e998b0cb5e10b6ed77da0fa909670d64f`.
- The failed log holds 606 lines. Lines 559 to 573 hold the resolver error:

```text
ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.
The user requested mando==0.8.2
radon 6.0.1 depends on mando<0.8 and >=0.6
ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
##[error]Process completed with exit code 1.
```

- The log holds no vulture output. The vulture scan never ran. The failing rule is the pip resolver rule `ResolutionImpossible`.
- The same resolver line appears in 26 failed jobs of the run. The job names follow.
  - Bandit (security)
  - Black (format check)
  - Citation reference lint
  - CodeQL verdict register check
  - Dependency lock and exports
  - Diagram reference lint
  - E2E shard (upgrade-portal)
  - E2E shard (web-portal)
  - E2E shard (websockets-tab)
  - Interrogate (docstring coverage)
  - mypy (strict)
  - pip-audit (CVE scan)
  - pydocstyle (docstring style)
  - Pylint (score gate)
  - pytest coverage shard (root-and-contracts)
  - pytest coverage shard (root-units)
  - pytest coverage shard (upgrade-contracts)
  - pytest coverage shard (upgrade-units)
  - Quality exclusion drift (advisory)
  - Radon (complexity)
  - Ruff (lint)
  - Ruff (ops platform)
  - SpecKit task audit (advisory)
  - Test quality ratchet (gate)
  - Upgrade portal journeys
  - Vulture (dead code)
- Two more failed jobs are downstream. `pytest (coverage gate)` reports a failed dependency lock job. `E2E smoke tests` reports failed E2E shards.
- Main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Its latest Quality Gates run, 45774119357, concluded success. Its Vulture, Radon, and Dependency lock and exports jobs concluded success.
- Base commit `00d9a16e` and merge commit `5bb4b385` both exist on GitHub. The base `ci.yml` blob equals the main blob (RC-08).

## Decisions

### D-1 Fix layer: Dependabot ignore rule

- **Chosen**: Add an `ignore` rule for `mando` with versions `>= 0.8` to the pip stream of `.github/dependabot.yml`.
- **Alternatives**:
  - Upgrade `radon` so that it accepts `mando` 0.8. Rejected. No radon release accepts it (RC-41, RC-42, RC-43).
  - Replace `radon` in `requirements-dev.txt`. Rejected. It changes the radon gate and its documented limit.
  - Install `vulture` outside the pinned file. Rejected. It breaks the pin policy that the `pinned (issue #1779)` comments record (RC-04).
  - Close pull request #4888 only. Rejected. The weekly pip run reopens the same bump (RC-15).
- **Reason**: This is the smallest change that stops the recurrence. It keeps every pin and every gate.
- **Risk**: A later `mando` fix waits until radon accepts `mando` 0.8. The removal condition appears in two files to limit this risk.

### D-2 Pins: keep mando 0.7.1

- **Chosen**: Keep `mando==0.7.1` in `requirements-dev.txt` and in `uv.lock` (RC-01, RC-11).
- **Alternative**: Accept `mando==0.8.2` and regenerate `uv.lock`. Rejected. The resolver cannot satisfy `radon==6.0.1` with that pin (RC-44).
- **Risk**: None for this scope.

### D-3 Test location: existing policy guard

- **Chosen**: Add the rule to the snapshot and add two cases to `tests/guardrails/test_pr_title_workflow.py`, class `TestDependabotPolicy`.
- **Alternative 1**: Create a new guard file in `tests/guardrails`. Rejected. The folder holds 79 direct children (RC-37), and Principle I forbids a new child there (RC-28).
- **Alternative 2**: Create a new file in another test folder. Rejected. A new module for two cases adds structure without added coverage.
- **Risk**: The policy file covers a second concern. The class name and its docstring still describe the policy.

### D-4 Release-note fragment: add one file

- **Chosen**: Add `changelog.d/issue-4899-mando-radon-pin.md`.
- **Alternative**: Add no fragment and state an internal-only reason in the pull request body (RC-25).
- **Reason**: The constitution requires one fragment for each change (RC-26). The constitution supersedes practice documents (RC-27).
- **Risk**: A reviewer reads the README rule as an exception. The analysis names this conflict.

### D-5 Documentation: guide note and rule comment

- **Chosen**: Add one paragraph to `documentation/quality-gates.md` after the job table. Add a comment to the rule in `.github/dependabot.yml`.
- **Alternative**: Add the comment only. Rejected. `AGENTS.md` requires an update of directly related documentation (section "Documentation", RC-34 context at line 336).
- **Risk**: The two texts drift apart. Both state the same removal condition.

### D-6 Closing pull request #4888

- **Chosen**: Close pull request #4888 after the fix merges. Add a comment that names the fix pull request.
- **Alternatives**:
  - Close it now. Rejected. The thread leaves before the fix passes CI.
  - Rebase it onto the fix. Rejected. The rebased pull request keeps `mando==0.8.2`, so the conflict returns.
  - Leave it open. Rejected. Its checks stay red.
- **Caution**: Closing the pull request is recoverable. A person reopens it on GitHub.
- **Risk**: A reviewer misses the link. The comment names the fix pull request.

### D-7 Branch, title, and labels

- **Chosen**: Branch `fix/4899-vulture-gate-mando-radon-conflict`. Title `fix(ci): ignore mando 0.8 updates that radon 6.0.1 rejects`. Add `in-progress`. Keep `bug` and `ci`.
- **Alternative**: Use type `chore`, which the pip prefix uses (RC-32). Rejected. The change repairs a failing gate, and the issue carries the `bug` type label (RC-33).
- **Risk**: None for this scope.

### D-8 Ignore syntax

- **Chosen**: `versions: [">= 0.8"]`, a Python package specifier range.
- **Alternative 1**: `update-types`. Rejected. The GitHub docs define update types by SemVer level and do not state how 0.x releases map (RC-45, lines 430 to 436).
- **Alternative 2**: `versions: ["0.8.x"]`. Rejected. It covers the 0.8 series only, and 0.9 stays open.
- **Risk**: Dependabot rejects the range. Unverified item U-1 covers this risk.

### D-9 Other failed jobs

- **Chosen**: The fix addresses the shared resolver conflict. The fix pull request runs every job again.
- **Alternative**: Open one issue for each failed job. Rejected. Twenty-six jobs share one resolver line, and one issue holds one concern (AGENTS.md, section "Issue first").
- **Risk**: A job has a second cause. TEST-007 detects a resolver line only. Any other cause needs a new issue.

## Remote Verification

Repository checks use `main` unless the Ref column names another ref. The recursive tree of `main` or the contents API gives each blob SHA. Line numbers are 1-based.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | `requirements-dev.txt` pins `mando==0.7.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-02 | `requirements-dev.txt` pins `radon==6.0.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-03 | Merge commit input pins `mando==0.8.2` | `requirements-dev.txt` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RC-04 | Vulture job installs `requirements-dev.txt` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 563 |
| RC-05 | Vulture job runs vulture with both env values | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 565 |
| RC-06 | `VULTURE_PATHS` is `src/ MistHelper.py wsgi.py web_portal` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-07 | `VULTURE_CONFIDENCE` defaults to 70 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 127 |
| RC-08 | Base commit holds the same Vulture job file | `.github/workflows/ci.yml` | 00d9a16e998b0cb5e10b6ed77da0fa909670d64f | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 563 |
| RC-09 | Dependency lock job runs `uv lock --check` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-10 | Dependency lock job runs the export guard | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| RC-11 | `uv.lock` pins `mando` 0.7.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-12 | `uv.lock` lists `mando` as a dependency of `radon` 6.0.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RC-13 | `pyproject.toml` declares `radon==6.0.1` in the development extra | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RC-14 | Pip stream holds no ignore rule | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 11 |
| RC-15 | Pip stream checks for updates weekly | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 6 |
| RC-16 | Policy snapshot holds the pip stream | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 23 |
| RC-17 | Policy guard reads `.github/dependabot.yml` | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 278 |
| RC-18 | Policy guard compares the whole policy with the snapshot | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RC-19 | Mutation list starts in `test_unrelated_changes_fail` | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 302 |
| RC-20 | Changelog guard allows the issue-number name form | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-21 | Changelog guard lists five change types | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| RC-22 | Complexity guard reads `documentation/quality-gates.md` | `tests/guardrails/test_complexity_gate_limit.py` | main | 7e15fc70d292e52c134841f3c17aa3e7135a3749 | present | 34 |
| RC-23 | Vulture row states zero findings at confidence 70 | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 60 |
| RC-24 | No note on the vulture install step exists | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | absent | 74 |
| RC-25 | README rule 4 allows no fragment for an internal-only change | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-26 | Constitution requires one fragment for each change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-27 | Constitution supersedes other practice documents | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| RC-28 | Constitution Principle I states the five-item rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-29 | Local gates table lists the Dead code row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 70 |
| RC-30 | Local gates table lists the STE row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-31 | Local gates table lists the Tests row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-32 | Pip updates use the `chore` prefix | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 531 |
| RC-33 | Type labels include `bug` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 438 |
| RC-34 | Each Markdown file passes the STE gate | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-35 | Development setup installs `requirements-dev.txt` with pip | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |
| RC-36 | Container build runs only on listed product paths | `.github/workflows/container-build.yml` | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| RC-37 | `tests/guardrails` holds 79 direct children | `tests/guardrails` | main | 17c7b7f3c0ec8acc4c4d338ea27a8eb1fa2203da | present | 0 |
| RC-38 | Reference record shows the record shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-39 | No record exists at route `0/0/1/2/4/0/4/4` | `specs/numbered/0/0/1/2/4/0/4/4` | main | none | absent | 0 |
| RC-40 | No fragment exists yet for issue 4899 | `changelog.d/issue-4899-mando-radon-pin.md` | main | none | absent | 0 |
| RC-41 | Upstream radon pins `mando` to `>=0.6,<0.8` | `pyproject.toml` in `rubik/radon` | master | c25f1bd8b9a33b508b8600714e813db764841f7f | present | 11 |
| RC-42 | Upstream newest tag is `v6.0.1` | `refs/tags/v6.0.1` in `rubik/radon` | v6.0.1 | 5061d86a649223bdc5490c5dcc113743cc5b47f5 | present | 0 |
| RC-43 | PyPI shows radon 6.0.1 as the project version | `https://pypi.org/project/radon/` | pypi | not applicable | present | 0 |
| RC-44 | Local radon 6.0.1 metadata requires `mando` below 0.8 | `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` | local checkout | not applicable | present | 31 |
| RC-45 | GitHub docs define `versions` as package manager ranges | `content/code-security/reference/supply-chain-security/dependabot-options-reference.md` in `github/docs` | main | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 420 |
| RC-46 | Commit 5bb4b385 exists on GitHub | `repos/jmorrison-juniper/MistHelper/commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | not applicable | present | 0 |
| RC-47 | Commit 00d9a16e exists on GitHub | `repos/jmorrison-juniper/MistHelper/commits/00d9a16e998b0cb5e10b6ed77da0fa909670d64f` | 00d9a16e998b0cb5e10b6ed77da0fa909670d64f | not applicable | present | 0 |

## Sources

Local files, read from the read-only repository:

- `AGENTS.md`, read in full. Git flow starts at line 179. Documentation starts at line 336. Specifications start at line 345.
- `.github/copilot-instructions.md`, read in full. Local gates start at line 50. The test quality ratchet starts at line 95.
- `.specify/memory/constitution.md`, read in full. Principle I starts at line 38. Governance starts at line 526.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. The reference record holds four root files and a `design` folder with `checklists`, `contracts`, and three documents. The reference `spec.md` and `tasks.md` set the heading and task shape. No content is copied.
- `documentation/quality-gates.md`, read in full.
- `changelog.d/README.md`, read in full.
- `documentation/development-setup.md`, `architecture.md`, `container-deployment.md`, and `operator-guide.md`, searched for `requirements-dev`, `vulture`, `radon`, `dependabot`, and `mando`. Only `development-setup.md` line 137 and `architecture.md` line 167 match. Architecture, container deployment, and operator guide do not change.
- `tests/guardrails/test_pr_title_workflow.py`, `test_changelog_fragment_policy.py`, and `test_complexity_gate_limit.py`, read in ranges that hold the cited lines.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` and `mando-0.7.1.dist-info\METADATA`, read in ranges that hold the cited lines.
- The skill tool loaded no skill. No Podman, container, or Juniper device behavior applies.
- This review did not read the Mist API documents named in the brief or the pinned `mistapi` package. This change sends no Mist request and calls no SDK function, so they do not apply.

GitHub reads (GET only):

- `gh issue view 4899 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author`.
- `gh pr list -R jmorrison-juniper/MistHelper --state all --search 4899 --json number,title,state,url` (empty result).
- `gh pr view 4888 -R jmorrison-juniper/MistHelper --json files,body,state,mergedAt,headRefName,statusCheckRollup`.
- `gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336718674 --log-failed`.
- `gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137336718674` and `gh api repos/jmorrison-juniper/MistHelper/actions/runs/45064243269`.
- `gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs,headSha,conclusion`.
- `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`, with 11,404 entries and no truncation.
- The contents API with a file path and a ref, decoded from base64 for the cited lines.
- The commits API for `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` and `00d9a16e998b0cb5e10b6ed77da0fa909670d64f`.
- `gh issue view 1779` and `gh issue view 892`. Both are closed. `gh issue list --label quality-gate --state open` lists the sibling issues.
- `gh api repos/rubik/radon/contents/pyproject.toml` (default branch `master`), `gh api repos/rubik/radon/tags?per_page=5`, `gh api repos/rubik/radon/releases/latest` (HTTP 404, no release), and `gh api repos/github/docs/contents/content/code-security/reference/supply-chain-security/dependabot-options-reference.md?ref=main`.

Web source:

- `https://pypi.org/project/radon/` through the web fetch tool. The page shows version 6.0.1 and states that mando is required for the command-line interface.

## Unverified

- U-1: Dependabot accepts `versions: [">= 0.8"]` at runtime. Reason: the docs define the pattern class, but no Dependabot run has read the new file. Check the first run after the merge (SC-004).
- U-2: The fix pull request passes CI. Reason: the branch and the pull request do not exist yet. TEST-006, TEST-007, and TEST-008 check the result.
- U-3: The local gates pass for the changed files. Reason: the drafting rules forbid running gates. Task T-LOCAL-GATES records the results.
- U-4: A resolver run on the fix branch succeeds. Reason: the drafting rules forbid installs. TEST-007 checks the remote log.
- U-5: The 26 failed jobs have no second cause. Reason: the review read only the resolver line of each job. TEST-007 checks the fix pull request run.
- U-6: A future radon release accepts `mando` 0.8. Reason: no such release appears in the sources read (RC-41, RC-42, RC-43). Check at each Dependabot run.
- U-7: The two Windows checks in runs 45064235051 and 45064235097 fail for the same cause. Reason: their logs were not read. Both are out of scope.
- U-8: Open issues 4906, 4907, and 4908 relate to pull requests #4886, #4889, and #4890. Reason: their logs were not read. They are out of scope.
- U-9: Closing pull request #4888 stops the same bump from reopening. Reason: Dependabot behavior after a manual close is not observed. Check after the merge.
