# Data model: Long packet capture

## Capture request

| Field | Type | Rule |
| - | - | - |
| `duration` | Integer seconds | Accept 60 through 3600. Default to 60. |
| `num_packets` | Existing integer | Keep the current range and default. |
| `max_pkt_len` | Existing integer | Keep each device family's current range. |
| `tcpdump_expression` | Existing text | Keep the current validation and length limit. |

The server validates each value before it builds a Mist request. Reject Boolean,
Unicode-digit, non-decimal, negative, fractional, and oversized duration input.

## Capture session state

The existing session record remains the public session entity. Its utility
runner state gains private monotonic start and capture-completion values.

| State | Meaning |
| - | - |
| `CONNECTING` | The stream is opening or awaiting its subscription confirmation. |
| `LIVE` | The capture start succeeded and the session can receive records. |
| `STOPPING` | The operator requested a stop. The runner is checking cleanup. |
| `FINISHED` | The selected duration or a matching capture-end event completed. |
| `STOPPED` | The operator stop completed. |
| `FAILED` | Start, stop, identity, stream, or cleanup could not be confirmed. |

The capture clock starts after the successful capture response. The stream
remains open through quiet periods. The matching end event has the selected
capture identifier and a null packet record.

## Resource limits

The current session buffer, packet limits, and idle limit remain unchanged.
Only capture lifetime can exceed the configured generic stream life limit. Its
maximum is the greater of the configured limit and the selected duration plus
30 seconds. Measure this interval from the first live signal after the successful
capture response. Keep setup within the configured generic limit. Later output
does not reset the capture interval.
