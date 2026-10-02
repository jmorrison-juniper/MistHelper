# Presentation Contract: Sign-in credential layout

## Markup

The form contains its existing provider inputs, cloud picker, complete mode fieldset, token group, and submit button, in that order.
The group sits outside the flex fieldset.

| Element | Contract |
| --- | --- |
| Group | `div.signin-token-group`, `role="group"`, and group ID/test ID `signin-browser-token-group`. |
| Group name | `aria-labelledby="signin-browser-token-label"`. |
| Label | Exact text `Mist API token`, label ID/test ID `signin-browser-token-label`, and `for="signin-browser-token"`. |
| Input | Existing masked `signin-browser-token`, `name="token"`, no value attribute, and the existing note association. |
| Note | Existing text and `id="signin-browser-token-note"`. |
| Initial state | Group hidden and input disabled. |
| Startup gate | The complete group renders only under the existing browser-token gate. |

Keep all existing identifiers and native radio behavior.
Add no inline script, CSP exception, wrapper, or duplicate listener.

## Geometry

Measure the actual page at 1280x720 and 360x800.
Use `magenta` and `default` for four native acceptance cells.
Require one label, field, note, and semantic group, with finite positive rectangles.

- Left-edge difference: at most 1 CSS pixel.
- Label bottom: no lower than the field top.
- Vertical gap: 0 through 16 CSS pixels.
- Group top: no higher than the greatest mode-button bottom.

- Containment: each complete token rectangle lies inside the group.
- Width: the form and group have no horizontal overflow. The group lies inside the viewport.

The existing narrow service table has right edge `399.71875`, producing a document scroll width of `400`.
Preserve it and prove that all remaining page overflow belongs to `dependency-panel`.
Do not use an unrelated page-overflow exemption for the token group.

## Mode behavior

The existing callback updates the group and input on initialization and radio changes.
Outside browser-token mode, the callback hides and disables the token. Native `FormData` excludes that token.
Inside that mode, the token and note are visible. The token receives native keyboard focus.
Mode changes preserve all input values and the original provider-required baselines.

Reach the provider radio through actual Tab traversal.
Then require this native sequence:

| Key | Expected focus |
| --- | --- |
| ArrowRight | Browser-token radio |
| Tab | Token field |
| Tab | Sign in |
| Shift+Tab | Token field |
| Shift+Tab | Browser-token radio |
| ArrowLeft | Provider radio |
| Tab | Sign in |
| Shift+Tab | Provider radio |
| ArrowRight | Browser-token radio |
| Tab | Token field |

Ten complete mode cycles create zero requests and zero additional listeners.
One later submit creates exactly one JSON request with `mode`, `host`, and `token` only.
The existing CSRF header remains present. Clear the token before the request boundary.
Empty and whitespace-only client values create zero requests.

## Warning presentation

Reuse `.flash-item::before, .flash-danger.alert::before` for weight `700` and `white-space: nowrap`.
Keep standalone `.flash-danger::before` content exactly `"Warning: "`.
Compare service and sign-in alerts with a genuine 404 response that renders `error.html`.
Require one signal word, unchanged colors, and matching weight.
Keep hidden pseudo-elements suppressed and all other signal words unchanged.

## Refusal and privacy

Preserve these exact messages:

| Case | Message |
| --- | --- |
| Client empty token | `Type a Mist API token before you sign in.` |
| Refused token | `The portal could not sign you in. Check the token, then try again.` |
| Native empty token | `The token field is empty. Type your token, then try again.` |

Keep server behavior, native validation, JSON envelopes, statuses, session decisions, and destinations unchanged.
Use `textContent` and existing template escaping.
Require zero token occurrences in returned HTML, logs, cookies, session metadata, headers, URLs, and browser storage.
Retain screenshots only with synthetic or cleared fields.

## Collection and controls

The new browser module uses standard `pytest.importorskip`.
Its runtime support imports no conftest globals or runtime Playwright types.
Run installed-package cases through normal and strict full `tests/e2e/` collection.
Keep existing process-owner, trail, timeout, lifecycle, and strict guards unchanged.

Prove direct failures for alignment, overlap, excess gap, containment, empty measurements, zero area, overflow, inactive controls, and prefix styling.
Prove missing and foreign owner-header failures with the real `RunOwnerHeaderCheck`.
Use the actual shipped JavaScript in the offline Node probe.

Missing-package full-tree collection has an unrelated direct import in `test_map_title_contrast.py`.
Report that existing failure separately. Do not change it or claim a clean full-tree missing-package result.

## Supplemental assets

The four genuine main styles may supply eight separate compatibility measurements.
Require original-byte digests and status 200. Check the active stylesheet and its computed background value.
Do not count these as native themes or alter either catalog.
