# Research: WiFi Pagination Failure Handling

## Decision: Follow pages with the SDK page method

**Decision**: Use `mistapi.get_next` to request each page while the current response has a next-page link.

**Rationale**: The installed SDK implementation of `mistapi.get_all` keeps its accumulated rows in a local variable. A later request exception prevents that variable from reaching the caller. The method also appends data from later responses without checking their HTTP status.

**Alternatives considered**:

- Keep `mistapi.get_all`: rejected because it loses rows after a later exception and accepts later HTTP error payloads.
- Send direct HTTP requests: rejected because the repository requires the `mistapi` SDK for Mist requests.

## Decision: Classify each page before adding its records

**Decision**: Check every returned page status and body before adding its records. Reject HTTP errors. For a transport exception after a successful page, keep collected records and mark the result partial.

**Rationale**: The WiFi exporter must distinguish a complete empty result from a failed or partial read. The page status provides direct evidence of a failed HTTP response.

**Alternatives considered**:

- Treat every failed page as an empty result: rejected because it can create a false no-data placeholder.
- Export a later HTTP error as partial data: rejected because issue #4656 requires rejection, not success-shaped output.
- Discard all rows after a later timeout: rejected because issue #4657 requires retaining successful earlier pages.

## Decision: Reuse the repository's offline SDK response fixtures

**Decision**: Build real `mistapi.APIResponse` objects from controlled `requests.Response` objects and serve later pages through a controlled session.

**Rationale**: `tests/support/sdk_pages.py` already builds native SDK responses and records later-page links without network access. This exercises SDK response parsing and pagination while keeping tests offline.

**Alternatives considered**:

- Mock `mistapi.get_all` only: rejected because that would not prove the observed SDK pagination behavior.
- Call the Mist cloud: rejected because the task forbids live requests and credentials.

## Resolved Technical Questions

- The SDK methods are `searchSiteWirelessClients` and `searchSiteWirelessClientSessions`.
- The SDK method `get_next` accepts the authenticated session and the previous response, then calls the session's `mist_get` method with the SDK-created page link.
- Tests use the actual SDK response objects and SDK page method with controlled sessions. They do not use credentials or live HTTP or socket connections.
- Logs report the page label, site identifier, failure class, and retained count where needed. Logs do not include response bodies or credentials.
