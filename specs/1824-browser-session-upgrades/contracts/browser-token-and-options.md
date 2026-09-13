# Browser Token and Options Contract

## Sign-in page

When no environment token existed at startup, the sign-in page provides a
browser-token field. The form submits the token only to `POST /auth/signin`.
The rendered page, page context, and failure response do not contain its value.

The portal calls `GetSelf` after the Mist session logs in. The portal accepts
the sign-in only when the response contains a safe nonempty token name.

When `MIST_APITOKEN` or `MIST_API_TOKEN` existed at startup, the browser-token
field is absent. Existing environment-token and provider-login choices remain
available as they are today.

## Upgrade options

The upgrade options page presents checkboxes for access point, switch, and
gateway. The operator can select all supported types, a selected group, or one
type. The request carries the selected types with the saved options.

The portal rejects a request that includes an unsupported type, duplicate type,
or target from an unselected type. It performs the existing model availability
validation before it writes the options record.

## Target view

The target table shows rows for selected types only. Each row displays the
running version, safe target version, and mismatch state. The capture view
continues to show the complete site capture.

## Safety boundary

The options contract prepares targets only. It does not call the path that
requires `CONFIRM` and starts a firmware upgrade.
