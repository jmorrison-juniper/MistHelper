# Implementation Plan: Preserve First Retry Failure Evidence

**Branch**: `jmorrison-juniper-gateway-retry-evidence` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/0/4/2/0/0/2/2752-gateway-retry-evidence/spec.md`.

## Summary

Carry the first caught exception through the gateway API and synthetic test retry loops. Include it in the final retry diagnostic. Keep API calls, retry timing, and returned values unchanged.

## Technical Context

- Use Python 3.13 or newer.
- Use the existing `mistapi` and `requests` packages.
- Store no new data.
- Test with `pytest` and mocked Mist API calls.
- Support Windows 11, macOS, and Linux.
- Keep the existing CLI and export package.
- Keep the existing request count and retry delay.
- Do not change public result shapes or call the live Mist API.
- Limit this slice to two retry helpers and their direct unit tests.

## Constitution Check

- New specification files use the managed eight-level base-5 route. The route parents have fewer than five children.
- The release note uses one unique file in `changelog.d/`. The change does not edit the shared changelog.
- The current process-folder baseline remains unchanged. A later maintenance issue can reduce any existing folder debt.
- The implementation changes only the two named retry modules and their direct tests.
- The implementation adds no API endpoint, credential, data store, or production-system change.
- The added retry evidence uses a per-item list and preserves the first exception only.

## Project Structure

### Documentation

```text
specs/numbered/0/0/0/4/2/0/0/2/2752-gateway-retry-evidence/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/
      requirements.md
```

### Source Code

```text
src/mist/access/api/api_fetch_utils.py
src/operations/exporting/export/gateway_test_exporter.py
tests/unit/api/test_api_fetch_utils.py
tests/unit/export/test_gateway_test_exporter.py
```

**Structure Decision**: Keep the change in the existing API and exporter modules. Add no shared retry abstraction.
