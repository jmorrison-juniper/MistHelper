# Research: Hold mando below 0.8 for the mypy gate

**Issue**: #4893, `CI: quality-gate mypy failed (PR #4888)`

**Record route**: `specs\numbered\0\0\1\2\4\0\3\3\4893-mando-radon-pin`

## 1. Scope and method

- The issue, PR #4888, run 45064243269, and its failed logs came from GET requests only.
- Repository files came from the `main` tree and the blob contents API.
- Five local files match the remote blob SHA of `main`: `requirements-dev.txt`, `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `documentation/quality-gates.md`.
- Section 5 lists each path check. Section 3 lists GitHub object reads, which are not path checks.

## 2. Failure reproduction from CI logs

| Fact | Value | Source |
| - | - | - |
| Gate named by the issue | `mypy` | Issue #4893 body |
| Workflow | `Quality Gates`, file `.github/workflows/ci.yml` line 9 (RC-03) | Run metadata |
| Run | 45064243269, event `pull_request`, conclusion `failure` | `gh run view --json` |
| Head revision of the run | `e86098cdc2b189d217805b3b4060ef609cbc37af` (RC-66) | Run metadata |
| Failing check | `mypy (strict)`, job `mypy` at `ci.yml` lines 201-202, job ID 137338084785 | PR #4888 rollup and jobs API |
| Failing step | `Install dependencies` at `ci.yml` lines 232-235 (RC-01), step 5, conclusion `failure` | `gh api actions/jobs/137338084785` |
| Skipped step | `Run mypy` at `ci.yml` lines 236-237 (RC-02), step 6, conclusion `skipped` | Same jobs API call |
| Failing rule | pip resolver conflict | `--log-failed` output for `mypy (strict)` |
| Failing test | None. The job never ran a test. | Step list |

Exact log lines for the failing rule, from job `mypy (strict)`:

```text
2026-11-22T20:09:15.2216539Z ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.
2026-11-22T20:09:15.2225283Z ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
2026-11-22T20:09:15.6335838Z ##[error]Process completed with exit code 1.
```

Other run facts:

- The `requirements.txt` install finished before the failure. The log shows `mistapi-0.64.1` in the installed list.
- The run has 28 distinct failed jobs. 26 of them show the same `ResolutionImpossible` line.
- `pytest (coverage gate)` (job 137338980629) fails at step 2, `Verify dependency lock job`. That step exits 1 when `needs.dependency_lock.result` is not `success` (RC-08). Its cause is the same install failure.
- `E2E smoke tests` (job 137339065340) fails at step 2, `Verify E2E shards`. Its cause is not read. See section 8, U-4.

### Root cause chain

1. PR #4888 changes `requirements-dev.txt` line 179 from `mando==0.7.1` to `mando==0.8.2` (RC-09, RC-14).
2. `radon==6.0.1` requires `mando` below 0.8 and at least 0.6 (RC-67). The lock records mando as a radon dependency (RC-24).
3. pip cannot satisfy both pins, so it stops with `ResolutionImpossible`.
4. The `Install dependencies` step fails, so `Run mypy` is skipped (RC-01, RC-02).
5. Every job that installs `requirements-dev.txt` fails the same way (26 jobs). The pytest coverage gate fails through the dependency lock result (RC-08).

### Revision note

The issue cites merge revision `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`. The `mypy (strict)` log shows CI fetched `refs/remotes/pull/4888/merge` at that revision. The merge joins PR head `e86098cdc2b189d217805b3b4060ef609cbc37af` into base `00d9a16e998b0cb5e10b6ed77da0fa909670d64f`. Both revisions exist on GitHub (RC-65, RC-66).

### Main branch status

- `main` is not affected. The three newest `ci.yml` runs on `main` conclude `success`: 45774119357 at head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, 45743255974 at head `ccff03e05a686ac3f7c14fddb0828cd373c6e822`, and 45729359923 at head `4e81b2a4a724e29476270564be927f797def82be`.
- `main` pins `mando==0.7.1` (RC-09). The pin set resolves.

## 3. GitHub object evidence (not path checks, not counted in section 5)

- Issue #4893 is `OPEN`. Labels are `bug`, `ci`, and `quality-gate`. The author is `app/github-actions`. It has no comments. It was created at 2026-11-22T20:15:50Z.
- PR #4888 is `OPEN` and not merged. Head branch `dependabot/pip/mando-0.8.2`. It changes one file, `requirements-dev.txt`, with one addition and one deletion.
- Quality-gate issues #4891 to #4905 are 15 `OPEN` issues. Each title names one failed gate, for example `CI: quality-gate mypy failed (PR #4888)`. They were created from 2026-11-22T20:15:46Z to 20:16:11Z. The issue #4893 job is `mypy`.
- Job 137338084785 (`mypy (strict)`): step 5 `Install dependencies` failed, and step 6 `Run mypy` skipped.
- Job 137338980629 (`pytest (coverage gate)`): step 2 `Verify dependency lock job` failed, and steps 3 to 9 skipped.
- Job 137339065340 (`E2E smoke tests`): step 2 `Verify E2E shards` failed.
- `gh pr list --search 4893` returns an empty list.

## 4. Decisions

Each decision has alternatives, a choice, a reason, and a risk. No decision needs a human (`human_decision_required` is `false`), because none falls in brief section 6.

### D-1 Fix direction

- **Alternatives**: (a) keep `mando` at 0.7.1 and block newer minor and major releases. (b) raise `radon` to a release that accepts `mando` 0.8. (c) remove `radon` and its complexity gate. (d) install `mando` 0.8.2 with a pip override or a no-deps install.
- **Chosen**: (a), recommended.
- **Reason**: The PyPI project page lists radon 6.0.1 as the current release (RC-69). No newer radon accepts `mando` 0.8. Option (c) removes a gate that the local gates table requires (RC-36). Option (d) hides the conflict and installs an unsupported set.
- **Risk**: `mando` stays at 0.7.1 until radon accepts a newer release. `mando` is a development dependency (RC-22, RC-68), so the risk is low.

### D-2 Recurrence control

- **Alternatives**: (a) add an ignore entry for `mando` with `update-types` for minor and major updates. (b) add an ignore entry with a `versions` range. (c) keep only the guard tests. (d) close each new Dependabot pull request by hand.
- **Chosen**: (a), recommended.
- **Reason**: The npm block in `.github/dependabot.yml` already uses `update-types` in an ignore entry (RC-27). Option (c) fails only after pip fails, so it cannot stop the pull request. Option (d) depends on a person.
- **Risk**: The minor and major classification for 0.7.1 to 0.8.x is unverified (section 8, U-1 and U-2). T-MERGE checks the next pip cycle.

### D-3 Guard test location

- **Alternatives**: (a) extend `tests/guardrails/test_dependency_export.py`. (b) add a new file under `tests/guardrails/`. (c) extend `tests/guardrails/test_dependency_declaration_parity.py`.
- **Chosen**: (a), recommended.
- **Reason**: The file reads requirements exports (RC-28), and the `dependency_lock` job runs it (RC-05). Option (b) adds a direct child to `tests/guardrails/`, which already holds 79 children (RC-34). Constitution Principle I forbids new direct children in a noncompliant parent (RC-44). Option (c) compares pyproject declarations with exports (RC-30), a different contract.
- **Risk**: The file grows by about 60 lines. The helpers keep the function limits.

### D-4 PR #4888 disposition

- **Alternatives**: (a) close PR #4888 after the fix merges, with a closing comment. (b) leave PR #4888 open. (c) push a fix to the Dependabot branch.
- **Chosen**: (a), recommended.
- **Reason**: Option (b) keeps a failing request and 15 gate issues open. Option (c) pushes to a branch that Dependabot owns (RC-42). The closing comment gives the preservation proof that AGENTS.md requires.
- **Risk**: Closing an update request can hide a future decision. RC-39 warns against closing update pull requests to repair titles. This decision closes a request that cannot resolve. The pip update stream stays on. Caution: a closed request needs a new decision to reopen.

### D-5 Changelog fragment and folder debt

- **Alternatives**: (a) add one fragment. (b) add no fragment, because the change is CI only. (c) add the fragment in a new folder.
- **Chosen**: (a), recommended.
- **Reason**: The constitution requires one fragment for each change (RC-46). Option (b) conflicts with that rule. Option (c) adds a folder outside the process rules.
- **Folder debt**: `changelog.d/` holds 335 children (RC-35). The constitution allows one unique record in that folder (RC-45). The remediation action is a separate issue to group older fragments. It is outside this change.

### D-6 Revision reporting

- **Alternatives**: (a) name the head revision `e86098cd` as the failed revision and keep `5bb4b385` as the cited merge revision. (b) replace the cited revision with the head revision in the record.
- **Chosen**: (a), recommended.
- **Reason**: The run head is `e86098cd`, and the merge revision is the commit that CI checked out. Both revisions exist (RC-65, RC-66). The record must keep the issue text unchanged.
- **Risk**: None for the fix. A reader may compare the two revisions, so section 2 explains the difference.

## 5. Remote verification table

Path checks for this record. Each row names one check. The `Ref` column names the revision read. For commit rows, the blob column holds the commit SHA. `none` means the path is absent. `not applicable` means the check has no blob.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | `mypy` job runs `pip install -r requirements-dev.txt` in `Install dependencies` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 235 |
| RC-02 | `mypy` job runs `mypy $MYPY_PATHS` with pyproject config after install | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 237 |
| RC-03 | Workflow is named `Quality Gates` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| RC-04 | `dependency_lock` installs `requirements-dev.txt` before `uv lock --check` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 646 |
| RC-05 | `dependency_lock` runs the requirements export guard | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| RC-06 | `quality_gate_issues` lists `mypy` in `needs` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1298 |
| RC-07 | Job `pytest` is named `pytest (coverage gate)` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 331 |
| RC-08 | Job `pytest` fails when `dependency_lock` is not `success` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 343 |
| RC-09 | `requirements-dev.txt` on main pins `mando==0.7.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-10 | `requirements-dev.txt` on main names radon as the requirer of `mando` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 180 |
| RC-11 | `requirements-dev.txt` on main pins `radon==6.0.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-12 | `requirements-dev.txt` on main pins `mypy==2.4.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 205 |
| RC-13 | `requirements-dev.txt` on main pins `mistapi==0.64.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 195 |
| RC-14 | `requirements-dev.txt` on PR head pins `mando==0.8.2` | `requirements-dev.txt` | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RC-15 | `requirements-dev.txt` on PR head pins `radon==6.0.1` | `requirements-dev.txt` | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| RC-16 | `pyproject.toml` requires Python 3.15 or newer | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-17 | `pyproject.toml` dev extra pins `radon==6.0.1` | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RC-18 | `pyproject.toml` dev extra comment names the declaration parity guard | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 99 |
| RC-19 | `pyproject.toml` sets `[tool.mypy]` `strict = true` | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 279 |
| RC-20 | `requirements.txt` pins `packaging==26.3` | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 146 |
| RC-21 | `requirements.txt` pins `pyyaml==6.0.4` | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 209 |
| RC-22 | `requirements.txt` holds no `mando` or `radon` pin | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| RC-23 | `uv.lock` locks `mando` at version 0.7.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-24 | `uv.lock` lists `mando` as a dependency of `radon` 6.0.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RC-25 | `dependabot.yml` pip block has no ignore entry | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-26 | `dependabot.yml` pip block ends with the `chore` commit prefix | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 11 |
| RC-27 | `dependabot.yml` npm block uses `update-types` in an ignore entry | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 81 |
| RC-28 | `test_dependency_export.py` defines class `TestDependencyExport` | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 98 |
| RC-29 | `test_dependency_export.py` logs before the read at line 26 and after it at line 32 | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 26 |
| RC-30 | `test_dependency_declaration_parity.py` defines class `DeclarationParity` | `tests/guardrails/test_dependency_declaration_parity.py` | main | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 24 |
| RC-31 | `test_changelog_fragment_policy.py` exists | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-32 | `changelog.d/README.md` exists | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-33 | Pull request template exists | `.github/PULL_REQUEST_TEMPLATE.md` | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| RC-34 | `tests/guardrails/` holds 79 direct children | `tests/guardrails` | main | not applicable | present | 0 |
| RC-35 | `changelog.d/` holds 335 direct children | `changelog.d` | main | not applicable | present | 0 |
| RC-36 | `copilot-instructions.md` holds the Local gates table, header at line 55 | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| RC-37 | `copilot-instructions.md` names the pull request fragment file pattern | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-38 | `copilot-instructions.md` lists `container-build.yml` trigger on product file changes | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RC-39 | `copilot-instructions.md` says do not close update pull requests for title repair | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| RC-40 | `AGENTS.md` holds the writing style section | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-41 | `AGENTS.md` holds the Git flow section with issue first and branch rules | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 179 |
| RC-42 | `AGENTS.md` says do not push to a branch that a different agent owns | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 254 |
| RC-43 | `AGENTS.md` requires the STE gate for each Markdown file | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-44 | Constitution Principle I, five-item rule, holds at line 38 | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-45 | Constitution allows unique process records as direct children of process folders | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 46 |
| RC-46 | Constitution requires one unique changelog fragment for each change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-47 | Constitution Principle IV defines the full deployment pipeline | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-48 | Constitution holds Principles II, III, V, VI, and VII by heading | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| RC-49 | `quality-gates.md` lists the `mypy` job and threshold | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 52 |
| RC-50 | `quality-gates.md` lists the `quality_gate_issues` job | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 72 |
| RC-51 | `development-setup.md` shows the install command for both requirement files | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |
| RC-52 | `architecture.md` lists `requirements-dev.txt` as a tool file | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 167 |
| RC-53 | Spec template holds the mandatory section headings | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-54 | Plan template holds the technical context and constitution check headings | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-55 | Tasks template defines the task format | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-56 | Checklist template defines the checklist item format | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-57 | `spec-route.ps1` converts a number to base-5 segments | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-58 | Reference record `spec.md` shows the spec shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-59 | Reference record `plan.md` shows the plan shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| RC-60 | Reference record `tasks.md` shows the task shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-61 | Reference record `analysis.md` shows the analysis shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md` | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| RC-62 | Reference record `design/research.md` shows the research shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-63 | Route folder `specs/numbered/0/0/1/2/4/0/3/3` is absent | `specs/numbered/0/0/1/2/4/0/3/3` | main | none | absent | 0 |
| RC-64 | No folder named `4893-*` exists under `specs/` | `specs/**/4893-*` | main | none | absent | 0 |
| RC-65 | Commit `5bb4b385` exists and is the cited merge revision | `commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | present | 0 |
| RC-66 | Commit `e86098cd` exists and is the run head revision | `commits/e86098cdc2b189d217805b3b4060ef609cbc37af` | e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| RC-67 | Local radon 6.0.1 metadata requires `mando` below 0.8 | `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` | local .venv | 00765926c0dd3906f1e65015d4cd9d0b87a2b506 | present | 31 |
| RC-68 | Local mistapi 0.64.1 metadata declares no `mando` dependency | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` | local .venv | 86b3b7003d569a1311af4085e7e269a52decd795 | absent | 19 |
| RC-69 | PyPI project page for radon shows version 6.0.1 as the current release | `https://pypi.org/project/radon/` | web fetch 2026-11-26 | not applicable | present | 0 |
| RC-70 | `ci.yml` env `MYPY_PATHS` names source paths and no guard test | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-71 | `ci.yml` env `RADON_PATHS` names source paths and one unit test file, not `tests/guardrails` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |

Row count: 71. This count matches `remote_checks` in `4893-STATUS.json` and the count in `4893-summary.md`.

## 6. Sources

Local files, read with `view` or PowerShell:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `documentation/quality-gates.md` (read in full).
- `.specify/templates/` spec, plan, tasks, and checklist templates (read in full).
- `documentation/development-setup.md` line 137 and `documentation/architecture.md` line 167 (matched by search).
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` line 31 and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` lines 18 to 25.
- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (folder listing and line counts).

Remote files, read through `gh api` (GET): section 5.

URL, fetched with `web_fetch`: `https://pypi.org/project/radon/` (RC-69).

## 7. Applicability of documents and skills

- Skill: none loaded. No listed skill covers pip resolution, mypy, or Dependabot. The skill tool was not called.
- Mist API files (`documentation/mist-api-openapi31yaml.yaml`, `MIST_API_GET_ENDPOINTS.md`, `MIST_API_MISSING_ENDPOINTS.md`): not applicable. The failure involves no Mist endpoint. The files were not read.
- `mistapi` SDK: not applicable to the conflict. Its installed metadata declares no `mando` dependency (RC-68). Its pin stays unchanged (RC-13).
- `documentation/quality-gates.md`: applies. It defines the `mypy` job and `quality_gate_issues` (RC-49, RC-50).
- `documentation/development-setup.md`: applies. Its install command reaches the same conflict (RC-51). No change needed.
- `documentation/architecture.md`: applies to the file list (RC-52). No change needed.
- `documentation/container-deployment.md`: not applicable. The change alters no container file, and `container-build.yml` does not start for it (RC-38).
- `documentation/operator-guide.md`: not applicable. No operator-facing behavior changes.
- `AGENTS.md` and `.github/copilot-instructions.md`: apply to style, Git flow, and gates.
- Constitution: applies to the constitution check in `plan.md`.

## 8. Unverified

- **U-1**: Dependabot classifies a 0.7.1 to 0.8.x `mando` update as `version-update:semver-minor`. Reason: the Dependabot options reference was not fetched. Mitigation: T-MERGE checks the next pip cycle.
- **U-2**: Dependabot applies a pip `update-types` ignore entry the same way as the npm entry. Reason: only the npm entry in this repository (RC-27) shows the syntax.
- **U-3**: `importlib.metadata.requires("radon")` and `packaging` parse `mando (<0.8,>=0.6)` as expected. Reason: this agent runs no code (brief rule 2). Mitigation: T004 runs the guard tests.
- **U-4**: The cause of the `E2E smoke tests` failure at step `Verify E2E shards`. Reason: the step log was not read. Its record needs its own issue.
- **U-5**: Whether `pytest (coverage gate)` passes after the fix. Reason: it depends on `dependency_lock` and on U-4 only if its shards fail. T-REMOTE-CI checks it.
- **U-6**: Whether `Bandit` excludes `tests/` in `pyproject.toml`. Reason: the file was not read in this session. T-LOCAL-GATES runs the Security lint row on the guard test module.
- **U-7**: `symbol-diff` output for added module-level names. Reason: the tool was not run. T-LOCAL-GATES records the output.
- **U-8**: Folder counts in RC-34 and RC-35 describe the `main` tree on 2026-11-26 only.
