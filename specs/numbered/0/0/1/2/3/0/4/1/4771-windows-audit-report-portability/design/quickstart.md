# Quickstart: Windows Audit Report Portability

## Prerequisites

- Use the repository Python environment.
- Use synthetic report data only.
- Do not select a live Mist operation.

## Focused regression

Run the existing writer tests:

```text
python -m pytest tests/e2e/websockets_tab/dialog_audit/test_inventory.py
```

The tests must cover report contents, owner-only access, unsafe path rejection, failure cleanup, and preservation of earlier files.

## Windows validation

On Windows, run the focused tests and a synthetic report write in the approved directory. Verify that both files contain the expected data and that their access controls name only the current owner.

## Non-Windows validation

On macOS or Linux, run the same focused tests. Verify that exclusive staging, mode `0600`, and safe atomic replacement remain active.
