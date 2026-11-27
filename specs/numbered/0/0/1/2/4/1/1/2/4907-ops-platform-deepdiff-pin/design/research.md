# Research: Ops Platform Deepdiff Pin

Each decision lists the chosen option, the alternatives, the reason, and the risk. Each remote claim has one row in the table below. Each row holds a path, a SHA, a result, and a line. Line 0 means that no line applies.

## Trace: how the failure happens

1. The job `pytest (ops platform)` (`.github/workflows/ci.yml` line 1122) sets its working directory to `mist-ops-platform` (lines 1139 to 1141). Each `requirements.txt` in that job means `mist-ops-platform/requirements.txt`.
2. The step `Install dependencies` runs `pip install -r requirements.txt -e ".[dev]" -r requirements-dev.txt` (line 1162). On the PR head, the pin on line 56 of `mist-ops-platform/requirements.txt` is `deepdiff==9.2.1` (PR #4889 changes only that file, plus one line).
3. The editable install of `.[dev]` reads `mist-ops-platform/pyproject.toml`. Line 31 declares `deepdiff>=8.6.2,<9.0`.
4. pip cannot satisfy both requirements. The log shows `ERROR: Cannot install None and deepdiff==9.2.1` and `ERROR: ResolutionImpossible`. The step exits with code 1. The steps `Confirm the suite collects its tests`, `Run tests with coverage`, and `Report job timeout` are skipped. The log holds no pytest marker.
5. The consumers of the library are `mist-ops-platform/src/shared/services/diff.py` (line 13 imports `DeepDiff`, line 107 calls it, line 110 passes `ignore_order=True`) and `mist-ops-platform/tests/integration/test_drift.py` (line 36 constructs `DiffService`). Neither runs in the failed job.

Root cause: Dependabot changed one of two declarations of the same package. The declared constraint on line 31 did not change.

## Decisions

### D-1. Keep deepdiff at 8.6.2 under the declared constraint

- **Decision**: Keep the pin `deepdiff==8.6.2` and the constraint `deepdiff>=8.6.2,<9.0`. Do not adopt 9.2.1 in this change.
- **Alternatives considered**:
  - Widen the constraint to include 9.x and adopt 9.2.1. Rejected. The runtime effect is unverified (U-4). The constraint came from a deliberate commit (row 42).
  - Push a fix to branch `dependabot/pip/deepdiff-9.2.1`. Rejected. `AGENTS.md` line 254 forbids a push to a branch that another agent owns.
  - Leave PR #4889 open and failing. Rejected. The conflict stays unresolved.
- **Rationale**: The constraint and its comment state the intent (row 10). `DiffService` documents 8.x behavior (row 14) and passes `ignore_order=True` (row 15). The release notes quoted in PR #4889 describe output changes for `ignore_order` and new `to_dict` defaults.
- **Risk**: The project stays on the 8.x line. A later advisory for deepdiff 8.x reaches the dependency audit only through the pinned version.

### D-2. Add one test method to the existing dependency guard

- **Decision**: Add `test_ops_platform_pins_obey_declared_constraints` to class `TestDependencyExport` in `tests/guardrails/test_dependency_export.py`.
- **Alternatives considered**:
  - A new file under `tests/guardrails`. Rejected. The folder holds 79 direct children (row 39), so a new file adds a child to a grandfathered parent.
  - A new file under `mist-ops-platform/tests`. Rejected. The ops job fails at install (row 4), so its tests never run in a failed pipeline. The root shard runs its own `tests` paths (row 9).
  - A new CI job. Rejected. It changes a workflow, which FR-005 forbids.
- **Rationale**: The job `Dependency lock and exports` already runs this file on each pull request (row 8). It passed on PR #4889, which shows that it lacks this check (F1 in `analysis.md`).
- **Risk**: The class reaches the limit of five methods. A later guard needs a compliant package.

### D-3. Close PR #4889 after the change merges

- **Decision**: After the change merges, close PR #4889 unmerged. The closing comment holds the reason and the preservation proof. Do not change `.github/dependabot.yml`.
- **Alternatives considered**:
  - Leave PR #4889 open and red. Rejected. The conflict persists.
  - Add a Dependabot ignore for deepdiff 9.x to `.github/dependabot.yml`. Rejected. No stream covers `/mist-ops-platform` (row 20), so the ignore would not apply to the pull request. The policy test also pins the three streams (row 21).
  - Post a Dependabot command comment. Rejected for now. The command effect is unverified (U-3).
  - Merge PR #4889 with the constraint widened. Rejected by D-1.
- **Rationale**: `AGENTS.md` line 271 allows closing an unmerged pull request with a preservation proof. The branch keeps commit `9d4640661fa40b1e0a7809f46a0007eff7add517` (row 41).
- **Risk**: `.github/copilot-instructions.md` line 533 says not to close update pull requests. This record limits that rule to title remedies (F6 in `analysis.md`). Dependabot may reopen a 9.x pull request (U-3). The guard then fails that pull request in the dependency job.

### D-4. Add one changelog fragment

- **Decision**: Add `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`.
- **Alternatives considered**:
  - No fragment, under the internal-only exemption in `changelog.d/README.md` line 58. Rejected. The constitution requires one fragment for each change (row 26), and it supersedes practice documents (row 27).
  - A fragment named `pr-<number>.md`. Rejected for now. The pull request does not exist when the file is created. `changelog.d/README.md` lines 24 to 28 give the issue-based name first.
- **Rationale**: A CI change already carries a fragment (row 24).
- **Risk**: The constitution says a fragment triggers the full pipeline (line 175). That link is open question U-6.

### D-5. Record that no container build starts

- **Decision**: Record the result at T-MERGE. The expected result is no `container-build.yml` run for the merge commit.
- **Alternatives considered**:
  - Add a product path to start a build. Rejected. An unrelated product change would satisfy a trigger.
  - Wait for a build that never starts. Rejected. The merge would wait without end.
- **Rationale**: The push trigger lists product paths only (row 35).
- **Risk**: Constitution steps 10 to 12 do not run for this change (F7 in `analysis.md`). The owner must confirm the result (U-6).

### D-6. Add no dependency

- **Decision**: Parse the constraints with `tomllib`. Parse the requirements with `packaging`, which both root requirements files already pin.
- **Alternatives considered**:
  - Regular expressions for `pyproject.toml`. Rejected. They fail on extras and on comments.
  - A new parsing package. Rejected. It adds a pin and a lock change.
- **Rationale**: `tomllib` ships with Python 3.11 and later, and the runner uses Python 3.15 (row 11). `packaging` is pinned in both root files (row 22).
- **Risk**: The guard fails at import if `packaging` leaves `requirements-dev.txt`. That failure is loud, so no silent pass occurs.

## Remote verification table

Result values: `present`, `absent`, `partial`, or `stale`. All rows use the remote head `main` (`f03c6c9`), except the commit rows and the upstream row. The table holds 44 rows, and `STATUS.json` lists the same 44 rows.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
|---|-------|------|-----|----------|--------|------|
| 1 | CI defines job `ops_platform_pytest` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1122 |
| 2 | CI names the job `pytest (ops platform)` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1123 |
| 3 | CI runs the ops job in `mist-ops-platform` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1141 |
| 4 | CI install step installs `requirements.txt` and the editable dev extra | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1162 |
| 5 | CI sets the ops coverage floor to 56 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 116 |
| 6 | CI sets the ops collected-test floor to 390 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 121 |
| 7 | Job `quality_gate_issues` depends on `ops_platform_pytest` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1311 |
| 8 | Job `dependency_lock` runs the export guard test file | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| 9 | Root-and-contracts shard collects `tests/guardrails` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| 10 | Ops `pyproject.toml` declares `deepdiff>=8.6.2,<9.0` | `mist-ops-platform/pyproject.toml` | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 31 |
| 11 | Ops `pyproject.toml` sets `requires-python` to `>=3.15` | `mist-ops-platform/pyproject.toml` | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 13 |
| 12 | Ops `requirements.txt` pins `deepdiff==8.6.2` | `mist-ops-platform/requirements.txt` | main | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | present | 56 |
| 13 | `DiffService` imports `DeepDiff` | `mist-ops-platform/src/shared/services/diff.py` | main | 78aa5f55ee735da782aa6ffe828c96d8627ecdb1 | present | 13 |
| 14 | `DiffService` documents deepdiff 8.x behavior | `mist-ops-platform/src/shared/services/diff.py` | main | 78aa5f55ee735da782aa6ffe828c96d8627ecdb1 | present | 97 |
| 15 | `DiffService` passes `ignore_order=True` to `DeepDiff` | `mist-ops-platform/src/shared/services/diff.py` | main | 78aa5f55ee735da782aa6ffe828c96d8627ecdb1 | present | 110 |
| 16 | Architecture note R-05 records deepdiff 8.x | `mist-ops-platform/docs/architecture.md` | main | 2336031ed31b99d4f5170c2676795a52ccca8a38 | present | 78 |
| 17 | Drift integration test constructs `DiffService` | `mist-ops-platform/tests/integration/test_drift.py` | main | 5054b14a21a9746757762e1f5b432a450470e5ef | present | 36 |
| 18 | Gate trigger guard maps `ops_platform_pytest` to its job name | `tests/guardrails/test_ci_gate_triggers.py` | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 197 |
| 19 | Quality gate document lists the ops platform thresholds | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 70 |
| 20 | Dependabot policy has no update stream for `/mist-ops-platform` | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 0 |
| 21 | Dependabot policy test asserts exactly three update streams | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 299 |
| 22 | Root dev requirements pin `packaging` 26.3 | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 228 |
| 23 | Export guard test class holds four test methods | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 98 |
| 24 | An earlier CI change added a changelog fragment (precedent) | `changelog.d/issue-3071-merge-queue-support.md` | main | d88735dbdf2e32e92875c67a7f62b94c0b2d47e5 | present | 0 |
| 25 | Changelog README exempts internal-only changes from a fragment | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 26 | Constitution requires one fragment for each change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 27 | Constitution supersedes practice documents | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| 28 | Constitution requires the deployment pipeline after any code change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 145 |
| 29 | PR template requires one release note fragment | `.github/PULL_REQUEST_TEMPLATE.md` | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 36 |
| 30 | Instructions forbid closing update pull requests in the title section | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| 31 | Instructions list the ops platform gate row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 76 |
| 32 | AGENTS requires a preservation proof before closing an unmerged pull request | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| 33 | AGENTS requires a guard to count inputs and fail on unreadable input | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 142 |
| 34 | AGENTS requires the branch name `<type>/<issue>-<slug>` | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| 35 | Container build workflow limits its push trigger to product paths | `.github/workflows/container-build.yml` | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| 36 | STE workflow grades five named files and no specs file | `.github/workflows/ste-lint.yml` | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 44 |
| 37 | Route folder for this record is absent on main | `specs/numbered/0/0/1/2/4/1/1/2` | main | n/a | absent | 0 |
| 38 | No record folder named 4907 exists under `specs` | `specs/**/4907-*` | main | n/a | absent | 0 |
| 39 | The folder `tests/guardrails` holds 79 direct children | `tests/guardrails` | main | n/a | present | 0 |
| 40 | Issue commit `fd94cfcb` exists and has two parents | `commits/fd94cfcb82ba9020f526f06a8c7bf8d4fb73a77e` | commit | fd94cfcb82ba9020f526f06a8c7bf8d4fb73a77e | present | 0 |
| 41 | Run head commit `9d464066` exists as the PR head | `commits/9d4640661fa40b1e0a7809f46a0007eff7add517` | commit | 9d4640661fa40b1e0a7809f46a0007eff7add517 | present | 0 |
| 42 | Commit `23379f0e0` introduced the declared constraint | `commits/23379f0e075557cd5c0761a79f23ad8d3583e296` | commit | 23379f0e075557cd5c0761a79f23ad8d3583e296 | present | 0 |
| 43 | cachebox page states Python 3.10 and later, with no Python 3.15 statement | `https://pypi.org/project/cachebox/` | upstream | n/a | partial | 0 |
| 44 | Reference record analysis file exists on main | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md` | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |

Row 39 holds the count of 79 direct children from the tree listing. The list of direct children includes both files and folders.

## Sources

- Local files read in the checkout. The checkout matches remote head `f03c6c9`.
  - Read in full: `AGENTS.md`, `.github/copilot-instructions.md` (601 lines), `.specify/memory/constitution.md` (563 lines), and the four templates in `.specify/templates/`.
  - Read in part: `documentation/quality-gates.md` (lines 1 to 100 of 293) and the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`.
- Remote file bodies, read with `gh api repos/jmorrison-juniper/MistHelper/git/blobs/<sha>` using the SHA from `git/trees/main?recursive=1`. The tree call returned 11,404 entries, and its `truncated` flag is `false`.
- Commit metadata and comparisons: `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>` and the compare endpoint for base `main` and head `<sha>`. Commit `fd94cfcb` is 2 commits ahead and 7 behind `main`. Commit `9d464066` is 1 commit ahead and 7 behind.
- Run data: `gh run view 45064277976 -R jmorrison-juniper/MistHelper --json jobs,headSha` and `--log-failed`. Run `45774119357` on `main` (event `workflow_dispatch`, head `f03c6c9`, conclusion success) with job `pytest (ops platform)` (job 139753527584, conclusion success).
- Pull request data: `gh pr view 4889 -R jmorrison-juniper/MistHelper --json files,statusCheckRollup,body`. PR #4889 changes one file, `mist-ops-platform/requirements.txt`, with one addition and one deletion. Its check `Dependency lock and exports` reports success, and its check `pytest (ops platform)` reports failure.
- Search hit: `gh pr list --search "4907"` returned PR #4438, which is merged. Its body contains a link to an unrelated upstream pull request numbered 4907. It is not linked to issue 4907.
- Local git, read only. `git log -S` found the commit that added the declared constraint.
  - `git show -s --format=%B 23379f0e0` gives no reason for the constraint.
  - `git show 00d9a16e:.github/dependabot.yml` lists the streams `/` and `/ops-portal` only.
  - `git grep -n -i deepdiff` finds no documentation hit.
- URLs: `https://github.com/jmorrison-juniper/MistHelper/pull/4889` (read through `gh`), `https://github.com/jmorrison-juniper/MistHelper/actions/runs/45064277976` (the issue run), `https://github.com/jmorrison-juniper/MistHelper/actions/runs/45774119357` (the main run), and `https://pypi.org/project/cachebox/` (fetched. The text was truncated after the summary section).
- The release notes quoted in the PR #4889 body cite `https://github.com/qlustered/deepdiff/releases`. This record did not fetch that page directly.

## Applicability

- Documents read in full: `AGENTS.md`, `.github/copilot-instructions.md`, the constitution, and the four `.specify` templates.
- Documents read in part: `documentation/quality-gates.md` (the ops gate rows), and the reference record.
- Documents not read: `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`. Reason: `git grep` found no `deepdiff` hit in `documentation/`, and no hit for `mist-ops`, `ops platform`, or `ops_platform` other than `quality-gates.md` and one runbook.
- Skills: none loaded. Reason: no Podman behavior, Juniper device behavior, or Mist API behavior is in scope.
- Mist API OpenAPI files: not read. Reason: no endpoint behavior is in scope.
- mistapi source: not read. Reason: the change makes no mistapi call and changes no mistapi pin.

## Unverified

- U-1: Whether cachebox 6.1.2 and later install on Python 3.15 for this project. The only support for this claim is the release-notes quote in the PR #4889 body. The PyPI page read for row 43 states Python 3.10 or later and no 3.15 statement. No wheel listing was read.
- U-2: Which Dependabot update stream opened PR #4889 for `mist-ops-platform/requirements.txt`. Row 20 and the base commit both show no `/mist-ops-platform` stream.
- U-3: Whether Dependabot reopens a 9.x pull request after PR #4889 closes, and whether a Dependabot command comment blocks it. Reason: no Dependabot document was read. The fetch of the GitHub documentation failed with `WebFetchBlockedUrlError`.
- U-4: The runtime effect of deepdiff 9.2.1 on `DiffService`. Reason: the read-only rule forbids a test run. The release notes list output changes for `ignore_order` and `to_dict`.
- U-5: The result of `uv lock --check` on the change pull request. Reason: the check runs in CI (`.github/workflows/ci.yml` lines 647 and 648), and no local run is allowed.
- U-6: Whether constitution Principle IV steps 10 to 12 apply to a change that starts no build. Reason: the constitution uses MUST (line 145). The push trigger of `container-build.yml` lists product paths only (row 35). No owner statement resolves the conflict.
- U-7: Whether GitHub builds commit `fd94cfcb` as the merge commit of the pull request event. The inference uses the two parents (row 40) and the run head (row 41). The fetch of the GitHub documentation failed with `WebFetchBlockedUrlError`.

## Method notes

- The `contents` endpoint returned metadata for `.github/dependabot.yml`. The decode step in the PowerShell wrapper failed on the returned body in this session. Body reads therefore used the `git/blobs` endpoint with the SHA from the tree call.
- Every remote claim in this record came from a remote blob, a commit, a run, or a pull request. No claim depends on a local-only file.
