# Implementation Plan: Mist-Ops Platform API Endpoint Audit

**Branch**: `011-mist-ops-api-audit` | **Date**: 2025-07-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/011-mist-ops-api-audit/spec.md`

## Summary

Audit and fix all mistapi SDK endpoint usage across the mist-ops-platform codebase. Research (R-01 through R-08) identified 24 issues: 1 broken module path, 3 wrong method names, 5 missing `ApiResult` properties, 3 call signature mismatches, 3 list methods missing pagination, 1 internal method name error, 7 registry bypass calls, and 1 missing firmware SDK call. All fixes are verified against mistapi 0.60.4.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: mistapi 0.60.4 (Mist API SDK), FastAPI, Celery, SQLAlchemy
**Storage**: PostgreSQL 16, Redis 7
**Testing**: pytest
**Target Platform**: Linux containers (3-container app: API + Celery Workers + Celery Beat), Windows dev
**Project Type**: web-service
**Performance Goals**: N/A (correctness audit, not performance work)
**Constraints**: All SDK calls must go through entity registry; max 5 params / 25 lines per function (constitution)
**Scale/Scope**: 14 entity types in registry (expanding to ~23), 11 source files affected, 24 issues to fix

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Five-Item Rule

- **Registry expansion**: Adding ~9 new entity types brings the registry from 14 to ~23 entries. The `ENTITY_ENDPOINT_MAP` dict is a flat lookup table, not a hierarchy level — entries are data, not structural children. **PASS** (no hierarchy violation).
- **ApiResult expansion**: Adding 2 `@property` methods to a 2-field dataclass brings it to 4 members (2 fields + 2 properties). **PASS** (under 5).
- **MistEndpoint changes**: Adding `list_method` brings MistEndpoint to 6 fields (exceeds 5-field limit). **CONDITIONAL PASS** — justified in Complexity Tracking below; the alternative (3 separate dataclasses) adds more structural complexity than a single optional field.
- **New functions**: Pagination helper must stay under 25 lines and 5 params. **PASS** (planned at ~15 lines, 3 params).

### II. Class-Based Architecture

- All fixes modify existing classes (`ApiResult`, `MistEndpointService`, `FirmwareOrchestrator`). No standalone wrapper functions introduced. **PASS**.
- New entity types are data entries in the registry dict, not new classes. **PASS**.

### III. Safety-First

- Firmware upgrade is a destructive operation. The `FirmwareOrchestrator` already has `validate_upgrade()` with golden image checks. The new `execute_upgrade()` method must be called only after validation passes. **PASS** (existing safety gate preserved).
- No new `input()` calls introduced. **PASS**.

### IV. Full Deployment Pipeline

- Changes are to `mist-ops-platform/` (separate from MistHelper.py). The mist-ops-platform has its own container build via `compose.yml`. Standard `git commit` / container rebuild applies. **PASS**.

### V. Observability & Logging

- Existing `logger.error()` calls in executor.py and rollback.py already log error context. The `ApiResult.error` property provides structured error data. **PASS**.
- No Unicode introduced. **PASS**.

**Gate result**: 4 principles **PASS**, 1 principle **CONDITIONAL PASS** (Five-Item Rule — MistEndpoint 6 fields, justified in Complexity Tracking).

## Project Structure

### Documentation (this feature)

```text
specs/011-mist-ops-api-audit/
├── plan.md              # This file
├── research.md          # Phase 0 output (SDK verification findings)
├── data-model.md        # Phase 1 output (entity model changes)
├── quickstart.md        # Phase 1 output (implementation guide)
├── contracts/           # Phase 1 output (service interfaces)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (files modified by this audit)

```text
mist-ops-platform/src/
├── shared/
│   └── mist/
│       ├── types.py           # Entity registry (fix module paths, method names, add types)
│       ├── endpoints.py       # ApiResult expansion, pagination, optional read_method
│       └── session.py         # No changes needed
│   └── services/
│       └── auth.py            # Refactor to use registry
├── worker/
│   ├── sync/
│   │   ├── inventory.py       # Refactor to use registry, add pagination
│   │   ├── config.py          # No changes needed
│   │   ├── status.py          # Refactor to use registry
│   │   └── events.py          # Refactor to use registry, add pagination
│   ├── deploy/
│   │   ├── executor.py        # Fix call signature
│   │   ├── rollback.py        # Fix call signature
│   │   └── firmware.py        # Add SDK upgrade call
│   └── checks/
│       ├── pre_checks.py      # Fix method name, refactor to registry
│       ├── post_checks.py     # Fix method name, refactor to registry
│       └── drift.py           # Fix compute() -> compute_diff()

mist-ops-platform/tests/
└── unit/
    └── mist/                  # New/updated tests for all fixes
```

**Structure Decision**: No structural changes — all modifications are within the existing `mist-ops-platform/src/` layout. Tests added under the existing `tests/unit/` tree.

## Complexity Tracking

> One minor Five-Item Rule violation identified in post-design re-evaluation.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| MistEndpoint has 6 fields (5-field limit) | `list_method` field avoids creating 3 separate dataclass types (ReadEndpoint, WriteEndpoint, ListEndpoint) for a simple lookup table | Splitting into 3 dataclasses adds structural complexity to a data-only record; the 6th field defaults to None and is optional |
