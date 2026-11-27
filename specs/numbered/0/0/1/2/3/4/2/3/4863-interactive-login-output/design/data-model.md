# Data Model: Interactive Login Output

This record has no database table and no stored entity. The model describes the three runtime entities that the change affects: the operator line, the login state, and the console level. The full line table is in `contracts/operator-output.md`. The SDK call contract is in `contracts/sdk-login.md`.

## Entity 1: Operator line

One fixed text line that MistHelper prints or logs during the interactive login.

| Field | Type | Rule |
|-------|------|------|
| `module` | text | The Python module that owns the line, such as `src.mist.access.auth.interactive.clouds`. |
| `function` | text | The method or function that writes the line. |
| `wording` | text | The exact text. A quoted string does not change. |
| `channel` | enumeration | One of `direct output`, `info record`, `warning record`, or `error record`. |
| `state` | reference | The login state from Entity 2 in which the line can appear. |

Natural key: `module`, `function`, and `wording`. No generated identifier is needed. A changed line keeps its key when only its channel changes.

Channel rules:

- A banner, menu, prompt context, spacer, success line, or result line uses `direct output`.
- A progress line uses `info record` and never `direct output`.
- A failure line or a validation line uses `warning record` or `error record`, and it keeps its current level.
- A cancel record uses `info record`, because the direct output already reported the cancel.

## Entity 2: Login state

One run of the interactive login, from the cloud menu to the MSP summary.

States: `cloud_chosen`, `credentials_read`, `login_sent`, `two_factor_required`, `code_read`, `code_sent`, `finalized`, `msp_announced`, and the end states `canceled` and `failed`.

| From | Event | To | Operator line channel | Log record |
|------|-------|----|-----------------------|------------|
| start | The operator chooses a cloud or presses Enter | `cloud_chosen` | Direct output: the selection line and one blank line | Info record: the cloud prompt start |
| start | The operator ends input at the cloud prompt | `canceled` | None | Info record: the cloud selection abort |
| `cloud_chosen` | The email and the password are read | `credentials_read` | None | Info records: the prompt starts |
| `cloud_chosen` | The email or the password is blank | `canceled` | None | Warning record: the validation line |
| `credentials_read` | The SDK reports a refused password | `failed` | Direct output: none. The failure line uses a warning record. | Error record: the login error |
| `credentials_read` | The SDK reports a 2FA requirement | `two_factor_required` | Direct output: the 2FA banner | Info record: the 2FA prompt start |
| `two_factor_required` | The operator ends input or types an empty code | `canceled` | None | Warning record for an empty code, info record for an end of input |
| `two_factor_required` | The operator types a code | `code_sent` | None | Info record: the resubmission |
| `code_sent` | Mist accepts the code | `finalized` | Direct output: the 2FA success line | Debug record: the 2FA result |
| `code_sent` | Mist refuses the code | `failed` | None on success. The failure line uses a warning record. | Error record: the 2FA failure |
| `credentials_read` | Mist accepts the password without 2FA | `finalized` | None | Debug record: the initial result |
| `finalized` | The session is stored | `msp_announced` | Direct output: the login success line and the MSP summary | Info records: the login success and the MSP callback |
| any | A connection, value, or generic error occurs | `failed` | None | Error record and a warning record for the failure line |

Each run ends in one end state. A run that reaches `msp_announced` does not return to an earlier state.

## Entity 3: Console level

Two values control the terminal output of log records and SDK lines.

| Value | Owner | Default | Effect |
|-------|-------|---------|--------|
| `CONSOLE_LOG_LEVEL` | The root console handler, set at startup | 20 when unset. The sample file sets 20. | The lowest level of log records that reach the terminal. |
| SDK console level | The mistapi module, set when an `APISession` is constructed | 20 in the SDK default | The lowest level of SDK console lines. The interactive login sets 30. |

Rules:

- The SDK console level is one process-wide value. The most recent `APISession` construction sets it.
- A token session that runs after the interactive login sets the level back to the SDK default of 20 when that session is constructed. The token path does not pass `console_log_level` (RC-69 gives the default, and a search of `src` and `MistHelper.py` finds no other argument).
- The direct output of `echo` ignores both values, because `echo` calls `print` directly (RC-27).

Caution: the SDK console level is process-wide. SDK info lines stay hidden after a login until another SDK session sets the level.

## Natural keys and uniqueness

No table uses these keys. The operator line key is unique within one module, because each wording appears once in one function.
