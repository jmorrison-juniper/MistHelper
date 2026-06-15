# Quickstart: Implementing Org Async Claim Menu Operations

## Goal

Implement and verify three new menu operations for mistapi 0.63.0 org async-claim APIs:
- 208: list async claims (safe)
- 209: create async claim (destructive)
- 210: get status by claim ID (safe)

## 1) Edit scope

Primary files expected in implementation phase:
- `MistHelper.py`
- `README.md`
- `CHANGELOG.md`
- `tests/unit/*` (new or updated tests)

## 2) Implementation checklist

1. Add three handler functions in `MistHelper.py`:
   - `list_org_async_claims()`
   - `create_org_async_claim()`
   - `get_org_async_claim_status()`
2. Add menu entries `208`, `209`, `210` in `menu_actions`.
3. Add PK strategy mappings in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for:
   - `listOrgAsyncClaims`
   - `createOrgAsyncClaim`
   - `getOrgAsyncClaimStatus`
4. Wire destructive confirmation in create path with exact `CREATE` gate.
5. Validate claim ID input in status path before API call.
6. Ensure list/status use standard flatten + export pipeline.
7. Add destructive skip mapping for menu 209 in default `--test` harness.
8. Update operation count and menu docs in `README.md`.
9. Add changelog entry in `CHANGELOG.md` (timestamp format used by project).

## 3) Verification checklist

### Static checks
- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py`
- `python -m black --check MistHelper.py`

### Unit tests
- run targeted tests for new operations:
  - list success/empty/error
  - create confirmation gate + success/error
  - status validation + success/error

### Behavioral checks (manual)
- menu 208 returns records or clean empty-result message.
- menu 209 does not call API unless confirmation exactly `CREATE`.
- menu 210 rejects blank claim ID and handles not-found cleanly.

## 4) Done criteria

Feature is complete when:
- all FR-001..FR-013 from `spec.md` are satisfied,
- tests pass,
- README and changelog reflect operation count 210,
- destructive behavior is blocked in default `--test` profile.
