# Cleanup ordering evidence

## Decision

Delay every terminal notification until stream close and required capture cleanup finish.

## Rationale

The unchanged source calls `UtilityFinisher.finish()` inside `_execute()`.
The `run()` method subsequently calls `_close()` from `finally`.
`_close()` performs the capture identity check and matching deletion.
The existing sink wait therefore does not establish cleanup completion.

The deterministic test blocks the cleanup GET before the controlled API records it.
Both site and organization cases observed `STOPPED` while that barrier remained blocked.
The assertion failed without a retry, sleep-based observation, or timeout change.

Base commit: `9991d30a187e5d215462eefac60a09a57e5f99e5`.
Base tree: `8d28a4e9d24a27fed77528ec0975d6a5a88ad237`.

Command:

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py -k terminal_waits_for_matching_cleanup
```

Result: `2 failed, 5 deselected in 0.92s`.
Both failures reported `Terminal state was published while cleanup remained blocked.`
Production source and the existing utility test module were unchanged during this run.

## Alternatives considered

- Repeated passing runs cannot prove the ordering boundary.
- Waiting longer in the existing test hides the product defect.
- Removing identity checks can delete another capture.
- Mapping cleanup errors through the existing stop finisher hides cleanup failure.
- Changing capture timing would combine this repair with the separate #3575 behavior.

## Evidence limits

The issue-artifacts list endpoint returned HTTP 404.
The issue body and all three comments were read.
They contain no image attachment.
Only controlled loopback services run during verification.
