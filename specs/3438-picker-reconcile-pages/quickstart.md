# Quickstart: Validate the lost-page notes

**Issue**: #3438 | **Plan**: [plan.md](plan.md)

## Prerequisites

1. Open the worktree `MistHelper-i3438`.
2. Activate the virtual environment with `.venv\Scripts\Activate.ps1`.
3. For the browser journeys, install Microsoft Edge.

## Unit tests

Run the two new test files and the three updated test files.

```powershell
python -m pytest tests/unit/upgrade_portal/test_issue_3438_picker_pages.py tests/unit/upgrade_portal/test_issue_3438_reconcile_pages.py tests/unit/upgrade_portal/test_org_picker.py tests/unit/upgrade_portal/test_cloud_cache.py tests/unit/upgrade_portal/test_site_stats_evidence_reader.py -q -p no:cacheprovider -o addopts=""
```

Expected result: every test passes.

## Browser journeys

Run the journeys in a real browser.

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTEST_ADDOPTS = "--browser-channel msedge"
python -m pytest tests/e2e/upgrade_portal/test_lost_site_page.py -q -p no:cacheprovider -o addopts=""
```

Expected result: every journey passes. Each journey writes a screenshot. Read
each screenshot.

1. In the single-site mode, the site picker shows both Caution notes above the
   site table.
2. In the multi-site mode, the site picker shows both Caution notes above the
   check boxes.
3. For an organization whose reads are whole, the site picker shows no note.

## Site list answer

Read `GET /api/sites` as the lost-page operator in the browser journey. The
answer holds `site_list_complete` and `device_counts_complete` with the value
`false`. [data-model.md](data-model.md) names each field.
