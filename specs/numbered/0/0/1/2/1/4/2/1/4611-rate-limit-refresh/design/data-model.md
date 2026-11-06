# Data Model: Preserve Rate-Limit State on HTTP Failure

## Usage Cache

The usage cache contains the last accepted quota reading.

| Field | Meaning | Failure behavior |
|-------|---------|------------------|
| `used` | Requests used in the current quota window | Preserve the prior value |
| `limit` | Request limit for the quota window | Preserve the prior value |
| `last_updated` | Time of the last accepted refresh | Preserve the prior value |
| `perceived_requests` | Local requests counted since refresh | Preserve the prior value |
| `initialized` | Whether the cache has accepted a reading | Preserve the prior value |

Other cache fields remain unchanged by the response-status check.

## Usage Response

The usage response contains SDK data and an underlying HTTP response.

| Value | Validation |
|-------|------------|
| HTTP status | Accept only values from 200 through 299 |
| Usage data | Read only after status validation |
| Missing HTTP response | Treat as a failed refresh |

## State Transition

```text
Valid cache + successful status + usable data -> refreshed cache
Valid cache + failed status or missing response -> unchanged cache
```
