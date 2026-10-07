# Plan: record menu 92 selection result

## Approved commit

Add the focused regression test, the issue specification, the implementation
plan, and one changelog fragment. Do not edit `web_portal/services/operation.py`.

## Future production repair

The later repair must preserve the successful handler result from the operation
execution decision around lines 113-118. It must pass that result to the
completion decision instead of discarding it after the handler returns.

The later repair must update the completion decision around lines 1194-1201.
It must recognize a menu-92-specific successful-selection marker and return a
selection completion message. The marker must identify a successful selection,
not a general no-output condition.

The later repair must not add `selected site id` to global no-output markers.
That text is a successful menu-92 result and must not make unrelated empty
operations complete. The later repair removes the xfail from the focused test.

## Test design

Add `test_menu_92_successful_selection_completes_without_file` to
`tests/unit/web_portal/test_portal_silent_completion.py`. Build the production
`OperationExecutor` decision for menu 92, record the successful selection
result, and call `_finish_successful_operation`.

The test must assert a future `completed` status and a completion message that
confirms the selected site. Until the production repair lands, the test must
remain an xfail with this exact reason:

```text
Issue #4035: successful site selection is classified as a failed no-output run.
```

The current xfail must expose the measured failed status and exact error:

```text
status=failed
completion_message=None
error_message='Operation finished without an output file or a no-data message.'
```

## Validation

Run the focused test and confirm exactly one xfail. Run the full Ruff and
Black checks. Run the test-quality preflight and the changed-from analyzer
when the local inputs permit it.
