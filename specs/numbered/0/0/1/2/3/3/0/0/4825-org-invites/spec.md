# Feature Specification: Organization Invites Export Reports Missing SDK Call

**Feature Branch**: `4825-org-invites` (git branch `fix/4825-org-invites`)

**Created**: 2026-11-18

**Status**: Local commit ready. Publication pending.

**Input**: User description: "Runtime: missing listOrgInvites SDK method in OrgExportUtils._invites" (GitHub issue #4825)

## Summary

`OrgExportUtils._invites` reads `mistapi.api.v1.orgs.invites.listOrgInvites` directly. The installed mistapi SDK does not provide that function, so the export raises `AttributeError`. This specification defines the behavior when the call is absent. It keeps the supported path unchanged. The work is already committed in commit b2249e25.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export continues when the SDK call is absent (Priority: P1)

An operator runs organization exports. When mistapi lacks the invites list call, the invites export must not stop the other exports. The export logs one clear error and writes no file.

**Why this priority**: The defect raises an unhandled exception in the shared export path. One missing call must not stop other work.

**Independent Test**: Remove the `listOrgInvites` attribute in a unit test, then call `OrgExportUtils._invites()`. The call returns without an exception. It logs one error and starts no fetch.

**Acceptance Scenarios**:

1. **Given** mistapi has no `listOrgInvites` function, **When** `OrgExportUtils._invites()` runs, **Then** it logs one error that names `listOrgInvites` and `OrgInvites.csv`.
2. **Given** mistapi has no `listOrgInvites` function, **When** `OrgExportUtils._invites()` runs, **Then** it raises no exception and starts no fetch.

---

### User Story 2 - Supported path stays unchanged (Priority: P2)

When mistapi provides `listOrgInvites`, the export passes that function to the shared export pipeline. The data type stays `invites`, and the sort key stays `email`.

**Why this priority**: The fix must not change an export that already works.

**Independent Test**: Provide a callable as `listOrgInvites` in a unit test. Confirm that the shared export receives it with `data_type="invites"` and `sort_key="email"`.

**Acceptance Scenarios**:

1. **Given** mistapi provides `listOrgInvites`, **When** `OrgExportUtils._invites()` runs, **Then** the shared export receives that callable, the data type `invites`, and the sort key `email`.

---

### Edge Cases

- What happens when a later mistapi release adds `listOrgInvites`? The supported path runs with no code change.
- What happens when the export has no rows? On the absent path, the export writes no empty file. An empty file reads as zero invites.
- What happens when another SDK function lists invites? The export does not use it unless its contract matches. `listSdkInvites` lists SDK onboarding invites, which is a different resource.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The invites export MUST pass `mistapi.api.v1.orgs.invites.listOrgInvites` to the shared export when that function exists.
- **FR-002**: The invites export MUST log one error when that function is absent. The error MUST name `listOrgInvites` and `OrgInvites.csv`.
- **FR-003**: The invites export MUST NOT raise an exception when that function is absent.
- **FR-004**: The invites export MUST NOT write `OrgInvites.csv` when that function is absent.
- **FR-005**: The invites export MUST NOT substitute another SDK function or a raw endpoint.
- **FR-006**: The supported path MUST keep `data_type="invites"` and `sort_key="email"`.

### Mist Cloud Transport Requirements

- The change adds no mistapi REST method. The supported path passes `listOrgInvites`, which the installed SDK does not provide. The absent path makes no request.
- SDK insufficiency: introspection of `mistapi.api.v1.orgs.invites` lists only `inviteOrgAdmin`, `uninviteOrgAdmin`, and `updateOrgAdminInvite`. The Mist OpenAPI files in `documentation/` define only POST for `/api/v1/orgs/{org_id}/invites`.
- SDK endpoint parity: `listSdkInvites` calls `GET /api/v1/orgs/{org_id}/sdkinvites`. That endpoint lists SDK onboarding invites. It is a different resource, so it is not a substitute.
- SDK authentication: unchanged. The shared export keeps the session that it already uses.
- Failure safety: the absent path logs one error, writes no file, and raises no exception.
- Secret redaction: the log message holds no token, password, or invite content.

### Key Entities

- **Organization invite**: A pending invitation for an organization administrator. The export keys each row by `email`. This change adds no entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The focused test file `tests/unit/export/test_org_export_utils.py` passes all 96 tests.
- **SC-002**: The new absent-path test fails before the fix with `AttributeError`, and passes after the fix.
- **SC-003**: `ruff`, `black`, `py_compile`, `mypy`, `pylint`, `symbol-diff`, and the test-quality gate pass for the changed files.
- **SC-004**: The export test folder, the SDK signature guard, and the markdown link guard pass with no failure.

## Assumptions

- No menu route runs `OrgExportUtils._invites` in this release. The fix changes no operator menu.
- The locked mistapi line is `>=0.64.0,<0.65`. The installed version is 0.64.1.
- A future mistapi release may add `listOrgInvites`. The supported path then needs no change.

## Out of Scope

- Adding a menu route for the invites export.
- Calling `listSdkInvites` or another endpoint for invites.
- Correcting other generated API documentation pages.
