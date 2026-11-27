# Data Model: MSP organization list skipped without the listing right

## ProfileGrant

One entry of the `privileges` list from the `GET /api/v1/self` response. The report reads only these fields.

| Field | Type | Source | Use |
| - | - | - | - |
| `msp_id` | string or absent | Profile | Names the MSP. A grant with a non-empty string is an MSP grant. |
| `scope` | string or absent | Profile | Holds the listing right when the value is `msp`. An absent key counts as `msp` (D3). |
| `role` | string | Profile | Read for the record only. The role does not gate the call (D2). |
| `org_id` | string or absent | Profile | Names a direct organization when present. |
| `org_name` or `name` | string or absent | Profile | Display name for a direct organization. |

**Natural key**: For an MSP grant, the pair of `msp_id` and `scope`. The report keeps the first direct organization for each `org_id`.

**Validation**: A grant that is not a mapping is ignored. A grant with a non-string `msp_id` is ignored.

## MspSource

One MSP id that the report reads. The report reads each MSP source once for its listing decision.

| Attribute | Rule |
| - | - |
| `msp_id` | Non-empty string from a profile grant. |
| `listing_right` | True when at least one profile grant for `msp_id` has scope `msp`. |
| `outcome` | One of `listed`, `failed`, or `skipped`. |

**Natural key**: `msp_id`.

**Uniqueness**: One skipped row for each `msp_id` (D5). The listing call may run once for each MSP-scope grant, as before.

## StatusRow (`OrganizationScope`)

One record for `CrossOrgOrganizationStatus.csv`. The change reuses the existing dataclass fields.

| Field | Direct organization row | MSP skipped row |
| - | - | - |
| `org_id` | The organization ID | The missing value `Missing` |
| `org_name` | The organization name | `MSP <msp_id>` |
| `msp_id` | Empty | The MSP id |
| `source` | `direct` or `msp` | `msp` |
| `request_status` | `success`, `partial`, `failed`, or `unavailable` | `skipped` |
| `error` | Empty, or the failure text | The reason text from `design/contracts/status-rows.md` |

**Natural key**: `org_id` for an organization row. `msp_id` with `source` `msp` for an MSP row.

## State Transitions for an MSP Source

```text
profile read succeeds
  -> MSP grant found
      -> grant holds the listing right
          -> listing call sent
              -> HTTP 200: organizations added (listed)
              -> other status: failure row written (failed)
      -> grant lacks the listing right, and no grant for the MSP holds the right
          -> skipped row written (skipped), no listing call
      -> grant lacks the listing right, but another grant for the MSP holds it
          -> handled by the grant that holds the right (listed or failed)
profile read fails
  -> profile failure row written, no MSP source is read
```

## Console Summary Lines

| Count | Source | Rule |
| - | - | - |
| Organizations discovered | All status rows | Excludes skipped rows (FR-008) |
| MSP sources skipped | Skipped rows | Always printed, zero or more (FR-007) |
| Skipped source line | One line for each skipped row | Prints the MSP id and the reason (FR-007) |

## Relationships

- One profile holds zero or more profile grants.
- One MSP source comes from one or more MSP grants that name the same `msp_id`.
- One MSP source yields zero or more organization rows through the listing call.
- One MSP source yields at most one skipped row.
- One direct organization comes from one profile grant with `org_id` and no skipped row.
