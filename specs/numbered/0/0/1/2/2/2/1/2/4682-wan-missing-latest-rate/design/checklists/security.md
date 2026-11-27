# Security Checklist: Report a missing latest WAN rate

**Purpose**: Check the secret handling, input handling, and network use of the plan before the change starts.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder of this checklist.

## Input Handling

- [x] Each source value passes the existing numeric check before use (`snapshot_client.py` line 345, R-82).
- [x] A timestamp outside the expected interval starts still raises ValueError (line 322, R-78).
- [x] Misaligned arrays still raise ValueError (line 266, R-83).
- [x] The change adds no input path from the browser. The change touches the collection path only (plan.md, Architecture and Trace).

## Secrets and Logs

- [x] The plan adds no log field that holds a credential (plan.md, Constitution Check, Observability row).
- [x] The plan requires `%s` formatting and counts or states in new log lines (plan.md, Constitution Check, Action logging row).
- [x] The plan requires ASCII log text only (constitution.md Principle V).

## Network and SDK Use

- [x] The plan reuses the existing mistapi method (`getSiteInsightMetricsForGateway`, R-50).
- [x] The plan adds no HTTP request and no direct Mist REST call (plan.md, Constitution Check, mistapi only row).
- [x] FR-010 forbids live Mist calls in tests (spec.md, Functional Requirements).

## Residual Risks

- [x] The snapshot partial flag does not change (D-6). Residual risk AN-5 is recorded in `analysis.md`.
- [ ] A live Mist response check is not run in this pass. Not met by design: issue 4682 requires zero live calls. Unverified items U-2 and U-3 in `design/research.md` remain open.
