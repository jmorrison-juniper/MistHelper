# Site Lock Logging Contract

## Scope

This contract covers the take, beat, and release routes and the six refusal raises that issue #3506 found without a log record.

## Log record fields

Route refusal records include the site identifier, machine refusal code, and HTTP status as separate logging values. Lock-module refusal records include the machine code, site identifier or lock key, and safe owner digest where available.

The record does not include a lock token, an email address, a confirmation word, or raw personal data.

## Levels

- A confirmation request uses INFO because the portal asks the operator for a word.
- A lock contention or lost lock uses WARNING.
- A takeover audit refusal uses ERROR. Its existing error record remains.
- A lock-store failure keeps its existing warning record. The route may add the HTTP refusal record.
- A successful route action has an INFO record before the action and a DEBUG result record after it.

## Behavior

Logs do not change the lock decision, action order, exception, HTTP status, response body, or return value.
