# Implementation Plan: Guarded Marvis Alarm Acknowledge

## Design

- Add a class that owns the second confirmation and the batch loop.
- Keep the Mist call in `MarvisActionsClient`.
- Join explicit alarm IDs before mode 3 resolves the selected actions.
- Acknowledge only results that the verify read marks `resolved`.
- Add alarm acknowledge fields to the existing mode 3 result rows.
- Add a seventh operations portal control with a blank default.

## Validation

- Test the client request shape.
- Test that a blank confirmation sends no request.
- Test that 1,001 alarms use batches of 1,000 and 1.
- Test that a failed resolve never makes its alarm eligible.
- Test the portal control order and the submitted answer order.
- Run Ruff, Black, mypy, and focused pytest.

## Release

Open a pull request with the `needs-human-review` and `destructive` labels. Do
not add the `auto-merge` label.
