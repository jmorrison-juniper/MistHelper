# Implementation Plan: Remove Deprecated Mist Edge WebSocket Channels

**Branch**: `fix/3737-remove-deprecated-mxedges` | **Date**: 2026-10-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/3737-remove-deprecated-mxedges/spec.md`

## Summary

Remove the `org.mxedges` and `site.mxedges` rows from the frozen WebSocket channel catalog.
Keep the `org.stats.mxedges` and `site.stats.mxedges` rows, including their identifier fields and
`stats/mxedges` path templates. Update only the direct catalog verification that currently expects
18 rows or parity with deprecated SDK event classes.

The catalog is implemented by `ChannelCatalog` in
`src/mist/realtime/websocket_streams/catalog/channels.py`. It builds immutable
`ChannelDefinition` records from `_ROWS`, indexes them by key, and returns `None` for unknown
keys. Removing two rows therefore preserves lookup, path construction, page order, and all other
channels without a new abstraction.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi` 0.64.x for public WebSocket channel parity checks, plus the
existing `ChannelCatalog` and `ChannelDefinition` classes.

**Storage**: None. The change affects an in-memory catalog only.

**Testing**: `pytest` unit and contract tests under `tests/unit/websocket_streams/catalog/` and
`tests/contract/websocket_streams/`. Use synthetic identifiers and do not open a WebSocket.

**Target Platform**: Windows, macOS, Linux, and the existing portal container.

**Project Type**: Python CLI and web portal support library.

**Performance Goals**: Preserve current constant-time key lookup and immutable tuple storage.

**Constraints**: Change only the channel catalog and direct verification. Do not change Mist Edge
REST operations, statistics data handling, utility discovery, transport code, or unrelated tests.

**Scale/Scope**: Remove two rows from one catalog table and adjust focused catalog assertions.
The resulting catalog must contain 16 channel entries in the existing relative order.

## Constitution Check

*GATE: Must pass before implementation. Re-check after the design in this plan.*

### Principle I: Five-Item Rule

- **PASS** -- The plan edits one existing module and its direct tests. It adds no hierarchy level.
- **PASS** -- The catalog constructor and lookup methods remain unchanged.
- **PASS** -- The row removal does not add a function, class, parameter, or expression block.
- **Debt recorded** -- Existing catalog modules contain more than five definitions and existing
  test modules contain multiple test functions. This plan does not increase either count.
- **Remediation** -- Track existing hierarchy debt in a later structural maintenance issue. Do not
  expand this issue beyond the two deprecated rows.

### Principle II: Class-Based Architecture

- **PASS** -- `ChannelCatalog` remains the owner of channel definitions and lookups.
- **PASS** -- No wrapper, alias, adapter, or fallback path is introduced.

### Principle III: Safety-First

- **PASS** -- The change removes unsupported selectable streams before any request can build a
  deprecated path.
- **PASS** -- Verification uses synthetic UUID values and no Mist credential or live connection.
- **PASS** -- Retained statistics entries keep their existing required identifier fields.

### Principle IV: Full Deployment Pipeline

- **PASS for this planning change** -- Only `specs/3737-remove-deprecated-mxedges/plan.md` is
  created. No production code or test file is changed in this phase.
- **Implementation gate** -- The later implementation must run focused tests, formatting, lint,
  and the repository gates that apply to the changed Python files before commit.

### Principle V: Observability and Logging

- **PASS** -- No runtime action or log statement changes.

### Principle VI: Inline Comments

- **PASS** -- No executable code changes are planned.

### Principle VII: Action Logging

- **PASS** -- No new action, request, output, or persistence operation is planned.

## Research and Design Findings

### Existing architecture

1. `ChannelCatalog._ROWS` is the single source of truth for the 18 channel definitions.
2. Each row stores the key, scope, display text, description, path template, identifier fields,
   and repeatable field.
3. `ChannelCatalog.__init__` converts rows to frozen `ChannelDefinition` records and creates a
   key lookup map.
4. `ChannelCatalog.get()` already returns `None` for an absent key, so removed keys need no
   special branch.
5. `ChannelDefinition.build_paths()` formats checked identifiers into the retained statistics
   paths.
6. `StreamCatalog.page_payload()` exposes channel metadata without exposing path templates.

### Existing verification

1. `tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py` asserts the current count,
   page endpoints, repeatable path behavior, and unknown-key behavior.
2. `tests/contract/websocket_streams/test_ws_channel_parity.py` maps catalog keys to public SDK
   channel classes and currently includes both deprecated event classes.
3. `tests/e2e/websockets_tab/dialog_audit/support/inventory.py` has an SDK-backed diagnostic map
   that currently names both deprecated event classes.
4. `tests/e2e/websockets_tab/dialog_audit/test_inventory.py` uses a broad minimum inventory count,
   so removal of two channel entries must not reduce the dynamic catalog below its existing
   safety checks.
5. `tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py` validates joined payload
   behavior without depending on the exact channel count.

### Planned implementation changes

1. Remove the `org.mxedges` row from `_ROWS`.
2. Remove the `site.mxedges` row from `_ROWS`.
3. Leave `org.stats.mxedges` immediately in its current relative position and retain
   `/orgs/{org_id}/stats/mxedges`.
4. Leave `site.stats.mxedges` immediately in its current relative position and retain
   `/sites/{site_id}/stats/mxedges`.
5. Update the focused unit test to expect 16 entries and to assert both removed lookups return
   `None`.
6. Add focused unit assertions for the retained organization and site statistics paths.
7. Remove deprecated event cases from the SDK parity test while retaining both statistics cases.
8. Review the dialog-audit SDK map and update it only if its catalog verification treats the
   deprecated SDK classes as required catalog entries. Do not remove the SDK classes themselves.

### Files in the implementation manifest

The later implementation may change only these direct surfaces:

```text
src/mist/realtime/websocket_streams/catalog/channels.py
tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py
tests/contract/websocket_streams/test_ws_channel_parity.py
tests/e2e/websockets_tab/dialog_audit/support/inventory.py
```

The implementation must not change `MistHelper.py`, Mist Edge REST modules, statistics handling,
WebSocket transport runners, utility catalogs, or generated documentation.

## Validation Plan

Run the focused tests after implementation:

```text
python -m pytest tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py
```

The focused assertions must prove all of the following:

- `ChannelCatalog().entries()` contains exactly 16 rows.
- The two removed keys are absent from the entry keys.
- `catalog.get("org.mxedges") is None`.
- `catalog.get("site.mxedges") is None`.
- The retained organization entry builds
  `/orgs/11111111-1111-4111-8111-111111111111/stats/mxedges`.
- The retained site entry builds
  `/sites/22222222-2222-4222-8222-222222222222/stats/mxedges`.
- The retained entries match `orgs.MxEdgesStatsEvents` and `sites.MxEdgesStatsEvents`.
- The first and last catalog keys, and all unaffected relative order, remain unchanged.

Then run the applicable repository checks:

```text
python -m ruff check src/mist/realtime/websocket_streams/catalog/channels.py tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py
python -m black --check src/mist/realtime/websocket_streams/catalog/channels.py tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py
```

No live Mist credential, production WebSocket, container, REST call, or database is required.

## Project Structure

### Documentation

```text
specs/3737-remove-deprecated-mxedges/
└── plan.md
```

This planning request intentionally creates no `research.md`, `data-model.md`, `quickstart.md`,
`contracts/`, or `tasks.md` because the user requested only `plan.md`.

### Source Code

```text
src/mist/realtime/websocket_streams/catalog/
├── channels.py       # Frozen channel row table and key lookup.
├── model.py          # ChannelDefinition and path construction.
└── registry/
    └── stream_catalog.py  # Joined page payload and lookup boundary.

tests/unit/websocket_streams/catalog/
└── test_ws_channel_catalog.py  # Count, order, lookup, and path tests.

tests/contract/websocket_streams/
└── test_ws_channel_parity.py  # Public SDK path parity tests.
```

**Structure Decision**: Keep the existing catalog architecture. Remove only the two deprecated
rows and adjust direct verification at the existing unit and contract boundaries.

## Complexity Tracking

No constitution exceptions are required. The change removes data from an existing immutable table
and does not add a function, class, module, dependency, or runtime branch.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | Not applicable | Not applicable |

## Post-Design Constitution Re-Check

- **Principle I**: PASS. The plan removes two existing rows and does not increase hierarchy debt.
- **Principle II**: PASS. `ChannelCatalog` remains the sole owner of catalog definitions.
- **Principle III**: PASS. Deprecated paths become unresolvable, while retained identifiers remain
  validated by the existing request path.
- **Principle IV**: PASS for the planned scope. Implementation validation is listed explicitly.
- **Principle V**: PASS. Runtime logging remains unchanged.
- **Principle VI**: PASS. No new executable code is introduced by the plan.
- **Principle VII**: PASS. No new meaningful runtime action is introduced.

**Post-Design Gate**: PASS. The design is ready for task generation and implementation.
