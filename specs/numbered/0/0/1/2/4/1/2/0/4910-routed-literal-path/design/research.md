# Research: Restore -LiteralPath in the setup scripts

## Method

- Remote first. Each repository claim in this record cites one row of the remote verification table below. The rows come from reads of `main` through `gh api`. Each row gives the blob SHA and the line of the claim.
- Local reads covered only files whose decoded remote content equals the working copy on 2026-11-26. The equal files are the four scoped scripts, `common.ps1`, both guard modules, `changelog.d/README.md`, and `.gitattributes`.
- Upstream checks read the tag `v1.4.3` of `github/spec-kit` through `gh api`. Each upstream row gives the API URL that the check read.
- No code, test, linter, build, or container ran in this pass (brief rule 2).
- Documentation read: `.github/copilot-instructions.md` and `AGENTS.md` in full, and the constitution in full. `documentation/quality-gates.md` and `documentation/development-setup.md` were searched for the gate, test-quality, and `pwsh` entries (RC-96, RC-97). `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md` were not read. The change adds no architecture module, no container, no port, and no operator text.
- Not applicable: the Mist API and the mistapi SDK. The issue names no Mist endpoint and no SDK function.
- No skill loaded. The issue has no Podman, container, or Juniper device question.

## GitHub Facts

- Issue #4910: open, labels `bug` and `tests`, no comments. Created 2026-11-23. The body names the two scripts, commit `1982b7e84`, and issue #4873.
- Linked pull requests: `gh pr list --state all --search "4910"` returned none.
- Open pull requests: seven. None lists `check-prerequisites.ps1`, `setup-tasks.ps1`, `create-new-feature.ps1`, `test_routed_core_port.py`, `test_spec_route_contract.py`, `speckit.manifest.json`, or `changelog.d/issue-4910`.
- Issue #4873: open, labels `chore`, `docs`, and `in-progress`. Its part 1 record is on `main` (RC-33, RC-34).
- Issues #4869 and #4882: closed. Issue #4869 upgraded the scaffold to 1.4.3 and kept the routed layout.
- Legacy record: no local folder under `specs` starts with `4910-`, and the remote tree holds no path with `4910` (RC-36, RC-37).
- `main` head: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-56). The `ci.yml` workflow run `45774119357` succeeded on the head `f03c6c9b3`.

## Decisions

Each decision names the chosen option, the alternatives, the reason, and the risk. No decision needs a human.

### D-1. Restore -LiteralPath on the optional-document probes

- Chosen: Use `Test-Path -LiteralPath` on each optional-document probe in `check-prerequisites.ps1` and `setup-tasks.ps1`. Use `Get-ChildItem -LiteralPath` on the contracts folder.
- Alternatives: (a) Replace each routed block with the upstream block. (b) Change only the `Test-Path` calls.
- Reason: Upstream 1.4.3 reads these probes with `-LiteralPath` (RC-43, RC-44, RC-45). Option (a) drops the routed `design/` paths (RC-06). Option (b) keeps a wildcard read on the same condition (RC-03, RC-09).
- Risk: Low. The change alters only paths that hold wildcard characters. Tasks T003 and T008 verify the change.

### D-2. Keep the design/ paths

- Chosen: Keep `GetRelativePath` on each design path.
- Alternatives: (a) Restore the upstream literal names, such as `research.md`.
- Reason: The routed layout keeps optional documents under `design/` (RC-100, RC-101). `Get-SpecDesignArtifact` returns design paths (RC-17, RC-18).
- Risk: None new.

### D-3. Scope the guard and the fix to four scripts

- Chosen: The scoped scripts are `check-prerequisites.ps1`, `setup-plan.ps1`, `setup-tasks.ps1`, and `create-new-feature.ps1`. Fix the two bare probes of `create-new-feature.ps1` (RC-13, RC-14).
- Alternatives: (a) Cover only the two scripts that the issue names. (b) Cover every script in the folder.
- Reason: Option (a) leaves the spec-file probe bare. The spec file is a feature path, and upstream keeps `-LiteralPath` on it (RC-46). Option (b) reaches `common.ps1` and `update-agent-context.ps1`. Those probe template paths, override paths, and feature plan paths (RC-21, RC-23, RC-58, RC-59). Each needs its own decision.
- Risk: Two follow-up issues stay open (U-1 and U-2 in `analysis.md`).

### D-4. Place the guard in test_routed_core_port.py

- Chosen: Add the guard to `tests/guardrails/test_routed_core_port.py`.
- Alternatives: (a) A new file in `tests/guardrails`. (b) A new file in `tests/guardrails/e2e_timeout_budget`. (c) A new file in `tests/guardrails/local_test_quality_loop`.
- Reason: Option (a) adds a child to a folder with 81 tracked children (RC-38). Principle I forbids that (RC-74). Option (b) fits by count (RC-61), but that folder tests timeout budgets. Option (c) holds five children (RC-62), which is the limit. The module docstring names the routed-rule guards (RC-24).
- Risk: The module holds 14 top-level names after the change (A-7).

### D-5. Use a line scan with one class and one method

- Chosen: Read each scoped script as text. Split it into lines. Count the probe lines and the bare lines.
- Alternatives: (a) Parse each script with the PowerShell AST through `pwsh`. (b) Use one regular expression across the whole text.
- Reason: Option (a) adds a `pwsh` call to a static check. It adds a failure point and slows the test. Option (b) handles split probes in the same way, but the expression is harder to read. The scripts keep each probe on one line (RC-60).
- Risk: A split probe escapes the scan (A-12). The examined count fails an empty scan.

### D-6. Use bracket characters in the behavior test

- Chosen: Name the feature folders with the characters `[` and `]`.
- Alternatives: (a) Use `*` or `?`. (b) Skip the behavior test and keep only the static guard.
- Reason: Option (a) cannot exist on Windows, because Windows reserves `*` and `?` (Microsoft naming rules). Option (b) does not prove the symptom. The static guard cannot show that `research.md` disappears from the list.
- Risk: The behavior test covers the square-bracket form only. The wildcard `*` and `?` forms cannot exist on Windows.

### D-7. Log with Write-Verbose and Write-Debug

- Chosen: Write each info line with `Write-Verbose`. Write each debug line with `Write-Debug`.
- Alternatives: (a) `Write-Output`. (b) `[Console]::Error.WriteLine`.
- Reason: Option (a) changes the text and JSON output. The scoped scripts have no log channel today, because none calls `Write-Verbose` or `Write-Debug` (RC-60). Option (b) writes to standard error on every run. Both preference variables default to `SilentlyContinue` (Microsoft preference variables, Sources).
- Risk: An operator who passes `-Debug` receives a prompt for each debug line. This is standard PowerShell behavior.

### D-8. Add one changelog fragment

- Chosen: Add `changelog.d/issue-4910-routed-literal-path.md` with one `Fixed` bullet.
- Alternatives: (a) Add no fragment.
- Reason: The change alters the Spec Kit output for bracket folders. Issue #4873 added a fragment for the routed port (RC-32). The fragment rule names the issue form (RC-31) and the heading and bullet form (RC-98).
- Risk: None.

### D-9. Leave the managed manifest unchanged

- Chosen: Do not edit `.specify/integrations/speckit.manifest.json`.
- Alternatives: (a) Update the two hashes to the new file bytes.
- Reason: The manifest is a managed file. Its hashes match neither the fetched upstream bytes nor their CRLF form (RC-48, RC-49). A manual update hides the drift. Issue #4873 part 2 classifies managed-file differences.
- Risk: The manifest stays stale (A-9).

### D-10. Use the fix branch and the conventional title

- Chosen: Use branch `fix/4910-routed-literal-path`. Use the title `fix(spec-kit): restore -LiteralPath in the setup scripts`.
- Alternatives: (a) Use the `feat` type. (b) Use the `chore` type.
- Reason: AGENTS.md lists `fix` as a branch type (RC-70). A restored guard repairs a defect. The title form follows the pull request title rule (RC-87).
- Risk: None.

### D-11. Rely on the auto-merge dispatch for the main image build

- Chosen: Do not dispatch `container-build.yml` by hand. Verify the dispatched run in task T-MERGE.
- Alternatives: (a) Dispatch the workflow by hand after the merge.
- Reason: The auto-merge workflow dispatches each main workflow after a merge (RC-55). The build filter excludes this change (RC-54). A hand dispatch adds a second run.
- Risk: If the dispatch fails, the owner dispatches the workflow by hand (A-10).

## Remote Verification

Columns: ID, claim, path or API URL, ref, blob SHA or commit SHA, result, line. Result values are `present`, `absent`, or `stale`. A line value of 0 means that the claim has no single line.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | check-prerequisites.ps1 probes RESEARCH with Test-Path without -LiteralPath | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 135 |
| RC-02 | check-prerequisites.ps1 probes DATA_MODEL with Test-Path without -LiteralPath | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 136 |
| RC-03 | check-prerequisites.ps1 probes CONTRACTS_DIR with Test-Path and reads it with Get-ChildItem -Path | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 139 |
| RC-04 | check-prerequisites.ps1 probes QUICKSTART with Test-Path without -LiteralPath | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 143 |
| RC-05 | check-prerequisites.ps1 keeps -LiteralPath on the feature folder probe | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 92 |
| RC-06 | check-prerequisites.ps1 builds design document paths with GetRelativePath | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 135 |
| RC-07 | setup-tasks.ps1 probes RESEARCH with Test-Path without -LiteralPath | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | present | 56 |
| RC-08 | setup-tasks.ps1 probes DATA_MODEL with Test-Path without -LiteralPath | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | present | 57 |
| RC-09 | setup-tasks.ps1 probes CONTRACTS_DIR with Test-Path and reads it with Get-ChildItem -Path | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | present | 58 |
| RC-10 | setup-tasks.ps1 probes QUICKSTART with Test-Path without -LiteralPath | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | present | 61 |
| RC-11 | setup-tasks.ps1 keeps -LiteralPath on the tasks template probe | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | present | 71 |
| RC-12 | create-new-feature.ps1 derives the spec file path from the feature folder | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 193 |
| RC-13 | create-new-feature.ps1 probes the spec file with Test-Path without -LiteralPath | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 211 |
| RC-14 | create-new-feature.ps1 probes the spec template with Test-Path without -LiteralPath | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 213 |
| RC-15 | create-new-feature.ps1 keeps -LiteralPath on the spec probe before creation | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 195 |
| RC-16 | setup-plan.ps1 keeps -LiteralPath on the plan probe | .specify/scripts/powershell/setup-plan.ps1 | main | 77c52390bd327f5a7e93588a72ef5e1f9f5d80ab | present | 42 |
| RC-17 | common.ps1 selects design artifacts through Get-SpecDesignArtifact | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 218 |
| RC-18 | common.ps1 Get-SpecDesignArtifact probes with -LiteralPath | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 233 |
| RC-19 | common.ps1 Test-FileExists probes with -LiteralPath (issue 4873 hardening) | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 271 |
| RC-20 | common.ps1 states that -LiteralPath handles wildcard characters | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 10 |
| RC-21 | common.ps1 template and override probes use Test-Path without -LiteralPath | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 379 |
| RC-22 | update-agent-context.ps1 sets NEW_PLAN to the feature plan path | .specify/scripts/powershell/update-agent-context.ps1 | main | 10d3c06f50892ad34c4983ca43056d1821d62936 | present | 44 |
| RC-23 | update-agent-context.ps1 probes NEW_PLAN with Test-Path without -LiteralPath | .specify/scripts/powershell/update-agent-context.ps1 | main | 10d3c06f50892ad34c4983ca43056d1821d62936 | present | 120 |
| RC-24 | test_routed_core_port.py states its purpose as the issue 4873 routed rules guard | tests/guardrails/test_routed_core_port.py | main | 458c160ecc25c85d60bb7242cf2f8814b921f85f | present | 1 |
| RC-25 | test_routed_core_port.py defines the CREATE_NEW_FEATURE constant | tests/guardrails/test_routed_core_port.py | main | 458c160ecc25c85d60bb7242cf2f8814b921f85f | present | 17 |
| RC-26 | test_routed_core_port.py defines ten top-level names | tests/guardrails/test_routed_core_port.py | main | 458c160ecc25c85d60bb7242cf2f8814b921f85f | present | 14 |
| RC-27 | test_spec_route_contract.py defines the SpecCommandFixture class | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 159 |
| RC-28 | test_spec_route_contract.py runs check-prerequisites and setup-tasks in the pointer test | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 254 |
| RC-29 | test_spec_route_contract.py asserts that design/research.md is listed | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 263 |
| RC-30 | test_spec_route_contract.py feature helper writes the design research files | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 190 |
| RC-31 | changelog.d/README.md defines the issue-number-slug fragment name form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-32 | changelog.d/issue-4873-routed-core-port.md shows the Changed fragment shape | changelog.d/issue-4873-routed-core-port.md | main | 751d9bd74d0f149ccda5a8e9edce69a5a100e180 | present | 1 |
| RC-33 | issue 4873 tasks record the -LiteralPath port for common.ps1 | specs/numbered/0/0/1/2/3/4/4/3/4873-routed-git-port/tasks.md | main | 73e57e1c77da14035f5d5ff5bd6c6728bdeb9bbb | present | 7 |
| RC-34 | The issue 4873 route record folder exists | specs/numbered/0/0/1/2/3/4/4/3/4873-routed-git-port | main | f64fb919bc388e33e72d0c2360f6dc28590980b4 | present | 0 |
| RC-35 | The reference record spec file exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-36 | No remote path exists for the issue 4910 route leaf | specs/numbered/0/0/1/2/4/1/2/0 | main | none | absent | 0 |
| RC-37 | No path in the full remote tree names issue 4910 | git/trees/main?recursive=1 | main | none | absent | 0 |
| RC-38 | tests/guardrails holds 81 tracked direct children (79 files and 2 directories) | tests/guardrails | main | none | present | 0 |
| RC-39 | The route node 0/0/1/2/4/1 holds one child, 4 | specs/numbered/0/0/1/2/4/1 | main | none | present | 0 |
| RC-40 | The route node 0/0/1/2/4 holds two children, 1 and 2 | specs/numbered/0/0/1/2/4 | main | none | present | 0 |
| RC-41 | The route node 0/0/1/2/4/1/2 does not exist before this change | specs/numbered/0/0/1/2/4/1/2 | main | none | absent | 0 |
| RC-42 | Commit 1982b7e84 is returned by the commits API and is an ancestor of main | repos/jmorrison-juniper/MistHelper/commits/1982b7e84 | main | 1982b7e8412160f81cb19e8113d784a65b7853b9 | present | 0 |
| RC-43 | Upstream v1.4.3 check-prerequisites.ps1 probes RESEARCH with -LiteralPath | https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/check-prerequisites.ps1?ref=v1.4.3 | v1.4.3 | 734c6c0eabcf59a04495e078fdb38f5a548674a6 | present | 140 |
| RC-44 | Upstream v1.4.3 check-prerequisites.ps1 reads CONTRACTS_DIR with Get-ChildItem -LiteralPath | https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/check-prerequisites.ps1?ref=v1.4.3 | v1.4.3 | 734c6c0eabcf59a04495e078fdb38f5a548674a6 | present | 144 |
| RC-45 | Upstream v1.4.3 setup-tasks.ps1 probes RESEARCH with -LiteralPath | https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/setup-tasks.ps1?ref=v1.4.3 | v1.4.3 | 003bae55ac07faf98d35e8b276a9996850e49fa1 | present | 51 |
| RC-46 | Upstream v1.4.3 create-new-feature.ps1 probes the spec file with -LiteralPath | https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/create-new-feature.ps1?ref=v1.4.3 | v1.4.3 | edb75b32229c1f07b0b9f65604d13f7cdfe94486 | present | 300 |
| RC-47 | Upstream tag v1.4.3 exists in github/spec-kit | https://api.github.com/repos/github/spec-kit/git/refs/tags/v1.4.3 | v1.4.3 | d274613d7469a72d946d61f76b4f2b9bb11b91e2 | present | 0 |
| RC-48 | Manifest hash for check-prerequisites.ps1 differs from the fetched upstream bytes | .specify/integrations/speckit.manifest.json | main | 7f7bc8c7d5e170863aaf8eec0ff27897ffd6c737 | stale | 6 |
| RC-49 | Manifest hash for setup-tasks.ps1 differs from the fetched upstream bytes | .specify/integrations/speckit.manifest.json | main | 7f7bc8c7d5e170863aaf8eec0ff27897ffd6c737 | stale | 11 |
| RC-50 | ci.yml runs speckit-task-audit with the || true suffix | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| RC-51 | ci.yml root-and-contracts shard runs tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-52 | ci.yml runs bandit on the repository with pyproject.toml | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| RC-53 | .gitattributes sets *.ps1 files to eol=crlf in the working tree | .gitattributes | main | 1745af40eeb78dfb5034e6cb2872bf3e0baed923 | present | 20 |
| RC-54 | container-build.yml push filter lists product paths and no .specify, tests, specs, or changelog.d path | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| RC-55 | auto-merge.yml names container-build.yml in its dispatch list after each merge | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 65 |
| RC-56 | main head is commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | repos/jmorrison-juniper/MistHelper/commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-57 | test_spec_route_contract.py defines test_generator_creates_grouped_record | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 427 |
| RC-58 | update-agent-context.ps1 probes the feature plan path with Test-Path without -LiteralPath in Parse-PlanData | .specify/scripts/powershell/update-agent-context.ps1 | main | 10d3c06f50892ad34c4983ca43056d1821d62936 | present | 140 |
| RC-59 | update-agent-context.ps1 probes the feature plan path again with Test-Path without -LiteralPath | .specify/scripts/powershell/update-agent-context.ps1 | main | 10d3c06f50892ad34c4983ca43056d1821d62936 | present | 156 |
| RC-60 | The four scoped scripts hold 26 probe lines (9, 2, 9 and 6 per script), 10 of them bare, and none calls Write-Verbose or Write-Debug | .specify/scripts/powershell/ | main | multiple (RC-01, RC-16, RC-07, RC-13) | present | 0 |
| RC-61 | tests/guardrails/e2e_timeout_budget holds four tracked children | tests/guardrails/e2e_timeout_budget | main | none | present | 0 |
| RC-62 | tests/guardrails/local_test_quality_loop holds five tracked children | tests/guardrails/local_test_quality_loop | main | none | present | 0 |
| RC-63 | test_spec_route_contract.py defines python_route, the base-5 route formula | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 33 |
| RC-64 | test_spec_route_contract.py holds 31 top-level names | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 14 |
| RC-65 | test_spec_route_contract.py requires pwsh and fails when pwsh is missing | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 68 |
| RC-66 | ci.yml sets MYPY_PATHS, VULTURE_PATHS, PYDOCSTYLE_PATHS, and INTERROGATE_PATHS to src and entry files, not tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-67 | AGENTS.md defines the Inline comments rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| RC-68 | AGENTS.md defines the Action logging rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| RC-69 | AGENTS.md defines the Tests rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| RC-70 | AGENTS.md defines the Branch naming rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 192 |
| RC-71 | AGENTS.md defines the Writing style rule for Simplified Technical English | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-72 | AGENTS.md defines the Pull request rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 221 |
| RC-73 | AGENTS.md defines the Structure limits for functions | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 77 |
| RC-74 | Constitution Principle I, Five-Item Rule, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-75 | Constitution Principle II, Class-Based Architecture, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| RC-76 | Constitution Principle IV, Full Deployment Pipeline, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-77 | Constitution Principle VI, Inline Comments, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-78 | Constitution Principle VII, Action Logging, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-79 | Constitution Complexity-Driven SpecKit Escalation section is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| RC-80 | copilot-instructions defines the Local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-81 | copilot-instructions gate table Tests row runs the changed test file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-82 | copilot-instructions gate table STE row names the ste-linter command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-83 | copilot-instructions Spec Kit rule requires the eight-level base-5 route for numeric records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| RC-84 | copilot-instructions label sets include the bug type and the tests scope | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 438 |
| RC-85 | copilot-instructions workflow table says close-linked-issues.yml closes the issue named by a merged pull request | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 472 |
| RC-86 | copilot-instructions workflow table says container-build.yml runs on product paths or manual dispatch | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RC-87 | copilot-instructions pull request title section accepts the type(scope) form | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| RC-88 | .ste-linter.toml configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-89 | Pull request template file exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| RC-90 | ci.yml runs the pytest coverage shard on ubuntu-latest | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 248 |
| RC-91 | Constitution Principle III, Safety-First, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| RC-92 | Constitution Principle V, Observability and Logging, is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| RC-93 | Constitution Development Workflow and Quality Gates section is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 337 |
| RC-94 | Constitution Multi-Agent Git Workflow section is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 453 |
| RC-95 | Constitution Technology and Compatibility Constraints section is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| RC-96 | documentation/development-setup.md contains no pwsh or PowerShell 7 text | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| RC-97 | copilot-instructions defines the Test quality ratchet section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-98 | changelog.d/README.md says to write one heading and one bullet for each change type | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 37 |
| RC-99 | The reference record 4920 holds spec.md, plan.md, tasks.md, and analysis.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/ | main | none | present | 0 |
| RC-100 | The reference record 4920 holds design/research.md, design/data-model.md, design/quickstart.md, and design/checklists/requirements.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/ | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-101 | copilot-instructions says design/ holds supporting artifacts when a feature root would exceed five children | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 168 |
| RC-102 | spec-template.md exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-103 | plan-template.md exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-104 | tasks-template.md exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-105 | checklist-template.md exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |

Summary of the table: 105 checks. Results: 100 present, 3 absent, and 2 stale.

## Sources

Repository files, read through the remote checks above:

- `AGENTS.md` (RC-67 to RC-73).
- `.github/copilot-instructions.md` (RC-80 to RC-87, RC-97, RC-101).
- `.specify/memory/constitution.md` (RC-74 to RC-79, RC-91 to RC-95).
- `.specify/templates/` (RC-102 to RC-105).
- `.specify/scripts/powershell/` (RC-01 to RC-23, RC-58 to RC-60).
- `tests/guardrails/test_routed_core_port.py` (RC-24 to RC-26).
- `tests/guardrails/test_spec_route_contract.py` (RC-27 to RC-30, RC-57, RC-63 to RC-65).
- `changelog.d/README.md` and `changelog.d/issue-4873-routed-core-port.md` (RC-31, RC-32, RC-98).
- `.github/workflows/ci.yml`, `container-build.yml`, and `auto-merge.yml` (RC-50 to RC-55, RC-66, RC-90).
- `.gitattributes`, `.ste-linter.toml`, `.github/PULL_REQUEST_TEMPLATE.md`, and `documentation/development-setup.md` (RC-53, RC-88, RC-89, RC-96).

Upstream sources, read through the GitHub API:

- https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/check-prerequisites.ps1?ref=v1.4.3 (RC-43, RC-44).
- https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/setup-tasks.ps1?ref=v1.4.3 (RC-45).
- https://api.github.com/repos/github/spec-kit/contents/scripts/powershell/create-new-feature.ps1?ref=v1.4.3 (RC-46).
- https://api.github.com/repos/github/spec-kit/git/refs/tags/v1.4.3 (RC-47).

Web sources, read with the fetch tool:

- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/test-path?view=powershell-7.6. The `-LiteralPath` text states that no characters are interpreted as wildcard characters.
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_wildcards?view=powershell-7.6. The page states that square brackets are wildcards for the Item cmdlets, so they need escaping.
- https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file. The page lists the reserved characters: `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, and `*`. Square brackets are not in the list.
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables?view=powershell-7.6. The page states that `$VerbosePreference` and `$DebugPreference` default to `SilentlyContinue`.

## Unverified

1. The runtime result of `Test-Path` with `[` and `]` was not observed. Brief rule 2 forbids running code in this pass. The claim rests on the Microsoft wildcard page and on the repository comment (RC-20). Tasks T003 and T008 observe the result.
2. The cause of the manifest hash mismatch (RC-48, RC-49) is not determined. The fetched upstream bytes and their CRLF form give hashes that differ from the manifest.
3. `pwsh` on the CI runner image was not read from the runner documentation. The claim rests on the green `main` run and on the existing tests that require `pwsh` (RC-65, RC-90).
4. The behavior of `speckit-task-audit` on draft records was not read. The record does not depend on it, because CI ignores its exit status (RC-50).
5. The `ste-linter` scores for the new Markdown files were not computed. Brief rule 2 forbids running a linter in this pass. Task T-LOCAL-GATES computes them.
6. The next merge will start `container-build.yml` through the dispatch. The workflow file states that behavior (RC-55). No run was observed. Task T-MERGE observes it.
