# Research: SLE window identity

## Decisions

Use request identifiers plus response `start` and `end`.
Use `classifier_name` for the classifier endpoint because flattening produces that field from the nested classifier object.
The request classifier supplies the selected identity, not an arbitrary response value.

Use a deterministic digest only for these two complete SLE composite strategies in ArangoDB.
Keep all unrelated primary-key behavior unchanged.

For SQLite, add `misthelper_sle_window_key` to new rows and create a unique index on that column.
Legacy rows receive no value and remain outside the new uniqueness constraint.
Do not rebuild the table or change its existing primary key.
Reject incoming surrogate IDs so a new row cannot replace a legacy row.

Rejected alternatives: destructive migration violates the supplied decision.
A strategy-only repair fails because old SQLite primary keys remain unchanged and Arango uses only the first primary-key column.
A global composite-key repair changes unrelated endpoint behavior.

## Complete registry measurement

Measured `5bacafb3ee1aae6e46aeee7c45e09bce708ad7c3` before repair.
The runtime table contains 584 entries, including 318 auto-increment entries.
Eleven operation names contain `summary` or `trend`. Two contain `trend`.
The scan examines every entry, then resolves every matching OpenAPI response and schema reference.
It maps 517 entries to OpenAPI operations. The other 67 entries have no matching operation ID.
Of 126 schemas with required start/end boundaries, 122 are result envelopes and four are direct window objects.
Seventy-seven auto-increment strategies have result-envelope schemas.
Those envelopes require separate row-shape review because their returned rows do not necessarily retain the envelope boundaries.
The four direct objects are both repaired trends, `getSiteSleHistogram`, and `getSiteSleImpactSummary`.

| Entry | Existing strategy | Evidence and decision |
| --- | --- | --- |
| `getOrgLicensesSummary` | Auto | Entitlement and usage snapshot, no top-level window |
| `showSiteGatewayOspfSummary` | Composite | Asynchronous command session, already composite |
| `showSiteDeviceBgpSummary` | Composite | Asynchronous command session, already composite |
| `orgDeviceModelSummary` | Auto | Local model-count report, not an API window |
| `orgDeviceFirmwareSummary` | Auto | Local firmware-count report, not an API window |
| `listOrgDevicesSummary` | Auto | Device-count snapshot, no top-level window |
| `getSiteCallsSummary` | Auto | Aggregated call counts, no top-level window |
| `siteVariableSummary` | Natural | Local per-site variable report |
| `getSiteSleClassifierSummaryTrend` | Auto | Required start/end and time-series description, repair here |
| `getSiteSleImpactSummary` | Auto | Required start/end, metric, classifier, and failure, report separately |
| `getSiteSleSummaryTrend` | Auto | Required start/end and time-series description, repair here |

The complete table has two additional direct window-object defects: `getSiteSleHistogram` and `getSiteSleImpactSummary`.
The histogram requires `metric`, `start`, `end`, `data`, `x_label`, and `y_label`.
The impact summary requires `classifier` and `failure` in addition to its metric and window.
Both require separate schema review, not unrequested registry edits.
The guard reports both defects explicitly and rejects an unrecorded direct window object.
Follow-up issue #4347 records the impact-summary defect. Issue #4348 records the histogram defect.

## Structural review

The first analysis found six top-level declarations in the proposed schema utility module.
Move the helper to the owned strategy module and update every import.
The strategy module then has two declarations. The schema utility module stays unchanged with five declarations.
No compatibility import or old helper location remains.
This measurement does not certify all remaining auto-increment entries as keyless.

## Evidence

The authority is `documentation/mist-api-openapi31json.json`, under `paths` and `components`.
The relevant schemas are `sle_summary_trend`, `sle_classifier_summary_trend`, and `sle_impact_summary`.
The exporter currently flattens responses without request identifiers.
SQLite clears auto-increment tables, so the old duplicate-growth claim applies to ArangoDB, not SQLite.
Arango assigns UUID keys to auto-increment documents and uses the first field for other keys.

## Hooks

The mandatory before-specify branch hook completed.
Optional commit hooks are disabled in `git-config.yml`. Disabled companion hooks do not run.
The active feature path is command-scoped to avoid changing another feature selector.
