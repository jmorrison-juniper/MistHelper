# Research: Keep mando inside the radon requirement

## Terms

- **Check**: The name that a pull request shows for one result.
- **Job**: The unit in `.github/workflows/ci.yml` that reports a check. A job has an ID and a name.
- **Step**: One named command group inside a job.
- **Pin**: A line in requirements-dev.txt that uses `==`.
- **Export**: The file that `uv export --locked` writes from uv.lock.

## R1. Failing Checks and the Failing Rule

Run 45064243269 is a Quality Gates run. Its event is `pull_request`. Its title is "chore: bump mando from 0.7.1 to 0.8.2". Its head is e86098cd. The issue cites merge commit 5bb4b385, which has e86098cd as its second parent. The run has 33 jobs. 28 jobs fail. Five jobs pass: Mermaid syntax lint, Menu reference drift, ops-portal, pytest (ops platform), and Sync quality-gate issues.

No test runs on the pull request head. The failing rule is the pip resolver rule. pip refuses a set of requirements that conflict.

Exact log text from job 137338442288, check `pytest coverage shard (root-units)`, at 2026-11-22T20:11:01Z:

```text
ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.
The conflict is caused by:
    The user requested mando==0.8.2
    radon 6.0.1 depends on mando<0.8 and >=0.6
ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

The failing checks of run 45064243269 and the two Windows runs:

| Check | Job ID | Failing step | Line in ci.yml or workflow |
| - | - | - | - |
| pytest (coverage gate) | 137338980629 | Verify dependency lock job | ci.yml 339 |
| pytest coverage shard (root-and-contracts) | 137338442294 | Install dependencies | ci.yml 293 |
| pytest coverage shard (root-units) | 137338442288 | Install dependencies | ci.yml 293 |
| pytest coverage shard (upgrade-units) | 137338442235 | Install dependencies | ci.yml 293 |
| pytest coverage shard (upgrade-contracts) | 137338442226 | Install dependencies | ci.yml 293 |
| Dependency lock and exports | 137336719111 | Run pip install -r requirements-dev.txt | ci.yml 646 |
| Ruff (lint) | 137336719229 | Run pip install -r requirements-dev.txt | ci.yml 163 |
| Ruff (ops platform) | 137336719241 | Install ruff | ci.yml 1232 |
| Black (format check) | 137339161296 | Run pip install -r requirements-dev.txt | ci.yml 194 |
| mypy (strict) | 137338084785 | Install dependencies | ci.yml 235 |
| Pylint (score gate) | 137338442217 | Install dependencies | ci.yml 522 |
| Bandit (security) | 137336719159 | Run pip install -r requirements-dev.txt | ci.yml 435 |
| pip-audit (CVE scan) | 137338084755 | Run pip install -r requirements-dev.txt | ci.yml 483 |
| Radon (complexity) | 137336719006 | Run pip install -r requirements-dev.txt | ci.yml 543 |
| Vulture (dead code) | 137336718674 | Run pip install -r requirements-dev.txt | ci.yml 563 |
| pydocstyle (docstring style) | 137336719204 | Run pip install -r requirements-dev.txt | ci.yml 582 |
| Interrogate (docstring coverage) | 137336719025 | Run pip install -r requirements-dev.txt | ci.yml 598 |
| Test quality ratchet (gate) | 137336719038 | Run pip install -r requirements-dev.txt | ci.yml 615 |
| CodeQL verdict register check | 137336719141 | Run python -m pip install -r requirements-dev.txt | ci.yml 403 |
| Diagram reference lint | 137336718990 | Run python -m pip install -r requirements-dev.txt | ci.yml 669 |
| Citation reference lint | 137336719093 | Run python -m pip install -r requirements-dev.txt | ci.yml 701 |
| SpecKit task audit (advisory) | 137336719307 | Run python -m pip install -r requirements-dev.txt | ci.yml 746 |
| Quality exclusion drift (advisory) | 137336718972 | Run pip install -r requirements-dev.txt | ci.yml 765 |
| E2E shard (upgrade-portal) | 137338442186 | Install dependencies | ci.yml 841 |
| E2E shard (web-portal) | 137338442234 | Install dependencies | ci.yml 841 |
| E2E shard (websockets-tab) | 137338442334 | Install dependencies | ci.yml 841 |
| E2E smoke tests | 137339065340 | Verify E2E shards | ci.yml job at 954 |
| Upgrade portal journeys | 137339161249 | Install dependencies | ci.yml 991 |
| Native Windows timeout budget (run 45064235051) | 137336693688 | Install test dependencies | windows-timeout-budget.yml 48 |
| Native Windows audit report (run 45064235097) | 137336693895 | Install test dependencies | windows-audit-report.yml 48 |

The `E2E shard (web-portal)` and `Upgrade portal journeys` jobs also show failed upload steps. This record did not read those logs, so their cause is unverified (U-06).

## R2. The Check Named in the Issue

Issue #4894 names gate `pytest`. Three checks on the pull request contain `pytest` in their names:

- `pytest (coverage gate)` fails. Job 137338980629.
- Four `pytest coverage shard` checks fail.
- `pytest (ops platform)` passes. Job 137336719056.

The failing causal chain is:

1. The shard jobs run `pip install -r requirements.txt`, then `pip install -r requirements-dev.txt` (ci.yml lines 290 to 293). The second command fails.
2. The `Dependency lock and exports` job runs `pip install -r requirements-dev.txt` at line 646. It fails before `uv lock --check` at line 648 and the export guard at line 650.
3. The `pytest (coverage gate)` job needs `pytest_coverage_shards` and `dependency_lock` (ci.yml lines 332 to 334). Its first step, `Verify dependency lock job` (lines 339 to 346), exits 1 when the lock result is not `success`.
4. The `Ruff (ops platform)` job installs `../requirements-dev.txt` at line 1232. That file is the root file, so the same conflict occurs.

The `pytest (ops platform)` job passes. Its working directory is `mist-ops-platform` (ci.yml lines 1122 to 1162). Its install line 1162 reads the sub-project files, so it does not reach the root requirements-dev.txt.

## R3. Why radon Constrains mando

- requirements-dev.txt line 179 pins `mando==0.7.1`. Line 180 reads `# via radon`. Line 365 pins `radon==6.0.1` (RC-04, RC-06).
- pyproject.toml line 118 pins `radon==6.0.1` in the dev extra (RC-07). The dev extra is the source of the export.
- uv.lock line 1301 locks mando at `0.7.1` (RC-08). Line 2432 lists mando as a dependency of radon 6.0.1 (RC-09).
- The PyPI JSON for radon reports `info.version` 6.0.1 and `requires_dist` `mando (<0.8,>=0.6)` (RC-35). The version field is the latest release that PyPI reports.
- The local `.venv` holds `radon-6.0.1.dist-info/METADATA`. Its line 31 reads `Requires-Dist: mando (<0.8,>=0.6)` (RC-36).

Conclusion: the latest radon release forbids every mando 0.8.x release.

## R4. Dependabot Evidence

- The commit e86098cd carries the message field `dependency-type: direct:development` and `update-type: version-update:semver-minor`. The GitHub commit read confirms both fields.
- Pull request #4888 changes one line of requirements-dev.txt. The change adds one line and removes one line (RC-03).
- The pip update block of `.github/dependabot.yml` has no ignore entry (RC-20). The npm update block has an ignore entry with a reason comment. That entry is the style precedent (RC-21).

## R5. Other Evidence

- Issue #4894 is OPEN. It carries the labels `bug`, `ci`, and `quality-gate`. It has no comments. Its body names gate `pytest`, pull request #4888, branch `dependabot/pip/mando-0.8.2`, commit 5bb4b385, and run 45064243269.
- Pull request #4888 is OPEN and not merged. Its base is main, and its head is e86098cd.
- Pull request #4176 is MERGED, on 2026-10-13. It matched the search for `4894`. It does not link to issue 4894.
- The latest Quality Gates run on main, run 45774119357, concluded success at head f03c6c9b. So main passes the gates at its current head.
- Seven pull requests are open. Only pull request #4888 touches requirements-dev.txt among them.
- The search for `4894` returned merged pull request #4176. Its body links to hypothesis issue 4894 in another repository. This pull request does not link to issue 4894.
- Issue #1779 is closed. It created the pinned install rule. Its title reads "ci: nine gate tools install unpinned, so a new release can fail CI on an unrelated commit."
- Issue #3400 is open. Its title reads "Decide: pin the Python dependencies with a tracked lock file." The export guard cites it.
- Branch protection on main sets strict mode. It requires 15 contexts (RC-31).

## R6. Decisions

Each decision names the alternatives, the choice, the reason, and the risk.

### D-1 Keep mando at 0.7.1

- Decision: Keep mando at 0.7.1 in requirements-dev.txt, requirements.txt, and uv.lock. Change none of those files.
- Alternatives: (a) Keep 0.7.1. (b) Move radon to a release that accepts mando 0.8. PyPI lists no such release. (c) Force mando 0.8.2 with a uv override. Rejected, because pip reads the file and still fails the same way. The lock would also disagree with the radon metadata.
- Reason: The radon requirement forbids mando 0.8.x. The export guard requires the export to equal the uv output.
- Risk: mando lags until radon moves. D-3 and the removal condition in the ignore comment limit that risk.

### D-2 Close pull request #4888 Without a Merge

- Decision: Close pull request #4888 without a merge. Its comment names run 45064243269, job 137338442288, and the radon requirement. The comment links the fix pull request.
- Alternatives: (a) Close without a merge. (b) Edit the pull request into a different change. Rejected, because any mando 0.8.x bump fails while radon 6.0.1 is pinned. (c) Keep it open. Rejected, because its 30 failing checks remain on the record.
- Reason: The pull request cannot pass with any mando 0.8.x version.
- Risk: Dependabot may reopen the pull request. U-02 records that the branch state is unverified. D-3 stops the proposal.

### D-3 Ignore mando in the Pip Update Block

- Decision: Add `ignore:` with `dependency-name: "mando"` to the pip update block of `.github/dependabot.yml`.
- Alternatives: (a) Ignore every mando version update. (b) Ignore only versions from 0.8 upward. Rejected, because this repository holds no example of that syntax, and this record did not verify it. (c) Add no entry and close each new pull request. Rejected, because the bump repeats on each weekly run.
- Reason: The ignore entry stops the proposal at its source.
- Risk: Caution: the entry also blocks a mando 0.7.x update. Check mando advisories by hand. U-01 records that the handling of security updates is unverified.

### D-4 Put the Guard Tests in the Existing Test File

- Decision: Add class `TestDependabotPipIgnore` to `tests/guardrails/test_dependency_export.py`.
- Alternatives: (a) Use the existing file. (b) Add a new file to `tests/guardrails/`. Rejected, because the folder holds 77 files, and the Five-Item Rule forbids that child. (c) Add a new nested package. Rejected, because its folder is still a direct child of `tests/guardrails/`.
- Reason: The Five-Item Rule forbids a new direct child of a noncompliant parent. AGENTS.md prefers existing test files.
- Risk: The file scope grows. The module docstring names both checks to limit that risk.

### D-5 Add One Changelog Fragment

- Decision: Add `changelog.d/issue-4894-mando-radon-pin.md`.
- Alternatives: (a) Add one fragment. (b) Add none, and state the internal-only reason in the pull request body, as README rule 4 allows. Rejected, because the constitution requires one fragment for each change and supersedes practice documents (line 529).
- Reason: The constitution governs. The precedent fragment for issue #4727 covers a dependency change (RC-24).
- Risk: An internal entry adds release-note noise. The bullet names the pin and the issue. FR-010 tracks the policy conflict.

### D-6 Open Two Separate Issues

- Decision: Open Issue A for the fragment policy conflict. Open Issue B for the folder debt of 335 files in `changelog.d/`.
- Alternatives: (a) Open two issues. (b) Fix the policy text in this change. Rejected, because AGENTS.md requires one concern for each issue. (c) Record the items here only. Rejected, because the constitution requires a tracked remediation action.
- Reason: One concern belongs to one issue.
- Risk: The owner tracks two more items.

Human decisions: none. No decision falls in a section 6 category. The categories are licensing or legal text, destruction of production data, credential policy, and product priority.

## R7. Remote Verification Table

Method: The rows read the remote body through the contents API, or they read a GET response from the GitHub API. The local hash of requirements-dev.txt equals the remote blob, so the local lines match. The local `.venv` row and the PyPI row use the local file and the upstream JSON.

| Row | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Issue cites commit 5bb4b385, the pull_request merge commit | commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 38314c25a56caeeaf0ce01777caa00014bd7cb32 (tree) | present | 0 |
| RC-02 | Pull request head e86098cd is the Dependabot commit | commits/e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | 38314c25a56caeeaf0ce01777caa00014bd7cb32 (tree) | present | 0 |
| RC-03 | Pull request 4888 changes only requirements-dev.txt | pull request 4888 file list | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: pull request metadata | present | 0 |
| RC-04 | main pins mando 0.7.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-05 | Pull request head pins mando 0.8.2 | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RC-06 | main pins radon 6.0.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-07 | Dev extra pins radon 6.0.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RC-08 | uv.lock locks mando 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-09 | uv.lock lists mando as a dependency of radon 6.0.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RC-10 | pytest (coverage gate) reads the dependency lock result | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 339 |
| RC-11 | Dependency lock and exports installs requirements-dev.txt, then runs uv lock --check and the export guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 646 |
| RC-12 | pytest coverage shards install requirements-dev.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 293 |
| RC-13 | Ruff (ops platform) installs the root requirements-dev.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1232 |
| RC-14 | pytest (ops platform) installs its sub-project requirements | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1162 |
| RC-15 | Quality Gates runs on pull_request without a paths filter | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 16 |
| RC-16 | Native Windows timeout budget installs requirements-dev.txt | .github/workflows/windows-timeout-budget.yml | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 48 |
| RC-17 | Native Windows timeout budget push paths list requirements-dev.txt | .github/workflows/windows-timeout-budget.yml | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 14 |
| RC-18 | Windows audit report installs requirements-dev.txt | .github/workflows/windows-audit-report.yml | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 48 |
| RC-19 | Windows audit report push paths list requirements-dev.txt | .github/workflows/windows-audit-report.yml | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 14 |
| RC-20 | dependabot.yml pip update block has no ignore entry | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-21 | dependabot.yml npm update block has an ignore entry as style precedent | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| RC-22 | Export guard test compares uv export output with the exports | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RC-23 | Changelog README rule 4 adds no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-24 | Precedent fragment for a dependency alignment | changelog.d/issue-4727-runtime-dependency-exports.md | main | 95640e7ef5b4a1996cd38f6b1f234a37a5bb8f47 | present | 3 |
| RC-25 | Constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-26 | Constitution supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| RC-27 | Copilot instructions limit fragments to user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-28 | Copilot instructions require the eight-level base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 161 |
| RC-29 | Reference record 4920 exists in the managed route | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-30 | Container build runs after each merge through the Auto-merge dispatch | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 22 |
| RC-31 | Branch protection requires 15 contexts including pytest (coverage gate) with strict mode | branches/main/protection/required_status_checks | main | not applicable: GitHub API response | present | 0 |
| RC-32 | changelog.d holds 335 files on main | changelog.d | main | not applicable: directory count from tree listing | present | 0 |
| RC-33 | tests/guardrails holds 77 files and 2 directories on main | tests/guardrails | main | not applicable: directory count from tree listing | present | 0 |
| RC-34 | PyYAML 6.0.4 is pinned for the YAML test read | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| RC-35 | Upstream radon 6.0.1 is the latest release and requires mando below 0.8 | https://pypi.org/pypi/radon/json | PyPI info.version 6.0.1 | not applicable: upstream JSON | present | 0 |
| RC-36 | Local radon 6.0.1 metadata requires mando below 0.8 | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local working tree | not applicable: untracked local file | present | 31 |

## R8. Sources

Local, read only:

- AGENTS.md, in full.
- .github/copilot-instructions.md, in full. The local gates table is at lines 50 to 92.
- .specify/memory/constitution.md, in full.
- .specify/templates/spec-template.md, plan-template.md, tasks-template.md, and checklist-template.md, in full.
- specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv, for the record shape. The content was not copied.
- documentation/quality-gates.md, in full.
- documentation/development-setup.md, lines 125 to 145.
- documentation/development-tooling-migration.md, lines 85 to 105. It states that Dependabot does not update the requirements-dev.txt pin.
- changelog.d/README.md, in full.
- tests/guardrails/test_dependency_export.py, in full.
- .github/dependabot.yml, in full.
- pyproject.toml, lines 100 to 125.
- .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA, matched lines 3 and 31.
- The read-only draft validator in the drafts meta folder, read for its checks.

GitHub, GET requests only:

- Issue #4894 and its comments, which are empty.
- Pull request #4888, for its files, body, and check rollup.
- Pull request #4176, for the body text that matched the search.
- Run 45064243269, runs 45064235051 and 45064235097, and their failed-step logs.
- Commits 5bb4b385 and e86098cd.
- The recursive tree of main, with 11404 entries and no truncation.
- Contents of requirements-dev.txt on main and on the pull request head.
- Contents of ci.yml, dependabot.yml, pyproject.toml, both Windows workflows, container-build.yml, the export test, the changelog files, the copilot instructions, and the constitution.
- The uv.lock blob 5445b4eb382dc9f6dd5c351ba40c521f01f93165, with 446204 bytes.
- The required status checks of branch protection on main.
- The latest Quality Gates runs on main.
- The open pull requests, which number seven.
- Issues #1779 and #3400.

Upstream, fetched once:

- https://pypi.org/pypi/radon/json, the first 20000 characters, read on 2026-11-26.
- https://pypi.org/pypi/mando/json, the first 3000 characters, read on 2026-11-26. Its description says mando wraps argparse.

Not consulted, with reasons:

- Mist API OpenAPI files and endpoint lists. The issue concerns no endpoint behavior.
- The mistapi SDK. The issue does not call the SDK.
- documentation/architecture.md, container-deployment.md, and operator-guide.md. Runtime, container, and operator behavior are outside the issue. Architecture line 167 names requirements-dev.txt only.
- The skill tool. The issue has no Podman or Juniper device question, so no skill was loaded.

## R9. Unverified

- U-01: Dependabot handling of ignore entries for security updates. Reason: the Dependabot configuration reference was not fetched in this run.
- U-02: Whether a closed Dependabot pull request keeps its branch, and whether Dependabot reopens it. Reason: this run did not check that state.
- U-03: CI results of the fix pull request head. Reason: the pull request does not exist yet. T-REMOTE-CI records the results.
- U-04: Coverage and Pylint results of the current head. Reason: the install stopped first, so no test or lint step ran on the head.
- U-05: Any radon release after 6.0.1. Reason: PyPI was read once on 2026-11-26.
- U-06: Cause of the failed upload steps in `E2E shard (web-portal)` and `Upgrade portal journeys`. Reason: the logs of those steps were not read. The install failure is the recorded cause of each job.
