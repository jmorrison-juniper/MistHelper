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
