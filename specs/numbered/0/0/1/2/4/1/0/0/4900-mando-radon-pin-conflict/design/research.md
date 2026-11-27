# Research: Mando Pin Conflict Behind the pydocstyle Gate Failure

This file lists the evidence, the decisions, the remote checks, the sources, and the unverified items. Each decision names its alternatives, its reason, and its risk. Each remote check is one row in the table of section "Remote Verification". The row count matches `remote_checks` in the STATUS file.

## Evidence

- **E-1 Baseline**: The issue names `pydocstyle` and pull request 4888. The issue body names commit 5bb4b385 and run 45064243269. The local HEAD is commit f03c6c9, which equals the remote main head. Local blob IDs from `git ls-files -s` match the remote tree for each cited file.
- **E-2 Failing job steps**: Job 137336719204 is `pydocstyle (docstring style)`. Its step `Run pip install -r requirements-dev.txt` has conclusion failure. Its step `Check docstring conventions` has conclusion skipped. Read with `gh run view 45064243269 --json jobs`.
- **E-3 Error text**: The job log for job 137336719204 contains these lines. `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` Then `radon 6.0.1 depends on mando<0.8 and >=0.6`. Then `ERROR: ResolutionImpossible`. Then `##[error]Process completed with exit code 1.` The collecting line names `requirements-dev.txt (line 179)`. Failing rule: none. No pydocstyle rule ran, and the failure occurred during dependency resolution. Read with `gh run view 45064243269 --job 137336719204 --log-failed`.
- **E-4 Failing jobs**: Table E-4 lists every failing job with its failing step. Each row that shows Yes has the same resolver error. The two rows that show No are downstream jobs.

| # | Run | Job ID | Workflow | Job | Failing step | Resolver error in log |
| - | - | - | - | - | - | - |
| 1 | 45064243269 | 137336718674 | Quality Gates | Vulture (dead code) | Run pip install -r requirements-dev.txt | Yes |
| 2 | 45064243269 | 137336718972 | Quality Gates | Quality exclusion drift (advisory) | Run pip install -r requirements-dev.txt | Yes |
| 3 | 45064243269 | 137336718990 | Quality Gates | Diagram reference lint | Run python -m pip install -r requirements-dev.txt | Yes |
| 4 | 45064243269 | 137336719006 | Quality Gates | Radon (complexity) | Run pip install -r requirements-dev.txt | Yes |
| 5 | 45064243269 | 137336719025 | Quality Gates | Interrogate (docstring coverage) | Run pip install -r requirements-dev.txt | Yes |
| 6 | 45064243269 | 137336719038 | Quality Gates | Test quality ratchet (gate) | Run pip install -r requirements-dev.txt | Yes |
| 7 | 45064243269 | 137336719093 | Quality Gates | Citation reference lint | Run python -m pip install -r requirements-dev.txt | Yes |
| 8 | 45064243269 | 137336719111 | Quality Gates | Dependency lock and exports | Run pip install -r requirements-dev.txt | Yes |
| 9 | 45064243269 | 137336719141 | Quality Gates | CodeQL verdict register check | Run python -m pip install -r requirements-dev.txt | Yes |
| 10 | 45064243269 | 137336719159 | Quality Gates | Bandit (security) | Run pip install -r requirements-dev.txt | Yes |
| 11 | 45064243269 | 137336719204 | Quality Gates | pydocstyle (docstring style) | Run pip install -r requirements-dev.txt | Yes |
| 12 | 45064243269 | 137336719229 | Quality Gates | Ruff (lint) | Run pip install -r requirements-dev.txt | Yes |
| 13 | 45064243269 | 137336719241 | Quality Gates | Ruff (ops platform) | Install ruff | Yes, with `../requirements-dev.txt` |
| 14 | 45064243269 | 137336719307 | Quality Gates | SpecKit task audit (advisory) | Run python -m pip install -r requirements-dev.txt | Yes |
| 15 | 45064243269 | 137338084755 | Quality Gates | pip-audit (CVE scan) | Run pip install -r requirements-dev.txt | Yes |
| 16 | 45064243269 | 137338084785 | Quality Gates | mypy (strict) | Install dependencies | Yes |
| 17 | 45064243269 | 137338442186 | Quality Gates | E2E shard (upgrade-portal) | Install dependencies | Yes |
| 18 | 45064243269 | 137338442217 | Quality Gates | Pylint (score gate) | Install dependencies | Yes |
| 19 | 45064243269 | 137338442226 | Quality Gates | pytest coverage shard (upgrade-contracts) | Install dependencies | Yes |
| 20 | 45064243269 | 137338442234 | Quality Gates | E2E shard (web-portal) | Install dependencies | Yes |
| 21 | 45064243269 | 137338442235 | Quality Gates | pytest coverage shard (upgrade-units) | Install dependencies | Yes |
| 22 | 45064243269 | 137338442288 | Quality Gates | pytest coverage shard (root-units) | Install dependencies | Yes |
| 23 | 45064243269 | 137338442294 | Quality Gates | pytest coverage shard (root-and-contracts) | Install dependencies | Yes |
| 24 | 45064243269 | 137338442334 | Quality Gates | E2E shard (websockets-tab) | Install dependencies | Yes |
| 25 | 45064243269 | 137339161249 | Quality Gates | Upgrade portal journeys | Install dependencies | Yes |
| 26 | 45064243269 | 137339161296 | Quality Gates | Black (format check) | Run pip install -r requirements-dev.txt | Yes |
| 27 | 45064235051 | 137336693688 | Native Windows timeout budget | Native Windows timeout budget | Install test dependencies | Yes |
| 28 | 45064235097 | 137336693895 | Windows audit report | Native Windows audit report | Install test dependencies | Yes |
| 29 | 45064243269 | 137338980629 | Quality Gates | pytest (coverage gate) | Verify dependency lock job | No. It reports the failed dependency lock job. |
| 30 | 45064243269 | 137339065340 | Quality Gates | E2E smoke tests | Verify E2E shards | No. It reports the failed E2E shards. |

- **E-5 Main passes**: Run 45774119357 is a `workflow_dispatch` run on main at commit f03c6c9. Its jobs `pydocstyle (docstring style)`, `Dependency lock and exports`, `Bandit (security)`, `Black (format check)`, `Vulture (dead code)`, and `Interrogate (docstring coverage)` conclude success. The pydocstyle job shows `Check docstring conventions` with success.
- **E-6 Pull request and commits**: Pull request 4888 is OPEN. Its head is commit e86098cd, a single Dependabot commit whose parent is 00d9a16e. Its only changed file is `requirements-dev.txt`. Commit 5bb4b385 is a merge commit. Its parents are 00d9a16e and e86098cd. The compare API reports `diverged` for 5bb4b385 against main, with 7 commits ahead and 2 behind. It reports `diverged` for e86098cd against main, with 7 commits ahead and 1 behind. Merged Dependabot pip pull requests 4802, 4803, 4804, 4805, and 4806 list `uv.lock` in their changed files.
- **E-7 Legacy record search**: No folder whose name starts with `4900-` exists under `specs\` locally. A recursive directory search returns zero matches. The remote tree search for the string `4900` returns zero matches. The search by issue number for pull requests returns an empty list. Pull request 4888 is linked by the issue body only.
- **E-8 Route derivation**: `spec-route.ps1` uses base 5 and default width 8 (lines 7 and 17). Issue 4900 has base-5 digits 1, 2, 4, and 1 at the powers 5, 4, 3, and 2. The other powers hold 0. Padded to eight digits, the route is 0 0 1 2 4 1 0 0. The reference record for issue 4920 has the route 0 0 1 2 4 1 4 0, which the same formula produces.
- **E-9 Upstream radon**: The PyPI project page for radon shows the header `radon 6.0.1`. It lists no newer release.

## Decisions

### R1. Keep mando 0.7.1 and close pull request 4888 without merge (D-1)

- **Decision**: Keep `mando==0.7.1` on main. Close pull request 4888 without merge after the fix merges.
- **Alternatives considered**:
  - Upgrade radon. Rejected, because PyPI lists radon 6.0.1 as the latest release (E-9).
  - Replace radon with another complexity tool. Rejected, because the change alters the radon JSON contract, the complexity gate, and its guard tests. That scope exceeds this issue.
  - Remove the mando pin or install with `--no-deps`. Rejected, because the lock export guard and reproducible installs then break.
  - Rebase pull request 4888 and keep the update. Rejected, because the resolver still fails.
- **Rationale**: Main already holds mando 0.7.1, and main passes the same jobs (E-5). The fix therefore declines the update and adds a guard.
- **Risk**: Development installs keep mando 0.7.1. A security fix that ships only in mando 0.8.x does not reach those installs. Decision D-5 opens a follow-up issue.

### R2. Ignore mando minor and major updates in Dependabot (D-2)

- **Decision**: Add an `ignore` block for `mando` with the update types `version-update:semver-minor` and `version-update:semver-major` to the pip entry of `.github/dependabot.yml`. Update the policy snapshot in the same change.
- **Alternatives considered**:
  - Ignore every mando update. Rejected, because patch updates that radon accepts would also stop.
  - Ignore nothing. Rejected, because the same pull request repeats each week.
  - Comment `@dependabot ignore this minor version` on pull request 4888. Rejected, because that choice lives in Dependabot state and not in version control.
  - Ignore minor and major updates only. Chosen.
- **Rationale**: Radon accepts mando 0.6 up to, but not including, 0.8 (local metadata line 31). Patch updates stay inside that range. Merged Dependabot pip pull requests update `uv.lock` too (E-6), so a patch update can stay consistent.
- **Risk**: A patch update that omits `uv.lock` fails the export guard. The guard reports the drift, so the failure stays visible.

### R3. Add one changelog fragment (D-3)

- **Decision**: Add `changelog.d/issue-4900-mando-radon-pin-conflict.md`.
- **Alternatives considered**:
  - Add no fragment, as `changelog.d/README.md` rule four allows for an internal change. Rejected.
  - Add one fragment, as constitution line 409 requires. Chosen.
- **Rationale**: Constitution line 529 states that the constitution supersedes all other practice documents when conflicts arise. The fragment guard accepts the file name (`TestFragmentNaming`).
- **Risk**: A reviewer may judge the fragment as noise. The risk is low.

### R4. Ship the record and the fix in one pull request (D-4)

- **Decision**: Put the record and the fix in one pull request. Close pull request 4888 only after that pull request merges.
- **Alternatives considered**:
  - Close pull request 4888 first. Rejected, because Dependabot recreates the update on its next weekly run before the ignore block lands.
  - Push a revert commit to pull request 4888. Rejected, because the Dependabot branch and its failing history remain.
  - Use two pull requests, one for the record and one for the fix. Rejected, because the record is not a separate product change and two merges add an ordering risk.
- **Rationale**: The ignore block and the close land in the same sequence.
- **Risk**: Pull request 4888 stays failing until the merge. Task T-MERGE closes it after the merge.

### R5. Defer any radon replacement (D-5)

- **Decision**: Make no radon change in this issue. Open a follow-up issue for the radon choice.
- **Alternatives considered**:
  - Replace radon now. Rejected, because the change exceeds this issue and alters a gate.
  - Open a follow-up issue. Chosen.
  - Accept the conflict without a plan. Rejected, because the development tool set then stays frozen without an owner.
- **Rationale**: No compatible radon release exists (E-9).
- **Risk**: The radon pin keeps mando at 0.7. The follow-up issue owns the mitigation.

## Remote Verification

Each row records one claim, the path, the reference, the blob SHA, the result, and the line. A `none` blob SHA marks an absent path. The head reference is commit e86098cdc2b189d217805b3b4060ef609cbc37af.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Pydocstyle job is defined in the Quality Gates workflow | .github/workflows/ci.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 570 |
| 2 | Pydocstyle job runs the pip install step before the docstring step | .github/workflows/ci.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 582 |
| 3 | Docstring step runs as a separate step and was skipped | .github/workflows/ci.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 584 |
| 4 | Dependency lock job installs requirements-dev.txt | .github/workflows/ci.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 646 |
| 5 | Pull request head pins mando 0.8.2 | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| 6 | Main pins mando 0.7.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| 7 | Main pins radon 6.0.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| 8 | Main pins pydocstyle 6.3.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 304 |
| 9 | Main uv.lock locks mando 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1300 |
| 10 | Main uv.lock locks radon 6.0.1 with a mando dependency | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2427 |
| 11 | Main pyproject dev extra pins radon 6.0.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| 12 | Dependabot pip entry has no ignore block | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 3 |
| 13 | Dependabot policy snapshot holds the pip entry without an ignore block | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 23 |
| 14 | Export guard reads requirements-dev.txt with the dev extra | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 14 |
| 15 | Native Windows timeout budget installs requirements-dev.txt | .github/workflows/windows-timeout-budget.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 48 |
| 16 | Windows audit report installs requirements-dev.txt | .github/workflows/windows-audit-report.yml | e86098cdc2b189d217805b3b4060ef609cbc37af | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 48 |
| 17 | Main run 45774119357 passes the pydocstyle job | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 570 |
| 18 | No record folder for issue 4900 exists on main | specs/numbered/0/0/1/2/4/1/0/0 | main | none | absent | 0 |
| 19 | Spec route uses base 5 and default width 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 20 | Changelog rule four allows no fragment for an internal change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 21 | Constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 22 | Constitution supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| 23 | Container build push trigger lists product paths | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| 24 | Auto-merge dispatches container-build after each merge | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 65 |
| 25 | Containerfile installs requirements.txt only | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 111 |
| 26 | Quality gate document lists pip audit for requirements.txt only | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 57 |
| 27 | Branch name rule uses type, issue, and slug | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |

Rows 15 and 16 cite the head reference. Pull request 4888 changes only `requirements-dev.txt`, so these two workflow files keep the blob IDs of main.

## Sources

Local sources, read only:

- `AGENTS.md`, issue first and claim: lines 183 to 187.
- `AGENTS.md`, branch name: lines 192 to 197.
- `AGENTS.md`, merge and closing rules: lines 235, 239, and 271.
- `AGENTS.md`, specifications: line 345.
- `.github/copilot-instructions.md`: lines 68 (dependency audit row), 71 (docstrings row), 74 (STE row), 159 (managed roots), and 451 to 455 (changelog rule).
- `.specify/memory/constitution.md`, version and Principle I: lines 4, 38, 46, and 57.
- `.specify/memory/constitution.md`, Principles II to VII: lines 91, 113, 143, 182, 204, and 235.
- `.specify/memory/constitution.md`, technology and workflow: lines 274, 298, 302, and 337.
- `.specify/memory/constitution.md`, release notes and supersession: lines 409 and 529.
- `changelog.d/README.md`: line 32 (keep the first name) and line 58 (rule four).
- `tests/guardrails/test_pr_title_workflow.py`: lines 18 to 30 (snapshot), line 271 (class `TestDependabotPolicy`), and line 297 (`test_complete_policy`).
- `tests/guardrails/test_dependency_export.py`: line 14 (export entry for requirements-dev.txt with the dev extra).
- `tests/guardrails/test_changelog_fragment_policy.py`: line 37 (slug pattern), line 151 (`test_every_fragment_uses_an_allowed_name`), and line 192 (`test_every_fragment_holds_a_heading_and_a_bullet`).
- `tests/guardrails/test_spec_route_contract.py`: line 464 (`test_numeric_feature_route_remains_stable`).
- `.specify/scripts/powershell/spec-route.ps1`: line 7 (default width), line 17 (base), line 31 (digits), and line 51 (numbered path).
- `documentation/quality-gates.md`: line 57 (pip-audit row) and line 61 (pydocstyle row).
- `.github/workflows/ci.yml`: line 9 (workflow name), line 104 (`PYDOCSTYLE_PATHS`), lines 570 to 584 (pydocstyle job), and line 646 (dependency lock install).
- `.github/workflows/container-build.yml` lines 6 to 19, `.github/workflows/auto-merge.yml` lines 61 and 65, and `Containerfile` line 111.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` line 31: `Requires-Dist: mando (<0.8,>=0.6)`.
- `requirements-dev.txt`: lines 179 and 180 (mando pin and `# via radon`), line 304 (pydocstyle), and line 365 (radon).
- `uv.lock`: lines 1300 and 1301 (mando), and lines 2427 to 2432 (radon).
- `pyproject.toml`: lines 99 and 100 (parity comment), line 118 (radon), line 120 (pydocstyle), and line 600 (`[tool.pydocstyle]`).
- `.specify/templates/` (spec, plan, tasks, and checklist templates) and `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference shape only).

Remote sources, read only:

- `gh issue view 4900`, `gh issue view 1779`, and `gh issue view 3400` (issue facts and related issues).
- `gh pr view 4888` and `gh pr list --author app/dependabot` (pull request state and changed files).
- `gh run view` for runs 45064243269, 45774119357, 45064235051, and 45064235097, with `--json jobs` or with `--job` and `--log-failed`.
- `gh api` commit lookups by SHA, and the compare endpoint for two commit references.
- The Git trees endpoint for main with `recursive=1`, and the contents endpoint with a path and a ref (blob IDs and file bodies).

External source:

- https://pypi.org/project/radon/ (fetched 2026-11-26). The header reads `radon 6.0.1`.

Skills: no skill was loaded. The issue concerns Python dependency resolution and CI configuration. It does not concern Podman or Juniper device behavior.

Mist API and mistapi: not read. No claim in this record depends on a Mist endpoint or an SDK symbol.

## Unverified

- **U-1**: `uv lock` cannot select mando 0.8.2, because radon 6.0.1 requires mando below 0.8. Reason: the brief forbids repository scripts and package installs. The claim rests on the pip error (E-3) and the radon metadata (line 31).
- **U-2**: Dependabot honors the new ignore block for a transitive pin. Reason: the change has not merged, so no weekly run has occurred.
- **U-3**: Dependabot updates `uv.lock` for patch updates of mando. Reason: the claim rests on merged sibling pull requests (E-6). No mando patch update exists to test.
- **U-4**: The pytest shards, E2E shards, mypy, and Pylint pass on the fix pull request. Reason: the remote run occurs after T-PR.
- **U-5**: The pip-audit scope excludes development-only packages. Reason: the claim rests on the job command and the documentation. The audit was not run.
- **U-6**: The route guard passes on main. Reason: the brief forbids running repository tests.
- **U-7**: The remote state may change after this record. Reason: the observations date from 2026-11-26.
