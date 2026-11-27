# Contract: Apply Response

This contract defines the JSON body that `status` and `submit` return. It holds identifiers and outcomes only. It never holds a payload value, a token, or a secret.

## Body Shape

```json
{"operation_id": "0123456789abcdef0123456789abcdef", "phase": "executing", "organization_id": "3f1c2a9e-0000-4000-8000-000000000001", "site_ids": ["3f1c2a9e-0000-4000-8000-000000000002"], "gateway_ids": ["3f1c2a9e-0000-4000-8000-000000000003"], "items": [{"family_id": "F-04", "action": "create", "object_id": null, "outcome": "verified"}], "error": null}
```

## Fields

| Field | Type | Rule |
| --- | --- | --- |
| `operation_id` | string | Local identifier. |
| `phase` | string | One phase from the issue 4636 phase list. |
| `organization_id` | string | Natural Mist organization ID. |
| `site_ids` | list of strings | Natural Mist site IDs in scope. |
| `gateway_ids` | list of strings | Natural Mist gateway IDs in scope. |
| `items` | list of objects | One entry for each change item, in run order. |
| `items[].family_id` | string | One of `F-01` to `F-08`. |
| `items[].action` | string | `create`, `update`, or `assign`. |
| `items[].object_id` | string or null | Natural Mist ID, or null before a create returns one. |
| `items[].outcome` | string | `verified`, `failed`, `partial`, `indeterminate`, or `not-applied`. |
| `error` | object or null | Fixed `code` and `message` strings. Null when no error exists. |

## Scope View Rule

Before approval, the `status` response for a draft operation lists the same organization, sites, gateways, and items. Each item has a null outcome. Requirement FR-001 uses this view.
