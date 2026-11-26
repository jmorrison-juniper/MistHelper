# Feature Specification: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

**Feature Branch**: `feat/4934-mist-netcool-runbook`

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: `"NOC runbook for the Juniper Mist to IBM Netcool alarm integration"`

## Clarifications

### Session 2026-11-25

- Q: Which product names and person names can the runbook contain? -> A: The runbook can name only Juniper Mist, IBM Netcool, and their components. The runbook can also name the command tools MistHelper, mistapi, Python, PowerShell, and curl. The only person is the author, Joseph Morrison. Other systems use a generic role term, for example "the legacy event manager".

- Q: Does the runbook choose REST polling, webhooks, or a hybrid design? -> A: The baseline is REST polling of the organization search endpoints. A hybrid design (webhooks for low latency, polling for reconciliation and replay) is a recommended enhancement that needs change approval.

- Q: Which Netcool receiver does the runbook specify? -> A: None. The Netcool administrator selects the probe or the interface. The runbook gives a proposed normalized record and a proposed field mapping, and it marks each one as a proposal. Facts from IBM documentation have the mark "Verified (vendor documentation)".

- Q: Which HTTP methods and how many requests can the smoke test use? -> A: The smoke test uses GET only. The default budget is 60 requests in one run. Each paged request uses `limit=1000`.

- Q: Where does the smoke test write its evidence, and what can a committed file hold? -> A: Redacted JSON under `test-artifacts/`, which Git ignores. A committed file holds statuses, field names, catalog names, and catalog sizes only. It holds no organization identifier and no organization data volume.

## User Scenarios & Testing *(mandatory)*

This feature adds a runbook and a read-only smoke test. The runbook tells a network operations center (NOC) how to collect alarms and events from Juniper Mist.

The runbook also tells the NOC how to send them to IBM Netcool and how to operate the feed.

### User Story 1 - Configure the Mist to Netcool collection (Priority: P1)

The integration engineer uses the runbook to configure the collection of Mist alarms and events.

The configuration covers the endpoint families, scope rules, collection windows, pagination, rate limits, tokens, and the Netcool mapping.

**Why this priority**: The collection does not start until the configuration is correct. The configuration decides which alarms reach the NOC.

**Independent Test**: The reviewer reads Sections 5, 6, 8, and 9 of the runbook. Each setting has a value or a placeholder, and a verification mark.

**Acceptance Scenarios**:

1. **Given** the runbook is complete, **When** the engineer reads Section 5, **Then** the engineer finds the regional host, token, and organization settings.

2. **Given** the runbook is complete, **When** the engineer reads Sections 6 and 8, **Then** each endpoint family shows its collection window and rate-limit rule.

3. **Given** the runbook is complete, **When** the engineer reads Section 9, **Then** each Netcool field shows its mapping and its status as a proposal.

---

### User Story 2 - Verify the runbook and the organization with a read-only smoke test (Priority: P1)

The integration engineer runs a read-only smoke test. The smoke test checks the runbook facts and the readiness of one Mist organization.

It sends GET requests only.

**Why this priority**: Each Verified (live) mark needs evidence from a live call. The smoke test creates that evidence.

**Independent Test**: First, run the offline document test with no token and no network access. Then the engineer runs the smoke test with one test organization and reads the exit code and the evidence record.

**Acceptance Scenarios**:

1. **Given** a valid token and an approved origin, **When** the engineer runs the smoke test, **Then** each smoke check reports a result.

2. **Given** a finished smoke test run, **When** the engineer reads the output, **Then** the output prints the number of checks examined.

3. **Given** a finished smoke test run, **When** the engineer reads the evidence record, **Then** the record holds no token or identifier.

4. **Given** no network access, **When** the engineer runs the offline document test, **Then** the test checks each API path.

---

### User Story 3 - Operate the feed (Priority: P2)

A NOC operator operates the feed. The operator runs the start-of-shift check, handles alarms, recovers the checkpoint, replays a collection window, rotates the token, and escalates a fault.

**Why this priority**: The feed runs in every shift, so each shift needs the same procedures.

**Independent Test**: The reviewer follows each operating procedure on a test feed. Each step shows an expected result.

**Acceptance Scenarios**:

1. **Given** the start-of-shift check in Section 11, **When** the operator performs each step, **Then** the operator knows whether the feed is healthy.

2. **Given** a failed collection, **When** the operator follows the checkpoint recovery procedure, **Then** the operator replays the missed collection window.

3. **Given** an unresolved fault, **When** the operator follows the escalation procedure, **Then** the operator sends the evidence to the named role.

---

### User Story 4 - Troubleshoot zero results, high volume, and HTTP errors (Priority: P2)

A NOC operator or an integration engineer finds the cause of a symptom. The symptoms are zero results, a large number of device events, and an HTTP error.

**Why this priority**: Each symptom can stop the feed or hide an alarm. Each symptom needs a cause and an action.

**Independent Test**: The reviewer reads each symptom row in Section 12 and follows its diagnostic steps on a test organization.

**Acceptance Scenarios**:

1. **Given** a system event search with zero records, **When** the engineer follows the zero-results procedure, **Then** the engineer finds the cause.

2. **Given** thousands of device events in one collection window, **When** the engineer applies the allowlist, **Then** the engineer measures the new volume.

3. **Given** an HTTP error, **When** the engineer reads the status reference, **Then** the engineer finds the cause and the next action.

---

### User Story 5 - Decide the scope (Priority: P3)

The owners decide the scope of the feed. The decisions cover the baseline, each enhancement, the AP Warning report (menu 307), and the open decisions.

**Why this priority**: The baseline is a like-for-like move. Each enhancement needs a separate approval, so the owners decide each one.

**Independent Test**: The reviewer checks that Section 3 and Section 15 list each enhancement, its approval status, and its owner role.

**Acceptance Scenarios**:

1. **Given** Section 3 of the runbook, **When** the change approver reads it, **Then** the approver finds the baseline and each enhancement in one table.

2. **Given** Section 10, **When** the NOC lead reads it, **Then** the lead finds the decision for the AP Warning report and its evidence.

3. **Given** Section 15 of the runbook, **When** an owner reads it, **Then** the owner finds each open decision with its owner role.

---

### Edge Cases

- **What happens when the operator sets no token?** The smoke test stops before it sends any request. It ends with the outcome class of a configuration error.

- **What happens when the regional host is wrong?** A host that is not in the OpenAPI server list gives exit code 2. Otherwise, the smoke test records the HTTP status or the connection error. The runbook gives the host check for this case.

- **What happens when the API returns HTTP 400?** The smoke test marks the smoke check as failed. The evidence keeps the status and at most 200 characters of the redacted error text.

- **What happens when the API returns HTTP 401?** The smoke test maps the rejected token to the Configuration error class, exit code 2, and stops the run. This applies at login and at any call. The `mistapi.APISession` raises `ValueError` on HTTP 401 during token validation.

- **What happens when the API returns HTTP 403?** The smoke test marks the smoke check as failed. The run continues, and the runbook gives the token scope check.

- **What happens when the API returns HTTP 404?** The smoke test marks the smoke check as failed. The runbook lists the causes, including a wrong organization identifier and a wrong path.

- **What happens when the API returns HTTP 429?** The mistapi SDK retries the request three times and waits for the `Retry-After` value. The smoke test does not retry again. A final HTTP 429 response ends the run with the outcome class of a rate-limit stop. The evidence record can hold the numeric `Retry-After` value. The value is not a secret.

- **What happens when the API returns HTTP 5xx?** The smoke test retries the request at most two times. It then marks the smoke check as failed.

- **What happens when a request times out?** The client runs each SDK call in a daemon worker thread and waits at most `--call-timeout` seconds (default 30) for the result. The smoke test does not retry a timeout. It marks the smoke check as failed with the error `Timeout`. The second timeout in one run ends the run with the rate-limit stop, exit code 3. Each call counts against the request budget.

- **What happens when the connection fails?** The smoke test retries the request at most two times. It then marks the smoke check as failed with the connection cause. A connection failure during token validation at login gives exit code 2. The runbook gives the network checks.

- **What happens when the body holds malformed JSON?** The smoke test marks the smoke check as failed. It does not count the response as zero records.

- **What happens when the body is empty?** The smoke test marks the smoke check as failed. A successful empty result has a valid body with no records.

- **What happens when a successful response contains no records?** The smoke test accepts the response as a valid result. The check status is WARN for an endpoint family. An empty Mist Edge device list or an empty webhook list gives INFO (SMK-10). Zero records of the AP statistics give WARN (SMK-10). The runbook gives the zero-results procedure.

- **What happens when a chain of next links does not end?** The smoke test ends the query at the page ceiling and marks the query as incomplete. The check status is WARN, and the stop reason is `PageCeiling`. The run continues.

- **What happens when a next link has a different origin?** The smoke test does not send a request to that link. It ends the run with the outcome class of an unsafe paging stop.

- **What happens when a next link returns a page that the run already read?** The smoke test ends the run with the outcome class of an unsafe paging stop.

- **What happens when the smoke test exhausts its request budget?** The smoke test sends no more requests. It lists each smoke check that did not run, and it ends the run with the outcome class of a budget stop.

- **What happens when the live catalog does not hold a catalog name from the runbook?** The smoke test fails the catalog check and names the missing value. The integration engineer corrects the runbook before any team uses the Verified (live) mark.

- **What happens when an organization has zero alarms?** The smoke test gives the check status WARN for the zero records. The runbook states that an empty result does not clear any open alarm.

- **What happens when the runbook lacks a section?** The test returns an error that names the missing heading.

- **What happens when the runbook or the specification file does not exist?** The offline document test fails, and it never reports a pass when it examines zero items. The smoke test gives SKIP for a missing default runbook. An explicit `--runbook` path that is missing gives exit code 2. An OpenAPI file that cannot be read also gives exit code 2.

## Requirements *(mandatory)*

### Functional Requirements

#### Runbook content

- **FR-001**: The feature delivers one self-contained Markdown file at `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`.

  In this feature, self-contained means that a reader can complete each procedure with this file alone. Links to other runbooks and to vendor documentation are optional references.

- **FR-002**: The runbook uses the outline in the table below, in the same order, with each heading text kept. The title is the H1 `# MIST_NETCOOL_ALARM_INTEGRATION`. A table of contents follows the Overview table. The runbook has no separate section 0.

| Heading text | Required content |
| --- | --- |
| 1. Overview | A table with the fields Document type, Platform, Purpose, Audience, Author, Version, Date, Status, and Verification, plus the verification legend. The date uses UTC ISO 8601. |
| 2. How to Use This Runbook | Audience, reading path for each role, conventions, placeholders, and safety rules for read-only commands. |
| 3. Purpose and Scope | Purpose, baseline and enhancement table, and device classes in scope. |
| 4. Architecture | Components, data flow diagram, polling versus webhook versus hybrid, and organization scope versus site scope rules. |
| 5. Prerequisites | Roles, API tokens, secret handling, network access, regional API hosts, and configuration model. |
| 6. Mist Data Sources | One subsection for each endpoint family, the definition catalogs, and the webhook topics. |
| 7. Alarm and Event Selection | Coverage matrix, device event allowlist, alarm type list, clear and recovery matrix with the columns Open condition, Clear condition, Source, Key match, and Fallback, and event inventory procedure. |
| 8. Collection Design | Schedule, checkpoint, overlap, indexing delay, pagination, rate-limit budget and sizing, collection result states, deduplication keys, correlation, restart, and replay. |
| 9. Netcool Integration | Delivery path, normalized record schema, field mapping, severity mapping, problem and resolution events, field rules, and delivery reliability. |
| 10. AP Warning Report (Menu 307) | Function, equivalence table, recommendation, unattended run, and mapping to Netcool. |
| 11. NOC Operating Procedures | Start-of-shift check, metrics and thresholds, alarm handling, checkpoint recovery and replay, token rotation, webhook check, and escalation. |
| 12. Troubleshooting | Symptom table, zero results, zero alarms for one organization, high device event volume, HTTP status reference, pagination faults, time faults, and webhook faults. |
| 13. Verification and Smoke Test | Manual read-only checks, automated smoke test, and live verification record. |
| 14. Acceptance Criteria and UAT Plan | Criteria, UAT cases, and evidence template. |
| 15. Open Decisions | Each open decision with its owner role. |
| Appendix A. Endpoint Reference | The GET endpoints, with the columns Method, Path, Scope, Purpose, and Verification. |
| Appendix B. Verified Catalog Names | The name tables B.1 to B.5. Section B.4 appears only when the live system event catalog is not empty. The offline test accepts B.4 present or absent, and the live run checks its names. |
| Appendix C. Sample Payloads | Synthetic and redacted examples. |
| Appendix D. Glossary | Each term and abbreviation of the runbook. |
| Appendix E. Revision History | A revision table with the columns Version, Date, Author, and Change. |

- **FR-003**: The runbook uses the six verification marks in the table below.

| Mark | Meaning |
| --- | --- |
| Verified (live) | A read-only call to the Mist API on the date in Section 13 showed the fact. |
| Verified (OpenAPI) | The specification file in `documentation/` shows the fact. |
| Verified (MistHelper) | The MistHelper source code shows the fact. |
| Verified (vendor documentation) | Official vendor documentation shows the fact. |
| Proposal | A design proposal. An owner must approve it. |
| Open decision | An owner must decide. Section 15 lists it. |

A fact marked `Pending live verification` becomes `Verified (live)` after the live run, or it leaves the runbook. A fact marked `Pending Netcool administrator confirmation` becomes `Proposal`. A fact marked `Open, confirm with Mist` becomes `Open decision`.

- **FR-004**: A technical claim is a statement of an API path, parameter, field, value, limit, product behavior, or Netcool column fact. Each technical claim has one verification mark in the runbook. Each fact table has a Verification column, and each prose claim carries its mark in parentheses.

- **FR-005**: The runbook answers each question of the integration team with a procedure that any NOC can repeat.

| Question | Required answer content |
| --- | --- |
| 1. Endpoint families | For each of the four endpoint families: the covered condition, event types, clear role, duplicates, filters, collection window, pagination, normal volume, meaning of zero results, latency, and baseline or enhancement status. Alarms have no clear record, so recovery comes from device events or from ExpireTime. Device events use the recovery event type of a pair. Mist Edge events use the reconnect event type. System events are information only. |
| 2. AP Warning report (menu 307) | What the report detects, whether its data is raw or derived, whether an organization endpoint gives the same data, whether site scope is needed, whether one run each hour is acceptable (an open decision, when 60 minutes plus the run time is within the NOC freshness target), and how report rows map to Netcool events and clears. The deduplication key is org_id + mac + code. The clear key is org_id + mac, and a row clears when it moves to the recovered file or is absent from a later complete run. |
| 3. Site-level queries | The site count, request volume, pagination worst case, concurrency, poll interval, timeout, retry, rate-limit behavior, maximum collection time, and the behavior when one site or one organization fails. The proposal values are bounded concurrency of 4 concurrent requests for each token (Proposal), a 30-second timeout for each request, and the state PARTIAL_ORGANIZATION when the site queries do not finish within the poll interval. |
| 4. Zero records from system event or Mist Edge event searches | The diagnostic steps: HTTP status, body, region, organization, parameters, collection window, filter, token scope, device ownership, longer lookback, no filter, and the documented page size. |
| 5. Device event volume | Event types, device families, server-side filters, pagination, normalization, deduplication, suppression of informational events, clear mapping, and the expected volume after the filter. Informational device events map to Netcool type 13 (Information) with an ExpireTime of 3600 seconds (Proposal), and they create no clear. |
| 6. Zero alarms for one organization | The organization identifier and region with no token in the output, the device inventory, the active alarms, a comparison with the Mist portal, a 24-hour lookback, no filter, full pagination, token access, the regional host, and a check for a hidden HTTP error. |

- **FR-006**: The runbook documents the five-minute poll interval and the hourly AP Warning report run as proposals. The baseline design is REST polling of the organization search endpoints.

- **FR-007**: The runbook ends each collection window a short time before the current time, and it overlaps successive collection windows. In this feature, a short time is 2 minutes (Proposal). The live measurement confirms or changes this value.

- **FR-008**: The runbook gives the collection window end lag and the collection window overlap as values with a verification mark. The end lag is 2 minutes (Proposal), and the overlap is 5 minutes (Proposal).

  On restart, the collector reads each checkpoint and starts the next collection window at the checkpoint minus the overlap.

- **FR-009**: Each paged request uses `limit=1000`, and the runbook never assumes that a larger page size is valid.

- **FR-010**: The runbook states that a `type` filter is a comma-separated list with no spaces, brackets, or quotes.

- **FR-011**: The runbook requires a check of the HTTP status and the error body for each Mist API call. An empty SDK list is not proof of success.

- **FR-012**: The runbook defines each collection result state. The nine states are `SUCCESS_WITH_RECORDS`, `SUCCESS_EMPTY`, `FAILED_HTTP`, `FAILED_AUTH`, `FAILED_THROTTLED`, `FAILED_PARSE`, `FAILED_INCOMPLETE_PAGINATION`, `FAILED_DELIVERY`, and `PARTIAL_ORGANIZATION`. Only `SUCCESS_WITH_RECORDS` and `SUCCESS_EMPTY` can advance a checkpoint. No state can create a clear by absence.

  The collector design uses these states. The smoke test does not use them. It uses check statuses (PASS, WARN, INFO, FAIL, SKIP) and outcome classes.

| Collection result state | Meaning |
| --- | --- |
| `SUCCESS_WITH_RECORDS` | Each page returns HTTP 200 with a valid body. The last page has no `next`. The collection holds one record or more. |
| `SUCCESS_EMPTY` | The same as `SUCCESS_WITH_RECORDS`, with zero records. |
| `FAILED_HTTP` | A request ends with an HTTP status other than 200, 401, 403, or 429 after the allowed retries, or the request times out, or the connection fails. |
| `FAILED_AUTH` | The API returns HTTP 401 or HTTP 403. |
| `FAILED_THROTTLED` | The API still returns HTTP 429 after one more attempt, or the remaining requests of the hour are fewer than the requests of the next poll. |
| `FAILED_PARSE` | The body is not valid JSON, is empty, or has no `results` list. |
| `FAILED_INCOMPLETE_PAGINATION` | The collection stops before the last page. The causes are a page ceiling, a foreign `next` origin, a repeated page, or missing pagination metadata. A production collector does not cap silently. In the smoke test, a page ceiling gives WARN. |
| `FAILED_DELIVERY` | The collection succeeds, but the delivery to Netcool or to the durable buffer fails. The checkpoint does not advance. |
| `PARTIAL_ORGANIZATION` | One endpoint family or more of an organization fails while others succeed. Checkpoints advance only for the families that succeed. |

  The collector rules are these (Proposal). The collector retries an HTTP 5xx response, a timeout, and a connection failure at most two times, with exponential backoff and jitter. On HTTP 429, the collector waits for the Retry-After value and makes at most one more attempt. The collector reads the pagination metadata fields `next`, `total`, `limit`, `start`, and `end`. A missing `results` list gives FAILED_PARSE. A last page with no `next` value, while the record count is less than `total`, gives FAILED_INCOMPLETE_PAGINATION.

- **FR-013**: The runbook states that an empty result does not clear any open alarm.

- **FR-014**: The parse state is the set of variables that hold the fields of one event. The collector creates the variables again for each event, so a field of one event never fills a missing field of the next event.

- **FR-015**: The runbook states that each scheduled command names its environment file by an absolute path. The environment file is outside source control, and only the service account can read it.

- **FR-016**: The runbook marks each Netcool item as a proposal until the Netcool administrator approves it. The Netcool items are the delivery path, normalized record schema, field mapping, severity mapping, problem and resolution events, field rules, and delivery reliability. The runbook names no Netcool receiver. The Netcool administrator selects the probe or the interface. Each fact from IBM documentation has the mark `Verified (vendor documentation)`.

  The column definitions of `alerts.status` carry the mark `Verified (vendor documentation)`. The mapping of Mist fields to these columns carries the mark Proposal. The NOC lead approves the severity mapping (Proposal). Mist critical maps to Netcool 5 (Critical), and major maps to 4 (Major) if Mist uses it. Mist minor maps to 3 (Minor) if Mist uses it, and warn maps to 2 (Warning). Mist info maps to 2 (Warning) with type 13 and an ExpireTime.

- **FR-017**: The runbook states that a fire-and-forget webhook does not meet the delivery requirement, unless the receiver can provide durable delivery, retry, replay, or reconciliation.

  The runbook describes a durable buffer (Proposal). The buffer stores each Netcool event until the Netcool receiver confirms it. It keeps each event for at least the replay window, which is 24 hours (Proposal).

  The UAT plan stops the Netcool receiver and confirms that the buffer holds the events. It restarts the receiver and confirms the delivery. It sends a duplicate event and confirms that `Tally` increases with no new row.

- **FR-018**: The runbook lists correlation and automatic clear as enhancements that need a separate approval. The runbook recommends the hybrid design as an enhancement that needs a separate approval. In the hybrid design, webhooks deliver events with low latency. Polling handles reconciliation and replay.

- **FR-019**: The runbook lets the owners choose the device classes in scope. The Mist device types are `ap`, `switch`, `gateway`, and `mxedge`. A router in the runbook is a `gateway`.

  The default classes in scope are `ap` (device events with `device_type=ap`), rogue detection (security alarms), and Mist Edge where present. Switches and gateways are an open decision. Section 15 lists it.

- **FR-020**: The runbook uses the seven roles in the table below.

| Role | Duties |
| --- | --- |
| NOC operator | Watches Netcool, runs the procedures, and escalates. |
| NOC lead | Approves the allowlists and the alarm policy of the NOC. |
| Integration engineer | Operates the collector and the delivery path. |
| Mist administrator | Owns the Mist organizations, API tokens, and webhooks. |
| Netcool administrator | Owns the Netcool probe, rules, and automations. |
| Change approver | Approves each change outside the baseline. |
| Security owner | Owns the approved secret store and the token rotation policy. |

- **FR-021**: The runbook names only the author, Joseph Morrison, as a person. It names no customer, customer site, or customer account.

- **FR-022**: The runbook names only these products: Juniper Mist, IBM Netcool, MistHelper, mistapi, Python, PowerShell, and curl. It also names the components Mist Edge, Marvis, Netcool/OMNIbus, ObjectServer, and Netcool probes. The runbook can use the term OpenAPI, because OpenAPI is a specification format.

  The words IBM and Juniper appear only inside a product name, or as the source of vendor documentation, for example IBM documentation. This rule applies to the runbook only. Planning files can name tools and operating systems.

- **FR-023**: For other products, the runbook refers to them with generic terms, for example the legacy event manager and another monitoring tool.

- **FR-024**: The runbook uses these placeholders: `{api_host}`, `{org_id}`, `{site_id}`, `{device_mac}`, `{token}`, `{alarm_id}`, `{event_id}`, `{mxedge_id}`, `{webhook_id}`, `{start_epoch}`, and `{end_epoch}`.

- **FR-025**: Each concept has one term in the runbook. The runbook uses the term collection window, and it does not use the term time window. The runbook uses the word site for a Mist site, and it does not use the word store for a site.

- **FR-026**: The runbook starts each safety statement with Warning or Caution, and each statement gives the consequence. The runbook uses Warning for an irreversible result, and Caution for a recoverable result.

- **FR-027**: The alarm handling procedure refers to the per-alarm runbook of each alarm type, when that runbook exists. Each per-alarm runbook is in `documentation/noc-runbooks/` of the MistHelper repository, and the procedure links each one with a relative link. An alarm type without a per-alarm runbook follows the generic steps of section 11.3 and the escalation of section 11.7.

- **FR-028**: The live verification record has the UTC date in ISO 8601 form, the tool version, and the request count. The record also has a table with the columns Check, Status, and Notes, and a table with the columns Question, Answer, and Evidence.

  The second table has one row for each of the eight live questions, q1 to q8, that `design/contracts/evidence.md` defines. The record holds no identifier. A committed record holds statuses, field names, catalog names, and catalog sizes only. It holds no organization data volume.

- **FR-029**: Section 15 lists each open decision with its owner role. It lists at least the generic forms of the 22 decisions of the writer guide. It also lists the token layout for each organization and for the AP Warning report.

  It lists the Netcool receiver, the webhook signature encoding check, and the webhook redelivery behavior. The security owner names the approved secret store. The rotation interval is an open decision (Proposal: 90 days).

- **FR-055**: The runbook states that the Netcool receiver must require authentication and TLS. The IBM documentation states that the probe HTTP interface is disabled by default and does not check credentials by default. This fact carries the mark `Verified (vendor documentation)`.

- **FR-056**: The runbook gives the webhook signature check. The check computes HMAC-SHA256 over the raw body with the shared secret. It compares the result with the `X-Mist-Signature-v2` header in constant time.

  Before go-live, the runbook requires a test delivery that confirms the encoding of the header.

#### Read-only smoke test

- **FR-030**: GET is the only method that the smoke test uses. It sends no POST, PUT, PATCH, or DELETE request.

- **FR-031**: The smoke test contacts only the approved origin. The operator sets the approved origin to the regional host, for example `https://{api_host}`.

- **FR-032**: The smoke test reads the token from an environment variable or an ignored file. It does not accept the token as a command-line argument.

- **FR-033**: The smoke test sends `limit=1000` on each request that takes a limit. The `limit=5000` probe of SMK-09 is the only request above 1000. It is an explicit exception to this requirement. The probe only observes the page size behavior, and the owner can remove the exception in the review.

- **FR-034**: The run ends with the budget stop when it uses its request budget. The login token validation (one GET) counts as one request. Each client call and each client retry counts as one request. The default budget is 60 requests in one run.

  The client never reads the private `_session` attribute of the SDK. The SDK can retry HTTP 429 at most three times inside one call, and the client cannot count those retries. The evidence record holds `sdk_retry_possible: true`, so the count can omit those SDK retries.

- **FR-035**: The query ends at the page ceiling, with the stop reason `PageCeiling`. The run continues.

- **FR-036**: The smoke test validates each next link against the approved origin before it sends a request to that link.

- **FR-037**: The run ends with the unsafe paging stop when a next link returns a page that the run already read.

- **FR-038**: The mistapi SDK retries each HTTP 429 response three times, and it waits for the `Retry-After` value. The smoke test does not retry an HTTP 429 response again. The smoke test reads `Retry-After` as integer seconds only, and it records another form as not numeric. A final HTTP 429 response ends the run with the rate-limit stop. The runbook and the quickstart guide state that the SDK can sleep for the full `Retry-After` value.

  A timeout does not retry. The second timeout in one run also ends the run with the rate-limit stop. Before the search checks, the smoke test reads `GET /api/v1/self/usage` once. The run ends with the rate-limit stop when `request_limit` minus `requests` is fewer than two times the request budget. A failed usage request gives WARN, and the run continues.

- **FR-039**: The smoke test reads the HTTP status and the error body of each call before it reads any record.

- **FR-040**: The smoke test runs the ten smoke checks in the table below, in order. Each check has an identifier, and the evidence record uses that identifier. The status rules and the triggers of each check are in `design/contracts/smoke-cli.md`, section 5, subsections 5.1 to 5.10.

| Check | Title | What it proves |
| --- | --- | --- |
| SMK-01 | Configuration | The token is present and does not conflict, the host is in the regional host table, and the organization identifier is a UUID. |
| SMK-02 | Runbook structure | Each required heading exists, each Appendix A path has a GET operation in the specification file, and each Appendix B table has names. |
| SMK-03 | Token and organization access | The self endpoint returns HTTP 200. An entry with the `org_id` of the organization, or with an `msp` scope, grants the organization. An entry without an `org_id` and without an `msp` scope does not grant it. When no entry grants the organization, the check gives FAIL and the run stops with exit code 2. |
| SMK-04 | Hourly request budget | The self usage endpoint returns HTTP 200 and a request limit. The check runs before the search checks. |
| SMK-05 | Definition catalogs | Each catalog returns HTTP 200 and is not empty. Each Appendix B name exists in its catalog. The catalogs are the alarm, device event, Mist Edge event, system event, AP LED status, and webhook topic catalogs. |
| SMK-06 | Organization search | Each organization search family returns HTTP 200, a results list, the page count, and the identifier fields that the runbook names. |
| SMK-07 | Organization count | Each organization count endpoint with `distinct=type` returns HTTP 200. The check compares the totals for alarms and system events, and for device events only when the device event search was complete. |
| SMK-08 | Site scope | The four site search endpoints return HTTP 200 for one site. |
| SMK-09 | Filters and limits | A `type` filter with two device event names returns only those types, and `limit=1000` is accepted. The behavior of `limit=5000` is recorded. The device event types for `device_type=switch` and `device_type=gateway` are recorded. The start and end values of the Mist Edge event search are recorded with and without `duration=1h`. |
| SMK-10 | Inventory and webhooks | The check sends six requests. Three inventory count requests use `type=ap`, `type=switch`, and `type=gateway`, each with `distinct=model` and `limit=1000`. The device count of a type is the sum of its `count` values. The other requests read one page of Mist Edge devices, one page of organization AP statistics (records whether `last_trouble` is present), and one page of organization webhooks (records only the count, the topics, and the enabled flags). |

- **FR-041**: The smoke test compares each catalog name in Appendix B with the live catalog. It fails each check for a name that the live catalog does not hold.

- **FR-042**: The smoke test writes a redacted JSON evidence record under `test-artifacts/`, which Git ignores. The record holds check names, statuses, counts, and timestamps in UTC ISO 8601.

- **FR-043**: The evidence record uses an operator label in place of the organization identifier. It holds no token, site identifier, or MAC address.

- **FR-044**: The smoke test redacts each token at the logging boundary, so no printed output, log entry, or evidence record holds a token.

Warning: a token in an output file can cause unauthorized access to the Mist organization.

- **FR-045**: The smoke test ends with one outcome class, and each outcome class has its own exit code. The table below lists the outcome classes. The page ceiling is not a run stop. SKIP does not change the exit code, and each SKIP prints its cause. The triggers of each outcome class are in `design/contracts/smoke-cli.md`, section 3.

| Outcome class | Exit code |
| --- | --- |
| Pass | 0 |
| Check failure | 1 |
| Configuration error | 2 |
| Rate-limit stop | 3 |
| Budget stop | 4 |
| Unsafe paging stop | 5 |
| Internal error | 6 |

- **FR-046**: The smoke test prints the number of smoke checks that it examined on every run, including a failed run. A smoke check counts as examined when it runs and gives PASS, WARN, INFO, or FAIL. A SKIP result has its own count, and it prints its cause. The summary line has this form: `Checks examined: N. Passed: P. Warnings: W. Info: I. Failed: F. Skipped: S. Requests sent: R of B.` The outcome line gives the outcome class and the exit code, and the evidence path follows. A run that fails before SMK-01, for example on an invalid option or env file, also prints both lines. Its counts are zero, its outcome is the Configuration error, and its exit code is 2. The smoke test writes the evidence record only when the output path is valid.

- **FR-047**: The smoke test prints and logs ASCII text only.

- **FR-048**: The smoke test accepts a complete response with zero records as a valid result.

Caution: a smoke test run can slow other jobs that use the same token. Each run uses part of the hourly request limit of the token.

#### Offline document test

- **FR-049**: The offline document test must not need a token or a network connection.

- **FR-050**: The offline document test must compare each Mist API path in the runbook with the specification file. The runbook paths include the paths in code spans, code blocks, and tables. The test reports each path that has no GET operation in the specification file.

- **FR-051**: The offline document test must examine the runbook for UUIDs, MAC addresses, email addresses, and tokens. A token match is the word `Token` followed by a space and 20 or more letters or digits. A second token match is any run of 40 or more letters or digits, because the runbook holds written text. The evidence record uses a stricter run of 32 or more letters or digits, as `design/contracts/evidence.md`, section 7, defines. It reports each match by line number and kind, and it never prints the matched value.

- **FR-052**: The offline document test must confirm that each heading of the outline in FR-002 exists in the runbook. The headings must appear in the order of FR-002.

- **FR-053**: The offline document test must write the number of paths, headings, and lines scanned that it examines. It fails when it cannot read the runbook or the specification file.

- **FR-054**: The offline document test must belong to the unit test suite of the repository.

### Mist Cloud Transport Requirements

The smoke test uses the mistapi methods in the table below.

It sends no direct HTTP request to a Mist endpoint that a mistapi method covers. Each listed method uses GET only.

| mistapi method | Module | GET path | Smoke check |
| --- | --- | --- | --- |
| `getSelf` | `mistapi.api.v1.self.self` | `/api/v1/self` | SMK-03 token and organization access |
| `getSelfApiUsage` | `mistapi.api.v1.self.usage` | `/api/v1/self/usage` | SMK-04 hourly request budget |
| `countOrgInventory` | `mistapi.api.v1.orgs.inventory` | `/api/v1/orgs/{org_id}/inventory/count` | SMK-10 inventory count by device type |
| `searchOrgAlarms` | `mistapi.api.v1.orgs.alarms` | `/api/v1/orgs/{org_id}/alarms/search` | SMK-06 alarm endpoint family |
| `countOrgAlarms` | `mistapi.api.v1.orgs.alarms` | `/api/v1/orgs/{org_id}/alarms/count` | SMK-07 alarm count |
| `searchOrgDeviceEvents` | `mistapi.api.v1.orgs.devices` | `/api/v1/orgs/{org_id}/devices/events/search` | SMK-06 and SMK-09 device event endpoint family |
| `countOrgDeviceEvents` | `mistapi.api.v1.orgs.devices` | `/api/v1/orgs/{org_id}/devices/events/count` | SMK-07 device event count |
| `searchOrgMistEdgeEvents` | `mistapi.api.v1.orgs.mxedges` | `/api/v1/orgs/{org_id}/mxedges/events/search` | SMK-06 and SMK-09 Mist Edge event endpoint family |
| `countOrgSiteMxEdgeEvents` | `mistapi.api.v1.orgs.mxedges` | `/api/v1/orgs/{org_id}/mxedges/events/count` | SMK-07 Mist Edge event count |
| `searchOrgSystemEvents` | `mistapi.api.v1.orgs.events` | `/api/v1/orgs/{org_id}/events/system/search` | SMK-06 system event endpoint family |
| `countOrgSystemEvents` | `mistapi.api.v1.orgs.events` | `/api/v1/orgs/{org_id}/events/system/count` | SMK-07 system event count |
| `searchSiteAlarms` | `mistapi.api.v1.sites.alarms` | `/api/v1/sites/{site_id}/alarms/search` | SMK-08 site alarm search |
| `searchSiteDeviceEvents` | `mistapi.api.v1.sites.devices` | `/api/v1/sites/{site_id}/devices/events/search` | SMK-08 site device event search |
| `searchSiteMistEdgeEvents` | `mistapi.api.v1.sites.mxedges` | `/api/v1/sites/{site_id}/mxedges/events/search` | SMK-08 site Mist Edge event search |
| `searchSiteSystemEvents` | `mistapi.api.v1.sites.events` | `/api/v1/sites/{site_id}/events/system/search` | SMK-08 site system event search |
| `listOrgSites` | `mistapi.api.v1.orgs.sites` | `/api/v1/orgs/{org_id}/sites` | SMK-08 site list |
| `listOrgDevicesStats` | `mistapi.api.v1.orgs.stats` | `/api/v1/orgs/{org_id}/stats/devices` | SMK-10 organization AP statistics |
| `listOrgWebhooks` | `mistapi.api.v1.orgs.webhooks` | `/api/v1/orgs/{org_id}/webhooks` | SMK-10 organization webhooks |
| `listOrgMxEdges` | `mistapi.api.v1.orgs.mxedges` | `/api/v1/orgs/{org_id}/mxedges` | SMK-10 Mist Edge page |
| `listAlarmDefinitions` | `mistapi.api.v1.const.alarm_defs` | `/api/v1/const/alarm_defs` | SMK-05 alarm catalog |
| `listDeviceEventsDefinitions` | `mistapi.api.v1.const.device_events` | `/api/v1/const/device_events` | SMK-05 device event catalog |
| `listMxEdgeEventsDefinitions` | `mistapi.api.v1.const.mxedge_events` | `/api/v1/const/mxedge_events` | SMK-05 Mist Edge event catalog |
| `listSystemEventsDefinitions` | `mistapi.api.v1.const.system_events` | `/api/v1/const/system_events` | SMK-05 system event catalog |
| `listApLedDefinition` | `mistapi.api.v1.const.ap_led_status` | `/api/v1/const/ap_led_status` | SMK-05 access point LED catalog |
| `listWebhookTopics` | `mistapi.api.v1.const.webhook_topics` | `/api/v1/const/webhook_topics` | SMK-05 webhook topic catalog |

The contract tests produce this evidence:

| Contract area | Evidence |
| --- | --- |
| SDK insufficiency | A test shows that an empty SDK list hides a rejected request, and that the smoke test detects the rejection from the HTTP status. |
| SDK authentication | A test shows that a run without a token stops before it sends any request. |
| SDK endpoint parity | An offline test shows that each method in the table maps to a GET path in the specification file. |
| Failure safety | A test shows that a failed smoke check still writes the evidence record and ends with its outcome class. |
| Secret redaction | A test shows that the token value does not appear in printed output, log entries, or the evidence record. |

### Mist API Operations

The entries below describe each GET operation of the transport table. Each entry gives its operationId, its mistapi SDK module, and its GET path.

- **operationId**: `getSelf`
- **mistapi SDK module**: `mistapi.api.v1.self.self`
- **GET path**: `/api/v1/self`

- **operationId**: `getSelfApiUsage`
- **mistapi SDK module**: `mistapi.api.v1.self.usage`
- **GET path**: `/api/v1/self/usage`

- **operationId**: `countOrgInventory`
- **mistapi SDK module**: `mistapi.api.v1.orgs.inventory`
- **GET path**: `/api/v1/orgs/{org_id}/inventory/count`

- **operationId**: `searchOrgAlarms`
- **mistapi SDK module**: `mistapi.api.v1.orgs.alarms`
- **GET path**: `/api/v1/orgs/{org_id}/alarms/search`

- **operationId**: `countOrgAlarms`
- **mistapi SDK module**: `mistapi.api.v1.orgs.alarms`
- **GET path**: `/api/v1/orgs/{org_id}/alarms/count`

- **operationId**: `searchOrgDeviceEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.devices`
- **GET path**: `/api/v1/orgs/{org_id}/devices/events/search`

- **operationId**: `countOrgDeviceEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.devices`
- **GET path**: `/api/v1/orgs/{org_id}/devices/events/count`

- **operationId**: `searchOrgMistEdgeEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.mxedges`
- **GET path**: `/api/v1/orgs/{org_id}/mxedges/events/search`

- **operationId**: `countOrgSiteMxEdgeEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.mxedges`
- **GET path**: `/api/v1/orgs/{org_id}/mxedges/events/count`

- **operationId**: `searchOrgSystemEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.events`
- **GET path**: `/api/v1/orgs/{org_id}/events/system/search`

- **operationId**: `countOrgSystemEvents`
- **mistapi SDK module**: `mistapi.api.v1.orgs.events`
- **GET path**: `/api/v1/orgs/{org_id}/events/system/count`

- **operationId**: `searchSiteAlarms`
- **mistapi SDK module**: `mistapi.api.v1.sites.alarms`
- **GET path**: `/api/v1/sites/{site_id}/alarms/search`

- **operationId**: `searchSiteDeviceEvents`
- **mistapi SDK module**: `mistapi.api.v1.sites.devices`
- **GET path**: `/api/v1/sites/{site_id}/devices/events/search`

- **operationId**: `searchSiteMistEdgeEvents`
- **mistapi SDK module**: `mistapi.api.v1.sites.mxedges`
- **GET path**: `/api/v1/sites/{site_id}/mxedges/events/search`

- **operationId**: `searchSiteSystemEvents`
- **mistapi SDK module**: `mistapi.api.v1.sites.events`
- **GET path**: `/api/v1/sites/{site_id}/events/system/search`

- **operationId**: `listOrgSites`
- **mistapi SDK module**: `mistapi.api.v1.orgs.sites`
- **GET path**: `/api/v1/orgs/{org_id}/sites`

- **operationId**: `listOrgDevicesStats`
- **mistapi SDK module**: `mistapi.api.v1.orgs.stats`
- **GET path**: `/api/v1/orgs/{org_id}/stats/devices`

- **operationId**: `listOrgWebhooks`
- **mistapi SDK module**: `mistapi.api.v1.orgs.webhooks`
- **GET path**: `/api/v1/orgs/{org_id}/webhooks`

- **operationId**: `listOrgMxEdges`
- **mistapi SDK module**: `mistapi.api.v1.orgs.mxedges`
- **GET path**: `/api/v1/orgs/{org_id}/mxedges`

- **operationId**: `listAlarmDefinitions`
- **mistapi SDK module**: `mistapi.api.v1.const.alarm_defs`
- **GET path**: `/api/v1/const/alarm_defs`

- **operationId**: `listDeviceEventsDefinitions`
- **mistapi SDK module**: `mistapi.api.v1.const.device_events`
- **GET path**: `/api/v1/const/device_events`

- **operationId**: `listMxEdgeEventsDefinitions`
- **mistapi SDK module**: `mistapi.api.v1.const.mxedge_events`
- **GET path**: `/api/v1/const/mxedge_events`

- **operationId**: `listSystemEventsDefinitions`
- **mistapi SDK module**: `mistapi.api.v1.const.system_events`
- **GET path**: `/api/v1/const/system_events`

- **operationId**: `listApLedDefinition`
- **mistapi SDK module**: `mistapi.api.v1.const.ap_led_status`
- **GET path**: `/api/v1/const/ap_led_status`

- **operationId**: `listWebhookTopics`
- **mistapi SDK module**: `mistapi.api.v1.const.webhook_topics`
- **GET path**: `/api/v1/const/webhook_topics`

### Key Entities

- **Mist organization**: A tenant of the Juniper Mist cloud. The feed reads each Mist organization by its identifier and its regional host.

- **Specification file**: A file in `documentation/` that lists each path and HTTP method of the Mist API.

- **Endpoint family**: One of the four search families of an organization: alarms, device events, Mist Edge events, and system events. Each endpoint family has its own collection window and pagination rules.

- **Collection window**: The time range that one poll reads. It ends a short time before the current time, and it overlaps the previous collection window.

- **Checkpoint**: The end time of the last collection window that completed for one Mist organization and one endpoint family. Only `SUCCESS_WITH_RECORDS` and `SUCCESS_EMPTY` can advance a checkpoint.

- **Healthy feed**: At the start of a shift, each Mist organization and each endpoint family has a `SUCCESS_WITH_RECORDS` or `SUCCESS_EMPTY` state within the last two poll intervals. The delivery backlog is zero.

- **Collection result state**: The outcome of one collection. Each collection has one of nine states: `SUCCESS_WITH_RECORDS`, `SUCCESS_EMPTY`, `FAILED_HTTP`, `FAILED_AUTH`, `FAILED_THROTTLED`, `FAILED_PARSE`, `FAILED_INCOMPLETE_PAGINATION`, `FAILED_DELIVERY`, and `PARTIAL_ORGANIZATION`. The collector design uses these states. The smoke test does not use them.

- **Normalized record**: One Mist record in one common shape. The feed creates each normalized record before it creates a Netcool event.

- **Netcool event**: One event that the feed sends to a Netcool probe. Each Netcool event carries the fields of one normalized record and a deduplication key.

- **Smoke check**: One named check inside the smoke test. It has a status, a count of requests, and a short result message.

- **Evidence record**: The redacted JSON file that the smoke test writes under `test-artifacts/`. It holds the results of each smoke check and no token.

### Out of Scope

- A production collector or any scheduled job. A later feature covers each one.

- Any change to the Mist configuration or the Netcool configuration.

- Any write request to the Mist API, including POST, PUT, PATCH, and DELETE.

- Any change to the code of the AP Warning report (menu 307).

- Any build of correlation or automatic clear. The runbook describes each one as an enhancement only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The runbook scores 80 or more on the STE gate in both modes, with and without the licensed dictionary.

- **SC-002**: The runbook contains no broken relative links and no broken heading anchors.

- **SC-003**: 100 percent of the Mist API paths in the runbook have a GET operation in the specification file. The paths in code spans, code blocks, and tables count too.

- **SC-004**: 100 percent of the catalog names in Appendix B exist in the live catalogs, as shown by a final smoke test run. The final run reaches SMK-05 and reports PASS for each Appendix B name check. A run that has a run stop before SMK-05 does not satisfy this criterion. The final run shows no SKIP for SMK-02 or for an Appendix B name check.

- **SC-005**: GET is the only method of the smoke test, and the counted requests never exceed the request budget.

- **SC-006**: The offline scan finds no customer identifier in the runbook. A customer identifier is any value that identifies a customer, a site, a device, or a person of a customer.

  It includes each organization ID, site ID, device MAC address, device serial, device name, site name, and customer name. It also includes each person name of a customer, each email address, and each token. The offline scan checks the pattern classes UUID, MAC address, email address, and token. A separate name check uses a term list that is never committed.

- **SC-007**: Each edge case in this specification has a unit test that fails when the behavior is absent.

- **SC-008**: The new code and tests add no test quality findings to the baseline.

- **SC-009**: The runbook contains an answer section for each question of the integration team. Question 1 maps to sections 6 and 7, and question 2 maps to section 10. Question 3 maps to sections 4.4 and 8.4, and question 4 maps to section 12.2.

  Question 5 maps to sections 7.2 and 12.4, and question 6 maps to section 12.3. The host and network checks map to sections 5.4, 5.5, 12.2, and 12.5.

- **SC-010**: The smoke test prints the number of checks examined on 100 percent of its runs, including failed runs. The outcome line prints the outcome class and the exit code on each run.

## Assumptions

- The owner merges the pull request. The feature does not merge itself.

- Each Netcool item in the runbook is a proposal until the Netcool administrator approves it. The facts from IBM documentation are the exception.

- The live verification uses the credentials that the author holds, and the runbook records no identifier.

- The default request budget is 60 requests for each smoke test run, and the login token validation counts as one of them. The owner can change this value.

- The default page ceiling is 3 pages for each query. The owner can change this value with the `--max-pages` option.

- The smoke test retries an HTTP 5xx response or a connection failure at most two times. The owner can change this value.

- The collection window end lag and the collection window overlap are proposals until the live verification confirms them.

- The approved origin is the regional host that the operator sets. The smoke test rejects every other origin.

- The runbook describes the AP Warning report (menu 307) as the repository code and documents show it on 2026-11-25.

- The specification file in the repository is current for this feature.

- The author and technical contact for Mist questions is Joseph Morrison.

- The production collector is a later feature. This feature delivers the runbook, the smoke test, and the offline document test only.
