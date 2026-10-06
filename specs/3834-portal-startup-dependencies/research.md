# Research: Portal Startup Dependencies

## Startup and override boundary

**Decision**: Keep the no-argument factory. Install a request-safe provider, not services that hold missing or shared collaborators.

**Evidence**: `wsgi_capture.py:48` calls `create_app()` without overrides.
`app/factory.py:1195` reads settings, validates optional overrides, and installs seams before blueprints.
`app/wiring.py:1425` returns after installing the complete E2E configuration.
The production branch then calls four installers that read absent `MIST_CLIENT` and `DB_ROUTER`.
The action repository receives an Arango handle. It does not supply a `DatabaseRouter`.

**Rationale**: Factory startup has no authenticated operator. A shared service with a mutable client can mix operator sessions.

**Alternatives considered**: A process-wide token client violates request identity.
Constructing services with `None` preserves the defect. Creating dependencies before the E2E branch breaks isolation.

## Identity lookup and background work

**Decision**: Resolve the current operator through `identity.current_session()` inside the active request.

**Evidence**: `runtime/identity.py:761` reads the signed `owner_key`, queries `SESSION_REGISTRY`, and compares the browser identifier.
`SessionRegistry` protects the owner-key map with an `RLock`.
`app/wiring.py:791` resolves request bindings before starting an upgrade worker.
The worker receives the operator session explicitly because its thread cannot read the request context.

**Rationale**: The existing lookup rejects stale keys and a copied signed session with a different browser identifier.
It provides the authenticated operator's `cloud_session`, not an invented global client.

**Alternatives considered**: Reading only the cookie skips registry validation.
Using Flask application context in a worker does not recreate authenticated request identity.

The provider must check that the resolved record has a usable cloud session.
It must not close the registry-owned session during request teardown.
Do not put that borrowed session in `g.mist_session`, because factory teardown closes that name.
If worker work outlives the request, bind ownership before launch and use the existing worker lifecycle.
Never pass a lazy request proxy into a worker.

## Database construction and settings

**Decision**: Build `DatabaseRouter` with a validated `DatabaseConfig` and the existing strategy mapping.
Create an explicit document handle for reads. Keep these two dependencies distinct.

**Evidence**: `src/foundation/persistence/db/__init__.py:68` provides `DatabaseConfig.from_env()`.
It resolves hosts, can select standalone mode, and validates database credential variables when storage is configured.
`src/foundation/persistence/db/router.py:117` requires `config` and optionally accepts `strategies`.
Construction attempts ArangoDB, Redis TimeSeries, and RedisJSON connections.
`health_check()` returns `arangodb`, `redis`, `redis_json`, and `standalone`.
`capture/store.py:590` accepts an explicit config. The no-argument path instead caches a process-wide handle.
Portal Arango and Redis settings use the existing environment variables and carry password-variable names.

**Rationale**: A database handle is not a router. A router in standalone mode cannot supply durable capture storage.
Reject invalid settings before construction. Require Arango availability for these service records.
Preserve separate Redis lock refusals. Do not require RedisJSON for an Arango-only service write.

**Alternatives considered**: Calling `DatabaseRouter()` without config fails.
Using the action repository's database handle as a router fails its interface contract.
Using no-argument `connect_database()` for request-owned handles introduces shared lifecycle ambiguity.

Use `DatabaseConfig.from_env()` as the current configuration source.
Verify its host, database, username, Redis host, and Redis port against the loaded portal settings.
Reject inconsistent configuration instead of silently connecting to another store.
Keep credential values inside connection objects. Log variable names or error types only.

## Real storage and audit call shapes

**Decision**: Replace invalid service call sites. Do not add methods to the shared router to match test doubles.

**Evidence**: `DatabaseRouter.write()` accepts `data` and `api_function_name`.
It has no `query`, `get_run`, `get_comparison`, `update_run`, or `update_comparison` method.
Capture, upgrade, settle, and comparison services instead call `write(collection=..., document=...)`.
Upgrade status and cancellation call a nonexistent `query()` method.
Comparison routes call four nonexistent router methods.

`DatabaseRouter._csv_fallback()` reports `success=True`, `backend="csv_only"`, and zero records.
`WriteResult` is a dataclass. Object truthiness does not prove its `success` field.
`capture/store.write_capture()` and `write_run()` verify durable writes by reading records again.
Capture verification also requires schema, digest, and nonzero size.
Existing strategy keys `upgrade_captures` and `upgrade_runs` use natural keys and no expiry.

`app/wiring.py` supplies a stdlib logger as `audit_logger`.
Services require `log_operation()`, which that logger does not provide.
The existing `audit.logger.AuditLogger` owns that method, but its write arguments also disagree with the router.
Some service audit calls use extra keywords that disagree with `AuditLogger.log_operation()`.

**Rationale**: Supplying non-null objects can leave every operation broken.
Use the real router signature for routed writes and documented Arango collection or parameterized AQL operations for reads and updates.
Reuse existing capture assembly and verified store behavior for capture and run records.
Use the real audit class and align affected call arguments. Preserve masking and durable failure reporting.

**Alternatives considered**: A facade with invented router methods hides incorrect assumptions.
Modifying the shared router for portal-only methods expands scope.
Treating CSV fallback, a returned identifier, or a dummy comparison as success violates FR-006 and FR-007.

Do not create a new collection or key strategy as a shortcut.
When a current service collection lacks a supported routed-write strategy, use its existing operational document-store boundary.
Preserve its current document shape and verify its write explicitly.
Do not change the collected-data export boundary.

## Mist and service operation patterns

**Decision**: Pass the request's real SDK session and reuse existing domain readers and gate evidence.
Replace unsupported client convenience methods at their existing service owners.

**Evidence**: `capture/devices.py:425` calls `mistapi.api.v1.sites.stats.listSiteDevicesStats` with explicit session and site arguments.
Its page reader validates status, payload shape, and completeness.
`capture/devices.py:394` reads inventory through `mistapi.api.v1.orgs.inventory.getOrgInventory`, with `vc=True`.
`capture/extras.py:507` derives radio records from device statistics.
`upgrade/gate.py:871` uses `mistapi.api.v1.orgs.stats.listOrgDevicesStats`.
`upgrade/options.py` owns supported version choices through `read_model_versions`.
`upgrade/org_versions.py` uses `RunningFirmwareVersionResolver` for running-version evidence.
Running-version evidence is not proof that a target firmware version is available.

Capture services call convenience methods such as `listSiteDeviceStats` on a client.
Upgrade services call `validateFirmwareVersion`. These are not the supported session interface used by the portal.
Settle service checks contain production placeholders.
Comparison service assumes settlement and returns dummy pre/post captures.

**Rationale**: The provider is a dependency owner, not a Mist API adapter.
Validate target firmware through existing option/version readers.
Read actual pre/post captures and settlement results. A missing policy or neighbor reader must cause an explicit incomplete result.
Never substitute an unverified SDK method or an assumed successful check.

**Alternatives considered**: Adding convenience methods to the session creates a prohibited adapter.
Direct REST requests violate the SDK boundary. Implementing a new endpoint or transport is outside this feature.
Expanding this repair into a replacement firmware engine is unnecessary.

## Routes and test evidence

**Decision**: Resolve dependencies at every current service consumer. Test registered routes and the default factory, not only route bodies.

**Evidence**: Capture start uses `CAPTURE_SERVICE`.
Upgrade service start, status helper, and cancel use `UPGRADE_SERVICE`.
The existing public status route has one owner. Keep it.
Comparison results and approval read `COMPARISON_SERVICE` and `DB_ROUTER` directly.
Comparison results check service availability but do not invoke `ComparisonService.compare()`.
The comparison blueprint has no `identity.require_session` decorator in its current handlers.
Portal security supplies address, CSRF, and response-header controls, not a replacement operator-session guard.

`tests/unit/upgrade_portal/test_phase2_service_wiring.py` checks installers and seam names.
`test_phase2_phase3_route_connections.py` uses mock services and unwrapped route bodies.
These tests do not prove real dependency compatibility or authentication.
`tests/integration/upgrade_portal/test_two_operators.py` provides a real registry and lock-isolation pattern.
`api/run_controls/models.py` supplies the complete immutable E2E override groups.
Their values cover records, actions, security, and cloud readers, not injected `MIST_CLIENT` or `DB_ROUTER`.

**Rationale**: Preserve complete E2E semantics without adding new required override fields.
Do not enter the production provider for E2E routes.
Apply authenticated request resolution to comparison consumers before any store access.
Do not treat comparison GET as a new computation endpoint.
Exercise settlement and comparison computation through real service calls inside authenticated request contexts.

**Alternatives considered**: Extending only the capture installer leaves upgrade and comparison paths broken.
Adding a second status or settle route changes ownership.
Testing only key presence repeats the evidence gap in issue #3834.

## Structure and process decisions

**Decision**: Use the existing `app/wiring.py`. Record hierarchy remediation separately.

**Evidence**: Runtime has nine functional modules plus its package marker.
App, capture, upgrade, and compare directories also exceed five functional children.
The provider belongs to application wiring, not the runtime preflight module.

**Rationale**: Existing-file edits avoid adding children to noncompliant product parents.
Replace the four eager installer declarations with class-owned provider construction and bounded dependency records.
Keep the net declaration count from increasing. Record touched class-member debt before task generation.

**Alternatives considered**: A direct `runtime/service_provider.py` child violates FR-009.
A new package directly under runtime also violates FR-009.
A broad hierarchy repair conflicts with the narrow defect scope.

**Process decision**: Use the current plan template manually because Python setup is absent and PowerShell is unavailable.
The mandatory companion command is registered, but extension inspection reports it corrupted and disabled.
Report an unsuccessful hook execution honestly. Do not write a false planned-state receipt.
