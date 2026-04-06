# Implementation Plan — SSID Template Consolidation (Feature 018)

## Objectives

- Implement a 5-phase guided workflow in MistHelper to consolidate per-site SSID templates into a small set of consolidated templates.
- Maintain idempotence and auditability for every operation.
- Ensure PSK-based sites are excluded from automated modifications.

## Phases (Mapping to the spec)

1. Phase 1 — Inventory & Deviation Analysis (FR-005 ⇒ FR-010b)
2. Phase 2 — Write Site Variables (FR-011 ⇒ FR-013)
3. Phase 3 — Assign Site Groups (FR-014 ⇒ FR-015)
4. Phase 4 — Create/Update Consolidated Templates (FR-016 ⇒ FR-018)
5. Phase 5 — Disable Old Template SSIDs (FR-005 & FR-010)

## High-Level Design

- Single top-level command: `menu 159` (or named) that loads `specs/feat/018-ssid-template-consolidation/spec.md` for the operational contract and drives the guided flow.
- Cache layer under `data/ssi-template-consolidation/cache.db` (sqlite) for Phase 1 results.
- Results/logging: per-phase CSV and SQLite outputs for audit. Logs stored in `data/logs/ssid-consolidation/`.
- API client: reuse `mistapi` helpers already present in the project, obey existing rate-limiting helpers.
- Confirmation style: destructive writes require typed `CONFIRM` per agents.md guidance.

## Data Model

- `Phase1Matrix` (SQLite table): site_id PK, site_name, template_id, template_name, target_ssid_name, target_ssid_id, psk_detected boolean, edge_cluster_id, edge_cluster_name, anomaly_code
- `DeviationReport` (serialized JSON stored in SQLite blob column): per-cluster field -> values map with counts
- `OperationsLog`: per-phase per-site operation results (success/failure, error message, timestamp)

## Acceptance Criteria

- All Phase 1 CSV/DB outputs are generated and include the deviation analysis (FR-010a).
- Phase 2 writes are idempotent (FR-011/FR-012).
- Phase 3 site groups exist and membership is idempotent (FR-014/FR-015).
- Phase 4 template creations are idempotent and append-only for multiple SSID runs (FR-016).

## Security & Safety

- All writes are gated behind typed `CONFIRM`.
- No destructive deletes; old SSIDs are disabled (FR-005/FR-010)
- PSK sites are never modified automatically.

## Rollback & Resume

- If the workflow is interrupted, reconciling uses `OperationsLog` to detect finished sites and resumes where left off.
- If templates need rollback, the system re-enables old template SSIDs from the archived state in `OperationsLog`.

## Implementation Steps (developer-friendly)

1. Add new menu option wiring in `MistHelper.py` to hook `menu 159` to new `SSIDTemplateConsolidationManager` class.
2. Implement `SSIDTemplateConsolidationManager.phase1_collect()` to create Phase1Matrix and DeviationReport.
3. Implement caching helpers around Phase1Matrix (refresh window configurable via env `SSID_CONSOLIDATION_CACHE_MINUTES`).
4. Implement `phase2_apply_site_vars()` with typed confirmation and idempotent writes.
5. Implement `phase3_assign_site_groups()` with create-if-missing site groups.
6. Implement `phase4_create_templates()` with interactive deviation resolution UI.
7. Implement `phase5_disable_old_ssids()` that sets `enabled=False` in templates per-site, preserving configs.
8. Tests: unit tests for `deviation_analysis()` and `generate_template_name()`; integration test mocking the `mistapi` client to validate idempotence.
9. Docs: Add `specs/feat/018-ssid-template-consolidation/quickstart.md` and a short README entry.

## Timeline

- Quick prototype (Phase 1): 1–2 days
- Phases 2–4 with tests: 3–5 days
- Phase 5 and cleanup: 1–2 days

## Notes / Constraints

- Must avoid overwhelming the Mist API — use existing rate-limit helpers and backoff.
- This plan assumes `mistapi` is installed and available.
