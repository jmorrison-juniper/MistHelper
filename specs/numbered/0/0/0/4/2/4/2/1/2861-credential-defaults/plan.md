# Credential default resolution implementation plan

**Issue**: #2861  
**Route**: `specs/numbered/0/0/0/4/2/4/2/1/2861-credential-defaults/`  
**Dependency rule**: Complete each batch in order. Do not combine shared hot
files from different active pull requests.

## Batch 0: establish the guard

Create the AST scanner, baseline, negative fixture, and guard tests.

Files:

* `tests/guardrails/test_credential_default_ratchet.py`
* `.github/credential-default-baseline.json`
* `tests/guardrails/fixtures/credential_defaults_negative.py`

The guard must scan 2,295 tracked Python files, report zero parse failures, and
record the current candidate baseline. It must fail on zero input and on the
negative fixture.

Dependency: none.

## Batch 1: enforce the Mist session boundary

Remove process-wide token fallbacks from the Mist request paths.

Files:

* `MistHelper.py`
* `src/mist/networking/network/_routing_utils_payload.py`
* `src/mist/realtime/websocket/manager.py`
* `src/mist/resources/device/arp_command_manager.py`
* The focused tests named in the candidate manifest.

Reject a missing session token before the SDK call. Apply the selected token
environment rule once. Do not add a compatibility fallback.

Dependency: Batch 0.

## Batch 2: enforce organization token resolution

Make the organization session reject a global configured token after scoped
providers miss.

Files:

* `mist-ops-platform/src/shared/mist/session.py`
* `mist-ops-platform/tests/unit/mist/token_resolution/conftest.py`
* `mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py`
* `mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py`
* `mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py`

Preserve cache, Vault, configured environment behavior only when the provider
belongs to the requested organization. Test missing, blank, conflicting, and
valid opaque values.

Dependency: Batch 0.

## Batch 3: remove direct database credential defaults

Make direct database configuration require explicit validated credentials.

Files:

* `src/foundation/persistence/db/__init__.py`
* `src/foundation/persistence/db/writers/redis_writer.py`
* `tests/unit/db_discovery/test_config.py`
* `tests/unit/test_standalone.py`

Reject missing Arango and Redis credentials before client creation. Preserve a
validated standalone path without placeholder identity values.

Dependency: Batch 0.

## Batch 4: remove the portal database username default

Make the upgrade portal require its configured database identity.

Files:

* `src/interfaces/portals/upgrade_portal/app/config.py`
* `tests/unit/upgrade_portal/test_config.py`

Reject a missing Arango username before the portal creates a database client.
Keep the local generated session-key behavior only where it cannot authenticate
as a database identity.

Dependency: Batch 0.

## Batch 5: review the remaining 54 candidates

Classify each remaining candidate as an intentional optional value, a
fail-closed value, or a required credential defect. Repair only the required
credential defects.

Files:

* The remaining candidate files in the 40-file manifest.
* Their focused tests.
* The guard baseline.

The batch must not change a display label, fixture, disabled feature flag, or
optional value only to satisfy a broad text rule.

Dependency: Batches 1 through 4.

## Batch 6: close the ratchet and publish the implementation evidence

Remove repaired entries from the baseline, run the smallest test boundary, and
record the measured counts in the pull request.

Files:

* `.github/credential-default-baseline.json`
* `tests/guardrails/test_credential_default_ratchet.py`
* Batch-specific test files only when a failure needs repair.

Dependency: Batch 5.

## Ownership and conflict controls

* The integration owner must reserve `MistHelper.py` before Batch 1 starts.
* Each batch must use one pull request and one issue-scoped changelog fragment.
* No batch may edit a source file held by another active pull request.
* The guard owner must review every baseline reduction.
* A security reviewer must read each wrong-identity repair before merge.
