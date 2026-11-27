# Contract: Port Series Response

This contract defines how the service reads the response of the port series call. It also defines the state that each outcome produces.

## Accepted Shape

The response body is a JSON object with these fields.

| Field | Type | Rule |
| - | - | - |
| `start` | Integer | Equals the requested window start (FR-012) |
| `end` | Integer | Equals the requested window end (FR-012) |
| `interval` | Integer | Equals 3600 (FR-002) |
| `timestamps` | Array of integers | Each value lies in the window and sits on a UTC hour |
| `rx_bps` | Array of numbers or null | Each value is a finite, non-negative number or null |
| `tx_bps` | Array of numbers or null | Each value is a finite, non-negative number or null |
| `next` | Value or null | Present means partial (FR-003) |

Caution: the OpenAPI file names `results` and `rt` for this response (R-39). The accepted shape uses named arrays (D-4). A response in the OpenAPI shape is malformed and fails closed. The live shape is unverified (U-2).

## Validation Order

1. Reject a status code other than 200 with the status state in the table below.
2. Reject a body that is not an object as `malformed_response`.
3. Reject a window mismatch as `window_mismatch`.
4. Reject an interval other than 3600 as `malformed_response`.
5. Reject a missing array or an array with a different length as `malformed_response`.
6. Reject more than 168 samples as `malformed_response`.
7. Reject a timestamp outside the window or off the UTC hour as `malformed_response`.
8. Convert each invalid rate value to null for that sample.
9. Compute coverage and totals from the valid samples.

Each rule returns on its first failure.

## Outcome States

| Outcome | Data state | Notice |
| - | - | - |
| 200 with complete, valid samples | `live` | None |
| 200 with a `next` value or fewer than 168 samples | `partial` | Coverage shown |
| HTTP 429 | `stale` if a prior value exists, otherwise `unavailable` | Rate limit notice (R-12) |
| HTTP 4xx or 5xx | `stale` if a prior value exists, otherwise `unavailable` | Status notice without the body |
| Transport error | `stale` if a prior value exists, otherwise `unavailable` | Error class name only |
| Malformed response | `unavailable` for the new value. The prior value stays stale. | Malformed notice |
| Admission refusal | `unavailable` or `stale` | Admission notice without credentials |

Caution: a malformed response never replaces a prior complete value with an empty value (FR-012). The prior value remains with its collection time.

## Output Shape

The service writes each accepted value with the following fields.

| Field | Meaning |
| - | - |
| `samples` | List of objects with `timestamp`, `timestamp_utc`, `rx_bps`, and `tx_bps` |
| `rx_bytes` | Seven-day RX total from valid samples (D-5) |
| `tx_bytes` | Seven-day TX total from valid samples (D-5) |
| `coverage` | Present samples divided by 168 |
| `sample_count` | Present samples |
| `state` | One data state |
| `collected_at_utc` | UTC time of the refresh that wrote the value |
| `resolution` | `1 hour` for every range |

The range keys hold the sliced values for 1h, 6h, 24h, 3d, and 7d (D-2). The slices keep the same field names.

## Units and Time

- Rates use bits per second. The OpenAPI rate schema states bits per second (R-44).
- Totals use bytes.
- Times use UTC ISO 8601 text with a `Z` suffix.
- Epoch values use integer seconds.
