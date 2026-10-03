# Research: Remove deprecated SLE operations

**Date**: 2026-10-01

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Scope**: Local read-only research for [the completed specification](spec.md).

No dependency installation, live Mist request, source edit, or SDK-index refresh was needed.
The existing environment reports Python 3.13.13 and `mistapi` 0.64.0.

## 1. Exact registration removal

**Decision**: Remove only `getSiteSleSummary` and `getSiteSleClassifierDetails` from the three active registration modules.

**Rationale**: `_SITE_SLE_OPS` contains one row for each retired identifier.
The catalog and supplemental PK table contain matching registrations.
`ALL_STAGE_TWO_ENDPOINT_OPS` expands the existing family tuples.
Deleting the SLE rows therefore reduces the stage-two count without changing its construction.
The PK supplement uses `setdefault` to preserve earlier key definitions.
Keep that merge unchanged.

**Alternatives considered**:

- A prefix-based removal would also remove `getSiteSleSummaryTrend`.
- An alias or fallback would leave an unsupported selectable operation.
- A repository-wide string ban would change historical records and the vendored discovery index.
- Deleting retained strategies would change export routing and persistence metadata.

**Evidence**: `src/operations/exporting/export/endpoint_family_exporter.py`, `src/operations/exporting/export/endpoint_catalog.py`,
and `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.

## 2. Real installed trend functions

**Decision**: Keep the real SDK 0.64.0 methods and their existing operation rows.
Keep the dependency constraint `mistapi>=0.64.0,<0.65`.

**Rationale**: The installed `mistapi.api.v1.sites.sle` module defines both retained functions.
`getSiteSleSummaryTrend` requires `site_id`, `scope`, `scope_id`, and `metric`.
`getSiteSleClassifierSummaryTrend` also requires `classifier`.
Both methods accept optional `start`, `end`, and `duration` values.
Their Python defaults are `None`.
The existing exporter supplies only the required positional values.

The summary path ends in `/metric/{metric}/summary-trend`.
The classifier path ends in `/metric/{metric}/classifier/{classifier}/summary-trend`.
Both methods call the session's real `mist_get` method.
Neither method delegates to a retired function.

**Alternatives considered**:

- Upgrading to SDK 0.65.0 would change the dependency boundary and is not authorized.
- Replacing SDK methods with mocks would not prove actual resolution or request construction.
- Direct HTTP production calls would bypass the required SDK integration.

**Evidence**: Installed SDK `mistapi/api/v1/sites/sle.py` and the existing `_resolve` method.
The upstream deprecation history is already verified in the specification and issue.
Do not modify or regenerate upstream records.

## 3. SDK pagination and normalization

**Decision**: Preserve the complete `_run` and `_persist` paths.
Use real SDK response processing in the trend tests.

**Rationale**: SDK `get_all` returns records from list payloads or dictionaries with `results`.
It follows the real response's `next` link.
A dictionary without `results` currently produces an empty list.
Do not add a new response extractor to make that case export records.
The documented responses for both trend operations are objects without `results`.
The real SDK proof confirmed that each object yields zero collected rows.
The existing normalizer would retain each raw object as one row.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) owns this separate defect.
The coordinator confirmed metadata-only scope for #3335.
The local tests prove retained entries and generic processing, not verified exports of the documented objects.

The exporter normalizes `None`, lists, tuples, dictionaries, and scalar values.
It then calls the existing flatten and multiline-escape methods.
An empty normalized result does not reach `DataExporter`.
A nonempty result uses `write_with_format_selection` with the original operation identifier.
The filename comes from the operation and existing argument labels.

**Alternatives considered**:

- Mocking `mistapi.get_all` would hide response-shape and pagination regressions.
- Mocking `_normalize` or `_persist` would hide record and dispatch changes.
- A new flattening implementation would add an unrelated behavior change.

**Evidence**: Installed SDK `__pagination.py` and `__api_response.py`;
`EndpointFamilyExporter._run`, `_normalize`, and `_persist`;
`DataProcessingUtils.flatten_nested_fields` and `escape_multiline`.

## 4. Test boundaries and required answers

**Decision**: Use real selectors, answer handling, endpoint functions, and export processing.
Supply local console input and mock only local HTTP transport and final output.

**Rationale**: `SourceDependencyResolver` resolves existing source classes and `MainEntrypoint.context`.
Site selection reads `data/SiteList.csv`.
The site-name lookup uses the SDK organization-site request.
A fresh site CSV in a pytest temporary directory avoids cache regeneration.
An existing `AppContext` supplies a local organization and session.
The real `InputUtils.safe_input` handles blank input, EOF, and interruption.

Create a real local `APISession` without production credentials.
Use an empty test environment file and a reserved `.test` host.
Patch only that session's HTTP `get` transport before requests.
Return real `requests.Response` values so SDK `APIResponse` and pagination remain real.
Set their status, JSON body, URL, and real prepared request with headers.
The SDK reads `response.request.headers` before response decoding.
An incomplete response double could trigger an SDK error while still returning a payload.
Require no SDK error log in successful cases.
Supply operator responses at `builtins.input`, not by replacing `safe_input`.
Capture the final writer call and require its exact payload, filename, and routing identifier.
Restore local state and both deleted SDK attributes after each case.

**Alternatives considered**:

- The existing `_fake_mist_helper` is useful for older isolated tests but cannot prove the real trend journey.
- Replacing `_mist_helper`, `_resolve`, `_collect_arguments`, or site selectors would hide the relevant behavior.
- A live Mist service, persistent database, container, or new fixture framework is unnecessary.

**Evidence**: `SourceDependencyResolver`, `SiteDeviceExporter._resolve_site_for_stats`,
`PromptUtils.select_site_id_from_csv`, `ConfigUtils`, `InputUtils`, and SDK `APIRequest.mist_get`.

## 5. Existing keys and persistence

**Decision**: Keep both trend strategy dictionaries byte-for-byte equivalent in meaning.
Delete only the two obsolete supplemental registrations.

**Rationale**: Both retained strategies use `auto_increment_with_unique`.
Their primary key is `["misthelper_internal_id"]`.
Their unique-constraint lists are empty.
Their indexes contain `site_id`, `scope`, `scope_id`, and `metric`.
The classifier strategy adds `classifier`.
Descriptions name the corresponding retained operation.

Do not replace these existing strategies with invented natural keys.
The feature adds no uniqueness or trend deduplication promise beyond unchanged behavior.
Repeated trend tests compare the exact writer payload and routing metadata.
Existing inventory and device-statistics tests prove their own established upsert contracts.
No stored row, table, index, or schema needs removal.

**Alternatives considered**:

- A new composite trend key would be a persistence redesign.
- Deleting stored trend or historical retired-operation data would be a migration.
- Claiming that an empty unique-constraint list guarantees new trend deduplication would be unsupported.

**Evidence**: Both retained PK entries, the supplement's `setdefault` merge,
and the existing schema and temporary SQLite upsert tests.

## 6. Direct absence guards and controlled rejection

**Decision**: Extend existing `TestCatalogCoverage` with a private typed guard decision.
Exercise it directly on raw selectable rows, catalog entries, and PK metadata.

**Rationale**: The existing coverage and orphan tests prove catalog agreement.
They do not explicitly reject either retired identifier in all three sources.
Use six parameterized live-source absence assertions and keep them after the change.
Use six additional cases that inject one exact retired registration into a source copy.
Each rejection must name the violation and report the actual nonzero inspected count.

The decision must reject empty, missing, malformed, and unreadable input.
Count only successfully inspected records.
A partial-read error must retain its measured count and still reject.
An error before the first read reports zero and rejects.
Do not turn a skipped or empty scan into successful evidence.

**Alternatives considered**:

- An independent forbidden-name fixture would not inspect actual registrations.
- Testing only a mock's call count would not prove guard decisions.
- Appending only a name after inspection would not prove rejection of an injected source registration.
- Global table mutation could contaminate later tests.
- A new guard production class or standalone helper wrapper is unnecessary.

**Evidence**: `tests/guardrails/test_endpoint_catalog.py` and the specification's VC-001 and VC-002.

## 7. Labels, generated references, and ownership

**Decision**: Change only the three fixed menu 263 counts.
Later regenerate only the two wiki references and four operation-map pages.

**Rationale**: `MistHelper.py`, `web_portal/menu_registry.py`, and `documentation/menu-highlights.md` each state 17 operations.
All three must state 15.
The wiki generator writes exactly two existing reference files.
The API-map generator uses the vendored SDK index but derives active calls from source.
Its `--check` mode writes nothing.
Its normal mode can remove orphan pages, so the later run needs a strict output-scope check.

The live check at `2026-10-01T17:33:21Z` found no reservation overlap.
All 12 open PR file lists were complete and stable, with 103 exact file entries.
All 23 reserved paths matched the claim comment.
This included the five design paths and six generated paths.
The later generator run still needs another live check.

**Alternatives considered**:

- Refreshing `scripts/menu_api_map/reference/sdk_index.json` would modify a historical discovery record.
- Editing shared README or changelog files would violate the reservation.
- Generating an additional guide or accepting another generated path would expand scope.

**Evidence**: The three fixed labels, both existing generators, the completed spec,
and [the reservation](https://github.com/jmorrison-juniper/MistHelper/issues/3335#issuecomment-5936510347).

## 8. Gates and delivery boundary

**Decision**: Use the existing gate configuration without baseline, suppression, exclusion, or dependency changes.
Use the strict own-worktree audit alternative only for the standard macOS resolver failure.

**Rationale**: CI names full `ruff check .`, full `black --check --diff .`, and five exact mypy targets.
Bandit scans with `pyproject.toml` and a separate cross-platform exclude check.
The test-quality gate uses `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
Use the full local ratchet before publication so uncommitted tests cannot be omitted by a HEAD-only changed-file scope.
Keep old findings and their baseline unchanged.

The current STE minimum is 80.
The planning run passed that minimum for all five files.
The optional word dictionary was unavailable, so the tool reported partial coverage.
Keep that limitation visible without changing configuration or generating another artifact.
The Markdown checker reads tracked files only.
During isolated planning, check new untracked design files directly with its existing file parser.
An empty tracked-file selection is not evidence for these documents.

For the audit alternative, compile only `requirements.txt` with this worktree's Python and native TLS.
Write the hashed lock to `data/issue-3335/runtime-audit-lock.txt` during later authorized validation.
Audit it with `--no-deps --disable-pip --require-hashes`.
The Git-only `misthelper-devtools` pin is a development tool outside that runtime lock.
Do not ignore any advisory.

**Alternatives considered**:

- Narrowing lint or type scopes would weaken the requested gates.
- Updating a baseline or adding an ignored advisory would hide a failure.
- Reusing another worktree's audit lock would not prove this runtime input.
- Deployment or publication now would violate the explicit local preparation limit.

**Evidence**: `.github/workflows/ci.yml`, `.github/workflows/ste-lint.yml`,
`.pre-commit-config.yaml`, `.ste-linter.toml`, both test-quality files, and installed CLI help.

## Resolution

All technical decisions are resolved.
The [plan](plan.md), [data model](data-model.md), [contract](contracts/endpoint-removal.md),
and [validation guide](quickstart.md) apply these decisions.
The separate issue remains open and unrepaired by this feature.
Local code and metadata results appear in [the task evidence](tasks.md).
