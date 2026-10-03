# Feature Specification: Webhook delivery refusals

**Feature Branch**: `jmorrison-juniper-webhook-delivery-refusals`

**Created**: 2026-10-03

**Status**: Ready for local implementation

**Input**: Repair [issue #3745](https://github.com/jmorrison-juniper/MistHelper/issues/3745) within its exact local reservation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Distinguish a refused delivery search (Priority: P1)

An operator must distinguish a failed search from a successful search with no deliveries.

**Why this priority**: The existing permission refusal prints the normal empty-data notice.

**Independent Test**: Run the actual delivery operation with controlled failed responses. Check the exporter error and zero persistence calls.

**Acceptance Scenarios**:

1. **Given** a selected webhook, **When** the first response fails, **Then** the exporter reports the refusal without persistence.
2. **Given** an accepted first page, **When** a later page fails, **Then** the exporter refuses the complete export.
3. **Given** an unreadable status or body, **When** the exporter reads the response, **Then** the exporter reports the failure.

---

### User Story 2 - Retain successful output (Priority: P2)

An operator retains the existing output for successful delivery searches.

**Why this priority**: A refusal repair must not change successful data, pagination, or output selection.

**Independent Test**: Read real temporary CSV output from native single-page and multiple-page controls.

**Acceptance Scenarios**:

1. **Given** successful pages, **When** the export completes, **Then** the output retains all records in page order.
2. **Given** a successful empty array, **When** the search completes, **Then** the normal empty-data notice remains.
3. **Given** standalone mode, **When** a successful CSV export completes, **Then** the existing database warning remains.

---

### User Story 3 - Distinguish failed webhook discovery (Priority: P3)

An operator must distinguish failed webhook discovery from an organization without configured webhooks.

**Why this priority**: The same class consumes discovery responses before the delivery search.

**Independent Test**: Run actual native webhook discovery with failed and successful controls.

**Acceptance Scenarios**:

1. **Given** a failed discovery page, **When** discovery runs, **Then** the exporter reports the refusal without a selection prompt.
2. **Given** successful discovery pages, **When** the operator selects a webhook, **Then** the existing identifier and name remain.
3. **Given** successful empty discovery data, **When** discovery runs, **Then** the configured-empty notice remains.

### Edge Cases

- A later page refuses access after the first page returns records.
- The status is missing, unreadable, nonnumeric, Boolean, or outside the HTTP range.
- The wire body is blank, malformed, or an unsupported JSON shape.
- A record array contains a non-object item.
- A page link is unreadable, malformed, repeated, or returns no response.
- A successful page contains a delivery whose own destination status is an HTTP failure.
- The SDK retains its original session, native error records, and response identity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exporter must read a reliable successful HTTP status before accepting body data.
- **FR-002**: The exporter must validate every response page before persistence.
- **FR-003**: A failed or unreadable response must produce an exporter-owned ERROR record.
- **FR-004**: A refusal must prevent persistence, final output, CSV output, and partial-success notices.
- **FR-005**: Successful list and `results` arrays must retain their records and order.
- **FR-006**: Successful empty arrays must retain the existing empty-result notices.
- **FR-007**: Successful output must retain its filename, endpoint metadata, normalization, and format selection.
- **FR-008**: Directly coupled webhook discovery must apply the same response refusal decision.
- **FR-009**: Refusal records must contain safe resource, organization, webhook, and page context without raw bodies or secrets.
- **FR-010**: SDK pagination links, session identity, and native failure records must remain unchanged.

### Key Entities *(include if feature involves data)*

- **Response page**: The status, body, record array, and next-page link of one SDK response.
- **Delivery record**: An unchanged record from the selected organization webhook.
- **Response refusal**: A safe failure reason that prevents normal empty-result and persistence paths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every controlled failed first or later page produces an exporter error and zero persistence calls.
- **SC-002**: Native `401`, `403`, `404`, and `503` cases produce no final output or partial success.
- **SC-003**: Successful controls retain exact output metadata, filenames, record values, and page order.
- **SC-004**: Genuine successful empty controls retain their normal empty-result notices.
- **SC-005**: The unchanged source fails the new native refusal contract while the successful control passes.
- **SC-006**: Scoped runtime evidence records zero live HTTP, DNS, socket, SQLite, router, and database operations.

## Assumptions

- The controlled host is `api.mist.com`, in the US cloud.
- Tests use synthetic organization and webhook identifiers.
- The preparation base is `f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0`.
- This repair remains local at queue position 51. The base grants no publication permission.
- Existing tests and every unreserved file remain read-only unless the coordinator grants a narrow fixture correction.
- Issue #2746 remains a separate test-quality campaign.
- This change adds no API integration, dependency, schema, primary key, or database guarantee.
