# Feature Specification: Mist-Ops Platform API Endpoint Audit

**Feature Branch**: `011-mist-ops-api-audit`  
**Created**: 2025-07-16  
**Status**: Draft  
**Input**: User description: "Audit and fix all mistapi SDK endpoint usage across the mist-ops-platform codebase — verify module paths, method names, parameter signatures, response handling, and pagination against the actual mistapi Python library."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify All SDK Method Calls Are Valid (Priority: P1)

As a platform operator, every call that mist-ops-platform makes to the Juniper Mist cloud must use a real, existing method from the mistapi Python library so that operations succeed at runtime instead of crashing with AttributeError or ImportError.

**Why this priority**: If SDK method names or module paths are wrong, the entire platform is non-functional — no data sync, no config deployment, no health checks. This is the most critical correctness issue.

**Independent Test**: For each SDK call site in the codebase, confirm the module path resolves to an importable module and the method name exists on that module. A simple import check and `hasattr()` verification delivers immediate value by catching all broken references.

**Acceptance Scenarios**:

1. **Given** the entity endpoint registry maps 14 entity types to SDK modules and methods, **When** each `api_module` + `read_method` and `write_method` combination is checked against the installed mistapi library, **Then** every combination resolves to a callable function with zero ImportError or AttributeError.
2. **Given** the auth service calls a self-identity endpoint with a doubled module segment, **When** the call path is verified against mistapi, **Then** the correct module path is confirmed or corrected.
3. **Given** sync services call `listOrgSites`, `getOrgInventory`, `listOrgAuditLogs`, and `getSiteDeviceStats`, **When** each method name is checked against its respective mistapi module, **Then** every method exists and is callable.
4. **Given** pre-check and post-check services call `getOrgDevice` via `orgs.devices`, **When** the module path `mistapi.api.v1.orgs.devices` is verified, **Then** the module either exists or a corrected path is identified.
5. **Given** 7 bypass calls exist outside the entity registry (5 dynamic `list_entities()` calls in sync/check services + 1 direct SDK call in auth + 1 direct SDK call in status), **When** each bypass call is audited, **Then** new entity types are added to the registry and all bypass calls are refactored to use registered types.

---

### User Story 2 - Fix Method Signature Mismatches (Priority: P1)

As a platform operator, every call site must pass the correct parameters in the correct order so that write operations (config pushes, rollbacks) do not silently fail or corrupt device configurations.

**Why this priority**: Signature mismatches in deployment code (executor, rollback) mean config pushes will crash. This is equally critical to Story 1 because broken deploys risk production outages.

**Independent Test**: Compare each call site's arguments against the actual function signature from the SDK. Every mismatch is documented and corrected. Can be tested by extracting function signatures via `inspect.signature()` and comparing against call-site argument lists.

**Acceptance Scenarios**:

1. **Given** the config push executor calls `write_entity()` passing `api_module` and `write_method` as keyword arguments, **When** the actual `MistEndpointService.write_entity()` signature is checked, **Then** the call is corrected to pass `entity_type` as the first positional argument per the method's actual interface.
2. **Given** the rollback service calls `read_entity()` with `api_module` and `read_method` keyword arguments, **When** the actual method signature is verified, **Then** the call is corrected to use `entity_type` and `ids` parameters.
3. **Given** SDK methods require specific parameter ordering (session, org_id/site_id, then entity-specific ids), **When** each call site is audited, **Then** all parameters are passed in the correct order.

---

### User Story 3 - Fix Response Handling Inconsistencies (Priority: P2)

As a platform operator, the system must correctly interpret API responses so that success/failure states are accurately detected, preventing silent data loss or false-positive deployment confirmations.

**Why this priority**: If the system checks for `.success` on a result object that only has `.status_code` and `.data`, every conditional branch based on success/failure is broken. This affects reliability but the platform may still partially function.

**Independent Test**: Search for all usages of the `ApiResult` dataclass and verify that code only accesses attributes that exist on the dataclass. Can be verified by tracing all attribute accesses on `ApiResult` instances.

**Acceptance Scenarios**:

1. **Given** the `ApiResult` dataclass defines only `status_code` and `data` attributes, **When** derived `.success` and `.error` properties are added to the dataclass, **Then** all existing consumer code that references these attributes becomes valid without per-file rewrites.
2. **Given** the executor checks `result.success` after a write operation, **When** the ApiResult `.success` property returns True for 2xx status codes, **Then** success detection works correctly via the derived property.
3. **Given** the rollback service references `result.error` and `result.success`, **When** the ApiResult `.error` property extracts error details from `data` on non-2xx responses, **Then** error information is available to consumers through the standard interface.

---

### User Story 4 - Add Pagination for List Operations (Priority: P2)

As a platform operator, list operations that retrieve sites, devices, events, and inventory must handle pagination so that organizations with hundreds or thousands of items receive complete data sets, not just the first page.

**Why this priority**: Missing pagination causes silent data truncation. The system appears to work but returns incomplete results, leading to missing devices in inventory, missed events, and incomplete site lists.

**Independent Test**: Verify that every list/search operation in sync services checks for and follows pagination markers from the SDK response. Can be tested with a mock returning multi-page results.

**Acceptance Scenarios**:

1. **Given** `listOrgSites` returns paginated results for orgs with more than the default page size, **When** the inventory sync service calls this method, **Then** all pages are fetched and combined.
2. **Given** `listOrgAuditLogs` returns paginated event data, **When** the event sync service ingests logs, **Then** pagination is followed until all events in the requested time window are retrieved.
3. **Given** `getOrgInventory` may return paginated device lists, **When** the inventory sync pulls the full inventory, **Then** all devices across all pages are captured.

---

### User Story 5 - Cross-Reference Internal Method Calls (Priority: P3)

As a platform operator, internal service-to-service method calls (not SDK calls) must use correct method names so that the drift scanner, diff service, and other internal components work together without runtime errors.

**Why this priority**: Internal method name mismatches (like calling `compute()` when the method is named `compute_diff()`) cause runtime crashes in specific workflows. Lower priority because it affects fewer code paths than SDK issues.

**Independent Test**: For every cross-service method call, verify the called method exists on the target class. Can be tested with static analysis or simple attribute checks.

**Acceptance Scenarios**:

1. **Given** the drift scanner calls `self._diff.compute()`, **When** the DiffService class is inspected, **Then** the call is corrected to use the actual method name `compute_diff()`.
2. **Given** the firmware orchestrator builds payloads but never calls a Mist API for the actual upgrade, **When** the firmware workflow is audited, **Then** the correct SDK method for triggering firmware upgrades is identified, added to the entity registry, and implemented in the orchestrator.

---

### Edge Cases

- What happens when the mistapi SDK version is upgraded and method names change? The entity registry targets a single SDK version. Version upgrades are handled by updating registry entries directly — no version-aware dispatch mechanism is needed.
- How does the system handle SDK methods that exist but have been deprecated? Deprecated methods should be replaced with their recommended successors.
- What happens when an SDK method returns an unexpected response structure (e.g., raw dict vs. wrapped object)? Response handling must be resilient to both SDK response formats.
- How does the system behave when a previously valid module path is reorganized in a new SDK release? Import errors should be caught gracefully with clear diagnostic logging.

## Clarifications

### Session 2026-03-08

- Q: Should ApiResult be expanded with derived properties (.success, .error) or should all consumers be rewritten to check status_code directly? → A: Expand ApiResult with derived properties
- Q: Should the firmware orchestrator's missing SDK call be implemented in this audit or documented for a separate feature? → A: Fix in this audit — implement the actual firmware upgrade SDK call
- Q: Should all SDK calls (including auth/self-identity and utility calls) be forced through the entity registry, or are exceptions allowed? → A: All through registry — every SDK call must use registered entity types, no bypass calls
- Q: Should the entity registry support version-aware method resolution for different mistapi SDK versions, or target a single version? → A: Single version — target current SDK version only; upgrades handled by updating registry entries directly

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every entry in the entity endpoint registry MUST map to a valid, importable mistapi module and an existing callable method on that module.
- **FR-002**: All call sites that invoke `MistEndpointService.read_entity()` and `write_entity()` MUST pass arguments matching the actual method signature (entity_type, ids, body).
- **FR-003**: The `ApiResult` dataclass MUST be expanded with derived `.success` and `.error` properties (computed from `status_code` and `data`) so that existing consumer code referencing these attributes becomes valid without rewriting every call site.
- **FR-004**: The auth service's SDK call path MUST resolve to the correct mistapi module for the self-identity endpoint, without duplicated path segments.
- **FR-005**: All list/search operations in sync services MUST handle paginated SDK responses, retrieving all pages before processing.
- **FR-006**: All internal cross-service method calls MUST use method names that exist on the target class.
- **FR-007**: The entity endpoint registry MUST cover all entity types used anywhere in the codebase — no SDK calls may bypass the registry. All 7 existing bypass calls (5 dynamic `list_entities()` calls in sync/check services + 1 direct SDK call in auth + 1 direct SDK call in status) MUST be refactored to use registered entity types.
- **FR-008**: The firmware orchestrator MUST include the actual SDK call to trigger firmware upgrades on devices, not just build payloads.
- **FR-009**: Every SDK method call MUST pass the API session and scope IDs (org_id, site_id) in the order the SDK method expects.
- **FR-010**: All corrected call sites MUST be covered by tests that verify the SDK method is called with correct arguments.

### Key Entities

- **Entity Endpoint Mapping**: The central registry that routes entity type names to SDK module paths and method names. Key attributes: entity type, API module path, read method, write method, required ID parameters.
- **API Result**: The standard response wrapper returned by the endpoint service after SDK calls. Key attributes: HTTP status code, response data payload, derived `.success` property (True for 2xx), derived `.error` property (error details from data on non-2xx).
- **Sync Service**: Background workers that pull data from Mist cloud into the local database. Each sync service targets specific SDK endpoints for sites, devices, configs, events, and status.
- **Deploy Service**: Background workers that push configuration changes to Mist cloud. Each deploy service uses write endpoints from the registry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of SDK module paths in the entity registry resolve to importable modules when verified against the installed mistapi library.
- **SC-002**: 100% of SDK method names in the entity registry exist as callable functions on their respective modules.
- **SC-003**: Zero runtime errors occur when exercising every registered entity type's read and write operations end-to-end.
- **SC-004**: All call sites pass arguments in the correct order and with correct names, verified by comparing call-site argument lists against SDK function signatures — 0 mismatches remaining.
- **SC-005**: The ApiResult dataclass provides `.success` and `.error` derived properties, and all consumer code accesses these attributes without error.
- **SC-006**: List operations return complete data sets: a test with a mock returning 3 pages of results retrieves all 3 pages' worth of items.
- **SC-007**: Every audited file has at least one corresponding test that exercises the corrected SDK interaction.

## Assumptions

- The mistapi Python library version 0.60+ is the sole target SDK version for verification. The registry does not support version-aware method resolution; when the SDK is upgraded, registry entries are updated directly to match the new version.
- The `ENTITY_ENDPOINT_MAP` in `src/shared/mist/types.py` is the single source of truth for all SDK method routing. All SDK calls — including auth/self-identity and utility calls — must go through the registry. No exceptions are permitted.
- The `ApiResult` dataclass is the only response wrapper used by `MistEndpointService`. If other response types exist, they are out of scope for this audit.
- Pagination handling follows the mistapi SDK's built-in pagination patterns (next-page tokens or limit/offset). The specific pagination mechanism will be determined during implementation.
- The firmware upgrade SDK call gap (Story 5) requires API research to identify the correct mistapi method. The implementation will be completed within this audit scope, including adding the method to the entity registry and wiring it into the firmware orchestrator.
