# Feature Specification: Juniper RMA Correlation for Mist Support Tickets

**Feature Branch**: `3519-juniper-rma-correlation`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Correlate Mist support cases with Juniper service requests and RMA shipping details"

The quoted input is the user request, kept as written. STE does not change quoted text.

Data moves from Mist support tickets into the Juniper support portal, one way only. Only the Juniper portal holds the RMA details. These details include the shipping address, the carrier, the tracking number, and the delivery status. MistHelper cannot show these details today. An operator must open the Juniper portal for each case.

This specification defines a Mist support ticket as a Mist case. It uses the term service request for a Juniper case.

This feature adds a read-only path from MistHelper to Juniper. The path reads the service requests, the RMA details, and the asset data. It links each Mist support ticket to its Juniper records. It writes the result to the standard export outputs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Juniper access (Priority: P1)

An operator checks that MistHelper reaches Juniper with the configured settings.

**Why this priority**: Every other story depends on working access. This check finds a configuration fault before a long run starts.

**Independent Test**: Run the check with valid settings, with one setting removed, and with a wrong identifier. Each run gives a clear pass or fail result.

**Acceptance Scenarios**:

1. **Given** valid settings for Juniper, **When** the operator runs the access check, **Then** the check reports success and writes no output file.
2. **Given** one required setting has no value, **When** the operator runs the access check, **Then** the check stops and names the missing setting. It shows no secret value.
3. **Given** a wrong application identifier, **When** the operator runs the access check, **Then** the check reports the Juniper fault code and its plain-language meaning.

### User Story 2 - Correlate Mist tickets with Juniper RMAs (Priority: P1)

An operator runs the action once. The action lists the Mist support tickets of the organization. It finds the matching Juniper service requests. It adds the RMA details for each matched request. The result is one export. The export shows each ticket with its RMA shipping status.

**Why this priority**: This story delivers the main need. It shows the RMA status beside each Mist support ticket.

**Independent Test**: Use a test set of Mist support tickets. Each ticket links to a known service request. Run the correlation. Check that each ticket shows the expected request number, RMA number, and tracking number.

**Acceptance Scenarios**:

1. **Given** a Mist support ticket with exactly one matching service request, **When** the correlation runs, **Then** the export shows the ticket as matched. It shows the request number and every RMA item of that request.

2. **Given** a Mist support ticket with no matching service request, **When** the correlation runs, **Then** the export lists the ticket as unmatched. The export gives the reason.

3. **Given** a Mist support ticket that matches two or more service requests, **When** the correlation runs, **Then** the export marks the ticket as ambiguous. The export does not choose a request.

4. **Given** a matched service request with two RMAs, **When** the correlation runs, **Then** the export shows a row for each RMA item.

### User Story 3 - Look up one service request or RMA (Priority: P2)

An operator enters a service request number, a customer case number, or an RMA number. The action shows the details on screen and in an export.

**Why this priority**: Operators need a quick answer for one case. This action does not need a full run.

**Independent Test**: Look up a known request number and a known RMA number. Each lookup shows the status, the shipping details, and the tracking numbers.

**Acceptance Scenarios**:

1. **Given** a valid request number, **When** the operator looks it up, **Then** the action shows the request status, priority, product, and RMA numbers.
2. **Given** an RMA number with its request or case number, **When** the operator looks it up, **Then** the action shows each item's tracking number.
3. **Given** a number that Juniper does not know, **When** the operator looks it up, **Then** the action reports that Juniper did not find the number.

### User Story 4 - Add asset and warranty data for serial numbers (Priority: P2)

An operator enters the serial numbers. The correlation can also use the serial numbers of its matched requests. The action adds the asset status, the warranty dates, and the service contract dates for each serial number.

**Why this priority**: Warranty and contract status help the operator decide on an RMA. This story adds value after the core correlation works.

**Independent Test**: Look up a known serial number. The export shows its warranty and contract dates.

**Acceptance Scenarios**:

1. **Given** a list of 350 serial numbers, **When** the operator runs the asset lookup, **Then** the action sends batches of 300 or fewer. It merges the results.
2. **Given** a serial number that Juniper does not find, **When** the lookup finishes, **Then** the export lists that serial number as not found.

### Edge Cases

- Juniper returns a warning with a result. The system keeps the result and shows the warning.

- Juniper returns a fault. The system shows the fault code, its meaning, and the request number. It keeps the other results of the run.

- The network fails during a run. The system retries a fixed number of times. Then it keeps the partial results and marks the run as incomplete.

- Juniper rejects a repeated request identifier. The system creates a new identifier and sends the request once more.

- A service request is older than the list window. A request number in the system still reaches it, and so does a manual lookup.

- An organization has no support tickets. The run finishes with zero rows and states the reason.

- The corporate network inspects encrypted traffic. The access check names the certificate problem and the setting that fixes it.

- Juniper sends a value with characters outside ASCII. The log shows an ASCII-safe form of that value.

## Requirements *(mandatory)*

### Functional Requirements

#### Access and settings

- **FR-001**: The system MUST provide an access check that reports pass or fail for the Juniper settings.
- **FR-002**: The system MUST read the Juniper settings from the environment or from the local settings file.
- **FR-003**: The system MUST name a missing setting. It MUST NOT show the value of any secret setting.
- **FR-004**: The system MUST send Juniper requests only to approved secure host names.
- **FR-005**: The system MUST NOT follow a redirect that Juniper returns.

#### Read-only boundary

- **FR-006**: The system MUST NOT create, update, close, or escalate a Juniper service request.
- **FR-007**: The system MUST NOT attach a file to a Juniper service request. It MUST NOT upload a file to Juniper.

#### Correlation

- **FR-008**: The system MUST read the Mist support tickets of the organization.
- **FR-009**: The system MUST link each Mist support ticket to Juniper service requests by the join rule in Clarification 1.
- **FR-010**: The system MUST mark a ticket with two or more matching requests as ambiguous. It MUST NOT choose one of them.

- **FR-011**: The system MUST list each unmatched ticket with the reason for the missing match.
- **FR-012**: For each matched service request, the system MUST retrieve its RMA list. It MUST retrieve the details of each RMA.
- **FR-013**: The correlation export MUST show these fields for each RMA item. The fields are the RMA number, item type, serial number, product identifier, carrier, tracking number, ship date, receipt or delivery date, and status.

- **FR-014**: The correlation export MUST apply the personal-data rule in Clarification 2.
- **FR-015**: The system MUST write results through the standard export outputs that the operator selects.
- **FR-016**: The system MUST record each run. The record MUST show the start time and the end time. It MUST show the counts of matched, unmatched, ambiguous, and failed items. It MUST show a status of complete or incomplete.

#### Lookup

- **FR-017**: The system MUST look up a service request by its request number or by its customer case number.
- **FR-018**: The system MUST look up an RMA by its RMA number together with its request number or its customer case number.
- **FR-019**: The system MUST report a number that Juniper does not know as not found. It MUST NOT report that number as a fault.

#### Asset data

- **FR-020**: The system MUST look up asset and warranty data for serial numbers in batches of 300 or fewer.
- **FR-021**: The system MUST repeat the lookup for serial numbers that Juniper reports as not processed. The repeat stops after a fixed number of attempts.
- **FR-022**: The system MUST list each serial number that Juniper does not find or does not process.

#### Reliability and response handling

- **FR-023**: The system MUST limit how fast it sends requests to Juniper. The default limit is 2 requests per second.
- **FR-024**: The system MUST retry a temporary failure a fixed number of times. Each retry waits for more time than the retry before it.

- **FR-025**: The system MUST NOT retry a fault that Juniper returns in a response.
- **FR-026**: The system MUST read the status that Juniper reports in each response. It MUST report each warning and each fault with its code and meaning.
- **FR-027**: The system MUST give each request an identifier that Juniper accepts. It MUST NOT reuse an identifier.

#### Security and privacy

- **FR-028**: Log lines MUST use ASCII only.
- **FR-029**: Log lines MUST NOT show a secret. They MUST NOT show a full email address or a full telephone number.
- **FR-030**: The system MUST keep the secret values out of the error messages and out of every export.

#### Testing

- **FR-031**: The automated test suite MUST run without network access and without Juniper credentials.
- **FR-032**: The new actions MUST NOT call Juniper during an automated test run. A live test MUST need an explicit opt-in setting.

Warning: A write call to Juniper can change a customer's service request. This feature has no write action. A reviewer must reject any change that adds one.

### Key Entities *(include if feature involves data)*

- **Mist Support Ticket**: A support case that the organization opened in Mist. It has an identifier, a subject, a status, and a type.

- **Juniper Service Request**: A support case in the Juniper portal. It has a request number, a customer case number, a status, a priority, a product identifier, and a serial number.

- **RMA**: A return authorization for a Juniper service request. It has an RMA number and one or more items.

- **RMA Item**: A defective item or a replacement item in an RMA. It has a serial number, a carrier, a tracking number, and dates.

- **Shipping Contact**: The ship-to details of an RMA. Its personal fields follow the rule in Clarification 2.

- **Asset Record**: The warranty, contract, and status data for one serial number.

- **Correlation Link**: The record that links a Mist support ticket to a Juniper service request. It shows the match rule and the match status.

- **Run Record**: The summary of one run. It shows the counts and the status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator confirms access to Juniper in one action. A failed check names the failed setting in the same result.

- **SC-002**: On a test set of 20 known pairs, 100% of the pairs with one match show as matched with the correct request number.

- **SC-003**: On the same test set, 100% of the RMA items that Juniper returns appear as rows in the export.

- **SC-004**: A scan of the logs finds no secret value. It finds no unmasked email address and no unmasked telephone number in a log line. The exports keep the personal values in full (Clarification 2, amended 2026-10-08).

- **SC-005**: A run sends no request that creates, updates, closes, or escalates a service request. The count of write requests in the request log is zero.

- **SC-006**: A correlation run finishes within 30 minutes at the default request rate for 500 Mist support tickets. If a run takes longer, it reports itself as incomplete and names the items that it did not finish.

- **SC-007**: An operator finds the tracking number for a Mist support ticket in under 2 minutes, from the export.

## Assumptions

- Juniper issues the application identifier, the registered user identifier, the account identifier, the customer source identifier, and the base addresses during onboarding.

- Juniper issues an OAuth 2.0 client ID and client secret, as the endpoints document describes. The design uses the client credentials flow.

- Juniper rate limits are unknown until onboarding. The default rate is 2 requests per second.

- The list from Juniper covers the last 90 days only. For older tickets, the design uses the customer case number for the detail lookup. Juniper must confirm this during onboarding.

- The Mist support tickets of the organization include a ticket identifier, a display name, and a status.

- Notes and attachments of Juniper service requests are out of scope. They can hold sensitive data.

- Correlation results stay in the local data folder or in the approved database.

- This feature changes no existing menu, export, or stored record.

- Live tests need the Juniper onboarding to finish. Until then, automated tests use recorded sample responses.

## Dependencies

- Juniper API onboarding for the test environment and the production environment.
- The existing Mist support ticket listing.
- The existing export outputs and database routing.
- The existing secret redaction support.

## Out of Scope

- Creating, updating, closing, or escalating a Juniper service request.

- Attaching or uploading a file for Juniper.

- Receiving push events from Juniper.

- Downloading bulk asset files from Juniper storage links.

- Caching of the software version lists of Juniper.

- Scheduled runs. This needs a separate decision.

- A web portal view. Clarification 3 decides this.

## Clarifications

The user was not available to answer. These decisions use the recommended option. Review them before implementation starts.

### Clarification 1: Join key

Decision: A link joins a Mist support ticket and a Juniper service request. The link exists when the customer case number of the request equals the value of one field of the Mist ticket. The default field is `case_number`, the display name of the ticket. An operator can select `id`, the ticket identifier, with a setting.

The comparison trims spaces and is case-sensitive. One match is a matched link. Two or more matches make an ambiguous link. No match makes an unmatched ticket. Juniper must confirm the field during onboarding, with one known pair of values.

### Clarification 2: Personal data

Decision: Store the RMA shipping fields. Keep the personal fields in full in every export. Mask the personal fields in every log line. The personal fields are the contact name, the email address, the telephone number, and the street address lines.

Keep stored personal fields for 180 days. Amended 2026-10-08: the operator asked for the names and e-mail addresses in the exports, so the exports stopped masking them. Version one has no option that shows unmasked values in a log line.

### Clarification 3: Where results appear

Decision: Menu exports only. Results use the standard export path, which writes CSV, SQLite, or the configured database. A web portal page and scheduled runs are out of scope for version one.
