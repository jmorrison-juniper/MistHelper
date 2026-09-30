# Data Model: Subscription Contract Expiry Report

## Entity: ReportContext

`ReportContext` identifies one report run.

| Field | Type | Validation |
| - | - | - |
| `org_id` | `str` | Required UUID string from organization selection. |
| `report_date` | `date` | Required. Defaults to the local run date. |

## Entity: LicenseSummarySource

`LicenseSummarySource` holds the SDK response from `getOrgLicensesSummary`.

| Field | Type | Validation |
| - | - | - |
| `entitled` | `dict[str, int]` | Missing map becomes an empty map. |
| `licenses` | `list[dict[str, object]]` | Missing list becomes an empty list. |
| `summary` | `dict[str, object]` | Missing map becomes an empty map. |

## Entity: LicenseUsageSource

`LicenseUsageSource` holds one SDK response row from `getOrgLicensesBySite`.

| Field | Type | Validation |
| - | - | - |
| `site_id` | `str | None` | Optional site identifier. |
| `num_devices` | `int | None` | Optional device count. |
| `usages` | `dict[str, int]` | Missing map becomes an empty map. |
| `fully_loaded` | `dict[str, object]` | Missing map becomes an empty map. |

## Entity: JsiContractSource

`JsiContractSource` holds one `results[]` row from
`searchOrgJsiAssetsAndContracts`.

| Field | Type | Validation |
| - | - | - |
| `serial` | `str | None` | Missing value becomes the missing value marker. |
| `model` | `str | None` | Missing value becomes the missing value marker. |
| `sku` | `str | None` | Optional. |
| `type` | `str | None` | Optional. |
| `warranty_type` | `str | None` | Maps to contract status when available. |
| `eol_time` | `int | str | None` | Optional source date value. |
| `eos_time` | `int | str | None` | Optional source date value. |

## Entity: SubscriptionExpiryRow

`SubscriptionExpiryRow` is one scored subscription type for
`SubscriptionExpiry.csv`.

| Field | Type | Validation |
| - | - | - |
| `subscription_type` | `str` | Required. Use a missing value marker only when no source key exists. |
| `entitled` | `int | str` | Keep missing values visible. |
| `usage` | `int | str` | Keep missing values visible. |
| `status` | `str` | One of `Active`, `Expired`, `Exceeded`, or `Inactive`. |
| `end_date` | `str` | ISO date or missing value marker. |
| `days_remaining` | `int | str` | Integer when date exists, otherwise missing value marker. |
| `band` | `str` | One of `expired`, `0-30 days`, `31-90 days`, `more than 90 days`, or missing value marker. |

### Subscription scoring rules

1. If usage is greater than entitlement, set status to `Exceeded`.
2. If the end date is before the report date, set status to `Expired` unless a
   more severe source status exists.
3. If the source marks a subscription inactive, preserve status `Inactive`.
4. If no severe condition applies, set status to `Active`.
5. If no end date exists, show the missing value marker and do not assign a
   dated band.
6. If the date difference is less than 0, export days remaining as `0` and
   assign band `expired`.
7. If days remaining is 0 through 30, assign band `0-30 days`.
8. If days remaining is 31 through 90, assign band `31-90 days`.
9. If days remaining is more than 90, assign band `more than 90 days`.

## Entity: ContractExpiryRow

`ContractExpiryRow` is one scored device contract for `ContractExpiry.csv`.

| Field | Type | Validation |
| - | - | - |
| `serial` | `str` | Required for identity. Use a missing value marker if absent. |
| `model` | `str` | Use a missing value marker if absent. |
| `contract_status` | `str` | One of `Declined`, `EOS`, `Service Available`, `Active`, or a visible source value. |
| `contract_state` | `str` | One of `Supported` or `Unsupported`. |
| `end_date` | `str` | ISO date or missing value marker. |
| `bucket` | `str` | One of `Expired`, `0-3 months`, `0-12 months`, `more than 12 months`, or missing value marker. |

### Contract scoring rules

1. If contract status is `Active`, set contract state to `Supported`.
2. If contract status is `Declined`, `EOS`, or `Service Available`, set
   contract state to `Unsupported`.
3. If no supported status exists, preserve the visible source status and mark
   the state `Unsupported`.
4. If no end date exists, show the missing value marker and do not assign a
   dated bucket.
5. If the end date is before the report date, assign bucket `Expired`.
6. If the end date is today through three calendar months after the report
   date, assign bucket `0-3 months`.
7. If the end date is more than three months and not more than twelve calendar
   months after the report date, assign bucket `0-12 months`.
8. If the end date is more than twelve calendar months after the report date,
   assign bucket `more than 12 months`.

## Entity: ConsoleSummary

`ConsoleSummary` holds row counts printed after export.

| Field | Type | Validation |
| - | - | - |
| `subscription_band_counts` | `dict[str, int]` | Contains every subscription band with zero defaults. |
| `contract_bucket_counts` | `dict[str, int]` | Contains every contract bucket with zero defaults. |

## State transitions

The report does not change Mist state. Report rows move through these internal
states only:

1. Source response row.
2. Normalized dataclass.
3. Scored output row.
4. Exported CSV row.
5. Counted summary row.
