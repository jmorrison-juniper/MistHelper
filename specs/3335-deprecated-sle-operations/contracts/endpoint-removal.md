# Contract: Deprecated SLE operation removal

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Inputs**: [Completed spec](../spec.md), [plan](../plan.md), and [data model](../data-model.md).

## Contract Boundary

This contract covers existing menu 263, its three active registration sources, and the retained trend export path.
It adds no public endpoint, production class, wrapper, shim, schema, or store.
The coordinator confirmed metadata-only scope and authorized the validated local commit.
This contract retains offered replacement entries and unchanged invocation behavior.
It does not certify working exports of their documented object responses.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) records that separate existing defect.

## C1. Exact Registration Absence

The following exact identifiers must not exist in active selectable rows, catalog keys, or PK metadata keys:

- `getSiteSleSummary`
- `getSiteSleClassifierDetails`

Check all three sources independently.
Do not use prefix matching.
`getSiteSleSummaryTrend` is not the retired `getSiteSleSummary` identifier.
The historical spec, upstream API references, and SDK discovery index may still contain the retired names.
Do not scan those records as active callers or edit them.

The three source owners remain:

- `src/export/endpoint_family_exporter.py`
- `src/export/endpoint_catalog.py`
- `src/refactors/endpoint_primary_key_strategies.py`

No alias from a retired selection to a trend operation is permitted.
The existing resolver's missing-operation behavior remains unchanged.

## C2. Family and Menu Identity

| Set | Required post-removal count |
| --- | ---: |
| Site SLE operations | 15 |
| Stage-two operations | 132 |
| Catalog entries | 284 |
| Site map operations | 7 |
| Site detail operations | 33 |
| Organization detail operations | 61 |
| MSP detail operations | 10 |
| Other detail operations | 6 |

Both trend operations remain selectable.
Every unrelated row and retained row field remains unchanged.
The SLE tuple's only membership difference is the two exact retired rows.
The stage-two aggregate loses only those rows.

Top-level menu numbers, entry counts, categories, handlers, and safety flags remain unchanged.
The inspected baseline has 293 distinct top-level `MenuEntry` identifiers and 179 portal description entries.
Menu 263 remains an `interactive_safe`, non-destructive endpoint-family menu.
Its three fixed labels must read:

```text
Run any site SLE endpoint with scope prompts (15 operations)
```

The fixed labels live in `MistHelper.py`, `web_portal/menu_registry.py`, and `documentation/menu-highlights.md`.

## C3. Retained SDK Resolution and Requests

Resolution must return the actual installed SDK 0.64.0 function object for each retained row.
The rows keep their existing module, required tuple, issue references, and relative order.

| Operation | Required argument order |
| --- | --- |
| `getSiteSleSummaryTrend` | Session, `site_id`, `scope`, `scope_id`, `metric` |
| `getSiteSleClassifierSummaryTrend` | Session, `site_id`, `scope`, `scope_id`, `metric`, `classifier` |

The actual SDK functions construct these request paths:

```text
/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend
/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend
```

The SDK's optional query arguments remain `start`, `end`, and `duration`.
All three default to `None`.
The existing family exporter adds no optional-query prompt and supplies no new query value.
Direct SDK tests can supply those values to verify the existing request construction.

Delete both deprecated attributes temporarily from the actual SDK module in absence-simulation tests.
Both retained function identities, resolutions, and invocation paths must remain available.
Restore the two deleted attributes after each test.
Do not install SDK 0.65.0 or change `mistapi>=0.64.0,<0.65`.

## C4. Prompts and Output Processing

Keep the real `_choose`, `_prompt_identifier`, and `_collect_arguments` methods.
Keep real site selection and the existing EOF-safe input handling.
Blank, invalid, EOF, or interrupted required answers must retain the current cancellation behavior.
An aborted request must not make a trend HTTP request or final output write.

Keep the real SDK endpoint methods, `APIResponse`, and `mistapi.get_all`.
The real pagination helper collects list payloads or dictionaries containing `results`.
For a dictionary without `results`, preserve the existing empty-result behavior.
Do not add a replacement extractor or fallback.
The documented trend objects have this shape and currently produce zero collected records.
Their repair belongs to the separate issue.
Positive list and `results` fixtures prove existing generic processing, not documented trend-object exports.

Keep `_normalize`, flattening, and multiline escaping unchanged.
For a local record with nested `summary.value` and multiline `note`, assert the literal flattened and escaped output.
Do not compute the expected record with the production method being tested.

The final dispatch remains:

```text
DataExporter.write_with_format_selection(
    sanitized_data,
    existing_filename,
    api_function_name=original_trend_identifier,
)
```

The filename retains the selected operation and existing argument labels.
The writer receives the original trend identifier, not a retired alias.
An empty endpoint-family result makes no final writer call.

Mocks are limited to local transport, console input, and final output boundaries.
Preparing local `AppContext` state and a temporary fresh site CSV is test setup, not a replacement implementation.
Real transport responses must include status, JSON body, URL, and prepared request headers.
Successful cases must contain no SDK error log caused by an incomplete response fixture.
Do not replace `_mist_helper`, SDK endpoint methods, resolution, answer collection, pagination, or normalization for the new trend proof.
A real `.test` session transport must not reach the network.

## C5. Keys and Persistence

Both retained PK strategy dictionaries must remain exactly as recorded in [data-model.md](../data-model.md).
Keep all unrelated strategies and the supplemental `setdefault` merge.
Do not change natural, composite, time-series, or other existing key decisions.
Do not add a field or constraint to produce a new trend deduplication guarantee.

Repeated local trend runs must produce the same normalized payload, filename, and routing identifier.
Run the unchanged configured-key and temporary SQLite upsert selectors.
Those tests prove existing persistence contracts without touching live stores.

No schema or data migration is required.
Do not delete an old table, change an index, rewrite stored rows, or clear output files.
Keep the separate menu 73 SLE refusal behavior from issue #3305 unchanged.

## C6. Guard Proof

Use one private typed decision in existing `TestCatalogCoverage`.
It must inspect actual raw sources, not only a separate expected-name fixture.
Do not introduce a production guard class or standalone helper wrapper.

| Case | Required decision | Count evidence |
| --- | --- | --- |
| Each retired identifier against each actual source, before removal | Six absence assertions fail. | Each reports the actual nonzero inspected count. |
| The same six cases, after removal | All pass. | Each reports the actual nonzero inspected count. |
| Either retired selectable row injected into a real source copy | Reject both cases. | Count the copied rows, including the injected row. |
| Either retired catalog entry injected into a real source copy | Reject both cases. | Count the copied catalog keys, including the injected key. |
| Either retired PK entry injected into a real source copy | Reject both cases. | Count the copied metadata keys, including the injected key. |
| Empty source for each of the three kinds | Reject. | Zero is measured and cannot pass. |
| Missing or unreadable required input | Reject. | Report zero before any read, or the actual partial count. |
| Invalid source shape or invalid record | Reject. | Do not substitute an empty source and pass. |

At the inspected baseline, live sources contain 286 selectable rows, 286 catalog entries, and 571 PK keys.
After removal, the corresponding expected measurements are 284, 284, and 569.
Each one-row injection therefore measures 285, 285, or 570.
Compute those counts from the actual input.
Do not substitute these documented numbers for inspection.

Each injected failure must identify the exact injected retired operation.
Each direct live-source case must explicitly assert absence of its named retired identifier.
Do not accept `pytest.skip`, collection failure, a weak truth assertion, or a mock-call assertion as guard evidence.

## C7. References and Regression Boundary

Only these generated outputs may change during later generation:

- `documentation/menu_reference.md`
- `documentation/wiki/Menu-Reference.md`
- `documentation/menu-api/README.md`
- `documentation/menu-api/interactive-safe.md`
- `documentation/wiki/Menu-API-Endpoints.md`
- `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md`

Check current exact PR file ownership again before running either generator.
Repeated runs must preserve identical bytes for all six outputs.
The operation map must pass `--check`.
Do not refresh the vendored SDK index.
Stop and report any additional changed path.

Changed tests are limited to:

- `tests/guardrails/test_endpoint_catalog.py`
- `tests/unit/export/test_endpoint_family_exporter.py`

Run these two existing modules unchanged:

- `tests/unit/web_portal/test_portal_label_accuracy.py`
- `tests/unit/web_portal/test_portal_required_answers.py`

Also run the unchanged contract, configured-key, upsert, and SLE-refusal selectors in [quickstart.md](../quickstart.md).
No shared quality baseline, suppression, exclusion, dependency, or instruction edit is permitted.

## C8. Delivery Stop

The unique later release fragment must name both removals and both retained trends.
Do not edit `README.md`, `CHANGELOG.md`, `.github/copilot-instructions.md`, or `operator-guide.md`.
No new standalone guide is needed.
Issue #3334 is outside this contract.

This planning run ends with five design files.
The completed local implementation uses only the exact reserved paths.
The authorized local commit uses Conventional Commits with the Copilot trailer.
It makes no branch change, PR, shared-context write, container operation, or cloud mutation.
The parent owns publication at position 16 after issue #3366.
Do not publish or deploy without the parent's separate release.
