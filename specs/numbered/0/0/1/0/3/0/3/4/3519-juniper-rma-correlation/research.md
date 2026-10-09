# Research: Juniper RMA Correlation

**Feature**: `3519-juniper-rma-correlation` | **Date**: 2026-10-08

Each decision lists the choice, the reason, and the rejected options. Open items link to the onboarding list in [plan.md](plan.md).

## R-01: HTTP transport

- **Decision**: Use `requests.Session` with explicit timeouts, `allow_redirects=False`, and a bounded response size.
- **Rationale**: `requests` is already a dependency. The capture downloader uses it for vendor URLs. It gives direct control of redirects and TLS verification.
- **Alternatives rejected**: `httpx` is used only by the separate `mist-ops-platform` package. `urllib` offers no retry control.

## R-02: Credential model

- **Decision**: Use OAuth 2.0 client credentials. Request a bearer token from the token endpoint with the client ID and secret. Cache the token until it nears expiry. Send `Authorization: Bearer <token>` on each call. Only `JuniperTokenProvider` reads the client secret.
- **Rationale**: The endpoints document names OAuth2.0 as the authentication mechanism and lists no API key. It gives the token endpoint `invoke/pub.apigateway.oauth2/getAccessToken` and a token lifetime of 3600 seconds. Keeping the secret in one class limits its exposure.
- **Alternatives rejected**: An API key header, because the document lists none. A client certificate on port 8443, because the document does not require it for this client.

## R-03: Request identifier

- **Decision**: Generate `uuid.uuid4().hex` for each attempt. The result has 32 letters and digits.
- **Rationale**: The Case export lists 40 characters for `customerCaseNumber` and `customerSourceID`. The Asset export fault 986 requires alphanumeric characters only. A 32-character lowercase hex value meets both rules. A new value on each retry avoids fault 955 (duplicate identifier).
- **Alternatives rejected**: A hyphenated UUID breaks the Asset API rule. A reused identifier triggers fault 955 on retry.

## R-04: Request timestamp

- **Decision**: Format `requestDateTime` in UTC with milliseconds and a `Z` suffix. Example: `2026-10-08T14:03:22.123Z`.
- **Rationale**: Fault 903 rejects any other format.
- **Alternatives rejected**: Local time with an offset is not accepted by the documented format.

## R-05: Join rule (Clarification 1)

- **Decision**: A Mist ticket matches a Juniper service request when the request's `customerCaseNumber` equals the value of the Mist ticket field named by `JUNIPER_TICKET_KEY_FIELD`. The default field is `case_number`. The other allowed field is `id`. The comparison trims spaces and is case-sensitive. One match is a matched link. Two or more matches make the ticket ambiguous, and the engine does not choose. No match makes the ticket unmatched. Fault 763 also makes the ticket ambiguous.
- **Rationale**: The Case export describes `customerCaseNumber` as the "Customer Tracking Number" (40 characters). The Mist API reference describes `case_number` as the display name of the ticket. It describes `id` as the ticket identifier. Neither reference says which value Juniper stores. Onboarding confirms the field with one known pair. Fault 763 confirms that one case number can map to more than one request.
- **Alternatives rejected**: A derived case number needs a transform rule that nobody has written. Parsing ticket comments for request numbers is free text and gives false positives. Hard-coding one field before onboarding risks zero matches.

## R-06: Discovery window

- **Decision**: Run one list call (`querysrlist`) for the last 90 days. For each ticket older than 90 days, run one detail call (`querysrdetails`) with its case number.
- **Rationale**: The list call returns requests from the last 90 days only. The Case export lists `customerCaseNumber` as an identifier type of the detail call. Fault 956 says a request needs a request number or a case number. Fault 763 describes a case-number lookup that matches one request (O-4). The list filter field names are not documented, so the engine filters on the client side.
- **Alternatives rejected**: Server-side filtering on `caseFilter` (field names unknown). Dropping older tickets (loses valid matches).

## R-07: Response outcome

- **Decision**: The body `statusCode` decides the outcome. `200` means success. `300` means a warning, and the result is kept. `400` means a fault, and the result is empty. The HTTP status decides only the transport outcome. An HTTP `3xx` is never followed. It is reported as unexpected.
- **Rationale**: The export defines body codes 200, 300, and 400. An HTTP `300` would otherwise be read as a redirect.
- **Alternatives rejected**: Reading the HTTP status alone hides the warning and fault codes.

## R-08: Fault meaning map

- **Decision**: Keep a static table in `messages.py` for the codes listed in `contracts/juniper-case-api.md` and `contracts/juniper-asset-api.md`. Show the code, the meaning, and the endpoint name. Show raw messages only for unknown codes.
- **Rationale**: Operators need plain text. The export gives the meaning for each code.
- **Alternatives rejected**: Showing only the raw code leaves operators with no next step.

## R-09: Parsing variants

- **Decision**: Accept each variant that the export documents:
  - `rmaInfo` as one object or as a list.
  - `warranty` and `serviceContract` as lists.
  - Asset results under a `data` object or at the top level.
  - Shipping address fields as a nested `address` object or as flat fields.
  - Malformed timestamps such as `2017-09-05-T12:57:00.000Z` and `2017:09:12T17:37:30.000Z`. Keep the raw text when parsing fails.
- **Rationale**: The export examples and schemas disagree in these places (O-5 to O-7).
- **Alternatives rejected**: One strict shape would fail on the first real response that differs.

## R-10: Rate limit

- **Decision**: Use a token bucket on `time.monotonic()`. The default is 2 requests per second. `JUNIPER_MAX_REQUESTS_PER_SECOND` changes it within the range 0.5 to 10.
- **Rationale**: Neither export states a request rate (O-3). A conservative default protects the account.
- **Alternatives rejected**: A fixed sleep between calls wastes time when responses are fast.

## R-11: Retry policy

- **Decision**: Retry connection errors, timeouts, and HTTP 429, 502, 503, and 504. Allow up to three attempts. Wait 2 seconds, then 4 seconds. Never retry a fault in a response body.
- **Rationale**: These statuses are temporary by definition. A body fault repeats on every retry.
- **Alternatives rejected**: Retrying faults wastes quota. Retrying forever stalls a run.

## R-12: Timeouts and size limit

- **Decision**: Connect timeout 10 seconds. Read timeout 60 seconds. Response size limit 16 MB, checked while streaming.
- **Rationale**: The export gives payload sizes up to about 8 MB. A limit above that protects memory without rejecting valid responses.
- **Alternatives rejected**: No size limit allows one bad response to exhaust memory.

## R-13: TLS trust

- **Decision**: Verify TLS by default. Read an optional `JUNIPER_CA_BUNDLE` path and pass it as `verify`. Reuse the corporate overlay `deploy/compose.corporate-ca.yml` in the container. Check whether the system CA bootstrap from spec 3302 covers `requests`. Use `JUNIPER_CA_BUNDLE` if it does not.
- **Rationale**: `requests` uses its own CA bundle by default. A corporate root certificate is missing from that bundle unless the setting points at a bundle that includes it.
- **Alternatives rejected**: Disabling verification exposes the API key to interception.

## R-14: Personal data (Clarification 2)

- **Decision**:
  - Keep personal fields in full in every export. The CSV files, SQLite, and the optional ArangoDB mirror receive the same full rows (amendment A-3, amended 2026-10-08).
  - Mask every personal column in each log line. The column table is `LOG_MASKS` in `src/operations/exporting/juniper_rma/model/export_rows.py`. It covers the names, the e-mail addresses, the telephone numbers, the street lines, and the free text. The telephone country code stays visible.
  - Log masking format: a name keeps its first letter. An email keeps its first letter and its domain. A telephone number keeps its last two digits. A street line becomes `[masked]`.
  - Delete the export files that hold personal fields when they are older than `JUNIPER_PII_RETENTION_DAYS`. The purge runs at the start of each run (amendment A-3).
  - Do not store notes, attachments, linked references, or the free-text problem description.
- **Rationale**: Operators need the shipping view and the names in the exports. The log masking keeps the run log safe.
- **Alternatives rejected**: Storing nothing removes the shipping detail the feature exists to show. Masked exports hid the names and e-mail addresses that the operator needs (2026-10-08).

## R-15: Storage and keys

- **Decision**: Write every export through `DataExporter.write_with_format_selection()`. Add these strategies to `ENDPOINT_PRIMARY_KEY_STRATEGIES`. The table lists each strategy and its key.

| Strategy | Key type | Key fields |
| - | - | - |
| `juniperQuerySrList`, `juniperQuerySrDetails` | Natural | Request number |
| `juniperQueryRmaDetails` | Composite | RMA number, item type, item number |
| `juniperQueryAssetsDetails` | Natural | Serial number |
| `juniperQueryAssetCoverage` | Composite | Serial number, coverage kind, index, contract line item (amendment A-4) |
| `juniperCorrelationLinks` | Composite | Mist ticket key value, request number |
| `juniperRunRecords` | Auto | Unique run ID |

- **Rationale**: The constitution requires natural keys and `DataExporter`. The strategy type names follow the code, which uses `auto_pk` rather than the constitution's older label.
- **Alternatives rejected**: Artificial IDs break the natural-key rule. Writing files without `DataExporter` breaks the output rule.

## R-16: Mist ticket listing

- **Decision**: Read tickets with the same `listOrgTickets` call that menu 188 uses, with `duration="365d"`. Resolve the organization with `ConfigUtils.get_cached_or_prompted_org_id()`. Use only `id`, `case_number`, `status`, `subject`, and `created_at` in the export.
- **Rationale**: Reusing the call keeps one code path for Mist tickets. Ticket comments can hold personal data, so the export excludes them.
- **Alternatives rejected**: A new Mist call duplicates the existing path.

## R-17: Menus and registry

- **Decision**: Register menus 301 to 304 in `OperationRegistry` with category `interactive_safe` and a skip reason that names the Juniper settings. Confirm the next free numbers with `OperationRegistry.registered_options()`. A runtime guard refuses live calls under `--test` and `--testinteractive` unless `JUNIPER_LIVE_TESTS=1`.
- **Rationale**: FR-032 forbids live calls in automated runs. The runtime guard makes the rule explicit, not dependent on the category alone.
- **Alternatives rejected**: The `safe` category would run the live calls in every `--test` run.

## R-18: Test strategy

- **Decision**: Build fixtures from the examples in the two exports. A fake gateway replays the fixtures. Tests assert the envelope keys, the identifier format, the timestamp format, the parser variants, the masking, and the correlation outcomes. A boundary test fails if any write operation name appears in the client. The live smoke test is opt-in.
- **Rationale**: The feature can be built and tested before onboarding ends. The fixtures show the exact shapes that the parsers must accept.
- **Alternatives rejected**: Live-only tests block development on onboarding.

## R-19: Layout and the five-item rule

- **Decision**: Place source code in `src/operations/exporting/juniper_rma/`. Split it into nested packages so that each directory holds five or fewer children. Place tests in `tests/unit/juniper_rma/` and record the debt in C-1.
- **Rationale**: `src/` holds four domain packages, and its guard allows no other direct child. `src/operations/exporting/` holds one child and can take one more.
- **Alternatives rejected**: A new top-level `src/juniper_rma/` package violates the rule. Tests in an existing package would make that package larger than five children.

## R-20: Logging

- **Decision**: Use `structlog` in each new module. Escape non-ASCII values with `ascii()` before they reach a log line. Log the configured or missing state of a secret, never its value. Do not hash a secret to make a log label.
- **Rationale**: Principle V requires structured, ASCII-only logs. The CodeQL rule `py/weak-sensitive-data-hashing` flags fast hashes of credentials.
- **Alternatives rejected**: A short hash of the key still leaks the key's identity to anyone with the log file.
