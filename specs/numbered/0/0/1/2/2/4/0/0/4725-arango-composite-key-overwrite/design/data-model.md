# Data Model: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

This model covers the entities that the document key rule reads and writes. It names each natural key, each state transition, and each validation rule. It adds no table and no collection.

## Entities

### BGP Peer Statistic Record

- **Source**: One item of the Mist search response for `searchSiteBgpStats` (`bgp_stats` schema, RC-44).
- **Declared identity**: `mac`, `neighbor`, and `timestamp`, in that order (strategy entry, RC-64). The schema declares all three (RC-45, RC-46, RC-47).
- **Other attributes**: `neighbor_as`, `state`, `vrf_name`, `router_id`, `node`, and counters. These attributes do not identify the record.
- **Natural key**: The tuple of `mac`, `neighbor`, and `timestamp` identifies one observation of one peer.
- **Declared absence**: The schema declares no `id` (RC-48). A graph mapping that reads `id` finds no value (RC-59).

### Strategy Entry

- **Source**: One effective value of `ENDPOINT_PRIMARY_KEY_STRATEGIES` after last-definition-wins resolution (RC-70, RC-76).
- **Fields**: The collection name (the API function name), `type`, `primary_key` as an ordered list, and `indexes`.
- **Types**: `composite_pk`, `natural_pk`, `auto_increment_with_unique`, and `timeseries_pk`. Only `timeseries_pk` routes to Redis TimeSeries instead of ArangoDB (RC-79).
- **Affected rule**: An entry is affected when its type is `composite_pk` or `natural_pk`. It must declare two or more fields. It must not be an SLE identity or an exemption (FR-001, D-2).
- **Count at main f03c6c9b**: 121 affected entries (RC-76).

### Identity Key

- **Format**: `identity_` followed by 64 lowercase hexadecimal characters. The total length is 73 bytes.
- **Derivation**: The writer encodes each declared key value as a typed pair, in declared order. The writer encodes the list as ASCII JSON, then takes its SHA-256 digest.
- **Type tags**: `s` for text, `n` for a number, and `b` for a boolean.
- **Number text**: A number becomes the plain decimal text of `Decimal(repr(value)).normalize()`, formatted without an exponent. Integer `1` and float `1.0` produce the same text.
- **Constraints**: The key uses ASCII letters, digits, and the underscore only (FR-005). It is unique within its collection (FR-002).

### Document (ArangoDB)

- **Fields**: `_key` (string), the record fields, `_misthelper_updated_at` (integer seconds), and `_misthelper_deleted_at` (null).
- **Legacy document**: `_key` equals the value of the first declared field. Records written before the change have this form.
- **Identity document**: `_key` equals the identity key of the record. Records written after the change have this form for affected entries.
- **Fallback document**: `_key` equals a UUID4 string. The writer uses this form when a declared key value is missing or invalid (FR-006).

### Exemption Entry

- **Source**: A reviewed list in `composite_key_identity.py`. The list is empty at the start of the change (D-3).
- **Fields**: The collection name, the OpenAPI evidence (path and line), the decision date in UTC, and the reviewer.
- **Rule**: An exemption requires documented evidence that the first declared field identifies one stored record (FR-009).

### Identity Verdict

- **Source**: One audit row for one affected entry (T002, `design/contracts/identity-audit-format.md`).
- **Fields**: The collection, the effective type, the declared fields, the first field, the OpenAPI item schema, the evidence line, the verdict, and notes.
- **Verdict values**: `identity-required`, `exempt-unique-record`, `single-field-unchanged`, `sle-unchanged`, and `insufficient-identity`.

## Relationships

- One strategy entry maps to one collection and to many documents.
- One identity verdict describes one strategy entry.
- One exemption entry, at most, applies to one collection.

## State Transitions

| From | Event | To | Notes |
| - | - | - | - |
| No document | First write of a record with identity I | Document with key I | Insert. |
| Document with key I | The same record again | Same document, replaced | One document remains. The batch reports the write (D-12). |
| Document with key I | A distinct record with identity J | New document with key J | Document I is unchanged. |
| Legacy document with key L | A new write of record R with identity I | Legacy document unchanged, plus a document with key I | Two key families for one record until a migration runs. |
| No document | A record that lacks a declared key value | Document with a UUID key | The batch warning counts the record (FR-006). |
| Legacy document with key L | A migration | Rekeyed, merged, or removed | Gated by D-7. A verified backup comes first. |

Warning: A migration that removes legacy documents is irreversible without a verified backup.

Warning: A legacy key can already hide a replaced record. No migration restores that record.

## Validation Rules

- A declared key value must be a scalar. A list, an object, `None`, an empty string, or a non-finite number is missing (FR-006).
- An identity key must match the pattern `^identity_[0-9a-f]{64}$`.
- A verdict must cite an evidence path and a line that exist in the repository or in the installed package.
- An exemption entry must cite OpenAPI evidence before it enters the list (FR-009).
