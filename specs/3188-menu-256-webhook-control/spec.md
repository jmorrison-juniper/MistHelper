# Feature Specification: Menu 256 Webhook Control

**Feature Branch**: `jmorrison-juniper-endpoint-explorer-sweep-3188`

**Created**: 2026-10-06

**Status**: Implemented with focused local validation

**Input**: Repair web portal menu 256 organization webhook delivery selection for issue #3188.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select a Webhook in the Portal (Priority: P1)

A portal operator selects one organization webhook before running menu 256.

**Why this priority**: Menu 256 cannot run correctly in the portal without a webhook selection.

**Independent Test**: Request the menu 256 parameter route with mocked webhooks. Verify one required choice control contains each webhook.

**Acceptance Scenarios**:

1. **Given** an organization has webhooks, **When** the portal requests `/api/operations/parameters/256`, **Then** the route returns one required webhook choice parameter.
2. **Given** a webhook has an identifier and name, **When** the route builds its option, **Then** the value is the identifier and the label is readable.
3. **Given** the operator selects a webhook, **When** menu 256 runs, **Then** the delivery search uses the selected webhook identifier.

---

### User Story 2 - Preserve Command-Line Selection (Priority: P2)

A command-line operator continues to select a webhook with the displayed one-based number.

**Why this priority**: The portal repair must not break the existing command-line workflow.

**Independent Test**: Supply a mocked webhook list and the input `2`. Verify the resolver selects the second webhook.

**Acceptance Scenarios**:

1. **Given** the command line displays two webhooks, **When** the operator enters `2`, **Then** the resolver returns the second webhook identifier and name.
2. **Given** the resolver receives a valid webhook identifier, **When** it resolves the choice, **Then** it returns the matching webhook identifier and name.
3. **Given** the resolver receives an unknown identifier, **When** it validates the choice, **Then** it rejects the choice without a delivery search.

---

### User Story 3 - Handle Missing or Failed Choice Data (Priority: P3)

A portal operator receives a clear safe result when webhook choices are unavailable.

**Why this priority**: Empty and failed reads must not create an invalid selection or a false successful run.

**Independent Test**: Mock an empty webhook list and a failed webhook request. Verify each response without a live Mist call.

**Acceptance Scenarios**:

1. **Given** an organization has no webhooks, **When** the portal requests menu 256 parameters, **Then** the choice parameter has no options.
2. **Given** the webhook list request fails, **When** the portal requests menu 256 parameters, **Then** the route returns an error and no fabricated choice.
3. **Given** no valid webhook is selected, **When** menu 256 starts, **Then** no delivery search occurs.

### Edge Cases

- A webhook name can be empty. The portal uses the stable identifier as its readable fallback label.
- A webhook record can lack a usable identifier. The portal does not expose that record as a selectable option.
- Two webhooks can have the same name. Their identifiers keep their choices distinct.
- The Mist response can return webhooks in a different order between requests.
- A numeric webhook identifier can also resemble a command-line number. An exact identifier match takes precedence over positional selection.
- The webhook list can be empty without being an API failure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST expose the exact static route `/api/operations/parameters/256`.
- **FR-002**: The static route MUST return the existing parameter envelope with exactly one choice parameter in `parameters`.
- **FR-003**: The choice parameter MUST use `name` value `webhook_id`.
- **FR-004**: The choice parameter MUST use `label` value `Webhook`.
- **FR-005**: The choice parameter MUST use `param_type` value `choice`.
- **FR-006**: The choice parameter MUST use `required` value `true`.
- **FR-007**: The choice parameter MUST include an `options` list.
- **FR-008**: Each option MUST contain `value` and `label` fields.
- **FR-009**: Each option value MUST equal the webhook stable identifier.
- **FR-010**: Each option label MUST use the webhook name when the name is available.
- **FR-011**: Each option label MUST use the webhook identifier when the name is absent.
- **FR-012**: The route MUST preserve the Mist webhook order in the returned option list.
- **FR-013**: The route MUST return the same choice parameter shape with an empty `options` list when no webhooks exist.
- **FR-014**: The route MUST return a clear non-success response when the webhook list request fails.
- **FR-015**: A failed webhook list request MUST NOT return stale, partial, or fabricated options.
- **FR-016**: The exporter resolver MUST accept an exact stable webhook identifier.
- **FR-017**: The exporter resolver MUST retain existing one-based command-line number support.
- **FR-018**: An exact identifier match MUST select the same webhook after the webhook list order changes.
- **FR-019**: A one-based number MUST select the webhook at that current displayed position.
- **FR-020**: The resolver MUST reject an identifier that is not present in the current webhook list.
- **FR-021**: The resolver MUST reject zero, negative, nonnumeric positional input, and positions beyond the current list.
- **FR-022**: An invalid selection MUST stop before the webhook delivery search.
- **FR-023**: The portal parameter route and exporter tests MUST use mocked Mist responses.
- **FR-024**: No test for this feature MAY make a live Mist cloud request.
- **FR-025**: The feature MUST preserve the existing menu 256 export behavior after a valid selection.
- **FR-026**: The exact route MUST use the existing always-registered settings blueprint.

### Mist Cloud Transport Requirements

- The feature uses `mistapi.api.v1.orgs.webhooks.listOrgWebhooks` to obtain organization webhook choices.
- Menu 256 uses `mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries` after a valid selection.
- Direct HTTP requests to the Mist REST API are prohibited for this feature.
- Contract tests MUST prove successful lists, empty lists, list failures, and delivery-search suppression after invalid selection.
- Contract tests MUST use a mocked authenticated session and MUST not expose credentials.

### Key Entities

- **Webhook Choice Parameter**: The required portal control with a name, label, type, required state, and option list.
- **Webhook Option**: A selectable webhook with a stable identifier value and a readable label.
- **Webhook Selection**: The portal identifier or command-line position that resolves to one current webhook.
- **Webhook Delivery Search**: The menu 256 read operation that requires a validated organization and webhook identifier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The exact menu 256 parameter route returns one required choice control for every successful request.
- **SC-002**: One hundred percent of returned option values equal stable webhook identifiers.
- **SC-003**: A selected identifier resolves to the same webhook across all tested webhook order changes.
- **SC-004**: All existing valid one-based command-line selections continue to resolve to their displayed webhook.
- **SC-005**: Every tested invalid identifier results in zero webhook delivery search calls.
- **SC-006**: Empty webhook lists return zero options and do not enable a valid selection.
- **SC-007**: Mocked webhook list failures return a non-success result with zero fabricated options.
- **SC-008**: The feature test suite completes with zero live Mist cloud calls.

## Assumptions

- The portal already understands the existing `choice` parameter shape.
- The portal queues the selected option value as the exporter input.
- Mist webhook identifiers are stable within an organization.
- Webhook names are display text and are not stable selection keys.
- The current menu 256 export format and output naming remain outside this repair.
- General portal parameter routing changes remain outside this feature.
