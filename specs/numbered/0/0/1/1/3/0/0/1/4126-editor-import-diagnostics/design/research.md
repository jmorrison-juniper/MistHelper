# Research: Editor Import Diagnostics (issue #4126)

## 1. Method

- Remote truth: GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local HEAD is the same commit. Each remote row cites a ref, a blob SHA, and a line.
- Local rows cover the pinned SDK in `.venv`, the installed Pylint package, and the VS Code extension folders. Each local row uses ref `local` and blob SHA `none`.
- The run used read-only commands only. No analyzer, build, test, install, or editor session ran.
- No skill was loaded. The issue concerns Pylint and editor setup, not Podman or Juniper device behavior.
- No URL was fetched. Each external claim cites a local source.

## 2. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk.

### D-1 Record location and slug

- Alternatives: a timestamp route under `specs\live\` (rejected, because numeric issue records use the numbered route). A direct child of `specs\` (rejected, because only managed roots are allowed).
- Chosen: `specs\numbered\0\0\1\1\3\0\0\1\4126-editor-import-diagnostics`. The base-5 digits of 4126, padded to width 8, are 0 0 1 1 3 0 0 1 (row R67).
- Reason: No legacy record exists (row R74). Each parent holds five children or fewer (rows R72 and R73).
- Risk: None known. The level `1/1` already holds all five digits, so the route reuses an existing digit folder there.

### D-2 Fix scope

- Alternatives: commit `.vscode\settings.json` (rejected, because Git ignores `.vscode/`, row R53). Remove or change the `init-hook` in `pyproject.toml` (rejected, because it changes lint behavior for all developers and CI). Change production imports to another layout (rejected by FR-009, and the imports already match `main`, rows R37 and R41 to R46).
- Chosen: keep the fix in the editor window, the setup doc, and the owner settings. Change no source, `pyproject.toml`, or CI file.
- Reason: The `init-hook` adds the working directory (row R51). The window folder sets that directory (row R82).
- Risk: Each owner window needs setup. The setup doc and the live check cover this risk.

### D-3 Documentation change

- Alternatives: add the 10-path map to `documentation/development-setup.md` (rejected, because the map is issue data and drifts). Add `pylint.importStrategy` guidance now (rejected until the live check confirms the precedence, finding A-05). Keep the file unchanged.
- Chosen: keep `documentation/development-setup.md` unchanged.
- Reason: Its claims match the repository evidence (rows R47 to R49 and R51).
- Risk: The `importStrategy` precedence stays open (unverified item U-3).

### D-4 Verification method

- Alternatives: agent screen inspection (blocked by the missing Screen Recording permission, comment `IC_kwDOQltU8c8AAAABhemIow`). A CI job that runs Pylint from the worktree root (rejected, because CI cannot reproduce the editor window, its working directory, or its interpreter). A terminal check alone (rejected, because the setup doc at lines 243 and 250 says a terminal result does not verify the editor).
- Chosen: an owner-run live editor check. Terminal evidence supports it.
- Reason: The editor state exists only on the owner machine.
- Risk: Owner time is needed. The checklist in `design/checklists/live-check.md` reduces the effort.

### D-5 Automated tests

- Alternatives: a guard test for the 27-path list (rejected, because it checks data, not behavior added by this change). A guard test for the setup doc text (rejected, because it restates the doc). Acceptance checks AT-01 to AT-11 (chosen).
- Chosen: acceptance checks.
- Reason: This change adds no code. The constitution test rule applies to code.
- Risk: CI gives no signal for new E0401 or E0611 messages (findings A-03 and A-04).

### D-6 Closure keyword

- Alternatives: `Closes #4126` (rejected, because it closes the issue at merge, and the owner forbids closure before live evidence). No issue reference (rejected, because it loses the link).
- Chosen: `Refs #4126` in the pull request body.
- Reason: The owner instruction in comment `IC_kwDOQltU8c8AAAABkdn4vA`. The merge commit `83d404f66ada402ed9e8d334da8c8df255e9dee0` says the same.
- Risk: The owner closes the issue by hand after the evidence passes.

### D-7 Path authority

- Alternatives: keep the issue list (rejected, because ten listed paths do not exist). Edit the issue body now (rejected, because rule 5 bars GitHub edits in this task).
- Chosen: the remote-verified current paths (rows R01 to R27), with the old prefix recorded as absent (row R28).
- Reason: GitHub `main` outranks any local search.
- Risk: The issue body stays stale until the owner edits it.

### D-8 Worktree base for the live check

- Alternatives: check the old layout (rejected, because its paths do not exist on `main`). Check the main checkout only (rejected, because the reported failure concerns a worktree window).
- Chosen: rebase onto `main` first when the worktree still uses the retired `org/juniper_rma` folder under `src`.
- Reason: The issue asks for a path check before a rebase, and `main` changed the layout.
- Risk: A rebase can conflict. Resolve the conflict before the live check.

### D-9 Labels

- Alternatives: keep `needs-investigation` (rejected, because this record documents the root cause). Remove `in-progress` (rejected, because the live check is pending).
- Chosen: remove `needs-investigation`. Keep `in-progress`.
- Reason: The repository label list contains both labels.
- Risk: None known.

### D-10 Changelog fragment

- Alternatives: no fragment (rejected, because the constitution says each change MUST add one fragment). a `pr-` prefix followed by the pull request number (rejected, because no pull request number exists yet, row R59). The name from pull request #4322 (rejected, because it collides, row R50).
- Chosen: `changelog.d/issue-4126-editor-import-spec.md` with a `### Changed` heading.
- Reason: The fragment naming rule for an issue without a pull request (row R59).
- Risk: An extra fragment for a change that users do not see. The constitution accepts this.

### D-11 Branch and commit

- Alternatives: a `docs/` branch prefix (rejected, because the constitution lists `fix`, `feat`, and `chore` only, finding A-09). A `fix/` prefix (rejected, because the change fixes no defect in code).
- Chosen: branch `chore/4126-editor-import-diagnostics`. Commit subject `docs(spec): record editor import diagnostics for issue 4126`.
- Reason: The constitution branch rule and the Conventional Commits rule.
- Risk: None known.

## 3. Remote Verification

Result values are `present`, `absent`, `partial`, or `stale`. Ref `main` means GitHub `main` at `f03c6c9b`. Ref `local` means a file in the reviewed checkout or a local tool folder.

Row groups: R01 to R28 are listed issue paths (28 rows). R29 to R36 are cited lines (8 rows). R37 to R40 are current imports (4 rows). R41 to R46 are import targets (6 rows). R47 to R70 are documents and configuration (24 rows). R71 to R74 are route and legacy checks (4 rows). R75 to R90 are local tools (16 rows). R91 is the CI run (1 row). The total is 91 rows.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | Listed MistHelper.py exists on main. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 0 |
| R02 | Listed web_portal/services/operation.py exists on main. | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 0 |
| R03 | Listed correlation.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/workflows/correlation.py` | main | 5687bf116cae51f8180242a51fb4d4e12c1cf06f | present | 0 |
| R04 | Listed asset_lookup.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | main | d4e34076440a8709c409c95a1fed81cbc0091e8a | present | 0 |
| R05 | Listed lookup.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/workflows/lookup.py` | main | 58b5d099659e00e28f0b5e7621f68c5eac548a4d | present | 0 |
| R06 | Listed settings.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/settings.py` | main | 43667e5cff756b8e097d184cefd72286f24aff03 | present | 0 |
| R07 | Listed access_check.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/workflows/access_check.py` | main | ed39f4e1ad8a313041fb5fff0b46458207f75fb2 | present | 0 |
| R08 | Listed case_service.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/api/case_service.py` | main | 51f1042be48a135d587f03e21fae047bb9a71722 | present | 0 |
| R09 | Listed asset_service.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/api/asset_service.py` | main | 3828354a10305391194b8302bd5bceb7a762c20c | present | 0 |
| R10 | Listed export_rows.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/model/export_rows.py` | main | 6d83f9554e08a583a1488a9ae7c04f47b49c7071 | present | 0 |
| R11 | Listed asset.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/model/asset.py` | main | 97a26e5bb997942d3fb06fa81e52f2a6fe665ca7 | present | 0 |
| R12 | Listed gateway.py from the retired `org/juniper_rma` folder moved to the current path. | `src/operations/exporting/juniper_rma/api/gateway.py` | main | 9f857510ad86fd2951f8b94ba549d24ad3ca291c | present | 0 |
| R13 | Listed fake_gateway.py exists on main. | `tests/unit/juniper_rma/fixtures/fake_gateway.py` | main | 13072a7bd637c6c8bac98968b2f775e0243968c8 | present | 0 |
| R14 | Listed test_lookups.py exists on main. | `tests/unit/juniper_rma/workflows/test_lookups.py` | main | 779b9ae49c4d0642cc5cef9eb8d6ab6c3595cc09 | present | 0 |
| R15 | Listed test_asset_service.py exists on main. | `tests/unit/juniper_rma/api/test_asset_service.py` | main | 1296b0162dedb9f5661d283afe1e4b99630eb047 | present | 0 |
| R16 | Listed test_correlation.py exists on main. | `tests/unit/juniper_rma/workflows/test_correlation.py` | main | 77b384814b86033c4cf9cdd1cc9e91907256f8cb | present | 0 |
| R17 | Listed test_access_check.py exists on main. | `tests/unit/juniper_rma/workflows/test_access_check.py` | main | ce27c701c2a0c1e688d36375460b336f8146ae11 | present | 0 |
| R18 | Listed test_case_service.py exists on main. | `tests/unit/juniper_rma/api/test_case_service.py` | main | 4c484570dcef318c666540fc62ce63c2c40d6ffa | present | 0 |
| R19 | Listed test_export_rows.py exists on main. | `tests/unit/juniper_rma/model/test_export_rows.py` | main | 13eca341e57696b462522ba75d173645c3929d59 | present | 0 |
| R20 | Listed test_read_only_boundary.py exists on main. | `tests/unit/juniper_rma/workflows/test_read_only_boundary.py` | main | fdae6c9ed3b3a6b7f097e470860c09dde6ad9816 | present | 0 |
| R21 | Listed test_messages.py exists on main. | `tests/unit/juniper_rma/api/test_messages.py` | main | 8a04bc3b0e6f39b66692f3a5e03061813add06a1 | present | 0 |
| R22 | Listed test_gateway.py exists on main. | `tests/unit/juniper_rma/api/test_gateway.py` | main | 33cd8f17aa235caf10b975aa91f375c7cfead89b | present | 0 |
| R23 | Listed test_asset.py exists on main. | `tests/unit/juniper_rma/model/test_asset.py` | main | 82c413715791f3e4075ca6787c99a4aa5d498739 | present | 0 |
| R24 | Listed test_run_record.py exists on main. | `tests/unit/juniper_rma/model/test_run_record.py` | main | 3532693686e08e3b2d3e989938db2bd23f1ed880 | present | 0 |
| R25 | Listed test_service_request.py exists on main. | `tests/unit/juniper_rma/model/test_service_request.py` | main | 002ff367d8995fc2fc37afcb0f5598e105a701ae | present | 0 |
| R26 | Listed test_menu_entry_metadata.py exists on main. | `tests/unit/test_menu_entry_metadata.py` | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 0 |
| R27 | Listed test_settings.py exists on main. | `tests/unit/juniper_rma/api/test_settings.py` | main | 54102ec08f1539ff121622226f23bb25079164d8 | present | 0 |
| R28 | No path under the listed retired `org/juniper_rma` folder exists on main. | `org/juniper_rma/` below the retired `src` root | main | none | absent | 0 |
| R29 | Cited line 474 holds a closing parenthesis of an import block. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 474 |
| R30 | Cited line 480 holds a name inside an import block. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 480 |
| R31 | Cited line 543 holds a name inside an import block. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 543 |
| R32 | Cited line 699 holds a name inside an import block. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 699 |
| R33 | Cited line 779 holds a closing parenthesis of an import block. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 779 |
| R34 | Cited line 3426 holds a dictionary entry. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 3426 |
| R35 | Cited requests.adapters import at line 3384 does not exist in the file. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 3384 |
| R36 | Cited mistapi devices import moved from line 3678 to lines 3633 and 7904. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 3678 |
| R37 | Six juniper_rma workflow imports use current paths. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 895 |
| R38 | mistapi devices import at line 3633 exists. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3633 |
| R39 | listSiteDevices call at line 7904 exists. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7904 |
| R40 | Interactive auth import block at line 475 exists. | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 475 |
| R41 | Interactive package re-exports LoginOrchestrator and MspOrgSelector. | `src/mist/access/auth/interactive/__init__.py` | main | abc3eba503aa5084272ddbdad218af4590dabf36 | present | 11 |
| R42 | DataCollectionManager is defined in its module. | `src/mist/intelligence/analytics/data_collection_manager.py` | main | 9bb8016a27f1e2146af38424725698a73e983389 | present | 27 |
| R43 | OrgDeviceInventorySummary is defined in its module. | `src/mist/resources/inventory/org_device_inventory_summary_facade.py` | main | 9f3549a47a941287968a9f9fff5cb163a62c75a9 | present | 23 |
| R44 | SiteSystemEventsExporter is defined in its module. | `src/operations/exporting/export/site_system_events_exporter.py` | main | 12dcaccad3a704231f66127e6ed1f60e2414d27d | present | 34 |
| R45 | MarvisActionsOperation is defined in its module. | `src/mist/intelligence/marvis/actions/operation.py` | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 592 |
| R46 | AuditAnalysisOps is defined in its module. | `src/mist/access/audit/audit_analysis_ops.py` | main | dbd8f92a3779e1ef1abef6be90e5f3c5940cdaeb | present | 29 |
| R47 | Setup section heading exists in development-setup.md. | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 197 |
| R48 | Setup doc settings block sets pylint.cwd to the workspace folder. | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 218 |
| R49 | Setup doc terminal command for E0401 and E0611 exists. | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 236 |
| R50 | Pull request 4322 changelog fragment exists on main. | `changelog.d/issue-4126-editor-import-worktree.md` | main | ae9629b50c75033a3f784e1e03ae3ca93fad3a5f | present | 0 |
| R51 | Pylint init-hook adds the working directory to sys.path. | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 566 |
| R52 | Dev requirements pin pylint 4.1.4. | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 313 |
| R53 | Git ignores the .vscode folder. | `.gitignore` | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 248 |
| R54 | Worktree bootstrap Python script exists. | `scripts/bootstrap_worktree.py` | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| R55 | Worktree bootstrap PowerShell script exists. | `scripts/bootstrap_worktree.ps1` | main | 36db3250f4183110584f4bd6d69d1f47ea89aefa | present | 0 |
| R56 | CI runs Pylint with the score threshold. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| R57 | CI citation check scans src and tests only. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 702 |
| R58 | Quality gates document lists the Pylint gate. | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 58 |
| R59 | Changelog README defines the issue fragment name. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R60 | Repository instructions give the worktree bootstrap command. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| R61 | Repository instructions list the STE gate command. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R62 | Repository instructions record the issue 1866 worktree pitfall. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 543 |
| R63 | Spec template exists. | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R64 | Plan template exists. | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R65 | Tasks template exists. | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R66 | Checklist template exists. | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R67 | Route script sets base 5 with width 8. | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R68 | Constitution exists. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R69 | Agent instructions file exists. | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R70 | Reference record spec exists. | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R71 | Target record route has no existing entries. | `specs/numbered/0/0/1/1/3/0/0/1/` | main | none | absent | 0 |
| R72 | Route directory 1/1 holds five children, so no child is added. | `specs/numbered/0/0/1/1` | main | none | present | 0 |
| R73 | Route directory 1/1/3/0 holds one child, so one more child is allowed. | `specs/numbered/0/0/1/1/3/0` | main | none | present | 0 |
| R74 | No record folder named 4126 exists under specs. | `specs/**/4126-*` | main | none | absent | 0 |
| R75 | Local SDK module defines listSiteDevices. | `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py` | local | none | present | 17 |
| R76 | Local SDK package version 0.64.1 meets the pin. | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | local | none | present | 0 |
| R77 | Local requests adapters module exists. | `.venv\Lib\site-packages\requests\adapters.py` | local | none | present | 0 |
| R78 | Local Pylint package version 4.1.4 is installed. | `.venv\Lib\site-packages\pylint-4.1.4.dist-info` | local | none | present | 0 |
| R79 | Local Pylint removes the working directory from sys.path. | `.venv\Lib\site-packages\pylint\__init__.py` | local | none | present | 69 |
| R80 | Local Pylint entry point calls modify_sys_path before run. | `.venv\Lib\site-packages\pylint\__main__.py` | local | none | present | 9 |
| R81 | Local Pylint exits zero at or above fail-under when no fail-on message is set. | `.venv\Lib\site-packages\pylint\lint\run.py` | local | none | present | 267 |
| R82 | Local Pylint extension defines pylint.cwd with a workspace default. | VS Code extensions folder, ms-python.pylint-2026.8.0 `package.json` | local | none | present | 99 |
| R83 | Local Pylint extension defines pylint.importStrategy. | VS Code extensions folder, ms-python.pylint-2026.8.0 `package.json` | local | none | present | 131 |
| R84 | Local Pylint extension defines pylint.interpreter. | VS Code extensions folder, ms-python.pylint-2026.8.0 `package.json` | local | none | present | 145 |
| R85 | Local Pylint extension defines pylint.path. | VS Code extensions folder, ms-python.pylint-2026.8.0 `package.json` | local | none | present | 163 |
| R86 | Local extension bundle contains the interpolation token from the setup doc. | VS Code extensions folder, ms-python.pylint-2026.8.0 `dist/extension.js` | local | none | present | 0 |
| R87 | Local extension text says pylint.path may be ignored in fromEnvironment mode. | VS Code extensions folder, ms-python.pylint-2026.8.0 `package.nls.json` | local | none | present | 0 |
| R88 | Local worktree settings set pylint.cwd to the workspace folder. | `.vscode\settings.json` | local | none | present | 29 |
| R89 | Local settings omit the documented pylint.path and pylint.interpreter keys. | `.vscode\settings.json` | local | none | partial | 30 |
| R90 | Local Windows interpreter path exists in the worktree. | `.venv\Scripts\python.exe` | local | none | present | 0 |
| R91 | Quality Gates run on main at the pinned commit completed with success. | Quality Gates workflow run, event workflow_dispatch | main | none | present | 0 |

## 4. Sources

- Repository files read in full: `AGENTS.md` (blob 44a9afffb5bd6f774973a845d27343e4e528b6ad), `.github/copilot-instructions.md` (blob f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179), `.specify/memory/constitution.md` (blob 4584997a264c5a7ade2ca7441246e1f067083aa1), and the four templates (rows R63 to R66).
- Repository files read in part:
  - `documentation/development-setup.md`, blob 1733975a7e0a0962fe5367e165a21f5831f8c3e5, lines 197 to 262 and the heading list.
  - `pyproject.toml`, lines 563 to 596.
  - `.github/workflows/ci.yml`, lines 503 to 529, 686 to 702, and 734 to 750.
  - `documentation/quality-gates.md`, lines 7, 58, and 170.
  - `changelog.d/README.md`, lines 26 to 28.
  - `MistHelper.py`, the lines in section 3.
  - `web_portal/services/operation.py`, lines 19 to 21 and 285 to 315.
  - `src/mist/access/auth/interactive/__init__.py`, lines 11 to 20.
  - `.specify/scripts/powershell/spec-route.ps1`, lines 7, 17, 34, and 93.
- Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its spec opening, its analysis headings, and its research headings were read for shape only. No content was copied.
- Local SDK and tools: `.venv\Lib\site-packages\mistapi`, `.venv\Lib\site-packages\pylint`, and `.venv\Lib\site-packages\requests`.
- Local editor files: the VS Code extension folder for `ms-python.pylint-2026.8.0`, read for `package.json`, `package.nls.json`, and `dist/extension.js`. The `.vscode\settings.json` and `tasks.json` files were read for key names and for the pylint and python keys only.
- Git commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`: read-only `git grep`, `git ls-tree`, and `git show` commands. A search for the retired dotted form of the listed path returned no match.
- GitHub pull request #4322 (state, changed files, checks, and merge commit) and issue #4126 (body, comments, and labels) were read with `gh`.

## 5. Unverified

- U-1 Live editor state: the window root, the selected interpreter, and the Pylint output. Reason: no editor session is available. The macOS Screen Recording permission is missing (comment `IC_kwDOQltU8c8AAAABhemIow`).
- U-2 Current diagnostic counts on `main` and on the active worktree. Reason: analyzers are forbidden for this task.
- U-3 Precedence between `pylint.path` and `pylint.importStrategy` set to `fromEnvironment`. Reason: the extension says `pylint.path` may be ignored (row R87). The runtime behavior was not run.
- U-4 Runtime meaning of the `${interpreter}` token (row R86). Reason: only the presence of the token in the bundle was checked.
- U-5 STE score of each changed Markdown file. Reason: the STE linter is an analyzer. Task T-LOCAL-GATES measures the score.
- U-6 Extension versions used by the owner editor. Reason: only the reviewed machine was read.
- U-7 Whether every imported name resolves on `main` beyond the cited lines. Examples are the `_SITE_OPS` imports at `web_portal/services/operation.py` lines 314 and 315. Reason: no analyzer runs. The Quality Gates run on `main` (row R91) covers tested import paths, not editor diagnostics.
- U-8 The claim at setup doc line 212 that a changed `python.defaultInterpreterPath` does not replace a saved selection. Reason: the Python extension source was not read.

## 6. Not Applicable References

- Mist API OpenAPI files and endpoint coverage files: not applicable. The change makes no Mist endpoint call. Only the import path and the signature of `listSiteDevices` matter (row R75).
- `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`: not applicable. A `git grep` at `f03c6c9b` for pylint, E0401, E0611, worktree, interpreter, or editor returned no match (exit code 1).
- Skills: none loaded. The issue concerns Pylint and editor setup. No Podman or Juniper device behavior applies.
