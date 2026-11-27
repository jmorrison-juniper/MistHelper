# Contract: Structured Proposal (Version 2)

This contract defines the JSON object that version 2 routes return and accept. The object is the single source for review, export, and the digest. The contract tests in `proposals/test_proposal_assembly.py` pin the key set (test 1).

## Identity

- `proposal_version` is the integer `2`.
- The object holds exactly the ten keys in the table below. A missing key or an extra key is an error (FR-012).

## Keys

| Key | Type | Rule |
| - | - | - |
| `proposal_version` | integer | Equal to `2`. |
| `scope` | object | Keys `name` (string), `template_type` (string), `source` (object), `hardware_role` (null), `hardware_model` (null), and `target` (null). |
| `scope_digest` | string | The digest of `scope`. Sixty-four lowercase hexadecimal characters. |
| `gateway_template` | object | Key `name` (string, required), key `type` (`standalone` or `spoke`), and key `dns_servers` (array of strings). The key `dns_servers` appears only when at least one IPv4 address converts. |
| `object_changes` | array | One entry for the gateway template. Its rules appear below. |
| `omissions` | array | One entry for each unsupported source line, each known gap, and the no-command case. Its rules appear below. |
| `unresolved_mappings` | array | Empty for the DNS subset. |
| `verification` | object | Keys `local_schema` (`passed`), `cloud_state` (`unavailable`), and `reason` (text). |
| `unsupported_items` | array | The version 1 shape. Each entry holds `line`, `command`, and `reason`. |
| `known_gaps` | array of strings | The version 1 text, unchanged. |

The `source` object holds two keys. Key `bytes` is the UTF-8 byte count of the source content. Key `suffix` is the lowercase suffix of the file name, such as `.cfg`.

## Object Change Entry

| Key | Value |
| - | - |
| `object` | `gateway_template` |
| `action` | `propose_create` |
| `identity` | An object with `name` and `type`, copied from the scope |
| `fields` | The field names present in `gateway_template`, in the order of the object |
| `existing_state` | `not_checked` |

The schema of `gateway_template` comes from the OpenAPI component at line 80654. The name is required (line 80783). The type enum holds `spoke` and `standalone` (line 80788). The `dns_servers` property holds an array of strings (lines 80678 and 78042). The request body references that schema at line 9887.

## Omission Entry

Omissions appear in a fixed order. First come the unsupported source lines, in source order. Then come the known gaps, in list order. The no-command entry comes last, and only when no IPv4 address converts.

| Key | Present when | Value |
| - | - | - |
| `kind` | Always | `unsupported_source_line`, `known_gap`, or `no_supported_command` |
| `line` | `kind` is `unsupported_source_line` | The one-based source line number |
| `category` | `kind` is `unsupported_source_line` | The version 1 command label, such as `ip name-server [values omitted]` |
| `text` | `kind` is `known_gap` or `no_supported_command` | The known gap text, or the text `No supported command was found. The proposal holds no DNS addresses.` |
| `disposition` | Always | `omitted` |

## Digest Rules

- Canonical JSON uses `json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)`. The encoded text is UTF-8, and the hash is SHA-256 in lowercase hexadecimal. This is `ReviewState.digest` (row 14 and row 15 of `design/research.md`).
- `scope_digest` is the digest of `scope`.
- The proposal digest is the digest of the full object, which includes `scope_digest`.

## Shape Example

The example uses the synthetic source below. It holds 52 bytes, and the second line uses an IPv6 address.

```text
ip name-server 192.0.2.1
ip name-server 2001:db8::1
```

The request uses the name `Branch Office` and the type `spoke`.

```json
{
  "proposal_version": 2,
  "scope": {
    "name": "Branch Office",
    "template_type": "spoke",
    "source": {"bytes": 52, "suffix": ".cfg"},
    "hardware_role": null,
    "hardware_model": null,
    "target": null
  },
  "scope_digest": "a7d70563ba231de5dabc69b6ddd3e039e67cc8e03571cf7ea5d9560a02e4fdcb",
  "gateway_template": {
    "name": "Branch Office",
    "type": "spoke",
    "dns_servers": ["192.0.2.1"]
  },
  "object_changes": [
    {
      "object": "gateway_template",
      "action": "propose_create",
      "identity": {"name": "Branch Office", "type": "spoke"},
      "fields": ["name", "type", "dns_servers"],
      "existing_state": "not_checked"
    }
  ],
  "omissions": [
    {"kind": "unsupported_source_line", "line": 2, "category": "ip name-server [values omitted]", "disposition": "omitted"},
    {"kind": "known_gap", "text": "Only global IPv4 ip name-server commands are converted.", "disposition": "omitted"},
    {"kind": "known_gap", "text": "IPv6, hardware mappings, and all other settings remain unsupported.", "disposition": "omitted"},
    {"kind": "known_gap", "text": "Cloud apply is unavailable. Unsupported values are omitted to protect credentials.", "disposition": "omitted"}
  ],
  "unresolved_mappings": [],
  "verification": {
    "local_schema": "passed",
    "cloud_state": "unavailable",
    "reason": "Offline preview. No Mist request is made."
  },
  "unsupported_items": [
    {"line": 2, "command": "ip name-server [values omitted]", "reason": "Unsupported command or context."}
  ],
  "known_gaps": [
    "Only global IPv4 ip name-server commands are converted.",
    "IPv6, hardware mappings, and all other settings remain unsupported.",
    "Cloud apply is unavailable. Unsupported values are omitted to protect credentials."
  ]
}
```

The scope digest in the example is the SHA-256 value of the canonical scope text with `bytes` 52 and suffix `.cfg`. A reviewer can recompute it with the digest rule above.

## Privacy Rules

- The object holds no source text, no template name in logs, and no unsupported value. Unsupported items keep a line number and a label only (research rows 74 and 75).
- The object holds no digest of the source content (decision D-4).
- Each text value stays in the response only. The browser session stores digests only (`data-model.md`).

## Error Shapes

- Invalid source, name, or type: HTTP 400. The body names the input problem, for example `Use a template name with 1 to 120 visible characters.`
- Invalid body on review or export: HTTP 400 with `{"error": "Submit a valid JSON proposal."}`.
- No review or a changed proposal: HTTP 409. The body uses the version 1 messages `Create a new preview before review or export.` or `Review this proposal before export.`
