# Research: Site Marvis Config Action APIs Menu Set (mistapi 0.63.0)

## Decision 1: Operation set and menu safety classes

- **Decision**: Implement four menu operations grouped by risk class:
  1. Site Marvis Config Action count (safe)
  2. Site Marvis Config Action search (safe)
  3. Submit Site Marvis Config Action feedback (mutating)
  4. Delete Site Marvis Config Action by action ID (destructive)
- **Rationale**: Matches feature requirements and keeps operator intent explicit by separating read, mutate, and destructive actions.
- **Alternatives considered**:
  - Combining feedback + delete under one "manage" operation: rejected because destructive safeguards become less explicit.
  - Exposing only safe operations initially: rejected because spec requires feedback and delete parity in same feature.

## Decision 2: SDK-first endpoint binding

- **Decision**: Use mistapi 0.63.0 site-level Marvis config action methods only, with no raw HTTP fallbacks in the main path.
- **Rationale**: Constitution requires SDK-first integration when endpoint exists; improves compatibility and consistency.
- **Alternatives considered**:
  - Direct REST calls: rejected by project rules and adds maintenance risk.

### Verified callable names and signatures (mistapi 0.63.0)

- `mistapi.api.v1.sites.marvis_configs.countSiteMarvisConfigActions(mist_session, site_id, distinct=None, mac=None, type=None, src=None, admin_id=None, op=None, port_id=None, vlan_ids=None, reason=None, limit=None, start=None, end=None, duration=None)`
- `mistapi.api.v1.sites.marvis_configs.searchSiteMarvisConfigActions(mist_session, site_id, mac=None, type=None, src=None, admin_id=None, op=None, port_id=None, vlan_ids=None, reason=None, limit=None, start=None, end=None, duration=None)`
- `mistapi.api.v1.sites.marvis_configs.submitSiteMarvisConfigFeedback(mist_session, site_id, id, body)`
- `mistapi.api.v1.sites.marvis_configs.deleteSiteMarvisConfigAction(mist_session, site_id, id)`

## Decision 3: Input and validation contract

- **Decision**: Reuse `safe_input()` for all interactive prompts and enforce strict validation before API calls:
  - required field checks for feedback payload
  - allowlist checks for enumerated values
  - format checks for action IDs and bounded text fields
- **Rationale**: Satisfies Safety-First and explicit FR guardrail requirements.
- **Alternatives considered**:
  - Best-effort pass-through validation: rejected due to mutation risk and non-actionable errors.

## Decision 4: Destructive guard pattern

- **Decision**: Keep delete behind a two-layer guard:
  1. explicit warning banner describing impact
  2. exact typed confirmation string (case-sensitive)
- **Rationale**: Aligns with existing destructive operation policy and prevents accidental invocation.
- **Alternatives considered**:
  - yes/no confirmation only: rejected as too weak for production destructive action.

## Decision 5: Pagination and deterministic export behavior

- **Decision**: Search operation supports pagination traversal and exports deterministic rows through existing export path.
- **Rationale**: Needed for large datasets and stable operator audit outputs.
- **Alternatives considered**:
  - single-page only search: rejected because it silently drops data in larger sites.

## Decision 6: Primary key strategy for new datasets

- **Decision**: Define explicit `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries:
  - count dataset: deterministic scope key (site/window/filter hash)
  - search dataset: idempotent record key (action_id preferred, timestamp/context fallback)
  - feedback result dataset: operation-context key with request identity and timestamp
  - delete result dataset: operation audit key keyed by site+action+execution time
- **Rationale**: Required by spec for deterministic upsert behavior across CSV/SQLite/polyglot backends.
- **Alternatives considered**:
  - implicit/default key strategy: rejected due to duplicate row risk and drift in reruns.

## Decision 7: Observability and operator messaging

- **Decision**: Add action logging before/after every meaningful step and return actionable terminal summaries:
  - selected site + filter scope
  - validation outcomes
  - affected row count/result status
- **Rationale**: Constitution non-negotiable logging rules and junior-operator usability.
- **Alternatives considered**:
  - minimal logging: rejected because failure triage becomes opaque.

## Decision 8: Test strategy and destructive guard enforcement

- **Decision**: Extend automated tests for:
  - safe count/search happy paths
  - feedback valid/invalid payload gates
  - destructive delete guard behavior (wrong confirm, cancel, exact confirm path simulated)
  - explicit destructive skip/guard in unattended full-test mode
- **Rationale**: Meets FR-012/FR-013 and prevents accidental mutation during CI-style runs.
- **Alternatives considered**:
  - manual-only destructive verification: rejected due to regression risk and hidden-test constraints.

## Open risk log and mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| SDK method signature drift vs expected params | runtime failure | verify signatures during implementation and centralize call wrappers per operation |
| Ambiguous action ID input format from operators | rejected requests or wrong target | enforce validation + preview target context before mutation/destruction |
| Very large search result sets | partial export if pagination mishandled | mandatory continuation loop and completion summary with page counters |
| Delete operation accidentally triggered in automation | production state mutation risk | keep hard destructive guard and explicit test-skip behavior in unattended mode |
