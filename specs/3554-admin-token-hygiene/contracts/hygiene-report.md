# Contract: Admin and API Token Hygiene Report

## Scope

This contract defines the observable behavior of menu 273. It does not define a
new HTTP API.

## Inputs

| Input | Source | Required | Rule |
| - | - | - | - |
| Organization ID | Existing MistHelper org resolver | Yes | Use the active organization. |
| Mist API session | Existing shared session | Yes | Use the installed `mistapi` SDK. |
| Admins | `listOrgAdmins` | No | Empty data is valid. |
| Organization API tokens | `listOrgApiTokens` | No | Empty data is valid. |
| Organization settings | `getOrgSettings` | No | Missing settings become `unknown` context. |
| `TOKEN_IDLE_DAYS` | Environment | No | Default is `90`. |

## Admin CSV Output

**File**: `data/AdminHygiene.csv`

**Header**:

```text
admin_id,email,name,role_summary,site_scope,two_factor_state,sso_state,password_age_days,invite_expiry,findings
```

**Rules**:

1. Write one row per administrator.
2. Keep rows when optional fields are missing.
3. Use pipe-separated finding labels.
4. Use stable role and scope summaries.
5. Do not include secrets.

## Token CSV Output

**File**: `data/TokenHygiene.csv`

**Header**:

```text
id,name,created_by,created_time,last_used,idle_days,privilege_summary,source_ip_restriction_present,findings
```

**Rules**:

1. Write one row per organization API token.
2. Never include the token `key` field.
3. Treat missing `last_used` as `never`.
4. Set `idle_days` to token age when the token was never used and
   `created_time` exists.
5. Set `source_ip_restriction_present` to `true` only when `src_ips` is
   non-empty.

## Console Summary

The operation must print or log a summary that contains these counts:

| Count | Rule |
| - | - |
| Super Users | Admin rows with `super_user`. |
| Admins with no two-factor authentication and no SSO | Admin rows with `no_two_factor_no_sso`. |
| Idle tokens | Token rows with `idle_token`. |
| Unrestricted write tokens | Token rows with `unrestricted_write_token`. |

## Redaction Contract

The token key value must not appear in:

1. Logs.
2. Console output.
3. `AdminHygiene.csv`.
4. `TokenHygiene.csv`.
5. Exceptions.
6. Test failure output that prints model objects.

Implementation must drop or redact `key` before it builds a model object that
can be logged or exported.

## Failure Behavior

| Condition | Required behavior |
| - | - |
| No admins | Write `AdminHygiene.csv` with headers and zero rows. |
| No tokens | Write `TokenHygiene.csv` with headers and zero rows. |
| Settings read fails | Continue report generation and mark settings context as `unknown`. |
| Admin read fails | Fail the operation and do not report success. |
| Token read fails | Fail the operation and do not report success. |
| Invalid `TOKEN_IDLE_DAYS` | Log a clear error and use the repository-standard configuration handling path. |
