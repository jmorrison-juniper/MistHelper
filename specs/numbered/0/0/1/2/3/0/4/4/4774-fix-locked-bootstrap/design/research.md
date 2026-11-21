# Research: Locked Bootstrap Sources

## Evidence

An isolated local server supplied two synthetic indexes with the same package.
The lock used the first index. A locked dry-run sync used each test setting.

| UV version | Primary changed | Extra added | Primary unchanged |
| - | - | - | - |
| 0.12.23 | Stale lock | Pass | Pass |
| 0.13.7 | Stale lock | Pass | Pass |
| 0.13.8 | Stale lock | Pass | Pass |

The first condition changes `UV_INDEX_URL`.
The second condition adds `UV_EXTRA_INDEX_URL` while retaining the locked primary.
The test did not contact a private mirror.

An actual locked install with UV 0.13.8 and an empty cache used the locked primary.
It did not request the package from the extra index.
The synthetic probe is retained in the session files as `locked_source_probe.py`.

## Decision

Do not change the lock or use an unlocked sync.
Do not assume that an extra index preserves a primary source policy.
Establish a safe source-policy contract before implementation.

## Alternatives

- Ignore the pip primary and use the locked source. This can bypass the configured policy.
- Map the primary to an extra index. The test retrieved the artifact from the locked primary.
- Update the lock for each mirror. This changes a shared dependency record for one host.
- Use a frozen sync. This skips the required lock consistency check.
