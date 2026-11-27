# Research: Windows Symlink Privilege in the Spec-Route Contract Guard

Each decision lists the chosen option, the reason, the other options, and the risk. The evidence uses local files whose blob SHA matches the remote `main` tree, GitHub reads, and Microsoft pages that this run fetched. This run executed no test, build, or gate.

## Decisions

## D-1. Change the test fixture only

- **Decision**: Change `tests/guardrails/test_spec_route_contract.py` only. Keep the production reparse-point checks unchanged.
- **Rationale**: The failing call is `selected.symlink_to(parent, target_is_directory=True)` at line 296. The production check already rejects reparse points at `common.ps1` lines 258-259 and `spec-route.ps1` lines 110-111 (F-4, F-5). A junction carries the same attribute, so the production branch still runs.
- **Alternatives considered**:
  - Relax the production reparse-point rule for symlinks. Rejected: it weakens the guard, and the issue says no guard changes.
  - Change only the test fixture. Chosen.
- **Risk**: A junction proves the same branch that a symlink proves. It does not prove the symlink creation path. The Ubuntu shard covers that path (F-9).

## D-2. Use a junction, then skip with the cause

- **Decision**: On WinError 1314, create a junction with `cmd /c mklink /J`. If that command fails, skip the case and print the `mklink` output. Raise every other error again.
- **Rationale**: The Windows host still runs the rejection checks. The skip prints a cause, as AGENTS.md lines 142-143 require. CI on Ubuntu runs the real symlink case (F-9).
- **Alternatives considered**:
  - Skip on any link error. Rejected: the Windows host loses the check even when a junction works.
  - Raise the error when the junction fails. Rejected: a host limit then becomes a red gate with no fallback.
  - Monkeypatch the rejection check. Rejected: it weakens the guard.
- **Risk**: `mklink /J` may also need the symlink privilege on the host. The FSCTL page states that rule for setting reparse points and does not limit it to symlinks (F-7). The skip path covers that outcome. Task T-LOCAL-GATES records the result.

## D-3. Do not change host privilege or policy

- **Decision**: This change does not grant the symlink privilege and does not enable Developer Mode.
- **Rationale**: Microsoft states that the right goes only to trusted users, and by default only Administrators hold it (F-8). AGENTS.md line 159 says not to widen permissions to repair a permission error. The fallback works without any host change.
- **Alternatives considered**:
  - Grant the symlink privilege to the account. Rejected: it widens rights to repair a test fixture.
  - Enable Developer Mode. Rejected for this change. It changes a host setting outside this repository, and this run did not verify its effect.
  - Use the junction fallback with a skip (D-2). Chosen.
- **Risk**: Hosts without the privilege need junction creation to work. The owner can still choose Developer Mode on a personal host, outside this record.

## D-4. Add the tests as one class in the existing module

- **Decision**: Add three test methods in the class `TestLinkSelectionFallback`, in `tests/guardrails/test_spec_route_contract.py`. Add the method `link_selection` and the attribute `PRIVILEGE_NOT_HELD` to `SpecCommandFixture`.
- **Rationale**: The task rules prefer existing test files. A single class adds one top-level name to a module that already exceeds five top-level names. `SpecCommandFixture` then holds five members, which the five-item rule allows (constitution line 38).
- **Alternatives considered**:
  - Add three top-level test functions. Rejected: each function adds a top-level name to the module.
  - Add a new module under `tests/guardrails/`. Rejected: it adds a child to a busy directory and splits the shared fixture.
- **Risk**: The module keeps growing. Remediation R-1 in `plan.md` tracks a split in a separate issue.

## D-5. Update the setup document

- **Decision**: Update `documentation/development-setup.md`. Add a PowerShell 7 row to the Requirements table. Add a note about the junction fallback under Step 4.
- **Rationale**: AGENTS.md lines 336-339 require the documentation update in the same change, and they require one location for each technical fact. The guard fails when `pwsh` is absent (RC-20), and the setup document does not mention PowerShell 7 (F-10).
- **Alternatives considered**:
  - Make no document change. Rejected: the Windows behavior changes.
  - Add a new document page. Rejected: it repeats setup facts.
  - Edit the existing setup document. Chosen.
- **Risk**: Low. The STE gate checks the new prose.

## D-6. Add no changelog fragment

- **Decision**: Add no fragment under `changelog.d/`. The pull request states the reason.
- **Rationale**: `changelog.d/README.md` line 58 says to add no fragment for an internal-only change, and to state the reason in the pull request (RC-32). No user sees this change.
- **Alternatives considered**: Add `changelog.d/issue-4778-windows-symlink-privilege.md`. Rejected: the change is internal.
- **Risk**: A reviewer may expect a fragment. The pull request reason answers that question.

## D-7. Branch name and commit type

- **Decision**: Use the branch `fix/4778-windows-symlink-privilege`. Use the subject `fix(tests): use a junction when the symlink privilege is missing`.
- **Rationale**: Issue #4778 carries the `bug` label (F-15). AGENTS.md lines 179-206 give the branch form with a type, the issue number, and a slug. `fix` is the Conventional Commits type for a defect, and `tests` names the changed area.
- **Alternatives considered**: The `test` commit type. Rejected: the commit repairs a defect that users of the guard see.
- **Risk**: None known.

## Findings

- **F-1. The failing call**: `selected.symlink_to(parent, target_is_directory=True)` runs at line 296 of `tests/guardrails/test_spec_route_contract.py`, inside `test_unsafe_feature_selection_fails` (lines 287-301). The call runs before `fixture.run` (line 298). Rows RC-17, RC-21, and RC-22.
- **F-2. The error code**: Microsoft lists error 1314 as `ERROR_PRIVILEGE_NOT_HELD` with the text "A required privilege is not held by the client." Row RC-46.
- **F-3. The selection path**: `check-prerequisites.ps1` line 67 calls `Get-FeaturePathsEnv -NoPersist`. `common.ps1` line 195 calls `Assert-SpecFeatureSelection`. Rows RC-09, RC-10, RC-11, and RC-14.
- **F-4. The reparse-point check**: `Assert-SpecFeatureSelection` starts at the selected path (`$current = $FeatureDir`, line 252). Lines 258-259 reject a reparse point and print `Unsafe selected feature path: $current. Examined $examined parents.` Rows RC-12 and RC-13.
- **F-5. The route script check**: `spec-route.ps1` line 110 rejects a reparse point in `Get-SpecDirectoryCount`. Row RC-15.
- **F-6. Junction documentation**: The mklink page lists `/J` as "Creates a Directory Junction." The hard-links-and-junctions page states that junctions are implemented through reparse points. Rows RC-48 and RC-49.
- **F-7. Junction privilege**: The hard-links-and-junctions page states no privilege rule for junctions (row RC-50, absent). The FSCTL_SET_REPARSE_POINT page states that the calling process must have `SE_CREATE_SYMBOLIC_LINK_NAME` (row RC-51, partial). The two pages do not settle the junction case. Unverified item U-1.
- **F-8. The symlink privilege default**: The Microsoft policy page says that Administrators hold the right by default. It also says that only trusted users should receive it. Row RC-47.
- **F-9. CI platform**: The guard shard job `pytest_coverage_shards` runs on `ubuntu-latest` (row RC-26) and lists `tests/guardrails` in its test paths (row RC-27). A search of the decoded `ci.yml` for `windows-` returned no line. CI therefore runs the symlink case with a real symlink.
- **F-10. Setup document gap**: A search of `documentation/development-setup.md` for `pwsh`, `PowerShell 7`, `Developer Mode`, `symlink`, and `junction` returned no match. The Requirements table starts at line 9 (row RC-35) and ends at line 15 (row RC-36).
- **F-11. Changelog rule**: `changelog.d/README.md` line 58 (row RC-32).
- **F-12. mistapi pin**: The installed `mistapi` reports `__version__ = "0.64.1"` (row RC-44). The pin `>=0.64.0,<0.65` in the section Language and environment of `.github/copilot-instructions.md` holds. This change calls no mistapi function.
- **F-13. Route for issue 4778**: The base-5 algorithm in `spec-route.ps1` (`Get-SpecRadixSegments`, lines 4-31, row RC-16) gives the eight-digit route `0/0/1/2/3/1/0/3` for 4778. The route matches the given ROUTE. No record exists under that route on `main` (row RC-43).
- **F-14. Linked pull requests**: A pull request search for `4778` returned only PR #3361. PR #3361 closes issue #3244. Its body contains the text "4778 passed in 361 seconds", which explains the search hit. PR #3361 is not linked to issue #4778.
- **F-15. Related issue**: Issue #4771 (closed 2026-11-16, label `bug`) reports `os.O_NOFOLLOW` in a dialog audit on Windows. Its body says to investigate "Windows-safe report opening without weakening symlink protection." That issue has a different code path (`tests/e2e/websockets_tab/dialog_audit/support/reporting.py`). Issue #4778 names it as related.
- **F-16. Skills**: No listed skill covers pytest guards or Windows link APIs. No skill was loaded.
- **F-17. Mist API**: The issue names no Mist endpoint. The OpenAPI file `documentation/mist-api-openapi31yaml.yaml` exists locally (4,317,370 bytes). The JSON twin named in the brief is absent. The record makes no Mist claim.
- **F-18. Skip precedent and rule**: The same test module already skips a POSIX-only check with `pytest.mark.skipif` (row RC-23). AGENTS.md lines 142-143 say that a skip must print the cause. `.github/copilot-instructions.md` line 560 records issue #2689, where a guard skipped all its tests and reported green.
- **F-19. Local pwsh**: `C:\Program Files\PowerShell\7\pwsh.exe` exists on the local host (row RC-45). The affected host is not checked (U-8).
- **F-20. Local working tree**: Five files have unstaged edits that the issue does not name (`git status`). The record uses only blobs that match the remote tree. The local edits do not affect any claim.

## Remote Verification

Remote checks use `gh api` on `repos/jmorrison-juniper/MistHelper`. The tree call used `git/trees/main?recursive=1` with `truncated` equal to `false`. Each content read decoded the base64 body and searched it for the cited line. Local `git ls-tree HEAD` blob SHAs matched the remote SHAs for every repository file that this table cites with a line number. Local line numbers for `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md` therefore equal the remote line numbers (rows RC-01 to RC-03).

| # | Claim | Path | Ref | Blob SHA | Result | Line |
|---|-------|------|-----|----------|--------|------|
| RC-01 | AGENTS.md is present with the writing and safety rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-02 | Repository instruction file is present with the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| RC-03 | Constitution is present with Principles I to VII | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| RC-04 | Spec template is present | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-05 | Plan template is present | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-06 | Tasks template is present | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-07 | Checklist template is present | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-08 | Selection helper file is present | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 0 |
| RC-09 | Feature path resolver Get-FeaturePathsEnv is defined | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 145 |
| RC-10 | Resolver calls the selection check | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 195 |
| RC-11 | Selection check Assert-SpecFeatureSelection is defined | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 242 |
| RC-12 | Selection check rejects a reparse point | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 258 |
| RC-13 | Selection check prints the unsafe path message with the examined count | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 259 |
| RC-14 | Prerequisite script calls the resolver | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | present | 67 |
| RC-15 | Route script rejects a reparse point | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 110 |
| RC-16 | Route script defines the base-5 segment function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC-17 | Spec-route contract guard file is present | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| RC-18 | snapshot_tree helper is defined | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 19 |
| RC-19 | SpecCommandFixture class is defined | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 159 |
| RC-20 | Fixture run method requires pwsh | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 172 |
| RC-21 | Target test function test_unsafe_feature_selection_fails is defined | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 287 |
| RC-22 | Symlink creation call raises WinError 1314 at setup | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 296 |
| RC-23 | POSIX-only skipif precedent exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 406 |
| RC-24 | Guard baseline file is present and this record does not change it | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-25 | CI workflow file is present | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |
| RC-26 | Guard shard runs on ubuntu-latest | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 248 |
| RC-27 | Guard shard test paths include tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-28 | MYPY_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-29 | RADON_PATHS excludes the guard module | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| RC-30 | Test-quality analyzer runs in CI | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| RC-31 | Changelog fragment policy guard runs in CI | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| RC-32 | Changelog README allows no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-33 | Quality gates document is present | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| RC-34 | Development setup document is present and is the edit target | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| RC-35 | Development setup has a Requirements heading | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 9 |
| RC-36 | Development setup Requirements table ends with the Container runtime row | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 15 |
| RC-37 | Development setup has a Step 4 heading | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 168 |
| RC-38 | Development setup has the heading "Work on a change" | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 176 |
| RC-39 | Architecture document is present and is read only in this change | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 0 |
| RC-40 | Container deployment document is present and is read only in this change | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 0 |
| RC-41 | Operator guide is present and is read only in this change | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 0 |
| RC-42 | Reference record spec is present | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-43 | No record for issue 4778 exists on main | specs/numbered/0/0/1/2/3/1/0/3/ | main | none | absent | 0 |
| RC-44 | mistapi 0.64.1 is installed locally for the pin check | .venv\Lib\site-packages\mistapi\__version.py | local | not in repository tree | present | 1 |
| RC-45 | PowerShell 7 is installed locally | C:\Program Files\PowerShell\7\pwsh.exe | local | not in repository tree | present | 0 |
| RC-46 | Error 1314 means ERROR_PRIVILEGE_NOT_HELD | https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699- | web | not applicable | present | 0 |
| RC-47 | The symlink privilege defaults to Administrators and goes to trusted users | https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/create-symbolic-links | web | not applicable | present | 0 |
| RC-48 | mklink with the /J option creates a directory junction | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/mklink | web | not applicable | present | 0 |
| RC-49 | Junctions are implemented through reparse points | https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions | web | not applicable | present | 0 |
| RC-50 | Junction creation needs no symlink privilege | https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions | web | not applicable | absent | 0 |
| RC-51 | Setting a reparse point requires SE_CREATE_SYMBOLIC_LINK_NAME. The scope for junctions is unclear. | https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_reparse_point | web | not applicable | partial | 0 |

## Sources

Local files read in this run (read only, with the blob SHA rows that confirm them):

- `AGENTS.md` (full), `.github/copilot-instructions.md` (full), `.specify/memory/constitution.md` (full).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` (full).
- `.specify/scripts/powershell/common.ps1`, `check-prerequisites.ps1` (full), and `spec-route.ps1` (cited ranges).
- `tests/guardrails/test_spec_route_contract.py` (cited ranges, including lines 1-45, 156-218, and 280-430).
- `.github/workflows/ci.yml` (cited ranges), `changelog.d/README.md` (line 58).
- `documentation/development-setup.md` (lines 1-60 and 146-215), `quality-gates.md` and `architecture.md` (headings only), `container-deployment.md` and `operator-guide.md` (not applicable, see below).
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (shape only: folder tree, headings, and checklist layout).
- `.venv\Lib\site-packages\mistapi\__version.py` (line 1).
- `tests/guardrails/process_folder_baseline.json` (existence and blob SHA only).

Not applicable, and not used for a claim:

- `documentation/container-deployment.md` and `documentation/operator-guide.md`: this change starts no container and changes no operator-visible behavior.
- `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md`: the issue names no Mist endpoint (F-17).

GitHub reads (`gh`, with the account token from the brief, read only):

- `gh issue view 4778`, `gh issue view 4771`, `gh pr list --search 4778`, `gh pr view 3361`.
- `gh api repos/jmorrison-juniper/MistHelper/commits/main` (returned `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`).
- `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` with a `--jq` filter for the rows above.
- `gh api` on the contents endpoint of each cited file with `?ref=main`, then base64 decoding of the body. The decoded text gives each cited line.
- Read-only git commands: `rev-parse`, `log -1`, `status`, and `ls-tree HEAD`.

Web pages fetched in this run:

- https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699- (RC-46).
- https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/create-symbolic-links (RC-47). The page is archived.
- https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/mklink (RC-48).
- https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions (RC-49 and RC-50).
- https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_reparse_point (RC-51).
- https://learn.microsoft.com/en-us/windows/win32/fileio/creating-symbolic-links and https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points were read. They state no junction privilege rule, so they support RC-50 as absent and add no row.

Skills: none (F-16).

## Unverified

- **U-1. Junction creation without the symlink privilege**: No fetched source states the rule for junctions (RC-50 absent). The FSCTL page states a privilege rule for reparse points (RC-51 partial). Check: T-LOCAL-GATES on the affected host, and the skip path (D-2).
- **U-2. Results on the affected host**: This run executed no test (repository rule 2). The WinError 1314 result comes from issue #4778. Check: T002.
- **U-3. Junction traversal in `snapshot_tree`**: `Path.rglob` may read junction contents on Python 3.15.2. The before and after comparison holds either way when nothing changes. Check: TEST-01 on Windows.
- **U-4. Junction cleanup by pytest**: Removal of a `tmp_path` that holds a junction is not verified on Python 3.15.2. The junction target stays inside `tmp_path` (Warning in `spec.md`).
- **U-5. Cause of the "in-progress relocation mapping failure"**: The word "relocation" appears in no file under `tests/guardrails`. The issue gives no test identifier. This record makes no claim about it.
- **U-6. The "structural/SDK/output gate" command**: The issue gives no command. No job name in `ci.yml` contains "structural", "sdk compat", or "output scan". This record makes no claim about the gate.
- **U-7. The "137 passed, 1 skipped" composition**: The issue gives no list of tests for this count.
- **U-8. PowerShell 7 on the affected host**: Only the local host was checked (RC-45).
- **U-9. The JSON twin of the Mist OpenAPI file**: The brief names `documentation/mist-api-openapi31yaml.json`. The file is absent locally. The record makes no Mist claim, so this gap has no effect on it.
