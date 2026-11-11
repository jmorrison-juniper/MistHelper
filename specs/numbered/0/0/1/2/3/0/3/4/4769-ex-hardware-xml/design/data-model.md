# Data Model: EX Hardware XML Collection

**Feature**: [spec.md](../spec.md)

## Hardware XML Preset

One server-owned operation for a single configured organization.

| Field | Type | Rule |
|---|---|---|
| `preset` | string | Must equal `ex-hardware-xml`. |
| `format` | string | One of `xml`, `json`, or `both`. Omission means `xml`. |
| `organization_id` | Mist identifier | Taken from the configured portal scope, not from browser input. |
| `fixed_commands` | array of fixed text | XML uses `display xml`. JSON uses `display json`. BOTH runs XML, then JSON. Each command ends with `| no-more`. |
| `created_at` | UTC timestamp | Uses the existing preview time and expiry rules. |

The preset does not accept a browser command, organization, site list, or target list.

## Target

One unique EX switch or Virtual Chassis logical device from the complete organization inventory.

| Field | Type | Rule |
|---|---|---|
| `org_id` | string | Trusted configured organization identity. |
| `site_id` | string | Site that owns the device. |
| `device_id` | string | Stable Mist device identity and filename collision suffix. |
| `hostname` | string or empty | Source for the safe filename stem. |
| `family` | string | Must equal `ex` for execution. |
| `status` | state | Only `connected` from current Mist running statistics is eligible. `disconnected` and unknown states are excluded or skipped. |

Deduplicate by the organization, site, and device identity. A target without a valid stable device identifier cannot produce a filename and must fail closed.

## XML Document

One complete XML response for one target and one command.

| Field | Type | Rule |
|---|---|---|
| `raw_xml` | UTF-8 text | Contains only the XML document, without command echo, prompt, ANSI controls, banners, or paging text. |
| `root` | XML element | Must be `rpc-reply` or `chassis-inventory`, with the required chassis inventory content. |
| `well_formed` | boolean | True only after strict UTF-8 decode and full-document parse succeed. |
| `safe` | boolean | False for DTD, entity declarations, or credential fields and values. |

The application does not modify valid native documents to redact them.
Credential fields and values prevent publication. Public namespace URLs and slash-separated hardware descriptions remain valid.

## Native JSON Document

One native response from `show chassis hardware detail | display json | no-more`.
Preserve the device text, arrays, string values, and whitespace inside the document.
Do not derive this document from XML.

| Field | Type | Rule |
|---|---|---|
| `chassis-inventory` | nonempty array | Contains native chassis inventory objects and chassis content. |
| `raw_json` | UTF-8 text | Complete native JSON without command echo, prompt, or routing-engine marker. |

## Device Result and Run Archive

Each target has one outcome: `completed`, `failed`, `skipped`, or `stopped`.
Each requested format has its own state and reason code.
A failed target can retain a successful format file. The manifest must not describe a failed format as successful.

Output names use a sanitized hostname stem and a stable device identifier suffix. A unique run directory prevents collisions between runs. In BOTH mode, the `.xml` and `.json` files share one stem.

Hardware manifests contain `durable: true` and a unique `run_id`.
The run directory and partial files survive session expiry, session deletion, and process restart.
