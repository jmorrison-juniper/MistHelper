# Contract: Parameter request and response for menu 304

This contract covers the request that the browser sends for the parameters of menu 304, and the response fields that the browser reads. The menu 304 test waits on this request.

## Request

- Method and path: `GET /api/operations/parameters/304`. The browser sends the menu number as text.
- Server route: `web_portal/routes/operations.py` line 256, function `operation_parameters`. Blob `c7ef542129a0764a55ba18f2a1c9a2d6c5573754` on main.
- Browser sender: `web_portal/static/js/operations.js` line 282, function `loadParameters`. Blob `e92f687f958dcd108f1c0db30fa86511ec68b827` on main.

## Response on success

- HTTP status 200 with a JSON body.
- Fields read by the browser:
  - `error`: text. The browser shows it as a parameter error when present.
  - `category`: text. The value `cli_only` hides the form and shows the SSH-only message.
  - `cli_only_message`: text. Shown only when `category` is `cli_only`.
  - `parameters`: list. Each item becomes one control.
- Menu 304 returns one item for `serial_numbers`, a required text control. Source: `web_portal/services/operation.py` lines 400 and 401.
- The browser gives the control the id `param-serial_numbers`. The id comes from the prefix `param-` and the parameter name. Source: `web_portal/static/js/operations.js` line 741 (blob `e92f687f958dcd108f1c0db30fa86511ec68b827`).

## Response on failure

- When the executor returns `None` for the menu, the route returns HTTP 404 with the body `{"error": "Operation not found"}`. Source: `web_portal/routes/operations.py` lines 260 to 263.
- For the selected menu, the browser hides `#parameterLoading` after a response or an error. It shows the error text for an `error` field or a failed fetch.

## Use in the browser test

- `select_menu` requires HTTP 200 for the path of the selected menu (FR-002).
- For any other status, `select_menu` raises an `AssertionError` that names the status (FR-004).
- The helper does not parse the body beyond the wait. The serial number control check reads the rendered DOM.
