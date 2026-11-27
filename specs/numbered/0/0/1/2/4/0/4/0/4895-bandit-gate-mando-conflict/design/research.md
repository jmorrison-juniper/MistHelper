# Research: Bandit Gate Dependency Conflict

Each finding cites its source. Each decision lists the choice, the reason, and the rejected alternatives. Facts come from GitHub reads, the repository tree of `main`, the CI log, and PyPI.

## Findings

### F-1. Failing check and step

- **Fact**: Job `Bandit (security)` (job 137336719159, workflow `Quality Gates`, run 45064243269) failed at step 5, `Run pip install -r requirements-dev.txt`. Steps 6 and 7 show `skipped`. No Bandit rule ran.
- **Source**: The job step list of run 45064243269, and the failed-step log of job 137336719159.
- **Classification**: A pip dependency conflict, not a Bandit finding. `AGENTS.md` lines 306 to 309 require reading `skipped` as unknown.

### F-2. Root cause

- **Fact**: PR #4888 changes `requirements-dev.txt` line 179 from `mando==0.7.1` to `mando==0.8.2`. Line 365 pins `radon==6.0.1`. Radon 6.0.1 requires `mando (<0.8,>=0.6)`.
- **Log evidence**: The failed-step log reads `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` It also reads `radon 6.0.1 depends on mando<0.8 and >=0.6` and `ERROR: ResolutionImpossible`.
- **Upstream evidence**: The PyPI JSON for radon 6.0.1 lists `mando (<0.8,>=0.6)` in `requires_dist` (RV-28). The installed METADATA file lists the same requirement at line 31 (RV-31).

### F-3. Scope of the failure

- **Fact**: 28 jobs in run 45064243269 failed. 26 jobs log `ResolutionImpossible` with the `mando==0.8.2` conflict. Two jobs are aggregators with no pip log. They are `pytest (coverage gate)`, which fails at `Verify dependency lock job`, and `E2E smoke tests`, which fails at `Verify E2E shards`.
- **Method**: Each failed job log was read with `gh run view 45064243269 --job` and its database ID, using `--log-failed`. Counts came from exact pattern matches.
- **Ops platform**: Job `Ruff (ops platform)` installs `../requirements-dev.txt` at `.github/workflows/ci.yml` line 1232. Its log reads `ERROR: Cannot install -r ../requirements-dev.txt (line 365)`, which is the same conflict.

### F-4. Commit cited by the issue

- **Fact**: Commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` is a merge commit. Its message reads `Merge e86098cdc2b189d217805b3b4060ef609cbc37af into 00d9a16e998b0cb5e10b6ed77da0fa909670d64f` (RV-24).
- **Consequence**: The failing head is `e86098cdc2b189d217805b3b4060ef609cbc37af`, the `headSha` of run 45064243269 (RV-25).

### F-5. Health of `main`

- **Fact**: The `main` head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Run 45774119357, workflow `Quality Gates`, concluded `success` on that head (RV-26). Its job `Bandit (security)` shows steps 5, 6, and 7 as `success`.

### F-6. Route

- **Fact**: `Get-SpecRadixSegments` uses base 5 and width 8 (`.specify/scripts/powershell/spec-route.ps1` lines 4 to 17, RV-21). The number 4895 has the base-5 value 124040. Eight digits give `0 0 1 2 4 0 4 0`.
- **Method**: The script was read, not run. The digit arithmetic was checked by hand.

### F-7. Skills and Mist API

- **Fact**: No local skill was loaded. The brief limits skills to Podman and Juniper questions, and this issue raises neither.
- **Fact**: The Mist API documents and the mistapi source do not apply, because the change makes no Mist call.

## Decisions

### D-1. Keep `mando` at 0.7.1

- **Decision**: Keep `mando` at 0.7.1 in `requirements-dev.txt` and `uv.lock`. `main` already holds this pin (RV-07, RV-11).
- **Rationale**: Version 0.7.1 is the only `mando` release that radon 6.0.1 accepts in the locked set. `main` passes the Bandit job (F-5).
- **Alternatives considered**:
  - Upgrade radon. Rejected: PyPI shows radon 6.0.1 as the latest release (RV-29).
  - Remove the radon gate. Rejected: `AGENTS.md` line 308 forbids removing a gate.
  - Force `mando` 0.8.2 with a resolver override. Rejected: the override installs packages that radon declares invalid.

### D-2. Close PR #4888 after the fix merges

- **Decision**: Close PR #4888 after the fix merges. The closing comment names the merged fix commit and the surviving branch.
- **Rationale**: PR #4888 cannot pass while radon 6.0.1 stays pinned. Closing after the fix keeps the ignore rule active when Dependabot runs again. The branch stays on the remote, so the preservation proof holds. The `AGENTS.md` section "Preserve work before you close an unmerged pull request" requires that proof.
- **Alternatives considered**:
  - Keep it open. Rejected: it stays red and keeps the gate issues open.
  - Run `@dependabot ignore this minor version`. Rejected: the rule would live in Dependabot state, outside the reviewed repository.
  - Run `@dependabot recreate`. Rejected: it recreates the same conflicting pin.

### D-3. Add a Dependabot ignore for `mando` major and minor updates

- **Decision**: Add an `ignore` block to the pip stream. It lists `version-update:semver-major` and `version-update:semver-minor` for `mando`.
- **Rationale**: Dependabot runs the pip stream weekly (`.github/dependabot.yml` lines 3 to 7), so it can propose the same pin again. The npm stream already uses an `ignore` block with a stated reason (lines 45 to 81). Both update types cover a 0.x release, whichever type Dependabot assigns (U-1).
- **Alternatives considered**:
  - No rule. Rejected: the same bump returns.
  - Ignore every `mando` update. Rejected: it also blocks patch releases that radon accepts.
  - Ignore `version-update:semver-minor` only. Rejected: a 0.x release can carry the major type (U-1).

### D-4. Put guard cases in existing test files

- **Decision**: Add the regression cases to `tests/guardrails/test_dependency_declaration_parity.py`. Update the snapshot in `tests/guardrails/test_pr_title_workflow.py`. Add no new file.
- **Rationale**: `tests/guardrails` holds 77 files, which is grandfathered debt. The constitution forbids a new direct child under a noncompliant parent (constitution lines 42 and 43). The parity file already imports `Requirement` and `SpecifierSet` (RV-19).
- **Alternatives considered**:
  - A new file under `tests/guardrails`. Rejected: it adds a direct child to a noncompliant parent.
  - A new test folder. Rejected: it adds a hierarchy level with no need.
  - No test. Rejected: `AGENTS.md` line 135 requires a test for each change.

### D-5. Update the complete-policy snapshot

- **Decision**: Add the same `ignore` entry to the pip stream of `POLICY_SNAPSHOTS["dependabot"]`.
- **Rationale**: `assert_policy` compares the complete policy at line 295 (RV-18). Without this update, the snapshot test fails after the YAML change.
- **Alternatives considered**: Relax the comparison to skip `ignore`. Rejected: it hides future policy drift.

### D-6. Record the container build as not started

- **Decision**: Record that `container-build.yml` does not start for this change.
- **Rationale**: Its push paths (lines 6 to 19) include `requirements.txt`, `pyproject.toml`, and `uv.lock`, but not `requirements-dev.txt` or `.github/dependabot.yml` (RV-16). The `Containerfile` installs only `requirements.txt` (RV-17). No image input changes.
- **Alternatives considered**:
  - Run `gh workflow run container-build.yml`. Rejected: the run builds an image without a product change.
  - Wait for the run. Rejected: the paths filter excludes the run, so the wait cannot end.

### D-7. Add no changelog fragment

- **Decision**: Add no fragment under `changelog.d/`.
- **Rationale**: `.github/copilot-instructions.md` line 451 requires a fragment only for a change that a user sees. This change alters CI policy and tests only.
- **Alternatives considered**: Add `issue-4895-bandit-gate-mando-conflict.md`. Rejected: no user sees the change.

### D-8. Set the labels

- **Decision**: Add `in-progress`. Keep `bug`, `ci`, and `quality-gate`.
- **Rationale**: The status label applies while work is in progress (`.specify/memory/constitution.md` line 487). `bug` and `ci` already give the type and the scope.
- **Alternatives considered**: Use `chore`. Rejected: the issue reports a defect.

### D-9. Leave the gate issues to the bot

- **Decision**: Do not close the 15 gate issues by hand. The bot closes each one after PR #4888 closes and a `main` run completes.
- **Rationale**: `documentation/quality-gates.md` lines 160 to 165 define the closure rule. A manual close hides the state that the bot tracks.
- **Alternatives considered**: Close them by hand after PR #4888 closes. Rejected: it duplicates the bot logic.

## Remote Verification

The `main` tree was read with one `gh api` call on `git/trees/main?recursive=1`. Blob SHAs come from that tree. File lines come from decoding each file body read with `gh api` on the contents endpoint, with `ref=main` or with the PR head SHA. Result values are present, absent, partial, or stale. Each result states what the cited item shows.

| No. | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RV-01 | Job `Bandit (security)` is defined | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 414 |
| RV-02 | Bandit job runs `pip install -r requirements-dev.txt` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 435 |
| RV-03 | Bandit job runs `bandit -c pyproject.toml -r .` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| RV-04 | Job `quality_gate_issues` lists `bandit` in `needs` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1300 |
| RV-05 | Job `dependency_lock` runs `uv lock --check` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RV-06 | Job `ops_platform_ruff` installs `../requirements-dev.txt` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1232 |
| RV-07 | `main` pins `mando==0.7.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RV-08 | `main` pins `radon==6.0.1` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RV-09 | PR #4888 head pins `mando==0.8.2` | `requirements-dev.txt` | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RV-10 | PR #4888 changes only `requirements-dev.txt` | `requirements-dev.txt` (PR file list) | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RV-11 | `uv.lock` pins `mando` 0.7.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RV-12 | `uv.lock` records that radon 6.0.1 depends on `mando` | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| RV-13 | Bandit excludes `tests` | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| RV-14 | Dependabot pip stream has no `ignore` key | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RV-15 | Dependabot npm stream shows the `ignore` syntax | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| RV-16 | Container build push paths omit `requirements-dev.txt` | `.github/workflows/container-build.yml` | main | 737325976de75e90aa4526ab1cf2978782e648ce | absent | 6 |
| RV-17 | `Containerfile` installs `requirements.txt` only | `Containerfile` | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 120 |
| RV-18 | Policy snapshot compares the complete Dependabot policy | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RV-19 | Parity guard imports `Requirement` and `SpecifierSet` | `tests/guardrails/test_dependency_declaration_parity.py` | main | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 13 |
| RV-20 | Export guard compares exports with the lock | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RV-21 | Route width is 8 and base is 5 | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RV-22 | Record folder for issue 4895 is absent | `specs/numbered/0/0/1/2/4/0/4/0` | main | none (no tree entry) | absent | 0 |
| RV-23 | Reference record 4920 exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RV-24 | Issue cites a test-merge commit | commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | present | 0 |
| RV-25 | Failed job 137336719159 failed at step 5 | `.github/workflows/ci.yml` (run 45064243269, job 137336719159) | e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 435 |
| RV-26 | `main` Bandit job succeeds in run 45774119357 | run 45774119357, job 139753527450 | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RV-27 | Fifteen gate issues name PR #4888 | issues 4891 to 4905 | not applicable | not applicable | present | 0 |
| RV-28 | Upstream radon 6.0.1 requires `mando (<0.8,>=0.6)` | https://pypi.org/pypi/radon/6.0.1/json | 6.0.1 | not applicable | present | 0 |
| RV-29 | Upstream radon latest release is 6.0.1 | https://pypi.org/project/radon/ | latest | not applicable | present | 0 |
| RV-30 | Upstream `mando` 0.8.2 release exists | https://pypi.org/pypi/mando/0.8.2/json | 0.8.2 | not applicable | present | 0 |
| RV-31 | Installed radon metadata requires `mando (<0.8,>=0.6)` | `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` (local third-party file) | local | not applicable | present | 31 |
| RV-32 | No open PR touches the target files | open PR file lists (PRs 4208, 4813, 4886 to 4890) | main | not applicable | absent | 0 |

The table holds 32 rows. `STATUS.json` and `summary.md` use the same count.

## Sources

Local files read:

- `AGENTS.md`, in full.
- `.github/copilot-instructions.md`, in full.
- `.specify/memory/constitution.md`, in full.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, in full.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. The headings, the checklist, and the start of the research and tasks files were read for shape. No content was copied.
- `documentation/quality-gates.md`, in full. `documentation/development-setup.md`, in full. The setup page needs no change.
- `documentation/architecture.md`, by term search. Line 167 names `requirements-dev.txt` for development tools and is not affected.
- `documentation/container-deployment.md` and `documentation/operator-guide.md`, by term search. Neither file names Bandit, `requirements-dev`, `mando`, or `radon`. Both are not applicable.
- `.specify/scripts/powershell/spec-route.ps1`, read only. The script was not run.
- `tests\guardrails`, listed. It holds 77 files and 3 folders.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA`, line 31. This is installed third-party metadata.

URLs fetched:

- `https://pypi.org/pypi/radon/6.0.1/json`. The field `info.requires_dist` lists `mando (<0.8,>=0.6)`.
- `https://pypi.org/project/radon/`. The page header reads `radon 6.0.1`.
- `https://pypi.org/pypi/mando/0.8.2/json`. The version endpoint returns the release.

Not applicable: Mist API documents and the mistapi source, because the change makes no Mist call.

## Unverified

- U-1: Dependabot's classification of a 0.x release as minor or major. The rule covers both types, so the classification does not change the result. Dependabot documentation was not read.
- U-2: The Bandit result on the fix head. The head does not exist yet. T-REMOTE-CI checks it.
- U-3: The content of `reusable-quality-gate-issues.yml` in `misthelper-devtools`. The workflow was not read. The record relies on `documentation/quality-gates.md` lines 160 to 165.
- U-4: The bot closure of the 15 gate issues. The closure cannot occur before PR #4888 closes. T-MERGE checks it.

## Process Notes

- P-1: One `gh api` call used `-f ref=main`, which sends a POST request. GitHub returned HTTP 404, and no change occurred. Later calls used GET query strings only.
- P-2: Two decode calls failed because of PowerShell variable interpolation. Both returned HTTP 404 on GET requests, and no change occurred. The fix used braces around the variable names.
