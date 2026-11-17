# Implementation Plan: Fail Closed on VPN Inventory Errors

**Branch**: `jmorrison-juniper-wan-vpn-list-failure` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification for issue #4792.

## Summary

Keep VPN creation unavailable unless every page and VPN name is valid. Validate native SDK pagination headers, stop on repeated links, and preserve valid single-page and empty inventories.

## Technical Context

**Language/Version**: Python 3.15 or newer

**Primary Dependencies**: Existing `mistapi` SDK, `pytest`

**Storage**: N/A

**Testing**: Focused mocked tests in `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`

**Target Platform**: Windows, macOS, and Linux

**Project Type**: Python command-line application

**Performance Goals**: No additional network requests beyond existing VPN pagination.

**Constraints**: Do not call a live Mist organization. Retain the existing typed confirmation. Reject failed, malformed, or incomplete inventory.

**Scale/Scope**: One VPN inventory read in the existing WAN VPN builder.

## Constitution Check

- The feature uses the managed numbered root at `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure`. It does not add a direct child under `specs/`.
- The existing `specs/` root has 795 children. This change uses the managed `numbered/` route and adds no direct child to that root.
- The changelog change is one issue-specific release fragment. It does not edit `CHANGELOG.md`.
- The implementation keeps the existing Mist SDK list and create methods. It adds no direct HTTP transport.
- Synthetic tests cover native SDK headers, error payloads, complete empty inventory, invalid records, repeated links, later-page failures, and the stop-before-create behavior.
- The existing typed confirmation remains unchanged. No live organization call or mutation is part of implementation or validation.
- `specs/` has 795 direct children, and `WanVpnBuilder` already exceeds the five-member limit. This change uses the managed numbered route and adds only focused inventory validation methods.
- Separate incremental remediation action: track a later refactor that moves WAN VPN inventory handling into a compliant module and reduces the existing builder class size. This action is outside issue #4792.
- The commit subject will use a Conventional Commit form accepted by the title guard.

**Gate result**: Pass. The change preserves the current transport and confirmation boundary and adds no new product output.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
src/operations/wan/wan_vpn_builder.py
tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py
changelog.d/issue-4792-wan-vpn-list-failure.md
```

**Structure Decision**: Update the existing WAN VPN builder and its existing focused unit test module. Add one issue-specific release note. Do not edit the live integration test, which can create and delete VPNs.

## Phase 0: Research

The relevant behavior is fully specified. The repository already has a validated, paginated SDK response pattern for gateway profiles. The implementation will follow that pattern for VPN pages and return an unavailable result when any page fails.

## Phase 1: Design

- Stage VPN definitions until every response page has a successful status, valid result list, and usable name for each record.
- Treat a successful empty list as complete inventory.
- Treat an exception, failed status, malformed record, unusable name, invalid or inconsistent pagination headers, repeated link, or missing next page as unavailable inventory.
- Treat a truthy `error` field as a failure even when a 2xx body also contains `results`.
- Stop the workflow before the name prompt when inventory is unavailable.
- Include every page in duplicate-name validation and keep the typed confirmation.
- Add mocked tests only. Do not run live VPN integration tests.

**Post-design gate result**: Pass. The design adds no external interface, database, product output, or alternate transport.

## Complexity Tracking

No constitution violations require an exception.
