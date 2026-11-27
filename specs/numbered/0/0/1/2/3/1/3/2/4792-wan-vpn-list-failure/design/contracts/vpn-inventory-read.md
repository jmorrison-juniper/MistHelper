# Contract: VpnInventoryReader

This contract defines the internal interface between `WanVpnBuilder` and the new module `src/operations/wan/vpn_inventory.py`. It also defines the SDK calls and the log lines.

## Interface

- Module: `src/operations/wan/vpn_inventory.py`.
- Class: `VpnInventoryReader`, a dataclass with two fields.
- Field `apisession`: the mistapi session that the menu passes to `WanVpnBuilder`.
- Field `org_id`: the organization identifier that the menu selects.
- Public method: `read(self) -> list[Any] | None`.
- Private methods: `_collect_pages`, `_validated_page`, `_page_numbers`, and `_follow_next`. The class has five methods in total.

## Output

- A list of VPN records (objects) when the inventory is verified. Each record has a nonblank string `name`.
- An empty list when the first page is a verified read with zero records and total 0.
- None when the inventory is unavailable. The reader writes an error line before it returns None.

The reader never returns a partial list. A caller must treat None as an unavailable inventory.

## SDK Calls

| Call | Source | Arguments | Use |
|------|--------|-----------|-----|
| `mistapi.api.v1.orgs.vpns.listOrgVpns` | `.venv\Lib\site-packages\mistapi\api\v1\orgs\vpns.py` line 17 (RC-53) | `self.apisession` and `self.org_id`, passed by position | The first page. The call passes no `limit` and no `page`. |
| `mistapi.get_next` | `.venv\Lib\site-packages\mistapi\__pagination.py` line 17 (RC-55) and `mistapi/__init__.py` line 16 (RC-60) | `self.apisession` and the previous response, passed by position | Each later page after the reader validates the next link. |

The reader never calls `mistapi.get_all` (FR-011). The reader never sends a direct HTTP request.

## Page Rules

| Rule | Check | Failure result |
|------|-------|----------------|
| R1 | The status code is an integer from 200 through 299. | Unavailable, reason `status`. |
| R2 | The data is a list. | Unavailable, reason `payload`. |
| R3 | Each record is an object with a nonblank string `name`. | Unavailable, reason `record`. |
| R4 | The headers `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` are integers. The limit and the page are 1 or more. The total is 0 or more. | Unavailable, reason `headers`. |
| R5 | The limit and the total equal the first page values. The page does not exceed the declared page count. | Unavailable, reason `position`. |
| R6 | A page without a next link satisfies limit times page is at least total. | Unavailable, reason `position`. |
| R7 | A page with a next link satisfies limit times page is less than total. | Unavailable, reason `position`. |
| R8 | A next link is a nonblank text value that has not been followed. | Unavailable, reason `link`. |
| R9 | `mistapi.get_next` returns a response for the next link. | Unavailable, reason `request`. |
| R10 | `listOrgVpns` returns without an exception. | Unavailable, reason `request`. |

## Log Lines

Each message template uses `%s` values. Each message uses ASCII characters. No message holds a token.

| Level | Template | When |
|-------|----------|------|
| info | `Reading organization VPN inventory for %s` | Before the call to `listOrgVpns`. |
| debug | `Received organization VPN page with status %s` | After each first or later page response. |
| info | `Requesting organization VPN page %d of %d` | Before each call to `mistapi.get_next`. The first value is the requested page. The second value is the declared page count. |
| debug | `Received the next organization VPN page` | After each call to `mistapi.get_next`. |
| debug | `Verified %d organization VPN records` | When the reader returns a verified inventory. |
| error | `Failed to read organization VPNs after %s` | When the call to `listOrgVpns` or `mistapi.get_next` raises. The value is the exception type name. |
| error | `Organization VPN inventory is unavailable for reason %s` | When any page rule fails. The value is the reason code from the page rules table. |

## Ownership

The reader owns the page rules, the list calls, the next-page calls, and the reader log lines. The builder owns the operator messages, the stop point, and the names. The builder does not parse headers or pages.
