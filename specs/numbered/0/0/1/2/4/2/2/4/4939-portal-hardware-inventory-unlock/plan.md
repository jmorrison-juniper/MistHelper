# Implementation Plan: Portal hardware inventory unlock without the free-form shell

**Branch**: `feat/4939-portal-hardware-inventory-unlock` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification in `specs/numbered/0/0/1/2/4/2/2/4/4939-portal-hardware-inventory-unlock/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add the hardware flag `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`. The flag unlocks only the server-owned hardware preset. The shell flag keeps its effect on every free-form shell. The server sets lock scope `hardware_preset` in the hardware branch only. The server checks that scope at preview, for each target, and at start admission. The page names the variable that unlocks the action. This record recommends option 1. Implementation waits for owner decision D-1.

Remote evidence IDs (RC-nnn) refer to `design/research.md`. Line numbers come from `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Technical Context

- **Language**: Python. `pyproject.toml` line 23 requires 3.15 or later (RC-031).
- **Dependencies**: The mistapi pin is `>=0.64.1,<0.65` in `pyproject.toml` line 29 (RC-032). `requirements.txt` line 129 pins `mistapi==0.64.1` (RC-033). The installed package is 0.64.1 (RC-034). The project instruction at `.github/copilot-instructions.md` line 21 says 0.64.0 (RC-004, stale). No dependency changes.
- **Web layer**: Blueprint routes in `web/blueprint/routes/sessions.py` (RC-104).
- **Storage**: No new storage. A preview lives in memory for 300 seconds (`sessions.py` line 77, RC-080).
- **Testing**: pytest (Tests gate, RC-003). Playwright tests in `tests/e2e/websockets_tab/` (RC-119, RC-120). Guardrail tests in `tests/guardrails/` (RC-121, RC-122).
- **Target platform**: Windows 11, macOS, Linux, and the Podman container. This record runs no container.
- **Project type**: Existing portal package `src/mist/realtime/websocket_streams`.
- **Performance**: The lock check adds no network call. It reads one flag and one scope value.
- **Constraints**: Functions hold five parameters or fewer, five blocks or fewer, and 25 lines or fewer. These limits come from the coding standards in this session, not from a repository file. `from_environment` spans lines 46 to 69, which is 24 lines (RC-052, RC-054). One added line reaches the limit.
- **Scale**: One organization or an MSP scope. The MSP checker is `ScopeAwareChecker` (RC-074). Shells run at the existing concurrency, set by `PORTAL_WS_HARDWARE_CONCURRENCY` (`documentation/wiki/Web-Portal.md` line 291, RC-048).

## Constitution Check

The gate runs before research and again after design. Each row cites the evidence.

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule | Pass with recorded debt | Principle I starts at line 38 (RC-006). The five levels are listed on line 71 (RC-007). `StreamSettings` holds nine attributes on lines 35 to 43 (RC-051). This change adds one. Complexity Tracking records it. |
| II. Class-based architecture | Pass | Every change stays in an existing class or module. No wrapper is added (RC-008). |
| III. Safety-first | Pass | The free-form shell stays locked. The server sets the scope. An invalid flag reads as false (RC-009, RC-124, RC-125). |
| IV. Full deployment pipeline | Pass | Steps 1 to 9 (RC-011) map to T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 (RC-012) run after the merge (U-8). |
| V. Observability and logging | Pass | New log lines use ASCII and name the variable only (RC-013, RC-125). |
| VI. Inline comments | Pass | Each changed line gets an inline comment. T-PR checks the comments in review (RC-014). |
| VII. Action logging | Pass | The hardware branch logs before and after the lock check (RC-015). |
| Python version | Pass | RC-031 |
| mistapi REST only | Pass | No REST call is added (FR-014). RC-032, RC-033 |
| Owned WebSocket transport | Pass | The shell path keeps the owned `ShellClient` (RC-101, RC-102). No transport starts. |
| Podman and test containers | Pass | This record runs no container. The live check stays Unverified (U-1). |
| Specification required | Pass | The change touches 22 files in four packages. The escalation rule is RC-016. |
| Audit and secrets | Pass | Each hardware start keeps the WARNING audit event (FR-013). The change adds no token logging. RC-103 reads the token attribute only. |
| Data directory | Not applicable | The change writes no output file. |
| Output backends | Not applicable | The change adds no export. |
| Operational store | Not applicable | The change adds no coordination record. |
| Process folder route | Pass | Route digits `0/0/1/2/4/2/2/4` equal issue 4939 in base 5, padded to eight digits (computed). Each route maps one issue. |

Existing debt does not allow new debt. The only touched debt is the nine-attribute count on `StreamSettings`.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/2/4/4939-portal-hardware-inventory-unlock/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      settings.md
      catalog-payload.md
      refusals.md
    checklists/
      requirements.md
```

### Source Code (repository root)

The change edits existing modules. It adds one changelog fragment and no source module. It adds no test module.

**Structure Decision**: Keep every change in the existing `websocket_streams` package, the batch routing module, the page, the documents, and the existing test modules. The lock scope is a keyword argument, not a new class. The catalog owns the lock rule, as it owns the shell rule (`stream_catalog.py` lines 52 to 63, RC-059, RC-060).

## Architecture

```text
POST preview   (web/blueprint/routes/sessions.py line 110 checks the preset name, RC-104)
  -> WebSocketBatchService.preview          (sessions.py lines 891 to 914, RC-091)
       -> HardwareXmlPreset.parse           (hardware_xml.py line 342, class at line 300, RC-094)
       -> HardwareXmlPreset.batch_request   (hardware_xml.py line 361, fixed command at line 304, RC-096)
       -> Input.selection                   (sessions.py line 94, RC-081)
            -> SelectionParser.parse        (sessions.py line 113, RC-082)
                 -> checker.resolve_definition(kind, key, lock_scope)  (checker.py line 67, RC-070)
                      -> RequestValidator.check_lock                   (validation.py line 53, RC-066)
                           -> StreamCatalog.lock_flag                  (stream_catalog.py line 52, RC-059)
       -> TargetRequestFactory.build -> checker.check_batch(body, lock_scope)  (sessions.py line 447, RC-084)

POST start     (admission)
  -> WebSocketBatchService.start            (sessions.py line 916, RC-092)
       -> validate_fingerprint              (sessions.py line 614, RC-087)
            -> checker.resolve_definition(stored kind, key, lock scope)  (sessions.py line 619, RC-088)
            -> start values include the preset  (sessions.py line 628, RC-089)
       -> owned ShellClient                 (live/runners/shell/lifecycle/opening.py line 90, RC-102)
```

## File-by-File Change Map

Line numbers refer to `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Each cited line has a row in the remote verification table of `design/research.md`.

| # | Exact repository path | Action | Lines on main | RC IDs | Change |
|---|-----------------------|--------|---------------|--------|--------|
| 1 | `src/mist/realtime/websocket_streams/live/sessions/settings.py` | modify | 35 to 43, 46 to 69, 59, 88 | RC-051 to RC-055 | Add field `hardware_inventory_enabled` after line 43. Add one reader line after line 59 that calls `cls._read_flag` with `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`. |
| 2 | `src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py` | modify | 27, 29 to 35, 46 to 48, 52 to 63, 73 to 75 | RC-057 to RC-061 | Add `HARDWARE_FLAG` and `HARDWARE_SCOPE` after line 27. Add a constructor keyword. Apply the scope in `lock_flag`. Add `flags.hardware_inventory` after line 75. |
| 3 | `src/mist/realtime/websocket_streams/intake/start_request/validation.py` | modify | 53 to 59 | RC-066, RC-067 | `check_lock` accepts `lock_scope` and passes it to `lock_flag`. The message on line 59 does not change. |
| 4 | `src/mist/realtime/websocket_streams/intake/start_request/checker.py` | modify | 57, 67 to 71 | RC-069, RC-070 | `check_batch` and `resolve_definition` accept `lock_scope` and pass it to `check_lock`. |
| 5 | `src/operations/exporting/ex_hardware_inventory/run/routing.py` | modify | 207, 215 to 223 | RC-074 to RC-076 | `ScopeAwareChecker.check_batch` accepts `lock_scope` and passes it to the checker. |
| 6 | `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | modify | 94 to 96, 113, 138 to 149, 447, 614 to 619, 891 to 900 | RC-081 to RC-092 | Pass `lock_scope` through `Input.selection` and `SelectionParser.parse`. Pass it to `_operation`. Set the scope in the hardware branch of `preview`. Pass it at the per-target check (line 447) and at admission (lines 614 to 619). |
| 7 | `src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py` | modify | 48, 58 to 63 | RC-099, RC-100 | `_catalog` passes `hardware_inventory_enabled` from the settings to `StreamCatalog`. |
| 8 | `src/mist/realtime/websocket_streams/web/static/websockets.js` | modify | 69, 204 to 215 | RC-105, RC-106 | `changeBatchHardwarePreset` shows the flag name when the payload reports both flags false. It reads `flags.hardware_inventory` only when the key exists. |
| 9 | `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` | modify | 177 to 189 | RC-108, RC-109 | Add the hidden element `wsBatchHardwareLock` with `data-testid="ws-batch-hardware-lock"` near the hardware preset controls. |
| 10 | `deploy/.env.example` | modify | 218 to 221 | RC-039 to RC-041 | Add a commented `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` block after line 221. Blocked until draft PR #4208 merges or its owner completes a handover. |
| 11 | `documentation/operator-guide.md` | modify | 398 to 432 | RC-042 to RC-045 | Rewrite the action section. Name the hardware flag first. Keep the shell warning. Remove the sentence on line 432. |
| 12 | `documentation/wiki/Web-Portal.md` | modify | 130, 284, 291 | RC-046 to RC-049 | Add the hardware flag row after line 284. Update the shell row. Update the unlock steps that start on line 130. |
| 13 | `changelog.d/issue-4939-portal-hardware-inventory-unlock.md` | add | none | RC-021, RC-022 | One `###` heading and one bullet for each change type used. |
| 14 | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/portal.md` | modify | 94, 96 | RC-037, RC-038 | Add a dated amendment under "Locks and limits". |
| 15 | `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py` | modify | 32 | RC-111 | T001, three cases. |
| 16 | `tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py` | modify | 23, 37 | RC-112, RC-113 | T002, five cases. |
| 17 | `tests/unit/websocket_streams/intake/test_ws_start_request.py` | modify | 194 | RC-114 | T003, three cases. |
| 18 | `tests/unit/websocket_streams/web/test_ws_web_services.py` | modify | 489 | RC-115 | T004, four cases. |
| 19 | `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` | modify | 34, 569 | RC-116, RC-117 | T005, three cases. |
| 20 | `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py` | modify | 53 | RC-118 | T006, one case. The fake checker forwards `lock_scope`. |
| 21 | `tests/e2e/websockets_tab/test_websockets_page.py` | modify | 159, 998 | RC-119, RC-120 | T007, one case. |
| 22 | `tests/guardrails/test_hardware_shell_lock_docs.py` | modify | 112, 140 | RC-121, RC-122 | T008, four cases. |

Files 1 to 9 hold the behavior. Files 10 to 14 hold the documents. Files 15 to 22 hold the tests. Total: 21 modify and 1 add. `batch.py` (RC-078, RC-079) and `hardware_xml.py` (RC-094 to RC-098) do not change. `CHANGELOG.md`, `README.md`, `.specify/feature.json`, and the constitution do not change.

### Interface Contracts

Three contract files live in `design/contracts/`: `settings.md` for the environment variables, `catalog-payload.md` for the page payload, and `refusals.md` for refusal codes and browser fields.

## Dependencies

- No new package. The mistapi pin does not change (D-8).
- Owner decision D-1 must precede code.
- Draft PR #4208 lists `deploy/.env.example`. Task T022 waits for that PR to merge or for a handover (AGENTS.md lines 244 and 245, RC-001, RC-002).
- PR #4940 merged on 2026-11-26. It changed `documentation/operator-guide.md`, `documentation/wiki/Web-Portal.md`, `tests/guardrails/test_hardware_shell_lock_docs.py`, and `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`. Tasks T005, T008, T018, and T019 edit that text again (analysis.md A-06).
- Overlap scan: seven open pull requests. Only PR #4208 shares a file with this change map.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| The operator reads the hardware flag as a full unlock. | The operator expects the shell to stay closed. | The page hint, the operator guide, and the wiki name the limit. T002 (c) and T005 (c) check the limit. |
| Warning: a browser field that sets the lock scope opens every free-form shell. | Full command line access to the device. | The scope comes only from the server preset branch. The allowed browser fields exclude commands (`hardware_xml.py` line 344, RC-097). T004 (d) checks the refusal. |
| Caution: a flag change after preview refuses the start. | The operator must preview again. | The admission re-check uses the stored operation (`sessions.py` lines 614 to 619). T004 (c) checks the refusal. |
| `from_environment` exceeds 25 lines. | A coding standard fails. | The change adds one line to the method. A second line needs a helper. |
| Existing callers break on the new keyword. | Test and CLI failures. | The keyword defaults to false. The CLI route keeps `shell_enabled=True` (`batch.py` lines 144 and 147). T006 covers the route. |
| The page fixture lacks the payload key. | The page script fails. | The handler reads the key only when present. T007 covers the fixture on line 159. |
| `deploy/.env.example` changes while PR #4208 is open. | A merge conflict or a lost edit. | T022 waits for the merge or a handover. |
| The documents drift from the code. | The operator follows a wrong step. | T008 checks the flag name and the steps. The STE gate does not cover these files (analysis.md A-02). |
| The site query uses the shell kind (`websockets.js` line 69). | The lock result for the site list is unknown. | Open item U-4. T007 covers the page with both flags false. |

## Rollback Steps

1. Revert the merged change with a new pull request. Do not force-push `main`.
2. Remove the changelog fragment in the revert pull request.
3. Operators leave `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` unset or false. The default keeps the action locked.
4. No data migration exists. Run folders from earlier runs stay valid.
5. Rebuild the container from the reverted revision with `.github/workflows/container-build.yml` (RC-030).

## Complexity Tracking

Grandfathered debt and new design stay in separate rows.

| Violation | Grandfathered or new | Why needed | Simpler alternative rejected because |
|-----------|----------------------|------------|-------------------------------------|
| `StreamSettings` holds nine attributes on `main` (RC-051). The change adds one, so the count becomes ten. | Nine grandfathered. One new. | The hardware flag must reach `StreamCatalog` through the settings reader that owns the other flags. | A second environment reader duplicates the parser and its warning. |
| `StreamSettings.from_environment` spans 24 lines on `main` (RC-052, RC-054). The change makes it 25. | Within the limit. Now at the limit. | One line reads the flag. | A helper for one line adds a function without a gain. |

Remediation action: open a separate incremental issue to group the lock flags of `StreamSettings` into one record. This change does not open that issue.
