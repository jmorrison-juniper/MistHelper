# Security Checklist: Read-only Mist target discovery

**Purpose**: Confirm that the discovery design keeps credentials, customer data, and cloud state safe.
**Created**: 2026-11-26
**Feature**: `spec.md`, `plan.md`, `design/contracts/`

## Credentials

- [x] The client reads the operator session through `identity.current_session()` only (FR-007).
- [x] The client creates no credential, no token reader, and no environment variable read (plan, Architecture).
- [x] No token value appears in a contract, a task, or the record. The record names no credential value.
- [x] Test TC-19 searches each response body and each captured log line for the synthetic token value (FR-016).

## Cloud State

- [x] The client calls `getSelf`, `listOrgSites`, `getOrgInventory`, and `mistapi.get_next` only (FR-005).
- [x] No write function appears in the client, and TC-02 fails when a write call appears (FR-006).
- [x] The preview path does not call the discovery client (TC-21, plan, Architecture).
- [x] No site, gateway, or other object is created during a check (FR-006).

## Input Handling

- [x] `org_id` accepts a UUID only. An invalid value returns HTTP 400 before any SDK call (FR-018, TC-18).
- [x] The route accepts no file name, path, or free text that reaches Mist (contract `discovery-http.md`).

## Logging and Responses

- [x] Logs carry state codes and counts only (FR-016, contract `discovery-http.md`, Logging section).
- [x] Responses carry no authorization header, cookie, or source configuration (FR-016).
- [x] Each discovery response carries `Cache-Control: no-store` (FR-019, TC-20).
- [x] Log output uses ASCII only (constitution Principle V, research R35).

## Browser Storage

- [x] The page stores no value in browser storage (FR-007, contract `ui.md`, Browser Storage).

## Tests

- [x] Tests use mocked SDK responses and synthetic identities (FR-020).
- [x] Each test run opens no network socket (TC-02, SC-004).
- [x] No production credential appears in a test (plan, Constitution Check, rule III).
