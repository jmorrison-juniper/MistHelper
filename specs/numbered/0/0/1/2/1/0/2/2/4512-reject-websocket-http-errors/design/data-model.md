# Discovery response model

Configuration contains tenant and service definitions. Statistics contains observed service names.
Both arrive in SDK response objects with `status_code` and `data`.

Only HTTP 200 authorizes payload extraction.
An invalid or missing status must fail before extraction.
Failed configuration leaves existing device caches unchanged.
Failed statistics leaves accepted configuration names unchanged.
Successful empty dictionaries preserve existing empty-discovery behavior.

No persisted schema changes.
