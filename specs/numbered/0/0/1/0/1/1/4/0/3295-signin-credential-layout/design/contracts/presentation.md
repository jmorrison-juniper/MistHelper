# Presentation Contract: Sign-in Credential Layout

## Sign-in Page

- The browser-token mode keeps its existing radio identifier.
- The token group carries `data-testid="signin-browser-token-group"`.
- The token label carries `data-testid="signin-browser-token-label"`.
- The token field keeps its existing identifier and description.
- The token group is hidden and its field is disabled when browser-token mode is not selected.
- The label appears above and aligns with the token field when the group is active.
- Keyboard selection of browser-token mode enables the field and lets the next Tab focus it.

## Warning Prefix

- The sign-in alert and the error-page alert both show the “Warning:” prefix in bold weight.

## Server Behavior

- The contract adds no route, request, response, credential decision, or persistent state.
