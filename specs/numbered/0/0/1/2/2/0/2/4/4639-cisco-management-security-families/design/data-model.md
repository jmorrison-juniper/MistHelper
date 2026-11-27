# Data Model: Review management and security configuration families

## Entities

| Entity | Natural key | Attributes | Rules |
| --- | --- | --- | --- |
| Management family | `family_id`, one of MGT-01 to MGT-14 | Fixed label, disposition, source row, and fixed limit | One row for each family. The label and limit never change at run time. |
| Keyword phrase | Lowercase phrase from the allow-list | Family ID and scope (top-level or child) | Matching ignores case. The phrase matches whole leading tokens. |
| Secret keyword | Lowercase token | Omission marker | The first secret token in a line starts the omitted part. |
| Management observation | Source line number within one review call | Status, family ID, label, limit, field, value, and pointer | One observation for each matched line. The observation holds no source text. |
| Verified mapping entry | Keyword phrase | Family ID, field path, pointer, evidence ID, roles, models, value rule, and two fixture IDs | Exists only when the evidence row is verified-present. |
| Evidence row | `evidence_id`, one of E-01 to E-08 | Status, repository row IDs, and SDK signature | Changes status only after a read-only check. |

## Observation Statuses

Precedence applies in this order.

1. `secret-omitted`. A secret keyword appears on the line or in the parent line.
2. `mapped`. A verified mapping entry exists, the value passes its rule, and the model is supported.
3. `display-only`. Every other matched line. The label and limit explain the reason.

## State Transitions

- Family disposition moves from `conditional` to `mapped-entry-present` only after its evidence row reaches verified-present and T008 adds the entry.
- Family disposition stays `display-only` for MGT-03 to MGT-11, MGT-13, and MGT-14 in this issue.
- Evidence row moves from `pending` to `verified-present` when the pointer and SDK signature match the repository and the installed SDK, and both fixtures pass.
- Evidence row moves from `verified-present` to `stale` when a later pointer check fails. A stale row removes its mapping entry from the registry.
- Evidence row moves to `absent` when a check finds no property. An absent row keeps its family display-only.

## Relationships

- One management family owns one or more keyword phrases.
- One verified mapping entry cites one evidence row.
- One evidence row cites one or more repository rows from `design/research.md`.
- One management observation cites one management family.

## Natural Key Rules

- A review call returns at most one observation for each source line number.
- Observations keep the source order.
- The pair of family ID and line number identifies one observation in one review call.
- A mapping entry is identified by its keyword phrase. Two entries cannot share a keyword phrase.

## Validation Rules

- The observation `value` is empty unless the status is `mapped`.
- The observation `label` never contains a token that follows a secret keyword.
- The observation `pointer` is empty unless the status is `mapped`.
- A mapped value must pass the value rule of its entry. A value that fails the rule becomes `display-only`.
