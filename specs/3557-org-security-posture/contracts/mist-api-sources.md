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
