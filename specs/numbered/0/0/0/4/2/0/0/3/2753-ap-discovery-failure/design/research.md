# AP discovery research

## Decision

Keep the original pagination exception and remove the response-data fallback.

## Evidence

The current helper catches every `mistapi.get_all` exception.
It then reads `getattr(sites_response, "data", []) or []`.
Absent data becomes an empty collection.
Populated data becomes an incomplete site scan.
The migration caller treats an empty result as nothing to migrate.

The installed SDK reads `response.data` before pagination.
A missing attribute can raise before a site collection exists.
A later page can also raise after the first page exists.

## Alternatives

Do not retain a test-only response fallback in production.
Do not convert the failure to an empty collection or add a retry.
Do not change the separate per-site device-read exception boundary.

## Ownership

PR #4503 owns the address utility candidate.
No open pull request names this source or test.
The #2753 reservation names both exact paths.
Active #2861 and #2863 claims remain outside this repair.
