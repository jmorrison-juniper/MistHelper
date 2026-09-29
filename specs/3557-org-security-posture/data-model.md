# Data Model: Organization Security Posture Checklist

## Entity: SecurityPostureCheck

Represents one stable rule that evaluates one organization security setting.

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `check_id` | string | Yes | Stable ID in the `ORGSEC-AREA-NNN` format. |
| `area` | string | Yes | Human-readable area name. |
| `setting_path` | string | Yes | Organization setting path that the reviewer can find. |
| `recommended_value` | string | Yes | Expected secure value. |
| `source_page` | string | Yes | Mist page or source resource for the setting. |

## Entity: SecurityPostureCheckResult

Represents one CSV row.

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `check id` | string | Yes | Matches the owning `SecurityPostureCheck.check_id`. |
| `area` | string | Yes | Matches the owning check area. |
| `setting path` | string | Yes | Matches the owning check setting path. |
| `current value` | string | Yes | Uses a safe display value. Secrets must be redacted. |
| `recommended value` | string | Yes | Matches the owning recommended value. |
| `verdict` | string | Yes | One of `pass`, `fail`, or `review`. |
| `reason` | string | Yes | One sentence that explains the verdict. |

## Entity: OrganizationSecuritySourceData

Holds the source data that all checks evaluate.

| Field | Source operation ID | Purpose |
|-------|---------------------|---------|
| `org_settings` | `getOrgSettings` | Password policy, session policy, API policy, remote shell, packet capture, and stale cleanup settings. |
| `org_ssos` | `listOrgSsos` | Federated identity evidence for settings that require review context. |
| `org_admins` | `listOrgAdmins` | Administrator access evidence for API policy review. |
| `org_api_tokens` | `listOrgApiTokens` | Token age and expiration evidence. |
| `org_webhooks` | `listOrgWebhooks` | Webhook URL evidence. |

Implementation must verify each operation ID in `documentation/mist-api-openapi3json.json` and in `mistapi` before it writes client code.

## Entity: OrgSecurityPostureCheckRegistry

Returns the checks in a stable order.

| Field | Type | Rule |
|-------|------|------|
| `checks` | list of check classes | Contains each enabled check exactly once. |

Validation rules:

- No duplicate `check_id` value is allowed.
- The registry must contain at least twelve checks.
- The registry order must be deterministic.

## Entity: OrgSecurityPostureRunner

Coordinates one checklist run.

| Step | Input | Output |
|------|-------|--------|
| Build source data | Organization context or test fixture | `OrganizationSecuritySourceData` |
| Load checks | Registry | Ordered check list |
| Evaluate checks | Source data and checks | `SecurityPostureCheckResult` rows |
| Export CSV | Result rows | `data/OrgSecurityPosture.csv` |
| Summarize | Result rows | Console counts for `pass`, `fail`, and `review` |

## Check Registry

| Check ID | Class name | Area | Setting path |
|----------|------------|------|--------------|
| `ORGSEC-PASSWORD-001` | `PasswordPolicyEnabledCheck` | Password policy | `organization settings > password policy > enabled` |
| `ORGSEC-PASSWORD-002` | `PasswordMinimumLengthCheck` | Password policy | `organization settings > password policy > minimum length` |
| `ORGSEC-PASSWORD-003` | `PasswordUppercaseRequiredCheck` | Password policy | `organization settings > password policy > uppercase required` |
| `ORGSEC-PASSWORD-004` | `PasswordLowercaseRequiredCheck` | Password policy | `organization settings > password policy > lowercase required` |
| `ORGSEC-PASSWORD-005` | `PasswordNumberRequiredCheck` | Password policy | `organization settings > password policy > number required` |
| `ORGSEC-PASSWORD-006` | `PasswordSpecialCharacterRequiredCheck` | Password policy | `organization settings > password policy > special character required` |
| `ORGSEC-PASSWORD-007` | `PasswordReuseHistoryCheck` | Password policy | `organization settings > password policy > password reuse history` |
| `ORGSEC-PASSWORD-008` | `PasswordMaximumAgeCheck` | Password policy | `organization settings > password policy > maximum password age` |
| `ORGSEC-SESSION-001` | `SessionIdleTimeoutCheck` | Session policy | `organization settings > session policy > idle timeout` |
| `ORGSEC-SESSION-002` | `SessionMaximumLifetimeCheck` | Session policy | `organization settings > session policy > maximum session lifetime` |
| `ORGSEC-API-001` | `ApiAccessRestrictionCheck` | API policy | `organization settings > API policy > API access` |
| `ORGSEC-API-002` | `ApiTokenExpirationCheck` | API policy | `organization settings > API policy > token expiration` |
| `ORGSEC-API-003` | `ApiWebhookHttpsCheck` | API policy | `organization settings > API policy > webhook URLs` |
| `ORGSEC-REMOTE-001` | `RemoteShellDisabledCheck` | Remote shell | `organization settings > remote shell` |
| `ORGSEC-CAPTURE-001` | `PacketCaptureDisabledCheck` | Packet capture | `organization settings > packet capture` |
| `ORGSEC-CLEANUP-001` | `StaleCleanupEnabledCheck` | Stale configuration cleanup | `organization settings > stale configuration cleanup` |

## State Rules

- A check returns `pass` only when the source data clearly meets the recommended value.
- A check returns `fail` when the source data clearly violates the recommended value.
- A check returns `review` when the source value is absent, unreadable, ambiguous, or needs exception evidence.
- A reason that reports absent source data must contain the word `absent`.
