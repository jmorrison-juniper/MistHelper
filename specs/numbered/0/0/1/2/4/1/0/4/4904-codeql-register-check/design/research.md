# Research: CodeQL register check fails on pull request 4888

Each decision names the chosen option, the reason, and the rejected options. Each claim cites a row of the remote verification table. Row IDs `RC-##` match the status file.

## Decisions

### R1. Keep the mando pin at 0.7.1 and close pull request #4888 unmerged

- **Decision**: Keep `mando==0.7.1` in `requirements-dev.txt` and in `uv.lock`. Close pull request #4888 unmerged after this change merges (D-1).
- **Rationale**: Radon 6.0.1 requires `mando` below 0.8 (RC-30, RC-31). Resolution cannot succeed while radon 6.0.1 stays pinned (RC-07). The lock pins `mando` 0.7.1 (RC-09). The PyPI read shows radon 6.0.1 as the current release (RC-31).
- **Alternatives considered**:
  - Merge the bump and regenerate the lock. Rejected: the lock cannot select `mando` 0.8 while radon 6.0.1 is pinned.
  - Replace radon. Rejected: this change would also replace the complexity gate, which is out of scope.
  - Keep pull request #4888 open until radon releases. Rejected: the check stays red and blocks that pull request.
- **Risk**: A future radon release can accept the bump. The owner then updates the pin and the lock in one change.

### R2. Add a Dependabot ignore entry for minor and major mando updates

- **Decision**: Add an `ignore` entry to the pip stream of `.github/dependabot.yml`. The entry lists the update types `version-update:semver-minor` and `version-update:semver-major` for `mando` (D-2).
- **Rationale**: The key form matches the npm entry that already exists (RC-17). Dependabot labels the rejected bump as `version-update:semver-minor` in its commit message (RC-18). Patch updates stay allowed.
- **Alternatives considered**:
  - Close pull request #4888 only. Rejected: no repository rule then stops a later proposal.
  - Post the Dependabot command `@dependabot ignore this minor version` on the pull request. Rejected: the rule lives in the Dependabot service and not in a reviewed file. This agent also cannot post comments.
  - Add a constraint to `pyproject.toml`. Rejected for now: whether Dependabot honors such a constraint is unverified (U-1).
- **Risk**: The entry also blocks a valid `mando` upgrade until the owner removes it.

### R3. Add a radon ceiling guard to the existing lock guard module

- **Decision**: Add class `RadonRequirementCheck` and two tests to `tests/guardrails/test_dependency_lock_file.py` (D-3).
- **Rationale**: The CI failure appears only after the install of the full development set. The local guard fails in seconds. The installed metadata holds the radon requirement text (RC-30). The lock gives the radon version (RC-10). The existing module already holds the lock guard (RC-13), so the change adds no child to `tests/guardrails/`.
- **Alternatives considered**:
  - Rely on the CI install step. Rejected: the failure appears late and only in CI.
  - Create a new module under `tests/guardrails/`. Rejected: the directory already exceeds five children, and the rule forbids a new direct child.
  - Parse `requirements-dev.txt` only. Rejected: that file lists pins and comments, not the radon ceiling.
- **Risk**: The guard fails when radon is absent. This result is intended, because the guard fails closed.

### R4. Keep the gate job, its install command, and its check command unchanged

- **Decision**: Make no change to `.github/workflows/ci.yml` lines 385-411 (D-4).
- **Rationale**: The gate guard requires the exact command pair (RC-11, lines 50-51), and it forbids `continue-on-error`. The job comment states that the install step supplies the pinned register tool (RC-02, lines 401-403).
- **Alternatives considered**:
  - Install the register tool alone. Rejected: this changes a guarded command and the pinned source.
  - Set `continue-on-error: true` on the job. Rejected: the guard forbids it, and a failed check would stop reporting.
- **Risk**: None for the gate definition.

### R5. Keep radon pinned at 6.0.1

- **Decision**: Make no change to the radon pin (D-5).
- **Rationale**: Version 6.0.1 is the current release (RC-31). The radon pin is in `requirements-dev.txt` (RC-07).
- **Alternatives considered**:
  - Pin an older radon release. Not evaluated: this change keeps the current release and avoids a tool change.

### R6. Document the cause and add one release-note fragment

- **Decision**: Add one note below the job table of `documentation/quality-gates.md` (RC-24). Add the fragment `changelog.d/issue-4904-codeql-register-check.md` (RC-23). These are decision D-6.
- **Rationale**: The constitution requires one fragment for each user-visible change. The file name follows the rule for an issue without a pull request (RC-23). The note helps the next maintainer diagnose the same install failure.
- **Alternatives considered**:
  - Add no note. Rejected: the next maintainer repeats the diagnosis.
  - Add a row to the local gates table in `.github/copilot-instructions.md`. Rejected for this change: that table guides every local gate (RC-28), and widening it needs its own review.

## Remote Verification Table

Each row is one remote or external check. Result values are present, absent, partial, or stale. Line values are one-based.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | Job codeql_register_check is defined | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 385 |
| RC-02 | Job installs requirements-dev.txt before its check | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 403 |
| RC-03 | Job runs codeql-verdict-register check | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 411 |
| RC-04 | quality_gate_issues needs codeql_register_check | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1309 |
| RC-05 | Job dependency_lock runs uv lock --check | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-06 | requirements-dev.txt pins mando 0.7.1 | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-07 | requirements-dev.txt pins radon 6.0.1 | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| RC-08 | requirements-dev.txt lists radon as the source of mando | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 180 |
| RC-09 | uv.lock pins mando 0.7.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| RC-10 | uv.lock pins radon 6.0.1 | `uv.lock` | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2428 |
| RC-11 | Gate guard fixes the job commands and forbids continue-on-error | `tests/guardrails/test_codeql_register_gate.py` | main | 5cb34ac78a2ca8237492541d6915d5a5c1738d64 | present | 50 |
| RC-12 | Export guard requires parity with uv.lock | `tests/guardrails/test_dependency_export.py` | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RC-13 | Lock guard requires each requirement to match the locked version | `tests/guardrails/test_dependency_lock_file.py` | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| RC-14 | Policy guard compares the complete Dependabot policy with a snapshot | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 295 |
| RC-15 | Policy snapshot records the pip stream | `tests/guardrails/test_pr_title_workflow.py` | main | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 24 |
| RC-16 | Pip stream of dependabot.yml has no mando ignore entry | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-17 | dependabot.yml shows the update-types ignore syntax in the npm stream | `.github/dependabot.yml` | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 81 |
| RC-18 | Pull request 4888 head commit exists and names version-update:semver-minor | `commits/e86098cdc2b189d217805b3b4060ef609cbc37af` | e86098cdc2b189d217805b3b4060ef609cbc37af | e86098cdc2b189d217805b3b4060ef609cbc37af | present | 0 |
| RC-19 | Issue commit 5bb4b385 exists and merges base 00d9a16e with head e86098cd | `commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | present | 0 |
| RC-20 | Head of main is f03c6c9b | `git/refs/heads/main` | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-21 | Quality Gates run 45774119357 on main succeeded | `actions/runs/45774119357` | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-22 | No record for issue 4904 exists under the route | `specs/numbered/0/0/1/2/4/1/0/4/` | main | none | absent | 0 |
| RC-23 | Changelog rules name a fragment by issue when no pull request exists | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 24 |
| RC-24 | Quality gates document lists codeql_register_check | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 55 |
| RC-25 | Development setup installs requirements-dev.txt | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 137 |
| RC-26 | Windows audit workflow installs requirements-dev.txt | `.github/workflows/windows-audit-report.yml` | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 48 |
| RC-27 | Windows timeout workflow installs requirements-dev.txt | `.github/workflows/windows-timeout-budget.yml` | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 48 |
| RC-28 | Local gates table has no CodeQL register row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | absent | 55 |
| RC-29 | Container build paths exclude every changed path | `.github/workflows/container-build.yml` | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| RC-30 | Installed radon 6.0.1 requires mando below 0.8 | `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` | local .venv outside the repository tree | not applicable | present | 31 |
| RC-31 | PyPI reports radon 6.0.1 as current with mando below 0.8 | `https://pypi.org/pypi/radon/json` | pypi | not applicable | present | 0 |
| RC-32 | Job log and step table show the resolver conflict in the install step | `gh run view 45064243269 --job 137336719141 --log` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | not applicable | present | 587 |
| RC-33 | 26 of 28 failed jobs print the same resolver conflict | `gh run view 45064243269 --log-failed` | 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | not applicable | present | 0 |
| RC-34 | Runs 45064235051 and 45064235097 print the same resolver conflict | `gh run view 45064235051` and `gh run view 45064235097` | not applicable | not applicable | present | 0 |

Remote table rows: 34.

## Sources

- Remote, read only: issue #4904 through `gh issue view`. Run 45064243269 with its jobs and logs. Runs 45064235051 and 45064235097 with their logs.
- Remote, read only: pull request #4888 through `gh pr view` and `gh pr diff`. The open pull request list. The Git tree, commits, refs, and contents at `main`, with blob SHAs in the table.
- Local, read only. Local HEAD `f03c6c9b` equals remote `main`. Files: `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`.
- Local, read only: the four `.specify/templates/` files and `documentation/quality-gates.md`.
- Local, read only: the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`, for shape only.
- Local package metadata: `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` and `mando-0.7.1.dist-info` (RC-30).
- URL fetched on 2026-11-26: `https://pypi.org/pypi/radon/json` (RC-31).
- Skills: none loaded. No Podman, Juniper device, or Mist behavior is in scope.
- Mist API OpenAPI file and mistapi SDK: not applicable. The failing path installs packages and calls GitHub only.
- Linked work: pull request #4888 is open. Its head is `e86098cd`, and it changes one file, `requirements-dev.txt`. A search for issue 4904 found no pull request.
- Existing record: a search of `specs/` for folders named `4904-*` found none. The search was read only.
- Documentation read: `documentation/quality-gates.md` and `documentation/development-setup.md`. Not read in full: `architecture.md`, `container-deployment.md`, and `operator-guide.md`.
- Documentation scan: a grep for the pin names found one description in `architecture.md` line 167 and no match in `container-deployment.md` or `operator-guide.md`.

## Unverified

- U-1: Dependabot applies an `update-types` ignore entry to a transitive pin in `requirements-dev.txt`. Reason: no Dependabot run is available to the agent. Mitigation: check SC-005 after the merge.
- U-2: No newer radon release appears after 2026-11-26. Reason: only one PyPI read was made. Mitigation: the implementer rereads the PyPI JSON before opening the pull request.
- U-3: `uv lock --check` passes on the fix head. Reason: the agent does not run `uv`. Mitigation: the `dependency_lock` job on the fix pull request.
- U-4: `tests/guardrails/test_changelog_fragment_policy.py` accepts the fragment name. Reason: the file was not read. Mitigation: task T005 runs that test.
- U-5: The label, merge, and close actions succeed on GitHub. Reason: write actions are outside the agent role. Mitigation: the orchestrator performs them after authorization.
