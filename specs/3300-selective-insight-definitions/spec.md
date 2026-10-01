# Feature Specification: Selective Insight Definitions

**Feature Branch**: `jmorrison-juniper-selective-insight-definitions`

**Created**: 2026-10-01

**Status**: Ready for planning

**Input**: Refresh only the insight metric definition for the four insight exports described in issue #3300. Preserve caching, export compatibility, and truthful failure reporting.

**Source**: [Issue #3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300)

**Related work**: [Issue #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266)

**Reservation**: [Authenticated scope claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419)

## User Scenarios & Testing *(mandatory)*

The four insight exports need only `ConstInsightMetrics.csv`. Their current refresh also processes 27 unrelated constant definitions.

The issue records 18 live refresh runs from September 22 through September 23, 2026.

| Reported cache state | Runs | Definition refresh duration |
| --- | --- | --- |
| Fresh caches, with 28 definitions skipped | 17 | 0.6-2.4 seconds |
| Stale caches, with 28 definitions updated | 1 | 67.3 seconds |

These values are reported live observations. They are not measurements from this specification step or targets for an offline benchmark.

### User Story 1 - Start Insight Exports Without Unrelated Refreshes (Priority: P1)

As a network operator, I want an insight export to refresh only its required definition.
I must not wait for unrelated constant definitions before the export starts.

**Why this priority**: The reported stale refresh accounts for 67.3 seconds of the delay before insight collection.

**Independent Test**: Run each actual caller path with all definition caches expired and successful offline responses.
Count definition requests, writes, and access to unrelated caches.

**Acceptance Scenarios**:

1. **Given**: All 28 definition caches are expired.
   **When**: Each of the four operations performs its definition refresh.
   **Then**: Each operation requests the insight definition once and writes `ConstInsightMetrics.csv` once.
   It does not access or change another definition cache.
2. **Given**: The insight definition cache is missing, and unrelated caches have mixed ages.
   **When**: An affected operation refreshes its definitions.
   **Then**: It requests and writes only the insight definition.
3. **Given**: The insight definition supports multiple scopes.
   **When**: Each operation loads its metrics after a successful refresh.
   **Then**: Each operation receives the same ordered metric list for its scope as before the repair.

### User Story 2 - Reuse Fresh Definitions and Refresh at the Boundary (Priority: P1)

As a network operator, I want fresh insight definitions to remain available without another request or file write.
I want expired definitions to refresh under the existing 24-hour rule.

**Why this priority**: The repair must reduce unnecessary work without changing cache freshness.

**Independent Test**: Exercise each caller with a controlled cache clock and isolated files.
Check fresh, exactly 24-hour-old, expired, and missing insight caches.

**Acceptance Scenarios**:

1. **Given**: The insight cache is one second younger than 24 hours.
   **When**: Each caller performs its refresh.
   **Then**: It makes zero definition requests and zero writes.
   The file contents and modification time remain unchanged.
2. **Given**: The insight cache is exactly 24 hours old.
   **When**: Each caller performs its refresh.
   **Then**: It requests and writes the insight definition once.
3. **Given**: The insight cache is older than 24 hours or missing.
   **When**: Each caller performs its refresh.
   **Then**: It requests and writes the insight definition once.
4. **Given**: A successful refresh created a fresh insight cache.
   **When**: The same caller performs a second refresh within 24 hours.
   **Then**: The second refresh uses the cache without a definition request or write.

### User Story 3 - Identify a Failed Refresh Without False Success (Priority: P1)

As a network operator, I want refresh failures to retain their original status and first error.
An existing file must not make a failed refresh appear successful.

**Why this priority**: False success hides the reason that an export cannot obtain current definitions.

**Independent Test**: Exercise each actual caller with offline HTTP `4xx`, HTTP `5xx`, transport, discovery, and output failures.
Include an existing stale file and a secondary output failure.

**Acceptance Scenarios**:

1. **Given**: The definition request returns HTTP `4xx` or HTTP `5xx`.
   **When**: Each caller performs its refresh.
   **Then**: The refresh reports failure and retains the original HTTP status and first error.
   It does not count the refresh as a successful update.
2. **Given**: An old insight file remains after a failed refresh.
   **When**: The operation reports the refresh outcome.
   **Then**: File existence does not cause a success message.
   Existing caller error and empty-output behavior remains intact.
3. **Given**: A request fails, and a later output action also fails.
   **When**: The operation reports the failure.
   **Then**: It retains the request status and first error.
   It can report the secondary error without replacing the first error.
4. **Given**: The selected definition cannot be found.
   **When**: An insight operation attempts its refresh.
   **Then**: It reports failure without refreshing other definitions.

### User Story 4 - Continue to Export All Definitions on Request (Priority: P2)

As a network operator, I want the separate full-definition export to retain its complete definition coverage.
Selective insight refresh must not reduce that operation's coverage.

**Why this priority**: The repair must not remove an existing export capability.

**Independent Test**: Compare the full-definition export before and after the repair with the same controlled definition set and responses.

**Acceptance Scenarios**:

1. **Given**: The controlled set contains the same 28 definitions as the baseline.
   **When**: The operator runs the full-definition export with expired caches.
   **Then**: The operation processes all 28 definitions and retains their existing export behavior.
   Existing handling for definitions with additional parameters remains available.
2. **Given**: All controlled definition caches are fresh.
   **When**: The operator runs the full-definition export.
   **Then**: It retains the existing cache skips and full coverage.

### Edge Cases

- A fresh insight cache and expired unrelated caches must produce zero definition requests and writes.
- An expired insight cache and fresh unrelated caches must refresh only the insight definition.
- A cache timestamp that cannot be read must retain the existing refresh behavior.
- An empty successful response must retain the existing empty-definition output behavior.
- Missing scope values, blank metric names, and template metric names must retain their existing exclusions.
- Unknown or invalid definition selection must not trigger full-definition discovery or refresh.
- A failed request with an empty body must retain its HTTP status and first available error.
- A failed output write must not count as a successful update or conceal an earlier request error.
- Counts must describe the current refresh attempt, not another caller or a previous attempt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All four affected insight operations MUST refresh only the insight metric definition before loading metrics.
  A successful expired-cache refresh MUST make one definition request and one definition write.
- **FR-002**: Selective refresh MUST NOT discover, read, inspect timestamps, fetch, create, update, or otherwise touch unrelated definition caches.
  Unrelated file contents and modification times MUST remain unchanged.
- **FR-003**: An insight cache younger than 24 hours MUST remain a cache hit.
  An insight cache exactly 24 hours old, older than 24 hours, or missing MUST require a refresh.
- **FR-004**: All affected operations MUST use one consistent definition refresh contract.
  The repair MUST preserve the existing authority for discovery, cache decisions, normalization, output, and failure counts.
- **FR-005**: The full-definition export MUST retain discovery and processing of every previously supported definition.
  Its cache policy and existing handling for definitions with additional parameters MUST remain unchanged.
- **FR-006**: Insight definition output MUST retain its filename, column order, and normalized values.
  The CSV columns MUST remain `description`, `intervals`, `metric_name`, `report_intervals`, `report_scopes`, `scopes`, `type`, and `unit`.
- **FR-007**: Metric selection for `site`, `device`, `client`, and `org` MUST retain the same ordered results.
  Existing scope parsing and exclusions MUST remain unchanged.
- **FR-008**: Existing caller return values, operation banners, selection prompts, output names, error handling, and empty-output behavior MUST remain compatible.
  Refresh messages MAY change to describe the selected definition and actual outcome accurately.
- **FR-009**: Every failed refresh MUST retain its first error and any original HTTP `4xx` or HTTP `5xx` status.
  A later failure or file-existence check MUST NOT replace that evidence or report a successful refresh.
- **FR-010**: Refresh counts MUST distinguish processed definitions, fresh-cache skips, successful updates, and failures.
  Failed refreshes MUST NOT increment the successful-update count.
- **FR-011**: Meaningful cache, fetch, and write actions MUST have before-and-after logs.
  Logs MUST identify the definition, cache decision, relevant counts, and outcome status without secrets.
- **FR-012**: Unknown or invalid definition selection MUST report failure without a fallback to the full-definition export.
- **FR-013**: Acceptance tests and timing trials MUST use temporary files and offline responses.
  They MUST NOT access production data, live Mist services, stores, or containers.

### Key Entities *(include if feature involves data)*

- **Insight metric definition**: The descriptions, types, units, scopes, and intervals that determine available insight metrics.
- **Definition cache**: A saved definition with a modification time used by the existing 24-hour freshness rule.
- **Refresh outcome**: The selected definition, cache decision, request and write counts, successful updates, failures, and original error information.
- **Insight operation**: One of the site, device, client, or organization exports that consumes the insight metric definition.

### Required Acceptance Evidence

Record failing tests before implementation for every actual stale-cache caller path.
Direct exporter tests alone do not satisfy this requirement.
The tests must retain the real refresh path and replace only external responses and necessary runtime dependencies.

Record passing evidence for all acceptance scenarios after implementation.
Include the cache boundary, a second-run cache hit, unrelated-cache isolation, output compatibility, and full-definition coverage.
Include HTTP `4xx` and HTTP `5xx` failures, first-error preservation, and failure counts.

Measure actual elapsed refresh time before and after the repair through all four callers.
Use equivalent expired caches, the same offline definition responses, and the same documented request delay.
Use at least five paired trials per caller and report each elapsed duration and the median.
Report definition, request, and file-write counts with each caller's results.

Label these results as controlled offline measurements.
Keep them separate from the issue's live 67.3-second observation.
Do not claim a new live duration or run live requests to obtain one.

The [requirements checklist](checklists/requirements.md) records the inherited implementation boundaries and later validation obligations.
No implementation tests or benchmarks run during this specification step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four affected operations refresh one definition instead of 28 in equivalent controlled stale-cache cases.
  Each successful case makes one definition request and one definition write, with zero unrelated cache accesses or changes.
- **SC-002**: All four operations pass fresh, exactly 24-hour-old, expired, missing, and second-run cache-hit scenarios.
  Every fresh-cache case has zero definition requests and writes.
- **SC-003**: Every caller reduces median refresh time by at least 90% across five equivalent paired offline trials.
  The report states the controlled request delay, elapsed times, and request and file counts.
- **SC-004**: All four operations retain identical definition columns, normalized values, ordered scope results, and caller output contracts in compatibility tests.
- **SC-005**: The full-definition operation retains all 28 controlled baseline definitions and its existing cache and parameter handling.
- **SC-006**: Every tested failed refresh reports failure, retains its original status and first error, and records zero successful updates.
- **SC-007**: Operators can distinguish a cache hit, successful refresh, and failed refresh in every tested outcome.
  Relevant before-and-after logs include counts and status, use ASCII, and expose zero secrets.

## Assumptions

- The 28-definition count describes the reported baseline and the controlled comparison set.
  The full-definition export remains dynamic, not limited to a new fixed list of 28 names.
- Existing file modification times remain the source of cache age.
  This repair does not introduce a new cache policy or duplicate cache decisions.
- Timing covers each actual refresh entry, including its existing local work.
  It excludes interactive selections and later collection of insight data.
- Controlled comparisons use the same response data, request delay, cache ages, and output behavior.
  The 90% target applies only to these offline trials.
- Failed refreshes retain existing caller error and empty-output contracts.
  This repair does not introduce a new retry policy or promise successful current definitions after a failure.

### Scope and Authorization

This step writes only `spec.md` and `checklists/requirements.md` within `specs/3300-selective-insight-definitions/`.
It does not create source code, tests, release notes, plans, or other artifacts.
The existing app branch and base revision remain unchanged.
The base revision is `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The app session is `97654420-27aa-4469-b541-949a2e1d042d`.

The authenticated reservation reports no overlap after inspection of all 11 open pull requests.
This specification step does not claim another overlap inspection.

Later implementation remains limited to the source files, test files, and release-note path in the requirements checklist.
The site, device, and organization caller files remain unchanged.
Shared files, dependency pins, schemas, primary keys, baselines, suppressions, and exclusions remain unchanged.

This step does not create or rename branches, run feature creation scripts, write shared SpecKit state, or commit.
It does not push, open a pull request, or start publication.
Later publication requires an explicit parent release.

### Dependencies and References

- The [project constitution](../../.specify/memory/constitution.md) governs existing safety, class ownership, output compatibility, and logging requirements.
- The [current CI workflow](../../.github/workflows/ci.yml) and [project configuration](../../pyproject.toml) define later validation scope.
- The [STE writing guide](../../documentation/ASD-STE100_writing-guide.md) governs concise, complete sentences and consistent terms.
- The [scope reservation](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419) defines the file boundary and publication hold.
