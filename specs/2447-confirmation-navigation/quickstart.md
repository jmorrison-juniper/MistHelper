# Quickstart: Confirm Navigation

## Prerequisites

- Repository dependencies installed.
- Portal test fixtures available.
- No production upgrade submission.

## Contract validation

```powershell
python -m pytest tests/contract/upgrade_portal/test_upgrade_routes.py -k "run_page"
```

Expected: the prepared run exposes `upgrade-confirm-link`; unprepared runs do not.

## Browser validation

```powershell
$env:CAPTURE_PORT='8066'
python -m pytest tests/e2e/upgrade_portal/test_capture.py -k "confirm or run"
```

Expected: an operator reaches the confirmation page through visible controls without typing `/confirm` into the address bar.
