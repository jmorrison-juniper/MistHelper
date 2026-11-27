# UI Checklist: Stable selectors and keyboard operation

This checklist covers the controls in `contracts/portal-selection.md`, section Stable selectors. It covers the page that `converter.html` renders and the script that `converter.js` runs.

## Stable Selectors

- [ ] The page has one `data-testid` value for each control in the table of stable selectors.
- [ ] Each dynamic port row carries a `data-port` attribute that names the Mist port.
- [ ] The retired `cisco-type` selector is absent from the page.
- [ ] The register data block carries the `cisco-register` value and holds valid JSON.

## Keyboard Operation

- [ ] Each control is a native `select`, `input`, or `button`. No element uses a `div` with a click handler for a choice.
- [ ] Tab order follows the visible order: role, family, model, each port row, preview, review, and export.
- [ ] The role, family, and model selects carry the `required` attribute.
- [ ] Changing a selection calls the reset on the `input` and `change` events.

## Labels and Status

- [ ] Each control has a visible label with a `for` attribute.
- [ ] Each port label names the port, for example "Usage for ge-0/0/7".
- [ ] The status region keeps `role="status"` and `aria-live="polite"`.
- [ ] Blocker messages appear as text in the proposal. Color adds no meaning to a blocker.

## Safety of Rendered Text

- [ ] The script writes proposal text with `textContent`, not `innerHTML`.
- [ ] The register data block uses the Jinja `tojson` filter.
- [ ] The page sends the CSRF header on review and export requests, as it does on main.
