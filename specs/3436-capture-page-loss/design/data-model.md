# Data model: Capture reads report a lost page

## Paged read

The existing `DeviceRead` carries these fields.

| Field | Meaning |
| - | - |
| `section` | The existing source name. |
| `records` | The available cloud records in page order. |
| `partial_reasons` | The existing reason dictionaries. |

The raw wireless statistics read uses this same record.
No persisted field changes.
The result is passive.
Only the existing page reader performs an SDK operation.

## Partial reason

```json
{
  "section": "upgrade_gate_statistics",
  "reason": "page_count_mismatch",
  "http_status": 503
}
```

The capture collector keeps its existing section mapping.
It adds `source` when it maps a source reason to a report row.

```json
{
  "section": "clients_wireless",
  "reason": "page_count_mismatch",
  "http_status": 503,
  "source": "wireless_statistics"
}
```

No HTTP response means status `0`.
The failed later response supplies every other status.

## Tier 3 paged response

The private paged response carries joined rows, an HTTP status, and a reason.
A partial response keeps earlier rows even when its status is outside the success range.
The actual `ExtraSection` copies that outcome.
The shared port read copies it into both `switch_ports` and `poe`.

## Fleet read and capture

`FleetRead` keeps its existing readings and reasons.
The existing final capture keeps its section rows, counts, keys, digests, and schema.
The repair changes evidence completeness only.
It changes no firmware decision or write policy.
