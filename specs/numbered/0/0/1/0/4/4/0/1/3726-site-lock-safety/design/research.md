# Research: Site Lock Safety for Uncertain Upgrade Replies

## Decision 1: Use a narrow HTTP refusal allowlist

**Decision**: Treat HTTP 400, 401, 403, and 404 as proven refusals only when the reply has no upgrade identifier.

**Rationale**: The repository OpenAPI lists these statuses for `upgradeOrgDevices`, `upgradeSiteDevices`, and `upgradeOrgSsrs`. It also lists HTTP 429. A 429, timeout, server error, missing status, or unlisted code does not prove that the cloud did not start a job.

**Alternatives considered**:

- Treat every 4xx as a refusal. Rejected because HTTP 408 and HTTP 429 are uncertain, and HTTP 499 is not a documented Mist response.
- Treat every returned error as a refusal. Rejected because an error can arrive after the cloud starts a job.
- Treat every reply as uncertain. Rejected because documented request refusals must release locks for later valid work.

## Decision 2: Require an identifier for acceptance

**Decision**: Mark a submission accepted only when its existing success rule passes and it has an upgrade identifier.

**Rationale**: Later status reads and cancellation use the identifier. A success status without it cannot prove which job the portal should follow.

**Alternatives considered**:

- Accept a device response without an identifier when it lists accepted devices. Rejected because the portal cannot reconcile or cancel that job.
- Change the API service response schema. Rejected because the existing response already carries the status and identifier fields needed for safe classification.

## Decision 3: Preserve existing lock ownership and recovery

**Decision**: Keep the current operation-wide lock map and the existing lease and operator recovery controls.

**Rationale**: The current lock gate already holds locks for unknown outcomes. The defect is that returned ambiguous replies use `rejected` and bypass that gate.

**Alternatives considered**:

- Add a lock migration or change the lease. Rejected because neither change is needed to keep an unknown outcome locked.
- Add a new manual recovery route. Rejected because the portal already has lock recovery controls.

## Evidence

The local OpenAPI file `documentation/mist-api-openapi31json.json` lists the same response codes for the three existing upgrade methods. The issue's source-export evidence shows that returned ambiguous replies currently enter the `rejected` lock-release path. Existing cancellation logic already treats HTTP 500 and malformed HTTP 200 replies as uncertain, but it uses a broad 4xx range.

No live Mist request was made.
