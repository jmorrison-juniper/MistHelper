# Research: Show a final multi-site operation as final

**Issue**: #3225

## Decision 1: The service refuses a cancel of a final operation

`AggregateUpgradeService.cancel` reads the stored operation before it writes the
cancel marker. If the stored state is `completed`, `cancelled`, or `failed`, the
service raises `FinalOperationError`. The service makes no write and sends no
cloud request.

### Rationale

- The service sends the cloud cancel calls, so the guard sits next to them.
  Every caller of the service then obeys the rule.
- `_current` reads the durable record. A stale page or a second tab cannot
  pass the guard with an old state.
- A cancel of a completed operation sent one cloud cancel call for each child
  job. The organization cancel sort then listed each upgraded access point as
  a cancelled device. That result is false.
- The single-site stop refuses every canonical final state in
  `StopRequestStore` with `RunNotStoppableError`. The multi-site refusal uses
  the same message shape: `The operation is final: completed.`
- `attention_required`, `partial`, `running`, and `planned` stay cancellable. A
  later read can settle `attention_required`, and the page poll keeps it for
  that reason (issue #3220).

### Alternatives

- **Check the state in the route only.** The route already reads the owned
  operation. A second caller of the service would then still send the cloud
  calls. Rejected.
- **Skip each final child job inside the cancel loop.** That rule also repairs
  a cancel of a running operation. It changes a pinned unit test and a wider
  behavior, so issue #3367 holds it. Rejected for this issue.

## Decision 2: The route answers 409 with its own code

`FinalOperationError` is a subclass of `ValueError`. The route catches it before
the general `ValueError` clause, and it answers 409 with the code
`org_upgrade_not_cancellable`.

### Rationale

- A client can tell a final operation from a damaged record. The general clause
  answers `org_upgrade_cancel_failed`.
- The single-site stop answers 409 with `run_not_stoppable`. The new code
  follows the same pattern.
- The subclass keeps every existing `ValueError` handler correct.

## Decision 3: The earlier organization job obeys the same rule

`_cancel_org_job` reads the state of the signed job marker after the ownership
check. If the state is final, the route answers the same 409 and sends no cloud
request.

### Rationale

- `remember_job_state` stores the last read state in the marker on each page
  view and each poll. The page that shows a final state therefore holds a
  marker with that state.
- The route used `TERMINAL_JOB_STATES` for the replay rule. The service now owns
  `FINAL_OPERATION_STATES`, and the route imports it. One set serves both rules.

## Decision 4: The summary carries `cancel_allowed`

`aggregate_summary` and `status_summary` add the boolean `cancel_allowed`. The
template renders the form only when the value is true. The page script hides
the form when a poll reports false.

### Rationale

- The single-site stop page reads `stop_available`, which the route computes.
  The multi-site page now reads one server value in the same way.
- The server decides the rule. The page script does not copy the state list for
  this decision.
- The controls signature of issue #3247 does not name the state. A poll that
  reports `completed` with no failed device does not load the page again. The
  page script must therefore hide the form itself.
- The script only closes the form. A final state never changes back, and a
  script that enables the submit button would pass the typed word gate.
- The name `cancel_allowed` does not contain the list name
  `no_cancel_available`, so a search for one name does not find the other.

## Decision 5: A new cell class keeps each word whole

The rule `.portal-table .cell-word` sets `word-break: normal` and
`overflow-wrap: normal`. The family cell, the status cell, the type cell, and
the state cell use it in the template and in the page script.

### Rationale

- The shared cell rule `word-break: break-word` lets a word break at any
  letter. The minimum width of a column then drops to one letter.
- With the new class, the minimum width of the column is its longest word. The
  table grows, and the scroll box of issue #3278 scrolls sideways.
- A cell that holds two words can still wrap between them.
- The address and version cells keep the shared rule. A long identifier must
  still fit a narrow screen.

## Decision 6: A missing family reads `unknown`

The template, the page script, and the outcome panel heading use the default
`unknown`. `status_summary` adds `device_family: "ap"` to each site row of an
earlier organization job.

### Rationale

- The default `ap` claimed a family that the record does not hold.
- The earlier organization job upgrades access points only. Its rows now state
  that fact from the server, so the page needs no guess.

## Decision 7: The server builds the Cancellation text

The new class `OrgCancelText` builds one text from a stored cancel result. The
child row of the summary carries it as `cancellation_text`. The template and
the page script print that text.

### Rationale

- One builder gives one format. The render and the repaint cannot differ.
- The labels match the headings of the cancel outcome panel: `Cancelled`,
  `Writing firmware`, and `No cancel available`.
- The status word gets the label `Status`. The message keeps the exact cloud
  words.

## Decision 8: The page adds no new link

The navigation bar links the site choice, the history, and the comparison on
every page. The single-site progress page adds no link for a final run, so
parity holds with no change.

## Fact checks

- `ORG_UPGRADE_FINISHED_STATES` in `portal.js` holds `cancelled`, `completed`,
  and `failed`. The poll stops on these words when no phase watch runs.
- `_aggregate_state` gives `failed` only when no child job is active, claimed,
  or uncertain. A `failed` operation is therefore final.
- `_cas` advances `record_version` on every write, also when nothing changes.
  A refusal before `_start_cancellation` keeps the version unchanged.
- The E2E test `test_org_upgrade_flow.py` fakes a poll with the state
  `completed` and then cancels. That fake now needs a live state.
