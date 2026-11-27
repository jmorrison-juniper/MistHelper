# Research: R0902 and R0903 class design (issue 4134)

## 1. Scope and Scan Basis

The issue names eleven files. Ten of them hold findings at `main` commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca. The eleventh, `fake_gateway.py`, holds none (RC-25).

Each class counts with the pylint rules in the installed source (RC-57 to RC-59):

- **Instance attributes** are the attributes that methods assign. For a dataclass, each field counts. The threshold is 7 (RC-59, line 380). A finding has R0902 when the count is above 7.
- **Public methods** are the methods whose names do not start with an underscore. Dunder methods count too, except `__init__` (RC-58, line 242). Inherited methods count. The threshold is 2 (RC-59, line 390). A finding has R0903 when the count is below 2.
- **Exemptions**: a dataclass is exempt from R0903 (RC-57, line 199).

The counts below are taken from the source at `main` f03c6c9. Pylint did not run (see Unverified U-1).

| Measure | Count |
| - | - |
| Findings at `main` f03c6c9 | 25 |
| R0902 findings | 9 |
| R0903 findings | 16 |
| Files with findings | 10 |
| Resolved by this change | 6 (all R0903) |
| Remaining after this change | 19 (9 R0902, 10 R0903) |

## 2. Decisions

Each decision names the alternatives, the choice, the reason, and the risk. No decision needs a human decision under brief section 6.

### D-1 Keep the three menu factory classes and record three R0903 findings

- **Choice**: Keep `SiteExportUtilsFactory`, `RoutingUtilsFactory`, and `GatewayTemplateConfigManagerFactory` unchanged. Record three R0903 findings (register rows 4 to 6).
- **Alternatives**: (a) Merge the three classes into one `MenuDependencyFactory` with three builder methods. (b) Replace the classes with module-level builder functions.
- **Reason**: The merge changes 18 handler lambdas (RC-05, first at line 3734) and about 12 generated menu pages (RC-27 and the wiki copies). Most of the handlers are interactive or destructive, so the automated sweeps do not run them. Module-level functions break the class-based rule (constitution principle II, in the file that RC-42 cites).
- **Risk**: Three R0903 findings remain. The register states the reason. A future menu change can revisit the merge.

### D-2 Keep the three fallback classes and record three R0903 findings

- **Choice**: Keep `FuzzFallback`, `SSHFallback`, and `RedexpectFallback` (RC-04, lines 2311, 2341, and 2358). Record three R0903 findings (register rows 7 to 9).
- **Alternatives**: (a) Delete the classes, so that a missing package fails with a plain attribute error. (b) Replace the classes with `types.SimpleNamespace` stand-ins.
- **Reason**: Each class raises an `ImportError` with install guidance when the code calls it. Deletion changes the error that an operator sees. A namespace stand-in hides the finding without a design gain. No test names the install functions for these classes (local search of `tests` and `src/foundation/support/refactors/serial_cc` found no match).
- **Risk**: Three R0903 findings remain. The operator guidance stays unchanged.

### D-3 Keep the datetime adapter and record one R0902 and one R0903 finding

- **Choice**: Keep `_DateTimeHandler` (RC-02, line 1744). The dictionary `special_import_handlers` maps `datetime` to the adapter factory (RC-02, line 1404), so the module namespace receives the adapter. Record one R0902 finding (9 attributes) and one R0903 finding (one public method, `__call__`). Follow-up F-2 owns the removal (analysis.md).
- **Alternatives**: (a) Bind the real `datetime` class now and remove the adapter. (b) Move the nine attribute names into a helper object.
- **Reason**: Option (a) changes the bootstrap binding, which runs before the menus start. The five direct `datetime.now(UTC)` call sites (RC-06, line 6690, and lines 7707, 7733, 7770, and 7783) would still work after the change. No test names the adapter or its install function (local search). Option (b) keeps the same nine names in a different object.
- **Risk**: Two findings remain. Follow-up F-2 adds a characterization test before it removes the adapter.

### D-4 Keep GlobalImportManager and record one R0902 finding

- **Choice**: Keep `GlobalImportManager` with 22 instance attributes (RC-01, line 1207). Record one R0902 finding (register row 1). Follow-up F-1 owns the grouping.
- **Alternatives**: (a) Group the attributes into dependency-policy, import-ledger, and UV-state records now. (b) Move the import state into `import_initialization_service.py`.
- **Reason**: The import-initialization service reads these attributes (RC-21, reads from line 19 through line 99). The serial_cc setup test module also reads them (local search, Unverified U-6). Option (a) changes at least two source files and one test module. Option (b) moves the state to a file that already holds the readers, and it keeps the same count.
- **Risk**: One R0902 finding remains. Follow-up F-1 needs a bootstrap-order test first.

### D-5 Keep OperationExecutor and record one R0902 finding

- **Choice**: Keep `OperationExecutor` with 15 instance attributes (RC-20, line 918). Record one R0902 finding (register row 17). Follow-up F-3 owns the grouping.
- **Alternatives**: (a) Group the attributes into `RunCaps`, `RunRegistry`, and `RunServices` now. (b) Extract only `RunCaps`.
- **Reason**: The test modules read private attributes of this class in 34 files (local search, Unverified U-4). One test module alone reads 15 private attributes (RC-22, first at line 80). Extracting only `RunCaps` leaves 11 attributes, which is still above the limit of 7.
- **Risk**: One R0902 finding remains. The run lifecycle and the event publication keep their current form.

### D-6 Keep six frozen schema records and record six R0902 findings

- **Choice**: Keep `ServiceRequest` (18 fields), `RmaRecord` (15 fields), `RmaItem` (21 fields), `JuniperSettings` (16 fields), `AssetRecord` (16 fields), and `AssetCoverageRow` (15 fields). Record six R0902 findings (register rows 11 to 16).
- **Alternatives**: (a) Split each record into nested sub-records. (b) Remove fields that the exports do not read.
- **Reason**: Each field maps to one schema field or one export column. The export code maps the record fields to export keys (RC-15 blob, `export_rows.py` line 380 maps `row.eos_date` to `eosDate`). Nested sub-records change the constructors and the mapping. Removing fields changes the export contract (FR-005).
- **Risk**: Six R0902 findings remain. The register states the reason. The contract tests in the model test modules keep the field behavior fixed.

### D-7 Keep IdentifierRule and record one R0903 finding

- **Choice**: Keep `IdentifierRule` (RC-08, line 14) with one public method, `is_valid`. Record one R0903 finding (register row 10).
- **Alternatives**: (a) Add a `partition` method for the asset lookup (RC-19, line 61). (b) Replace the class with a module-level function.
- **Reason**: Four callers use the same predicate, at RC-17 (lines 103 and 122), RC-18 (line 74), and RC-19 (line 61). Each caller rejects a value in its own way, so a second method serves one caller only. Option (a) widens the scope to the asset lookup module and its tests. Option (b) breaks the class-based rule.
- **Risk**: One R0903 finding remains.

### D-8 Keep the two test doubles and record two R0903 findings

- **Choice**: Keep `FakeTickets` (RC-23, line 84) and the `FakeExporter` in `test_lookups.py` (RC-24, line 52). Record two R0903 findings (register rows 18 and 19).
- **Alternatives**: (a) Add a second public method to each double. (b) Move the doubles to a shared fixture.
- **Reason**: Each double implements one method of one collaborator. A second method has no caller. A shared fixture keeps the same class and the same finding.
- **Risk**: Two R0903 findings remain. The pylint gate reads `src/` only (RC-34), so these findings do not block CI.

### D-9 Add one public method to each of six classes and resolve six R0903 findings

- **Choice**: Add one public method to each of six classes. Each method names logic that the class already performs (RC-10, RC-11, RC-13, RC-14, RC-15, and RC-16). The six resolved findings are listed in section 3.
- **Alternatives**: (a) Record six more exceptions. (b) Add methods that no caller uses.
- **Reason**: Each method extracts a step that a caller already runs. Extraction keeps every result and makes each step testable without the network or the clock.
- **Risk**: Small behavior drift is possible. TS-01 to TS-15 and the existing tests pin each behavior. Caution: a changed token boundary or rate rule can change the request timing. Warning: a wrong cutoff deletes export files that the retention window keeps. Deleted files cannot be restored, so TS-12 and TS-13 pin the cutoff before the change.

### D-10 Use no inline pylint pragma and keep the reasons in the register

- **Choice**: Add no pragma. Keep each reason in section 3. Verify the register with the scan in `quickstart.md`, and with TS-16.
- **Alternatives**: (a) Add `# pylint: disable=too-few-public-methods` or `too-many-instance-attributes` to each class, with a reason. (b) Add entries to `quality_gate_exclusions.json`.
- **Reason**: The repository has no existing pragma for these two messages (local search of `src`, `tests`, `web_portal`, and `scripts` found no match). The repository rules reject suppressions as shortcuts for findings (constitution Security Findings section, file in RC-36). The exclusions file records counts for each gate and path, not reasons for each finding (RC-39, line 90).
- **Risk**: The register can drift from the code when `main` changes. TS-16 repeats the comparison, and T014 repeats the scan before the merge.

### D-11 Add one changelog fragment and follow the constitution

- **Choice**: Add `changelog.d/issue-4134-r0902-r0903-class-design.md`.
- **Alternatives**: (a) Add no fragment, which follows changelog README rule 4 (RC-35, line 58).
- **Reason**: The constitution says that each change MUST add one fragment (RC-36, line 409). The constitution supersedes other practice documents when they conflict (RC-36, line 529). AGENTS.md limits fragments to user-visible changes (RC-37, line 342). The constitution governs.
- **Risk**: A reviewer can ask for no fragment. The pull request body states the conflict and the decision.

## 3. Exception Register

### 3.1 Recorded exceptions (19 rows)

The count column uses the pylint message format, found over limit (for example, 22/7 for R0902) or found over minimum (for example, 1/2 for R0903).

| # | File | Class | Finding | Count | Decision | Reason |
| - | - | - | - | - | - | - |
| 1 | `MistHelper.py` | `GlobalImportManager` | R0902 | 22/7 | D-4 | Import state that the import-initialization service reads. Follow-up F-1. |
| 2 | `MistHelper.py` | `_DateTimeHandler` | R0902 | 9/7 | D-3 | Adapter bound into the module namespace during bootstrap. Follow-up F-2. |
| 3 | `MistHelper.py` | `_DateTimeHandler` | R0903 | 1/2 | D-3 | Adapter exposes names, and it has no method besides `__call__`. |
| 4 | `MistHelper.py` | `SiteExportUtilsFactory` | R0903 | 1/2 | D-1 | Factory with one build entry point for the site export dependencies. |
| 5 | `MistHelper.py` | `RoutingUtilsFactory` | R0903 | 1/2 | D-1 | Factory with one build entry point for the routing dependencies. |
| 6 | `MistHelper.py` | `GatewayTemplateConfigManagerFactory` | R0903 | 1/2 | D-1 | Factory with one build entry point for the template manager. |
| 7 | `MistHelper.py` | `FuzzFallback` | R0903 | 1/2 | D-2 | Stand-in with one entry point. Its operator guidance stays. |
| 8 | `MistHelper.py` | `SSHFallback` | R0903 | 1/2 | D-2 | Stand-in with one entry point. Its operator guidance stays. |
| 9 | `MistHelper.py` | `RedexpectFallback` | R0903 | 1/2 | D-2 | Stand-in with one entry point. Its operator guidance stays. |
| 10 | `src/operations/exporting/juniper_rma/model/service_request.py` | `IdentifierRule` | R0903 | 1/2 | D-7 | One rule predicate with four callers. |
| 11 | `src/operations/exporting/juniper_rma/model/service_request.py` | `ServiceRequest` | R0902 | 18/7 | D-6 | Frozen schema record. Each field is one request field. |
| 12 | `src/operations/exporting/juniper_rma/model/service_request.py` | `RmaRecord` | R0902 | 15/7 | D-6 | Frozen schema record for RMA shipping and contact fields. |
| 13 | `src/operations/exporting/juniper_rma/model/service_request.py` | `RmaItem` | R0902 | 21/7 | D-6 | Frozen schema record for RMA item fields. |
| 14 | `src/operations/exporting/juniper_rma/settings.py` | `JuniperSettings` | R0902 | 16/7 | D-6 | Frozen settings record that readers use by field name. |
| 15 | `src/operations/exporting/juniper_rma/model/asset.py` | `AssetRecord` | R0902 | 16/7 | D-6 | Frozen export record. Each field is one export column. |
| 16 | `src/operations/exporting/juniper_rma/model/asset.py` | `AssetCoverageRow` | R0902 | 15/7 | D-6 | Frozen export record. Each field is one export column. |
| 17 | `web_portal/services/operation.py` | `OperationExecutor` | R0902 | 15/7 | D-5 | Run state read by 34 test and support files. Follow-up F-3. |
| 18 | `tests/unit/juniper_rma/workflows/test_correlation.py` | `FakeTickets` | R0903 | 1/2 | D-8 | Test double for one collaborator method. |
| 19 | `tests/unit/juniper_rma/workflows/test_lookups.py` | `FakeExporter` | R0903 | 1/2 | D-8 | Test double for one collaborator method. |

Totals: 9 R0902 (rows 1, 2, and 11 to 17) and 10 R0903 (rows 3 to 10, 18, and 19).

### 3.2 Resolved findings (6 rows)

| # | File | Class | Before | After | Decision |
| - | - | - | - | - | - |
| a | `src/operations/exporting/juniper_rma/settings.py` | `JuniperSettingsLoader` | R0903 1/2 | `load`, `missing_names` | D-9 |
| b | `src/operations/exporting/juniper_rma/settings.py` | `JuniperLiveCallGuard` | R0903 1/2 | `refusal_message`, `is_automated_run` | D-9 |
| c | `src/operations/exporting/juniper_rma/api/gateway.py` | `RequestRateLimiter` | R0903 1/2 | `acquire`, `refill` | D-9 |
| d | `src/operations/exporting/juniper_rma/api/gateway.py` | `JuniperTokenProvider` | R0903 1/2 | `authorization_header`, `is_fresh` | D-9 |
| e | `src/operations/exporting/juniper_rma/model/export_rows.py` | `PersonalDataRetention` | R0903 1/2 | `purge`, `cutoff` | D-9 |
| f | `src/operations/exporting/juniper_rma/workflows/correlation.py` | `MistTicketReader` | R0903 1/2 | `read`, `to_tickets` | D-9 |

## 4. Remote Verification Table

Each row is one check. The ref column names the branch, the pull request, or the installed package. A `present` result means that the path and the blob or the line exist. A `stale` result means that the issue claim does not match `main`. An `absent` result means that the path does not exist on `main`. Local rows (RC-56 to RC-59) verify installed third-party packages. The blob SHA of each repository path equals the local `git hash-object` value of the same bytes. RC-55 gives a tree SHA, because it names a directory.

| RC | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | GlobalImportManager class (D-4) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1207 |
| RC-02 | _DateTimeHandler class and datetime binding (D-3) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1744 |
| RC-03 | Three menu factory classes (D-1) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1270 |
| RC-04 | Three fallback classes (D-2) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2311 |
| RC-05 | Factory handler lambda, 18 sites (D-1) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3734 |
| RC-06 | datetime.now(UTC) call site outside the adapter (D-3) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6690 |
| RC-07 | Issue body finding at line 1087 (line is an ImportError) | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 1087 |
| RC-08 | IdentifierRule, ServiceRequest, RmaRecord, RmaItem (D-6, D-7) | `src/operations/exporting/juniper_rma/model/service_request.py` | main | 35d3e8beb82b239d71de1f687209071bb98bea1f | present | 14 |
| RC-09 | JuniperSettings record (D-6) | `src/operations/exporting/juniper_rma/settings.py` | main | 43667e5cff756b8e097d184cefd72286f24aff03 | present | 42 |
| RC-10 | JuniperSettingsLoader.load, target of missing_names (D-9) | `src/operations/exporting/juniper_rma/settings.py` | main | 43667e5cff756b8e097d184cefd72286f24aff03 | present | 86 |
| RC-11 | JuniperLiveCallGuard.refusal_message, target of is_automated_run (D-9) | `src/operations/exporting/juniper_rma/settings.py` | main | 43667e5cff756b8e097d184cefd72286f24aff03 | present | 197 |
| RC-12 | AssetRecord and AssetCoverageRow records (D-6) | `src/operations/exporting/juniper_rma/model/asset.py` | main | 97a26e5bb997942d3fb06fa81e52f2a6fe665ca7 | present | 14 |
| RC-13 | RequestRateLimiter.acquire, target of refill (D-9) | `src/operations/exporting/juniper_rma/api/gateway.py` | main | 9f857510ad86fd2951f8b94ba549d24ad3ca291c | present | 50 |
| RC-14 | JuniperTokenProvider.authorization_header, target of is_fresh (D-9) | `src/operations/exporting/juniper_rma/api/gateway.py` | main | 9f857510ad86fd2951f8b94ba549d24ad3ca291c | present | 85 |
| RC-15 | PersonalDataRetention.purge, target of cutoff (D-9) | `src/operations/exporting/juniper_rma/model/export_rows.py` | main | 6d83f9554e08a583a1488a9ae7c04f47b49c7071 | present | 410 |
| RC-16 | MistTicketReader.read and its listOrgTickets call, target of to_tickets (D-9) | `src/operations/exporting/juniper_rma/workflows/correlation.py` | main | 5687bf116cae51f8180242a51fb4d4e12c1cf06f | present | 75 |
| RC-17 | IdentifierRule.is_valid callers (D-7) | `src/operations/exporting/juniper_rma/workflows/lookup.py` | main | 58b5d099659e00e28f0b5e7621f68c5eac548a4d | present | 103 |
| RC-18 | IdentifierRule.is_valid caller (D-7) | `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py` | main | 2fad0cc40c90f0d7f20997427a27420803bf0b4c | present | 74 |
| RC-19 | IdentifierRule.is_valid caller (D-7) | `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | main | d4e34076440a8709c409c95a1fed81cbc0091e8a | present | 61 |
| RC-20 | OperationExecutor class and attribute assignments (D-5) | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 918 |
| RC-21 | GlobalImportManager attribute readers, first at line 19 (D-4) | `src/foundation/support/refactors/serial_cc/import_initialization_service.py` | main | 7c53ccd111cad144afc0fce488a2fb369d42343b | present | 19 |
| RC-22 | Private OperationExecutor attribute reads (D-5) | `tests/unit/web_portal/test_operation_run_registry_caps.py` | main | c72359a797b17b24bed3daa79a0604c3d6255c81 | present | 80 |
| RC-23 | FakeTickets test double, and target module for to_tickets (D-8) | `tests/unit/juniper_rma/workflows/test_correlation.py` | main | 77b384814b86033c4cf9cdd1cc9e91907256f8cb | present | 84 |
| RC-24 | FakeExporter test double in test_lookups (D-8) | `tests/unit/juniper_rma/workflows/test_lookups.py` | main | 779b9ae49c4d0642cc5cef9eb8d6ab6c3595cc09 | present | 52 |
| RC-25 | FakeClock has two public methods, so no finding | `tests/unit/juniper_rma/fixtures/fake_gateway.py` | main | 13072a7bd637c6c8bac98968b2f775e0243968c8 | present | 79 |
| RC-26 | Issue body finding at line 96 (line is a docstring) | `tests/unit/juniper_rma/fixtures/fake_gateway.py` | main | 13072a7bd637c6c8bac98968b2f775e0243968c8 | stale | 96 |
| RC-27 | Generated menu 6 row names a factory handler (D-1) | `documentation/menu_reference.md` | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 43 |
| RC-28 | Target module for missing_names and is_automated_run | `tests/unit/juniper_rma/api/test_settings.py` | main | 54102ec08f1539ff121622226f23bb25079164d8 | present | 1 |
| RC-29 | Target module for refill and is_fresh | `tests/unit/juniper_rma/api/test_gateway.py` | main | 33cd8f17aa235caf10b975aa91f375c7cfead89b | present | 1 |
| RC-30 | Target module for cutoff | `tests/unit/juniper_rma/model/test_export_rows.py` | main | 13eca341e57696b462522ba75d173645c3929d59 | present | 1 |
| RC-31 | Pylint fail-under 9.5 (line 565), and the disable list has no R0902 or R0903 (line 594) | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 565 |
| RC-32 | Documentation pylint row, score at least 9.5 | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 58 |
| RC-33 | Local gates table, Code quality row (line 69), and the Python 3.15 language statement | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 69 |
| RC-34 | CI pylint gate reads SRC_PATH, default src/ | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| RC-35 | Rule 4, no fragment for an internal-only change | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-36 | Constitution: one fragment MUST for each change (409), supremacy clause (529) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-37 | AGENTS: no compatibility shim in refactors (88), user-visible fragment rule (342) | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 88 |
| RC-38 | Reference record tasks file shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 1 |
| RC-39 | Exclusion registry records counts only (pylint entry) | `quality_gate_exclusions.json` | main | 1dc1e56bb0b8579e3a1cb75f125c6178b2c62f0d | present | 90 |
| RC-40 | Windows Python path in the virtual environment | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 44 |
| RC-41 | Architecture guide read, with no RMA class-design guidance | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 0 |
| RC-42 | Constitution principles I, VI, and VII (five-item rule, inline comments, action logging) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-43 | Spec template headings | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| RC-44 | Plan template headings and Constitution Check | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| RC-45 | Tasks template format and phases | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| RC-46 | Checklist template format | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| RC-47 | Base-5 route rule, width 8 | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-48 | Target route folder does not exist before this record | `specs/numbered/0/0/1/1/3/0/1/4` | main | absent | absent | 0 |
| RC-49 | Issue body path src/org/juniper_rma does not exist | `src/org/juniper_rma/model/service_request.py` | main | absent | absent | 0 |
| RC-50 | Changelog guard test reads changelog.d | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 8 |
| RC-51 | Issue comment: PR #4607 still owns MistHelper.py (PR merged 2026-11-13) | `MistHelper.py` | PR #4607 | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 0 |
| RC-52 | Issue comment: draft PR #4358 renames the RMA tests (PR merged 2026-11-13, no RMA test in its file list) | `tests/unit/juniper_rma/workflows/test_lookups.py` | PR #4358 | 779b9ae49c4d0642cc5cef9eb8d6ab6c3595cc09 | stale | 0 |
| RC-53 | PR #4660 changed this file (merged 2026-11-09) | `tests/unit/juniper_rma/workflows/test_lookups.py` | PR #4660 | 779b9ae49c4d0642cc5cef9eb8d6ab6c3595cc09 | present | 0 |
| RC-54 | PR #4662 changed this file (merged 2026-11-09) | `web_portal/services/operation.py` | PR #4662 | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 0 |
| RC-55 | No open PR (7 checked) changes the target directory | `src/operations/exporting/juniper_rma` | open PRs | 5cf8f9c516bb0d95cf5fee3c2a52ddd61155a7fe | present | 0 |
| RC-56 | Installed mistapi 0.64.1 defines listOrgTickets | `.venv\Lib\site-packages\mistapi\api\v1\orgs\tickets.py` | mistapi 0.64.1 (local) | 6a7295f458547c0efe32bc6963ec5e308e559a5b | present | 17 |
| RC-57 | Installed pylint 4.1.4 exempts dataclasses from R0903 | `.venv\Lib\site-packages\pylint\checkers\design_analysis.py` | pylint 4.1.4 (local) | 77d83dd10e7f555103719c43bcb6d0d32d69a960 | present | 199 |
| RC-58 | Installed pylint counts non-underscore methods, inherited ones included (line 239), and dunder methods (line 242), except `__init__` | `.venv\Lib\site-packages\pylint\checkers\design_analysis.py` | pylint 4.1.4 (local) | 77d83dd10e7f555103719c43bcb6d0d32d69a960 | present | 242 |
| RC-59 | Installed pylint defaults: max-attributes 7 (line 380), min-public-methods 2 (line 390) | `.venv\Lib\site-packages\pylint\checkers\design_analysis.py` | pylint 4.1.4 (local) | 77d83dd10e7f555103719c43bcb6d0d32d69a960 | present | 380 |

Remote checks: 59 rows. Stale rows: 4 (RC-07, RC-26, RC-51, RC-52). Absent rows: 2 (RC-48, RC-49).

## 5. Sources

Each source is a local path or a GitHub path at `main` f03c6c9. No URL was fetched.

- Governing files: `AGENTS.md` (RC-37), `.github\copilot-instructions.md` (RC-33), `.specify\memory\constitution.md` (RC-36 and RC-42), `changelog.d\README.md` (RC-35).
- Spec Kit templates: `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` (RC-43 to RC-46). The route rule is in `.specify\scripts\powershell\spec-route.ps1` (RC-47).
- Documents: `documentation\quality-gates.md` (RC-32), `documentation\development-setup.md` (RC-40), `documentation\architecture.md` (RC-41).
- Configuration: `pyproject.toml` (RC-31), `.github\workflows\ci.yml` (RC-34), `quality_gate_exclusions.json` (RC-39).
- Source and test code: the files and symbols in section 3 (RC-01 to RC-27 and RC-50).
- Reference record shape: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (RC-38). Its layout is copied. Its content is not copied.
- Installed packages: `.venv\Lib\site-packages\mistapi` version 0.64.1 (RC-56) and `.venv\Lib\site-packages\pylint` version 4.1.4 (RC-57 to RC-59).
- Issue facts: GitHub issue 4134, body and three comments, read through `gh issue view` on 2026-11-26.
- Linked pull requests: PR #4607, #4358, #4660, and #4662, read through `gh pr view`. The search for `4134` returned no linked pull request.

## 6. Unverified

- **U-1**: Pylint did not run on `main`. The brief forbids linter runs during authoring. The counts are taken from the class bodies and the rules in RC-57 to RC-59. The implementation must run the scan (quickstart section 2).
- **U-2**: The test suite did not run. The brief forbids test runs during authoring.
- **U-3**: The definition of mistapi `get_all` was not found. A definition search of the installed `mistapi` folder returned no match. The call is at `correlation.py` line 83, which this change leaves unchanged. No decision depends on the definition.
- **U-4**: The count of 142 private attribute reads in 34 files is a local search result at HEAD f03c6c9. Only one file (RC-22) has a remote check. The decisions do not depend on the exact figure.
- **U-5**: Readers of the module name `datetime` outside the repository tests and `src/foundation/support/refactors/serial_cc` were not searched. The search covered those folders for the adapter and fallback names only.
- **U-6**: The serial_cc setup test module reads GlobalImportManager attributes 13 times (local search). The file has no remote check.
- **U-7**: The CI pylint job does not print a message list (RC-34). The current message list in CI was not read.
- **U-8**: No upstream pylint documentation was fetched. The installed source is the only pylint evidence.
- **U-9**: The devtools commands (`symbol-diff`, `ste-linter`, `test-quality-analyzer`, `complexity-gate`, and `bandit-exclude-check`) live in `misthelper-devtools`. They were not inspected. Their use comes from the command descriptions in RC-33.
- **U-10**: The reasons that issue comment 3 proposes for the factories, the fallbacks, and the test doubles were checked against the listed call sites. Their full call graphs were not traced.

## 7. Skills and Documents Not Read

- **Skills**: No skill was loaded. The issue concerns Python class design. No Podman, Juniper device, or Mist endpoint behavior is in scope.
- **Not read**: `documentation\container-deployment.md` and `documentation\operator-guide.md`. The change has no container or operator-visible behavior, so these documents do not apply.
- **Not read**: The Mist OpenAPI files. No endpoint behavior is claimed. The one SDK call in scope, `listOrgTickets`, is unchanged (RC-56).
