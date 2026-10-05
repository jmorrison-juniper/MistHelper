# Quickstart: Validate WebSocket Form Cancellation

## Prerequisites

- Use the repository's configured development environment with Python 3.13+
  and the development dependencies from `requirements-dev.txt`.
- Playwright browser support must be installed as required by the repository's
  E2E test setup.
- Run only against the fake portal harness. Do not connect to a Mist
  organization or start a live operation.

## Regression scenario

1. Open the WebSockets page as a normal user in the browser harness.
2. Keep an existing fake live session card visible.
3. Select an operation with a picker and wait until the test holds its picker
   response.
4. Enter any available target/parameter/confirmation values, then activate
   the form's Cancel control.
5. Verify that the form is unselected, its fields and confirmation are empty,
   and Start cannot submit an operation.
6. Release the delayed picker response. Verify that the form stays unselected
   and that no current field, selected-entry presentation, or shared result
   changes.
7. Verify that the original live session card retains the same identity and
   state.
8. Verify that the fake session-start route observed zero requests during the
   cancellation journey, and that no session-stop request was issued.

Also exercise supersession: start a picker read for selection A, select
selection B, then release A's response. Only B's valid picker results may be
visible.

## Validation command

The ownership gate is cleared, and the regression is in the existing browser
test module. Run:

```text
pytest tests/e2e/websockets_tab/test_websockets_terminal.py -k cancellation
```

Expected outcome: the browser regression passes with the fake harness; picker
requests are controlled, zero operation-start requests occur on Cancel, and
the live session card remains unchanged. The test may follow the repository's
normal Playwright skip behavior when Playwright is unavailable.

## Design references

- State and transition definitions: `data-model.md`
- Behavioral UI and asynchronous-response contract: `contracts/ui-cancellation.md`
- Implementation plan and validation status: `../plan.md`
