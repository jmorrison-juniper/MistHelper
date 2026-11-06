# Implementation Plan: Reject Profiles from Failed Responses

**Branch**: `jmorrison-juniper-fix-4564-wan-vpn-profile-503` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/1/2/2/4/4564-wan-vpn-profile-503/spec.md`.

## Summary

The WAN VPN builder reads profile data from an HTTP 503 response. Check the Mist SDK response status before reading its profile data. Keep the existing endpoint and successful-response behavior.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi` 0.64.x.

**Storage**: None.

**Testing**: `pytest` unit tests with mocked Mist SDK responses.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Python CLI application.

**Performance Goals**: No measurable change to successful profile reads.

**Constraints**: Reject non-success HTTP responses before profile data is used. Do not call Mist during tests.

**Scale/Scope**: One existing profile-read method, its unit tests, one release-note fragment, and this feature record.

## Constitution Check

- The code uses the existing Mist SDK method `listOrgDeviceProfiles`. It adds no transport or authentication path.
- The test uses a native SDK response object and a mocked endpoint call. It proves failure safety without a live request.
- The change adds no class, function, or nested source package. The existing `_fetch_profiles` method remains within the documented limits.
- The feature record uses the required eight-level base-5 route. Its root will contain four items: `spec.md`, `plan.md`, `tasks.md`, and `design/`.
- The existing `changelog.d/` folder contains 272 entries. This change adds only its required unique issue fragment.
- Separate remediation action: track gradual reduction of the existing `changelog.d/` folder debt in a future process change. That work is outside this bug fix.
- The tracked `.specify/feature.json` points to issue #4258. Keep that other feature pointer unchanged.

**Gate result**: Pass. The new record stays within the bounded route. The required release-note fragment is the only new direct child of the established release-note folder.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/1/2/2/4/4564-wan-vpn-profile-503/
  spec.md
  plan.md
  tasks.md
  design/
    data-model.md
    quickstart.md
    research.md
    checklists/
      requirements.md
```

### Source Code

```text
src/operations/wan/wan_vpn_builder.py
tests/unit/test_wan_vpn_builder.py
changelog.d/issue-4564-wan-vpn-profile-503.md
```

**Structure Decision**: Change the existing WAN VPN builder and its unit test. Do not add a class, API method, or data store.

## Phase 0: Research

The Mist SDK `APIResponse` exposes `status_code` before its `data` is passed to pagination. The failure check can use the SDK response directly. No unresolved technical choices remain.

See [research.md](design/research.md) for the evidence and rejected alternatives.

## Phase 1: Design

- The response consists of an HTTP status and a body that may contain profile data.
- A successful response may supply profiles. An unsuccessful response supplies none.
- The public API call and its gateway filter remain unchanged.
- The feature is internal to the CLI. It adds no external interface contract.

See [data-model.md](design/data-model.md) and [quickstart.md](design/quickstart.md).

## Complexity Tracking

| Existing condition | Decision | Separate remediation action |
|---|---|---|
| `changelog.d/` has 272 direct entries because each issue requires a unique fragment. | Add only the fragment for issue #4564. | Track a separate process change to reduce existing folder debt. |
