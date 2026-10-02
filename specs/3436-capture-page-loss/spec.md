# Feature Specification: Capture reads report a lost page

**Feature Branch**: `jmorrison-juniper-capture-page-loss-reporting`

**Created**: 2026-10-02

**Status**: Ready for implementation

**Input**: Issue [#3436](https://github.com/jmorrison-juniper/MistHelper/issues/3436)
and [comment 5845437029](https://github.com/jmorrison-juniper/MistHelper/issues/3436#issuecomment-5845437029).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep device evidence after a lost page (Priority: P1)

An operator needs the available device evidence and a clear indication of an incomplete read.
This applies to capture inventory, capture device statistics, and gate fleet statistics.

**Why this priority**: An incomplete device read must not appear complete during a firmware investigation.

**Independent Test**: Supply valid pages, then a failed page, through an offline cloud response source.
Check the retained device evidence and the exact partial reason.

**Acceptance Scenarios**:

1. **Given** valid device pages, **When** a later page fails, **Then** the read retains earlier records and reports the failed status.
2. **Given** a JSON error page, **When** the reader receives it, **Then** the reader reports the loss without a row-copy exception.
3. **Given** complete device pages, **When** the read ends, **Then** values, order, and absence of partial reasons remain unchanged.
4. **Given** a partial fleet read, **When** the gate receives it, **Then** the existing settle decisions remain unchanged.

### User Story 2 - Keep wireless evidence in the final capture (Priority: P1)

An operator needs the wireless clients that the portal read before a page failed.
The final capture must name the incomplete wireless read.

**Why this priority**: A helper result provides no protection if the collector discards its partial reason.

**Independent Test**: Run the real collector and final assembly with offline response sources.
Check the wireless rows and the final `partial_reasons`.

**Acceptance Scenarios**:

1. **Given** valid wireless statistics followed by a failed page, **When** the collector builds the capture, **Then** earlier clients remain available.
2. **Given** that failed page, **When** the collector builds the capture, **Then** the wireless reason carries its exact status.
3. **Given** a successful wireless statistics read, **When** the collector builds the capture, **Then** the existing client join remains unchanged.
4. **Given** a failed wired, wireless-search, or guest map read, **When** the collector receives it, **Then** its existing visible failure remains unchanged.

### User Story 3 - Keep tier 3 evidence in the final capture (Priority: P1)

An operator needs available ports, tunnels, BGP peers, and alarms after a later page fails.
The shared port read must report the loss for both port sections.

**Why this priority**: The status of the first page cannot describe a failed later page.

**Independent Test**: Run each real tier 3 endpoint through the collector with native paged responses.
Check the retained rows and the exact final section reasons.

**Acceptance Scenarios**:

1. **Given** a lost port page, **When** the collector builds the capture, **Then** `switch_ports` and `poe` retain earlier rows and report the loss.
2. **Given** a lost tunnel, BGP, or alarm page, **When** the collector builds the capture, **Then** that section retains earlier rows and reports the loss.
3. **Given** a failed later page, **When** the page walk ends, **Then** it makes no subsequent page request.
4. **Given** complete or valid empty pages, **When** the capture finishes, **Then** no false partial reason appears.

### Edge Cases

- A later response carries `403`, `404`, `429`, `500`, or `503`.
- A later response carries HTML, a JSON error map, malformed JSON, or an unreadable body.
- A later response carries no HTTP status, or the page call raises a transport exception.
- A failure follows two valid pages.
- A page holds a malformed individual record.
- The first page fails, or a successful read holds zero records.
- A virtual chassis header total differs from its collapsed row count.
- A search response carries `results` and a native next link.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All five required read surfaces MUST report a lost later page.
- **FR-002**: Each lost-page reason MUST use `page_count_mismatch` and the failed page's real HTTP status.
- **FR-003**: A transport failure without an HTTP response MUST use status `0`.
- **FR-004**: Each read MUST retain every record of the earlier valid pages.
- **FR-005**: A failed page MUST contribute no error-body key as a record.
- **FR-006**: The page walk MUST stop at the first lost page.
- **FR-007**: A malformed individual record MUST remain inside the read error boundary.
- **FR-008**: A complete read MUST preserve record values and order.
- **FR-009**: A valid empty read MUST remain successful.
- **FR-010**: The existing first-page status, shape, and body-total classifications MUST remain available.
- **FR-011**: The final capture MUST retain wireless and tier 3 reasons, not only helper results.
- **FR-012**: Each final reason MUST preserve the existing report section and source names.
- **FR-013**: The repair MUST NOT compare header totals against record counts.
- **FR-014**: Endpoint parameters, page sizes, normalization, keys, schema, scheduling, and rate limits MUST remain unchanged.
- **FR-015**: Firmware writes, settle policy, confirmations, and downstream decision rules MUST remain unchanged.
- **FR-016**: The site picker and reconciliation repair of issue #3438 MUST remain outside this change.
- **FR-017**: Every acceptance test MUST use an offline source and make zero live transport or write calls.
- **FR-018**: The guard proof MUST count its checked cases and demonstrate a failing decision.

### Key Entities *(include if feature involves data)*

- **Paged read**: The section name, available records, and partial reasons from one read.
- **Partial reason**: The existing `section`, `reason`, and `http_status` fields.
- **Fleet read**: The available device readings and the partial reasons of one gate round.
- **Capture**: The existing final document with retained sections and `partial_reasons`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five required surfaces report the exact lost-page reason and status in offline acceptance cases.
- **SC-002**: Every complete-read acceptance case preserves the expected values and order with no partial reason.
- **SC-003**: Every lost-page acceptance case makes zero subsequent requests after the failed page.
- **SC-004**: The final capture carries the wireless reason and each applicable tier 3 reason.
- **SC-005**: The acceptance cases make zero live transport calls and zero store or firmware write calls.
- **SC-006**: A counted negative proof rejects the former unchecked walk.
- **SC-007**: All measured changed statements and branches have direct coverage.

## Assumptions

- The issue and its later comment define one complete repair, not a three-read subset.
- This work prepares one validated local commit at publication position 39.
- The parent must grant a full verified-main SHA before publication.
- A human must review this firmware-evidence change before merge.
- The temporary `clients.py` handoff permits no edit to `page_limit` or numeric-input policy.
- The later authorized rebase must retain the merged numeric-input repair of issue #3395.
- No live cloud, browser, container, firmware operation, or production store is necessary.
