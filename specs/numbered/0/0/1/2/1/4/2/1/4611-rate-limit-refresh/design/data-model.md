# Data Model: Preserve API Usage After Failed Refresh

**Feature**: [spec.md](../spec.md)

## Usage Cache

The rate limiter keeps the last accepted Mist usage state in an in-memory mapping.

| Field | Meaning | Failure behavior |
|---|---|---|
| `used` | Accepted request count | Preserve the prior value |
| `limit` | Accepted request limit | Preserve the prior value |
| `last_updated` | Time of the last accepted refresh | Preserve the prior value |
| `perceived_requests` | Locally tracked requests since refresh | Preserve the prior value |
| `initialized` | Whether the cache has accepted usage data | Preserve the prior value |

## Refresh Transition

| Input result | Cache transition |
|---|---|
| Successful HTTP status with usage data | Apply the existing update rules |
| Unsuccessful HTTP status | Do not change any field |
| Raised refresh exception | Do not change any field |

The feature adds no stored fields or persistent data.
