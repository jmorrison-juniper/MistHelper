# Contract: Log records of the browser sign-in

Each record uses the standard logging module, with `%s` placeholders and the values listed here. Each record uses ASCII text only. A record never holds a password, a 2FA code, a token value, a raw email address, or the text of a Mist response.

## Records

| Level | Event | Template | Values allowed |
| - | - | - | - |
| info | Before the password step | `auth: browser sign-in step one for operator %s on cloud %s` | Email digest, host |
| debug | After the password step | `auth: browser sign-in step one answered with state %s` | State name |
| info | Before the 2FA step | `auth: browser second factor step for operator %s` | Email digest |
| debug | After the 2FA step | `auth: browser second factor answered with state %s` | State name |
| info | Before the profile read | `auth: reading the account profile for operator %s` | Email digest |
| debug | After the profile read | `auth: profile read with status %s and lifetime %s minutes` | Status number, lifetime number or the word unknown |
| info | Before the holder write | `auth: replacing the process session for operator %s` | Email digest |
| debug | After the holder write | `auth: process session replaced, organization count %s` | Count of organizations, which is 0 or 1 |
| info | Sign-out | `auth: process session ended by sign-out` | None |
| warning | Lifetime unknown | `auth: session_expiry is absent or outside 10 to 20160, so the portal sets no timer` | None |
| warning | Cloud outside the catalog | `auth: the request named a cloud outside the catalog, so the portal used the default` | None. The requested value is not logged. |
| error | SDK call fault | `auth: the cloud call failed (%s)` | Exception class name only |

## Rules

- Each SDK call has one info record before it and one debug record after it (FR-017).
- The exception record carries the class name only. The exception text may echo the input value, so it is never logged (`plan.md` risk table).
- The operator digest comes from `email_digest` in the capture identity module (D-13).
- The state names are `ok`, `two_factor`, `rate_limited`, `refused`, and `network_fault`.
- Redaction happens at the logging boundary (constitution Principle V). Callers do not format a secret into a message.

## Example sequence for an account with 2FA

```text
INFO auth: browser sign-in step one for operator 3f2a9c1b07d4 on cloud api.mist.com
DEBUG auth: browser sign-in step one answered with state two_factor
INFO auth: reading the account profile for operator 3f2a9c1b07d4
DEBUG auth: profile read with status 200 and lifetime 1440 minutes
INFO auth: browser second factor step for operator 3f2a9c1b07d4
DEBUG auth: browser second factor answered with state ok
INFO auth: replacing the process session for operator 3f2a9c1b07d4
DEBUG auth: process session replaced, organization count 1
```

The digest in the example is an illustrative value. The real digest comes from `email_digest` at run time.
