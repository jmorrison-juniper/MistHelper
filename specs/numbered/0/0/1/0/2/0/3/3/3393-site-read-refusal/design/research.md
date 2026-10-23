# Research: Site read refusal

## Decision

Use 503 for connection failures and timeouts from the site read.
Catch the save failure before any session write.
Protect only the `selected_rows` call in each page route.

## Rationale

Current `main` is `9991d30a1`.
The issue assessment still matches all three affected calls.
Sibling cloud-status failures already return 503.
The existing browser script reopens form controls after an error without clearing values or navigating.
The site list read precedes aggregate plan construction and persistence.

## Alternatives considered

- Status 502 would differ from the sibling cloud-failure convention.
- A blueprint-wide transport handler would change unrelated routes.
- A reader change would affect other callers and exceed the issue scope.
- Saving rejected options would create unvalidated state and unnecessary cookie growth.

## Evidence limits

The artifact list endpoint returns HTTP 404. No issue artifact was available.
The issue body and all comments contain no required image.
All 11 open pull requests had no matching path ownership before implementation.
The two existing contract modules passed all 96 tests before the repair.
PowerShell was absent. An ignored local PowerShell installation resolved the managed route.
