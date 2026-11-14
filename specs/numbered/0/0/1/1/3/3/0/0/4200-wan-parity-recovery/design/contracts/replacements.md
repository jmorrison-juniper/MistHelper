# Independently designed WAN replacement contracts

## Authority and evidence

The later user direction authorizes building defensible replacements when original contracts or acceptance evidence are absent.
This policy defines destination behavior. It does not assert source equivalence.
Keep original acceptance states and historical records unchanged.
Use four evidence labels: verified source contract, designed replacement, operator declaration, and synthetic validation.
Absent network facts remain absent. A synthetic record cannot establish a production fact.

## Version one observation reports

Reports use the existing bounded retained view for one full identity.
Group present hourly projection values by exact metric name and unit.
Give each present value one equal weight. Missing values contribute neither zero nor a weight.
Retain missing-hour and measurement-completeness states separately.
Report present-value count, minimum, mean, nearest-rank p95, and maximum.
For N sorted values, p95 selects the value at one-based rank `ceil(95*N/100)`.
Do not interpolate percentiles or combine incompatible units.
Compute the mean from exact rational representations of supplied decimal strings.
Display derived means with at most 28 significant decimal digits and half-even rounding.
Remove insignificant trailing zeros. Preserve original values in the existing table.
Empty groups have no statistic. Do not substitute zero.
These are hourly-projection observation statistics, not raw-sample percentiles or duration-weighted measurements.
Source sample timestamps, weighting, and statistical equivalence remain unverified.

For percentage units `%` and `percent`, permit an integer threshold from zero through 100.
The default threshold is 80. Values strictly greater than the threshold count as exceedances.
The longest run counts adjacent above-threshold UTC hour keys.
A missing hour, absent value, or value not above the threshold breaks a run.
Other units have no percentage-threshold result.
Counts and runs never imply congestion minutes, healthy duration, or availability.
Changing the threshold performs only the existing scoped view read.
Local plot zoom, visibility, and rectangle selection do not change this full-window report.

## Replacement policies for remaining goals

| Goal | Designed contract | External facts or later implementation |
| --- | --- | --- |
| Performance ranking | Rank a selected metric/unit by its observed value. Use full identity for stable ties and name the bounded population. | Do not infer complete organization inventory, role comparison, or region membership. |
| Capacity, region, and role | Accept explicit operator declarations with full identity, UTC effective interval, and declaration provenance. | Actual declarations must come from an operator or verified system. A fixture is not network configuration. |
| Failure reporting | Distinguish observed state changes from complete event intervals. Never carry a state through an unobserved gap. | Source event taxonomy, authoritative ordering, and elapsed coverage need actual evidence. |
| SLE | Preserve catalog identifiers and supplied raw gateway fields with explicit units and completeness limits. | Do not invent classifier formulas, duration units, or impacted interface/peer mappings. |
| Long-term history | Validate thirteen calendar months using independently generated synthetic hour keys in isolated stores. | Real retained data, production capacity, and deployment acceptance require real environments and authorization. |
| Historical recovery | Validate supplied archive/query metadata before any local import. Preserve source timestamps and report rejected or incomplete pages. | No documented Mist historical-write operation exists. Do not manufacture older observations or write into Mist. |
| Visual acceptance | Use independently designed, accessible destination interactions and record actual browser results. | Internal source captures do not authorize importing protected implementation or assets. |
| Historical task mapping | Preserve the original ledger and maintain an explicit replacement-task map. Mark absent historical states unknown. | Do not reconstruct the original 87 checkbox states from guesses. |
| Preservation | Preserve each verified commit in a uniquely named recovery ref, with its exact remote SHA verified. | Do not modify the existing PR branch, enable publication, or overwrite another ref. |

## Historical query eligibility

### Version-one ranking

Rank observations, not inferred device quality or complete organization inventory.
The cached population is the full authorized route selection before lexical table filtering or display pagination.
The retained population is the existing selected window for one full identity. Without that window, report unavailable.
Select an exact metric name and unit together. Never convert units or substitute missing values.
Order present values numerically, descending by default or explicitly ascending.
Resolve equal-value ties by full natural identity, UTC observation hour, and collection time, always ascending.
Show at most twenty ranked rows. Report population, eligible, displayed, missing, and incompatible-unit counts separately.
Missing cache coverage and source completeness remain unknown. No ranking control starts an additional request or read.

### Version-one declarations

Accept a version-one object with full identity, UTC effective bounds, declared values, and `operator-declaration` provenance.
Limit each declaration to 64 KiB. Reject every unsupported field rather than retaining undeclared metadata.
Require capacity in bit/s to be finite and positive. Region and role remain bounded, printable operator text, not inferred taxonomies.
Require at least one declared value and an increasing UTC effective interval.
Require exact `DECLARE` before accepting metadata for an identity in the current cached tenant.
Reject changed metadata at an existing identity/effective-interval key. Identical replay changes nothing.
Keep at most one thousand declarations per selected organization in process-lifetime state.
Provide JSON export and state clearly that a restart removes this state.
This feature changes neither Mist configuration nor observed metric values.

### Version-one archive import

Accept at most eight MiB and 9528 unique projection records, spanning at most 397 days.
Before CSRF processing, replacement POST requests require a known content length of at most eight MiB plus 64 KiB.
Unknown lengths return HTTP 411 without reading the stream, including server-terminated streams.
Excessive declared lengths return HTTP 413 before form parsing or membership access.
Per-request multipart parsing permits five parts and 128 KiB of field memory, without increasing stricter application limits.
The parser bounds file spooling through the complete body limit. Unrelated requests keep their existing limits and CSRF behavior.
Require at least one projection record. Limit each printable metric name and unit to 128 characters.
Require version, provenance, full identity, half-open UTC bounds with `complete: false`, and records.
Validate every record, exact identity, matching provenance, unique hour, finite values, units, and UTC timestamps before storage.
Reject unknown envelope fields, incomplete identities, out-of-window rows, duplicate hours, and unsupported completeness claims.
Synthetic import requires exact `IMPORT_SYNTHETIC` and uses only a separate process-lifetime synthetic store.
Synthetic export preserves provenance and original bounds. It does not enable the live history codec.
The synthetic process store caps combined archive and record bytes at eight MiB per organization and distinct hour keys at 9528.
Preserve full-identity hour keys across overlapping synthetic archives. Reject conflicting values before changing any state.
Live import requires exact `IMPORT` and an uploaded-byte SHA-256 digest present in a trusted server-side review map for the full identity.
An archive cannot approve its own digest. No review map exists by default.
This approval establishes reviewed input admission, not endpoint retention or source sampling completeness.
Atomically append new live hour keys. Preserve identical replay and reject changed existing keys without replacing any record.
SQLite executes this decision under one write transaction. Arango uses non-overwriting inserts in one streaming transaction.
The SQLite append primitive requires an existing hourly table. It creates no schema or database.
Arango performs one bounded existing-key query and one bulk append. Every document acknowledgment must match its requested key.
No raw-sample import, Mist write, historical synthesis, deletion, or schema migration occurs.
Tests use temporary SQLite, isolated synthetic state, or mocked live-shaped inputs and Arango transactions.
Native SQLite tests exercise the generic append primitive with synthetic payloads. The application read codec still rejects them.
No invented fixture becomes real live history.

Gateway insight start/end/interval/page controls establish query capability only.
An interval applies an aggregation function. Do not label its returned aggregates as unaggregated samples.
Require actual metric metadata before selecting supported intervals or retention windows.
Example `max_age` values and product-level thirteen-month Premium Analytics descriptions are not endpoint or tenant guarantees.
Validate `rt`/`results` positional alignment, query bounds, page limits, and response metadata.
Missing metadata or incomplete coverage remains explicit and cannot become successful complete backfill.
For cursor searches, use only the cursor supplied in the preceding Mist `next` URL.
Never construct a `search_after` cursor.
Peer searches with time controls do not establish peer sample history, aggregation, or retention.
This contract authorizes no live request or production write.

The official public schema research is at:
<https://raw.githubusercontent.com/mistsys/mist_openapi/master/mist.openapi.yaml>.
The bundled OpenAPI remains the executable-contract reference for independently verified SDK behavior.

## Synthetic historical validation

Generate records independently, using explicit UTC hour keys and `synthetic` provenance.
Use only a temporary, existing SQLite file and mocked Arango adapters.
The application codec rejects synthetic records on reads and writes. Preserve that guard.
Validate native SQLite payload storage separately from application-codec acceptance.
Mocked Arango checks prove query construction and synthetic rejection, not executed database persistence.
Read exact half-open thirteen-calendar-month intervals and compare complete identities and payloads.
Exercise missing periods, repeated writes, and boundary exclusions.
Record actual counts and outcomes without relabeling them as live data.
No test may select a production database, inherit credentials, or start an external service.
Passing synthetic validation proves the exercised local contract, not real historical availability or production capacity.
