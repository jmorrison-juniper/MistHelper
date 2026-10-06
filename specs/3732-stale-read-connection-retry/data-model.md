# Data Model: Safe read transport retry

This feature adds no persistent data.
The model describes runtime policy and picker results.

## Safe Read Retry Policy

| Field | Type | Rule |
| - | - | - |
| Allowed methods | Frozen set of strings | Contains `GET` and `HEAD` only |
| Total retries | Integer | Equals 2 |
| Connection retries | Integer | Equals 2 |
| Read retries | Integer | Equals 1 |
| Status retries | Integer | Equals 0 |
| Other retries | Integer | Equals 0 |
| Redirect retries | Integer | Equals 0 |
| Backoff factor | Number | Equals 0 |
| Retry-header support | Boolean | False |

### Validation

- Reject a retry when the method is not GET or HEAD.
- Stop after one stale read retry.
- Stop after two eligible connection retries.
- Stop after two total retries.
- Do not retry an HTTP response status.

### State transitions

```text
initial safe read
├── valid response -> complete
├── stale read reset -> one retry
│   ├── valid response -> complete
│   └── transport failure -> failed
└── eligible connection failure -> bounded retry
    ├── valid response -> complete
    └── third failed attempt -> failed
```

Each write method moves from its first transport failure directly to `failed`.

## Write Session Policy

| Field | Type | Rule |
| - | - | - |
| SDK retries | Integer | Equals 0 |
| Transport retry total | Integer or Boolean | Equals 0 or `False` |
| Validation result | Boolean | True only when both retry layers are disabled |

The shared read policy is invalid for an upgrade write session.

## Pick-List Read Result

| Field | Type | Rule |
| - | - | - |
| Rows | List of dictionaries | Contains only rows from valid HTTP 2xx answers |
| Reason | String or `None` | Uses the fixed failure reason or the existing no-rows reason |
| Status | Integer or `None` | Comes from the SDK response |
| Valid empty | Boolean | True only for an empty HTTP 2xx answer |
| Failed source | Boolean | True when a client source has no usable HTTP 2xx answer |

### Validation

- A missing status is a failed read.
- A non-integer status is a failed read.
- A status outside 200 through 299 is a failed read.
- An empty HTTP 2xx answer is valid.
- A failed read cannot become an unmarked empty list.

## Operator Failure Message

| Field | Value |
| - | - |
| Text | `The portal could not reach the Mist API. Try again.` |
| Audience | A junior network operations engineer |
| Secret content | None |
| Use | Each unavailable or refused picker read |

## Client Source Merge

| Wireless source | Wired source | Result |
| - | - | - |
| Rows | Any state | Return all valid rows and log each failed source |
| Valid empty | Rows | Return the wired rows |
| Failed | Rows | Return the wired rows and keep the wireless failure log |
| Rows | Failed | Return the wireless rows and keep the wired failure log |
| Valid empty | Valid empty | Return a valid empty picker |
| Failed | Valid empty | Return a failed picker |
| Valid empty | Failed | Return a failed picker |
| Failed | Failed | Return a failed picker |
