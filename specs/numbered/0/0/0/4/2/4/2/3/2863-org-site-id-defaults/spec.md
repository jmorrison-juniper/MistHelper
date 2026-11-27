# Feature Specification: Organization and site identifier defaults

**Feature Branch**: `fix/2863-tenant-identifier-validation` (first batch only)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #2863, "chore: audit org and site ID defaults that mask missing inputs". Issue #2753 triaged the visible inventory and deferred organization and site identifier defaults to this issue. Each repair must fail visibly at the missing identifier.

## Clarifications

### Session 2026-11-26

- Q: Does the first batch close issue #2863? -> A: No. The owner states that the audit stays open. The pull request body uses `Part of #2863`. Sources: issue comments of 2026-10-01 and 2026-10-21.
- Q: What does an empty optional site identifier mean? -> A: It is a refusal, not organization-only scope. Only `None` selects organization-only scope. Sources: comment of 2026-10-21 and `src/mist/access/api/tenant_fetch.py:156`, which treats an empty value as organization-only today.
- Q: Does a valid identifier need a UUID format check? -> A: No. The owner requires opaque valid identifiers, such as `org-1`, to pass unchanged. The OpenAPI file declares `format: uuid`, but the existing tests use opaque values.
- Q: Which file owns the tenant boundary now? -> A: `src/mist/access/api/tenant_fetch.py`. The reserved path `api/tenant_fetch.py` (retired src root) does not exist on main.
- Q: Which menu runs the SSID site-variable writes? -> A: Menu 145, category `interactive`. The comment of 2026-10-06 names menu 159, which the registry lists as "Bounce port".
- Q: Are gateway reboot and virtual chassis conversion destructive? -> A: Yes. Registry entries 158, 161, and 162 use category `destructive`. The comment of 2026-10-06 says otherwise, and that statement is stale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Refuse a missing required identifier (Priority: P1)

An operator starts a discovery that needs an organization or site identifier. The tool stops before any Mist SDK call when that identifier is missing. The operator sees the field name.

**Why this priority**: An empty tenant result hides the missing input. The operator then reads a false "no tenants" result.

**Independent Test**: Call each tenant discovery method with each invalid identifier. Assert one `ValueError` that names the field, and zero SDK calls.

**Acceptance Scenarios**:

1. **Given** an organization resolver that returns an empty string, **When** organization tenant discovery runs, **Then** it raises `ValueError` with `org_id` and makes no SDK call.
2. **Given** an empty site identifier, **When** site tenant discovery runs, **Then** it raises `ValueError` with `site_id` and makes no SDK call.
3. **Given** a supplied optional site identifier that is blank, **When** policy or template discovery runs, **Then** it raises before the organization SDK call.
4. **Given** an invalid identifier with sensitive private text, **When** the refusal occurs, **Then** the message and log contain no input value.

---

### User Story 2 - Keep valid tenant discovery unchanged (Priority: P1)

An operator runs discovery with valid identifiers or with organization-only scope. The results match the existing results.

**Why this priority**: Organization-only discovery is intentional when no site applies. The fix must not block valid work.

**Independent Test**: Assert the exact SDK arguments and the exact sorted results for valid organization, site, and combined calls.

**Acceptance Scenarios**:

1. **Given** `site_id=None`, **When** policy or template discovery runs, **Then** only the organization SDK call runs.
2. **Given** valid identifiers `org-1` and `site-1`, **When** combined discovery runs, **Then** the sorted and unique tenant union returns.
3. **Given** an HTTP error, a parse failure, or a transport error, **When** discovery runs, **Then** the existing empty result returns.
4. **Given** a resolver that raises an unexpected error, **When** discovery runs, **Then** the original error propagates.

---

### User Story 3 - Block new masking defaults (Priority: P2)

A maintainer changes production code. A ratchet guard fails when a new masking default appears in tracked production Python.

**Why this priority**: The audit covers many occurrences. A guard stops the count from growing while repairs continue.

**Independent Test**: Run the guard on a fixture with one new masking default. The guard fails. Run it on an empty scope. The guard fails.

**Acceptance Scenarios**:

1. **Given** a new `.get("site_id", "")` default in production code, **When** the guard runs, **Then** it fails and names the file.
2. **Given** zero tracked production files in scope, **When** the guard runs, **Then** it fails with zero scanned files.

---

### User Story 4 - Refuse missing identifiers before state changes (Priority: P2)

An operator runs a state-changing workflow. A missing site identifier stops the step before the write or restart call.

**Why this priority**: A blank scope can send a change to the wrong scope or to an invalid scope.

**Independent Test**: Call each repaired write path with a missing site identifier. Assert zero write calls and one visible refusal.

**Acceptance Scenarios**:

1. **Given** a site-variable row with an empty site identifier, **When** the SSID phase 2 write runs, **Then** no site write call runs for that row.
2. **Given** a virtual chassis row with an empty site identifier, **When** the conversion runs, **Then** no convert call runs.
3. **Given** a gateway reboot target with an empty site identifier, **When** the reboot runs, **Then** no restart call runs.

---

### Edge Cases

- A resolver returns `None`, an empty string, a whitespace-only string, or a non-string value.
- A site identifier is `None` in one call and an empty string in another call. The two calls have different meanings.
- A valid opaque identifier, such as `org-1`, has no UUID format. The validator accepts it.
- A private value has a `__str__` method that returns sensitive text. The refusal must not print that text.
- A per-record tenant name is missing. This is an optional payload field, and it keeps the existing collection rule.
- The diagnostic label `tmpl.get("name", "unnamed")` keeps its existing behavior.
- Service ping discovery receives a refusal. The manager prints the refusal as a workflow error.
- A batch repair changes a destructive path. That batch needs human review before merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Required organization identifiers must pass validation before each organization SDK call in tenant discovery.
- **FR-002**: Required site identifiers must pass validation before each site SDK call in tenant discovery.
- **FR-003**: Organization-only policy and template discovery must run only when the optional site identifier is `None`.
- **FR-004**: An empty, whitespace-only, or non-string site identifier must cause zero SDK calls, including the organization call.
- **FR-005**: Each refusal must raise `ValueError` with a message that names `org_id` or `site_id` and no input value.
- **FR-006**: Each refusal must write one error log record that names the field and no input value.
- **FR-007**: Valid identifiers must reach the SDK call unchanged.
- **FR-008**: Valid tenant results must keep their deduplication, sorting, and unknown-record handling.
- **FR-009**: HTTP error, parse-failure, and transport-error results must keep their existing empty results.
- **FR-010**: Unexpected resolver exceptions must propagate unchanged.
- **FR-011**: Service ping discovery must show a refusal as a workflow error, not as an empty tenant source.
- **FR-012**: The first batch must add no direct child to `src/mist/access/api/` and no file under `tests/guardrails/`.
- **FR-013**: The first batch must add one release-note fragment under `changelog.d/`.
- **FR-014**: The masking-default audit must use one counted rule over tracked non-test Python files at the implementation revision.
- **FR-015**: The ratchet guard must fail on each new masking default. It must reject a zero-file scope and a zero-parse scope.
- **FR-016**: Each state-changing repair must refuse a missing site identifier before its write or restart call.

### Key Entities

- **Required identifier**: A string with at least one non-whitespace character. Organization and site identifiers use this form.
- **Optional site identifier**: `None` for organization-only scope, or a required site identifier.
- **Refusal**: A `ValueError` with the field name and one error log record. It occurs before any SDK call.
- **Masking default**: A source default that turns a missing identifier into an empty or organization-only scope.
- **Baseline entry**: A normalized repository path and a positive count of accepted masking defaults.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every invalid required-identifier case makes zero SDK calls.
- **SC-002**: Every refusal raises exactly one named `ValueError` and writes exactly one error log record.
- **SC-003**: Every organization-only call makes zero site SDK calls.
- **SC-004**: Every valid call keeps its exact SDK arguments and its exact sorted results.
- **SC-005**: The changed tenant module reaches 90 percent branch coverage in its focused tests.
- **SC-006**: Existing tenant, response-integrity, and discovery tests pass without modification.
- **SC-007**: The masking-default count and its rule are recorded before the ratchet guard merges.

## Out of Scope

- A UUID format check for organization or site identifiers.
- Credential and environment defaults. These belong to issue #2861. The list includes `scripts/probe_pk_strategy.py`.
- Upgrade input defaults outside the organization and site identifier rule. These belong to issue #2862.
- General display, record-shape, and optional lookup defaults. These belong to issue #2753.
- Splitting the existing `APITenantFetchUtils` class. This is a separate remediation.
- Changing the menu category of any operation.
- Closing issue #2863 in the first batch.

## Assumptions

- The resolver `get_cached_or_prompted_org_id` returns a non-empty string or stops the process. Source: `src/foundation/runtime/config/config_utils.py:181-200`.
- Tests use mocked SDK responses. No test calls the live Mist cloud.
- The repository interpreter is Python 3.15.2. The installed `mistapi` package is version 0.64.1.
- The parent grants publication after queue position 30. The owner comment places this slice at queue position 31, after issue #2977.
- The issue keeps the `needs-human-review` label until a human removes it.
- The owner approved the first batch behavior on 2026-10-21.
