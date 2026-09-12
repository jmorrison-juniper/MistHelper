# Feature Specification: Mist API Read Operation -- optimizeInstallerRrm

**Feature Branch**: `858-mist-optimize-installer-rrm`
**Created**: 2026-06-29
**Status**: Deliberately excluded from safe endpoint families
**Input**: User description: "Catalog the missing Mist API GET endpoint `optimizeInstallerRrm` and add it as a new MistHelper menu item."

## Source Endpoint

- **operationId**: `optimizeInstallerRrm`
- **Method**: `GET`
- **Path**: `/api/v1/installer/sites/{site_name}/optimize`
- **Tag**: `Installer`
- **mistapi SDK module**: `mistapi.api.v1.installer.sites.optimize`

### Decision

This endpoint starts radio optimization on a live site.
MistHelper must not add it to a safe export family.
Add it only as a destructive action with typed confirmation.
Issue #1366 is closed as out of scope for the read-only backlog.
A guard test prevents this operation from entering the safe family tables.

### Description

After installation is considered complete (APs are placed on maps, all powered up), you can trigger an optimize operation where RRM will kick in (and maybe other things in the future) before it’s automatically scheduled.

### Path Parameters

- `site_name` (required)

### Query Parameters

_None._

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliberate safe-family exclusion (Priority: P1)

A junior NOC engineer reads this specification.
The engineer sees that `optimizeInstallerRrm` is not a safe export.

**Why this priority**: A GET method can still change the network. This call starts radio optimization.

**Independent Test**: Run the safe-family guard test. Verify that `optimizeInstallerRrm` is absent.

**Acceptance Scenarios**:

1. **Given** the safe endpoint family tables, **When** the guard test runs, **Then** it rejects `optimizeInstallerRrm`.
2. **Given** a future implementation, **When** it adds a menu item, **Then** the menu item must be `destructive`.
3. **Given** a future implementation, **When** it calls the SDK, **Then** it must require typed confirmation.

### Edge Cases

- Do not classify this endpoint by method alone.
- Do not export the response through a read-only family.
- Do not run this endpoint during unattended tests.

## Requirements *(mandatory)*

**FR-001**: Do not add `optimizeInstallerRrm` to a safe export family.
**FR-002**: Collect required inputs using `safe_input()` so the operation works in SSH and container contexts.
**FR-003**: Apply rate limiting and retry logic consistent with adjacent menu items (delay_metrics.json + tuning_data.json).
**FR-004**: If implemented later, classify the menu action as `destructive`.
**FR-005**: If implemented later, require typed confirmation before the API call.
**FR-006**: Log `INFO` before the API call and `DEBUG` with response counts after, ASCII-only, per Action Logging principle.
**FR-007**: Add inline comments on every new executable line per Inline Comments principle.
**FR-008**: Keep a guard test that excludes this operation from safe family tables.

## Constitution & Instructions Conformance

- Inline comments on every executable line (Constitution VI -- NON-NEGOTIABLE).
- Action logging before/after every meaningful step (Constitution VII -- NON-NEGOTIABLE).
- 5-Item Rule: implementation function <=25 lines, <=5 params, <=5 nesting blocks.
- ASCII-only logging (no Unicode/emoji).
- A guard test prevents safe-family inclusion.
- A later implementation must use destructive confirmation.

## Non-Functional Requirements

- **Performance**: Single-page request <=5s; full paginated retrieval bounded by Mist API rate limits.
- **Security**: API token loaded from `.env`; never logged.
- **Compatibility**: Python 3.13+, mistapi 0.59+, runs in Podman container and on bare Windows venv.

## Out of Scope

- Write operations against the same path (POST/PUT/PATCH/DELETE) -- separate spec when needed.
- UI changes beyond the new menu item label.
- Database schema migrations beyond the new primary-key strategy entry.

## Acceptance Criteria Checklist

- [ ] `optimizeInstallerRrm` is absent from safe family tables.
- [ ] The guard test fails if a safe family adds this operation.
- [ ] This issue records the destructive-action decision.
