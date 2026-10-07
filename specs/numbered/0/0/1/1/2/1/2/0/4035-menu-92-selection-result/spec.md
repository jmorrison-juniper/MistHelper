# Menu 92 selection result

## Problem

Menu 92 selects a site and logs the selected site identifier. The web portal
discards the handler result. The portal then classifies the successful
selection as a failed run because it has no output file or no-data message.

## Production reproduction

The measured production decision is:

```text
status=failed
completion_message=None
error_message='Operation finished without an output file or a no-data message.'
```

The reproduction uses a valid menu 92 site selection and the successful
selection log line. The selection does not create an output file.

PR #4081 changes `_RunLogHandler._OUTPUT_FILE_RE` near line 1488. It does not
repair `_finish_successful_operation` and `_completion_message`. PR #3990
merged and established the routed spec path.

## Scope

This change records the defect and adds a regression test. It does not change
production code. The later repair commit owns `operation.py`.

## Expected result

When menu 92 selects a valid site, the operation status is `completed` and the
completion message confirms the selected site. The result does not require an
output file.

## Acceptance criteria

- The test records the production decision and the exact failure message.
- The test remains an expected failure until the later repair commit.
- The later repair uses a menu-92-specific successful-selection marker.
- The later repair does not add `selected site id` to global no-output markers.
- The later repair removes the xfail.
