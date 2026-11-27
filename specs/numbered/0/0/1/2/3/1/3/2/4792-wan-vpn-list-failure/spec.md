# Feature Specification: Stop VPN Creation When the VPN Inventory Is Unverified

**Feature Branch**: `fix/4792-wan-vpn-list-failure`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4792, "[Bug]: WAN VPN builder treats a failed VPN list as empty." The builder runs from menu 147. The issue names menu 164. On `main`, menu 164 is a different operation. See Clarifications.

**Problem**: `WanVpnBuilder._fetch_existing_vpns` returns an empty list after an exception. It does not check the response status. It does not prove that every page was read. The menu then asks for a VPN name with no duplicate check. A create call can then add a VPN with the name of an existing VPN.

## Clarifications

### Session 2026-11-26

- Q: Which menu runs the WAN VPN builder? -> A: Menu 147. On `main`, `MistHelper.py` registers `WanVpnBuilder.execute` under `"147"` at lines 6170 to 6179. Menu 164 is the gateway template apply operation at lines 5106 to 5114. The issue text, PR #4619, and the test module docstring still name menu 164. This record treats that name as stale.
- Q: Is menu 147 a destructive operation? -> A: The registry places menu 147 in the `interactive` category. Its menu entry sets `destructive=False`. The builder still creates a VPN in Mist through `createOrgVpn`. The typed word `CREATE` and the owner review gate stay in place.
- Q: Does this change rebase commit `8d8f1a63c`? -> A: No. That commit sits on a branch that is 42 commits behind `main` and 2 commits ahead. This record uses the commit as a design reference only. The fix starts from `main`.
- Q: What does an empty list mean? -> A: Only a verified read with zero records means an empty VPN inventory. Every other failed read means an unavailable inventory.
- Q: What proves that a read is complete? -> A: Each page must carry valid pagination headers. A page without a next link must prove that it is the last page. Missing or invalid headers stop the read.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop before the name prompt when the VPN inventory is unverified (Priority: P1)

An operator starts menu 147 for an organization. The builder reads the VPN inventory before it asks for a VPN name. If the read cannot prove a complete inventory, the builder stops. It shows the existing error line and one stop line. It asks for no name and creates no VPN.

**Why this priority**: A failed read that looks empty can allow a VPN with the name of an existing VPN. The operator also sees "No existing VPN definitions" after a read that failed.

**Independent Test**: Mock `listOrgVpns` to raise an exception, to return HTTP 503, to return a page without pagination headers, and to return a record without a name. Run `WanVpnBuilder.run()` for each case. Verify that no name prompt and no `createOrgVpn` call occur.

**Acceptance Scenarios**:

1. **Given** `listOrgVpns` raises an exception, **When** the operator starts menu 147, **Then** the builder stops before the name prompt and makes no VPN create call.
2. **Given** the first page returns HTTP 503, **When** the builder reads the inventory, **Then** the inventory is unavailable and no VPN create call occurs.
3. **Given** a page with a 2xx status and no pagination headers, **When** the builder reads the inventory, **Then** the inventory is unavailable.
4. **Given** the first page succeeds and a later page fails, **When** the builder reads the inventory, **Then** the builder discards every earlier page and stops.

---

### User Story 2 - Check each new name against every verified VPN (Priority: P1)

An operator enters a name that matches an existing VPN. The builder rejects the name when the match is on a later page. It also rejects the name when the match differs only by letter case or surrounding spaces. A verified empty inventory keeps the normal flow.

**Why this priority**: Duplicate protection depends on a complete inventory. A verified empty inventory must not block the first valid VPN.

**Independent Test**: Mock two verified pages with the duplicate name on page 2. Enter the duplicate name, then enter `q`. Verify that the builder asks again and makes no create call. Mock a verified empty inventory and verify that the name prompt appears.

**Acceptance Scenarios**:

1. **Given** a verified inventory of two pages, **When** the operator enters a name from page 2, **Then** the builder rejects the name and asks again.
2. **Given** a verified empty inventory, **When** the operator starts menu 147, **Then** the builder asks for a name as before.
3. **Given** an existing VPN named `OrgOverlay` with trailing spaces in Mist, **When** the operator enters `orgoverlay`, **Then** the builder rejects the name.

---

### User Story 3 - Review the evidence with mocked responses (Priority: P2)

A reviewer runs the focused unit test module. Each failure class has a named test case. The tests use mocked native responses. No test calls a live Mist organization. No test uses a production credential.

**Why this priority**: The owner requires a human review of this safety path before merge.

**Independent Test**: Run `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py -q`. Verify that the new cases fail on the unchanged code and pass after the change.

**Acceptance Scenarios**:

1. **Given** the unchanged code, **When** the reviewer runs the new cases, **Then** each failure-class case fails.
2. **Given** the changed code, **When** the reviewer runs the module, **Then** every case passes.

### Edge Cases

- A 2xx page with an empty list and a total of 0 is a verified empty inventory.
- A next link that repeats an earlier link makes the inventory unavailable.
- A page number above the page count that the first page declares makes the inventory unavailable.
- A total or a limit that changes between pages makes the inventory unavailable.
- A record that is not an object, has no `name`, or has a blank `name` makes the inventory unavailable.
- A next link with no following response from `mistapi.get_next` makes the inventory unavailable.
- An exception from `listOrgVpns` or from `mistapi.get_next` makes the inventory unavailable.
- An operator who enters `q` still cancels the name prompt.
- An operator who enters a blank name is asked again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The reader MUST return an unavailable inventory when the list request raises an exception.
- **FR-002**: The reader MUST return an unavailable inventory when any page has a status code outside 200 through 299.
- **FR-003**: The reader MUST return an unavailable inventory when any page holds data that is not a list.
- **FR-004**: The reader MUST return an unavailable inventory when any record is not an object or has no nonblank string `name`.
- **FR-005**: The reader MUST require the headers `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` on every page, each as an integer. The limit and the page MUST be 1 or more. The total MUST be 0 or more.
- **FR-006**: A page without a next link MUST prove that it is the last page. The reader MUST accept that page only when the limit multiplied by the page is at least the total.
- **FR-007**: A page with a next link MUST declare more records. The reader MUST accept that page only when the limit multiplied by the page is less than the total. It MUST follow only a nonblank next link that it has not followed before.
- **FR-008**: The reader MUST return an unavailable inventory when a page number exceeds the page count that the first page declares. It MUST also return an unavailable inventory when the limit or the total differs from the first page.
- **FR-009**: The reader MUST return an unavailable inventory when `mistapi.get_next` returns no response for a next link.
- **FR-010**: The reader MUST return an empty list only for a verified read with zero records.
- **FR-011**: The reader MUST NOT call `mistapi.get_all`. It MUST request each later page with `mistapi.get_next` and validate that page before it uses the records.
- **FR-012**: The builder MUST stop before the name prompt, the VPN list display, the profile list display, the preview, the typed confirmation, and the create call when the inventory is unavailable.
- **FR-013**: The builder MUST show the existing message `! Error retrieving VPN definitions. Check API connectivity.` when the inventory is unavailable. It MUST show one more error line that states that no VPN was created.
- **FR-014**: The builder MUST compare each entered name with every nonblank name in the verified inventory. The comparison MUST ignore letter case and surrounding spaces.
- **FR-015**: The builder MUST keep the typed word `CREATE` and the existing `safe_input` confirmation unchanged.
- **FR-016**: The change MUST add no method to `WanVpnBuilder`. The new logic MUST live in the class `VpnInventoryReader` in the new module `src/operations/wan/vpn_inventory.py`.
- **FR-017**: The reader and the builder MUST write an info line before each list request and each next-page request. They MUST write a debug line after each one. An exception MUST write an error line that names the exception type and no secret.
- **FR-018**: The change MUST add one changelog fragment. It MUST NOT change the menu number, the registry category, or the README.

### Mist Cloud Transport Requirements

- The existing `mistapi.api.v1.orgs.vpns.listOrgVpns` method reads the VPN inventory. The existing `mistapi.api.v1.orgs.vpns.createOrgVpn` method creates the VPN. `mistapi.get_next` requests each later page.
- The change adds no direct HTTP request and no owned transport.
- SDK insufficiency is not applicable. The SDK methods remain sufficient for the read and for the create.
- SDK authentication and endpoint parity are unchanged. The session and the endpoint path `/api/v1/orgs/{org_id}/vpns` stay the same.
- Failure safety and secret redaction are covered by mocked tests. The log lines name the exception type and never log a token.

### Key Entities *(include if feature involves data)*

- **VPN record**: One object in a list response. Its natural key is `id`. Its duplicate key is `name` after trimming and lowering the case.
- **Page**: One response from `listOrgVpns` or from `mistapi.get_next`. It holds a status code, data, a next link, and pagination headers.
- **Verified inventory**: All records from every page of one organization. It can hold zero records.
- **Unavailable inventory**: The result when the read cannot prove a complete inventory. It holds no records and stops the builder.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each unavailable-inventory case stops before the name prompt. The count of name prompts in those cases is zero.
- **SC-002**: Each unavailable-inventory case makes zero `createOrgVpn` calls.
- **SC-003**: The verified empty case asks for a name one time.
- **SC-004**: A duplicate name on page 2 is rejected before any create call.
- **SC-005**: Each new failure-class case fails on the unchanged code and passes after the change.
- **SC-006**: The method count of `WanVpnBuilder` does not increase.

## Assumptions

- Mist returns `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` on each 2xx page of `listOrgVpns`. The local OpenAPI file does not document these headers, and no upstream page was readable. The owner checks this before merge in T-HEADER-CHECK.
- The `vpn` schema requires `name` with at least one character. See `documentation/mist-api-openapi31yaml.yaml` lines 117790 and 117807.
- The installed `mistapi` is version 0.64.1. That version satisfies `pyproject.toml` line 29 and `requirements.txt` line 129.
- On `main`, the builder runs from menu 147.

## Out of Scope

- `WanHubGroupNumberManager` in `src/operations/wan/wan_hub_group_manager.py` (lines 170 to 185) has the same empty-list failure pattern. A separate issue covers it.
- Editing the issue title or body, PR #4619, or the test docstring that names menu 164. This record names the mismatch only.
- Changing the registry category, the `skip_reason` text, or the typed word.
- Changing mistapi, the README, the operator guide, or the live integration test.
- Live Mist calls in any test or verification step. The owner runs the read-only check that T-HEADER-CHECK describes.

## Dependencies

- Pinned `mistapi` version 0.64.1.
- `InputUtils.safe_input` for each keyboard read.
- The generators `scripts/generate_menu_wiki.py` and `scripts/menu_api_map.py`.

Warning: `tests/integration/test_wan_vpn_builder_live.py` calls the live Mist API and deletes VPNs. Do not run it for this change.

Caution: a create call after an unavailable read can add a VPN with the name of an existing VPN. The fix stops that path before the create call.
