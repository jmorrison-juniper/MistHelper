# Feature Specification: Tenant identifier validation

**Feature Branch**: `jmorrison-juniper-tenant-identifier-validation`

**Created**: 2026-10-01

**Status**: The local validation passed. Publication awaits the parent grant.

**Input**: Repair one proven identifier failure in
[issue #2863](https://github.com/jmorrison-juniper/MistHelper/issues/2863).
The audit records 102 historical candidates. This specification covers tenant
discovery only. It does not complete or close the audit.

## User Scenarios & Testing

### User Story 1 - Refuse a missing required identifier (Priority: P1)

An operator must see a missing organization or site identifier before tenant
discovery contacts the cloud.

**Why this priority**: An empty tenant result can hide a missing required input.

**Independent Test**: Call each affected tenant method with an invalid required
identifier. Assert a named error, one refusal, and zero SDK calls.

**Acceptance Scenarios**:

1. **Given** an invalid organization identifier, **when** organization tenant
   discovery runs, **then** it raises a named error before any SDK call.
2. **Given** an invalid required site identifier, **when** site tenant discovery
   runs, **then** it raises a named error before any SDK call.
3. **Given** an invalid supplied optional site identifier, **when** policy or
   template tenant discovery runs, **then** it refuses before any SDK call.
4. **Given** an invalid identifier with private metadata, **when** discovery
   refuses it, **then** the error and logs contain no input value.

### User Story 2 - Preserve valid tenant discovery (Priority: P2)

An operator can continue to use organization-only discovery and combined
organization and site discovery.

**Why this priority**: Optional site scope is intentional, not a missing-input
failure.

**Independent Test**: Assert exact SDK arguments and exact tenant results for
valid organization, site, and combined calls.

**Acceptance Scenarios**:

1. **Given** no optional site identifier, **when** policy or template discovery
   runs, **then** it calls only the organization endpoint.
2. **Given** valid organization and site identifiers, **when** combined
   discovery runs, **then** it returns the sorted tenant union.
3. **Given** a valid empty cloud response, **when** discovery runs, **then**
   it preserves the existing empty result.
4. **Given** an unexpected resolver error, **when** discovery runs, **then**
   the original error propagates.

### Edge Cases

- Required identifiers reject `None`, empty strings, whitespace-only strings,
  and non-string values.
- Valid opaque identifiers remain valid. No UUID format check applies.
- Validation checks whitespace without changing a valid identifier.
- Only `None` selects organization-only policy or template discovery.
- An invalid supplied optional site must not permit an earlier organization
  SDK call.
- Per-record tenant-name omissions remain separate from required scope inputs.
- HTTP errors, parse failures, and transport errors keep their existing
  contracts.
- The service-ping caller must not turn a refusal into an empty-source message.

## Requirements

### Functional Requirements

- **FR-001**: Required organization identifiers must pass validation before
  organization network, policy, or template SDK calls.
- **FR-002**: Required site identifiers must pass validation before site
  network, policy, or template SDK calls.
- **FR-003**: Only `None` must select organization-only policy or template
  discovery.
- **FR-004**: An invalid supplied optional site identifier must cause zero SDK
  calls.
- **FR-005**: Each refusal must raise `ValueError` and name `org_id` or `site_id`.
- **FR-006**: Each refusal must log one checked identifier and one refused
  identifier without the input value.
- **FR-007**: Valid identifiers must reach the SDK unchanged.
- **FR-008**: Valid tenant results must preserve deduplication, sorting, and
  unknown per-record handling.
- **FR-009**: Existing HTTP, parse-failure, and transport-error contracts must
  remain unchanged.
- **FR-010**: Unexpected resolver exceptions must propagate unchanged.
- **FR-011**: Discovery callers must receive the refusal before empty-source
  reporting.
- **FR-012**: This repair must leave the broader audit open.

### Key Entities

- **Required identifier**: A string with at least one non-whitespace character.
- **Optional site scope**: `None`, or a valid required site identifier.
- **Refusal**: A named error and a counted log record before an SDK call.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every invalid required-input case produces zero SDK calls.
- **SC-002**: Every invalid-input case produces exactly one named refusal.
- **SC-003**: Organization-only optional calls produce zero site SDK calls.
- **SC-004**: Valid calls preserve exact arguments and exact sorted results.
- **SC-005**: Focused tenant coverage meets at least 90 percent.
- **SC-006**: Existing tenant, response-integrity, and discovery tests pass
  without changes.

## Assumptions

- The constructor resolves the organization identifier lazily.
- Validation must not contact Mist or use production credentials.
- Existing noncompliant directories remain separate technical debt.
- The parent controls publication after queue position 30.
- A future pull request will state `Part of #2863`, not `Closes #2863`.

## Specification Review

The user scenarios, edge cases, requirements, and measurable outcomes have
complete test mappings in [tasks.md](tasks.md).
No unresolved behavior choice remains.
The file-only SpecKit fallback preserves the app-managed branch and shared
SpecKit configuration. [plan.md](plan.md) records that constraint.
The consistency review checked 18 requirements and outcomes across three
artifacts. Every requirement and outcome has a task mapping.
