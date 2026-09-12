# Quickstart: Verify Complete Tier 3 Capture Output

## Local tests

1. Run the capture export tests.
2. Run the capture table tests.
3. Run the capture E2E browser tests in strict mode.
4. Run Ruff, Black, and mypy on the changed Python files.

## Browser journey

1. Sign in with the environment token mode.
2. Select an organization and a site.
3. Take the site lock.
4. Select Tier 3.
5. Start the capture.
6. Wait for `Verified`.
7. Confirm that all nine result tables are present.
8. Confirm that empty Tier 3 tables state that they have no rows.
9. Download CSV and JSON.
10. Confirm that each stored section count matches its export kind count.
11. Release the site lock.

Warning: Do not start the upgrade. This verification reads site state only.
