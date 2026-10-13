# Research: Mist WAN Performance

## Evidence and Provenance

The source revision reviewed for documentation is `2d1c2199fa1e31c129ef1e051c5389349a207785`.
Read-only GitHub API inspection examined the repository tree, README, screen guide, and operating guide.
The supplied assignment also identifies source CLI TODO stubs and HPE Network Operations authorship.
No source code, fixtures, or screenshot files enter this branch.

| Evidence | Confirmed fact | Limit |
| --- | --- | --- |
| [Source README](https://github.com/jmorrison-juniper/MistWANPerformance/blob/2d1c2199fa1e31c129ef1e051c5389349a207785/README.md) | WAN metrics, hourly UTC reporting, Redis cache, Snowflake expectation, internal-use notice | Does not prove every documented feature works |
| [Source screens](https://github.com/jmorrison-juniper/MistWANPerformance/blob/2d1c2199fa1e31c129ef1e051c5389349a207785/docs/screens.md) | Four routes, encoded port and peer examples, synthetic historical captures | Screens do not prove live collection or connectivity |
| [Source operations](https://github.com/jmorrison-juniper/MistWANPerformance/blob/2d1c2199fa1e31c129ef1e051c5389349a207785/docs/operations.md) | Candidate SDK methods, KPI definitions, source history TTL | Exact contracts and completed behavior remain unverified |
| [`WebPortalApp`](../../../web_portal/app.py) | Injects `APISESSION`, `ORG_ID`, `DATA_DIR`, and registers blueprints | Does not provide a WAN collector |
| [Portal configuration](../../../web_portal/services/config.py) | Address allowlist, CSRF, and response headers | No user authentication |
| [Base template](../../../web_portal/templates/base.html) | Shared navigation, local assets, stable existing selectors | New selectors require implementation |
| [Database configuration](../../../src/foundation/persistence/db/__init__.py) | Existing ArangoDB and Redis configuration, standalone mode | Selected-backend read/write capability needs investigation |
| [Database router](../../../src/foundation/persistence/db/router.py) | Existing writer dispatch and degraded CSV results | A CSV result does not prove durable history |
| [Rate-limit utilities](../../../src/foundation/support/utils/rate_limiting.py) | Adaptive delay and usage accounting | Not proof of cross-process admission |
| [Quota cache](../../../src/mist/access/api/api_usage_cache.py) | Shared process-local mutable cache | Multiple worker processes do not share this dictionary |
| [API fetcher](../../../src/mist/access/api/api_data_fetcher.py) | SDK pagination, failures, and runtime settings | Its export pipeline is not automatically suitable for page reads |
| [E2E fixtures](../../../tests/e2e/conftest.py) | Flask client fixtures require no separate server | Browser layout tests still need a scoped fixture |

## Decisions

### Portal integration

**Decision**: Use one Flask blueprint under `/wan-performance` and the existing base template.

**Rationale**: The current `/` route belongs to MistHelper. A feature prefix prevents route collision while preserving source identifiers.

**Alternatives considered**: A separate Dash server would add another application entry point. Replacing `/` would change existing portal behavior.
Both alternatives violate the scope.

### Historical storage

**Decision**: Write canonical hourly records and read period summaries through one selected existing application database.
Use the configured SQLite file or configured ArangoDB database, never a new file or database.
Do not select a store only because a connection happens to work.

**Rationale**: The user requires one shared application database.
Redis cache history cannot provide authoritative durable reporting.

**Alternatives considered**: Snowflake, a second SQLite file, and a new database service are prohibited.
Automatic backend switching can hide missing history and split the authoritative record set.
If the selected store fails, report history unavailable.

**Open evidence**: T005 must identify configuration selection, existing database readers, transaction behavior, and retention ownership.
T006 must map completed historical fields independently of source warehouse tables.
The declared source database `WAN_PERFORMANCE` and schema `RETAIL_WAN` are provenance only, not destination contracts.

### Cache and refresh

**Decision**: Permit the existing Redis service for isolated feature cache keys only.
Use the same configured application database for durable lease and coordinated request-admission state.
The existing quota subsystem must participate in that coordination before refresh is enabled.

**Rationale**: A process-local lock or copied limiter cannot prevent several portal workers from exhausting the shared allowance.

**Alternatives considered**: One scheduler per worker is unsafe. Another Redis service or another credential store is prohibited.
Redis absence must not cause page rendering to make direct cloud calls.

**Open evidence**: T007 verifies source cache and scheduler behavior.
T009 proves compatibility between proposed bounds and the existing runtime, SDK retries, pagination, and fast mode.
Proposed numeric limits in the contract are design assumptions, not source facts.

### Layout and offline testing

**Decision**: Use the four source screen captures as review references.
Create independently authored synthetic fixtures after rights and metric contracts are resolved.

**Rationale**: Screen guides show completed journeys, but synthetic historical values do not prove current network health.

**Alternatives considered**: Copying proprietary fixtures or substituting fixture values during a live outage is not permitted.
T003 must create a metric and layout inventory for each source screen before UI work.

## Investigation Register

| Task | Investigation | Required evidence | Status |
| --- | --- | --- | --- |
| T001 | Licensing and provenance | Written reuse permission, author notice, approved independent-work boundary | Unresolved |
| T002 | SDK endpoint mappings | Exact module, method, explicit arguments, REST path, units, pagination, response samples | Unresolved |
| T003 | Completed source behavior | Four-page inventory, charts, filters, formulas, links, screenshot baseline, CLI stub exclusions | Unresolved |
| T004 | Destination structure | Child counts and approved nested package paths | Unresolved |
| T005 | Selected application store | Existing selection setting, read/write paths, transactions, index support, retention ownership | Unresolved |
| T006 | Historical reporting | Actual completed query behavior, hour identity, field mapping, aggregation rules, retention and gap handling | Unresolved |
| T007 | Cache and scheduler | Source key format, serialization, expiry, worker lifecycle, refresh triggers, duplicate-worker behavior | Unresolved |
| T008 | Export capability | Completed route and format, or explicit unsupported decision | Unresolved |
| T009 | Shared API coordination | Count every page and retry across workers and existing operations, including fast mode | Unresolved |

Source documentation names `getOrg`, `listOrgSites`, `getOrgInventory`, `listOrgDevicesStats`, and `searchOrgSwOrGwPorts`.
It also names `searchOrgPeerPathStats`, `getSiteDeviceStats`, `searchSiteDeviceEvents`, and site SLE methods.
These are investigation candidates, not verified mappings.
Verify them against the pinned SDK and local Mist OpenAPI records.
Do not forward arbitrary `*args` or `**kwargs` to SDK endpoint methods.

Source documentation gives a utilization formula involving bytes and bandwidth.
Its units and sampling interval must be proven before adoption.
Calendar week start, percentile method, tunnel-path identity, and continuous-threshold behavior also require evidence.
Do not promise the source guide's 13-month reporting language from a 31-day cache or CLI stubs.
No unresolved item is represented as a completed user feature.
