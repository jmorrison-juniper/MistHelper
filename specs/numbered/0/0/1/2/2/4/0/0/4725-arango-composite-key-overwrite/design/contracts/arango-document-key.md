# Interface Contract: ArangoDB Document Key

This contract defines the `_key` value that the ArangoDB writer stores for each record. It covers the new class `CompositeKeyIdentity` and its call from `ArangoDBWriter._compute_key`.

## Call Path

- Caller: `ArangoDBWriter.write` (`src/foundation/persistence/db/writers/arango_writer.py`, line 3987, RC-52).
- Key call: `_prepare_document` (line 4047, RC-55), then `_compute_key` (line 4058, RC-56 and RC-57).
- Import: `_batch_import` with `on_duplicate="replace"` (line 4034, RC-53). This contract does not change the import.

## Inputs

| Name | Type | Source | Rule |
| - | - | - | - |
| strategy type | text | strategy entry field `type` | Affected types are `composite_pk` and `natural_pk`. |
| declared fields | ordered list of text | strategy entry field `primary_key` | Two or more fields make a record affected. |
| record | mapping | one API item | Read only. The writer does not change the record. |
| collection name | text | argument of `write` | Matched against the exemption set. |

## Output

- `_key`: text. For an identity key, the text is `identity_` followed by 64 lowercase hexadecimal characters, which is 73 bytes in total.
- For a fallback, `_key` is a UUID4 text.

## Rules

- **R1 SLE first.** If the declared fields match an SLE trend or window identity, the writer returns the SLE key. The SLE identity functions keep their behavior (RC-65, RC-66).
- **R2 Single field.** If the strategy declares one field, the writer returns the legacy value. The value is the text of the field value, as before (FR-007).
- **R3 Exempt collection.** If the collection name is in the exemption set, the writer returns the legacy first-field value (FR-009). The exemption set starts empty (D-3).
- **R4 Affected record.** The writer normalizes each declared value (R5). If any value is missing, the writer returns a UUID4 text and counts one fallback. Otherwise the writer returns the identity key (R6).
- **R5 Typed normalization.** A text value becomes the pair `["s", value]`. A number that is not a boolean becomes `["n", text]`, where the text is `Decimal(repr(value)).normalize()` formatted without an exponent. A boolean becomes `["b", value]`. Any other type, `None`, an empty text, NaN, and infinity count as missing.
- **R6 Digest.** The payload is the ASCII JSON array of the pairs, in declared order, with separators `,` and `:` and no spaces. The key is `identity_` followed by the SHA-256 hexadecimal digest of the payload.
- **R7 Bounds.** The key is ASCII. The key is 73 bytes long, which is below the 254-byte limit (RC-121).
- **R8 Stability.** The same declared values always produce the same key, on every run and on every platform.

## Examples

The examples use synthetic values. The test helper computes the expected digest with `hashlib`.

- Two records with equal `mac` and `timestamp` and different `neighbor` produce two different keys (FR-002).
- Two records with the same `mac`, `neighbor`, and `timestamp` produce one key (FR-003).
- A timestamp of `100` and a timestamp of `100.0` produce one key (FR-004).
- A text `"100"` and a number `100` produce two keys, because their type tags differ (FR-004).

## Errors and Logs

- A missing value is not an exception. The writer uses the UUID fallback (FR-006).
- The writer logs a warning when the fallback count is above zero. The warning names the collection and the count.
- The writer logs an info line before each batch and a debug line after it (FR-014). All log text is ASCII.
- Logs never contain a secret. The key fields in this contract hold no credential.

## Compatibility

- SLE keys and single-field keys do not change (FR-007, FR-008).
- Affected entries receive identity keys for new writes. Legacy documents stay in place (D-7).
- A reader that queries `_key` for affected collections must change to field queries (D-1).

## Non-Goals

- No change to `on_duplicate`, to `WriteResult` counts, or to the router (D-12).
