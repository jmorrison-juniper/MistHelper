# Implementation Plan: WAN VPN Update Response

**Branch**: `jmorrison-juniper-4379-wan-vpn-update-report` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/0/0/0/4/4379-wan-vpn-update-response/spec.md`.

## Summary

Check the Mist SDK response status before the WAN VPN manager reports changed paths. Accept 2xx responses and fail visibly for other statuses.

## Technical Context

- **Language/Version**: Python 3.13 or newer
- **Primary Dependencies**: `mistapi>=0.64.1,<0.65`
- **Storage**: None
- **Testing**: pytest with mocked SDK responses
- **Target Platform**: Windows, macOS, and Linux
- **Project Type**: Python command-line tool
- **Performance Goals**: No added network requests
- **Constraints**: Use the existing SDK method and never call a live Mist service during tests.

## Constitution Check

- The feature remains in the existing WAN manager and test module.
- The specification uses the eight-level base-five route. The `specs/` root has 795 existing direct children, so this change adds no direct child there. A separate migration must reduce that existing debt.
- The response check uses the existing `mistapi.api.v1.orgs.vpns.updateOrgVpn` method.
- The feature adds no owned transport, persistent data, configuration, or credential.
- Logs identify the VPN and status only. Tests use mocked SDK responses.
- The existing `.specify/feature.json` pointer names another feature and remains unchanged.
- The feature adds one issue-specific release-note fragment. The release coordinator owns `CHANGELOG.md`.

## Phase 0: Research

See [research.md](design/research.md). The published `mistapi` 0.64.1 source confirms that `updateOrgVpn` returns `APIResponse` and that `APIResponse.status_code` can be `None`.

## Phase 1: Design

- [Data model](design/data-model.md): no stored data changes.
- [Response contract](design/contracts/update-response.md): accept only HTTP 2xx statuses.
- [Quickstart](design/quickstart.md): run the focused unit test without Mist credentials.

## Project Structure

```text
src/operations/wan/wan_hub_group_manager.py
tests/unit/test_wan_hub_group_manager.py
changelog.d/issue-4379-wan-vpn-update-response.md
specs/numbered/0/0/1/2/0/0/0/4/4379-wan-vpn-update-response/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    └── checklists/
```

**Structure Decision**: Keep the behavior in the existing manager and tests. Put the specification in the managed numeric route. Use a separate release-note fragment for issue #4379.

## Complexity Tracking

No new module, class, or dependency is required. The existing `specs/` direct-child debt needs a separate migration and does not expand this feature.
