# Feature Specification: Organization Invites Export Handles a Missing mistapi Function

**Feature Branch**: `4825-org-invites` (record slug). The follow-up branch is `fix/4825-org-invites-followup`.

**Created**: 2026-11-26

**Status**: Complete as a specification. The guard is on GitHub main from pull request #4829. The follow-up change is open.

**Input**: User description: "Runtime: missing listOrgInvites SDK method in OrgExportUtils._invites" (GitHub issue #4825)

## Summary

`OrgExportUtils._invites` reads `mistapi.api.v1.orgs.invites.listOrgInvites` directly. The pinned mistapi release has no such function. The export raises `AttributeError` when it runs.

Pull request #4829 added a guard. The guard logs one error and skips the export. This record checks the guard on GitHub main. It also lists the defects that remain. No supported Mist API endpoint lists organization admin invites.

## Clarifications

### Session 2026-11-26

- Q: Does a supported Mist API endpoint list organization admin invites? A: No. The four local OpenAPI files define POST only for the invites path.
- Q: Does a supported mistapi function list organization admin invites? A: No. The pinned release and upstream tags v0.62.0 through v0.64.2 define none.
- Q: Does the mistapi pin need a change? A: No. Upstream v0.64.2 has the same invites module as v0.64.1.
- Q: What does the export do when the function is absent? A: It logs one error and writes no file. An empty file would read as zero invites.
- Q: Does the absent path use a substitute function? A: No. Other list functions read other resources.
- Q: Does a menu run the invites export? A: No. No caller of `_invites` exists on GitHub main.
- Q: Does the follow-up pull request close issue #4825? A: Yes. Its body uses `Closes #4825`. Pull request #4829 used `Refs #4825`, so the issue stayed open.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export continues when the mistapi function is absent (Priority: P1)

An operator runs organization exports. The pinned mistapi release lacks the invites list function. The invites export logs one error, writes no file, and raises no exception. The other organization exports continue.

**Why this priority**: The defect stopped the shared export path with an unhandled exception. One missing function must not stop other work.

**Independent Test**: Remove the `listOrgInvites` attribute in a unit test. Call `OrgExportUtils._invites()`. The call returns with no exception. It logs one error and starts no fetch.

**Acceptance Scenarios**:

1. **Given** mistapi has no `listOrgInvites` function, **When** `OrgExportUtils._invites()` runs, **Then** it logs exactly one ERROR record. The record names `listOrgInvites` and `OrgInvites.csv`.
2. **Given** mistapi has no `listOrgInvites` function, **When** `OrgExportUtils._invites()` runs, **Then** it raises no exception, calls no Mist API endpoint, and calls no shared export.

---

### User Story 2 - Supported path stays unchanged (Priority: P2)

When mistapi provides `listOrgInvites`, the export passes that function to the shared export. The data type stays `invites`. The sort key stays `email`.

**Why this priority**: The fix must not change an export that works. A later mistapi release can add the function.

**Independent Test**: Provide a callable as `listOrgInvites`. Confirm that the shared export receives the callable, the data type `invites`, and the sort key `email`.

**Acceptance Scenarios**:

1. **Given** mistapi provides `listOrgInvites`, **When** `OrgExportUtils._invites()` runs, **Then** the shared export receives that callable, `data_type="invites"`, and `sort_key="email"`.

---

### User Story 3 - Maintainer reads correct invite API pages (Priority: P3)

A maintainer reads the organization invite pages in `documentation/api/orgs/`. The Related Endpoints section must not name a list endpoint for organization invites.

**Why this priority**: A wrong link sends the reader to a page that does not exist. It repeats the assumption behind issue #4825.

**Independent Test**: Search the three organization invite pages for `GET_orgs_org_id_invites.md`. The search finds no match.

**Acceptance Scenarios**:

1. **Given** the three organization invite pages, **When** a reader opens the Related Endpoints section, **Then** no entry names a list of organization invites.

---

### User Story 4 - Touched code meets the logging and comment rules (Priority: P2)

A maintainer changes `OrgExportUtils._invites`. The function logs before and after the shared export call. Each changed line and each adjacent uncommented line carries a reason. The return type is declared.

**Why this priority**: The constitution makes logging and inline comments mandatory for each touched function. Pull request #4829 touched `_invites` and left these gaps.

**Independent Test**: Run the focused test file. The log-order test fails when the new log lines are removed.

**Acceptance Scenarios**:

1. **Given** `_invites` runs, **When** it calls the shared export, **Then** an INFO record comes before the call and a DEBUG record comes after it.
2. **Given** `_invites`, **When** a maintainer reads a changed line, **Then** the line has an inline comment that gives its reason.

---

### Edge Cases

- A later mistapi release adds `listOrgInvites`. The supported path runs with no code change. The write then uses the default primary key strategy. See analysis item A-3.
- A later mistapi release renames the function. The guard logs one error and skips the export. The export does not follow the new name.
- A later mistapi release adds `listOrgInvites` with another signature. The shared export calls it with its usual arguments. That contract is unverified.
- No caller reaches `_invites` on GitHub main. A runtime error in this method has no operator impact today.
- The generator in `scripts/generate_api_docs.py` runs again. It skips a page that has no placeholder text, so the corrected pages keep their text.
- A related list names `listSdkInvites` or `listOrgMarvisClientInvites`. Those entries stay valid, because each names a real GET endpoint.

## Requirements *(mandatory)*

### Functional Requirements

Supported and absent paths:

- **FR-001**: The invites export MUST pass `mistapi.api.v1.orgs.invites.listOrgInvites` to the shared export when that function exists.
- **FR-002**: The invites export MUST log exactly one ERROR record when that function is absent. The record MUST name `listOrgInvites` and `OrgInvites.csv`.
- **FR-003**: The invites export MUST NOT raise an exception when that function is absent.
- **FR-004**: The invites export MUST NOT write `OrgInvites.csv` and MUST NOT call the Mist API when that function is absent.
- **FR-005**: The invites export MUST NOT use another mistapi function or a raw HTTP request as a substitute.
- **FR-006**: The supported path MUST keep `data_type="invites"` and `sort_key="email"`.

Logging, comments, and typing:

- **FR-007**: The invites export MUST log one INFO record before the shared export call. It MUST log one DEBUG record after the call returns.
- **FR-008**: Each changed line and each adjacent uncommented line in `_invites` MUST carry an inline comment that gives its reason.
- **FR-009**: The invites export MUST declare the return type `None`.

Documentation:

- **FR-010**: The three organization invite API pages MUST NOT name a list endpoint for organization invites.

Tests:

- **FR-011**: The absent-path test MUST assert exactly one ERROR record and no call to the shared export.

### Mist Cloud Transport Requirements

- The change adds no mistapi REST method. The supported path passes the function `listOrgInvites`. The installed mistapi release does not define it.
- SDK insufficiency: `mistapi.api.v1.orgs.invites` defines `inviteOrgAdmin`, `uninviteOrgAdmin`, and `updateOrgAdminInvite` only. The four local OpenAPI files define POST only for `/api/v1/orgs/{org_id}/invites`.
- SDK endpoint parity: `listSdkInvites` calls GET `/api/v1/orgs/{org_id}/sdkinvites`. That endpoint lists SDK onboarding invites. It is a different resource, so it is not a substitute.
- SDK authentication: unchanged. The shared export keeps the session that it uses today.
- Failure safety: the absent path logs one error, writes no file, and raises no exception.
- Secret redaction: the error text is a constant string. It holds no token, password, or invite content.

### Key Entities

- **Organization invite**: A pending invitation for an organization administrator. The export keys each row by `email`. This change adds no entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All tests in `tests/unit/export/test_org_export_utils.py` pass after the follow-up change.
- **SC-002**: The absent-path test fails when the guard lines are removed. It passes when the guard lines are present.
- **SC-003**: Each gate in task T-LOCAL-GATES returns its expected result.
- **SC-004**: No organization invite page on GitHub main names `GET_orgs_org_id_invites.md`.
- **SC-005**: The follow-up pull request merges with `Closes #4825`, and issue #4825 closes.

## Assumptions

- `pyproject.toml` on GitHub main pins `mistapi>=0.64.1,<0.65`. `requirements.txt` pins `mistapi==0.64.1`.
- The local OpenAPI files in `documentation/` define the Mist API contract for this repository. No live Mist API request was made for this record.
- The local `.venv` holds mistapi 0.64.1. Its `orgs/invites.py` matches the upstream blob for v0.64.1.
- Gates run on Windows 11. The commands for macOS and Linux differ only in the interpreter path.

## Out of Scope

- A menu or CLI option for the invites export.
- A call to `listSdkInvites`, `listOrgMarvisClientInvites`, `listOrgAdmins`, or a raw endpoint for invites.
- A change to the mistapi pin.
- Removal of the `# type: ignore[no-untyped-call]` comments. Other export calls in `org_export_utils.py` use them too. A follow-up issue tracks them.
- Correction of the mislabeled link in `documentation/api/orgs/DELETE_orgs_org_id_admins_admin_id.md`.
- Correction of the mistapi version text in `.github/copilot-instructions.md` and `.specify/memory/constitution.md`.
- Edits to historical records, including `specs/009-api-docs-enrichment/research.md`.
- A primary key strategy for `listOrgInvites`. The Mist OpenAPI files define no list response for organization invites.
