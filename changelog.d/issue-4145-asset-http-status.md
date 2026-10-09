### Juniper asset serial lookup refuses HTTP errors

- **Fixed**: The Juniper asset serial lookup refuses an HTTP 4xx or 5xx reply, even when the body status says 200. Such a reply gives no serial data. Issue #4145.
