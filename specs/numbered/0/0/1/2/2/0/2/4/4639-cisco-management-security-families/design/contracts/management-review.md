# Contract: Management review output

Status: Specified. Producer: issue 4639, in `src/interfaces/portals/cisco_config_converter/conversion.py`. Consumers: issue 4637 (display) and issue 4641 (proposal and export).

## Entry Point

`ManagementFamilyReview.review(content: str) -> list[ManagementObservation]`

The method reads the validated source text. It returns one observation for each matched family line, in source order. It raises no exception for an unknown line. It returns no observation for that line.

## Observation Shape

| Field | Type | Rule |
| --- | --- | --- |
| `line` | integer | The one-based source line number. Unique in one review call. |
| `family_id` | string | One of MGT-01 to MGT-14. |
| `family` | string | The fixed family label from the family table. |
| `status` | string | `mapped`, `display-only`, or `secret-omitted`. |
| `label` | string | The matched keyword phrase, plus the secret keyword and a marker when the status is `secret-omitted`. |
| `limit` | string | The fixed family limit from the family table. |
| `field` | string or empty | The Mist field path. Filled only when the status is `mapped`. |
| `value` | string or empty | The validated value. Filled only when the status is `mapped`. Never logged. |
| `pointer` | string or empty | The evidence pointer from the mapping entry. Filled only when the status is `mapped`. |

## Invariants

1. `value` is empty unless the status is `mapped`.
2. `pointer` is empty unless the status is `mapped`.
3. `label` never contains a token that follows a secret keyword.
4. Observations keep the source order.
5. Banner bodies produce no observation.
6. Blank lines and comment lines beginning with an exclamation mark produce no observation.
7. A child line without a parent family produces no observation.

## Classification Rules

1. Skip each blank line and each comment line. Use the same rule as the DNS converter.
2. Skip each banner body. Use `IOSDnsConverter.banner_delimiter` (renamed from `_banner`, R27).
3. A line that starts with a space or a tab is a child line. It takes the family of the last top-level family line.
4. A top-level line matches a keyword phrase from the allow-list. Matching ignores case. The first match wins.
5. Any token that equals a secret keyword makes the status `secret-omitted`. The label is the phrase, the secret keyword, and the marker.
6. A verified mapping entry for the phrase makes the status `mapped` when the value rule passes and the model is supported.
7. Every other matched line has the status `display-only`.

## Family Table

| ID | Family | Disposition | Keyword phrases | Fixed limit |
| --- | --- | --- | --- | --- |
| MGT-01 | Syslog | conditional | `logging host`, `logging trap`, `logging facility`, `logging source-interface` | Syslog maps only for Branch and Standalone site settings after evidence E-01. Hub syslog has no verified field. |
| MGT-02 | SNMP | conditional | `snmp-server` | SNMP location and contact map after evidence E-03. Communities and SNMPv3 credentials are omitted. Trap targets stay display-only. |
| MGT-03 | Management egress | display-only | `ntp source`, `ip tacacs source-interface`, `ip radius source-interface`, `ip http client source-interface` | Management egress is an organization path preference. It is not a logging or SNMP destination. |
| MGT-04 | AAA | display-only | `aaa`, `radius server`, `radius-server` | No verified gateway AAA field exists. Shared secrets are omitted. |
| MGT-05 | TACACS | display-only | `tacacs server`, `tacacs-server` | TACACS fields apply to switch management only. Keys are omitted. |
| MGT-06 | Local accounts | display-only | `username`, `enable secret`, `enable password` | Local account fields apply to switch management only. Passwords and hashes are omitted. |
| MGT-07 | ACL | display-only | `ip access-list`, `ipv6 access-list`, `access-list` | No verified ACL mapping exists. No command is generated. |
| MGT-08 | Class | display-only | `class-map` | No verified class mapping exists. No command is generated. |
| MGT-09 | Policy | display-only | `policy-map` | No verified policy mapping exists. No command is generated. |
| MGT-10 | Zone | display-only | `zone security`, `zone-pair security` | No verified zone mapping exists. No command is generated. |
| MGT-11 | Crypto | display-only | `crypto` | No verified crypto mapping exists. Keys and secrets are omitted. |
| MGT-12 | Cellular | conditional | `interface cellular`, `controller cellular` | The cellular APN maps after evidence E-04 for a supported model. The username and password are omitted. |
| MGT-13 | Redundancy | display-only | `redundancy`, `standby` | Cisco redundancy has no verified Mist equivalent. No command is generated. |
| MGT-14 | Flow export | display-only | `flow exporter`, `flow monitor`, `flow record`, `ip flow-export` | No verified Mist flow export field exists. No device command is generated. |

## Mapped Fields

| Keyword phrase | Field path | Value rule | Evidence |
| --- | --- | --- | --- |
| `logging host` | `site_setting.remote_syslog.servers[].host` | An IPv4 address, or a DNS name of ASCII letters, digits, hyphens, and dots | E-01 |
| `snmp-server location` | `site_setting.snmp_config.location` | Printable ASCII text. The length bound comes from task T001 (research U-5). | E-03 |
| `snmp-server contact` | `site_setting.snmp_config.contact` | Printable ASCII text. The length bound comes from task T001 (research U-5). | E-03 |
| `interface cellular` APN line | `lte_apn` of the selected LTE port in `gateway_template.port_config`, with `wan_type` set to `lte` | An ASCII APN of letters, digits, hyphens, and dots | E-04 |

A mapped field exists only when its evidence row is verified-present (T008). Each field needs one positive fixture and one negative fixture.

## Value Rules for Secrets

A secret value never reaches a mapped field. A mapped line whose value would be secret becomes `secret-omitted`. Secret handling is in `design/contracts/secret-redaction.md`.

## Logging Rules

- The info line before a review states the number of source lines. It holds no value.
- The debug line after a review states the number of observations, the number of mapped observations, and the number of secret-omitted observations.
- The review never logs a `value`, a `label`, or a source line.

## Compatibility

- `IOSDnsConverter.convert` returns the same proposal keys and values as before (R31, R32).
- `ConversionProposal` keeps its keys (R30 shows the source kind limit that stays unchanged).
- The review returns a separate list. It does not change the unsupported item list.
