# Implementation Plan: Preserve Rate-Limit State on HTTP Failure

**Branch**: `jmorrison-juniper-http-4xx-test-quality-campaign` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/1/4/2/1/4611-rate-limit-refresh/spec.md`.

## Summary

Reject unsuccessful Mist SDK responses before reading quota data. Preserve every cached value on failure, and keep successful refresh behavior unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer
**Primary Dependencies**: `mistapi` 0.64.x, `requests` response objects
**Storage**: In-memory rate-limit cache
**Testing**: `pytest`
**Target Platform**: Windows, macOS, and Linux
**Project Type**: Python CLI and library
**Performance Goals**: Add no external request and no additional retry.
**Constraints**: Use the existing SDK method. Preserve cached state for all non-2xx responses. Make no live Mist request.
**Scale/Scope**: One helper, one unit-test module, one changelog fragment, and one bounded specification.

## Constitution Check

- The specification uses the managed numbered root and the eight-segment base-5 route for issue 4611.
- The new structural directories on the route have five children or fewer. Existing route parents have at most three children.
- The change adds one required, uniquely named release-note fragment. It does not edit the shared changelog.
- The code change touches the existing rate-limit helper. It adds no module, class, or package.
- The helper remains below the 25-line function limit. Test helpers and test methods remain below the same limit.
- The API call continues to use `mistapi.api.v1.self.usage.getSelfApiUsage`. No direct HTTP request is added.
- Tests use local native SDK response objects. They make no network request and use no credentials.
- Existing nested-source package debt remains tracked by issue #3824. This change does not add structural debt.
- The current `.specify/feature.json` selects another feature. Leave it unchanged.

## Design

### Response handling

Read the status from the SDK response before reading its data. Accept only status codes from 200 through 299. Route a missing response or a non-success status through the existing exception boundary. Do not write to the cache before status validation and data extraction.

Keep the current successful cache assignments and exception behavior. Include the failed status in the warning, but do not log a response body or credential.

### Tests

Use `requests.Response` and `mistapi.__api_response.APIResponse` to construct native SDK results. Stub only the `getSelfApiUsage` method. Verify HTTP 403 and HTTP 503 preserve the full cache and produce a warning. Verify HTTP 200 updates the cache. Use a valid usage-shaped failure body to prove status validation takes precedence over payload fields.

### Files

- `src/foundation/support/utils/rate_limiting.py`
- `tests/unit/test_rate_limiting.py`
- `changelog.d/issue-4611-rate-limit-refresh-http-status.md`
- `specs/numbered/0/0/1/2/1/4/2/1/4611-rate-limit-refresh/`

## Project Structure

```text
src/foundation/support/utils/rate_limiting.py
tests/unit/test_rate_limiting.py
changelog.d/issue-4611-rate-limit-refresh-http-status.md
specs/numbered/0/0/1/2/1/4/2/1/4611-rate-limit-refresh/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

**Structure Decision**: Keep behavior in the existing rate-limit utility and tests in its existing unit-test module. No contract directory is needed because this internal helper exposes no new interface.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | The change adds no structural or function-limit violation. | No alternative is needed. |
