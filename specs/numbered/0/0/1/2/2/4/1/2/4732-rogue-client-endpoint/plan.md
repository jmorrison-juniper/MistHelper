# Implementation Plan: Rogue client exports use the client endpoint name

**Branch**: `fix/4732-rogue-client-endpoint` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`. Keep five children or fewer at every new directory level.

## Summary

Menu 29 calls `OrgClientSecurityExporter.rogue_clients`. That method fetches with `listSiteRogueClients`. Its helper `_export_rogues` then writes with the hardcoded endpoint name `listSiteRogueAPs` (`src/operations/exporting/export/org_client_security_exporter.py:216`). The endpoint name selects the SQLite primary key, so client rows collapse under the AP key.

Phase 1 passes the endpoint name from each caller. It adds tests for both exports and the cache-hit path. It corrects the SDK documentation and adds a changelog fragment. Phase 2 repairs existing tables only after human decisions and coordination.

## Technical Context

- **Language/Version**: Python 3.15 or newer (`.github/copilot-instructions.md:20` and `.specify/memory/constitution.md:278`).
- **Primary Dependencies**: mistapi 0.64.1 (`mistapi>=0.64.0,<0.65`). pytest and `unittest.mock` for tests. No new dependency.
- **Storage**: The SQLite file `data/mist_data.db` through the SQLite branch of `DataExporter` (`src/operations/exporting/export/data_exporter.py:379-386`). ArangoDB and Redis through the polyglot router (`data_exporter.py:300-306`, `src/foundation/persistence/db/router.py:232`). Phase 1 changes no schema.
- **Testing**: pytest unit tests in `tests/unit/export/test_org_client_security_exporter.py`. The tests use mocks and `tmp_path` only.
- **Target Platform**: Windows 11, macOS, and Linux. The tool also ships as a Podman container (`.github/copilot-instructions.md:8-17`).
- **Project Type**: Python command-line menu tool with export modules.
- **Performance Goals**: Not applicable. The change adds no request, loop, query, or file read.
- **Constraints**: Obey the rate limit of an external system (`AGENTS.md:128`). Write ASCII-only logs (`constitution.md:182`). Add an inline comment to each changed line (`constitution.md:204`).
- **Scale/Scope**: Two export methods, one helper, one test file, one documentation page, and one changelog fragment.

## Constitution Check

Each row states the result and the reason. Phase 1 rows are Pass. Rows marked planned become Pass after the tasks finish.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, structure (`constitution.md:38`) | Pass | `_export_rogues` gains one keyword-only parameter. No module or directory is added. The route parent `specs/numbered/0/0/1/2/2/4/1/` holds two children, `4` and `2`. |
| I. Function limits (`constitution.md:38`) | Pass | `_export_rogues` keeps two logical blocks, `if rogues` and `else`. The function stays under 25 lines after the logs are added. |
| II. Class-based design (`constitution.md:91`) | Pass | Changes stay inside `OrgClientSecurityExporter`. No wrapper function is added. |
| III. Safety-first (`constitution.md:113`) | Pass | Phase 1 reads no input and adds no destructive operation. Phase 2 deletes nothing without decision D-4 and a typed confirmation. |
| III. Secrets (`constitution.md:113`) | Pass | Log lines name the label and the endpoint name. No secret is logged. |
| IV. Full pipeline (`constitution.md:143`) | Pass, planned | Tasks `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` run in order. |
| V. ASCII logs (`constitution.md:182`) | Pass | Each new log line uses ASCII characters only. |
| VI. Inline comments (`constitution.md:204`) | Pass, planned | Each changed line in the helper and each call site gets an inline comment. |
| VII. Action logging (`constitution.md:235`) | Pass, planned | `_export_rogues` logs info before the export writer call and debug after it (FR-007). |
| Mist Cloud access (`constitution.md:274`) | Pass | The change calls the mistapi functions only. It adds no direct HTTP request. |
| Python version (`constitution.md:278`) | Pass | No version-specific syntax is added. |
| Output backends (`constitution.md:312`) | Pass | The export path stays `DataExporter.write_with_format_selection`. |
| Database keys (`constitution.md:322`) | Pass | `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defines both endpoints (`src/foundation/support/refactors/endpoint_primary_key_strategies.py:1296-1309`). |
| Data directory (`constitution.md:326`) | Pass | Tests use mocks and `tmp_path`. No test writes to `data/`. |
| Test containers (`constitution.md:274`) | Pass | Phase 1 starts no container. |
| Testing (`constitution.md:361`) | Pass, planned | Tests cover both endpoint names, both cache hits, the empty result, and the primary key rule (TST-01 to TST-10). |
| Documentation (`constitution.md:398`) | Pass, planned | The SDK page changes (FR-010). `README.md` holds no rogue export text. |
| Release notes (`constitution.md:398`, `changelog.d/README.md:27`) | Pass, planned | One fragment is added (FR-011). |
| Issue-first and labels (`constitution.md:459`, `constitution.md:487`) | Pass, planned | Add `in-progress` before the branch. The issue already has `bug` and `MistHelper.py`. |
| Branch name (`constitution.md:476`) | Pass, planned | The branch is `fix/4732-rogue-client-endpoint` from `main`. |
| File overlap (`constitution.md:496`) | Pass with a note | Open PR #4813 changes `src/operations/exporting/export/data_exporter.py`. Phase 1 does not change that file. No open PR changes a Phase 1 file. |
| Shared-writer hold (issue comment 3) | Pass | Phase 1 changes none of `sqlite_database_writer.py`, `database_schema_utils.py`, `arango_writer.py`, `data_exporter.py`, or `endpoint_primary_key_strategies.py`. |
| Preservation hold (issue comment 2) | Pass | Phase 1 edits only the reserved test file among the #2746 paths. It does not touch the preserved branch. |
| Publication hold and serial merge (issue comment 3, `.github/copilot-instructions.md:483`) | Pass, planned | `T-PR` waits for the release. One serial merge slot is used. |
| Specification escalation (`AGENTS.md:345`) | Pass | The change touches more than three files and changes database behavior, so a specification is required. |
| Owned WebSocket transport (`constitution.md:274`) | Not applicable | The change owns no WebSocket transport. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      rogue-export-routes.md
      rogue-primary-key-contract.md
      mist-rogue-insights-api.md
    checklists/
      requirements.md
      coordination.md
      regression.md
```

### Source Code (repository root)

```text
src/operations/exporting/export/org_client_security_exporter.py
tests/unit/export/test_org_client_security_exporter.py
documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md
changelog.d/issue-4732-rogue-client-endpoint.md
```

**Structure Decision**: The record uses the managed numeric route. The route is base 5 with eight digits (`.specify/scripts/powershell/spec-route.ps1:7` and `:17`). Issue 4732 maps to the digits `0 0 1 2 2 4 1 2`. The sibling record `4734` uses `0 0 1 2 2 4 1 4` (`specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline`).

## Phase 1 Change Map

Line numbers refer to `main`. The blob SHAs match the local checkout for each file.

| Path | Action | Lines | Change |
| - | - | - | - |
| `src/operations/exporting/export/org_client_security_exporter.py` | Modify | 94 | Pass `api_function_name="listSiteRogueClients"` to `_export_rogues`. |
| same | Modify | 117 | Pass `api_function_name="listSiteRogueAPs"` to `_export_rogues`. |
| same | Modify | 210-224 | Add the keyword-only parameter `api_function_name: str`. Use it at line 216 in place of the literal. Add an info log before the export writer call and a debug log after it. Update the docstring. |
| `tests/unit/export/test_org_client_security_exporter.py` | Modify | 264-283 | Update the two `TestExportRogues` tests to the new signature. Assert the AP endpoint name and the info log text. |
| same | Modify | 291-321 | Update the `TestRogueClients` cache-hit and normal-flow tests. Add the two client tests. |
| same | Modify | 324-355 | Update the `TestRogueAps` cache-hit and normal-flow tests. |
| same | Add | 357-363 | Add class `TestRogueEndpointPrimaryKeys` with two DDL tests before `test_smoke_module_symbols` (line 358). |
| same | Keep | 21-25 and 138-143 | Import lines and the list-type assertion stay unchanged (FR-009). |
| `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md` | Modify | 136 and 153 | Name `mistapi.api.v1.sites.insights`. Name menu 29 as the caller. |
| `changelog.d/issue-4732-rogue-client-endpoint.md` | Add | not applicable | One `###` heading and one **Fixed** bullet that names issue #4732. |

## Phase 2 Change Map (HOLD)

Phase 2 starts only after decisions D-3, D-4, and D-10 and the coordination in `T-HOLD-COORD`.

| Path | Action | Lines | Change | Hold condition |
| - | - | - | - | - |
| `src/foundation/support/refactors/sqlite_database_writer.py` | Modify | 284-290 and 305-318 | Read the existing primary key before the insert. Stop with a report on mismatch (FR-014). | `T-HOLD-COORD` and D-3 |
| `src/foundation/persistence/db/writers/arango_writer.py` | Modify | 1844-1846 | Use a composite vertex key of `client_mac` and `bssid` (FR-016). | `T-HOLD-COORD` with #4725 |
| `tests/unit/export/test_rogue_primary_key_repair.py` | Add | not applicable | Tests TST-12, TST-13, and TST-14 in a new file, so the reserved file stays narrow. | Phase 2 start |
| `documentation/operator-guide.md` | Modify | 752 region | Document the read-only report and the backup step (FR-015). | D-3 |

## Dependencies

- mistapi 0.64.1 is already installed. No new package is added. `requirements.txt` stays unchanged.
- No issue blocks Phase 1. Comment 2 grants the reservation for the test file.
- Phase 2 needs coordination with the owners of #4723, #4724, #4725, and #4726.
- Open PR #4813 changes `data_exporter.py`. Rebase Phase 1 onto `main` before `T-PR`.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| - | - | - | - |
| An existing `OrgRogueClients` table keeps the AP primary key, so client rows still collapse. | High | High | Add the Caution to the changelog and PR body (FR-013). Repair in Phase 2 after D-3. |
| The ArangoDB client key uses `client_mac` only, so one client on two BSSIDs keeps one document. | Medium | Medium | Document the limit in the PR body. Change the key in Phase 2 (FR-016) after #4725 coordination. |
| Stale AP-keyed documents stay in ArangoDB and Redis. | Medium | Medium | Make no automatic cleanup. Require D-4 approval before any change (FR-017). |
| The keyword-only parameter misses a caller. | Low | High | Two callers exist, at lines 94 and 117. Tests TST-01, TST-05, TST-07, and TST-08 cover both. |
| The reserved test file loses an import or the list-type assertion. | Low | Medium | Keep lines 21-25 and 138-143 unchanged (T015). |
| Merge conflict with PR #4813 in `data_exporter.py`. | Low | Low | Phase 1 changes no line of that file. Rebase before `T-PR`. |
| Menu 24 combined export keeps the client endpoint name for AP rows. | Medium | Medium | Open a separate issue (D-9). Do not change the file here. |

## Rollback Steps

1. Revert the Phase 1 commit with a new commit on `main`. Do not force-push `main`.
2. Phase 1 creates no table, collection, or key, so a revert needs no database step.
3. Rows that the client endpoint name wrote stay in place after a revert. Their cleanup needs D-4 approval.
4. Revert the changelog fragment with the code change.

Caution: After a revert, a new SQLite table for rogue clients uses the AP primary key again.

## Complexity Tracking

No violation needs justification. The change adds one keyword-only parameter and two log lines to `_export_rogues`.

## Contracts

Three contract files describe the export route (`design/contracts/rogue-export-routes.md`), the primary key rule (`design/contracts/rogue-primary-key-contract.md`), and the Mist API response shape (`design/contracts/mist-rogue-insights-api.md`). No contract covers a menu title or a CLI option, because menus 29 and 30 keep their titles.

## Verification

Run the commands in `design/quickstart.md`. Record each gate result in the pull request body during `T-PR`.
