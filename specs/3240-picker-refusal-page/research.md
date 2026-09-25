# Research: Show a picker refusal inside the picker page

**Issue**: #3240

## Decision 1: Answer a browser refusal with a 303 redirect and one flashed sentence

The route stores the refusal sentence with `flask.flash`, and it answers a 303
redirect to the picker page. The picker page then renders the sentence in the
shared message region.

### Rationale

- The success path of each picker already answers a 303 redirect through
  `next_page_answer`. The refusal path then uses the same pattern, and the
  browser history holds only GET entries.
- A page that a POST renders stays in the history as a POST entry. A reload of
  that page, or a back step to it, makes the browser ask the operator to send
  the form again.
- The layout includes `partials/flash.html` on every page. The comment of that
  partial states that "the server reports one through a page reload". No route
  called `flash` before this change, so the region waited for this use.
- The GET page builds its content from the stored state only. A refusal
  changes no stored state, so the page shows the choice that the server holds
  (FR-004).

### Alternatives

- **Render the picker page with the status 400.** The POST route must then
  build the full context of each GET page. `sites_page` reads the site rows,
  the filter, the mode, and the stored site set. A second copy of that context
  can drift from the first copy. The page also stays a POST entry in the
  history. Rejected.
- **Render the shared error page of issue #3276.** `error_page` shows the
  cause and a link back. The operator must then click the link to see the form
  again. A missing choice is a condition that the operator corrects in the same
  form, so the form must show the sentence. Rejected.
- **Stop an empty choice in `portal.js`.** A script check can disable Continue
  until the operator selects a site. The server is still the authority, and a
  second tab or a stale page reaches the server with a refused choice anyway.
  The server path must be correct first. Out of scope for this issue.

## Decision 2: Use the level `warning`

The flashed sentence uses the level `warning`. `portal.css` prints the prefix
"Caution: " for that level.

### Rationale

- STE uses "Caution" for a recoverable condition. The operator corrects the
  choice and continues, so the condition is recoverable.
- The level `danger` prints "Warning: ". STE keeps "Warning" for harm, for data
  loss, or for an irreversible action. A missing choice is none of these.

## Decision 3: Read the sentence from the envelope

The class `PickerRefusal` takes the refusal envelope that the route built. It
reads the sentence out of that envelope for the browser path.

### Rationale

- The organization refusal comes from `identity.org_scope_refusal`, and that
  function returns a built envelope. One entry point that takes an envelope
  serves every refusal of the three pickers.
- The page and the envelope then hold the same sentence for one cause
  (FR-006). No second table of sentences exists.
- If the envelope holds no readable sentence, the class shows one fixed
  sentence. The operator still sees the picker page and not a raw body.

## Decision 4: Send each refusal to the page that corrects it

| Route | Refusal code | Status | Redirect target |
| - | - | - | - |
| `choose_org` | `org_not_chosen` | 400 | `/select/org` |
| `choose_org` | `org_not_permitted` | 403 | `/select/org` |
| `choose_mode` | `org_not_chosen` | 400 | `/select/org` |
| `choose_mode` | `mode_not_chosen` | 400 | `/select/mode` |
| `choose_sites` | `org_not_chosen` | 400 | `/select/org` |
| `choose_sites` | `mode_not_chosen` | 400 | `/select/mode` |
| `choose_sites` | `sites_not_chosen` | 400 | `/select/site` |
| `choose_sites` | `site_not_found` | 404 | `/select/site` |

A script and a JSON client read the same code and the same status as before.

## Fact checks

- `wants_browser_page` in `factory.py` answers True only when the `Accept`
  header prefers `text/html` and no `X-Requested-With: XMLHttpRequest` header
  marks a script. A request with no `Accept` header reads JSON.
- Flask keeps the flashed sentence in the signed session cookie. The next page
  that calls `get_flashed_messages` removes it, so the sentence shows one time.
- Each of the three picker templates extends `layout.html`, and `layout.html`
  includes `partials/flash.html`.
- Every form whose action starts with `/api/org-upgrades` sends its request
  from `portal.js`, and the script shows a refusal inside the page. The sign-in
  forms render the form again already. The three picker forms are the only
  plain form posts that answered a raw JSON page.
