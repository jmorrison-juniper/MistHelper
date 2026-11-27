# Contract: Secret redaction for management review

Status: Specified. This contract applies to review output, logs, test output, and the proposal and export contracts of issue 4641.

## Secret Keywords

Each keyword matches one whole token. Matching ignores case.

| Keyword | Typical Cisco form | Rule |
| --- | --- | --- |
| `password` | Local account and login password lines | Omit the value that follows. |
| `secret` | Enable secret and RADIUS secret lines | Omit the value that follows. |
| `key` | TACACS key and IPsec key lines | Omit the value that follows. |
| `key-string` | Key string lines | Omit the value that follows. |
| `community` | SNMP v2c community lines | Omit the value that follows. |
| `passphrase` | SNMPv3 and IPsec passphrase lines | Omit the value that follows. |
| `psk` | Pre-shared key lines | Omit the value that follows. |
| `auth` | SNMPv3 authentication lines | Omit the value that follows. |
| `priv` | SNMPv3 privacy lines | Omit the value that follows. |

## Omission Rule

1. Find the first token that matches a secret keyword.
2. Omit that token and every token after it in the line.
3. Build the label from the matched keyword phrase, the secret keyword, and the marker `[value omitted]`.
4. Set the observation status to `secret-omitted`.

For example, a synthetic line that holds a community value produces the label `snmp-server community [value omitted]`. The synthetic value never appears.

## Hash and Encoded Forms

- One-way hashes, such as Cisco type 5, 8, and 9 values, follow the omission rule.
- Cisco type 7 values are reversible encodings. The review treats them as secrets and follows the same rule.
- No code decodes, hashes, or reconstructs any value.
- No code computes a fingerprint for a value.

## Field Register

The register lists each Mist field that holds a secret or a credential. The treatment applies in every output.

| Field | Pointer | Repository row | Treatment |
| --- | --- | --- | --- |
| SNMP v2c community name | `snmp_config.v2c_config.community_name` | R50 | Omitted from review output. Never mapped. |
| SNMPv3 user authentication password | `snmp_usm_user.authentication_password` | R66 | Omitted. Never mapped. |
| SNMPv3 user encryption password | `snmp_usm_user.encryption_password` | R66 | Omitted. Never mapped. |
| RADIUS authentication secret | `radius_auth_server.secret` | R53 | Omitted. Never mapped in this issue. |
| RADIUS accounting secret | `radius_acct_server.secret` | R66 | Omitted. Never mapped in this issue. |
| Switch local account password | `config_switch_local_accounts_user.password` | R55 | Omitted. Never mapped in this issue. |
| LTE password | `gateway_port_config.lte_password` | R57 | Omitted. Never mapped. |
| LTE username | `gateway_port_config.lte_username` | R56 | Omitted. Never mapped. |
| IPsec pre-shared key passphrase | `psk.passphrase` | R64 | Omitted. Never mapped. |
| Gateway management root password | `gateway_mgmt.root_password` | R65 | Never mapped from a Cisco enable secret. |
| Switch root password | `switch_mgmt.root_password` | R66 | Never mapped in this issue. |
| TACACS server key | Source field named in source line 514 | R77 | Omitted. The Mist field name is pending (research U-4). |

## Output Rules

- Review output holds no secret value and no hash text.
- A display-only observation holds the allow-listed phrase and the family limit. It holds no source token.
- A mapped observation holds a validated value. A secret never becomes a mapped value.
- Issue 4641 applies the same rules to the proposal and the export.

## Log Rules

- Log lines hold counts and family IDs only.
- A log line never holds a label, a value, or a source line.
- The logging boundary enforces these rules. Each caller receives the same protection.

## Test Rules

- Fixtures use synthetic values such as `SYNTHETIC-SECRET-0001`.
- Each test asserts the absence of the synthetic value in the observation fields, in the captured log output, and in the failure messages.
- No fixture holds a real credential, a real customer configuration, or a live Mist response.

Warning: a secret value that reaches a log or an export cannot be removed from that copy.
