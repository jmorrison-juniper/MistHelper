# Research: Sign-in Credential Layout

## Decision

Keep the existing sign-in modes and routes. Place the browser-token label, field, and note in a separate group below the mode choices. Show and enable that group only when browser-token mode is selected.

## Rationale

The current template places the token controls inside a flex fieldset with the mode choices. The current browser script changes required fields but does not hide the unused token controls. The current stylesheet gives bold weight only to `.flash-item::before`, while the sign-in warning has no `flash-item` class.

The earlier local repair for issue #3295 used this same behavior at obsolete source paths. Current `main` still lacks it, so the repair remains necessary.

## Alternatives Considered

- Leave the token field visible but disabled. Rejected because the issue asks to hide or disable it, and a separate hidden group gives operators a clearer view.
- Clear the token value when another mode is selected. Rejected because the issue does not require value deletion and the field remains disabled and excluded from submission.
- Change the error-page markup. Rejected because the error page already uses the bold `flash-item` rule.

## Evidence

- `src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html` places the token label and field inside `.bubble-group`.
- `initBrowserTokenSignIn` in `portal.js` changes only the email and password `required` state.
- `portal.css` bolds `.flash-item::before`, but the sign-in alert uses `.flash-danger.alert`.
