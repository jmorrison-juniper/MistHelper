# Data Model: Admin Token Hygiene

## Source Entity: Mist Admin

**Source**: `listOrgAdmins`

| Field | Type | Required | Notes |
| - | - | - | - |
| `admin_id` | string | No | Preferred stable identifier. |
| `email` | string | No | Use as fallback identifier when `admin_id` is missing. |
| `first_name` | string | No | Report metadata only. |
| `last_name` | string | No | Report metadata only. |
| `name` | string | No | Optional display name. |
| `privileges` | list | No | Score role and scope from each item. |
| `enable_two_factor` | boolean | No | Local two-factor configured state. |
| `two_factor_verified` | boolean | No | Local two-factor verification state. |
| `via_sso` | boolean | No | SSO account state. |
| `password_modified_time` | integer | No | Epoch seconds for password age when present. |
| `expire_time` | integer | No | Invite or account expiry time when present. |
| `compliance_status` | string | No | Optional account state. |

### Validation Rules

- Keep every admin source row, even when optional metadata is missing.
- If both `admin_id` and `email` are missing, create a row with identifier
  `unknown`.
- Treat missing two-factor or SSO fields as `unknown`, not as `false`.
- Treat each privilege independently, then score the highest effective access.

## Source Entity: Mist Organization API Token

**Source**: `listOrgApiTokens`

| Field | Type | Required | Notes |
| - | - | - | - |
| `id` | string | No | Preferred stable identifier. |
| `name` | string | Yes by schema | Report display name. |
| `created_by` | string | No | Creator email or identifier. |
| `created_time` | integer | No | Epoch seconds. |
| `last_used` | integer | No | Epoch seconds. Missing means never used. |
| `org_id` | string | No | Organization identifier. |
| `privileges` | list | No | Score write access and scope. |
| `src_ips` | list | No | Source IP restriction list. |
| `key` | string | No | Secret. Delete before scoring, logging, or output. |

### Validation Rules

- Never store `key` in a model that can be logged or exported.
- Keep every token source row, even when optional metadata is missing.
- If `last_used` is missing and `created_time` exists, set idle days from token
  age and add `never_used`.
- If `created_time` is missing, set idle days to `unknown` and add
  `age_unknown`.
- Source IP restriction is present when `src_ips` is a non-empty list.

## Source Entity: Organization Settings

**Source**: `getOrgSettings`

| Field | Type | Required | Notes |
| - | - | - | - |
| `password_policy.enabled` | boolean | No | Local password policy state. |
| `password_policy.expiry_in_days` | integer | No | Schema field for password reset interval. |
| `password_policy.freshness` | integer | No | Example field for password reset interval. |
| `password_policy.min_length` | integer | No | Minimum password length. |
| `password_policy.requires_special_char` | boolean | No | Special character requirement. |
| `password_policy.requires_two_factor_auth` | boolean | No | Organization local two-factor requirement. |
| `ui_idle_timeout` | integer | No | Session idle policy context. |

### Validation Rules

- Read `expiry_in_days` first. If absent, read `freshness`.
- If settings cannot be read, keep admin and token rows and mark settings fields
  as `unknown`.

## Output Entity: Admin Hygiene Row

**File**: `data/AdminHygiene.csv`

| Column | Type | Rule |
| - | - | - |
| `admin_id` | string | Source `admin_id` or blank. |
| `email` | string | Source email or blank. |
| `name` | string | Best display name from source fields. |
| `role_summary` | string | Stable summary of all privilege role values. |
| `site_scope` | string | `all_sites`, `selected_sites`, `site_groups`, `org`, `msp`, or `unknown`. |
| `two_factor_state` | string | `enabled`, `verified`, `disabled`, or `unknown`. |
| `sso_state` | string | `sso`, `local`, or `unknown`. |
| `password_age_days` | integer or string | Whole days or `unknown`. |
| `invite_expiry` | string | ISO 8601 time, blank, or `unknown`. |
| `findings` | string | Pipe-separated finding labels. |

### Admin Findings

| Finding | Rule |
| - | - |
| `super_user` | Any effective privilege equals Super User access at organization scope. |
| `no_two_factor_no_sso` | Two-factor is disabled or unverified, and SSO state is local. |
| `stale_invite` | Invite expiry is in the past, or source state shows an expired invitation. |
| `unknown_role` | A privilege role value cannot be mapped. |
| `unknown_security_state` | Two-factor and SSO state are both unknown. |

## Output Entity: Token Hygiene Row

**File**: `data/TokenHygiene.csv`

| Column | Type | Rule |
| - | - | - |
| `id` | string | Source token `id` or blank. |
| `name` | string | Source token name. |
| `created_by` | string | Source creator or blank. |
| `created_time` | string | ISO 8601 time or `unknown`. |
| `last_used` | string | ISO 8601 time, `never`, or `unknown`. |
| `idle_days` | integer or string | Whole days or `unknown`. |
| `privilege_summary` | string | Stable summary of role and scope. |
| `source_ip_restriction_present` | boolean | `true` when `src_ips` is non-empty. |
| `findings` | string | Pipe-separated finding labels. |

### Token Findings

| Finding | Rule |
| - | - |
| `never_used` | `last_used` is missing. |
| `idle_token` | `idle_days` is greater than or equal to `TOKEN_IDLE_DAYS`. |
| `unrestricted_write_token` | Token has org-wide write privilege and no source IP restriction. |
| `age_unknown` | `created_time` is missing or invalid. |
| `unknown_privilege` | A privilege role or scope value cannot be mapped. |

## Output Entity: Console Summary

| Field | Rule |
| - | - |
| `super_users` | Count admin rows with `super_user`. |
| `admins_no_two_factor_no_sso` | Count admin rows with `no_two_factor_no_sso`. |
| `idle_tokens` | Count token rows with `idle_token`. |
| `unrestricted_write_tokens` | Count token rows with `unrestricted_write_token`. |

## State Transitions

This feature does not change Mist state. It converts live source data into
report rows, writes output through the configured exporter, and prints a
summary.
