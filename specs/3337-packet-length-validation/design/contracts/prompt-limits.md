# Terminal Contract: Packet Length Limits

**Issue**: #3337

The existing CLI supplies these interfaces.
The design adds no API endpoint.
The correction changes only the displayed and enforced maximum.
No payload format, command option, SDK version, or public signature changes.

## Real Entry Points

| Path | Existing entry point | Return |
| --- | --- | --- |
| Shared | `PacketCapturePrompts.prompt_max_packet_length(default: int = 128)` | `int | None` |
| Wireless | `SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)` | `tuple[int, ...] | None` |

The shared path must resolve the real `src.utils.input_utils.InputUtils`.
The wireless path receives that same real class.
Tests may substitute `builtins.input` only.

## Exact Packet-Length Prompts

Preserve the wording and trailing space.
These Python strings include the trailing ASCII space inside each closing quote:

```python
"Enter max packet length in bytes (default 128, max 1536): "
"Enter max packet length in bytes (default 1300, max 1536): "
```

The first line applies to the shared default.
The second line applies to wireless and the shared caller default 1300.
The shared interpolation preserves other valid defaults from callers.
The input context remains `max_pkt_len`.

## Exact Diagnostics

The range diagnostic begins with a newline:

```text
! Max packet length must be between 64 and 1536 bytes
```

The conversion diagnostic begins with a newline:

```text
! Invalid max packet length: {trimmed_text}
```

`{trimmed_text}` represents the real text from `safe_input`.
The shared path prints its diagnostic.
The wireless path logs its diagnostic at WARNING.
Neither prompt nor range diagnostic may describe 2048 as supported.

Preserve these input-safety log messages:

```text
[EOF] Input stream closed during max_pkt_len. Using default value: '128'
[EOF] Input stream closed during max_pkt_len. Using default value: '1300'
[INTERRUPT] User interrupted max_pkt_len. Canceling...
```

The EOF notice uses the applicable default.
The interruption notice precedes the existing conversion failure.
Do not change these messages to implement the limit correction.

## Required Results

| Input at packet length | Shared result | Wireless result after earlier inputs `120`, `7` |
| --- | --- | --- |
| Any integer from 64 through 1536 | That integer | `(120, 7, selected_integer)` |
| 63 or any integer from 1537 through 2048 | `None` and the range error | `None` and the range error |
| 0, -1, 2049, or 9999 | `None` and the range error | `None` and the range error |
| `text`, `64.0`, or `1e3` | `None` and the conversion error | `None` and the conversion error |
| Empty or whitespace-only text | 128, or the valid caller default | `(120, 7, 1300)` |
| A padded valid integer | The unchanged integer | `(120, 7, selected_integer)` |
| EOF | 128, or the valid caller default, with the EOF notice | `(120, 7, 1300)` with the EOF notice |
| `KeyboardInterrupt` | `None` with the cancellation notice | `None` with the cancellation notice |

Blank input across the wireless sequence returns `(60, 1024, 1300)`.
EOF across that sequence returns the same tuple.
Valid duration and packet count remain unchanged after packet-length selection.
An invalid packet length returns no settings.
The tests must not start later capture actions.

## Exhaustive Numeric Evidence

For each path, prove 1473 accepted integers: 64 through 1536.
For each path, prove 513 required rejected integers: 63 and 1537 through 2048.
Also prove the additional invalid and safety cases above.
Record the execution count for each path separately from the pytest item count.
Each parameterized test item executes one real path.
The final matrix uses `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
Both functions reside in existing `tests/unit/capture/test_multi_ap_scan_workflow.py`.
Parameterize each function for `shared` and `wireless`.
Group raw input, expected length, and exact diagnostic in the limits-case parameter.
The supplied final matrix executed 4010 items, with 2005 per path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.
The final green run passed 4010 cases with zero failures, errors, or skips.
These results come from supplied verified evidence, not execution by the documentation owner.
