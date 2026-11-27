# Research: Ops platform dateutil pin (issue #4908)

This file holds the evidence for the decisions in `spec.md` and `plan.md`. Each remote claim has a row (RC-##) in the verification table. Each external package claim cites a local source (S-#) first. Each unconfirmed claim appears under Unverified (U-#).

## R1. Failing check, job, step, and rule

- **Workflow**: Quality Gates, file `.github/workflows/ci.yml` (RC-01).
- **Check**: `pytest (ops platform)`. The job ID is `ops_platform_pytest`.
- **Run**: 45064318582, attempt 1, event `pull_request`, branch `dependabot/pip/python-dateutil-4.0.0`, conclusion `failure` (S-8).
- **Job**: ID 137336951691, conclusion `failure` (S-4).
- **Failed step**: `Install dependencies`, step number 4. The step name is at ci.yml line 1150 and the command at line 1162 (RC-02).
- **Failing rule**: pip resolves `requirements.txt` with `-e ".[dev]"` and `requirements-dev.txt`. The resolver stops with `ResolutionImpossible` (S-4).
- **Failing test**: None. The step failed before the steps that run the suite. The log shows no test name (S-4).
- **Reproduction source**: `gh run view 45064318582 -R jmorrison-juniper/MistHelper --log-failed` returns 446 lines. The lines at 20:08:49 to 20:08:51 hold the conflict (S-4).

Log lines that name the conflict (copied from S-4):

- `Collecting python-dateutil==4.0.0 (from -r requirements.txt (line 157))`
- `ERROR: Cannot install -r requirements.txt (line 27) and python-dateutil==4.0.0 because these package versions have conflicting dependencies.`
- `celery 5.7.0 depends on python-dateutil==2.9.0.post0`
- `Additionally, some packages in these conflicts have no matching distributions available for your environment: python-dateutil`
- `ERROR: ResolutionImpossible`

## R2. Trigger path from the pull request to the failure

1. Dependabot opens PR #4890 with one changed line, `mist-ops-platform/requirements.txt` +1 -1 (S-5).
2. The pull request event runs Quality Gates on test-merge commit `e30d4a95`. Its parents are `00d9a16e` (base) and `4be9d2e7` (PR head) (S-9, RC-03).
3. Job `ops_platform_pytest` sets `working-directory: mist-ops-platform` (RC-01 for the job).
4. Step `Install dependencies` runs `pip install -r requirements.txt -e ".[dev]" -r requirements-dev.txt` (RC-02).
5. Pip reads line 157 of the requirements file, which is `python-dateutil==4.0.0` on the merge commit (RC-18).
6. Pip reads line 27, `celery==5.7.0`, whose requirement is `python-dateutil==2.9.0.post0` (RC-15, RC-50). The two pins conflict, and pip stops.

The issue body cites `e30d4a95`, which is the test-merge commit. The run `headSha` reports `4be9d2e7`, which is the PR head (S-6, S-8). The two values name the same change.

## R3. Pin chain and cause

- `main` pins python-dateutil at `2.9.0.post0` on line 157 of `mist-ops-platform/requirements.txt` (RC-16).
- PR head pins `4.0.0` on line 157 (RC-17). The PR changes no other line (S-5).
- Celery 5.7.0 declares `python-dateutil==2.9.0.post0` in `requirements/default.txt` line 8 (RC-50).
- Celery 5.7.0 is the newest release (RC-53). Its tag declares the exact pin.
- The earlier tag `v5.7.0a1` declares `python-dateutil>=2.8.2` (RC-51). The upstream `main` declares `>=2.9.0.post0` (RC-52). That relaxation is not in any release.

Conclusion: no version of python-dateutil satisfies both pins in the ops requirements file. The bump fails for every 3.x and 4.x release.

## R4. Interpreter version is not the cause

- CI sets `PYTHON_VERSION` to `3.15` (RC-04). The ops job reads `env.PYTHON_VERSION` in its setup step.
- Python-dateutil 4.0.0 declares `Requires-Python: >=3.11` (S-2, local METADATA line 26). Python 3.15 satisfies that bound.
- The log does not name a Python version conflict. The message names the pins (S-4).

## R5. Upstream celery release state

- Newest release: `v5.7.0`, published 2026-11-05 (RC-53, S-10).
- Final tag pin: `python-dateutil==2.9.0.post0` (RC-50).
- Upstream `main` has `>=2.9.0.post0` (RC-52). A release from that state is not in the release list.
- No released celery version accepts python-dateutil 4.x (RC-50, RC-53).

Decision D-6 follows from this state.

## R6. python-dateutil release and metadata state

- Releases: 4.0.0 (2026-11-01), 3.0.0 (2026-10-21), 2.9.0.post0 (2024-03-01), 2.9.0 (2024-03-01) (S-11).
- The newest 2.x release is `2.9.0.post0` (RC-54). The ops pin therefore covers every 2.x release.
- Local METADATA for 4.0.0 declares `Requires-Python: >=3.11`, `Requires-Dist: tzdata`, and `License-Expression: BSD-3-Clause` (S-2, lines 10, 26, 27).
- The PR body states that 4.0 drops `six` and changes `isoparse` (S-3).
- The root requirements already pin 4.0.0 (RC-26, RC-27).

## R7. Code use of python-dateutil

- Remote code search for `dateutil` returns 7 paths (S-13). None sits under `mist-ops-platform/src` (RC-55).
- The paths are `junk/build-output.txt`, `src/foundation/support/refactors/package_import_map.py`, `requirements.txt`, `specs/numbered/0/0/1/2/1/4/4/2/4622-runtime-dependency-refresh/tasks.md`, `mist-ops-platform/requirements.txt`, `requirements-dev.txt`, and `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py`.
- Only the ops requirements file and the root requirements files pin the package. The other paths hold a mapping, a text note, or a test.
- The local map at `src\foundation\support\refactors\package_import_map.py` line 32 maps the pip name to the import name `dateutil` (S-16). It does not import the package.
- The search index can lag (U-9).

## R8. Dependabot rule syntax and scope

- The repository already uses `dependency-name` with `update-types: ["version-update:semver-major"]` for TypeScript (RC-24). The same key format applies to python-dateutil.
- The pip entry targets `directory: "/"` (RC-23). PR #4890 changes `mist-ops-platform/requirements.txt` with the branch name `dependabot/pip/python-dateutil-4.0.0`. The name has no directory segment. The branch name suggests that the root entry produced that PR (inference). Whether the same entry produces future PRs for that file is unverified (U-1).
- A search of the `github/docs` repository for Dependabot ignore keys returned no result (S-17). The upstream behavior for security updates is unverified (U-3).

## R9. Repository rules that apply

- Each Dependabot update pull request stays open. Copilot instructions forbid closing update pull requests (RC-35). This rule governs D-4.
- Each change adds one changelog fragment (RC-40). The fragment name keeps its first form after the pull request opens (RC-42, RC-43).
- The guard for root exports is the test that the `dependency_lock` job runs (RC-08, RC-30). It reads root exports only, so it does not cover the ops requirements file.
- The pip-audit job scans root requirements only (RC-09). No gate audits the ops requirements file (analysis F-3).
- The record route uses the base-5 digits of the issue number (RC-38). The number 4908 has the digits 1 2 4 1 1 3 in base 5, padded to eight digits. The route folder is absent (RC-49).

## R10. Local gates that apply to T-LOCAL-GATES

- Applicable: Compile, Lint, Format, Tests, Symbols, Security lint, Complexity, Test quality, and STE (Local gates table in copilot instructions, RC-32). Citations applies too (`check-citations src tests`, the citation_lint row of `documentation/quality-gates.md`, file blob in RC-36).
- Not applicable to `tests/`: Types (RC-11), Dead code (RC-12), Docstrings (RC-13, RC-14), and Code quality (RC-10). Their paths exclude `tests/`.
- Not applicable: Dependency audit (RC-33). No requirements file changes. Dependency lock and exports (RC-08) runs in CI, and T-REMOTE-CI reads its result.
- Not applicable: Safe sweep, Menu reference, Diagram, Mermaid, Exclusion drift. The change touches none of their inputs.

## R11. Mist API, SDK, container, and skills

- Mist API: not applicable. The change makes no API request and no endpoint claim.
- SDK: not applicable. The pinned `mistapi` is not part of the failing resolution, and the record makes no SDK claim.
- Container: not applicable to the change. Principle IV steps 10 to 12 are handled in D-7 (RC-34, S-18).
- Other documents: `documentation\development-setup.md`, `documentation\architecture.md`, and `documentation\operator-guide.md` need no change for this issue (S-18).
- Skills: none loaded. No listed skill covers pip resolution, Dependabot policy, or GitHub Actions logs.

## D-1. Keep the ops pin at 2.9.0.post0

- **Alternatives**: (A) Keep `2.9.0.post0`. (B) Accept `4.0.0` and upgrade celery to a release that accepts it. (C) Edit the requirements file by hand to `4.0.0` and keep celery.
- **Chosen**: A.
- **Reason**: B is not available. The newest celery release pins the older version (RC-50, RC-53). C fails the same resolver check (S-4).
- **Risk**: The ops platform receives no python-dateutil update until a celery release relaxes its pin. No runtime defect is known in 2.9.0.post0. The advisory status is unchecked (U-6).

## D-2. Ignore python-dateutil major updates in the pip entry

- **Alternatives**: (A) Ignore `version-update:semver-major` for python-dateutil in the pip entry. (B) Ignore every update of python-dateutil. (C) Add a separate pip entry for `/mist-ops-platform`. (D) Add no rule.
- **Chosen**: A.
- **Reason**: The rule blocks each major release that Dependabot could propose for the ops pin. Those releases are 3.0.0 and 4.0.0 (RC-54, S-11). The root pin at 4.0.0 can still receive 4.x patch and minor updates. No 2.x minor release exists, so the rule covers every candidate (RC-54).
- **Risk**: The rule may not cover the ops requirements file (U-1). Root major updates also pause. Caution: a revert restores the proposal path and repeats the failure.
- **Rejected reasons**: B pauses root 4.x patch updates without a reason. C cannot stop the root entry from proposing the ops file (RC-23, R8). D repeats the failure each week.

## D-3. Add the guard cases to the existing parity module

- **Alternatives**: (A) Add cases to `tests/guardrails/test_dependency_declaration_parity.py`. (B) Add a new file under `tests/guardrails/`. (C) Add tests under `mist-ops-platform/tests/`.
- **Chosen**: A.
- **Reason**: `tests/guardrails/` already holds 79 tracked children (RC-31). A new file adds a direct child to a noncompliant parent, which Principle I forbids. The module already checks dependency declarations (RC-29, same blob, docstring lines 1 to 6). Tests under `mist-ops-platform/tests/` run in a later step of the ops job (RC-02 shows the install step), so they do not run when the install step fails.
- **Risk**: The module scope widens. The module docstring names the ops pin and the Dependabot rule.

## D-4. Leave PR #4890 and its branch unchanged

- **Alternatives**: (A) Leave PR #4890 open for a maintainer. (B) Close PR #4890 from this change. (C) Push a fix to the Dependabot branch.
- **Chosen**: A.
- **Reason**: Copilot instructions forbid closing update pull requests (RC-35). AGENTS forbids a push to a branch that another agent owns (S-15). Dependabot owns the branch.
- **Risk**: PR #4890 stays red until a maintainer acts (U-2). Caution: the stale red check can block a merge queue. The maintainer applies the Dependabot ignore command or closes the pull request.

## D-5. Limit the scope to python-dateutil

- **Alternatives**: (A) Fix only python-dateutil. (B) Fix python-dateutil and deepdiff in PR #4889. (C) Add a generic policy for every ops requirements bump.
- **Chosen**: A.
- **Reason**: AGENTS requires one concern for each issue (S-15). PR #4889 fails on a deepdiff upper bound that the ops pyproject declares (RC-22). Issue #4907 tracks that failure (S-7). Its cause is not examined here (U-8).
- **Risk**: The deepdiff failure remains until issue #4907 closes.

## D-6. Do not upgrade celery

- **Alternatives**: (A) Keep celery 5.7.0. (B) Upgrade to the newest release. (C) Upgrade to the upstream `main` declaration.
- **Chosen**: A.
- **Reason**: The newest release pins the exact older version (RC-50, RC-53). Upstream `main` is unreleased (RC-52). A celery upgrade changes runtime behavior and widens the scope (AGENTS, one concern for each issue).
- **Risk**: The ops pin stays old until a celery release relaxes its requirement. The Dependabot rule keeps that state (D-2).

## D-7. Skip Principle IV steps 10 to 12

- **Alternatives**: (A) Skip the wait, the revision check, and the deployment, with the reason recorded. (B) Dispatch `container-build.yml` manually after the merge. (C) Hold the merge until a product change exists.
- **Chosen**: A.
- **Reason**: The workflow runs only for a push that changes a product file or for a manual dispatch (RC-34). This change changes no product file. The local container document lists the image inputs as `src/`, `web_portal/`, `MistHelper.py`, `requirements.txt`, and the `Containerfile` (S-18, context only). This change touches none of them. AGENTS asks for a run only when a check needs it (S-15), so B spends runner minutes without need. C blocks an approved fix.
- **Risk**: The constitution text presumes an image build. The owner confirms the exception in review (analysis F-6).

## D-8. Add one changelog fragment

- **Alternatives**: (A) Add `changelog.d/issue-4908-ops-platform-dateutil-pin.md`. (B) Add no fragment, because the change is not visible to operators.
- **Chosen**: A.
- **Reason**: The constitution requires one fragment for each change (RC-40). Principle I allows one unique record under a process folder (RC-39, same section).
- **Risk**: The fragment reads as an operator note. The bullet names the change as a fix in the CI gate.

## D-9. Branch, commit type, and labels

- **Alternatives**: (A) Branch `fix/4908-ops-platform-dateutil-pin`, commit type `fix(ci)`, label `in-progress`. (B) Branch with type `chore`. (C) Branch with type `feat`.
- **Chosen**: A.
- **Reason**: The change repairs a failing gate, so the type is `fix` (S-15). The labels `bug` and `ci` already sit on the issue (S-6). The label `quality-gate` is managed by the sync job, so the record does not remove it. The label `in-progress` claims the issue (S-15).
- **Risk**: None known. The record adds no new label.

## Remote verification table

Each row is one remote check. The table has 55 rows. Result counts: present 52, absent 3, partial 0, stale 0.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Job `ops_platform_pytest` is named `pytest (ops platform)` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1122 |
| RC-02 | Install step runs pip for the ops requirements | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1162 |
| RC-03 | Failing merge commit carries the same ci.yml | .github/workflows/ci.yml | e30d4a95ae5f084becf4fcee7e0a2ba2944794ea | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1162 |
| RC-04 | PYTHON_VERSION defaults to 3.15 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 77 |
| RC-05 | OPS_PLATFORM_COVERAGE_THRESHOLD is 56 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 116 |
| RC-06 | OPS_PLATFORM_MIN_TESTS is 390 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 121 |
| RC-07 | Ops job comment says it runs 300 tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1135 |
| RC-08 | The dependency_lock job runs the root export guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| RC-09 | The pip-audit step scans root requirements.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 498 |
| RC-10 | SRC_PATH scope is src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| RC-11 | MYPY_PATHS scope excludes tests/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-12 | VULTURE_PATHS scope excludes tests/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-13 | PYDOCSTYLE_PATHS scope excludes tests/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-14 | INTERROGATE_PATHS scope excludes tests/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-15 | Ops requirements pin celery==5.7.0 | mist-ops-platform/requirements.txt | main | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | present | 27 |
| RC-16 | Ops requirements pin python-dateutil==2.9.0.post0 | mist-ops-platform/requirements.txt | main | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | present | 157 |
| RC-17 | PR head pins python-dateutil==4.0.0 | mist-ops-platform/requirements.txt | 4be9d2e76a4d21df95305cf2b0ef4941fb4f4b82 | 1d81e15e517ec3e41b00f2e4a18f1bceefba0bef | present | 157 |
| RC-18 | Merge commit pins python-dateutil==4.0.0 | mist-ops-platform/requirements.txt | e30d4a95ae5f084becf4fcee7e0a2ba2944794ea | 1d81e15e517ec3e41b00f2e4a18f1bceefba0bef | present | 157 |
| RC-19 | Ops requirements pin six==1.17.0 | mist-ops-platform/requirements.txt | main | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | present | 176 |
| RC-20 | Ops pyproject requires Python 3.15 or newer | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 13 |
| RC-21 | Ops pyproject declares celery[redis]>=5.7 | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 20 |
| RC-22 | Ops pyproject bounds deepdiff below 9.0 | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 31 |
| RC-23 | Dependabot pip entry spans lines 3 to 11 | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 3 |
| RC-24 | Dependabot TypeScript rule is the repository precedent | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 80 |
| RC-25 | Dependabot has no python-dateutil rule | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 0 |
| RC-26 | Root requirements.txt pins python-dateutil==4.0.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 201 |
| RC-27 | Root requirements-dev.txt pins python-dateutil==4.0.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 341 |
| RC-28 | Root requirements-dev.txt pins pyyaml==6.0.4 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| RC-29 | Parity guard module builds paths with pathlib | tests/guardrails/test_dependency_declaration_parity.py | main | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 20 |
| RC-30 | Export guard reads root exports only | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 12 |
| RC-31 | Guardrails folder holds 79 tracked direct children | tests/guardrails | main | 17c7b7f3c0ec8acc4c4d338ea27a8eb1fa2203da | present | 0 |
| RC-32 | Local gates row for Ops platform | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 76 |
| RC-33 | Local gates row for Dependency audit | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 68 |
| RC-34 | Container build runs on a product file change or a dispatch | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RC-35 | Rule forbids closing update pull requests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| RC-36 | Quality gates row for ops_platform_pytest | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 70 |
| RC-37 | Gate issue for a pull request closes after a later run or PR close | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 160 |
| RC-38 | Route base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-39 | Five-Item Rule principle | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-40 | Each change MUST add one release-note fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-41 | Writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-42 | Fragment naming table | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 24 |
| RC-43 | Fragment writing rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 37 |
| RC-44 | STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-45 | Test quality configuration exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RC-46 | Test quality baseline exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RC-47 | Test quality preflight module exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-48 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-49 | Route folder for issue 4908 is absent | specs/numbered/0/0/1/2/4/1/1/3 | main | none | absent | 0 |
| RC-50 | Celery v5.7.0 pins python-dateutil==2.9.0.post0 | requirements/default.txt in celery/celery | v5.7.0 | 1264149009fad7b4f32f3f8620ebee02bd52f939 | present | 8 |
| RC-51 | Celery v5.7.0a1 declares python-dateutil>=2.8.2 | requirements/default.txt in celery/celery | v5.7.0a1 | 344f10732867b7b62a1d516f27044c47f9bb91d3 | present | 8 |
| RC-52 | Celery main declares python-dateutil>=2.9.0.post0 | requirements/default.txt in celery/celery | main | 8cf8421d77a9527b469974e6bdbbf9044f636ab3 | present | 8 |
| RC-53 | Newest celery release is v5.7.0 | releases of celery/celery | releases | none | present | 0 |
| RC-54 | Newest python-dateutil 2.x release is 2.9.0.post0 | releases of dateutil/dateutil | releases | none | present | 0 |
| RC-55 | No dateutil import under mist-ops-platform/src | mist-ops-platform/src | main | none | absent | 0 |

## Sources

- **S-1**: Local `.specify\memory\constitution.md`, section "Complexity-Driven SpecKit Escalation". Read in full.
- **S-2**: Local `.venv\Lib\site-packages\python_dateutil-4.0.0.dist-info\METADATA`. Lines 2 to 3 (name and version), 10 (license), 26 (Requires-Python), and 27 (Requires-Dist tzdata).
- **S-3**: GitHub PR #4890 body, read with `gh pr view 4890 -R jmorrison-juniper/MistHelper --json body`. The body states that dateutil 4.0 drops `six`.
- **S-4**: GitHub Actions run 45064318582, job 137336951691. Read with `gh run view 45064318582 -R jmorrison-juniper/MistHelper --log-failed` and `--json jobs`.
- **S-5**: GitHub PR #4890 metadata, read with `gh pr view 4890 -R jmorrison-juniper/MistHelper --json files,body,state,mergedAt,headRefName,headRefOid,statusCheckRollup`. The state is OPEN, `mergedAt` is null, and the only file is `mist-ops-platform/requirements.txt` (+1, -1).
- **S-6**: GitHub issue #4908, read with `gh issue view 4908 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author`. No comment exists.
- **S-7**: GitHub PR #4889 title and head, read with `gh pr view 4889`. The title is `chore: bump deepdiff from 8.6.2 to 9.2.1`. Issue #4907 names the same gate.
- **S-8**: GitHub Actions run 45774119357 on `main` (workflow_dispatch), read with `gh run view --json jobs`. The jobs `pytest (ops platform)` and `Ruff (ops platform)` report success.
- **S-9**: GitHub commit `e30d4a95ae5f084becf4fcee7e0a2ba2944794ea`, read with `gh api repos/jmorrison-juniper/MistHelper/commits/e30d4a95ae5f084becf4fcee7e0a2ba2944794ea`. Its parents are `00d9a16e998b0cb5e10b6ed77da0fa909670d64f` and `4be9d2e76a4d21df95305cf2b0ef4941fb4f4b82`.
- **S-10**: https://api.github.com/repos/celery/celery/releases?per_page=6 (read with `gh api`). The newest release is `v5.7.0`.
- **S-11**: https://api.github.com/repos/dateutil/dateutil/releases?per_page=8 (read with `gh api`).
- **S-12**: https://api.github.com/repos/celery/celery/contents/requirements/default.txt?ref=v5.7.0 and the same path with `ref=v5.7.0a1` and `ref=main`. Read with `gh api`.
- **S-13**: https://api.github.com/search/code?q=dateutil+repo:jmorrison-juniper/MistHelper (read with `gh api -X GET`). It returns 7 paths.
- **S-14**: https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1 (read with `gh api`). The tree is not truncated and holds 11404 entries.
- **S-15**: Local `AGENTS.md`, sections "Git flow", "Parallel agents and shared state", and "GitHub Actions minutes". Read in full. Each rule matches its RC row where a remote row exists.
- **S-16**: Local `src\foundation\support\refactors\package_import_map.py` line 32.
- **S-17**: https://api.github.com/search/code?q=update-types+dependency-name+repo:github/docs+path:dependabot (read with `gh api -X GET`). It returns zero results.
- **S-18**: Local `documentation\container-deployment.md` lines 290 to 292 (context only, not a decision input). Local `documentation\development-setup.md` lines 17, 28, 137, and 141 describe the root setup only. Local `documentation\architecture.md` and `documentation\operator-guide.md` have no match for dateutil, celery, Dependabot, or the ops requirements.

## Unverified

- **U-1**: Dependabot applies the pip entry to `mist-ops-platform/requirements.txt` in later runs. Reason: PR #4890 is the only evidence. T-MERGE checks the next run.
- **U-2**: Dependabot closes or rewrites PR #4890 after the rule merges. Reason: no upstream behavior was read. A maintainer decides (D-4).
- **U-3**: The ignore rule covers Dependabot security updates. Reason: the search of the docs repository returned no page (S-17).
- **U-4**: The celery 5.7.0 wheel metadata matches `requirements/default.txt` at tag `v5.7.0`. Reason: the PyPI JSON response was truncated at 4000 characters. The CI log states the same pin (S-4).
- **U-5**: The route parents under `specs\numbered\` hold five or fewer children after the record is added. Reason: the counts come from the local checkout (route parent counts were 1, 1, 2, 3, 5, 2, and 1). The remote counts were not read.
- **U-6**: The advisory status of python-dateutil 2.9.0.post0 is unchecked. Reason: the change keeps that version, and no advisory source was read.
- **U-7**: The ops job passes after the fix. Reason: CI has not run on the fix branch. T-REMOTE-CI checks it.
- **U-8**: PR #4889 fails for the same cause as issue #4908. Reason: the deepdiff failure was not examined. Issue #4907 owns that analysis.
- **U-9**: The code search index covers every file on `main`. Reason: the index can lag. RC-55 depends on the index.
