# Research: Organization Security Posture Checklist

## Decision: Use one class for each security setting check

**Rationale**: A small class gives each setting one owner, one stable check ID, one recommended value, and one verdict rule. This matches the review requirement and keeps test failures easy to trace.

**Alternatives considered**:

- A dictionary of lambdas. Rejected because it hides the rule owner and makes logs less clear.
- One large evaluator class. Rejected because it would grow beyond the Five-Item Rule and make one defect affect many checks.

## Decision: Use a registry class for stable check order

**Rationale**: `OrgSecurityPostureCheckRegistry` can return check instances in one stable order. That order becomes the CSV order, which helps reviewers compare runs.

**Alternatives considered**:

- File discovery. Rejected because import order can change.
- Sorting by check ID only. Rejected because area order should stay intentional and readable.

## Decision: Use one runner for source collection, evaluation, export, and summary

**Rationale**: `OrgSecurityPostureRunner` can keep one clear workflow. It gets source data, asks the registry for checks, evaluates checks, writes the CSV, and prints the summary.

**Alternatives considered**:

- Let each check call Mist APIs. Rejected because repeated calls add latency and make test mode harder.
- Put export code in each check. Rejected because checks should only decide verdicts.

## Decision: Treat absent and ambiguous data as `review`

**Rationale**: A security checklist must not pass a setting that was not read. The `review` verdict makes missing evidence visible without reporting a false failure.

**Alternatives considered**:

- Treat absent values as `fail`. Rejected because absence means the tool lacks evidence, not always that the tenant is unsafe.
- Treat absent values as `pass`. Rejected because it creates false assurance.

## Decision: Fail any non-HTTPS webhook URL

**Rationale**: Webhooks can carry security-relevant event data. A URL that does not start with `https://` does not meet the transport requirement.

**Alternatives considered**:

- Mark non-HTTPS webhooks as `review`. Rejected because the requirement states that non-HTTPS webhook URLs fail.

## Decision: Use the existing CSV export path

**Rationale**: MistHelper already standardizes data export under `data/`. Reusing that path keeps operator behavior consistent and avoids a new storage path.

**Alternatives considered**:

- Write CSV directly from the runner. Rejected unless existing export utilities cannot preserve the required file name and columns.
- Add a database table first. Rejected because the first release needs a CSV evidence file only.

## Decision: Verify API operation IDs before client code

**Rationale**: The requested source operation IDs are `getOrgSettings`, `listOrgSsos`, `listOrgAdmins`, `listOrgApiTokens`, and `listOrgWebhooks`. Implementation must verify these IDs and response shapes in `documentation/mist-api-openapi3json.json` and `mistapi` before code uses them.

**Alternatives considered**:

- Trust the names from the feature text. Rejected because OpenAPI and SDK names can drift.
- Use direct HTTP calls. Rejected because MistHelper must use `mistapi` when a method exists.

**Implementation verification**:

| Operation ID | OpenAPI path | SDK module | Response evidence used |
|--------------|--------------|------------|------------------------|
| `getOrgSettings` | `GET /api/v1/orgs/{org_id}/setting` | `mistapi.api.v1.orgs.setting.getOrgSettings` | Organization settings keys read as a mapping. |
| `listOrgSsos` | `GET /api/v1/orgs/{org_id}/ssos` | `mistapi.api.v1.orgs.ssos.listOrgSsos` | SSO rows read as list data for identity evidence. |
| `listOrgAdmins` | `GET /api/v1/orgs/{org_id}/admins` | `mistapi.api.v1.orgs.admins.listOrgAdmins` | Administrator rows read as list data for access evidence. |
| `listOrgApiTokens` | `GET /api/v1/orgs/{org_id}/apitokens` | `mistapi.api.v1.orgs.apitokens.listOrgApiTokens` | Token rows read with `created_time`, `created_at`, `expire_time`, or `expires_at`. |
| `listOrgWebhooks` | `GET /api/v1/orgs/{org_id}/webhooks` | `mistapi.api.v1.orgs.webhooks.listOrgWebhooks` | Webhook rows read with `url`, `urls`, or `webhook_url`. |

**Field verification**:

- `password_policy` includes `enabled`, `min_length`, `expiry_in_days`, `requires_special_char`, and `requires_two_factor_auth`.
- `password_policy.requires_uppercase`, `password_policy.requires_lowercase`, `password_policy.requires_number`, and `password_policy.reuse_history` are treated as review when absent because the current OpenAPI schema does not prove them.
- `ui_idle_timeout` is an integer where `0` disables idle timeout, so the idle timeout check fails `0`.
- `disable_remote_shell` and `disable_pcap` are Boolean organization switches; the recommended value is `true`.
- `junos_shell_access` role values are `admin`, `viewer`, or `none`; the recommended value is `none` for each visible role.
- `switch_mgmt.remove_existing_configs` controls stale configuration cleanup; the recommended value is `true`.
- `pcap_bucket_verified` is read-only evidence that the packet capture bucket is verified.

**Skill citations**:

- `juniper-mist-management/03-security-and-access/02-password-policy-saml-and-certificates.md` names the `Password Policy` page and the common `12` character and `90` day recommendations.
- `juniper-mist-management/02-organization-sites-and-inventory/02-organization-settings-support-and-contracts.md` names the `Organization > Admin > Settings` page, `Session Policy`, `API Token`, and `Webhooks` sections.
- `juniper-mist-management/05-account-app-alerts-api-and-webhooks/02-user-tokens-alert-notifications-and-webhooks.md` names organization token scope and webhook delivery checks.

## Decision: Defer menu wiring and primary key strategy changes

**Rationale**: This step is a planning step with a strict edit boundary. Menu 276 wiring, generated menu references, and primary key strategy changes are implementation work.

**Alternatives considered**:

- Edit the menu and primary key files now. Rejected because the current fleet step allows edits only under `specs/3557-org-security-posture/`.
