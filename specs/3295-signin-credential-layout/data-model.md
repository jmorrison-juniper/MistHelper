# Data Model: Sign-in credential layout

## Existing browser state

| Value | Rule |
| --- | --- |
| Selected mode | Keep `provider_login`, `environment_token`, and `browser_token` unchanged. |
| Provider requirements | Read each original `required` attribute before synchronization. Restore it outside browser-token mode. |
| Token group | Hide it outside browser-token mode. Show it only inside that mode. |
| Token input | Disable it outside browser-token mode. Preserve its value until the existing submit path clears it. |
| Other inputs | Preserve email, password, and selected cloud on each mode change. |

## State transitions

| Condition | Group | Token | Provider requirements |
| --- | --- | --- | --- |
| Initial provider mode | Hidden | Disabled | Original attributes |
| Browser-token selection | Visible | Enabled | Existing relaxed state |
| Return to provider mode | Hidden | Disabled | Original attributes |
| Environment-token startup | Absent | Absent | Existing template baseline |
| Browser-token request | Visible | Enabled, value cleared | Existing relaxed state |

No transition creates a listener or request.
No transition introduces a new server mode or persistence rule.

## Safe evidence

Store rectangles, sample counts, focus identifiers, mode names, status codes, and listener counts.
Store asset digests and computed signal-word styles.
Store token-absence results and request counts, not token values or raw request bodies.
Require the existing process-owner header and server-written boundary evidence.

## Persistent state

No database, schema, primary key, session format, cache, cookie, or credential store changes.
