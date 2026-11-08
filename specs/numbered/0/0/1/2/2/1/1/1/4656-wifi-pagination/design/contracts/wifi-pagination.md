# WiFi Pagination Contract

## Request Boundary

- The client sequence begins with `searchSiteWirelessClients`.
- The session sequence begins with `searchSiteWirelessClientSessions`.
- Later pages use the SDK page link and the same authenticated Mist session.
- Tests use controlled `APIResponse` objects and controlled sessions. Tests make no live Mist request.

## Page Rules

1. Reject a first-page HTTP failure before pagination.
2. Add records only after each page passes its status and payload checks.
3. If a later transport request raises after a successful page, retain earlier records and mark the dataset partial.
4. If a later page returns an HTTP failure, reject the run and do not export a placeholder or complete-looking dataset.
5. If all pages succeed, preserve the current complete or valid-empty behavior.

## Required Evidence

- Demonstrate why `mistapi.get_all` loses accumulated records when a later request raises.
- Demonstrate why `mistapi.get_all` can accept a later HTTP 403 or 503 response without checking its status.
- Exercise the real SDK `get_next` page call with a controlled session.
- Verify that the existing API endpoint names and authenticated session reach each request.
- Verify complete multi-page results, a timeout after a successful page, later HTTP 403 and 503, first-page errors, and valid-empty results.
- Verify that logs do not include credentials, response bodies, or secret values.
