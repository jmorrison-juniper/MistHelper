# Contract: Mist API Source Operations

Implementation must verify each source operation before writing client code.

Verification sources:

1. `documentation/mist-api-openapi3json.json`
2. `mistapi`

## Required operation IDs

| Operation ID | Planned use | Required verification |
|--------------|-------------|-----------------------|
| `getOrgSettings` | Read organization settings for password policy, session policy, API policy, remote shell, packet capture, and stale cleanup. | Confirm the operation exists and identify the exact response keys. |
| `listOrgSsos` | Read federated identity evidence for checks that need review context. | Confirm the operation exists and identify enabled SSO fields. |
| `listOrgAdmins` | Read administrator scope evidence for API access review. | Confirm the operation exists and identify role and privilege fields. |
| `listOrgApiTokens` | Read API token expiration evidence. | Confirm the operation exists and identify expiration and creation fields. |
| `listOrgWebhooks` | Read webhook URL evidence. | Confirm the operation exists and identify URL fields. |

## Fail-safe source rules

- If an operation does not exist in OpenAPI or `mistapi`, implementation must stop and update this plan before client code is written.
- If a response field is absent, the affected check must return `review`.
- If a response field type is unexpected, the affected check must return `review`.
- If a value contains a secret or token, the result must redact it before export or logging.

## Source collection contract

The source collector returns one `OrganizationSecuritySourceData` object. Checks must read only that object. Checks must not make their own Mist API calls.

## Verified response keys

| Check area | Source operation ID | Response keys |
|------------|---------------------|---------------|
| Password policy | `getOrgSettings` | `password_policy.enabled`, `password_policy.min_length`, `password_policy.requires_special_char`, `password_policy.requires_two_factor_auth`, `password_policy.expiry_in_days` |
| Password policy legacy evidence | `getOrgSettings` | `password_policy.requires_uppercase`, `password_policy.requires_lowercase`, `password_policy.requires_number`, `password_policy.reuse_history` return `review` when absent. |
| Session policy | `getOrgSettings` | `ui_idle_timeout`, `session_policy.max_lifetime_hours` |
| API policy | `getOrgSettings` | `api_policy.access`; pass values are `disabled`, `restricted`, and `admins_only`; fail values are `enabled`, `unrestricted`, and `all_admins`; all other values return `review`. |
| Remote shell | `getOrgSettings` | `disable_remote_shell`, `junos_shell_access` as a role-to-access mapping. Known role keys include `admin`, `helpdesk`, `read`, and `write`; each visible role value must be `none`. |
| Packet capture | `getOrgSettings` | `disable_pcap`, `pcap_bucket_verified` |
| Stale cleanup | `getOrgSettings` | `switch_mgmt.remove_existing_configs` |
| SSO evidence | `listOrgSsos` | `enabled`, `id`, `name`, `domain` when present |
| Administrator evidence | `listOrgAdmins` | `role`, `privileges`, `email` when present |
| API token evidence | `listOrgApiTokens` | `created_time`, `created_at`, `expire_time`, `expires_at` |
| Webhook evidence | `listOrgWebhooks` | `url`, `urls`, `webhook_url` |
