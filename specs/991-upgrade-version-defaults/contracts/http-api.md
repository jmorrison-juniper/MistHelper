# HTTP API Contract: Per-Type Upgrade Version Defaults

## Existing save path

`POST /api/runs/<run_id>/options` remains the only options-save endpoint. The
request body continues to contain individual target entries.

```json
{
  "targets": [
    {"mac": "5c5b350e0001", "version_target": "0.14.30075"}
  ],
  "reboot": true,
  "junos_file_action": false,
  "strategy": "big_bang"
}
```

The endpoint re-reads current inventory and returned availability. It accepts a
target only when the target device exists and offers that exact version. It
rejects missing, unknown, cross-type, unavailable, and incompatible targets
with the existing `400` and `bad_option` response. The route does not write a
partial plan after any target fails.

The success response remains:

```json
{
  "targets": [
    {"mac": "5c5b350e0001", "version_target": "0.14.30075"}
  ],
  "warnings": []
}
```

The options read and options save do not invoke an upgrade. The existing
confirmation and start path remains the only upgrade submission path.

## Configuration contract

| Variable | Device type | Rule |
| --- | --- | --- |
| `CAPTURE_DEFAULT_AP_VERSION` | `ap` | Use only when it exactly matches a compatible returned candidate. |
| `CAPTURE_DEFAULT_SWITCH_VERSION` | `switch` | Use only when it exactly matches a compatible returned candidate. |
| `CAPTURE_DEFAULT_GATEWAY_VERSION` | `gateway` | Use only when it exactly matches a compatible returned candidate. |

If the variable is blank, malformed, unavailable, or incompatible, the portal
uses the highest numeric compatible candidate. If no candidate exists, the
portal sends no target for that type.
