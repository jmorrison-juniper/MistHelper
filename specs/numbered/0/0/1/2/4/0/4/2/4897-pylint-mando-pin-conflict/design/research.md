# Research: Pylint gate failure from the mando 0.8.2 pin

Each decision names the choice, the reason, the alternatives, and the risk. Each fact cites a remote check, shown in the table near the end of this file. A local file matches main when its blob SHA matches the remote blob SHA.

## Root cause

- The check `Pylint (score gate)` failed. Job 137338442217 of workflow `Quality Gates` in run 45064243269 failed at step 4, `Install dependencies`. Step 5, `Run Pylint`, did not run. (RC-01, RC-02, RC-29)
- The log shows `Collecting mando==0.8.2 (from -r requirements-dev.txt (line 179))` at log line 624. (RC-30)
- The log shows `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` at log line 932. (RC-30)
- The log shows `radon 6.0.1 depends on mando<0.8 and >=0.6` at log line 936. (RC-30)
- The log ends with `ERROR: ResolutionImpossible` at line 945. (RC-30)
- Pull request #4888 changes one file. It changes `mando` from 0.7.1 to 0.8.2 at line 179. (RC-12, RC-13)
- Main pins `mando==0.7.1` at line 179 and `radon==6.0.1` at line 365. Base commit `00d9a16e` has the same blob. (RC-08, RC-09, RC-11)
- `uv.lock` locks `mando` at 0.7.1 at line 1301. It locks radon 6.0.1 at line 2428, with a name-only mando dependency. (RC-15, RC-16)
- The file header names `uv export` as the generator. A hand edit to the file breaks the export guard. (RC-10, RC-23)
- Radon 6.0.1 requires `mando (<0.8,>=0.6)`. The installed metadata and PyPI agree. (RC-25, RC-26)
- The issue cites commit `5bb4b385`, which is the test merge. The run head is `e86098cd`. (RC-27, RC-28)
- 26 of 28 failed jobs log one resolution error each. The other two failed jobs are aggregate jobs. (RC-31)
- The Windows checks in two other runs log the same error at line 1003. (RC-32)
- Run 45774119357 on main passed. Its Pylint job and its dependency lock job passed. (RC-33, RC-34)

## R1. Keep mando at 0.7.1

- **Decision**: Keep `mando==0.7.1` in `requirements-dev.txt` at line 179. Do not change `uv.lock` or `pyproject.toml`.
- **Rationale**: PyPI reports radon 6.0.1 as the current release. Radon requires `mando` below 0.8. A mando 0.8 pin cannot install with radon 6.0.1. Main already holds 0.7.1, and its lock and export checks pass. (RC-08, RC-26, RC-34)
- **Alternatives considered**:
  - Raise mando to 0.8.2 and radon to a release that accepts it. Rejected: PyPI has no such radon release. (RC-26)
  - Remove radon and replace the complexity gate. Rejected: the Complexity row of the local gates table depends on radon. The change is larger than this issue. (RC-37)
  - Keep mando at 0.8.2 and remove radon from the dev extra. Rejected for the same reason as the previous option.
- **Risk**: mando stays one minor version behind. mando is a development-only package, because `requirements.txt` does not pin it. (RC-17) Decision D-2 limits the update stream.

## R2. Add a Dependabot ignore entry for mando 0.8 and later

- **Decision**: Add an `ignore` list to the pip stream of `.github/dependabot.yml`. The list names `mando` with `versions: [">= 0.8"]`.
- **Rationale**: Dependabot created the bump commit on 2026-11-22. The pip stream runs weekly. Without an entry, the same bump can return each week. The npm stream already uses an `ignore` list, so the repository has this pattern. (RC-18, RC-19, RC-20, RC-28)
- **Alternatives considered**:
  - Close each bump by hand. Rejected: the bump returns on each scheduled run.
  - Disable the pip stream. Rejected: the stream updates every other pip pin.
  - Ignore only major updates. Rejected: `versions` names the blocked range directly.
- **Risk**: Dependabot may not honor the `versions` key. This risk remains unverified. (U-1) A security fix that exists only in mando 0.8 would go unseen. pip-audit scans `requirements.txt` only, and mando is development-only. (RC-07, RC-17) This record accepts the risk for development tooling.

## R3. Add one pin test to the existing lock guard module

- **Decision**: Add `test_pinned_mando_satisfies_radon_requirement` to `tests/guardrails/test_dependency_lock_file.py`. Add `import importlib.metadata` to the same module.
- **Rationale**: The test names the failing rule. It reads the installed radon requirement with `importlib.metadata.requires("radon")`. The lock stores no radon range, so a lock parse cannot see the rule. (RC-16, RC-24, RC-25)
- **Alternatives considered**:
  - Rely on the existing lock and export guards. Rejected: their messages name `mando` and stale exports, and they do not name radon. (RC-23, RC-24)
  - Add a new file under `tests/guardrails`. Rejected: the directory holds 79 direct children, so a new child breaks the five-item rule. (RC-49)
  - Parse the range of radon from `uv.lock`. Rejected: the lock names mando without a range. (RC-16)
- **Risk**: The test reads the installed radon. If radon is missing, the test fails with a metadata error. The module already holds more than five top-level names. (RC-24) Complexity Tracking records that debt.

## R4. Keep the pylint threshold and scope

- **Decision**: Keep `PYLINT_THRESHOLD` at 9.5 and `SRC_PATH` at `src/`.
- **Rationale**: Main passes the gate at the current threshold. (RC-05, RC-33) The quality-gates document states the same floor. (RC-39) A lower floor hides a regression that the gate exists to catch. Removing the job removes a gate that every pull request runs. (RC-01, RC-02)
- **Alternatives considered**:
  - Lower the threshold to pass the check. Rejected for the reason in the rationale.
  - Remove the Pylint job. Rejected: the job is a required quality check.
- **Risk**: None for this change.

## R5. Close pull request #4888 after the fix merges

- **Decision**: Do not merge pull request #4888. Close it after the fix merges.
- **Rationale**: The branch cannot pass while the radon 6.0.1 pin stays in place. A closed pull request removes the red check. The implementer must not push to the Dependabot branch, because another agent owns it. (RC-44)
- **Alternatives considered**:
  - Push a revert to `dependabot/pip/mando-0.8.2`. Rejected: Dependabot owns that branch. (RC-44)
  - Keep the pull request open. Rejected: the open red check confuses the maintainers.
  - Ask Dependabot to ignore the version with a command. Rejected: the config entry in R2 covers the same range, and a command does not change the repository.
- **Risk**: The instruction file says not to close update pull requests. (RC-38) That rule targets the title-fix case. This closure removes one pull request, and it does not disable the stream.

## R6. Add a changelog fragment

- **Decision**: Add `changelog.d/issue-4897-pylint-mando-pin.md`.
- **Rationale**: The constitution says each change MUST add one unique fragment. (RC-45) The constitution supersedes other practice documents when they conflict. (RC-46) The README exempts internal-only changes. (RC-47) The constitution controls the conflict. The fragment name follows the issue-only rule, and the guard accepts that name. (RC-48)
- **Alternatives considered**:
  - Add no fragment, following README rule 4. Rejected: the constitution governs the conflict.
- **Risk**: One extra file enters `changelog.d`, which already holds 335 children. (RC-50) The constitution allows this process record.

## Remote verification

Each row is one remote check. The `Ref` column names the commit, the branch, or the source. The `Blob SHA` column names the git blob or the commit tree.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | The workflow file defines the name `Quality Gates` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| RC-02 | The workflow file defines job `Pylint (score gate)` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 504 |
| RC-03 | Step `Install dependencies` in the Pylint job installs `requirements-dev.txt` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 522 |
| RC-04 | Step `Run Pylint` runs pylint on `SRC_PATH` with `PYLINT_THRESHOLD` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| RC-05 | `PYLINT_THRESHOLD` defaults to 9.5 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 122 |
| RC-06 | Job `Dependency lock and exports` runs `uv lock --check` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-07 | The pip-audit job scans `requirements.txt` only | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 498 |
| RC-08 | `requirements-dev.txt` pins `mando==0.7.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-09 | `requirements-dev.txt` pins `radon==6.0.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-10 | The `requirements-dev.txt` header names `uv export` as its generator | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 2 |
| RC-11 | `requirements-dev.txt` has the same blob on base commit `00d9a16e` and on main | `requirements-dev.txt` | 00d9a16e998b0cb5e10b6ed77da0fa909670d64f | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-12 | The pull request branch pins `mando==0.8.2` | `requirements-dev.txt` | dependabot/pip/mando-0.8.2 | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RC-13 | Pull request #4888 changes exactly one file, `requirements-dev.txt` | `requirements-dev.txt` | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 0 |
| RC-14 | `pyproject.toml` declares `radon==6.0.1` in the dev extra | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RC-15 | `uv.lock` locks `mando` at 0.7.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-16 | `uv.lock` locks radon 6.0.1 with a name-only `mando` dependency and no version range | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2428 |
| RC-17 | `requirements.txt` pins no `mando` or `radon` | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 129 |
| RC-18 | The Dependabot pip stream has no ignore entry | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-19 | The Dependabot pip stream runs weekly | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 6 |
| RC-20 | The Dependabot npm stream holds an ignore list | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| RC-21 | The policy snapshot holds the pip stream without an ignore entry | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 20 |
| RC-22 | The policy guard compares the full Dependabot policy with the snapshot | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RC-23 | The export guard compares checked-in exports with `uv export` output | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RC-24 | The lock guard checks each requirement against its locked version | `tests/guardrails/test_dependency_lock_file.py` | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| RC-25 | Installed radon 6.0.1 declares `Requires-Dist: mando (<0.8,>=0.6)` | `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` | local working tree | 00765926c0dd3906f1e65015d4cd9d0b87a2b506 | present | 31 |
| RC-26 | PyPI reports radon 6.0.1 as the current release, and it requires `mando (<0.8,>=0.6)` | `https://pypi.org/pypi/radon/json` | upstream, fetched 2026-11-26 | not applicable: JSON response | present | 0 |
| RC-27 | Commit `5bb4b385` is the test merge of `e86098cd` into `00d9a16e` | `repos/jmorrison-juniper/MistHelper/commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | tree 38314c25a56caeeaf0ce01777caa00014bd7cb32 | present | 0 |
| RC-28 | Commit `e86098cd` is the pull request head, dated 2026-11-22 | `repos/jmorrison-juniper/MistHelper/commits/e86098cdc2b189d217805b3b4060ef609cbc37af` | e86098cdc2b189d217805b3b4060ef609cbc37af | tree 38314c25a56caeeaf0ce01777caa00014bd7cb32 | present | 0 |
| RC-29 | Job 137338442217 failed at step `Install dependencies`, and step `Run Pylint` did not run | `.github/workflows/ci.yml` | e86098cdc2b189d217805b3b4060ef609cbc37af | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |
| RC-30 | The log of job 137338442217 names the mando 0.8.2 conflict and the radon 6.0.1 requirement | `CI log: run 45064243269, job 137338442217` | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: CI log | present | 936 |
| RC-31 | 26 of 28 failed jobs in run 45064243269 log one resolution error each. Two aggregate jobs fail at `Verify dependency lock job` and `Verify E2E shards`. | `CI logs: run 45064243269, 28 failed jobs` | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: CI logs | present | 0 |
| RC-32 | The Windows checks in runs 45064235051 and 45064235097 log the same resolution error | `CI logs: jobs 137336693688 and 137336693895` | e86098cdc2b189d217805b3b4060ef609cbc37af | not applicable: CI logs | present | 1003 |
| RC-33 | Run 45774119357 on main passed job 139754538884, `Pylint (score gate)` | `.github/workflows/ci.yml` | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 504 |
| RC-34 | Run 45774119357 on main passed job 139753527647, `Dependency lock and exports` | `.github/workflows/ci.yml` | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 634 |
| RC-35 | `spec-route.ps1` sets an eight-segment width and base 5 | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-36 | The Known pitfalls section exists | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 540 |
| RC-37 | The Local gates row for Complexity names radon | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 66 |
| RC-38 | The instruction file says not to close update pull requests | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| RC-39 | `quality-gates.md` states the pylint score floor of 9.5 | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 58 |
| RC-40 | `development-setup.md` installs `requirements-dev.txt` for local development | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |
| RC-41 | `architecture.md`, `container-deployment.md`, and `operator-guide.md` name no `mando` or `radon` pin | `documentation/architecture.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce, f06228bc6bbe77cc009f956403872a06462466ea, 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| RC-42 | No record path that contains `4897` exists on main | `specs` (tree search for `4897`) | main | not applicable: no tree entry | absent | 0 |
| RC-43 | `AGENTS.md` has the Writing style section | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-44 | `AGENTS.md` says not to push to a branch that another agent owns | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 254 |
| RC-45 | The constitution says each change MUST add one unique fragment | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-46 | The constitution says it supersedes other practice documents when conflicts arise | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 528 |
| RC-47 | `changelog.d/README.md` rule 4 exempts an internal-only change from a fragment | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-48 | The changelog guard accepts issue-named fragments | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-49 | `tests/guardrails` holds 79 direct children on main | `tests/guardrails` | main | not applicable: directory | present | 0 |
| RC-50 | `changelog.d` holds 335 direct children on main | `changelog.d` | main | not applicable: directory | present | 0 |

## Sources

### Local paths (read-only)

- `AGENTS.md` lines 40 and 254 (RC-43, RC-44).
- `.github\copilot-instructions.md` lines 66, 533, 540, and 574 (RC-36, RC-37, RC-38).
- `.github\workflows\ci.yml` lines 9 to 529 and 634 to 650 (RC-01 to RC-06). Line 522 cites issue #1779 (RC-03).
- `tests\guardrails\test_dependency_export.py` line 1 cites issue #3400 (RC-23).
- `.specify\memory\constitution.md` lines 409 to 412 and 528 to 529 (RC-45, RC-46).
- `changelog.d\README.md` lines 19 to 58 (RC-47).
- `tests\guardrails\test_dependency_export.py`, `test_dependency_lock_file.py`, `test_pr_title_workflow.py`, and `test_changelog_fragment_policy.py` (RC-21 to RC-24, RC-48).
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` line 31 (RC-25).
- `.specify\templates\` (spec, plan, tasks, and checklist templates) for the record layout.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` for the record shape only.

### GitHub reads (GET only)

- Issue 4897: title, body, labels, state, and author.
- Pull request 4888: body, state, head commit, and file list.
- Run 45064243269 and its failed jobs, plus the log lines of job 137338442217.
- Run 45064235051 and run 45064235097, for the Windows checks.
- Run 45774119357 on main, jobs 139754538884 and 139753527647.
- Commits `5bb4b385` and `e86098cd`.
- Contents and tree queries for each remote path in the table above.

### Upstream URLs

- https://pypi.org/pypi/radon/json, fetched 2026-11-26. The `info` block reports version 6.0.1 and `requires_dist` `mando (<0.8,>=0.6)`. (RC-26)
- The record fetched https://pypi.org/pypi/mando/json. The response stops before the version field, so no claim uses it. (U-4)
- https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file was not readable. The fetch tool blocked the address. (U-1)

### Not applicable

- The Mist API OpenAPI file and the mistapi source were not read. This change makes no Mist call. The runtime pin `mistapi==0.64.1` at `requirements.txt` line 129 stays unchanged. (RC-17)
- The record loads no skill. No Podman or Juniper device question applies.

## Unverified

- U-1: Dependabot accepts the `versions` key with the value `>= 0.8` in an ignore entry. Reason: the fetch tool blocked the docs page, and a lookup in the github/docs tree found no matching path. Action: check the next scheduled Dependabot run.
- U-2: This record does not investigate the meaning of the pip note that mando has "no matching distributions available for your environment". Reason: the decision rests on the radon requirement in the same log.
- U-3: Dependabot raises the bump again without the ignore entry. Reason: Dependabot run history is not readable through the available tools. Action: the User Story 3 check in the spec.
- U-4: The latest mando release on PyPI. Reason: the JSON response stops before the version field. No decision depends on it.
