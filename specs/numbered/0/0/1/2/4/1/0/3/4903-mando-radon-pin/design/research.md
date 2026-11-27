# Research: Dependabot mando pin for the dependency_lock job

## Scope and Method

- **Issue facts**: Issue #4903 is open. Its title is "CI: quality-gate `dependency_lock` failed (PR #4888)". Its labels are `bug`, `ci`, and `quality-gate`. Its body names run 45064243269 and commit `5bb4b385`.
- **Linked work**: Pull request #4888 is the failing pull request. It is open, not merged, and based on `main`. Its head is `e86098cd`. A search for `4903` returned only pull request #323. Its six matches name `psf/black` issue 4903 in an upstream changelog, not issue 4903 of this repository.
- **Legacy record**: No folder named `4903-*` exists under `specs\` on the local checkout or on `main` (row RC-36).
- **Read-only rule**: Each `gh` call used GET requests only. No write command ran against GitHub. No build, test, install, or container command ran in the repository.
- **Skills**: No local skill applied. Podman, Juniper device behavior, and Mist API topics do not apply to this issue.
- **Mist API and mistapi**: Not applicable. The issue names no Mist API endpoint and no mistapi call.

## Research Findings

### R1. The failing check and step

- The check named "Dependency lock and exports" failed. Its job ID is `dependency_lock`, job record 137336719111, in workflow "Quality Gates" (row RC-04).
- Step 4, "Run pip install -r requirements-dev.txt", concluded `failure`. Steps 5 "Check dependency lock" and 6 "Check requirements exports" concluded `skipped`.
- The job definition is in `.github/workflows/ci.yml` lines 634 to 650 (rows RC-10 to RC-12).

### R2. The failing rule

The failed step log holds these lines (`gh run view 45064243269 --job 137336719111 --log-failed`):

```text
ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.
ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

The resolver explains the cause:

```text
radon 6.0.1 depends on mando<0.8 and >=0.6
```

The rule that fails is this radon constraint, `mando (<0.8,>=0.6)`. The pin that conflicts is `mando==0.8.2`, requested by pull request #4888 (row RC-07). The line numbers come from `requirements-dev.txt` on `main`: `mando==0.7.1` at line 179 (row RC-08) and `radon==6.0.1` at line 365 (row RC-09).

### R3. Local and upstream confirmation

- The local `.venv` radon 6.0.1 metadata holds `Requires-Dist: mando (<0.8,>=0.6)` at line 31 (row RC-48).
- PyPI lists radon 6.0.1 as the latest release. Its `requires_dist` holds `mando (<0.8,>=0.6)` (row RC-49).
- PyPI publishes mando 0.8.2, so the failure does not come from a missing release (row RC-50).

### R4. The main branch passes the same job

- Run 45774119357, on the `main` head `f03c6c9b`, passed the job. Job record 139753527647 concluded `success`, and steps 4 to 6 concluded `success` (row RC-06).
- The failure belongs to pull request #4888. The base branch does not fail.

### R5. The shared root cause

- Seven sampled failed jobs show the same resolver error (row RC-05). The other failed jobs were not sampled.
- `ci.yml` runs `pip install -r requirements-dev.txt` in eleven steps (lines 163, 194, 435, 483, 543, 563, 582, 598, 615, 646, and 765).
- The run holds 28 failed Quality Gates checks and 2 failed checks in other workflows. The sampled jobs all show the same error. The two other-workflow checks are not sampled (item U-7).
- Fourteen sibling issues cite pull request #4888 (row RC-51): issues 4891, 4892, 4893, 4894, 4895, 4896, 4897, 4898, 4899, 4900, 4901, 4902, 4904, and 4905.

### R6. Why the lock and export checks would also fail

- `uv.lock` locks `mando` 0.7.1 (row RC-13). `requirements-dev.txt` on the pull request head pins `mando==0.8.2`.
- `tests/guardrails/test_dependency_lock_file.py` checks each requirement against `uv.lock` (row RC-26). The check reports `mando: locked 0.7.1 does not satisfy ==0.8.2`.
- `tests/guardrails/test_dependency_export.py` compares the checked-in exports with `uv export --locked` output (row RC-27). The check reports `requirements-dev.txt` as a stale export.
- The two checks are skipped in the run. Item U-4 records this as a prediction from static evidence.

### R7. Why Dependabot creates the conflict

- `pyproject.toml` declares `radon==6.0.1` in the dev extra (row RC-15). It does not declare `mando` (row RC-16).
- `requirements-dev.txt` lists `mando==0.7.1` with the comment `# via radon` (row RC-08). Dependabot reads the pin in the file, not the radon constraint.
- The Dependabot pip update block has no `ignore` entry (row RC-18). Dependabot proposes `mando` 0.8.2 as a minor update, `version-update:semver-minor` (commit message of row RC-02).
- `requirements.txt` holds no `mando` entry (row RC-17). The runtime install does not need `mando`.

### R8. Gate documentation gap

- `documentation/quality-gates.md` holds no `dependency_lock` row and no `dependency_lock` text (row RC-23). The job list in the document omits the job.
- The complexity guard reads the document only for the radon limit sentence (row RC-29). A new row does not change that sentence.
- The install guide `documentation/development-setup.md` gives the `requirements-dev.txt` install commands (line 137). It names no mando or radon pin (row RC-52). This change needs no edit to that guide.

### R9. Policy guard constraint

- `tests/guardrails/test_pr_title_workflow.py` pins the complete Dependabot policy in `POLICY_SNAPSHOTS["dependabot"]` (row RC-20).
- The guard asserts that the policy equals the snapshot (row RC-21). A new `ignore` entry therefore fails the guard until the snapshot changes too.
- The guard lists mutations that must fail (row RC-22).

### R10. Changelog and record rules

- The changelog guard accepts `issue-<number>-<slug>.md` (row RC-30). The rule file names the same form (row RC-31).
- The guard requires one heading, one bullet, one change type word, and no version stamp (`tests/guardrails/test_changelog_fragment_policy.py`).
- No changelog fragment for issue 4903 exists on `main` (row RC-32).
- The route `specs/numbered/0/0/1/2/4/1/0/3/` does not exist on `main` (row RC-35). The route script computes the route from base 5 (rows RC-33 and RC-34). Issue 4903 converts to base-5 digits `00124103`, which gives the segments `0\0\1\2\4\1\0\3`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` exists on `main` (row RC-37). This record copies its shape, not its content.
- The process folder guard and the route contract test read the same rules (rows RC-38 and RC-39).

### R11. Constitution and repository rules

- The constitution lists the five-item rule, the full deployment pipeline, inline comments, action logging, and one release-note fragment for each change (rows RC-40 to RC-44).
- The repository instructions hold the local gates table (row RC-45). `AGENTS.md` holds the writing style and the issue-first git flow (rows RC-46 and RC-47).
- `container-build.yml` lists the paths that trigger the image build. `.github/dependabot.yml` is not one of them (row RC-25). The merge of this change starts no image build.

## Decisions

Each decision names its alternatives, the chosen option, the reason, and the risk. No decision requires a human.

### D-1. Keep mando at 0.7.1 in `uv.lock` and `requirements-dev.txt`

- **Alternatives**: (a) Keep mando 0.7.1. (b) Upgrade radon to a release that accepts mando 0.8. (c) Replace radon with another complexity tool.
- **Chosen**: (a).
- **Reason**: Radon 6.0.1 is the latest radon release (row RC-49). Option (b) has no release to use. Option (c) changes the complexity gate, the radon job in `ci.yml`, and the gate tables. It needs its own specification. Main already holds the compatible pin and passes the job (row RC-06).
- **Risk**: A future radon release can require a newer mando. The contract in `design/contracts/dependabot-policy.md` names the exit condition.

### D-2. Ignore mando minor and major updates in the Dependabot pip update block

- **Alternatives**: (a) Ignore by `update-types` for minor and major updates. (b) Ignore by a `versions` range. (c) Close each mando pull request by hand. (d) Disable pip updates.
- **Chosen**: (a).
- **Reason**: The ignore stops the recurrence at the source. The `update-types` values already appear in this repository (row RC-19 names `version-update:semver-major`) and in the commit message of pull request #4888 (row RC-02 names `version-update:semver-minor`). The `versions` syntax could not be verified, because the GitHub documentation domain was blocked (item U-1). Manual closure repeats on each Dependabot run. Disabling pip updates removes every Python dependency update.
- **Risk**: A security update can still propose mando 0.8 (item U-2). The `dependency_lock` job blocks such a pull request.

### D-3. Update the policy snapshot and add two mutation rows

- **Alternatives**: (a) Update the snapshot and add two mutation rows. (b) Leave the snapshot unchanged. (c) Weaken the guard so it skips the pip block.
- **Chosen**: (a).
- **Reason**: The guard pins the complete policy by design (row RC-20 and row RC-21). Option (b) leaves the guard failing on the new policy. Option (c) removes the protection. The two new rows prove that the guard fails for a removed ignore and for a weakened update type.
- **Risk**: A reviewer must read the snapshot diff. The two new rows protect against a silent weakening.

### D-4. Document the `dependency_lock` job and the mando pin in `quality-gates.md`

- **Alternatives**: (a) Add one table row and one section to `quality-gates.md`. (b) Add the note to `.github/copilot-instructions.md`. (c) Make no documentation change.
- **Chosen**: (a).
- **Reason**: `quality-gates.md` holds the CI gate table, and it omits the job (row RC-23). `copilot-instructions.md` holds the local gates table for MistHelper rules. `AGENTS.md` requires documentation in the same change that alters behavior.
- **Risk**: The section must pass the writing gate. `ste-linter` checks it before the commit.

### D-5. Close pull request #4888 after the fix merges

- **Alternatives**: (a) Close it after the merge, with a comment. (b) Recreate it with the same pin. (c) Leave it open.
- **Chosen**: (a).
- **Reason**: Option (b) repeats the failing pin. Option (c) keeps a failing pull request linked to fourteen sibling issues (row RC-51).
- **Risk**: Closure is reversible. Item U-3 records that the closure behavior of Dependabot is unverified.

### D-6. Use the slug `mando-radon-pin` for the branch, record, and fragment

- **Alternatives**: (a) `mando-radon-pin`. (b) `dependency-lock-mando-pin`.
- **Chosen**: (a).
- **Reason**: The slug is short and names the two packages. The same slug names the branch `fix/4903-mando-radon-pin`, the record folder `4903-mando-radon-pin`, and the fragment `issue-4903-mando-radon-pin.md`.
- **Risk**: None identified.

## Remote Verification

Each row is one check. The row count matches `remote_checks` in `META_DIR\4903-STATUS.json` and the count in the summary. Line `0` means the check cites no file line. Blob or object values come from the GitHub tree, the blob endpoint, or the commit endpoint.

| # | Claim | Path | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Issue cites commit 5bb4b385, the test merge commit | commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | commit | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | present | 0 |
| RC-02 | Pull request 4888 head is commit e86098cd | commits/e86098cdc2b189d217805b3b4060ef609cbc37af | commit | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| RC-03 | Main head is commit f03c6c9b | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-04 | Run 45064243269, job 137336719111, failed at the pip install step | actions/runs/45064243269/jobs/137336719111 | e86098cdc2b189d217805b3b4060ef609cbc37af | none (job record) | present | 0 |
| RC-05 | Seven sampled failed jobs show the same resolver error | actions/runs/45064243269/jobs/137336719229, 137336719159, 137336718674, 137336719006, 137338084785, 137339161296, 137338442288 | e86098cdc2b189d217805b3b4060ef609cbc37af | none (job records) | present | 0 |
| RC-06 | Run 45774119357, job 139753527647, passed the same job on main | actions/jobs/139753527647 | main | none (job record) | present | 0 |
| RC-07 | Pull request 4888 changes only requirements-dev.txt | pulls/4888/files | e86098cdc2b189d217805b3b4060ef609cbc37af | none (pull request record) | present | 0 |
| RC-08 | requirements-dev.txt pins mando 0.7.1 on main | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-09 | requirements-dev.txt pins radon 6.0.1 on main | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-10 | ci.yml defines the dependency_lock job | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 634 |
| RC-11 | The dependency_lock job installs requirements-dev.txt first | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 646 |
| RC-12 | The dependency_lock job runs uv lock --check before the export guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-13 | uv.lock locks mando 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-14 | uv.lock lists mando as a dependency of radon 6.0.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RC-15 | pyproject.toml declares radon 6.0.1 in the dev extra | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| RC-16 | pyproject.toml declares mando directly | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 0 |
| RC-17 | requirements.txt pins mando for the runtime | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| RC-18 | The Dependabot pip update block has an ignore for mando | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-19 | The Dependabot npm update block ignores typescript major updates | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 80 |
| RC-20 | The policy snapshot holds the Dependabot policy | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 20 |
| RC-21 | The policy guard asserts that the policy equals the snapshot | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RC-22 | The policy guard rejects each listed mutation of the policy | tests/guardrails/test_pr_title_workflow.py | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 321 |
| RC-23 | quality-gates.md documents the dependency_lock job | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | absent | 0 |
| RC-24 | quality-gates.md holds the pip_audit row, where the new row goes | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 57 |
| RC-25 | The container build path filter lists dependabot.yml | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | absent | 6 |
| RC-26 | The dependency lock guard checks each requirement against uv.lock | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| RC-27 | The export guard compares checked-in exports with uv export output | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RC-28 | The workflow guard requires the dependency_lock job to block | tests/guardrails/test_dependency_lock_workflow.py | main | e529b5c8dc2ce363c670a42595070135fac230c4 | present | 74 |
| RC-29 | The complexity guard reads the limit sentence of quality-gates.md | tests/guardrails/test_complexity_gate_limit.py | main | 7e15fc70d292e52c134841f3c17aa3e7135a3749 | present | 34 |
| RC-30 | The changelog guard defines the issue fragment name form | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-31 | The changelog README defines the issue name form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-32 | No changelog fragment for issue 4903 exists on main | changelog.d/issue-4903-* | main | none (absent on main) | absent | 0 |
| RC-33 | spec-route.ps1 builds numbered routes in base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-34 | spec-route.ps1 places numbered records under specs/numbered | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| RC-35 | The route folder for issue 4903 exists on main | specs/numbered/0/0/1/2/4/1/0/3/ | main | none (absent on main) | absent | 0 |
| RC-36 | A legacy record folder for issue 4903 exists under specs | specs/**/4903-* | main | none (absent on main) | absent | 0 |
| RC-37 | The reference record 4920 spec.md exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-38 | The route contract test reads spec-route.ps1 | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 15 |
| RC-39 | The process folder guard reads the baseline file | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 15 |
| RC-40 | Constitution Principle I states the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-41 | Constitution Principle IV states the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-42 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-43 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-44 | The constitution requires one release-note fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-45 | The copilot instructions hold the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-46 | AGENTS.md requires Simplified Technical English | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-47 | AGENTS.md defines the issue-first git flow | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 179 |
| RC-48 | Local radon 6.0.1 metadata requires mando below 0.8 | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local | sha256:ED647B7F367C60A2D7FD08A8FF3CAA95A0A6B893BACC164D574633636479E890 | present | 31 |
| RC-49 | PyPI lists radon 6.0.1 as latest and requires mando below 0.8 | https://pypi.org/pypi/radon/json | upstream | none (upstream JSON response) | present | 0 |
| RC-50 | PyPI publishes mando 0.8.2 | https://pypi.org/pypi/mando/0.8.2/json | upstream | none (upstream JSON response) | present | 0 |
| RC-51 | Fourteen sibling issues cite pull request 4888 | issues?search=4888 | github | none (issue records) | present | 0 |
| RC-52 | development-setup.md gives the requirements-dev.txt install commands and names no mando or radon pin | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |

## Sources

- **Repository files**: The remote table gives the blob SHA of each file below.
  - `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`.
  - The four templates in `.specify/templates/`.
  - `documentation/quality-gates.md`, `.github/workflows/ci.yml`, and `.github/dependabot.yml`.
  - `.github/workflows/container-build.yml`, `requirements-dev.txt`, `requirements.txt`, `pyproject.toml`, and `uv.lock`.
  - `.specify/scripts/powershell/spec-route.ps1` and `changelog.d/README.md`.
  - The guard tests named in the remote table.
- **Local third-party metadata**: `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA`, read in place. The repository tree does not hold it.
- **GitHub reads (GET only)**:
  - `gh issue view 4903`, and `gh issue list` for the label `quality-gate` and the search `4888`.
  - `gh pr list`, and `gh pr view 4888`.
  - `gh run view 45064243269` with `--json`, and with `--job 137336719111 --log-failed`.
  - `gh run view` with `--job` for the seven sampled job IDs.
  - `gh run list` for `Quality Gates` on `main`, and `gh run view 45774119357`.
  - `gh api` for commits, the `main` tree, and blobs.
- **Upstream URLs fetched**: `https://pypi.org/pypi/radon/json` and `https://pypi.org/pypi/mando/0.8.2/json`.

## Unverified

- **U-1**: Dependabot applies the `update-types` ignore to `mando` after this change. Reason: the GitHub documentation page `https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file` was blocked by the web tool. The SchemaStore copy `https://json.schemastore.org/dependabot-2.0.json` was fetched, but its response was truncated before the `ignore` section. The `update-types` values appear in this repository and in pull request #4888 metadata.
- **U-2**: Dependabot security updates honor the ignore entry. Reason: the same documentation block applies.
- **U-3**: Dependabot closes pull request #4888 after the ignore merges. Reason: this behavior is not observed.
- **U-4**: The skipped steps 5 and 6 of run 45064243269 would pass or fail on the pull request head. Reason: the log reads them as unknown. The prediction uses rows RC-13, RC-08, and RC-27.
- **U-5**: Sibling issues 4891 to 4905 close after pull request #4888 closes. Reason: the reusable issue workflow lives in `misthelper-devtools`, outside this tree, and it was not fetched.
- **U-6**: pip resolves `requirements-dev.txt` with the same result on the local Python 3.15 interpreter. Reason: this stage forbids package installs. The evidence comes from the CI log (row RC-04) and the local metadata (row RC-48).
- **U-7**: The two checks of other workflows in run 45064243269, "Native Windows timeout budget" and "Native Windows audit report", show the same resolver error. Reason: these two checks were not sampled.
