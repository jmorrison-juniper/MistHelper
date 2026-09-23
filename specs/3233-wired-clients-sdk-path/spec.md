# Feature Specification: Wired clients in the client pick list

**Feature Branch**: `fix/wired-clients-sdk-path` | **Created**: 2026-09-23 | **Status**: Implemented

**Input**: Issue #3233. "Client pick lists drop every wired client, because the route calls a missing SDK function."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The client list holds the wired clients (Priority: P1)

A NOC engineer opens a row that asks for a client at a site with wired clients. The list shows both the wireless and the wired clients.

**Acceptance Scenarios**:

1. **Given** a site with wired clients, **When** the client list loads, **Then** it holds each wired client.
2. **Given** a future SDK release moves a portal SDK function, **When** the unit tests run, **Then** a test names the call that no longer resolves.

## Requirements *(mandatory)*

- **FR-001**: `_fetch_wired_clients()` MUST call `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients`.
- **FR-002**: A guard MUST resolve every `mistapi.api...` call in `web_portal/` against the installed SDK.
- **FR-003**: A known drift MAY be exempt only with an issue number, and the exemption MUST end when the call resolves.
