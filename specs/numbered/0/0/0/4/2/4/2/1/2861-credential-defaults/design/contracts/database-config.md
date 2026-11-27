# Contract: DatabaseConfig credential fields

## Fields

- `arango_username`, `arango_password`, and `redis_password` default to an empty string.
- A non-empty credential value must not match a member of `_KNOWN_SAMPLE_CREDENTIALS`.
- `webhook_secret` keeps its empty default.

## Construction

- A direct construction with a sample value raises `ValueError`. The message names the field only.
- A direct construction without credentials succeeds in every mode.
- `from_env()` in non-standalone mode requires non-empty values through `_required_env`. This behavior stays unchanged.
- `from_env()` in standalone mode returns empty credentials. This behavior stays unchanged and tests cover it.

## Logs

A log line or an error message names the field only. No value appears in any message.
