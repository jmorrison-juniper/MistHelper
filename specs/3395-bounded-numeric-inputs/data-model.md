# Data Model: Bounded numeric inputs

This repair changes no stored records, schema, primary key, or API payload.

| Value | Source | Normalization | Number bound | Invalid result |
| - | - | - | - | - |
| Picker offset | Query `offset` | Remove surrounding whitespace and one leading plus sign. | `sys.maxsize` | Caller fallback 0. |
| Capture tier text | JSON or form `tier` | None. | Largest known tier 3. | No tier. |
| Client page limit | Environment `MIST_PAGE_LIMIT` | Remove surrounding whitespace. | `MAX_PAGE_LIMIT` | `DEFAULT_PAGE_LIMIT`. |

The immutable shared reader owns a maximum number and a field name.
Its read method receives normalized text.
It returns an integer or `None`.
The caller retains its existing default, minimum clamp, or HTTP refusal.

The diagnostic contains the field name, reason, character count, and checked count.
It contains no raw input.
