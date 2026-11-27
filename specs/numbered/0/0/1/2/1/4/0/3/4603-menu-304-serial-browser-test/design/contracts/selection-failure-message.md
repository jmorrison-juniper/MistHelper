# Contract: Failure message of the menu selection helper

This contract covers the `AssertionError` text that `select_menu` raises in `tests/e2e/web_portal/test_juniper_menus_browser.py` after task T003. TC-2 checks part of this text.

## Required content

Each item appears on its own line, in this order:

1. The menu number, written as `menu 304`.
2. The parameter path, written as `/api/operations/parameters/304`.
3. Exactly one of these outcomes:
   - The word `HTTP` followed by the status code, when a parameter response arrived. Example: `HTTP 503`.
   - `no parameter response` when the response wait ended without a response.
4. The text of `#selectedOpTitle`, in double quotes. Write `empty` when the element has no text.
5. The captured browser errors. List up to five entries, one per line, each prefixed with `page error:` or `console error:`. Write `no page errors` when the list is empty.

## Format

- Use ASCII characters only. Constitution principle V requires ASCII output.
- Start the message with the words `Menu selection failed:`.
- Keep each line at 200 characters or fewer. Cut longer error text at 200 characters.

## Example

```text
Menu selection failed: menu 304. Parameter path /api/operations/parameters/304. HTTP 503. Selected title "empty". Page errors: no page errors.
```

## Stability

- TC-2 asserts that the message contains `/api/operations/parameters/304` and `503`. A change to these words breaks TC-2, so update both together.
- The helper must not include secrets or Juniper payload text in the message. The browser errors come from the page, not from the Juniper gateway.
