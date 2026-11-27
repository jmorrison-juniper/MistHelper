# Research: Ruff (lint) check failure from the mando 0.8.2 pin

**Issue**: #4891, "CI: quality-gate `ruff` failed (PR #4888)"
**Scope**: Read-only research. No file in the repository changed. No build, test, or package install ran.

## 1. Method

- Read issue #4891, PR #4888, and failing run 45064243269 with GET requests only.
- Read the failed job logs of the Ruff (lint) check and the Ruff (ops platform) check.
- Compared `requirements-dev.txt` on `main` with the PR head.
- Confirmed each repository claim on GitHub `main` by blob SHA and line. Local files support third-party package claims only.

## 2. Failure reproduction

| Item | Value |
| --- | --- |
| Failing check | Ruff (lint), job ID `ruff`, job 137336719229 |
| Workflow and run | Quality Gates, run 45064243269, event `pull_request`, head `e86098cdc2b189d217805b3b4060ef609cbc37af` |
| Failing step | Step 5, `Run pip install -r requirements-dev.txt`, defined at `.github/workflows/ci.yml` line 163 (RV-09) |
| Skipped step | Step 6, `Ruff lint`, defined at line 165 (RV-10). The step was skipped, so no ruff rule ran. |
| Failing rule | None. The job stopped before any ruff rule ran. |
| Error text, job log at 2026-11-22T20:07:26.5519430Z | `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` |
| Cause text, same log | `radon 6.0.1 depends on mando<0.8 and >=0.6` |
| End of job log | `##[error]Process completed with exit code 1.` |

Other failed jobs in the same run:

- The run has 28 failed jobs. Twenty-six jobs print the same resolver conflict in their logs.
- `pytest (coverage gate)` fails at step `Verify dependency lock job`. That step reads the `dependency_lock` result (RV-13).
- `E2E smoke tests` fails at step `Verify E2E shards`. That step reads the `playwright_shards` result (RV-14).
- Ruff (ops platform), job 137336719241, fails at step `Install ruff`. That step runs `pip install -r ../requirements-dev.txt` (RV-11). Its later ruff steps skipped.
- Two other workflows show the same conflict at step `Install test dependencies`: run 45064235051 and run 45064235097.

The full job table is in `quickstart.md`, section 2.

## 3. Linked work

- Issue #4891: state OPEN, created 2026-11-22T20:15:46Z, labels `bug`, `ci`, and `quality-gate`, no comments. The issue body names the `ruff` gate, PR #4888, run 45064243269, and commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`.
- PR #4888: state OPEN, base `main`, head `dependabot/pip/mando-0.8.2` at `e86098cdc2b189d217805b3b4060ef609cbc37af`. The only changed file is `requirements-dev.txt`, with one addition and one deletion.
- The commit that the issue cites is the merge commit of `e86098cd` into `00d9a16e998b0cb5e10b6ed77da0fa909670d64f` (RV-26, RV-27). The run tested the head commit.
- A pull request search for `4891` found no pull request. The linked work is PR #4888, named in the issue body.
- The `main` tip is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RV-28). Quality Gates run 45774119357 on that commit reports success for Ruff (lint), Ruff (ops platform), and Dependency lock and exports (RV-29, RV-59, RV-51).

## 4. Legacy record check

- The repository has no folder whose name starts with `4891-` under `specs\` (RV-60). The existing-record count is zero. No verify or stale step applies.
- Reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Its shape is used. Its content is not copied.

## 5. Route check

- Base 5 of 4891 is `124031`. Padded to eight digits, it is `00124031`. The route is `0\0\1\2\4\0\3\1` (RV-40, RV-41, RV-42).
- The same rule gives `00124140` for issue 4920, which matches the reference record route.
- The route folder `specs\numbered\0\0\1\2\4\0` does not exist. On `main`, `specs/numbered/0/0/1/2/4/` holds two children, `1` and `2` (RV-45). The new route adds one child, so the level holds three children.

## 6. Decisions

Every decision below is a research decision by the author. None requires a human decision.

### D-1 Keep mando at 0.7.1

- **Decision**: Keep mando at 0.7.1. Do not raise the pin to 0.8.2 while radon 6.0.1 is pinned.
- **Recommended**: Yes.
- **Reason**: radon 6.0.1 requires mando below 0.8 (RV-24, line 31). `main` already pins mando 0.7.1 in the requirements file and in the lock (RV-01, RV-05). The lock lists mando under radon (RV-06).
- **Alternatives**:
  - Upgrade radon to a release that accepts mando 0.8. Rejected: the PyPI project page shows 6.0.1 as the latest release (RV-25).
  - Install mando 0.8.2 outside the lock, for example with `--no-deps`. Rejected: the export guard compares the requirements file with the lock (RV-23), and the install hides the resolver conflict.
  - Keep mando at 0.7.1 and block the minor update in Dependabot. Chosen (D-2).
- **Risk**: A future radon release may accept mando 0.8. The removal condition is written in the YAML comment (D-2).

### D-2 Add a pip ignore entry for mando minor updates

- **Decision**: Add an `ignore` entry for `mando` with `update-types: ["version-update:semver-minor"]` to the pip block of `.github/dependabot.yml`.
- **Recommended**: Yes.
- **Reason**: The failing update is a semver-minor update (RV-53). The repository already uses an `ignore` entry with `update-types` for npm (RV-16). The pip block runs weekly (RV-52), and no ignore entry for mando exists (RV-15).
- **Alternatives**:
  - An ignore entry with a `versions` range. Rejected: the repository has no pip precedent for ranges, and this record has no verified syntax for them.
  - Ignore every mando update. Rejected: the entry would block patch releases that radon 6.0.1 accepts.
  - No ignore entry. Rejected: the weekly pip stream can propose the same bump again.
  - Move the development tools to the uv update ecosystem. Rejected: a larger change with no link to the failure.
- **Risk**: Caution: a broad ignore entry hides future security updates for mando. The entry keeps patch updates allowed (FR-003). Dependabot behavior for the entry is unverified (U-01).

### D-3 Leave PR #4888 open

- **Decision**: Keep PR #4888 open. Do not close it, comment on it, or push to its branch in this change.
- **Recommended**: Yes.
- **Reason**: The repository rule says not to close update pull requests (RV-22). The branch belongs to Dependabot, and the repository rule says not to push to a branch that another agent owns (RV-54).
- **Alternatives**:
  - Close PR #4888 now. Rejected: RV-22 forbids it.
  - Comment `@dependabot ignore this minor version` on PR #4888. Rejected: that command closes the pull request, which RV-22 also forbids.
  - Push a revert commit to the Dependabot branch. Rejected: RV-54 forbids it.
- **Risk**: PR #4888 stays red until Dependabot acts. Dependabot behavior is unverified (U-02). T-MERGE records the state.

### D-4 Add the guard cases to the export guard module

- **Decision**: Add class `TestDependabotMandoIgnore` with three cases to `tests/guardrails/test_dependency_export.py`.
- **Recommended**: Yes.
- **Reason**: The `tests/guardrails` folder holds 79 direct children on `main` (RV-43). The constitution forbids a new direct child under a noncompliant parent (RV-44). CI runs the export guard in the `dependency_lock` job (RV-12). The export guard covers the requirements file that Dependabot edits.
- **Alternatives**:
  - A new file under `tests/guardrails`. Rejected: adds a direct child to a noncompliant parent (RV-43, RV-46).
  - A new package under `tests/guardrails`. Rejected: also adds a direct child.
  - `tests/guardrails/test_ci_gate_triggers.py`. Rejected: that module checks workflow triggers (RV-39). Dependabot config is not a workflow.
  - `tests/guardrails/test_dependency_lock_file.py`. Rejected: that module checks the lock against the requirements files. The ignore entry is a policy about updates.
- **Risk**: The module grows by about 40 lines. The change stays narrow (plan, Principle I).

### D-5 Add one changelog fragment

- **Decision**: Add `changelog.d/issue-4891-dependabot-mando-ignore.md` with one `###` heading and one `Fixed` bullet that names Issue #4891.
- **Recommended**: Yes.
- **Reason**: The constitution requires one fragment for each change (RV-20). The PR template has a fragment checklist item (RV-21). The issue name form applies when the issue exists and the pull request does not (RV-61).
- **Alternatives**:
  - No fragment. Rejected: the constitution and the PR template require one. The README rule for internal-only changes (RV-19) conflicts with them. The constitution states that it supersedes other practice documents (RV-62).
  - The pull request name form. Rejected: the pull request number does not exist when the commit is made.
- **Risk**: The conflict between the README rule and the constitution stays open. Analysis DEF-04 tracks it.

### D-6 Mark constitution steps 10 to 12 as not triggered

- **Decision**: Record constitution Principle IV steps 10 to 12 as not triggered for this change. Do not run a manual image build.
- **Recommended**: Yes.
- **Reason**: The container build workflow runs on a push to `main` that changes a product file, or on a manual dispatch (RV-36). This change changes no product file. The image content stays the same, so a verified revision and a deployment would not change the running container. Step 10 waits for the main build (RV-37).
- **Alternatives**:
  - Run a manual container build with `gh workflow run container-build.yml`. Rejected: it pushes an image with the same product code, and the push has no benefit here.
  - Skip the steps without a record. Rejected: the constitution requires a record of each step.
- **Risk**: A reviewer may expect a build. The pull request body states the reason (T-PR).

### D-7 Commit the record with the fix pull request

- **Decision**: Add the record folder to the fix pull request.
- **Recommended**: Yes.
- **Reason**: The constitution says each change adds only its own unique record (RV-44). The route is a numbered record under `specs/numbered/` (RV-42).
- **Alternatives**:
  - A separate record pull request. Rejected: it adds a second change for one issue.
  - No record in the repository. Rejected: the spec record belongs to the change.
- **Risk**: The process guard may reject the record. T-LOCAL-GATES runs the Full tests shard that includes `tests/guardrails` (RV-50).

## 7. Remote verification table

Each row is one remote check. The `remote_checks` array in `files\spec-drafts\_meta\4891-STATUS.json` has the same 62 rows in the same order. The result column states whether the claim holds.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RV-01 | requirements-dev.txt pins mando 0.7.1 on main | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RV-02 | requirements-dev.txt pins radon 6.0.1 on main | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RV-03 | requirements-dev.txt pins ruff 0.17.6 on main | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 399 |
| RV-04 | PR #4888 head pins mando 0.8.2 in requirements-dev.txt | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RV-05 | uv.lock locks mando 0.7.1 on main | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RV-06 | uv.lock lists mando as a dependency of radon 6.0.1 on main | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RV-07 | pyproject.toml pins radon 6.0.1 in the dev extra on main | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RV-08 | pyproject.toml declares mando directly on main | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 0 |
| RV-09 | Quality Gates ruff job installs requirements-dev.txt before its lint step on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 163 |
| RV-10 | Quality Gates ruff job runs ruff check . on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| RV-11 | Ops platform ruff job installs ../requirements-dev.txt on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1232 |
| RV-12 | Dependency lock job runs the export guard test on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| RV-13 | pytest job reads the dependency_lock result on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 341 |
| RV-14 | E2E smoke tests job reads the playwright_shards result on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 966 |
| RV-15 | Dependabot config has a mando ignore entry on main | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 0 |
| RV-16 | Dependabot config has a typescript ignore entry with update-types on main | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 80 |
| RV-17 | quality-gates.md lists ruff check . as the ruff job command on main | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 50 |
| RV-18 | quality-gates.md lists the dependency_lock job ID on main | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | absent | 0 |
| RV-19 | changelog.d README says to add no fragment for an internal-only change on main | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RV-20 | Constitution says each change must add one fragment on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RV-21 | PR template has a fragment checklist item on main | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 36 |
| RV-22 | Copilot instructions say not to close update pull requests on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| RV-23 | Export guard test defines class TestDependencyExport on main | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 98 |
| RV-24 | Local radon 6.0.1 metadata requires mando below 0.8 | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local | not applicable: local file | present | 31 |
| RV-25 | PyPI radon project page shows 6.0.1 as the latest release | https://pypi.org/project/radon/ | web | not applicable: web page | present | 0 |
| RV-26 | Issue-cited merge commit 5bb4b385 exists | commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | not applicable: commit check | present | 0 |
| RV-27 | PR head commit e86098cd exists | commits/e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: commit check | present | 0 |
| RV-28 | Main tip commit f03c6c9 exists | commits/main | main | not applicable: commit check | present | 0 |
| RV-29 | Ruff (lint) job succeeded in run 45774119357 on main | .github/workflows/ci.yml | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 140 |
| RV-30 | Bandit exclude_dirs names tests on main | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| RV-31 | MYPY_PATHS names no test path on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RV-32 | RADON_PATHS names one test file outside tests/guardrails on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| RV-33 | VULTURE_PATHS names no test path on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RV-34 | PYDOCSTYLE_PATHS names no test path on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RV-35 | INTERROGATE_PATHS names no test path on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RV-36 | Container-build row needs a product file change or a manual dispatch on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RV-37 | Constitution step 10 waits for the main build on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| RV-38 | pyproject.toml sets requires-python to 3.15 or newer on main | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RV-39 | Guard test test_ci_gate_triggers.py imports yaml on main | tests/guardrails/test_ci_gate_triggers.py | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 29 |
| RV-40 | Spec route script sets base 5 on main | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RV-41 | Spec route script sets width 8 by default on main | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RV-42 | Spec route script joins numbered records under specs numbered on main | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| RV-43 | tests/guardrails holds 79 direct children on main | tests/guardrails/ | main | not applicable: directory count | present | 0 |
| RV-44 | Constitution allows unique process records as direct children of a process folder on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 46 |
| RV-45 | specs/numbered/0/0/1/2/4 holds direct children 1 and 2 on main | specs/numbered/0/0/1/2/4/ | main | not applicable: directory listing | present | 0 |
| RV-46 | Constitution Core Principles I to VII headings are present on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RV-47 | Constitution step 4 requires a Conventional Commit subject on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 154 |
| RV-48 | Copilot instructions have the local gates section on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RV-49 | Copilot instructions have the test-quality preflight command on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 117 |
| RV-50 | Copilot instructions have the pytest-chunks guardrail command on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 88 |
| RV-51 | dependency_lock job succeeded in run 45774119357 on main | .github/workflows/ci.yml | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 634 |
| RV-52 | Dependabot pip block runs on a weekly schedule on main | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 6 |
| RV-53 | PR head commit message holds update-type version-update:semver-minor | commits/e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: commit check | present | 0 |
| RV-54 | AGENTS.md says not to push to a branch that a different agent owns | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 254 |
| RV-55 | AGENTS.md says to claim the issue with in-progress before branching | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| RV-56 | AGENTS.md says to use a worktree for each branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 198 |
| RV-57 | AGENTS.md says to write Closes issue in the pull request body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RV-58 | AGENTS.md says to add the auto-merge label only after each check is green | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RV-59 | Ops platform ruff job succeeded in run 45774119357 on main | .github/workflows/ci.yml | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1198 |
| RV-60 | Specs tree on main contains a path with 4891 | specs/ | main | not applicable: tree search | absent | 0 |
| RV-61 | changelog.d README gives the issue-number file name form on main | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RV-62 | Constitution states that it supersedes other practice documents on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |

Row count: 62.

## 8. Gate applicability

The table applies the local gates table in `.github/copilot-instructions.md` (RV-48) to this change set. The change set edits `.github/dependabot.yml`, one test module, adds one fragment, and adds one record folder.

| Local gate | Applies | Reason | Reference |
| --- | --- | --- | --- |
| Compile | No | `MistHelper.py` does not change | None |
| Lint | Yes | A Python test module changes | RV-10 |
| Format | Yes | A Python test module changes | RV-48 |
| Types | No | MYPY_PATHS names no test path | RV-31 |
| Tests | Yes | The guard module and the fragment guard run | RV-23, RV-48 |
| Full tests | Yes | `tests/guardrails` changes | RV-50 |
| Safe sweep | No | No product code changes | None |
| Coverage | No | No `src` file changes | None |
| Test quality | Yes | A test module changes | RV-49 |
| Complexity | No | RADON_PATHS names one test file outside `tests/guardrails` | RV-32 |
| Security lint | No | Bandit excludes `tests` | RV-30 |
| Dependency audit | No | `requirements.txt` does not change | None |
| Code quality | No | No `src` file changes | None |
| Dead code | No | VULTURE_PATHS names no test path | RV-33 |
| Docstrings | No | PYDOCSTYLE_PATHS and INTERROGATE_PATHS name no test path | RV-34, RV-35 |
| Menu reference | No | No menu file changes | None |
| Symbols | Yes | A Python module changes | RV-48 |
| STE | No | None of the five listed files changes | None |
| Ops portal | No | No `ops-portal` file changes | None |
| Ops platform | No | No `mist-ops-platform` file changes | None |

## 9. Sources

Local files read:

- `AGENTS.md` (18482 bytes), `.github\copilot-instructions.md` (35535 bytes), `.specify\memory\constitution.md`, and the four templates in `.specify\templates`. Their sizes match the remote blobs.
- `documentation\quality-gates.md`, read in full.
- `documentation\architecture.md`, `documentation\development-setup.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`, scanned by keyword. None of them changes a decision (U-08).
- `.specify\scripts\powershell\spec-route.ps1`, read for the route rule. Its remote lines are in RV-40 to RV-42.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` (RV-24) and `.venv\Lib\site-packages\mando-0.7.1.dist-info`. The mando folder shows that version 0.7.1 is installed.
- The reference record folder `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for its file shape only.

Remote reads (GET only):

- `gh issue view 4891`, `gh pr list --search 4891`, `gh pr view 4888`.
- `gh run view 45064243269` with `--json jobs`, `--job` with `--log-failed`, and the full failed-step log.
- `gh run view 45064235051` and `gh run view 45064235097` for the two other workflows.
- `gh run list --workflow ci.yml --branch main` and `gh run view 45774119357 --json jobs`.
- `gh api` reads of contents, git trees, git blobs, and commits.

URL read:

- `https://pypi.org/project/radon/`, fetched 2026-11-26. It shows radon 6.0.1 as the latest release (RV-25).

Skills: none loaded. The visible skill names do not cover Dependabot, pip resolution, or the Quality Gates workflow.

Mist sources: not consulted. This issue has no Mist API call, no mistapi call, and no SDK claim.

## 10. Unverified

- U-01: Dependabot applies the `update-types` filter to the pip stream. Reason: the repository has no pip ignore precedent (RV-16 is npm). Check at the next weekly Dependabot run.
- U-02: Dependabot's action on PR #4888 after the ignore entry merges. Reason: the service behavior is not observable before the merge.
- U-03: `ruff check .` on the PR #4888 head tree. Reason: step 6 was skipped. Partial evidence: `main` passed the Ruff (lint) job (RV-29).
- U-04: The ops platform ruff correctness gate on the PR #4888 head tree. Reason: the job stopped at step 4. Partial evidence: `main` passed the Ruff (ops platform) job (RV-59).
- U-05: A future radon release accepts mando 0.8. Reason: no such release existed on 2026-11-26 (RV-25). Future releases are unknown.
- U-06: The record passes the spec and process guards. Reason: no guard ran in this read-only phase. T-LOCAL-GATES runs the guard shard.
- U-07: The three guard cases pass. Reason: no test ran in this read-only phase. T002 and T003 run them.
- U-08: The four docs in section 9 contain no rule that changes a decision. Reason: keyword scan only, against the local copies.
