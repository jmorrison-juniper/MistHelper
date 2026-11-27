# Implementation Plan: Batch target site snapshot

**Branch**: `fix/4923-batch-site-snapshot` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/spec.md`. The route is `specs\numbered\0\0\1\2\4\1\4\3`, which is the eight-level base-5 route of 4923.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The batch target service reads the full organization site list for each site check. This change keeps one site snapshot in the batch target service of each organization. Each discovery replaces the snapshot. Site checks reuse it for 300 seconds. A lock lets concurrent threads share one read. A failed read clears the snapshot and raises the picker error.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml`, line 23, `requires-python = ">=3.15"`).

**Primary Dependencies**: mistapi 0.64.1. The pin in `pyproject.toml` is at line 29, `mistapi>=0.64.1,<0.65`. The pin in `requirements.txt` is at line 129, `mistapi==0.64.1`. The web UI runs under Gunicorn (`wsgi.py`, line 4).

**Storage**: None. The site snapshot is in memory and lives as long as its batch target service.

**Testing**: pytest for unit, integration, and guardrail tests. The local gates in `.github/copilot-instructions.md` apply to the changed files.

**Target Platform**: Windows 11, macOS, and Linux (`.github/copilot-instructions.md`, section "What this repository is").

**Project Type**: Web portal WebSocket services and the CLI batch of menu 309. Both paths use the same batch target service.

**Performance Goals**: One organization read for each discovery. The current code reads the organization N + 1 times for N sites.

**Constraints**: Mist documents a threshold of 5000 API calls each hour for each API token (`documentation/api/admins/POST_register.md`, line 213). The web UI runs four threads (`wsgi.py`, line 4).

**Scale/Scope**: Issue #4923 reports hundreds of sites in one MSP organization.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | PASS | The new module `pickers/site_snapshot.py` gives `web/services/pickers/` four tracked children: `__init__.py`, `related.py`, `service.py`, and `site_snapshot.py`. `intake/pickers/` keeps its five tracked children and receives no new child. |
| I. Five-item rule, existing debt | PASS with recorded debt | `related.py` has six top-level names: `logger` and five classes. The change adds none. The debt is listed under Complexity Tracking. |
| II. Class-based architecture | PASS | The change adds the class `OrganizationSiteSnapshot`. It adds no standalone wrapper function. |
| III. Safety-first input handling | PASS | The site check still refuses a foreign site before any resource read. A failed read clears the snapshot and raises. |
| IV. Full deployment pipeline | PASS, planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. Deployment and health checks need orchestrator approval. |
| V. Observability and logging | PASS | The new event names are ASCII. The module uses `StructuredTransportLogger`, as `related.py` and `intake/pickers/resources.py` do. |
| VI. Inline comments | PASS, planned | Tasks T005 to T007 require an inline comment on each new or changed line. |
| VII. Action logging | PASS, planned | The refresh logs an info event before the organization read and a debug event after it. A failure logs an error event. |
| Mist Cloud: mistapi only | PASS | The read uses `StreamPickerService.sites()`, which calls `mistapi.api.v1.orgs.sites.listOrgSites`. The change adds no direct HTTP request. |
| Mist Cloud: owned WebSocket transport | PASS, not applicable | The feature owns no WebSocket transport. |
| Package manager | PASS | No dependency file changes. The module uses only standard library modules `threading` and `time`. |
| Container runtime (Podman) | PASS, not applicable | No container starts for this change. |
| File paths | PASS | The change builds no path strings. |
| Output backends | PASS, not applicable | The change writes no export output. |
| Operational store | PASS, not applicable | The site snapshot is in-memory state. It is not a coordination record. |
| Data directory | PASS, not applicable | The change writes no product output file. |
| Container security | PASS, not applicable | No container image or volume changes. |
| Security findings | PASS | The change adds no suppression comment. |
| Test containers | PASS, not applicable | No test container starts. |
| Documentation | PASS | The changelog fragment is added. The operator guide stays accurate (D-10). |
| Branch and labels | PASS | The branch is `fix/4923-batch-site-snapshot`. The labels follow D-13. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      site-snapshot-interface.md
      batch-target-route.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

The file-by-file change map below replaces the generic source tree.

| Path | Action | Reason |
| - | - | - |
| `src/mist/realtime/websocket_streams/web/services/pickers/site_snapshot.py` | Add | Holds the class `OrganizationSiteSnapshot` and the constant `SITE_SNAPSHOT_LIFETIME_SECONDS`. |
| `src/mist/realtime/websocket_streams/web/services/pickers/related.py` | Modify | `BatchTargetPickerService` owns the snapshot and refreshes it in `sites()`. `BatchTargetResolver` receives the snapshot and reads it in `_site_rows`. |
| `tests/unit/websocket_streams/web/test_ws_web_services.py` | Modify | Adds seven unit tests for the snapshot behavior. |
| `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` | Modify | Changes the read-order assertion to the exact list `[ORG_A, ORG_B, ORG_C]` and updates its docstring (lines 557 to 563). |
| `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py` | Modify | Adds a read-count assertion for organization B after a site target read (lines 137 to 147). |
| `changelog.d/issue-4923-batch-site-snapshot.md` | Add | Adds the release-note fragment required by FR-009. |

The following files stay unchanged. Each one was read and checked for a dependency on the changed class.

| Path | Reason it stays unchanged |
| - | - |
| `src/operations/exporting/ex_hardware_inventory/run/routing.py` | `ScopeRouter.Discovery.sites` already calls each organization service once for each discovery (line 62). |
| `src/operations/exporting/ex_hardware_inventory/run/batch.py` | The CLI batch creates the same service with the same signature (line 156). |
| `src/mist/realtime/websocket_streams/web/services/assembly/factory.py` | It builds `ScopeAwareTargets` and passes the constructor signature that stays the same. |
| `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | The preview path calls the same public methods. |
| `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py` | The route contract stays the same (`contracts/batch-target-route.md`). |
| `src/mist/realtime/websocket_streams/web/static/websockets.js` | The browser request shape and concurrency stay the same. |
| `src/mist/realtime/websocket_streams/intake/pickers/resources.py` | `ResourcePicker.sites()` keeps its uncached behavior (FR-012). |
| `src/mist/realtime/websocket_streams/web/services/pickers/service.py` | The `SitePickerService` passthrough keeps its behavior. |
| `documentation/operator-guide.md` | Lines 344 to 347 stay accurate (D-10). |
| `pyproject.toml`, `requirements.txt` | No dependency change. |
| `MistHelper.py` | No menu change. |

## Architecture

The site snapshot sits between the batch target resolver and the picker.

1. **Discovery**: `WebSocketBatchService.preview` (`sessions.py`, line 891) calls `Targets.resolve` (line 903). The site selector calls `sites()` once (`related.py`, line 87). `sites()` calls `OrganizationSiteSnapshot.refresh()`. The refresh reads the picker and replaces the rows.
2. **Site checks**: `Targets._discover` calls `hardware_targets` or `targets` for each selected site (`sessions.py`, lines 288 and 302). `targets()` builds `BatchTargetResolver` with the snapshot (`related.py`, line 63). `_site_rows` calls `OrganizationSiteSnapshot.rows()` (`related.py`, line 160).
3. **Organization read**: The snapshot calls `StreamPickerService.sites()` only during a refresh (`intake/pickers/resources.py`, lines 71 and 77). That call reaches `GET /api/v1/orgs/{org_id}/sites` (OpenAPI, line 20018).
4. **Browser path**: The browser sends one request for each site, in groups of five (`websockets.js`, line 520). Each request reaches `BatchTargetPickerRoutes.site_targets` (`routes/pickers.py`, line 113). The request then follows step 2.
5. **MSP path**: `ScopeRouter.Discovery.sites` calls `services(org)[0].sites()` for each organization (`routing.py`, lines 46 and 62). Each organization has its own snapshot. `ScopeAwareTargets.hardware_targets` sends each site check to the owner service (`routing.py`, lines 186 and 192).

## Dependencies

- No new package. The module uses `threading` for the lock and `time.monotonic` for the lifetime clock. Both come from the standard library.
- Dependency files stay unchanged. The mistapi pin stays at `>=0.64.1,<0.65` in `pyproject.toml`.

## Documentation Updates

- `changelog.d/issue-4923-batch-site-snapshot.md` is added. It has one `###` heading and one `Changed` bullet that names issue 4923.
- `documentation/operator-guide.md` stays unchanged. Lines 344 to 347 still state that the portal loads all pages and does not start partial work.
- `README.md` stays unchanged. The operation count does not change.
- `documentation/architecture.md` stays unchanged. Its module map does not describe the picker classes.

## Risks and Mitigations

1. Caution: a site snapshot can keep a removed site for up to 300 seconds. Mitigation: each discovery replaces the snapshot. A failed read clears it. The lifetime is one named constant (D-2).
2. A slow organization read holds the lock, and other site checks wait. Mitigation: those checks would need the same read. The lock keeps the number of reads at one.
3. A concurrency test can become flaky. Mitigation: the test uses a barrier and asserts only the read count, not timing.
4. A caller can still use the old resolver signature. Mitigation: `BatchTargetResolver(` appears once in the source tree, at `related.py`, line 63. No test constructs the resolver directly.
5. Symbol loss. Mitigation: the change removes no module-level name. The `symbol-diff` gate reports the result.
6. The worker model can change. Mitigation: each process holds its own snapshot, so the read count stays bounded for each process. This assumption is listed in `analysis.md`.
7. The integration assertion depends on the start step. Mitigation: the start range (`sessions.py`, lines 916 to 968) contains no discovery call. The exact read list proves this.

## Rollback Steps

1. Revert the squash commit on `main` with a new pull request. Do not force-push `main`.
2. Restart the web portal process. The snapshot lives in memory, so no data cleanup is needed.
3. Run the three affected test files again. Each file must show the reverted behavior.

Caution: a revert restores the N + 1 organization reads. Previews become slower until a new fix lands.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `related.py` has six top-level names: `logger` and five classes. This is grandfathered debt. | The change edits existing classes and adds no name. | A new class in `related.py` adds a child to a noncompliant module, which the constitution forbids. Splitting the module is a separate refactor. |
