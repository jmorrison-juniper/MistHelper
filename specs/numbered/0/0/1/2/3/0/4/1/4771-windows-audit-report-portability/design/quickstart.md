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

Push a feature branch commit after coordinator review. The separate Windows workflow runs two native regressions on `windows-latest` only when a listed test input changes.

The workflow calls the real staged-file helper and the real report writer with synthetic evidence. It requires two passed tests and zero skips. It has no Mist credentials, endpoint, production data, or service.

The path filter includes the workflow, the dialog-audit report code and test, the workflow contract test, `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt`.

Do not treat the macOS skip as native Windows evidence. Do not merge until the Windows workflow reports both tests as passed.

## Non-Windows validation

On macOS or Linux, run the same focused tests. Verify that exclusive staging, mode `0600`, and safe atomic replacement remain active.
