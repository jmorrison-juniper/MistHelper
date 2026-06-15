# Research: Org Async Claim Menu Operations (mistapi 0.63.0)

## Decision 1: Menu numbering and operation scope

- **Decision**: Implement three operations as menu IDs **208**, **209**, and **210**.
- **Rationale**: Existing `menu_actions` currently ends at `207`; contiguous addition satisfies FR-012 (operation count 207→210) with minimal churn.
- **Alternatives considered**:
  - Reusing old gaps: rejected because it breaks numeric discoverability and operator expectation.
  - Grouping in lower ranges: rejected due to established high-range upstream additions (195+).

## Decision 2: API endpoint mapping

- **Decision**: Map feature operations to mistapi org-level async-claim endpoints:
  - list: `mistapi.api.v1.orgs.claims.listOrgAsyncClaims(...)`
  - create: `mistapi.api.v1.orgs.claims.createOrgAsyncClaim(...)`
  - status: `mistapi.api.v1.orgs.claims.getOrgAsyncClaimStatus(...)`.
- **Rationale**: `docs/UPSTREAM_mistapi_changes.md` identifies these v0.63.0 additions as target APIs for this feature.
- **Alternatives considered**:
  - Direct raw HTTP requests: rejected because constitution and repo standards require mistapi SDK usage when available.
  - Deferring status operation: rejected because status lookup is explicit FR-005/P3 scope.

## Decision 3: Destructive safety pattern for create

- **Decision**: Require exact uppercase typed confirmation (`CREATE`) via `_confirm_destructive("CREATE", "org_async_claim_create")` before dispatching create API call.
- **Rationale**: Aligns with existing destructive operations (e.g., menus 204–207) and constitution Safety-First rules.
- **Alternatives considered**:
  - Yes/No prompt only: rejected as too weak for destructive workflows.
  - Implicit confirmation from payload entry: rejected because FR-003 requires explicit typed confirmation.

## Decision 4: Input model and validation strategy

- **Decision**:
  - claim ID for status is required non-empty `safe_input(...).strip()`.
  - create payload captured using safe prompts and validated before API call.
  - on invalid/empty input, fail fast with user feedback and no API dispatch.
- **Rationale**: Matches `safe_input()` and early-return validation pattern already used throughout `MistHelper.py`.
- **Alternatives considered**:
  - Passing raw/unvalidated strings to API: rejected (FR-006 + constitution III).
  - JSON blob free-form parser only: rejected for operator usability and supportability.

## Decision 5: Export and persistence behavior

- **Decision**:
  - list and status results exported through `DataExporter.save_data_to_output(..., api_function_name=...)`.
  - create response optionally exported through same pipeline for auditability and repeatability.
  - flatten nested results with existing helpers before write.
- **Rationale**: FR-008 and existing MistHelper output conventions require consistent CSV/SQLite behavior.
- **Alternatives considered**:
  - Print-only output: rejected (does not satisfy export conventions).
  - Dedicated one-off writer: rejected (duplicates exporter logic and PK rules).

## Decision 6: Primary key strategy

- **Decision**: Add explicit endpoint PK strategy entries for list/create/status async-claim outputs in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- **Rationale**: FR-009 requires deterministic upserts and dedupe behavior in SQLite mode.
- **Alternatives considered**:
  - Falling back to `default` strategy: rejected as too weak/implicit for new endpoint family.
  - Composite on unstable fields only: rejected unless endpoint payload lacks stable IDs.

## Decision 7: Test strategy and destructive skip policy

- **Decision**:
  - unit tests for success + validation-failure + API-error for each operation.
  - mark destructive create operation as skipped in default `--test` profile by adding it to destructive skip map.
- **Rationale**: FR-010/FR-011 and existing systematic test guardrails prohibit executing destructive operations in default run.
- **Alternatives considered**:
  - Running create in standard `--test`: rejected due to safety policy.
  - Manual-only testing with no unit coverage: rejected (FR-010).

## Decision 8: Documentation updates

- **Decision**: Update `README.md` operation count and menu coverage text to include 208–210; add changelog entry in `CHANGELOG.md` for mistapi 0.63.0 async-claim support.
- **Rationale**: FR-012/FR-013 mandate docs and release-note alignment.
- **Alternatives considered**:
  - Defer docs to later PR: rejected because docs parity is part of acceptance criteria.

## Open risks and mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| SDK module-path mismatch (`orgs.licenses` vs actual `orgs.claims`) | Runtime call failure | Confirmed against installed mistapi 0.63.0 SDK during implementation; handlers use `mistapi.api.v1.orgs.claims.*`. |
| Async eventual consistency after create | confusing user state | clear user message to run status check if immediate completion not visible. |
| Endpoint response schema variability | flatten/export edge cases | normalize dict/list response shapes before flattening; add tests for empty and partial payloads. |
