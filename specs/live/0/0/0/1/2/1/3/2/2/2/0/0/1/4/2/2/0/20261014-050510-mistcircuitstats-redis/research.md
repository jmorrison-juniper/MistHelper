# Research: MistCircuitStats Redis Dashboard Migration

**Date**: 2026-10-20
**Status**: Planning decisions are approved. Product implementation may proceed with a fail-closed refresh schedule and lease duration.

## Current State

- Issue #4220 remains open. Planning PR #4223 merged on 2026-10-17.
- PR #4252 merged on 2026-10-16. It delivered the canonical WAN dashboard, shared SDK collection, and Redis cache, and closed #4195.
- Issue #4200 remains open. Draft PR #4208 remains a proposal. Do not edit its files or treat its code as merged behavior.
- The source repository is `jmorrison-juniper/MistCircuitStats-Redis`. The reviewed source revision is `61153fcb8dc51c6c7ff41a46179ef376d9da7601`.
- The source `LICENSE` declares CC BY-NC-SA 4.0. The source owner authorized reuse with documented attribution. Keep the source identity, revision, and license with every reused artifact.
- This planning PR contains no copied source code, tests, fixtures, screenshots, or assets.

## Evidence from the Merged Dashboard

The existing service is `src/interfaces/portals/wan_dashboard/services.py`. Its organization overview uses these four bulk SDK reads with pagination:

| SDK method | Use |
|---|---|
| `listOrgSites` | Read organization sites |
| `listOrgDevicesStats` | Read gateway status and statistics |
| `searchOrgSwOrGwPorts` | Read organization port records before filtering WAN rows |
| `getOrgInventory` | Read gateway profile and template references |

The existing code also has detail methods that make additional SDK calls. The #4220 refresh worker will use only the four bulk reads above. It will not port source per-site or per-port request loops. Source-specific per-port Insights parity is excluded and tracked in [issue #4330](https://github.com/jmorrison-juniper/MistHelper/issues/4330).

Merged PR #4252 uses the existing `wan-dashboard:v1:` cache. Its TTLs are 300 seconds for site data, 600 seconds for entity data, and 86,400 seconds for stale data. Keep these values and keys unchanged.

## Load and Rate Evidence

Current Mist API documentation states a limit of 5,000 API calls per hour per token. This is a shared limit. Other MistHelper work also uses the token, so the worker must use shared request admission.

The user's production bands are:

| Dataset | Production band |
|---|---:|
| Sites | 1,001–5,000 |
| Gateways | 1,001–5,000 |
| WAN ports | 5,001–20,000 |

The user's rough estimate is 12–35+ requests per full refresh for the four bulk reads at a page size of 1,000. Additional non-WAN port pages may increase this count. This is an estimate, not a measured production result.

Do not select a refresh interval from this estimate. Run a production-scale load test that measures all pages, shared token usage, complete refresh time, concurrent request behavior, and failure recovery. Derive the renewable worker lease from measured refresh and recovery times. Record the test result before selecting either value.

## Lab Evidence and Limitation

A read-only development lab query returned 67 port rows, 7 WAN rows, and 2 gateway MACs. This response is useful for a basic data-shape review. It does not represent the stated production bands.

The SDK logged a token-validation error during startup even though an endpoint returned a successful response. Do not treat that response as proof that SDK token validation works. Resolve or explain this diagnostic before using the lab to assess authentication behavior. This record includes no credentials or device identifiers.

## Source Settings and License

The source guide describes a 300-second worker interval and a cache TTL equal to three intervals. The reviewed worker sets four parallel workers, a 300-second interval, a 600-second stale threshold, and a 31-day TTL. These are source values only. They do not set MistHelper's refresh interval, lease, concurrency, or TTL.

The source owner authorized reuse with documented attribution. Preserve the source repository, reviewed revision, and CC BY-NC-SA 4.0 license. Check the license obligations for each reused code or asset. Keep new MistHelper implementation independently written unless a specific source artifact is approved for reuse. Do not copy source tests, fixtures, screenshots, or assets as part of this planning work.

## Decisions

### Decision 1: Keep PR #4252 as the canonical dashboard

**Decision**: Reuse the #4252 dashboard, shared SDK collection, and existing Redis cache. Add no second WAN dashboard or collector.

**Rationale**: #4252 merged and closed #4195. #4208 is still a draft proposal.

**Alternative rejected**: Build a second dashboard or assume #4208 will merge unchanged. Both choices create duplicate ownership.

### Decision 2: Use one worker and cache-only dashboard reads

**Decision**: One background worker is the sole Mist API collector and the sole WAN snapshot writer. Dashboard routes read the existing cache only. The Refresh control queues the same worker.

**Rationale**: Page reads and refresh controls must not make independent Mist requests or race to write snapshots.

**Alternative rejected**: Let each request collect or cache data. That creates duplicate calls and multiple writers.

### Decision 3: Reuse only the four existing bulk reads

**Decision**: Use `listOrgSites`, `listOrgDevicesStats`, `searchOrgSwOrGwPorts`, and `getOrgInventory` with the existing paginated SDK path. Use a page size of 1,000.

**Rationale**: These are the four bulk reads already used by the #4252 overview. The source's per-site and per-port request loops are not part of this migration.

**Alternative rejected**: Copy the source request fan-out. It would increase calls and bypass the accepted collection design.

### Decision 4: Preserve the existing Redis policy

**Decision**: Keep the existing `wan-dashboard:v1:` namespace and 300-, 600-, and 86,400-second TTLs. Add no new namespace or database.

**Rationale**: The values belong to the merged #4252 cache. This migration does not need another cache policy.

**Alternative rejected**: Add a feature-specific key namespace or copy the source TTL. Either choice duplicates ownership.

### Decision 5: Leave the refresh interval and lease unapproved

**Decision**: Select no scheduled refresh interval or renewable worker lease until the production-scale load test records request usage, refresh duration, and failure recovery.

**Rationale**: The API limit applies across features. The 12–35+ request estimate does not include every non-WAN port page or other shared token use.

**Alternative rejected**: Convert the rough estimate into a fixed interval or lease. It is not measured evidence.

### Decision 6: Move per-port Insights parity to a separate issue

**Decision**: Exclude source-specific per-port Insights parity from #4220. Track it in issue #4330.

**Rationale**: The source uses a per-port request pattern that this migration must not add. The SDK field and response contract also needs its own review.

**Alternative rejected**: Add direct HTTP or per-port calls to this worker. The user excluded both paths from this migration.

### Decision 7: Preserve source attribution

**Decision**: Record the source repository, reviewed revision, owner authorization, and CC BY-NC-SA 4.0 license.

**Rationale**: The user owns the source and authorized reuse with documented attribution. The license still governs reused material.

**Alternative rejected**: Omit source attribution or assume authorization removes license obligations.

### Decision 8: Use one leased worker and safe refresh status

**Decision**: Run the worker inside the existing web container. A renewable Redis lease elects one active collector across Gunicorn processes. Keep one active run and at most one queued follow-up. Coalesce further Refresh requests into that follow-up. On failure, keep the last complete snapshot as stale, show a safe error, and publish no partial data. Show the refresh state, current bulk-read phase, completed page counts, and timestamps.

**Rationale**: Multiple Gunicorn processes must not become competing collectors or cache writers. Operators need visible progress and safe failure information.

**Alternative rejected**: Let each process start an independent collector or publish partially completed reads. These choices can duplicate API use or misrepresent incomplete data.

### Decision 9: Use a bounded process-local fallback during Redis outage

**Decision**: When Redis is unavailable, show a complete snapshot held by the serving process as stale only when it is no more than 86,400 seconds old. Otherwise report unavailable data. Make no Mist request and add no local persistent store.

**Rationale**: The user approved a last complete local snapshot fallback without authorizing another persistent data store.

**Assumption**: "Local snapshot" means a complete in-memory snapshot that the serving Gunicorn process already holds. Another process may not hold a copy. No file or database fallback is added.

**Alternative rejected**: Call Mist from a dashboard route or show expired in-memory data. Both choices violate the cache-only and maximum-age requirements.

## Remaining Production-Only Blocker

Run the approved production-scale load test before setting the worker schedule or lease. The test must measure the shared token budget across the production bands and include all non-WAN port pages. Until it passes, the refresh interval and renewable lease stay unset.

The SDK startup token-validation diagnostic is a separate lab caveat. Resolve or explain it before treating the lab response as authentication evidence.
