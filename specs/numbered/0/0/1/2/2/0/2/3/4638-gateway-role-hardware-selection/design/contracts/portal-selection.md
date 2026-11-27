# Contract: Portal selection request and stable selectors

This contract defines the preview request for the converter and the controls on its page. It applies to `routes.py` and `presentation/converter.html`. It does not register a route on the shared portal.

## Preview request

Method and path: `POST /cisco-config-converter/preview`. The request is a multipart form. It needs the CSRF token from the page.

| Field | Type | Required | Rule | Failure |
| --- | --- | --- | --- | --- |
| `csrf_token` | string | Yes | Token from the page meta tag. | HTTP 400 from CSRF protection. |
| `file` | file | Yes | Existing upload rules from main: text suffix, 16 MiB maximum, UTF-8. | HTTP 400 with the existing message. |
| `name` | string | Yes | Existing rule: 1 to 120 visible characters. | HTTP 400 with the existing message. |
| `role` | string | Yes | One of `branch`, `hub`, or `standalone`. | HTTP 400: "Select a role: Branch, Hub, or Standalone." |
| `family` | string | Yes | One of `srx` or `ssr`. | HTTP 400: "Select a family: SRX or SSR." |
| `model` | string | Yes | 1 to 32 visible characters. The value need not be in the register. | HTTP 400: "Select a model with 1 to 32 visible characters." |
| `ports` | string | No | A JSON list of at most 16 assignment objects. An absent field means an empty list. | HTTP 400: "Submit ports as a JSON list of assignments." |
| `type` | string | Retired | Must be absent. | HTTP 400: "The type field is retired. Select a role: Branch, Hub, or Standalone." |

Each assignment object has exactly three keys:

| Key | Rule | Failure |
| --- | --- | --- |
| `mist_port` | Matches `^(ge\|xe)-[0-9]+/[0-9]+/[0-9]+$`. | HTTP 400: "Use a Mist port name such as ge-0/0/7." |
| `usage` | `wan` or `lan`. | HTTP 400: "Use the usage wan or lan." |
| `source_interface` | 1 to 64 characters. No whitespace and no control character. | HTTP 400: "Enter the Cisco interface name for each assigned port." |

A valid request returns HTTP 200 with the proposal in `proposal-json.md`. A blocked selection also returns HTTP 200. The page shows each blocker. Only input format errors return HTTP 400.

Each preview request removes the earlier review. The new digest replaces the earlier digest. This behavior already exists on main in `routes.py`, lines 76 and 77.

## Stable selectors

Each selector below is a `data-testid` value on the element named. Native `select`, `input`, and `button` elements provide keyboard support. Each control has a visible `label` with a `for` attribute.

| `data-testid` | Element | Label text | Option or behavior |
| --- | --- | --- | --- |
| `cisco-converter` | `section` | Not applicable | Existing root. |
| `cisco-upload` | `form` | Not applicable | Existing upload form. |
| `cisco-file` | `input type=file` | Configuration file | Existing. |
| `cisco-name` | `input` | Template name | Existing. |
| `cisco-role` | `select` | Role | Empty option, then Branch (`branch`), Hub (`hub`), Standalone (`standalone`). |
| `cisco-family` | `select` | Family | Empty option, then SRX (`srx`), SSR (`ssr`). |
| `cisco-model` | `select` | Model | Empty option, then the register models of the selected family. Filled by `converter.js`. |
| `cisco-port-usage` | `select` | Usage for the port name | Unassigned (empty value), then WAN (`wan`) or LAN (`lan`) only. One select for each port row. Carries `data-port`. |
| `cisco-source-interface` | `input type=text` | Cisco interface for the port name | Text, maximum 64 characters. One input for each port row. Carries `data-port`. |
| `cisco-ports` | `input type=hidden` | Not applicable | Holds the `ports` JSON that `converter.js` builds. |
| `cisco-register` | `script type=application/json` | Not applicable | Holds the register data from `hardware-register.md`. |
| `cisco-preview` | `button` | Not applicable | Existing preview button. |
| `cisco-status` | `p role=status` | Not applicable | Existing live status region. |
| `cisco-proposal` | `pre` | Not applicable | Existing proposal text. |
| `cisco-review` | `button` | Not applicable | Existing review button. |
| `cisco-export` | `button` | Not applicable | Existing export button. |

The retired selector `cisco-type` is removed. No page element uses `innerHTML` for proposal or register text.

## Register data block

The page embeds the register from `HardwareRegister.options()` in the `cisco-register` script block. The block uses Jinja `tojson`. A test reads the block and checks the revision value and the model names.
