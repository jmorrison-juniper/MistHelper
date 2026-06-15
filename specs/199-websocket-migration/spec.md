# Feature Specification: WebSocket Migration to `mistapi.websockets`

**Feature Branch**: `199-websocket-migration`
**Created**: 2026-06-11
**Status**: Draft
**Input**: Replace MistHelper's ~3,008-line custom WebSocket stack (`src/websocket/`) and the in-line `PacketCaptureManager` class with the upstream `mistapi.websockets` SDK (v0.59+), preserving the user-visible behavior of menu operations 102–123.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - NOC engineer runs show commands via menu 102–115 (Priority: P1)

A NOC engineer launches MistHelper, selects a "show ..." menu operation (e.g., menu 102 `show version`), picks an org/site/device, and expects identical prompts, identical output formatting, and identical CSV/log artifacts as the current custom implementation — but the underlying transport is `mistapi.websockets.DeviceCmdEvents`.

**Why this priority**: Show commands are the most-used WebSocket operations in daily NOC workflow. Behavioral parity here is the contract that gates the entire migration.

**Independent Test**: For each menu op 102–115, run against a known device, capture stdout + generated files, diff against the equivalent run from `main` before migration. Zero functional differences in prompts, columns, file names, or exit behavior.

**Acceptance Scenarios**:

1. **Given** the operator runs menu 102 against an AP, **When** the WebSocket completes, **Then** the same CSV (same columns, same row data) is written to `data/` and the same console summary is printed.
2. **Given** the Mist WebSocket drops mid-command, **When** the operator is using a migrated menu op, **Then** `mistapi.websockets` auto-reconnect transparently recovers and the operation completes without operator intervention (improvement over current behavior, but must not change displayed prompts).
3. **Given** the operator cancels with Ctrl-C during a show command, **When** the WebSocket is active, **Then** the session closes cleanly with no orphaned threads or leaked sockets.

---

### User Story 2 - NOC engineer runs diagnostics via menu 116–123 (Priority: P1)

Diagnostic operations (ping, arp, traceroute, shell, bgp summary, ospf neighbors, etc.) are dispatched through `mistapi.device_utils` (which internally uses `mistapi.websockets`), replacing the custom `MessageRouter` / `ResultCollector` flow.

**Why this priority**: Diagnostics are the second-largest WebSocket surface and the highest-value beneficiary of upstream `UtilResponse` auto-WS handling. Required for full removal of `src/websocket/`.

**Independent Test**: For each menu op 116–123, run against an AP/EX/SRX/SSR device, capture stdout + artifacts, diff against the equivalent run before migration. Zero functional differences in prompts, formatting, or files.

**Acceptance Scenarios**:

1. **Given** a ping diagnostic (menu 117) targeting `1.1.1.1` from an AP, **When** invoked, **Then** the operator sees the same prompts, the same line-by-line ping output, and the same final summary as before migration.
2. **Given** a long-running shell command (menu 122) on an EX switch, **When** the WebSocket exceeds the upstream default timeout, **Then** the migrated code surfaces a clear error message matching today's wording.
3. **Given** the operator runs a BGP summary on an SRX/SSR (menu 120), **When** the command completes, **Then** the CSV/text output is byte-identical to the pre-migration version (modulo timestamp fields).

---

### User Story 3 - Maintainer deletes the legacy `src/websocket/` package (Priority: P2)

After every menu op 102–123 is migrated and validated, the maintainer deletes `src/websocket/` (10+ files, ~3,008 lines) and the `PacketCaptureManager` WebSocket handling code inside `MistHelper.py`, then runs the full test suite and confirms no regressions.

**Why this priority**: The maintenance-surface reduction is the headline benefit. Cannot ship until P1 stories are complete, but is the explicit end-state.

**Independent Test**: After deletion, `python -m py_compile MistHelper.py` passes, `ruff check` passes, `pytest` passes, and menu ops 102–123 still behave per User Story 1 and 2 acceptance scenarios.

**Acceptance Scenarios**:

1. **Given** all migrations are complete, **When** `src/websocket/` is removed, **Then** no import in the repo references it (`grep -r "from src.websocket"` returns zero matches outside archived specs).
2. **Given** the legacy package is gone, **When** the test suite runs, **Then** unit + integration coverage of the WebSocket-using code paths is ≥ 70 %.

---

### User Story 4 - Operator benefits from upstream resilience features (Priority: P3)

By replacing the bespoke implementation, operators get auto-reconnect, bounded queues (no unbounded memory growth on a hung consumer), and authorization-header redaction in logs — all for free from upstream.

**Why this priority**: These are quality-of-life wins, not migration blockers. They land automatically once P1 and P2 ship.

**Independent Test**: Verify in code review that no MistHelper-side code re-implements reconnect, queue management, or log redaction for WebSocket traffic — all delegated to `mistapi.websockets`.

**Acceptance Scenarios**:

1. **Given** a transient network blip during a long show-command session, **When** the operator is using a migrated op, **Then** the session recovers without operator action and without losing already-emitted output.
2. **Given** debug logging is enabled, **When** WebSocket headers are logged, **Then** the `Authorization` token is redacted (delivered by upstream).

---

### Edge Cases

- **WebSocket auth fails** (expired API token): operator sees the same actionable error message as today; no stack trace.
- **Device offline / not subscribed**: `mistapi.websockets` raises a typed error; adapter translates to the same operator-facing message as today.
- **Mixed device types** in a multi-target operation (AP + EX + SRX): each device's session is dispatched to the correct `mistapi.device_utils` helper without breaking on the heterogeneous batch.
- **Partial migration window**: while migrations are in flight, both code paths coexist; the adapter layer ensures menu dispatch routes each op to the correct implementation, with no silent fallthrough.
- **Concurrent menu ops** (e.g., scripted via `--menu`): each op gets its own WebSocket session; no shared mutable state between calls.
- **Ctrl-C during reconnect**: operator interrupt cancels cleanly even if upstream is mid-reconnect attempt.
- **Upstream API change** between `mistapi` minor versions: pinning + the adapter layer's narrow surface keep the blast radius to one file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route menu operations 102–115 (show commands) through `mistapi.websockets.DeviceCmdEvents` instead of `src/websocket/WebSocketManager`.
- **FR-002**: System MUST route menu operations 116–123 (diagnostics: ping, arp, traceroute, shell, bgp, ospf, etc.) through `mistapi.device_utils` helpers, which internally use `mistapi.websockets`.
- **FR-003**: System MUST preserve every operator-visible prompt verbatim — wording, ordering, default values, and confirmation strings unchanged.
- **FR-004**: System MUST preserve every output artifact (CSV columns, file names, log formats, console summaries) byte-identical to pre-migration behavior, excluding fields that are inherently time-varying (timestamps, RTT values, sequence numbers).
- **FR-005**: System MUST expose a thin adapter layer (single module, well-defined surface) between MistHelper menu code and `mistapi.websockets`, so menu-op call sites do not import upstream classes directly.
- **FR-006**: System MUST migrate menu operations one at a time, with each migration shippable independently (no big-bang cutover).
- **FR-007**: System MUST keep both code paths functional during the migration window; the dispatcher MUST route per-op to either legacy or upstream based on a documented per-op flag or mapping.
- **FR-008**: System MUST delete `src/websocket/` (entire package) and the WebSocket handling code in the `PacketCaptureManager` class once all 22 ops are migrated and validated.
- **FR-009**: System MUST NOT reimplement reconnect, queue bounding, or header redaction on the MistHelper side — these are delegated to upstream.
- **FR-010**: System MUST surface upstream WebSocket errors with the same wording the operator sees today (the adapter normalizes exception types).
- **FR-011**: System MUST log every WebSocket lifecycle event (connect, message, reconnect, close, error) per the project's NON-NEGOTIABLE action-logging standard, even when delegating to upstream.
- **FR-012**: System MUST honor Ctrl-C interrupts cleanly during any WebSocket-backed operation, including during upstream reconnect attempts.
- **FR-013**: System MUST achieve ≥ 70 % unit + integration test coverage on the adapter layer and on each migrated menu-op dispatch path.
- **FR-014**: System MUST provide a regression-test harness that compares pre- and post-migration behavior per menu op (recorded fixtures or live mock server, whichever the test plan in `plan.md` selects).
- **FR-015**: System MUST update `CHANGELOG.md`, `README.md` operation counts (unchanged but verify), and the architecture mindmap to reference `mistapi.websockets` instead of the deleted package.

### Key Entities

- **Adapter Layer**: A single Python module that wraps `mistapi.websockets.DeviceCmdEvents`, `DeviceEvents`, `DeviceStatsEvents`, and the relevant `mistapi.device_utils` helpers. Exposes MistHelper-friendly call signatures and translates upstream exceptions to the operator-facing error messages already in use.
- **Menu Dispatcher Mapping**: A table that records, for each of the 22 menu ops (102–123), the upstream entry point, the adapter function, and the migration status (legacy / migrated). Used by the dispatcher during the transition window and removed once migration is complete.
- **Regression Fixtures**: Recorded pre-migration outputs (stdout, CSVs, log lines) for each menu op, used by the test harness to verify byte-identical post-migration behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 22 menu operations (102–123) execute end-to-end via `mistapi.websockets` / `mistapi.device_utils` with zero functional differences from pre-migration output (excluding inherently time-varying fields).
- **SC-002**: Total lines of WebSocket-related code in MistHelper shrink by ≥ 2,800 lines (from ~3,008 to ≤ 200 in the adapter layer).
- **SC-003**: `src/websocket/` package is deleted from the repository (`git ls-files src/websocket/` returns empty).
- **SC-004**: Unit + integration test coverage on the adapter layer and migrated dispatch paths is ≥ 70 %.
- **SC-005**: Operator-visible failure rate on WebSocket operations under transient network conditions improves (measured by manual scenario test: simulate a 5-second network drop during a show command and confirm the migrated op recovers where the legacy op would fail).
- **SC-006**: Migration ships incrementally: at least 4 separate PRs (adapter scaffolding, show-commands batch, diagnostics batch, legacy-deletion), each independently mergeable and revertable.
- **SC-007**: After migration, `grep -r "from src.websocket"` in `MistHelper.py` and `src/` returns zero matches.
- **SC-008**: CodeQL, Bandit, ruff, mypy, and pytest all pass on the final post-deletion commit.

## Assumptions

- **Upstream stability**: `mistapi.websockets` (v0.59+) is API-stable and provides the documented `DeviceCmdEvents`, `DeviceEvents`, `DeviceStatsEvents`, and `device_utils` surface. Source: `docs/UPSTREAM_mistapi_changes.md`.
- **Behavioral parity is the contract**: operators must see no change in prompts or output. Performance improvements and resilience gains are non-goals to advertise but welcome to deliver.
- **Existing MVP adapter**: prior exploratory work has produced an early adapter layer; this spec formalizes and completes that work rather than starting from scratch.
- **Test environment**: a real Mist org with at least one AP, one EX switch, and one SRX/SSR gateway is available for regression validation. Where live devices are not available, recorded fixtures are an acceptable substitute.
- **Non-goals (explicit)**:
  - Not rewriting menu UX or prompts.
  - Not changing CSV column layouts.
  - Not consolidating menu ops 102–123 into fewer ops.
  - Not introducing new menu ops as part of this work.
  - Not back-porting to MistHelper-Go in the same change (Python-first, per project rule).
- **Migration window coexistence**: legacy and upstream code paths run side-by-side during the transition; both paths share fixtures and the dispatcher selects per-op. This is acceptable temporary tech debt.
- **Dependency pin**: `mistapi` version is pinned in `requirements.txt` to a known-good release; any upstream upgrade during migration triggers a re-validation sweep.
- **No schema/database changes**: migration is purely transport-layer; no `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries change and no SQLite migrations are required.
- **Container rebuild required**: post-merge follows the standard mandatory deployment pipeline (validate → commit → push → workflow → pull → restart).
