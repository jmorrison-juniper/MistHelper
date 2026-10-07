# Implementation Plan: Empty Export Endpoint Response Handling

## Summary

Add a shared HTTP response status helper and wire it into the permitted endpoint family exporter.
Leave the claimed simple endpoint exporter unchanged for the #4043 follow-up.

## File Boundary

- `src/operations/exporting/export/http_response_status.py`
- `src/operations/exporting/export/endpoint_family_exporter.py`
- `tests/unit/export/test_http_response_status.py`
- `tests/unit/export/test_endpoint_family_exporter.py`
- `changelog.d/issue-4038-export-site-devices-http-errors.md`
- The three routed specification files in this directory

## Verification

Run targeted tests, compile checks, full Ruff, full Black, mypy, symbol checks,
the test-quality preflight, and the changed-from analyzer.
