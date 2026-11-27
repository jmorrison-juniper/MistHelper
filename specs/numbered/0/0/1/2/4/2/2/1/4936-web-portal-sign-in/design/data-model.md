# Data Model: Browser sign-in with 2FA for the web portal

The feature stores no database row and no file. Each entity lives in process memory. Each entity has a natural key, its attributes, an owner, and a lifetime. No entity holds a password, a 2FA code, a token value, or a raw email address.

## Entities

| Entity | Natural key | Attributes | Owner | Lifetime |
| - | - | - | - | - |
| PendingSignIn | Browser identifier from the `misthelper_browser` cookie | Email digest, host, start time on the monotonic clock, SDK session object | `PendingSignInStore` in `state/pending.py` | 300 seconds from the password step, or until replaced, completed, or dropped. The store holds at most 64 records. |
| ProcessSession | One slot for each web portal process | Email digest, host, organization identifier, start time, expiry time or none, SDK session object | `ProcessSessionHolder` in `state/holder.py` | Until sign-out, replacement, or the end of the session lifetime |
| SessionLifetime | The process session | Minutes from `session_expiry`, or the state unknown | `SessionLifetime` in `state/lifetime.py` | Read once for each accepted sign-in |
| CloudChoice | Host value of the catalog entry | Label and host | `CloudCatalog` in `cloud/catalog.py`, reading `MIST_CLOUDS` | Static |
| LoginOutcome | None, returned for each SDK call | State, SDK session or none | `LoginClassifier` in `state/outcome.py` | One call |
| SignInMessage | Failure code | One sentence | `state/outcome.py` | Static |
| OperatorDigest | Normalized email address, through `email_digest` | Digest value only | `identity.py` of the capture portal (D-13) | Derived for each record |

## Field rules

- The browser identifier is a random token of 32 bytes. It is not derived from the email address.
- `PendingSignIn` keeps the SDK session object by reference. The object holds the transport state of the first call. The record holds no password and no code (FR-004).
- `ProcessSession` holds the SDK session object. The organization identifier comes from `MIST_ORG_ID`, or from the first organization privilege of `getSelf` (FR-018).
- `SessionLifetime` accepts whole numbers from 10 through 20160 only. Any other value gives the unknown state (FR-009).
- `LoginOutcome` names the state. It never holds the text of a Mist response.

## State transitions

### PendingSignIn

| From | Event | To |
| - | - | - |
| None | The password step answers that a 2FA code is required | Open |
| Open | A correct 2FA code arrives within 300 seconds | Completed. The process session is set, and the record is dropped. |
| Open | A wrong 2FA code arrives | Open. The record stays until its window ends (FR-012). |
| Open | The window ends | Expired. The next read drops the record. |
| Open | The same browser starts a new password step | Replaced by the new record |
| Open | The browser submits sign-out | Dropped |
| Any | The password step fails or the network fails | None. The previous record for that browser is dropped. |

### ProcessSession

| From | Event | To |
| - | - | - |
| Absent | A sign-in completes | Active |
| Active | Another sign-in completes | Active, with the new account. The old session object is dropped. |
| Active | Sign-out is submitted and no operation runs | Absent |
| Active | Sign-out or a sign-in is submitted while an operation runs | Active. The request is refused with the `run_active` sentence (D-17). |
| Active | The lifetime ends | Absent. The `before_app_request` hook drops the session. |
| Active | The lifetime is unknown | Active until Mist refuses a request |

A refused password step or a refused 2FA code leaves the process session unchanged. A second browser cannot end the session of the first browser, except through sign-out, and a sign-out replaces the whole process session.

## Identifiers in logs

Log records name an operator by the email digest only (FR-017). Log records name a cloud by its host. Log records never name a password, a code, a token, or a raw email address.
