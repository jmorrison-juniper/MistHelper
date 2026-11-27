# Implementation Plan: Per-port Mist Insights parity in the WAN dashboard

**Branch**: `feat/4330-per-port-mist-insights-parity` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification record at `specs/numbered/0/0/1/1/4/3/1/0/4330-per-port-mist-insights-parity/`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add the seven-day hourly RX and TX series for each WAN port to the existing WAN dashboard. The refresh worker reads one series for each port inside a request cap. The dashboard routes stay cache-only. The change reuses the existing request helper, sample normalizer, last-complete-value writer, and key helpers. It adds one pure helper module and one organization scope for site-scoped requests.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `.github/copilot-instructions.md` requires for each change.

**Primary Dependencies**: mistapi 0.64.x (`mistapi>=0.64.0,<0.65`, R-47), Flask blueprint code, the redis-py client, and requests.

**Storage**: The existing shared Redis service, used through `RedisDashboardCache`. No new database and no file output.

**Testing**: pytest for unit and integration tests. Playwright for browser tests under `tests/e2e/`. Mocked Mist responses only.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container that serves the web portal on port 8055.

**Project Type**: A feature inside the existing web portal and its refresh worker.

**Performance Goals**: At most the request cap of port series calls for each refresh. A planned headroom of 2,500 calls for each token for each hour (D-8).

**Constraints**: 5,000 calls for each token for each hour (R-42). One SDK attempt for each token (R-49, FR-007). No direct HTTP (FR-006). No new published port (FR-015).

**Scale/Scope**: Production site, gateway, and port counts are unmeasured (U-1).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass with recorded debt | `services/` gains one child, which makes three. `tests/unit/wan_dashboard/` gains one child, which makes three. `tests/e2e/web_portal/` has 32 children, so its browser tests edit an existing file. `changelog.d/` has 335 children. It is a process folder, so one fragment is allowed. Debt is in Complexity Tracking. |
| II. Class-based architecture | Pass | The new helper module holds classes. It has no standalone wrapper function. |
| III. Safety-first | Pass | The change adds no destructive operation and no keyboard input. Inputs are validated before use. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. |
| V. Observability and logging | Pass | Log text is ASCII. The worker logs before and after each request. Logs carry no secret (FR-017). |
| VI. Inline comments | Pass | Each changed line gets an inline comment. T003 and T005 require the comments. |
| VII. Action logging | Pass | Each request and each cache write has an info line before it and a debug line after it. |
| Mist: REST through mistapi | Pass | One SDK method is used (R-45 and R-37). No direct HTTP is added. |
| Mist: owned WebSocket transport | Not applicable | The feature owns no WebSocket transport. |
| Mist: contract tests | Pass | TC-01 to TC-06 prove arguments, shapes, units, and failure states. |
| Output backends | Pass with recorded debt | The change adds no export. The WAN worker writes the cache, not an export. Existing portal CSV exports predate `DataExporter` (U-10). The debt has a separate remediation action in analysis.md (A-12). |
| Operational store | Not applicable | The change adds no coordination record. |
| Data directory | Pass | The change writes no product file. Redis holds the cache values. |
| Containers and ports | Pass | No container and no published port are added (FR-015). |
| Security findings | Pass | The plan adds no suppression comment. |
| Secrets | Pass | Redaction happens at the logging boundary (FR-017 and TC-22). |
| Specifications | Pass | This spec precedes the code change, as AGENTS.md requires for a change to three files or more (R-71). |

For a feature that uses Juniper Mist Cloud:

- Every REST request uses the mistapi method `getSiteInsightMetricsForGateway` (R-45).
- The feature proposes no owned WebSocket transport.
- The contract tests in T001 prove the arguments, the response fields, the units, the timestamps, and the port identity.
- The contract tests cover output, failure handling, safety, and secret redaction (TC-01 to TC-06 and TC-22).

## Architecture

The refresh worker runs one cycle. The cycle reads the bulk snapshot first. It then runs the port series phase inside the request cap.

```text
Refresh worker -> bulk snapshot (four reads) -> port series phase -> publish snapshot
Port series phase -> refresh method of WanDashboardService -> MistSessionRunner -> mistapi SDK -> shared admission
Refresh method -> last-complete-value writer -> Redis keys from _traffic_key and _insight_key
Dashboard route -> cache read only -> JSON envelope -> dashboard.js -> port view
```

The port series phase reuses four existing parts:

- The `_request` method of `WanDashboardService`, which applies the one-attempt rule and the token cooldown (R-75).
- The `WanDataNormalizer.traffic_samples` method, which validates UTC samples (R-74).
- The `_remember_result` method, which writes the shared last complete value and the local copy (R-64).
- The `_traffic_key` and `_insight_key` helpers (R-09 and R-76), which name the cache keys.

The phase adds no second collector and no second cache writer.

## File-by-File Change Map

| Path | Action | Purpose | Requirements | Tests |
| - | - | - | - | - |
| `src/interfaces/portals/wan_dashboard/services/port_insights.py` | Add | Pure helpers: window math, response validation, slices, totals, coverage, budget, and cursor. | FR-002, FR-003, FR-005, FR-008, FR-009, FR-011, FR-012 | TC-07 to TC-09, TC-12, TC-24 |
| `src/interfaces/portals/wan_dashboard/services/__init__.py` | Modify | Add one refresh method for a port series. The method uses `_request`, `_remember_result`, and the key helpers. The method wraps site reads in the organization scope. | FR-001, FR-004, FR-006, FR-007, FR-010, FR-011 | TC-15, TC-16, TC-22 |
| `src/interfaces/portals/wan_dashboard/services/worker.py` | Modify | Add the port series phase after the bulk reads. Read the request cap and the cursor. Stop on lease loss. | FR-004, FR-005 | TC-10, TC-11, TC-17 |
| `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` | Modify | Correct the RX and TX copy. Add the port view state elements with stable `data-testid` values. | FR-010, FR-013, FR-014 | TC-18 to TC-21 |
| `src/interfaces/portals/wan_dashboard/static/dashboard.js` | Modify | Render the data state, the UTC collection time, the coverage, and the port totals. Keep the refresh controls unchanged. | FR-010, FR-013, FR-014 | TC-18 to TC-21, TC-23 |
| `src/interfaces/wan_performance/collection/request_admission.py` | Modify | Add `organization_scope`. Site-scoped requests use the tenant from the scope. | FR-006, FR-017 | TC-13, TC-14 |
| `deploy/.env.example` | Modify | Document `WAN_PORT_INSIGHT_REQUEST_CAP` with an empty value and no default. | FR-005 | TC-10 |
| `documentation/operator-guide.md` | Modify | Document the request cap, the budget formula, and the data states. | FR-005, FR-010, FR-013 | STE gate |
| `changelog.d/issue-4330-per-port-mist-insights-parity.md` | Add | One release-note fragment for the change that a user sees. | All | STE gate |
| `tests/unit/wan_dashboard/test_port_insights.py` | Add | Unit tests for the helpers and the budget rules. | FR-002 to FR-005, FR-008, FR-009, FR-011, FR-012 | TC-07 to TC-09, TC-12, TC-24 |
| `tests/unit/wan_dashboard/test_worker.py` | Modify | Worker tests for the cap, the cursor, and the lease. | FR-004, FR-005 | TC-10, TC-11, TC-17 |
| `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` | Modify | Tests for `organization_scope` and the fail-closed rule. | FR-006 | TC-13, TC-14 |
| `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` | Modify | SDK contract tests for the request, the response, and the failure states. | FR-001 to FR-003, FR-007, FR-012 | TC-01 to TC-06 |
| `tests/integration/web_portal/wan_dashboard/test_services.py` | Modify | Service tests for the cache writes, the malformed input, and the redaction. | FR-010, FR-011, FR-017 | TC-15, TC-16, TC-22 |
| `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` | Modify | Browser tests for the port view states, the overview copy, and the refresh behavior. | FR-010, FR-013, FR-014 | TC-18 to TC-21, TC-23 |

No file is deleted.

The `services/` directory gains one child, `port_insights.py`. The `tests/unit/wan_dashboard/` directory gains one child, `test_port_insights.py`. No other directory gains a child.

## Dependencies

- No new package is added. `requirements.txt` stays unchanged.
- The pinned mistapi 0.64.1 supplies the one SDK method (R-45 and R-47).
- The existing Redis service stores the cache values and the cooldown keys.
- Pull request #4208 changes `request_admission.py` and `deploy/.env.example` (R-51 and gh output). The admission edit waits for its decision (D-12).

## Sequence and Gates

1. Resolve D-12. Confirm that the owner accepts the admission edit order.
2. Implement T001 and T003 in parallel. T001 changes only the contract test file. T003 adds only the helper module.
3. Implement T004 after T003.
4. Implement T002 after step 1. It changes `request_admission.py`.
5. Implement T005 after T002 and T003.
6. Implement T006 and T008 after T005. T007 and T011 are independent.
7. Implement T009 after T008. Implement T010 after T006 and T008.
8. Run T-LOCAL-GATES. Open the pull request with T-PR. Watch CI with T-REMOTE-CI. Merge only with T-MERGE.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The live response uses different key names from the code (A-04) | The parser rejects every live response | The parser fails closed (FR-012). TC-03 and TC-04 pin the shape. A live shape check needs owner approval (U-2). |
| The SDK default page size truncates the 168-sample window (A-05) | The series looks complete but misses samples | The request sets `limit` to 168 and `page` to 1. A `next` value marks the series partial (FR-003). |
| Port series calls consume the shared hourly limit for each token | Other MistHelper reads fail with HTTP 429 | The request cap is unset by default (D-8). The worker checks headroom before the phase (TC-24). |
| A caller makes a direct SDK call without the runner (A-23) | One logical read costs up to four attempts | Every port series call uses `_request`. The runner clone sets the SDK retry count to zero (R-11). |
| PR #4208 and the admission module conflict (A-10) | Merge conflict or lost behavior | The admission edit waits for the decision (D-12). The change keeps the admission edit to one function. |
| Local uncommitted owner changes differ from `main` (A-11) | Spec and code disagree with the owner's work | The spec cites `main` only (R-01 to R-81). The owner reviews the change before T002. |
| The byte totals differ from the source totals (U-5) | Operators compare the wrong numbers | The UI labels the totals as derived from hourly samples (FR-010). The source is not a comparable source for port counters (R-41). |
| Redis writes grow with port count | Redis load rises | The phase is bounded by the request cap. Each port writes at most nine range keys, each with a last-complete value. |

Caution: a request cap above the measured headroom can use the shared hourly limit for each token. The limit resets after one hour.

## Rollback Steps

1. Set `WAN_PORT_INSIGHT_REQUEST_CAP` to zero or remove the key. The worker skips the port series phase at the next refresh.
2. Keep the bulk snapshot. It stays unchanged by the rollback.
3. Revert the merge commit if the browser or contract tests show a defect in the port view.
4. Wait for the stale time to live to pass. The last complete values expire at that time (R-64 and R-65).
5. Confirm that the refresh status route reports the phase as disabled.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `services/__init__.py` is the WAN service module with blob SHA 11fdc93e4740e0a8c083f4f5ed4106448fa42745 (R-08) | The new refresh method extends the existing service | A second service file would create a second cache writer, which the issue forbids |
| `collect_worker_snapshot` starts at line 502 and returns at line 557 (R-62 and R-73), which exceeds the 25-line limit (R-79) | The phase reads the datasets that this method builds | Changing the method signature in this change would widen the change. The remediation runs as a separate action (A-13). |
| `tests/e2e/web_portal/` has 32 direct children (R-80) | The browser tests extend an existing file | A new file in that folder would add a child to a noncompliant parent |
| `changelog.d/` has 335 direct children (R-81) | One fragment is a required process record | No other place accepts a fragment, as the changelog rule requires (R-34) |
