# Contract: Proposal response, blockers, and review gate

This contract defines the JSON proposal that `/preview` returns. It extends the existing proposal shape from main. The keys `gateway_template`, `unsupported_items`, and `known_gaps` keep their names. The key `hardware` is new. Issue 4641 reads the `hardware` key.

## Proposal shape

The example below uses one verified selection. Each value is concrete. The `known_gaps` list keeps three entries, as the unit test expects.

```json
{
  "gateway_template": {
    "name": "Branch office edge",
    "type": "standalone",
    "dns_servers": ["192.0.2.1"]
  },
  "unsupported_items": [
    {"line": 3, "command": "[unsupported source line]", "reason": "Unsupported command or context."}
  ],
  "known_gaps": [
    "Only global IPv4 ip name-server commands are converted.",
    "IPv6 and all settings outside DNS and the verified hardware selection remain unsupported.",
    "Cloud apply is unavailable. Unsupported values are omitted to protect credentials."
  ],
  "hardware": {
    "role": "standalone",
    "family": "srx",
    "model": "SRX300",
    "port_assignments": [
      {"mist_port": "ge-0/0/3", "usage": "lan", "source_interface": "GigabitEthernet0/3"},
      {"mist_port": "ge-0/0/7", "usage": "wan", "source_interface": "GigabitEthernet0/7"}
    ],
    "evidence_revision": "openapi-b7fc2bfb-mistapi-0.64.1",
    "status": "verified",
    "blockers": []
  }
}
```

Rules for the shape:

- `gateway_template.type` is present only when the role maps to a verified deployment type. Standalone maps to `standalone`. Branch and Hub omit the key.
- `port_assignments` sorts by `mist_port`. Sorting keeps the digest stable for the same selection.
- `hardware.status` is `verified` when `blockers` is empty. Otherwise it is `blocked`.
- Each blocker has `code` and `message`. The codes appear in the table below.
- The `known_gaps` second entry replaces the main text "IPv6, hardware mappings, and all other settings remain unsupported." The first and third entries stay unchanged.

## Blocker codes

| Code | When the code appears | Message |
| --- | --- | --- |
| `role_unverified` | Role is Branch. | Branch has no verified gateway deployment type. Issue 4634 must record the mapping. |
| `role_without_deployment_type` | Role is Hub. | Hub has no value in the gateway deployment type enum. Hub stays blocked. |
| `model_unknown` | Model is absent from the register for the family. | This model is not in the verified register for the selected family. |
| `evidence_revision_stale` | The row revision differs from `CURRENT_REVISION`. | The evidence revision for this model differs from the current revision. |
| `model_without_inventory_sample` | The row lacks an inventory sample. | No inventory sample verifies this model. No port map is authorized. |
| `model_evidence_conflict` | The row evidence names conflicting cluster members. | The cabling evidence names conflicting cluster members for this model. |
| `port_evidence_absent` | The row holds no WAN or LAN port roles. | No verified WAN or LAN port roles exist for this model. |
| `port_not_selectable` | A Mist port is not a WAN or LAN name in the row. | This Mist port is not a verified WAN or LAN port for this model. |
| `port_duplicate` | A Mist port appears more than once. | A Mist port appears more than once. Assign each port one time. |
| `source_interface_duplicate` | A Cisco interface maps to more than one Mist port. | A Cisco interface maps to more than one Mist port. |
| `source_interface_not_found` | A Cisco interface name is absent from the uploaded file. | The Cisco interface does not appear in the uploaded file. |
| `port_missing_usage` | No WAN assignment, no LAN assignment, or no assignment at all. | Assign at least one WAN port and at least one LAN port. |

Evaluation order:

1. Role. Branch and Hub add their blocker, and the evaluation continues.
2. Model lookup. An unknown model adds `model_unknown` and stops.
3. Revision. A stale row adds `evidence_revision_stale` and stops.
4. Row status. A blocked row adds its blocker and stops. Port checks do not run.
5. Port checks. Each applicable port blocker is added once for each port that fails.

## Review and export gate

| Route | Condition | Status | Message |
| --- | --- | --- | --- |
| `/review` | The digest matches and `hardware.status` is `verified`. | 200 | Not applicable. The proposal is approved for export. |
| `/review` | The digest matches and `hardware.status` is `blocked`. | 409 | Resolve each hardware blocker before review. |
| `/review` | The digest differs from the session digest. | 409 | Create a new preview before review or export. |
| `/export` | No approved review exists for the digest. | 409 | Review this proposal before export. |
| `/export` | The approved review matches the digest. | 200 | JSON download named `cisco-proposal.json`. |

A changed role, family, model, port, Cisco interface, or source file changes the digest. The earlier review then fails with HTTP 409. This rule already exists for other input changes on main.
