# Portal and Review Contract

## Existing Contract

Preserve `/cisco-config-converter/`, `/preview`, `/review`, `/export`, and `/assets` under the current feature prefix.
Current preview accepts one multipart file, name, and type.
Current types are `spoke` and `standalone`.
Current preview returns `gateway_template`, `unsupported_items`, and `known_gaps`.
Current review binds the full proposal digest.
Current export requires that exact reviewed proposal.
Invalid input returns 400. Missing or stale review returns 409.
The request-body limit returns 413 before parsing.
Keep CSRF protection, converter-scoped memory upload handling, and `Cache-Control: no-store`.

Extended full-parity proposals require an explicit version contract.
Do not silently reinterpret existing clients' names, types, or export shape.
Keep existing routes and their narrow semantics while adding versioned full-review operations.
This is protocol preservation, not permission to add a compatibility shim around moved code.

## Integration Evidence and Blockers

`web_portal/app.py` supplies `APISESSION`, `ORG_ID`, and `DATA_DIR` and registers the shared security middleware.
It does not register the converter blueprint.
`web_portal/templates/base.html` does not provide converter navigation.
The current converter browser fixture mounts an isolated host, not the production portal factory.
T032 needs integration-owner handover and real-factory tests.

`web_portal/services/config.py` states that the portal has no user authentication.
Its IP allowlist is not operator identity or per-operator authorization.
A shared Mist credential and browser session ownership do not establish an operator identity.
Cloud writes remain blocked until the owner approves an identity and authorization design.
The design must prove denied, expired, changed, and cross-operator access with synthetic identities.

The portal secret comes from `PORTAL_SECRET_KEY` or a new random value at app initialization.
An unset or inconsistent secret can invalidate session-bound approval across processes or restarts.
T006 must define a stable, private secret configuration and test restart and multiworker behavior.
The example in `wsgi.py` uses one worker and four threads.
Do not assume that every deployment uses one worker.

The CSRF middleware selects JSON automatically for `/api/` paths or clients that prefer JSON.
The converter prefix is not `/api/`.
Test request headers and safe error shape for converter CSRF failures without changing other routes.
Trusted proxy behavior is opt-in and must remain unchanged.

`web_portal/services/data_browser.py` and `web_portal/services/output_scan.py` protect the existing firmware backup directory.
Those guards do not automatically protect a new converter-private directory.
Before persisting any private converter data, test browser listing, preview, download, output scan, links, and logs.
Prove that the selected storage policy blocks every unintended access path.
Firmware job storage and recovery code are prior art, not proof of converter authorization or safe reuse.

`compose.yml` shares the portal, `data/`, ArangoDB, and Redis and checks `/ready`.
Preserve service ownership, mounts, ports, and readiness behavior.
Do not add a separate stack or database without owner approval.

## Future Interface Families

| Family | Proposed namespace behavior | Required failure evidence |
| --- | --- | --- |
| Files | Converter catalog and bounded upload/select operations | Traversal, symlink, collision, invalid text, exact size |
| Display | Independent structured parser review | No conversion, no cloud calls, redacted values |
| Mapping | Role, family, model, and explicit port assignments | Unknown model, duplicate port, stale inventory |
| Proposal | Versioned conversion, change review, and export | Altered digest, omissions, unsupported fields |
| Discovery | Status, sites, assigned/unassigned gateways | Pagination, denied access, unavailable checks |
| Apply | Exact current approved scope and APPLY word | Zero writes on every refusal |
| Administration | Backup/catalog, restore, delete, and unassign | Hidden/denied mode, invalid backup, rejected CONFIRM |
| Recovery | Reconciliation and reviewed recovery proposal | Unknown result, unrelated changes, partial recovery |

These are planned interfaces, not existing route claims.
Finalize exact new paths in contract tests before implementation.
Do not take over generic source `/api/*` paths in the shared portal.
Reuse the existing portal health endpoint and preserve its response shape.

## Input and Persistence Rules

Support `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log`.
Require valid UTF-8, nonempty text, and no null bytes.
The file limit is 16 MiB. Keep the current separate multipart allowance of 16 KiB.
Resolve stored paths against a configured private subtree under `data/`.
Reject escapes after canonical resolution, including symlinks and Windows path forms.
Use opaque file IDs in requests rather than arbitrary client paths.
Never overwrite an existing upload silently.
Show only safe file metadata in the catalog.
Do not persist uploads unless the operator explicitly selects the approved retention workflow.

## Visual and Interaction Rules

Independently author the centered selection card within the shared portal shell.
Use the host theme manager for the four observed visual intentions.
Show structured input review separately from object-level proposed changes.
Show current organization, site, gateways, role, family, model, omissions, and recovery status before confirmation.
Typed APPLY enables submission only for a current, permitted, fully checked proposal.
Typed CONFIRM applies to approved administrative writes after a separate scope confirmation.
The server repeats every permission, digest, scope, and typed-word check.
Cancel clears typed input without cloud writes.
Use stable `data-testid` values for every new interactive element.
Test keyboard focus, dialog focus restoration, non-color status text, and safe rendering of untrusted source text.

## Error and Privacy Rules

Return a safe operation-specific error and correlation identifier.
Keep secret-redacted diagnostic context in server logs.
Use explicit pending, unavailable, denied, failed, partial, indeterminate, and verified states.
Do not treat a failed lookup as an absent object or a successful empty result.
Keep secret values out of ordinary HTML, JSON exports, cookies, browser storage, caches, and logs.
Full recovery backups require separate private access and must not use the ordinary export route.
