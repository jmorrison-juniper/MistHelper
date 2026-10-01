# Research: Selective Insight Definitions

**Date**: 2026-10-01

**Feature**: [spec.md](spec.md)

**Source revision**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

Research used local source reads and offline SDK discovery. No agent, HTTP request, implementation test, or timing trial ran.
All design questions below have decisions.

## 1. Select one definition inside the existing exporter

**Decision**: Add `ConstDefinitionsExporter.export_endpoint(endpoint_name)` in the existing exporter module.

Validate one public ASCII SDK module name before import. Reject dotted names, paths, private names, empty values, and non-string values.
Inspect only `mistapi.api.v1.const.<endpoint_name>` through `_inspect_module`.
Retain `_register_endpoint`, `EndpointConfig`, and `_process_single_endpoint`.
Remove an old registration for that selected name before discovery.
Do not enumerate the SDK package or process another registered definition.

**Rationale**: `_inspect_module` already owns imports, function selection, signature checks, filenames, and special handling.
`_process_single_endpoint` already owns the cache decision and processing counts.
Selected discovery therefore removes unrelated work without a second export implementation.

**Alternatives considered**:

- Reject a filtered `export_all`. It still discovers unrelated definitions.
- Reject direct `listInsightMetrics` calls from the helper. They duplicate exporter ownership.
- Reject a new forwarding service or compatibility shim. It adds no semantic responsibility.

**Evidence**: [Exporter discovery and processing](../../src/export/const_definitions_exporter.py).

## 2. Return evidence for the selected attempt

**Decision**: Return a small `DefinitionRefreshResult` from `export_endpoint`.

The record contains `endpoint_name`, `outcome`, `counts`, `http_status`, and `first_error`.
Use `fresh`, `updated`, or `failed` for `outcome`.
Snapshot the existing four exporter counters before and after the attempt.
Return their differences, not cumulative counts.
Keep request and write measurements in the offline test seams. Do not add another production counter system.

Let `_inspect_module` return a caught discovery exception while full discovery continues to ignore that return value.
Let `_fetch_and_export_endpoint` and `_process_single_endpoint` return the first expected exception, or `None`.
Keep `export_all()` and the shared insight helper's public `None` return contracts.

**Rationale**: File existence cannot distinguish a fresh cache from a failed refresh.
A local result retains error evidence without shared failure state or changes to the three existing callers.

**Alternatives considered**:

- Reject a Boolean result. It loses the original status and error.
- Reject failure state on the shared helper. Another caller could inherit it.
- Reject a new exception policy for caller methods. It changes their existing behavior.

**Evidence**: [Exporter counters](../../src/export/const_definitions_exporter.py) and
[helper availability check](../../src/analytics/insight_metrics_utils.py).

## 3. Preserve the first failure and count it once

**Decision**: Check an SDK response's HTTP status before data normalization.

Retain HTTP `4xx` and HTTP `5xx` evidence in a `requests.HTTPError` with the original response attached.
Retain the first available API error text. If the body is empty, use a message that contains the HTTP status.
An SDK response with `status_code=None` indicates no HTTP response.
Report that case as a transport failure, not a successful empty definition.
Keep existing raw payload support for inputs without an SDK status attribute.

Check the primary Boolean result from `DataExporter.write_with_format_selection`.
Only a successful primary write can increment `endpoints_updated`.
A `False` result becomes an output failure with the selected filename and SDK function name.
The Boolean interface cannot return a swallowed writer exception.
Retain its preceding error log and identify `False` as the first available exporter evidence.
If the writer raises an expected exception, retain that exception itself.

Record the first failure and increment `endpoints_failed` before the existing empty fallback write.
Catch an expected fallback failure inside that failure path.
Log it as a secondary error without changing the first error, HTTP status, or failure count.
A successful empty fallback remains a failed refresh.
Keep unexpected programming exceptions visible, as the existing tests require.

**Rationale**: The current fetch ignores HTTP status. The current export ignores the writer result.
The current fallback can prevent the first failure count and replace its visible error.
These repairs directly support a truthful selected result.

**Alternatives considered**:

- Reject success based on an old file or a successful fallback.
- Reject additional retries, atomic-output redesign, or changes to `DataExporter`.
- Reject a broad exception handler that converts programming faults into normal refresh failures.

**Evidence**: [Shared fetch and output methods](../../src/export/const_definitions_exporter.py),
[writer Boolean contract](../../src/export/data_exporter.py), and
[existing failure tests](../../tests/unit/export/test_const_definitions_exporter.py).

## 4. Keep the cache and output authorities unchanged

**Decision**: Retain `_is_file_fresh` and its strict age comparison.

An age below 86,400 seconds is fresh. An exact age of 86,400 seconds requires a refresh.
A missing file or an unreadable timestamp retains the existing refresh behavior.
Retain insight normalization, interval formatting, multiline handling, and the backend writer.
Retain normalizer insertion order and the eight sorted CSV columns.
Do not change scope parsing, exclusions, or metric order.
Keep a successful empty response as an empty write attempt and one successful update.
The CSV writer creates no file for empty data and can leave an existing stale file unchanged.
Do not add a cache policy for files that remain after a failed attempt.

**Rationale**: These methods already define the compatible cache and output behavior.

**Alternatives considered**:

- Reject a second cache test in the helper.
- Reject alternate filenames, a fixed metric list, or a new serialization path.
- Reject new cache invalidation or stale-data policy.

**Evidence**: [Cache and normalization methods](../../src/export/const_definitions_exporter.py) and
[scope reader](../../src/analytics/insight_metrics_utils.py).

## 5. Use the existing shared helper in all four callers

**Decision**: Change `InsightMetricsUtils.export_const_insight_metrics` to request `insight_metrics` and inspect the selected result.

Keep its banner and `None` return. Replace comprehensive-export notices with accurate selected-refresh notices.
Permit an availability message only after a `fresh` or `updated` result and a check of the selected CSV.
Report `failed` before any availability check. An old file cannot change that result.

Route `SiteClientInsightsService._print_intro_and_refresh` through `deps.InsightMetricsUtils`.
Remove `ConstDefinitionsExporter` from its dependency bundle.
Leave the site, device, and organization caller files unchanged.
Keep their scope loading, prompts, filenames, return values, and empty-output paths.
If a failed output leaves an old CSV, existing scope reading can still read it.
The helper must report the failed refresh and must not claim current definitions.

**Rationale**: The three other callers already use this helper.

**Alternatives considered**:

- Reject four separate selected-refresh implementations.
- Reject caller changes that impose a new abort or stale-file deletion policy.

**Evidence**: [Site caller](../../src/export/site_insights/site_metric_operation.py),
[device caller](../../src/export/site_insights/device_metric_operation.py),
[organization caller](../../src/export/org_export_utils.py), and
[client caller and dependency bundle](../../src/refactors/serial_cc/site_client_insights.py).

## 6. Preserve full coverage and measure actual elapsed time

**Decision**: Keep full SDK discovery dynamic.

Offline discovery with installed `mistapi 0.64.0` registered all 28 definitions in the spec's controlled baseline.
It retained `all_models`, `all_countries`, and `all_countries_channels`.
The full-coverage test will use that complete set, not a production allowlist.

The inspected baseline names are:

```text
alarm_defs, ap_channels, ap_esl_versions, ap_led_status,
app_categories, app_subcategories, applications, client_events,
countries, default_gateway_config, device_events, device_models,
fingerprint_types, gateway_applications, insight_metrics, languages,
license_types, marvisclient_events, marvisclient_versions, mxedge_events,
mxedge_models, nac_events, otherdevice_events, otherdevice_models,
states, system_events, traffic_types, webhook_topics
```

Use the real four refresh entries before and after implementation.
Use identical temporary caches, responses, one gateway model, one country, and a 50-millisecond delay per mock API request.
Measure with `time.perf_counter_ns`. Control cache age through `time.time`, not the elapsed-time clock.
Run at least five matched trials per caller and phase.
Match each pair by caller, trial number, fixture content, and cache age.
Print each duration, both medians, request counts, and file-write counts.
Require at least a 90% median reduction for each caller.

The chosen one-model, one-country fixture implies 31 baseline requests for 28 definitions.
Three extra requests obtain model or country lists.
This is a fixture expectation, not a timing result. Measure all requests through the session seam.
After implementation, each stale selected refresh must make one request and one definition write.

**Rationale**: A full export can make more than one request per definition.
Actual elapsed time includes discovery, cache checks, normalization, and output.

**Alternatives considered**:

- Reject `request_count * delay` as elapsed evidence.
- Reject direct-exporter-only timing or replacement of a caller's refresh method.
- Reject live requests or comparison claims against the reported live 67.3-second run.

**Evidence**: [Baseline discovery and special handling](../../src/export/const_definitions_exporter.py),
[required acceptance evidence](spec.md#required-acceptance-evidence), and
[issue #3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300).

## 7. Keep this step local and artifact-only

**Decision**: Write only this feature's planning and design documents with `apply_patch`.

The existing Python environment reports Python `3.13.13` and `mistapi 0.64.0`.
Use the current dependency manifests without changes.
Plan focused tests, changed-method coverage, configured code gates, citations, local links, and STE review.
Do not run implementation validation or timing trials during planning.

The supplied earlier baseline reports 321 passing tests in 1.71 seconds.
This plan does not claim a new execution of that command.
The host lacks `pwsh`, `powershell`, `hunspell`, `aspell`, and `data/ste_dictionary.json`.
The required PowerShell setup attempt failed with exit code 127.
Its common path resolver can persist `.specify/feature.json`, so no substitute writer will run.
The agent-context script would also edit prohibited shared instructions.
The configured companion hook has no installed command implementation in this checkout.
Report these workflow limits without creating shared state or installing tools.

**Rationale**: The explicit feature path and existing branch replace automatic feature selection.
The user's reservation excludes shared state, implementation changes, and publication.

**Evidence**: [Validation obligations](checklists/requirements.md#validation-obligations-for-later-implementation),
[CI workflow](../../.github/workflows/ci.yml), [project configuration](../../pyproject.toml),
[PowerShell path resolver](../../.specify/scripts/powershell/common.ps1),
[agent-context script](../../.specify/scripts/powershell/update-agent-context.ps1), and
[extension hooks](../../.specify/extensions.yml).

## Related work

- [Issue #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266) covers the related site insight path.
- [Issue #3300 scope claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419) defines this repair's reservation.
- [Issue #3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335) precedes queue position 17.
  Publication requires an explicit parent release.
