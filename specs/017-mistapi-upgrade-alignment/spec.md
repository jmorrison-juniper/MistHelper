# Feature Specification: Systematic mistapi Upgrade Alignment

**Feature Branch**: `017-mistapi-upgrade-alignment`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Systematically analyze and improve all MistHelper menu options to leverage new features, breaking changes, and improvements from mistapi releases v0.59.1 through v0.61.3. This includes adopting new WebSocket streaming module, device utilities module, search_after pagination, updated SLE endpoints, insights API parameter changes, alarm search enhancements, map stacks API, async helpers, auto-reconnect, bounded message queues, and exception-based error handling replacing sys.exit calls."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Breaking Change Fixes (Priority: P1)

A NOC engineer runs MistHelper menu options that call mistapi API functions whose signatures changed in v0.59.1-v0.61.3. Currently these calls may fail silently, pass incorrect parameters, or produce unexpected errors because the underlying API functions changed parameter names, types, or behavior.

**Why this priority**: Breaking changes cause runtime failures. If MistHelper passes parameters that no longer exist or calls deprecated functions, operations fail for users with no explanation. This must be fixed first.

**Independent Test**: Run `python MistHelper.py --test` with mistapi >= 0.61.3 installed. All safe menu options complete without parameter-mismatch errors or deprecation warnings.

**Acceptance Scenarios**:

1. **Given** mistapi v0.61.3 is installed, **When** user runs Menu 68 (Site Insight Metrics), **Then** `getSiteInsightMetrics()` is called with `metrics` as a query parameter (not a path parameter) per v0.61.2 change, and data exports successfully
2. **Given** mistapi v0.61.3 is installed, **When** user runs Menu 69 (Client Insight Metrics), **Then** `getSiteInsightMetricsForClient()` uses `metrics` query parameter instead of `metric` path parameter
3. **Given** mistapi v0.61.3 is installed, **When** user runs Menu 53 (SLE Insights), **Then** no deprecation warnings appear for `getSiteSleSummary` or `getSiteSleClassifierDetails` (migrated to `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`)
4. **Given** mistapi v0.61.3 is installed, **When** API session initialization encounters an authentication failure, **Then** MistHelper catches `ConnectionError` or `ValueError` exceptions (not `SystemExit`) and displays a clear error message

---

### User Story 2 - Enhanced Alarm and Search Operations (Priority: P2)

A NOC engineer uses Menu 1 (Org Alarms) and wants to leverage new filtering capabilities added in v0.59.5: `group`, `severity`, `ack_admin_name`, and `acked` parameters for `searchOrgAlarms()` and `searchSiteAlarms()`.

**Why this priority**: Alarm triage is a daily NOC task. Enhanced filtering reduces noise and speeds incident response.

**Independent Test**: Run Menu 1 and verify the exported alarm data includes group and severity fields. If the underlying API supports the new parameters, they should be passed through.

**Acceptance Scenarios**:

1. **Given** an organization with active alarms, **When** user runs Menu 1 (Export Org Alarms), **Then** the alarm export includes `group`, `severity`, `ack_admin_name`, and `acked` fields in the output
2. **Given** mistapi v0.61.3 is installed, **When** any search endpoint is paginated, **Then** `search_after` cursor-based pagination is used where available for more efficient large-result-set traversal

---

### User Story 3 - Device Utility Commands Use New mistapi.device_utils Module (Priority: P2)

A NOC engineer uses Menu options 123-157 (Device Utility Commands) which currently call low-level `mistapi.api.v1.sites.devices.*` functions directly. The new `mistapi.device_utils` module (v0.61.0+) provides higher-level wrappers with WebSocket streaming, non-blocking execution, and `UtilResponse` objects.

**Why this priority**: The device_utils module handles WebSocket plumbing automatically, provides structured response objects, and supports non-blocking execution. This improves reliability and reduces custom WebSocket management code.

**Independent Test**: Run each device utility command (Menu 123-157) and verify they produce the same or better output using the new module.

**Acceptance Scenarios**:

1. **Given** a site with an online switch, **When** user runs Menu 130 (Show BGP Summary), **Then** the command uses `mistapi.device_utils.ex.retrieveBgpSummary()` and returns structured data via `UtilResponse`
2. **Given** a site with an online gateway, **When** user runs Menu 123 (Traceroute), **Then** the command uses the appropriate `device_utils` function with non-blocking execution
3. **Given** a site with an online switch, **When** user runs Menu 136 (Monitor Traffic), **Then** the streaming command uses `device_utils.ex.monitorTraffic()` with real-time message delivery

---

### User Story 4 - WebSocket Operations Use New mistapi.websockets Module (Priority: P3)

A NOC engineer uses Menu options 5-8 (WebSocket device commands) and Menu 9-10 (Packet Captures). The current implementation uses raw `websocket.WebSocketApp` connections. The new `mistapi.websockets` module (v0.61.0+) provides auto-reconnect, bounded message queues, thread-safety, and header redaction.

**Why this priority**: WebSocket reliability directly impacts real-time operations. The new module adds auto-reconnect (v0.61.2), bounded queues preventing memory leak (v0.61.3), and thread-safety fixes. This is a robustness improvement.

**Independent Test**: Run Menu 5 (Show MAC Table) and Menu 9 (Packet Capture) and verify WebSocket connections use the new module with configurable reconnect and queue limits.

**Acceptance Scenarios**:

1. **Given** a site with an online switch, **When** user runs Menu 5 (Show MAC Table via WebSocket), **Then** the connection uses `mistapi.websockets` module with `auto_reconnect=True` and `queue_maxsize` configured
2. **Given** a packet capture is started, **When** the WebSocket connection drops transiently, **Then** it auto-reconnects using exponential backoff without user intervention
3. **Given** a high-frequency WebSocket stream, **When** the message buffer fills, **Then** oldest messages are dropped with a warning instead of unbounded memory growth

---

### User Story 5 - New API Endpoints and Parameters Adoption (Priority: P3)

A NOC engineer benefits from new API capabilities added in v0.59.1-v0.61.3: OSPF stats search endpoints, map stacks API, inventory model filtering, port-level insight metrics, and JSI date-based filters.

**Why this priority**: These are incremental improvements that expand MistHelper's data coverage.

**Independent Test**: Verify new endpoints are available via dedicated menu options or enhanced existing exports.

**Acceptance Scenarios**:

1. **Given** an organization with OSPF-configured devices, **When** OSPF stats are queried, **Then** the new `searchOrgOspfStats()` and `searchSiteOspfStats()` endpoints are available
2. **Given** mistapi v0.61.3 is installed, **When** user runs device-level insight metrics (Menu 81), **Then** the optional `port_id` parameter is supported for port-level filtering
3. **Given** a site with maps, **When** map data is exported (Menu 51), **Then** the new map stacks API (`listSiteMapStacks`) data is included alongside existing map data

---

### Edge Cases

- What happens when MistHelper is run with an older mistapi version (< 0.61.0) that doesn't have the new modules? Graceful fallback to legacy API calls with a warning message
- How does the system handle `ConnectionError` or `ValueError` exceptions from the new mistapi error handling (v0.59.5) during session initialization? Clear user-facing error messages with retry guidance
- What happens when `getSiteInsightMetrics()` is called with the old path-parameter style? The function signature changed; the call must be updated to use query parameters
- What happens when a device_utils function is called on a device type it doesn't support (e.g., calling `ex.monitorTraffic` on an AP)? The menu option should only offer commands applicable to the selected device type
- How does the bounded message queue (`queue_maxsize`) interact with long-running packet captures? Messages are dropped with logging when the queue is full; the capture continues

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST update `getSiteInsightMetrics()` calls to use `metrics` as a query parameter instead of a path parameter (v0.61.2 breaking change)
- **FR-002**: System MUST update `getSiteInsightMetricsForClient()` calls to use `metrics` query parameter instead of `metric` path parameter (v0.61.2 breaking change)
- **FR-003**: System MUST migrate deprecated SLE functions to their replacements: `getSiteSleSummary` to `getSiteSleSummaryTrend`, `getSiteSleClassifierDetails` to `getSiteSleClassifierSummaryTrend` (v0.59.2)
- **FR-004**: System MUST handle `ConnectionError` and `ValueError` exceptions from mistapi session initialization instead of relying on `sys.exit()` behavior (v0.59.5 breaking change)
- **FR-005**: System MUST pass new alarm search parameters (`group`, `severity`, `ack_admin_name`, `acked`) to `searchOrgAlarms()` and `searchSiteAlarms()` (v0.59.5)
- **FR-006**: System MUST adopt `search_after` cursor-based pagination where available for large result sets (v0.59.1)
- **FR-007**: System MUST migrate Device Utility Commands (Menu 123-157) to use `mistapi.device_utils` module where applicable (v0.61.0)
- **FR-008**: System MUST migrate WebSocket operations (Menu 5-8, 9-10) to use `mistapi.websockets` module with auto-reconnect and bounded message queues (v0.61.0, v0.61.2, v0.61.3)
- **FR-009**: System MUST update `requirements.txt` to specify `mistapi>=0.61.3` as the minimum version
- **FR-010**: System MUST provide graceful fallback when running with older mistapi versions, logging a clear warning about limited functionality
- **FR-011**: System MUST leverage the new `port_id` parameter for device insight metrics functions (v0.61.3)
- **FR-012**: System MUST adopt the `validate` parameter for `set_api_token()` to allow faster initialization when tokens are known valid (v0.61.0)
- **FR-013**: System MUST update the `searchOrgInventory()` call to support the new `model` parameter for device model filtering (v0.60.4)
- **FR-014**: Each menu option MUST be updated and verified individually with a syntax check and test run between changes (systematic, one-at-a-time approach)

### Key Entities

- **Menu Option**: A numbered operation in MistHelper's CLI menu (1-158) that calls one or more mistapi API functions
- **mistapi Release**: A versioned release of the mistapi SDK (v0.59.1 through v0.61.3) containing new features, breaking changes, or bug fixes
- **API Function Call**: A specific invocation of a mistapi function within MistHelper, identified by module path and parameters
- **Breaking Change**: A mistapi change that alters function signatures, parameter names, or behavior in a way that causes existing calls to fail
- **Enhancement**: A mistapi change that adds new parameters, endpoints, or modules that MistHelper can optionally adopt

## Assumptions

- MistHelper will target mistapi >= 0.61.3 as the minimum supported version going forward
- The systematic update process will proceed menu-by-menu (1, 2, 3, ..., 158) with validation between each
- Device utility commands that currently use low-level `mistapi.api.v1.sites.devices.*` functions will be migrated to `mistapi.device_utils.*` where a corresponding high-level function exists
- WebSocket operations will be migrated incrementally - packet captures and device commands first
- The `search_after` pagination enhancement will be applied to all search endpoints that support it, as a cross-cutting improvement
- Existing CSV/SQLite output format and column names will be preserved for backward compatibility

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 158 menu options complete without deprecation warnings or parameter-mismatch errors when run with mistapi v0.61.3
- **SC-002**: `python MistHelper.py --test` passes all safe menu options (excluding skip list) with zero failures related to API signature changes
- **SC-003**: WebSocket operations reconnect automatically within 30 seconds of a transient connection drop
- **SC-004**: Device utility commands return results within the same or shorter timeframe as the current implementation
- **SC-005**: Memory usage during long-running WebSocket streams remains bounded (queue_maxsize prevents unbounded growth)
- **SC-006**: Each menu option update is committed individually with `python -m py_compile MistHelper.py` validation before merge
