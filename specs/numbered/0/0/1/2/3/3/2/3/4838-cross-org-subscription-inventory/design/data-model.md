# Data Model: Cross-Org Subscription and Stock Inventory

## Organization Scope

| Field | Type | Validation |
|---|---|---|
| `msp_id` | string or missing | Use only for MSP-discovered organizations |
| `org_id` | string | Required for organization-specific reads |
| `org_name` | string | Use the API name or a missing marker |
| `source` | string | One of direct, MSP, or configured |
| `request_status` | string | One of success, partial, failed, or unavailable |
| `error` | string | Visible only for a failed request |

## Subscription Purchase

| Field | Type | Validation |
|---|---|---|
| `record_id` | string or missing | Use the source record ID when available |
| `subscription_id` | string or missing | Preserve the source subscription ID |
| `order_id` | string or missing | Preserve the source order ID |
| `subscription_type` | string | Required or missing |
| `quantity` | integer or missing | Reject negative and fractional values |
| `remaining_quantity` | integer or missing | Reject negative values |
| `start_date` | ISO date or missing | Normalize supported date shapes |
| `end_date` | ISO date or missing | Normalize supported date shapes |
| `created_date` | ISO date or missing | Normalize supported date shapes |
| `deal_period` | string | One of original-deal, post-original-deal, or missing |
| `source` | string | One of organization-summary or MSP-license |

## Subscription Balance

| Field | Type | Validation |
|---|---|---|
| `subscription_type` | string | Required or missing |
| `purchased_quantity` | integer or missing | Sum valid purchase records |
| `entitled_quantity` | integer or missing | Read the entitlement map |
| `in_use_quantity` | integer or missing | Sum usage across all organization sites |
| `unused_entitlement` | integer or missing | Maximum of entitled minus in-use |
| `over_entitlement` | integer or missing | Maximum of in-use minus entitled |
| `status` | string | One of Active, Expired, Exceeded, Inactive, or Missing |
| `start_date` | ISO date or missing | Use the earliest valid purchase start date |
| `end_date` | ISO date or missing | Use the latest valid subscription end date |
| `days_remaining` | integer or missing | Clamp expired values to zero |
| `band` | string | One of expired, 0-30 days, 31-90 days, more than 90 days, or Missing |

## Inventory Asset

| Field | Type | Validation |
|---|---|---|
| `serial` | string or missing | Preserve source serial |
| `mac` | string or missing | Preserve source MAC |
| `model` | string or missing | Preserve source model |
| `name` | string or missing | Preserve source name |
| `device_type` | string | One of ap, switch, gateway, mxedge, router, or other |
| `site_id` | string or missing | Missing means stock |
| `deployment_status` | string | One of assigned or stock |

## Stock Asset

| Field | Type | Validation |
|---|---|---|
| `organization_id` | string | Required |
| `organization_name` | string | Required or missing |
| `serial` | string or missing | Preserve one inventory identity |
| `mac` | string or missing | Preserve one inventory identity |
| `model` | string or missing | Preserve source model |
| `device_type` | string | Preserve normalized inventory type |
| `license_review_required` | string | One of yes or unknown |
| `jsi_match_status` | string | One of matched, no-match, unavailable, or missing |
| `contract_status` | string or missing | Preserve JSI evidence |
| `contract_end_date` | ISO date or missing | Preserve only an available date |

## Contract Evidence

| Field | Type | Validation |
|---|---|---|
| `serial` | string or missing | Use serial as the stock join key |
| `model` | string or missing | Preserve JSI model |
| `status` | string or missing | Preserve JSI status |
| `has_support` | boolean or missing | Preserve JSI support evidence |
| `claimed` | boolean or missing | Preserve JSI claim state |
| `contract_end_date` | ISO date or missing | Do not infer a date |
| `request_status` | string | One of success, partial, failed, or unavailable |

## Output State

Each organization result contains one final request status.
Partial means at least one source read succeeded.
Failed means no source read succeeded.
Unavailable means the feature has no linked JSI account or no permitted JSI read.
A missing source value remains Missing and never becomes a numeric zero.
