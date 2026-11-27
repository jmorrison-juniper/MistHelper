# Research: Mando pin conflict in the pip-audit gate

## Summary

Issue #4896 reports a failed quality gate `pip_audit` on pull request #4888. The job failed at its install step, and the CVE scan never ran. Dependabot changed the pin `mando==0.7.1` to `mando==0.8.2`. The pinned `radon==6.0.1` requires mando below 0.8. The pip resolver stops with `ResolutionImpossible`. Main still pins mando 0.7.1, and its latest run passes the job.

## R1. Failure reproduction from the CI logs

- **Check**: `pip-audit (CVE scan)`, the name of job `pip_audit` (`.github/workflows/ci.yml` line 454, R-09).
- **Workflow and run**: `Quality Gates`, run 45064243269, event `pull_request`, head commit `e86098cdc2b189d217805b3b4060ef609cbc37af` (R-02, R-03, R-12).
- **Failing step**: step 5, `Run pip install -r requirements-dev.txt`, conclusion `failure` (R-03). Step 6, `Run pip-audit`, conclusion `skipped` (R-05).
- **Error text**: `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.` The log adds `radon 6.0.1 depends on mando<0.8 and >=0.6` and `ERROR: ResolutionImpossible` (R-04).
- **Failing rule**: The pip dependency resolution rule. No test ran, because the install step failed before any test command.
- **Line of the conflict**: `requirements-dev.txt` line 179 pins mando (R-16). Line 365 pins radon (R-17).

## R2. Root cause

- radon 6.0.1 declares `mando (<0.8,>=0.6)` on PyPI (R-46) and in the local `.venv` metadata (R-51).
- The pull request changes the mando pin to 0.8.2 (R-16). It changes no other file (R-02).
- The lock file locks mando 0.7.1 (R-20) and lists mando as a dependency of radon (R-21).
- Dependabot labels the change `version-update:semver-minor` (R-08). The minor bump from 0.7.1 to 0.8.2 is outside the radon range.

## R3. Upstream and local evidence for radon and mando

- radon 6.0.1 is the current release on PyPI (R-47). PyPI lists no vulnerability for radon 6.0.1 (R-46). The upload date is 2023-03-26 (R-46).
- mando 0.8.2 exists on PyPI (R-48). mando 0.7.1 lists no vulnerability on PyPI (R-49).
- `requirements.txt` holds no mando, radon, or pip-audit pin (R-18). Pip-audit scans `requirements.txt` only (R-11). Mando is outside the CVE scan.

## R4. Dependabot configuration and documentation

- The pip entry starts at line 3 and holds no ignore key (R-22). The only ignore key sits in the npm entry (R-23).
- The npm entry uses an `update-types` rule for typescript (R-24). The repository already uses this rule shape.
- The GitHub options reference lists `update-types` values for ignore rules: `version-update:semver-patch`, `version-update:semver-minor`, and `version-update:semver-major` (R-50).
- The same reference lists version examples for npm, Bundler, Docker, NuGet, and Maven, and none for pip (R-65). The pip syntax for `versions` is therefore unconfirmed (U-8).

## R5. Guards, the lock, and the export

- `test_dependency_export.py` lists `requirements-dev.txt` with the dev extra (R-25). It runs `uv export --locked` (R-26). Mando 0.8.2 would differ from the exported mando 0.7.1. This result is inferred from the code. The job never reached this test (U-2).
- `test_dependency_lock_file.py` defines `test_lock_satisfies_every_requirement` (R-27). The function `find_defects` compares each requirement with the locked version (R-28). For mando 0.8.2, it reports a defect. This result is inferred from the code.
- `test_dependency_declaration_parity.py` checks only direct requirements, which `is_direct` identifies (R-66). Mando is transitive, so the parity guard does not check its pin.
- `test_ci_gate_triggers.py` maps `pip_audit` to `pip-audit (CVE scan)` (R-29). The check name stays fixed.

## R6. Recurrence and breadth

- Pull request #4673 (Dependabot pyee 16.0.1) failed at the same install step (R-45). The log names `playwright 1.64.1 depends on pyee<15 and >=13`. Issue #4688 records that failure and is closed (R-45).
- Twenty-six of 28 failed jobs of run 45064243269 log the same `ResolutionImpossible` error (R-06). The other two failed jobs do not log that error (U-10).
- Fifteen quality-gate issues, #4891 to #4905, name pull request #4888 (R-44). Issue #4896 is one of them.
- The class of cause is a Dependabot pin that conflicts with a transitive upper bound. A general check is a follow-up issue, outside this record (spec, Non-Goals).

## R7. Process rules and conflicts

- Constitution Principle I forbids a new direct child under a noncompliant parent (constitution, Principle I, R-33 for the file).
- The changelog README rule 4 skips a fragment for an internal-only change (R-32). The constitution requires one fragment for each change (R-33). The constitution states that it supersedes other practice documents. The Governance wording comes from the local checkout (U-11). Decision D-6 applies the constitution.
- Copilot-instructions line 451 requires a fragment for a user-visible change (R-34). This change is internal. The constitution is stricter (R-33), so decision D-6 follows the constitution.
- AGENTS.md sets the rules for a pull request, a safety statement, closing a pull request, and a gate that cannot be removed (R-67). The rule text cited in this record comes from the local checkout. The remote copy has the same size, 18482 bytes (U-11).

## R8. Route, reference record, and folder debt

- The route is the base-5 encoding of issue 4896, padded to eight digits. Base 5 gives `124041`. Padded to eight digits, it gives `00124041`, which maps to `0/0/1/2/4/0/4/1` (R-39, R-54).
- The route leaf `specs/numbered/0/0/1/2/4/0/4/1` is absent on main (R-42). The new record is its only child.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` holds `analysis.md`, `design`, `plan.md`, `spec.md`, and `tasks.md` on main (R-41). This record copies that shape.
- `tests/guardrails` holds 79 tracked entries on main (R-30). The local checkout holds 80, and the extra entry is `__pycache__`, which is absent from the main tree. The main count governs.
- `changelog.d` holds 335 entries on main (R-31). It is an established process folder, so one required record is allowed.
- The Mist API has no part in this change. The OpenAPI and endpoint documents are not read.

## R9. Build and deployment path

- `auto-merge.yml` lists `container-build.yml` among the main workflows that its dispatch job starts (R-52). The `container-build.yml` comment says the auto-merge workflow calls the trigger after every merge into main (R-68).
- `container-build.yml` has a push trigger that filters on product paths. The change touches none of those paths (R-53).
- Copilot-instructions line 473 states the product-file rule (R-55). Line 420 states a push to main triggers the build (R-64). The workflow file decides, because the dispatch runs after each merge (R-52, R-68).
- Constitution steps 10 and 11 therefore run after the merge. Step 12 needs the owner (decision D-8).

## Decisions

Each decision has a human_decision_required value of false. No decision falls in the categories of licensing, production data, credential policy, or product priority.

### D-1. Hold mando at 0.7.1

- **Alternatives**: (a) Accept mando 0.8.2 and wait for radon. Rejected: radon 6.0.1 is the current release, and it requires mando below 0.8 (R-46, R-47). (b) Replace radon with another complexity tool. Rejected for this record: the complexity gate would change, and the change would exceed one subject. (c) Remove the radon gate. Rejected: AGENTS.md forbids removing a gate (R-67).
- **Chosen**: Hold mando at 0.7.1, the value on main (R-13).
- **Reason**: Main, the lock, and the guards already agree on 0.7.1 (R-13, R-20, R-27).
- **Risk**: Mando stays at 0.7.1. D-2 and the review trigger in the documentation limit that risk.

### D-2. Ignore mando minor and major updates

- **Alternatives**: (a) No rule. Rejected: pull requests #4673 and #4888 failed the same way (R-45, R-02). (b) A `versions` range. Rejected: the pip syntax is not confirmed (R-65, U-8). (c) Close each Dependabot pull request by hand. Rejected: a manual step repeats the failure.
- **Chosen**: One rule for `mando` with `update-types` set to `version-update:semver-minor` and `version-update:semver-major` (R-24, R-50).
- **Reason**: The repository already uses this rule shape (R-24). The values are documented (R-50). The 0.8.2 update is a semver-minor update (R-08).
- **Risk**: The rule may also block security updates for mando (U-1). Pip-audit does not scan mando (R-18), and PyPI lists no vulnerability for 0.7.1 (R-49).

### D-3. Put the guard cases in the existing lock guard module

- **Alternatives**: (a) A new module in `tests/guardrails`. Rejected: the folder holds 79 entries, and FR-012 forbids a new direct child there (R-30). (b) A new folder under `tests/unit`. Rejected: the folder adds structure that this small change does not need. (c) No test. Rejected: AGENTS.md requires a test that can fail, and the install gate fails late (R-67).
- **Chosen**: `tests/guardrails/test_dependency_lock_file.py`, which already compares both requirements files with the lock (R-27, R-28).
- **Reason**: The module already reads both requirements files, so the new checks fit.
- **Risk**: The module grows by five functions. Each function stays within the limits of 25 lines and five parameters.

### D-4. Keep the job, its check name, and its commands unchanged

- **Alternatives**: (a) Install `requirements.txt` and the dev tools in two steps. Rejected: the gate semantics change. (b) Add `--ignore-vuln`. Rejected: a suppression hides a finding (AGENTS.md, Security findings, R-67). (c) Remove the install step. Rejected: pip-audit comes from the dev extra (R-62).
- **Chosen**: No change to the job, its name, its install line, or its audit command (R-09, R-10, R-11, R-29).
- **Reason**: FR-007 and FR-008 require these values to stay the same.
- **Risk**: None added. The job still fails when a future pin conflicts. The guard in D-3 reports that conflict earlier.

### D-5. Close pull request #4888 after the replacement merges

- **Alternatives**: (a) Close it now. Rejected: AGENTS.md requires a preservation proof before the closing comment, and the proof needs the merged replacement (R-67). (b) Keep it open. Rejected: its checks fail until someone closes it. (c) Rebase it. Rejected: the pin conflict belongs to the pin itself, so a rebase cannot resolve it.
- **Chosen**: Close it in T-MERGE, with the proof comment (FR-011).
- **Reason**: The proof keeps the record of the work after the close.
- **Risk**: The failing pull request stays open until T-MERGE. The task list names the step.

### D-6. Add the issue-named fragment

- **Alternatives**: (a) No fragment, as the changelog README rule 4 allows for internal-only changes (R-32). Rejected: constitution line 409 requires one fragment for each change (R-33), and the constitution governs. (b) A date-named fragment. Rejected: the naming rule uses the issue name when only the issue exists.
- **Chosen**: `changelog.d/issue-4896-mando-radon-pin-conflict.md` (FR-010).
- **Reason**: The constitution outranks the changelog README for this point.
- **Risk**: A reviewer may consider the fragment unnecessary for an internal change. The bullet states the fixed behavior.

### D-7. Document the hold in one place

- **Alternatives**: (a) Add the hold to the Known pitfalls of copilot-instructions. Rejected: AGENTS.md asks for one location for each fact (R-67), and the gate facts live in `documentation/quality-gates.md` (R-37). (b) No document. Rejected: FR-009 requires it.
- **Chosen**: One paragraph in `documentation/quality-gates.md`, below the job table (R-37).
- **Reason**: The file describes each gate, and the hold concerns one gate.
- **Risk**: A reader of copilot-instructions does not see the hold. The Dependabot comment names issue #4896 and points to the document.

### D-8. Run constitution steps 10 and 11 in T-MERGE, and leave step 12 with the owner

- **Alternatives**: (a) Skip steps 10 to 12, because the change touches no product path. Rejected: the dispatch runs the build after each merge (R-52, R-68). (b) Deploy from the agent. Rejected: deployment changes the running service, and the constitution calls for an approved image (constitution Principle IV, R-33 for the file. The wording comes from the local checkout, U-11).
- **Chosen**: Steps 10 and 11 run in T-MERGE. Step 12 stays with the owner.
- **Reason**: The build runs after each merge, so the agent can verify it. The owner holds the authority to deploy.
- **Risk**: Step 12 waits for the owner. T-MERGE hands over the merge commit and the image name.

## Remote Verification Table

Each row is one check. The `Result` column uses `present`, `absent`, `partial`, or `stale`. The `Line` column gives the line in the file that the check reads. A value of 0 means the check has no line.

| ID | Claim | Path or source | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Issue #4896 names gate pip_audit and pull request #4888. Labels: bug, ci, quality-gate. | issue #4896 | n/a | n/a | present | 0 |
| R-02 | Pull request #4888 is open, its head is dependabot/pip/mando-0.8.2, and it changes only requirements-dev.txt (1 addition, 1 deletion). | pull request #4888 | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | present | 0 |
| R-03 | Job 137338084755 failed at step 5, Run pip install -r requirements-dev.txt. | run 45064243269, job 137338084755 | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | present | 0 |
| R-04 | The job log holds ERROR ResolutionImpossible for mando==0.8.2 and radon 6.0.1. | run 45064243269, job 137338084755 log | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | present | 0 |
| R-05 | Step 6, Run pip-audit, has conclusion skipped in the same job. | run 45064243269, job 137338084755 | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | present | 0 |
| R-06 | 26 of 28 failed jobs of run 45064243269 log ResolutionImpossible. | run 45064243269 logs | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | present | 0 |
| R-07 | Commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71, which the issue cites, exists as a merge of e86098cd into 00d9a16e. | commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | n/a | n/a | present | 0 |
| R-08 | Commit e86098cdc2b189d217805b3b4060ef609cbc37af exists, and its message names update-type version-update:semver-minor. | commit e86098cdc2b189d217805b3b4060ef609cbc37af | n/a | n/a | present | 0 |
| R-09 | ci.yml names job pip_audit as pip-audit (CVE scan). | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 454 |
| R-10 | ci.yml job pip_audit installs requirements-dev.txt. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 483 |
| R-11 | ci.yml job pip_audit runs pip-audit -r requirements.txt. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 498 |
| R-12 | ci.yml names the workflow Quality Gates. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| R-13 | requirements-dev.txt pins mando==0.7.1 on main. | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| R-14 | requirements-dev.txt pins pyyaml==6.0.4 on main. | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| R-15 | requirements-dev.txt pins radon==6.0.1 on main. | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| R-16 | requirements-dev.txt on the pull request head pins mando==0.8.2. | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| R-17 | requirements-dev.txt on the pull request head pins radon==6.0.1. | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| R-18 | requirements.txt holds a mando pin on main. | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| R-19 | pyproject.toml dev extra pins radon==6.0.1. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| R-20 | uv.lock locks mando 0.7.1. | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| R-21 | uv.lock lists mando as a dependency of radon 6.0.1. | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| R-22 | The pip entry of .github/dependabot.yml starts at line 3 and holds no ignore key. | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 3 |
| R-23 | The only ignore key in .github/dependabot.yml sits in the npm entry. | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| R-24 | .github/dependabot.yml uses an update-types ignore rule for typescript. | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 81 |
| R-25 | The export guard lists requirements-dev.txt with the dev extra. | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 14 |
| R-26 | The export guard runs uv export with the --locked option. | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 55 |
| R-27 | The lock guard defines test_lock_satisfies_every_requirement. | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| R-28 | The lock guard class DependencyLock defines find_defects. | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 43 |
| R-29 | The gate-trigger guard maps pip_audit to pip-audit (CVE scan). | tests/guardrails/test_ci_gate_triggers.py | main | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 189 |
| R-30 | tests/guardrails holds 79 tracked entries on main. | tests/guardrails | main | n/a | present | 0 |
| R-31 | changelog.d holds 335 entries on main. | changelog.d | main | n/a | present | 0 |
| R-32 | The changelog README rule 4 skips a fragment for an internal-only change. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-33 | The constitution requires one unique fragment for each change. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-34 | Copilot-instructions requires a fragment for each user-visible change. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-35 | The copilot-instructions Local gates table holds the Tests row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-36 | The copilot-instructions Local gates table holds the STE row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-37 | documentation/quality-gates.md holds the pip_audit row. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 57 |
| R-38 | quality-gates.md states that a gate that passes on main again closes its issue. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 159 |
| R-39 | spec-route.ps1 sets base 5 for the numbered route. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-40 | spec-route.ps1 refuses a destination that already holds five children. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 92 |
| R-41 | The reference record 4920 holds analysis.md, design, plan.md, spec.md, and tasks.md. | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | n/a | present | 0 |
| R-42 | The route leaf specs/numbered/0/0/1/2/4/0/4/1 is absent on main. | specs/numbered/0/0/1/2/4/0/4/1 | main | n/a | absent | 0 |
| R-43 | Latest main run 45774119357 reports success for pip-audit (CVE scan). | run 45774119357 | main | n/a | present | 0 |
| R-44 | Fifteen quality-gate issues, #4891 to #4905, name pull request #4888. | issues #4891 to #4905 | n/a | n/a | present | 0 |
| R-45 | Pull request #4673 failed at the same install step (job 128848108669, run 42518136545), and playwright 1.64.1 requires pyee below 15. Issue #4688 for that failure is closed. | run 42518136545, job 128848108669 | n/a | n/a | present | 0 |
| R-46 | Upstream: radon 6.0.1 declares requires_dist mando (<0.8,>=0.6), with no vulnerability listed and upload time 2023-03-26. | https://pypi.org/pypi/radon/6.0.1/json | n/a | n/a | present | 0 |
| R-47 | Upstream: the radon project page on PyPI shows radon 6.0.1 as the current release. | https://pypi.org/project/radon/ | n/a | n/a | present | 0 |
| R-48 | Upstream: PyPI returns version metadata for mando 0.8.2. | https://pypi.org/pypi/mando/0.8.2/json | n/a | n/a | present | 0 |
| R-49 | Upstream: PyPI lists no vulnerability for mando 0.7.1. | https://pypi.org/pypi/mando/0.7.1/json | n/a | n/a | present | 0 |
| R-50 | Upstream: the Dependabot ignore update-types option accepts semver-patch, semver-minor, and semver-major. | https://api.github.com/repos/github/docs/contents/content/code-security/reference/supply-chain-security/dependabot-options-reference.md | github/docs main | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 407 |
| R-51 | Local: the .venv radon-6.0.1 METADATA declares Requires-Dist mando (<0.8,>=0.6). | .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA | local | n/a | present | 31 |
| R-52 | auto-merge.yml line 65 lists container-build.yml among the main workflows that its dispatch job starts. | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 65 |
| R-53 | The container-build.yml push trigger filters on product paths. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| R-54 | spec-route.ps1 sets the default route width to 8. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R-55 | Copilot-instructions table row states that container-build runs on a push that changes a product file, or on a manual dispatch. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| R-56 | The ci.yml path variables on lines 93 to 107 name no tests/guardrails path. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-57 | The copilot-instructions Test quality ratchet section starts at line 95. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| R-58 | The copilot-instructions Local gates table holds the Compile, Lint, and Format rows at lines 57 to 59. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R-59 | The copilot-instructions Local gates table holds the Symbols row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-60 | The copilot-instructions Local gates table holds the Security lint row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| R-61 | ci.yml sets PYTHON_VERSION to 3.15. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 77 |
| R-62 | pyproject.toml dev extra pins pip-audit==2.10.1. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 116 |
| R-63 | ci.yml job pip_audit runs on ubuntu-latest. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 465 |
| R-64 | Copilot-instructions line 420 states that container-build pushes the image on a push to main or on a manual dispatch. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 420 |
| R-65 | The Dependabot options reference lists version examples for npm, Bundler, Docker, NuGet, and Maven, and none for pip. | content/code-security/reference/supply-chain-security/dependabot-options-reference.md (github/docs) | github/docs main | 7a170f73f940ed043c828c028ba705b8f5c72847 | present | 422 |
| R-66 | test_dependency_declaration_parity.py checks direct requirements, which is_direct identifies. | tests/guardrails/test_dependency_declaration_parity.py | main | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 55 |
| R-67 | AGENTS.md exists at the repository root and holds the rules that this record cites. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-68 | The container-build.yml comment at line 22 says the auto-merge workflow calls the trigger after every merge into main. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 22 |
| R-69 | The .github folder holds 14 entries on main, which exceeds five. | .github | main | n/a | present | 0 |

## Sources

Local files, read only:

- `AGENTS.md`, in full. The rules for pull requests, closing, security findings, and gates.
- `.github/copilot-instructions.md`, lines 1 to 640, including the Local gates table.
- `.specify/memory/constitution.md`, in full. Principles I, IV, VI, and VII, and the Governance section.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The shape of each record file.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`, headings and ranges of `spec.md`, `plan.md`, and `tasks.md`.
- `documentation/quality-gates.md`, lines 1 to 80.
- `changelog.d/README.md`, in full.
- `tests/guardrails/test_dependency_lock_file.py`, `test_dependency_export.py`, and `test_dependency_declaration_parity.py`.
- `pyproject.toml`, lines 70 to 135. `uv.lock`, lines 1298 to 1306 and 2425 to 2450.
- `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA`, line 31.

Remote, GitHub API, GET only, repository `jmorrison-juniper/MistHelper`:

- Issue #4896, pull request #4888 (view, list, and files), issue #4688, and the quality-gate issue list.
- Run 45064243269 (view, jobs, and failed-job log), job 137338084755 log, run 42518136545 job 128848108669 log, and run 45774119357 (main).
- Commits `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` and `e86098cdc2b189d217805b3b4060ef609cbc37af`.
- File contents at `main` and at `e86098cdc2b189d217805b3b4060ef609cbc37af`, as listed in the table.
- One recursive tree call for `main`, and directory listings of `tests/guardrails`, `changelog.d`, `.github`, and the route leaf. The content of `container-build.yml` and `auto-merge.yml`.

Upstream, fetched:

- https://pypi.org/pypi/radon/6.0.1/json
- https://pypi.org/project/radon/
- https://pypi.org/pypi/mando/0.8.2/json
- https://pypi.org/pypi/mando/0.7.1/json
- https://api.github.com/repos/github/docs/contents/content/code-security/reference/supply-chain-security/dependabot-options-reference.md

The fetch tool blocked `docs.github.com`. The `github/docs` source file, read through the GitHub API, replaces that page.

## Unverified

- **U-1**: Whether an `ignore` rule with `update-types` applies to the pip ecosystem, and whether it also blocks Dependabot security updates for mando. The fetched reference states neither point (R-50).
- **U-2**: Whether the replacement pull request passes every job. No run exists for the branch yet.
- **U-3**: Whether issues #4891 to #4905 close on their own after the replacement merges. The documentation describes closure for a gate that passes on main (R-38), and the behavior for pull request issues is not confirmed.
- **U-4**: Whether radon has unpublished work that accepts mando 0.8. Only PyPI was checked (R-47).
- **U-5**: Whether pip-audit reports a vulnerability in `requirements.txt` today. The tool was not run, because the record runs no tool. Main reports success for the job (R-43).
- **U-6**: Whether the resolver error appears on Python versions other than the runner version. No install was run.
- **U-7**: Whether a legacy record for issue 4896 exists outside the route on main. The local search found none. The remote route leaf is absent (R-42). A second remote tree search was not run.
- **U-8**: The pip syntax for the `versions` option of an ignore rule. The reference shows no pip example (R-65).
- **U-9**: Whether the build sets the OCI image revision label to the merge commit SHA. The reusable build workflow that the container build calls was not read.
- **U-10**: Whether the two failed jobs without the resolver error, `pytest (coverage gate)` and `E2E smoke tests`, fail only on a downstream result. Their full logs were not read.
- **U-11**: Whether the remote copies of `AGENTS.md` and the constitution match the local files byte for byte. The sizes match for `AGENTS.md`, at 18482 bytes (R-67). The constitution size is 25791 bytes on main, and the local size was not compared. The rule text and the Governance wording come from the local checkout.
- **U-12**: Whether the `.specify/templates` files match their remote copies. The templates were read from the local checkout only.

## Skills

No skill was loaded. The issue concerns Python dependency resolution and GitHub Actions. It has no Podman or Juniper device question.
