# Quickstart: Sign-In Narrow Viewport Layout

## Prerequisites

- Create the local Python environment with `python3 scripts/bootstrap_worktree.py`.
- Use the Chromium browser installed by the bootstrap command.

## Validate the sign-in layout

Run the focused browser regression test:

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m pytest \
  tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py \
  -k test_sign_in_page_fits_narrow_viewport \
  --browser chromium -q --tb=short --timeout 300
```

The test passes when the sign-in page document width is no greater than the 390-pixel viewport width.
It uses a local test portal and does not contact the Mist cloud.
