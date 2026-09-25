# Implementation Plan: Show a final multi-site operation as final

**Issue**: #3225 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The aggregate service and the cancel route refuse a cancel of a final
operation with 409 and no cloud request. The page renders no cancel form for a
final operation, and the page script hides the form when a poll reports a final
state. Four cells keep each word whole, a missing family reads `unknown`, and
the server builds one Cancellation text for the render and the poll.

## Technical context

- Python 3.13, Flask 3.1, and Jinja templates. The page script is plain
  ECMAScript 5 in `portal.js`, with no build step.
- `AggregateUpgradeService.cancel` writes the cancel marker, sends each child
  cancel, and stores each result through `_cas`.
- `aggregate_summary` builds the page context and the poll answer of an
  aggregate operation. `status_summary` builds both for an organization job of
  an earlier release.
- `paintOrgUpgradeStatus` repaints the page from each poll answer.

## Design

### 1. The service in `src/firmware/aggregate_upgrade_service.py`

- Add `FINAL_OPERATION_STATES = frozenset({"cancelled", "completed", "failed"})`.
- Add `FINAL_CANCEL_TEXT`, the refusal message with one `{state}` field.
- Add `FinalOperationError(ValueError)`.
- Add `_refuse_final(record, store)`. It reads the durable record through
  `_current`, and it raises the refusal for a final state.
- `cancel()` calls `_refuse_final` after the write session check and before
  `_start_cancellation`.

### 2. The route in `src/upgrade_portal/app/routes/org_upgrade.py`

- Add the code `NOT_CANCELLABLE = "org_upgrade_not_cancellable"`.
- Replace `TERMINAL_JOB_STATES` with the imported `FINAL_OPERATION_STATES`.
- `_cancel_aggregate` catches `FinalOperationError` before `ValueError`, and it
  answers 409 with the new code.
- `_cancel_org_job` calls the new helper `_final_job_refusal` after the
  ownership check. The helper reads the marker state.
- `aggregate_summary` and `status_summary` add `cancel_allowed`.
- `_aggregate_child_summary` adds `cancellation_text`.
- `_site_summary` adds `device_family: "ap"`.

### 3. The new module `src/upgrade_portal/upgrade/org_cancel_text.py`

- The class `OrgCancelText` has one public class method, `text(cancellation)`.
- It returns an empty text for a child job with no cancel result.
- It joins the parts with one space: `Status: <word>.`, the exact message,
  `Cancelled: <list>.`, `Writing firmware: <list>.`, and
  `No cancel available: <list>.`

### 4. The template `upgrade/org_progress.html`

- Render the form and the caution inside `data-org-cancel-controls` only when
  `cancel_allowed` is true.
- Render the note `org-upgrade-cancel-closed` with the state word. It is hidden
  when the cancel is allowed.
- The family cell and the status cell of the site table, and the site cell, the
  type cell, and the state cell of the device table, use the class `cell-word`.
  The screenshot of T006 showed the site cell break "Stand-In" and "Second"
  inside the word, so the site cell joins the list.
- The family default is `unknown` in the site table and in the outcome heading.
- The Cancellation cell prints `site.cancellation_text`.

### 5. The page script `portal.js`

- Remove `cancellationText`. `paintOrgUpgradeSites` prints
  `site.cancellation_text`.
- The family default is `unknown`. Cell 1 and cell 2 get `cell-word`.
- `orgDeviceRow` gives the site cell, the type cell, and the state cell
  `cell-word`.
- Add `paintOrgCancelControls(status)`. When `cancel_allowed` is false, it hides
  the form region, disables each control in it, fills the state word, and shows
  the note.
- `paintOrgUpgradeStatus` calls the new painter after the state paint.

### 6. The style sheet `portal.css`

- Add `.portal-table .cell-word { word-break: normal; overflow-wrap: normal; }`
  after the `cell-control` rule, with a comment for issue #3225.

### 7. Tests

- Unit tests in `tests/unit/firmware/test_aggregate_final_cancel.py`:
  - Each final state raises `FinalOperationError`, with no store write and no
    cloud call.
  - `attention_required` and `partial` stay cancellable.
- Unit tests in `tests/unit/upgrade_portal/test_org_cancel_text.py` for each
  part of the text and for an empty result.
- Contract tests in `tests/contract/upgrade_portal/test_org_final_cancel_routes.py`:
  - The 409, the code, the message, no cloud call, and an unchanged record for
    each final state.
  - The page and the poll of a final operation and of a running operation.
  - The family `unknown`, the outcome heading, and the Cancellation text.
- Contract tests in `test_org_upgrade_routes.py` for the earlier job marker and
  for its `ap` rows.
- A unit test that the page script list of finished states equals
  `FINAL_OPERATION_STATES`.
- A browser journey in `tests/e2e/upgrade_portal/test_org_final_operation_page.py`
  with screenshots at 960 pixels and at 1280 pixels.
- Update `test_org_upgrade_flow.py`, which cancels after a fake final poll.

## Risks

- A record whose stored state is old can still read as live. The cancel then
  runs as before. Issue #3367 covers the child jobs that already ended.
- A page that loaded the old script paints the old text until the operator
  loads the page again. The server answer stays valid for that script.

## Performance

- The refusal adds one store read before the first cancel write. The cancel
  path already reads the record before each write.
- The summary builds one short text for each child job. An operation holds a
  few child jobs, so the cost is small.

## Constitution check

- The change adds no dependency, no route, and no stored field.
- The change adds one error code and two answer fields. It removes no field.
- The change touches the cancel path of menu 239, so a human reviews the pull
  request. The pull request carries no auto-merge label.
