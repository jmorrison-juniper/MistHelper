# Data Model: Browser Token and Safe Device Selection

## Startup credential state

| Field | Type | Rule |
| --- | --- | --- |
| `environment_token_at_boot` | Boolean | The portal reads this value once when the factory starts. |
| `browser_token_signin_allowed` | Boolean | The portal sets this to the inverse of `environment_token_at_boot`. |

The settings record stores no token value. The record names only whether a
token existed at startup.

## Browser credential session

| Field | Type | Rule |
| --- | --- | --- |
| `owner` | Owner record | The existing in-memory registry keys the session by this value. |
| `cloud_session` | Mist session object | The object holds the submitted token in process memory only. |
| `credential_mode` | Enum | The value identifies environment, provider, or browser-token sign-in. |
| `token_name` | Text | The portal derives this safe identity through `GetSelf`. |

The browser cookie carries no token name or token value. The run store, capture
store, lock store, response body, and log record carry no token value.

## Token owner identity

| Field | Type | Rule |
| --- | --- | --- |
| `identity_name` | Text | The portal derives this value from the token name for browser-token sessions. |
| `identity_digest` | Text | Logs use a one-way digest where existing records require a digest. |
| `browser_id` | Text | The portal uses this existing first-party cookie to separate browsers. |
| `display_name` | Text | The site lock shows a safe token name for a browser-token holder. |

Provider and environment-token behavior retains the existing email-based
identity. Browser-token behavior does not require an email address.

## Device-type selection

| Field | Type | Rule |
| --- | --- | --- |
| `selection_mode` | Text | The value is `all`, `selected`, or `single`. |
| `selected_types` | List of text | Each value is a supported type. |
| `available_types` | List of text | The portal derives this list from the full site inventory. |

The portal stores the selected types with the run options. The capture stores
the full site inventory and does not use this state.

## Safe target and mismatch

| Field | Type | Rule |
| --- | --- | --- |
| `version_before` | Text | The existing capture source supplies this value. Empty means unknown. |
| `version_target` | Text | The portal obtains a valid compatible override or highest compatible model version. |
| `version_mismatch` | Boolean | The portal sets this true only when both values are known and differ. |
| `target_source` | Text | The value identifies compatible override or model fallback. |

The portal does not mark an unknown running version as a mismatch.
