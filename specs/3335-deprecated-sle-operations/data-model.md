# Data Model: Deprecated SLE registration removal

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Related design**: [Plan](plan.md), [research](research.md), and [endpoint-removal contract](contracts/endpoint-removal.md).

## Model Boundary

This feature removes registration metadata only.
It introduces no production class, database schema, migration, table, index, or store operation.
Existing exported records and historical stored data remain untouched.

## 1. Selectable Operation Registration

**Existing type**: `_EndpointFamilyOp`.

**Owner**: `src/export/endpoint_family_exporter.py`.

| Field | Existing meaning | Required treatment |
| --- | --- | --- |
| `operation` | Exact SDK operation identifier and export-routing key | Remove only the two retired identifiers. |
| `module` | Dotted SDK module path | Retained SLE rows keep `mistapi.api.v1.sites.sle`. |
| `required` | Ordered required identifiers | Keep each retained tuple unchanged. |
| `issues` | Existing discovery issue references | Keep all retained references unchanged. |

| Retained operation | Required tuple | Issue reference |
| --- | --- | --- |
| `getSiteSleSummaryTrend` | `site_id`, `scope`, `scope_id`, `metric` | 1217 |
| `getSiteSleClassifierSummaryTrend` | `site_id`, `scope`, `scope_id`, `metric`, `classifier` | 1213 |

The retired rows are `getSiteSleSummary` and `getSiteSleClassifierDetails`.
Remove them, not their shared prefixes.
The remaining SLE rows keep their relative order.
Their submenu positions change only as a consequence of those two removals.
Top-level menu identifiers do not change.

## 2. Operation Family

**Existing representation**: Immutable operation tuples.

| Family or aggregate | Before | After |
| --- | ---: | ---: |
| `_SITE_SLE_OPS` | 17 | 15 |
| `_SITE_MAP_OPS` | 7 | 7 |
| `_SITE_DETAIL_OPS` | 33 | 33 |
| `_ORG_DETAIL_OPS` | 61 | 61 |
| `_MSP_DETAIL_OPS` | 10 | 10 |
| `_OTHER_DETAIL_OPS` | 6 | 6 |
| `ALL_STAGE_TWO_ENDPOINT_OPS` | 134 | 132 |
| All ten selectable family tables | 286 | 284 |

The stage-two aggregate continues to expand the same six family tuples.
Every unrelated member keeps its full operation row, not only its family count.
No duplicate registration is introduced.

## 3. Catalog Entry

**Existing type**: `EndpointInfo`.

**Owner**: `src/export/endpoint_catalog.py`.

**Relationship**: The exact operation identifier joins a selectable row to its catalog entry.

| Field | Meaning | Required treatment |
| --- | --- | --- |
| Dictionary key | Exact operation identifier | Remove the two retired keys. |
| `description` | Operator-facing description | Preserve every retained description. |
| `safety` | Existing registry vocabulary | Preserve `interactive_safe` for both trends and all unrelated flags. |
| `label` | Existing safety-label property | No change. |

The catalog count changes from 286 to 284.
Its key set must still equal the selectable operation set.
The unknown-operation fallback remains unchanged and does not create a selectable replacement.

## 4. Primary-Key Metadata

**Existing representation**: `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Owner**: `src/refactors/endpoint_primary_key_strategies.py`.

**Relationship**: `api_function_name` selects the existing strategy for a retained export.

| Field | Summary trend | Classifier trend |
| --- | --- | --- |
| Operation key | `getSiteSleSummaryTrend` | `getSiteSleClassifierSummaryTrend` |
| `type` | `auto_increment_with_unique` | `auto_increment_with_unique` |
| `primary_key` | `["misthelper_internal_id"]` | `["misthelper_internal_id"]` |
| `indexes` | `["site_id", "scope", "scope_id", "metric"]` | `["site_id", "scope", "scope_id", "metric", "classifier"]` |
| `unique_constraints` | `[]` | `[]` |
| `description` | `Endpoint family export for getSiteSleSummaryTrend` | `Endpoint family export for getSiteSleClassifierSummaryTrend` |

Keep these dictionaries unchanged.
Keep the supplemental `setdefault` merge and all earlier strategy definitions.
The observed 571 strategy keys become 569 after only the two removals.
Do not make that observed total a new unrelated global ratchet.

The empty unique-constraint lists are existing behavior.
Do not invent natural keys, add identity fields, or claim new deduplication behavior.
Existing upsert regressions continue to prove their own configured natural, composite, and time-series strategies.
No persisted table or row is removed when a metadata key disappears.

## 5. Trend Export Record

**Existing representation**: SDK response records processed by the current exporter.

The feature defines no new record schema.
Do not inject selection identifiers into returned records or alter their field values.

| Boundary | Existing behavior |
| --- | --- |
| SDK response | A real `APIResponse` holds decoded HTTP data and the next-page value. |
| SDK pagination | `get_all` collects a list or the dictionary's `results` list. Other dictionary shapes currently return no rows. |
| Exporter normalization | `None` becomes empty. Lists remain lists. Tuples become lists. Dictionaries become one row. Scalars use `value`. |
| Flattening | Existing `DataProcessingUtils` expands nested fields. |
| Multiline escaping | Existing code escapes newline characters and removes carriage returns. |
| Output dispatch | Nonempty rows reach `DataExporter.write_with_format_selection` with the original operation identifier. |
| Empty result | No final writer call. No new output file from this endpoint-family path. |

The filename uses the original operation identifier and existing argument labels.
Repeated local journeys must dispatch the same normalized records and identifier.
This comparison proves no new record transformation or routing change.
It does not authorize a new trend persistence algorithm.
Those local journeys use generic list and `results` fixtures.
They do not prove export of the documented trend objects.
The documented objects currently yield zero records at the SDK collection boundary.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) owns that separate existing defect.
The coordinator explicitly excludes response handling from this metadata-only change.

## 6. Menu Reference

**Existing representations**: `MenuEntry` title, portal description, documentation row, and generated pages.

| Field | Required value or invariant |
| --- | --- |
| Top-level menu identifier | `"263"` |
| Handler | `EndpointFamilyExporter.site_sle_endpoints` |
| Fixed title | `Run any site SLE endpoint with scope prompts (15 operations)` |
| Category | Existing `interactive_safe` category |
| Destructive flag | Existing `False` value |
| Top-level count | 293 distinct `MenuEntry` identifiers on the inspected baseline |
| Portal description count | 179 entries on the inspected baseline |

Only the operation-count text changes.
All six reserved generated pages must agree with the source.
The vendored SDK discovery index and upstream or historical documents are records, not active registrations.

## 7. Test-Only Guard Decision

**Owner**: Existing `TestCatalogCoverage` in `tests/guardrails/test_endpoint_catalog.py`.

This is private test logic, not a production model or new wrapper class.
Use typed inputs that distinguish existing selectable row objects from catalog and PK mappings.

The decision reports:

- Whether the source passed.
- The number of records actually inspected.
- The exact retired identifiers found, or the reason a required read failed.

Acceptance requires a readable, valid, nonempty source with neither retired identifier.
A read error always rejects, even when the earlier records were valid.
Empty or missing input rejects with a measured count of zero.
Injected source copies must reject with nonzero counts.

## State Transitions

1. **Registered**: Both retired operations currently appear in all three sources.
2. **Red evidence recorded**: All six exact live-source absence cases fail.
3. **Unregistered**: Only those six registrations are deleted.
4. **Green evidence recorded**: Absence cases pass, controlled injections reject, and retained SDK journeys pass.
5. **References synchronized**: Only the reserved labels and six generated files reflect 15 operations.

These are implementation evidence states, not persisted application states.
They require no shared feature-state file or migration.
