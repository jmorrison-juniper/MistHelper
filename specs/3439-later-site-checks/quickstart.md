# Quickstart: Validate the later site checks

**Issue**: #3439 | **Plan**: [plan.md](plan.md)

## Prerequisites

1. Open the worktree `MistHelper-i3439`.
2. Activate the virtual environment with `.venv\Scripts\Activate.ps1`.
3. For the browser journeys, install Microsoft Edge.

## Unit tests and contract tests

Run the two new test files.

```powershell
python -m pytest tests/unit/upgrade_portal/test_issue_3439_site_checks.py tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py -q -p no:cacheprovider -o addopts=""
```

Expected result: every test passes.

## Browser journeys

Run the journeys in a real browser.

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTEST_ADDOPTS = "--browser-channel msedge"
python -m pytest tests/e2e/upgrade_portal/test_later_site_checks.py -q -p no:cacheprovider -o addopts=""
```

Expected result: every journey passes. Each journey writes screenshots under
`data/test-artifacts/upgrade-portal-journeys/later-site-checks/`. Read each
screenshot.

1. The single-site mode: the inventory page of the site of page two shows the
   error page with the status 503. The inventory page of a site of page one
   shows the devices.
2. The capture page shows the sentence in the capture error region.
3. The multi-site mode: the site picker shows the Caution message after the
   forward press.
4. The options page and the confirm page show the error page with the status
   503 after a reload.
5. The options save shows the sentence, and the form keeps each typed value.
6. The pre-check card shows the sentence in its error region.
7. The retry shows the sentence, and the retry does not open.
8. After each refusal, a whole read opens the step as before.

## Error answer

Read the inventory answer of the site of page two while the test header is
present. The answer is 503 with the code `site_list_incomplete`.
[data-model.md](data-model.md) holds the full answer.
