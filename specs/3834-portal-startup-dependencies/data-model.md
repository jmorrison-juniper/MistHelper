# Data Model: Request Dependency Ownership

This feature changes dependency ownership, not stored schemas.
Existing capture, run, settlement, comparison, action, and audit records retain their keys and retention.

## Operator request

| Field | Source | Validation |
| - | - | - |
| Owner key | Signed Flask session | Must be a string and identify a registry record. |
| Browser identifier | First-party browser cookie | Must match the owner of the registry record. |
| Operator record | `identity.current_session()` | Must exist for each Mist-dependent operation. |
| Cloud session | `OperatorSession.cloud_session` | Must support the real SDK session contract. Never validate through object truthiness alone. |
| Organization and site | Existing request and run context | Existing authorization and run ownership checks remain authoritative. |

A copied owner key with a different browser cookie fails authentication.
A missing or stale registry record also fails authentication.
The provider does not replace the registry, sign-in flow, or authorization model.

## Request dependency record

Use a bounded typed record with at most five fields.

| Field | Ownership | Lifetime |
| - | - | - |
| Operator record | Borrowed from registry | Active operation. Never close its cloud session at request teardown. |
| Database router | Owned by request | Close once through `g.database_router`. |
| Document-store handle | Explicit connection from validated config | Request-owned connection scope. Never close the process-global cached handle. |
| Audit service | Constructed from this storage scope | Same request or explicit worker operation scope. |
| Service graph | Constructed after dependency validation | Same request. Never store resolved instances in shared Flask configuration. |

The service graph holds capture, upgrade, settle, and comparison services.
Comparison receives the exact settle service from its graph.
Every storage-dependent service receives the valid router required by FR-004.
Services use the separate document handle for real document reads and updates, not nonexistent router methods.

The provider can retain construction instructions in application configuration.
It cannot retain a resolved operator, cloud session, request graph, or request-owned database connection there.
Cache resolved dependencies only in Flask `g`.
Do not place the borrowed cloud session in `g.mist_session`, because existing teardown closes that name.

## Dependency resolution state

```text
unresolved
  -> authentication_refused
  -> storage_refused
  -> ready
ready
  -> operation_failed
  -> durable_success
ready / operation_failed / durable_success
  -> owned_resources_closed
```

Authenticate before opening storage or making a Mist call.
Validate config, construct the router and document handle, then check required storage availability.
Only then construct and invoke the service graph.
If partial construction fails, close each owned connection once.
Keep the registry-owned cloud session available for the operator's later request.

A worker cannot read `g` or request cookies after launch.
Capture the authenticated session before launch, following existing `request_bindings`.
The worker must own storage that remains open until its work completes.
Request teardown cannot close a worker's storage handle.
Do not add a worker merely to resolve dependencies.

## Persistence outcome

| Outcome | Required interpretation |
| - | - |
| `success=False` | Storage failure. Stop the operation. |
| `backend="csv_only"` | Backup/export only. Not durable portal evidence. |
| Zero records or failed read-back | Storage failure, even when the result object is truthy. |
| Matching durable record | Continue only after existing schema, key, digest, and size checks pass. |
| Audit write failure | Visible failure. Do not report the required audit action as complete. |

Retain current capture backup files under `data/`.
Keep current recovery and retention policies. Add no TTL, deletion, or schema migration.
Comparison approval cannot report completion after either required update fails.
Cancellation cannot report cloud cancellation when no verified operation occurred.
Comparison cannot pass with dummy captures or assumed settlement.

## Test override record

Keep `E2EFactoryOverrides` unchanged.
Validate its complete records, actions, security, and external groups before registering routes.
Install the supplied objects without replacing them.
The production provider, router constructor, document connector, and storage bootstrap must remain uncalled.
An incomplete override set raises before route registration.

## Structural rule

Reuse existing module locations and replace existing noncompliant members rather than adding siblings.
The request provider does not become a tenth functional child of `runtime/`.
See [plan.md](plan.md) for measured debt and separate remediation actions.
