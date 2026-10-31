# Portal Contract

The Labs blueprint registers in the existing Flask app. Each route uses the current allowlist, trusted-proxy handling, CSRF protection, and session. The portal adds no login.

| Route (proposed) | Method | Purpose |
| - | - | - |
| `/labs` | GET | Labs page |
| `/labs/api/catalog` | GET | Template list with compatibility |
| `/labs/api/templates/import` | POST | Import and validate a file |
| `/labs/api/preview` | POST | Validate and plan. No authority. |
| `/labs/api/drafts` | GET, POST | List and save drafts |
| `/labs/api/qualify` | POST | Read-only qualification |
| `/labs/api/proposals` | POST | Create an approval proposal |
| `/labs/api/proposals/<id>/approve` | POST | Typed approval |
| `/labs/api/jobs` | POST | Start a durable job from an approval |
| `/labs/api/jobs/<id>` | GET | Sanitized status |
| `/labs/api/jobs/<id>/events` | GET | SSE with polling fallback |
| `/labs/api/runs/<id>/monitor` | GET | Bounded monitoring read model |

Rules:

1. GET routes only read. Each POST needs CSRF.
2. A mutation returns a job identifier. It never blocks until completion.
3. A foreign private proposal or job returns the same 404 as a missing one.
4. Errors use the engine categories with a sanitized message.
5. Lab mutations are not registered in the generic Operations registry as `safe`.
6. Without ArangoDB, the portal starts and preview works. Persistence and action routes return an explicit unavailable error.
7. Each page element carries the `data-testid` from `quickstart.md`.
