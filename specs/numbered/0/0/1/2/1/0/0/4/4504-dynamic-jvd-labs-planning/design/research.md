# Research: Dynamic JVD Labs

**Baseline**: Issue #4504 and `jmorrison-juniper/vmm-topology-automation#19` (research date 2026-10-26). Both repositories need a refresh in task T001. This planning session contacted no VMM, Mist, or guest service.

## Decisions

| Topic | Decision | Alternative rejected |
| - | - | - |
| Catalog | Versioned catalog, YAML and JSON import, parameter forms, supported-block composition | Free-form scripts. The issue excludes executable templates. |
| Engine | `vmm_topology` through a pinned Git submodule, runtime package only | Source copy or history merge. |
| Frontend | Existing Flask portal and Jinja pages | React rewrite. The issue excludes it. |
| Persistence | Host ArangoDB repositories with transactions | SQLite journal, Redis authority, generic ingestion router that can degrade to CSV only. |
| Access | Existing allowlist, trusted proxy, CSRF, and sessions | New login or role system. |
| Jobs | Durable feature-specific job runner modeled on the firmware policy jobs | Process-local Operations executor. |
| Mist transport | Host `mistapi` session injected into the engine | Engine `urllib` client. |

## Known Gaps (engine)

- The compiler implements only the fixed dual-hub topology.
- Preview grants no approval, reservation, or capacity proof.
- Full-scenario apply, onboarding, convergence, and recovery are not implemented.
- No impairment control, verified restoration, or complete cleanup exists.
- Live run locks require POSIX.

## Known Gaps (host)

- The generic Operations registry is process-local and unsuitable for lab mutations.
- The image-producing reusable workflow omits submodule checkout.
- `PORTAL_SECRET_KEY` is optional, so cookies and private proofs reset at restart without it.
