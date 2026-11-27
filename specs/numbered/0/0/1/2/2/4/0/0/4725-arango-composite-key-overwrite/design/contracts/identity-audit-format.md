# Interface Contract: Identity Audit Table

This contract defines the identity audit. The audit gives one verdict to each affected strategy entry. The table of rows is produced by task T002. The guard test in T011 reads the table and checks it.

## Scope

- Affected entries: 121 effective entries on the ArangoDB path at main f03c6c9b (RC-76). Each entry has type `composite_pk` or `natural_pk` and two or more declared fields. SLE identities are not part of the 121 (RC-68, RC-69).
- Collection name: the API function name, which is also the ArangoDB collection name (RC-58).
- Effective type: the type from the last definition of the name (RC-70).

## Columns

| Column | Meaning |
| - | - |
| collection | API function name. |
| effective_type | Type of the effective (last) definition. |
| declared_fields | Ordered declared key fields. |
| first_field | The first declared field, which is the legacy key. |
| schema_evidence | OpenAPI item schema path and line for each declared field. |
| exemption_evidence | OpenAPI path and line that show a unique first field, or `none`. |
| verdict | One of the five values below. |
| note | Short ASCII text. |

## Verdict Values

- `identity-required`. The default for an affected entry with no exemption evidence (D-2, D-3).
- `exempt-unique-record`. The OpenAPI item documents the first declared field as a unique identifier of one stored record (D-3).
- `single-field-unchanged`. The entry declares one field, so the legacy key stays (FR-007).
- `sle-unchanged`. The entry uses an SLE identity (FR-008).
- `insufficient-identity`. The declared fields do not identify one record, for example a timestamp alone (A-6). The writer does not fix this value. A follow-up issue does.

## Example Rows

| collection | effective_type | declared_fields | first_field | schema_evidence | exemption_evidence | verdict | note |
| - | - | - | - | - | - | - | - |
| searchSiteBgpStats | composite_pk | mac, neighbor, timestamp | mac | RC-44, RC-45, RC-46, RC-47 | none | identity-required | The BGP item declares no `id` (RC-48). |
| searchOrgDeviceEvents | composite_pk | id, device_id, timestamp | id | RC-49, RC-50, RC-51 | none | identity-required | The `device_event` item declares no `id` (RC-49). |
| siteVariableAudit | natural_pk | site_id, template_id, variable_name, field_path | site_id | schema evidence is collected in T002 | none | identity-required | Natural key with four fields (RC-72). |
| listSiteAnomalyEvents | composite_pk | timestamp | timestamp | schema evidence is collected in T002 | not applicable | insufficient-identity | Single field, outside the 121 rows (RC-74). |

## Guard Output

The guard prints one ASCII line:

```text
identity_audit examined=<count> verdicts=<count> unclassified=<count>
```

- At main f03c6c9b, `examined` is 121 and `unclassified` is 0 (SC-005).
- The guard fails when `examined` is 0 (test 16).
- The guard fails when `unclassified` is above 0 (test 15).

## Rules

- Every verdict cites evidence, or it uses the default `identity-required`.
- A change to the audit file and a change to the guard input happen in one commit.
- A verdict of `exempt-unique-record` needs a reviewer name and a UTC date (data model, Exemption Entry).
