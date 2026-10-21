# Mist API Contract: MistCircuitStats Redis Dashboard Migration

**Status**: Approved collection boundary. This planning PR adds no product requests.

## Existing SDK Evidence

Merged PR #4252 provides the shared MistHelper `mistapi` session, SDK collection, and contract tests. The #4220 worker will use only the four existing bulk, paginated reads listed below.

| SDK method | API scope | Use |
|---|---|---|
| `listOrgSites` | Organization sites | Read sites for the active organization |
| `listOrgDevicesStats` | Organization device statistics | Read gateway state and statistics |
| `searchOrgSwOrGwPorts` | Organization switch and gateway ports | Read port pages, then select WAN rows |
| `getOrgInventory` | Organization inventory | Read gateway profile and template references |

The current page limit is 1,000. Reuse the existing #4252 pagination and request-admission path. Do not add source per-site or per-port request loops.

## Excluded SDK Operations

The following request classes are outside this migration:

- Source-specific per-port Insights requests. Issue #4330 tracks that contract.
- Per-device reads used by the current #4252 detail service.
- Per-site or per-port request loops copied from MistCircuitStats-Redis.
- Direct HTTP requests or manual token-header extraction.

Dashboard routes make no Mist API request. When the shared cache lacks a requested value, the route reports unavailable data.

## Request Rules

- Use the existing MistHelper `mistapi` session and active organization.
- Use explicit arguments for each of the four approved methods.
- Keep page size at 1,000 and follow only the existing SDK pagination path.
- Route every admitted request through the existing shared request-admission path.
- Count each admitted SDK request during the production-scale load test.
- Do not retry without the existing shared retry and admission policy.
- Do not log tokens, authorization headers, cookies, or raw sensitive responses.
- On an API error, rate limit, timeout, or incomplete page, stop publication, preserve the last complete snapshot as stale, and show a safe refresh error.
- Never publish partial data. Report unavailable data when no unexpired complete snapshot exists.
- Do not call Mist unless the current Gunicorn process holds the renewable Redis worker lease.
- Show the active SDK read phase and completed page counts without exposing sensitive response data.

## Rate and Load Contract

Current Mist documentation states a limit of 5,000 API calls per hour per token. The limit is shared with other MistHelper requests.

The user supplied production bands of 1,001–5,000 sites, 1,001–5,000 gateways, and 5,001–20,000 WAN ports. The rough estimate is 12–35+ requests per full refresh for four bulk reads with page size 1,000. Additional non-WAN port pages may increase the count. This is an estimate, not a measured result.

Do not select a refresh interval from this estimate. A production-scale load test must measure every page, other shared token use, refresh duration, concurrency, and failure recovery before the worker schedule and lease are set.

## Required Tests Before Product Acceptance

1. Prove that the worker calls only the four approved SDK methods.
2. Prove that every page uses the shared admission path and the 1,000-row limit.
3. Prove that duplicate, incomplete, repeated, and interrupted pages cannot publish a partial snapshot and preserve the last complete snapshot as stale.
4. Simulate rate limits, timeouts, HTTP 4xx and 5xx errors, and malformed responses.
5. Prove that dashboard route reads make zero Mist SDK calls.
6. Prove that logs and errors redact credentials and sensitive response values.
7. Prove that a process without the Redis lease makes no Mist request.
8. Measure total API calls across the stated production bands before selecting a refresh interval or lease duration.

## Lab Caveat

A read-only development lab query returned 67 port rows, 7 WAN rows, and 2 gateway MACs. The SDK also logged a token-validation error during startup despite a successful endpoint response. These observations are not production evidence. Resolve or explain the diagnostic before using the lab result as authentication evidence.
