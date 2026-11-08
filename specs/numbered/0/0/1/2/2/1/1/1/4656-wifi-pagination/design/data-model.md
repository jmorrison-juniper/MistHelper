# Data Model: WiFi Pagination Failure Handling

## WiFi Page Read

Represents one requested list of WiFi client or session records.

| Field | Meaning | Validation |
| - | - | - |
| `records` | Ordered records from successfully received pages. | Add records only after the page passes HTTP status and body checks. |
| `is_partial` | Whether a later transport request failed after at least one valid page. | Set only when at least one page completed and a later transport request raises. |
| `failure_status` | HTTP status for a later response that failed validation. | An HTTP error rejects the read and does not produce a partial result. |

## WiFi Export Result

Represents the combined client and session data for one site.

| State | Meaning | Export behavior |
| - | - | - |
| Complete | All pages for both datasets succeeded. | Keep current complete export behavior. |
| Partial | A later transport request failed after a valid page. | Export records from successful pages and clearly report that the result is partial. |
| Valid empty | All pages succeeded and both datasets contain no records. | Keep the current no-data placeholder behavior. |
| Failed | A first-page response failed or any page returned an HTTP error. | Report failure and do not create success-shaped output. |

## Relationships

- One export request reads one WiFi client page sequence and one WiFi session page sequence.
- The combined export uses the records collected from both sequences.
- A partial state in either sequence makes the combined export partial.
