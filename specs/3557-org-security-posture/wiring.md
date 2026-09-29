# Deferred Wiring: Organization Security Posture Checklist

This planning step may edit only `specs/3557-org-security-posture/**`. Implementation must complete the wiring in a later step.

## Deferred menu wiring

Menu 276 wiring is deferred.

Implementation must update the required menu and registry surfaces after the edit boundary allows it:

- `MistHelper.py`
- `src/utils/operation_registry.py`
- `README.md`
- `documentation/menu_reference.md`
- generated menu reference artifacts

## Deferred primary key strategy

Primary key strategy changes are deferred.

Implementation must decide whether this CSV-only checklist needs an entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. If a database export path stores checklist rows, use `check id` plus organization identity and collection time as the stable key. If the feature remains CSV-only, record why no primary key strategy is necessary.

The implementation must not change `src/refactors/endpoint_primary_key_strategies.py` during this planning step.

## Required implementation wiring

| Surface | Required result |
|---------|-----------------|
| Menu | Menu 276 starts the organization security posture checklist. |
| Operation registry | Menu 276 is classified as safe and works in `--test`. |
| Export | The run writes `data/OrgSecurityPosture.csv`. |
| Checks | The registry contains at least twelve checks. |
| Test mode | The safe test path uses fixture data and no prompt. |
| Documentation | User-facing references describe menu 276 and the CSV output. |
| Release note | The feature-owned changelog fragment moves to the normal release-note location when implementation is allowed to edit it. |

## Source verification before wiring

Before client code is written, implementation must verify these OpenAPI operation IDs in `documentation/mist-api-openapi3json.json` and `mistapi`:

- `getOrgSettings`
- `listOrgSsos`
- `listOrgAdmins`
- `listOrgApiTokens`
- `listOrgWebhooks`
