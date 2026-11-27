# Contract: OSPF Peer Identity Input and Key

This contract defines the input record, the validation rules, the canonical payload, and the key format. The implementation lives in `OspfPeerIdentity` (`src/foundation/persistence/identity/ospf_peer.py`).

## Input Record

The input is one OSPF peer record from `searchSiteOspfStats` or `searchOrgOspfStats`. The item schema lines appear in `design/data-model.md`, and the rows RV-49 to RV-54 verify them.

## Validation Order

Each rule applies to one record. The first failure rejects the whole batch.

1. `mac` must be a non-empty string. Otherwise the error names `mac`.
2. The neighbor component is `neighbor` when `neighbor` is a non-empty string. Otherwise it is `peer_ip` when `peer_ip` is a non-empty string. Otherwise the error names `neighbor`.
3. `timestamp` must be an int or a float, not a boolean, finite, and zero or greater. Otherwise the error names `timestamp`.
4. `vrf_name` and `port_id` are scope values. A string that is non-empty after trimming keeps its exact value. Any other value becomes JSON null.

Values are used as received. The code does not trim, lowercase, or change them, except for the scope test in rule 4.

## Timestamp Text

The timestamp text is the decimal form of the number with trailing zeros removed. The form has no exponent.

| Input | Text |
| - | - |
| `1700000000` | `1700000000` |
| `1700000000.0` | `1700000000` |
| `1700000000.5` | `1700000000.5` |

## Canonical Payload

The payload is a JSON array of five values. The order is fixed. The encoder uses ASCII escaping and no spaces.

Example A, with `neighbor` `172.29.1.4`, `vrf_name` `master`, and `port_id` `ge-0/0/1.0`:

`["020001c04668","master","ge-0/0/1.0","172.29.1.4","1700000000"]`

Example B, the same record with `neighbor` `172.29.1.5`. Its payload differs from example A in the fourth value only.

Example C, a record with no `vrf_name` and no `port_id`:

`["020001c04668",null,null,"172.29.1.4","1700000000"]`

Example D, the record of example A with `timestamp` `1700000000.0`. Its payload equals example A.

## Key Format

- The key is `ospf_` followed by 64 lowercase hexadecimal characters.
- The hexadecimal characters are the SHA-256 digest of the UTF-8 bytes of the payload.
- Examples A and D produce one key. Examples A and B produce two keys. Example A and example C produce two keys, because the scope value differs.

## Rejection Message

A rejected batch returns a failed write result. The message names the component and no value. The format is:

`OSPF identity rejected a record: missing or invalid component <name>.`

The `<name>` value is one of `mac`, `neighbor`, or `timestamp`.

## Applicability

The rules apply only to `searchSiteOspfStats` and `searchOrgOspfStats`. Every other endpoint keeps its own strategy and key.
