# Implementation Plan: Stop VPN Creation When the VPN Inventory Is Unverified

**Branch**: `fix/4792-wan-vpn-list-failure` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Add a reader class that proves a complete VPN inventory before the builder offers a VPN name. The reader returns an unavailable result for each failed or unverifiable read. The builder stops before the name prompt in that case. The change keeps the mistapi list and create calls and the typed word `CREATE`. Pagination uses `mistapi.get_next` with header checks instead of `mistapi.get_all`.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `.github/copilot-instructions.md` requires.

**Primary Dependencies**: `mistapi` 0.64.1. `requirements.txt` line 129 pins `mistapi==0.64.1`. `pyproject.toml` line 29 requires `mistapi>=0.64.1,<0.65`. No new dependency.

**Storage**: Not applicable. The change writes no file and changes no database.

**Testing**: pytest in the existing unit module, with mocked native responses. Each mock wraps a `requests.Response` in a mistapi `APIResponse`.

**Target Platform**: Windows 11, macOS, and Linux, as `.github/copilot-instructions.md` states.

**Project Type**: Menu operation in an existing Python command-line repository.

**Performance Goals**: The change adds one `mistapi.get_next` request for each later page that the first page declares. It adds no request when the first page proves completeness.

**Constraints**: Tests use mocks only. Each function has at most five parameters, five logical blocks, five operations for each block, and 25 lines. Each executable line has an inline comment. Log lines use ASCII only.

**Scale/Scope**: One organization read for each run of menu 147.

## Constitution Check

Gate result before research: pass. Gate result after design: pass.

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule | Pass | The new module adds one child to `src/operations/wan/`, which moves from 4 to 5 children (RC-34). The reader has five methods. `WanVpnBuilder` gains no method (FR-016). The existing debt in `changelog.d/` and `specs/` is in Complexity Tracking. |
| II. Class-based architecture | Pass | The new logic lives in one named class. The change adds no standalone wrapper function. |
| III. Safety first | Pass | The typed word `CREATE` and `safe_input` stay unchanged (FR-015). The stop happens before every prompt. No secret enters a log line. |
| IV. Full deployment pipeline | Pass (planned) | `tasks.md` runs the local gates, the pull request, the CI check, and the merge gate in order. No task pushes to `main`. |
| V. Observability and logging | Pass (planned) | Each new message uses ASCII. Each log call uses `%s` values. No token enters a log line. |
| VI. Inline comments | Pass (planned) | Each executable line in the new module and in each changed builder line has an inline comment. T-LOCAL-GATES includes a line audit. |
| VII. Action logging | Pass (planned) | Each list request and each next-page request has an info line before it and a debug line after it. An exception writes an error line with the exception type. |
| Mist Cloud transport | Pass | The change calls only mistapi methods (FR-014). SDK insufficiency is not applicable because the change owns no transport. |
| Output backends | Not applicable | The change exports no data. |
| Operational store | Not applicable | The change adds no coordination record. |
| Database keys | Not applicable | The change adds no endpoint and no stored key. |
| Data directory | Not applicable | The change writes no product output. |
| Container runtime | Not applicable | Unit tests run without a container. The Podman section of `documentation/container-deployment.md` is not used. |
| File paths | Pass | The new module builds no path. |
| Security findings | Pass | The change adds no suppression. The existing `# nosec B105` comments on `CANCEL_TOKEN` and `CONFIRM_TOKEN` stay in place. |
| Menu operations | Not applicable | The change adds no menu and changes no registry category (FR-018). |
| Documentation | Pass | One changelog fragment is added. The README stays unchanged, because the operation count and the menu table do not change. Generated menu pages are regenerated where the call path changes. |
| Specifications | Pass | The record lives under `specs/numbered/`, a managed root. It adds no direct child to `specs/`. |

## Architecture

```text
Menu 147 -> WanVpnBuilder.execute -> run()
  -> _prompt_name_after_display()                      (modified: stops on None)
       -> _fetch_existing_vpns()                       (modified: returns None when unverified)
            -> VpnInventoryReader.read()               (new module)
                 -> mistapi.api.v1.orgs.vpns.listOrgVpns   (SDK call, unchanged)
                 -> mistapi.get_next                       (SDK call for later pages)
       -> list: strip names, display, name prompt      (unchanged flow)
  -> _display_preview(): typed CREATE                 (unchanged)
  -> _create_vpn() -> mistapi.api.v1.orgs.vpns.createOrgVpn   (SDK call, unchanged)
```

## Reader Design

The class `VpnInventoryReader` is a dataclass with two fields: `apisession` and `org_id`. The module defines one logger and one class. The class has five methods.

| Method | Kind | Responsibility |
|--------|------|----------------|
| `read` | Public entry | Write the info line. Call `listOrgVpns` with explicit arguments. Return None after an exception. Collect the pages. Write the debug line with the record count. |
| `_collect_pages` | Loop | Validate each page. Apply the position rules. Return the records after the last page, or follow the next link. |
| `_validated_page` | Static | Accept a 200 through 299 status, a list of data, and a nonblank string `name` on each record (FR-002 to FR-004). |
| `_page_numbers` | Static | Parse the three pagination headers as integers and check their minimums (FR-005). |
| `_follow_next` | Instance | Check that the next link is nonblank and new. Write the info line. Call `mistapi.get_next(self.apisession, response)`. Write the debug line (FR-007, FR-009, FR-017). |

Position rules that `_collect_pages` applies (FR-006 to FR-008):

- The first page sets the limit, the total, and the declared page count. The declared page count is the total divided by the limit, rounded up, with a minimum of 1.
- Each later page must keep the same limit and the same total.
- A page number above the declared page count makes the inventory unavailable.
- A page without a next link must satisfy limit times page is at least the total.
- A page with a next link must satisfy limit times page is less than the total. Then `_follow_next` runs.

The builder change is small. `_fetch_existing_vpns` returns None when the reader returns None. It writes the existing message from line 404 of `wan_vpn_builder.py` in that case. `_prompt_name_after_display` returns None before any display or prompt when the inventory is None. It writes one stop line in that case. Names from a verified inventory are stripped before the duplicate check.

## File-by-File Change Map

| Path | Action | Purpose |
|------|--------|---------|
| `src/operations/wan/vpn_inventory.py` | Add | Class `VpnInventoryReader` with the verified read and the page rules. |
| `src/operations/wan/wan_vpn_builder.py` | Modify | Import the reader. `_fetch_existing_vpns` (lines 390 to 406) returns None when the inventory is unavailable. `_prompt_name_after_display` (lines 132 to 140) stops on None and strips names. |
| `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` | Modify | Replace the defect-encoding case at lines 322 to 333. Add 15 test functions with 25 cases in place of them. Keep every other test unchanged. |
| `changelog.d/issue-4792-wan-vpn-list-failure.md` | Add | One release-note fragment with the `Fixed` heading. |
| `documentation/menu-api/interactive.md` | Modify when regenerated | The call-site row for `listOrgVpns` moves from the builder method to the reader. |
| `documentation/wiki/Menu-API-Endpoints-Interactive.md` | Modify when regenerated | The same call-site row in the wiki page. |
| `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/` | Add | This record. It holds the spec, the plan, the tasks, the analysis, the design folder, the contracts, and the checklists. |

No other file changes. `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `README.md`, `documentation/operator-guide.md`, and the live integration test stay unchanged.

## Dependencies

No dependency is added or changed. The pinned `mistapi` version is 0.64.1. The mistapi functions used are `mistapi.api.v1.orgs.vpns.listOrgVpns`, `mistapi.api.v1.orgs.vpns.createOrgVpn`, and `mistapi.get_next`. The research file lists their source lines.

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| Mist omits a pagination header on a complete page | Every run stops with an unavailable inventory. Creation is blocked, and no VPN is created by mistake. | T-HEADER-CHECK runs before merge. The owner reverts the change if the check shows that Mist omits the headers. |
| `symbol-diff` lists the new import as a changed module-level name | The local gate reports a difference | The import adds one name and removes none. The pull request states this reason. |
| The regenerated menu pages change more lines than this change | The menu reference gate reports drift | Commit the exact generator output. Run the generator a second time and confirm that it changes no file. |
| The hub group manager has the same defect | Menu 146 can still treat a failed read as empty | A separate issue covers it. This change does not change menu 146. |
| A reviewer merges the diverged branch of commit `8d8f1a63c` | The fix is incomplete on `main` | The pull request states that it supersedes the diverged branch. |
| The stop line says "could not be verified" for malformed data | The operator may check the network first | The error line keeps the existing connectivity hint. The stop line says that no VPN was created. |
| Full test shards include the live test | A local run can delete VPNs in a live organization | Local runs skip the shards. CI runs them, as decision D-18 records. |

## Rollback Steps

1. Create a branch `revert/4792-wan-vpn-list-failure` from `main`.
2. Revert the squash commit of this change on that branch. The revert removes `src/operations/wan/vpn_inventory.py` and restores the lines in `wan_vpn_builder.py`.
3. Run `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Commit the regenerated pages only when they change.
4. Run `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py -q`. The module must pass on the reverted code.
5. Open the revert pull request with the `needs-human-review` label. Do not add the `auto-merge` label.

## Project Structure

```text
specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      vpn-inventory-read.md
      menu-147-console.md
    checklists/
      requirements.md
      safety.md
```

## Contracts

A contract applies. The reader is an internal interface, and the menu prints operator lines. Two contract files hold the details: `design/contracts/vpn-inventory-read.md` and `design/contracts/menu-147-console.md`.

## Complexity Tracking

The table lists existing debt that this change touches or keeps. The change adds no new debt in a parent that is already over its limit.

| Item | Kind | Why it stays | Remediation |
|------|------|--------------|-------------|
| `WanVpnBuilder` defines more than five methods (RC-70) | Grandfathered violation | The change adds no method to the class. The new logic lives in the new class. | A separate issue splits the builder class. |
| `changelog.d/` holds 335 direct children (RC-37) | Established process folder | The constitution allows one unique record for each change. This change adds one fragment. | A separate issue reviews the layout of the changelog folder. |
| `specs/` holds 795 direct children (RC-45) | Established process folder | The record lives under the managed root `specs/numbered/`. It adds no direct child to `specs/`. | A separate issue reviews the layout of the specs folder. |
| `src/operations/` holds five direct children (RC-35) | At its limit | The change adds no child to `src/operations/`. | None in this change. |
