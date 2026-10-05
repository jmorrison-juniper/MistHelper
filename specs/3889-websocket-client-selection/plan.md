# Implementation Plan: WebSocket Client Selection

**Branch**: `jmorrison-juniper-websocket-client-selection` | **Date**: 2026-10-04 | **Spec**: `specs/3889-websocket-client-selection/spec.md`

## Summary

Add optional, device-scoped client suggestions to selected WebSocket utility fields. Keep manual input, utility payloads, confirmation, and locks unchanged. The implementation is complete for verified EX client choices. Human review remains required before merge.

The available evidence supports a wired-client lookup for EX switches. It does not prove that WAN client records belong to one selected SRX or SSR gateway. Keep gateway discovery unavailable until the pinned SDK and response contract prove association.

## Technical Context

**Language/Version**: Python 3.13 or newer and the existing browser JavaScript.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, Flask, pytest, and the existing Playwright setup. Do not add dependencies.

**Storage**: None. Discovery results remain request-scoped and in memory.

**Testing**: Mocked SDK contract tests and isolated Playwright tests with intercepted HTTP requests.

**Target Platform**: MistHelper WebSocket operations portal.

**Project Type**: Python web service with browser JavaScript.

**Performance Goals**: End every discovery state within ten seconds. Do not display partial results as complete.

**Constraints**: Use the existing authenticated Mist SDK session. Do not add a direct HTTP fallback or a device-utility call. Preserve optional `macs` and `mac_address` request fields, accepted manual input, SDK argument order, confirmation, and action locks.

**Scale/Scope**: Three DHCP-release utilities and one EX MAC-table utility. Add no general client directory or persistent cache.

## Constitution Check

| Gate | Result | Evidence or required action |
| - | - | - |
| Ownership | **Cleared for this feature** | PR #3897 merged at `56818841691eda43e5db375071a0ec52b7ddd64e`. The parent transferred exclusive ownership of the WebSocket JavaScript. |
| Other shared files | **Scoped** | PR #3892 merged the audit harness. Only client-picker-specific audit expectations and fixtures changed. PR #3891 merged wording. No template or cancellation-module changes were needed. |
| Mist SDK | **Verified** | The worktree uses Python 3.13 and mistapi 0.64.0. Mocked tests cover SDK method behavior, target scope, response errors, and incomplete results. |
| Device association | **EX only** | Wired client results require selected-site and device-MAC association. SRX and SSR remain manual-only because WAN results do not prove gateway association. |
| MAC filter compatibility | **Unchanged** | The scalar checker accepts complete MAC addresses. The pinned SDK does not document partial or wildcard syntax. The feature does not alter validation. |
| Safety | **Pass** | Discovery uses a read-only SDK GET. Isolated browser tests block every write before transmission. DHCP changes require human review. |
| Test-first | **Pass** | A focused EX DHCP regression failed before page integration because the UI made no client request. It passes after implementation. |
| Deployment pipeline | **Deferred** | No live operation, release, or deployment is authorized. The pull request must not use auto-merge. |

This plan uses the checked-in plan template and the explicit feature directory `specs/3889-websocket-client-selection/`.
The shared feature pointer remains unchanged.

The `specs/` process directory already exceeds the five-child structural limit. This feature adds only its own design records. Track the existing directory debt as separate maintenance work. Do not restructure it here.

## Design

1. Keep the current operation and target fields as the source of truth.
2. Resolve the selected device against the existing site-scoped device picker cache. Use an explicit device MAC from the Mist device record. Do not derive it from `device_id`.
3. For EX only, request wired clients with the verified selected device MAC. Require the response site and device association fields to match the selected target before a row becomes a choice.
4. Keep SRX and SSR client selection unavailable until the exact installed SDK method and its response prove selected-gateway association.
5. Keep `macs` editable and optional. A client choice adds a MAC to the existing list input. Keep `mac_address` editable and optional. A client choice fills the field but does not restrict manual values to discovery results.
6. Return distinct loading, available, empty, request-error, service-error, and unavailable states. Timeout uses unavailable with a timeout reason. A failed lookup never starts or retries a utility.
7. Bind each lookup to the site, device, and operation. Clear stale choices when any target changes. Ignore late results for expired or replaced lookups.
8. Preserve the existing utility request body. The DHCP trigger copies `macs`. The MAC-table trigger copies `mac_address`.
9. Do not show a selector for aggregate streams or unrelated utilities.

If the wired query returns a next page, follow only the pagination method that the pinned SDK supports. If the complete result cannot be established within ten seconds, show unavailable instead of a partial list.

Keep each class at five methods or fewer. Separate wired-client response
validation and association checks from the general site-resource picker.
Keep the client suggestion route and readiness service separate from the
existing site-picker actions. Keep device identity in the validated
site-scoped device facts.

## Implemented File Set

This manifest records the implemented paths. The parent transferred the page scope after PR #3897 merged.

| Path | Proposed purpose | Ownership state |
| - | - | - |
| `src/mist/realtime/websocket_streams/intake/pickers/devices.py` | Resolve the selected site's explicit device MAC. | Implemented. |
| `src/mist/realtime/websocket_streams/intake/pickers/resources.py` and `src/mist/realtime/websocket_streams/intake/pickers/service.py` | Add read-only client lookup behavior using the shared authenticated SDK session. | Implemented. |
| `src/mist/realtime/websocket_streams/web/services/pickers/service.py`, `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py`, and `src/mist/realtime/websocket_streams/web/blueprint/registry.py` | Expose a site-and-device-scoped JSON lookup through the existing picker service. | Implemented. |
| `src/mist/realtime/websocket_streams/catalog/utilities/utility_fields.py` and `src/mist/realtime/websocket_streams/catalog/model.py` | Describe the optional suggestion control without changing SDK field names or payload shape. | Implemented. |
| `src/mist/realtime/websocket_streams/web/static/websockets.js` | Show suggestions, preserve manual values, and reject stale results. | Implemented after ownership transfer. |
| `tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py` | Prove SDK method, request scope, record association, and error handling with mocks. | Added and passing. |
| `tests/e2e/websockets_tab/dialog_audit/test_client_selection.py` | Prove target changes, manual input, selection, request payloads, and safety with intercepted calls. | Added and passing under the isolated audit boundary. |
| `tests/e2e/websockets_tab/test_websockets_page.py` | Existing page behavior and cancellation checks. | Unchanged. |

Do not edit `src/mist/realtime/websocket_streams/catalog/utility_text.py`, the parent-owned audit paths, the #3888 cancellation paths, shared instructions, or shared context records.

## Project Structure

```text
specs/3889-websocket-client-selection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── client-discovery.md

src/mist/realtime/websocket_streams/
├── catalog/utilities/
├── intake/pickers/
├── web/blueprint/
└── web/services/pickers/

tests/
├── unit/websocket_streams/
└── e2e/websockets_tab/
```

**Structure Decision**: Keep design artifacts in this feature's unique directory. Future implementation must extend existing picker and route classes. Create no new package until the five-item structure check confirms a compliant location.

## Validation and Stop Gates

1. PR #3897 merged. The parent transferred the WebSocket JavaScript ownership to this feature.
2. Mocked contract tests prove the pinned SDK method and device-associated client response.
3. The selected site's device record supplies the device MAC. Returned wired records must prove both site and device association.
4. The SDK does not define partial or wildcard `mac_address` filters. The implementation leaves validation unchanged.
5. Isolated browser tests cover success, errors, empty and incomplete results, timeout, stale targets, cancellation, and payload compatibility.
6. SRX and SSR remain manual-only until selected-gateway association is proven.
7. Require human review for DHCP release changes. Do not enable auto-merge.

Human review takes precedence over automatic delivery.
A maintainer controls merge and the existing release pipeline.
This task does not authorize a live DHCP release or production deployment.

## Complexity Tracking

Review the changed picker modules against the five-item rule before merge. The implementation adds no dependency or persistent state.
