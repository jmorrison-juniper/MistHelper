# Feature Specification: Menu Entry Rows and Menu Dependency Factories

**Feature Branch**: `1704-menu-entry`

**Created**: 2026-09-14

**Status**: Implemented

**Input**: Replace the menu tuple with a `MenuEntry` dataclass and extract the repeated menu dependency blocks into factories.

## User Scenarios and Testing

### User Story 1 - Keep the menu table stable (Priority: P1)

An operator selects a menu number. MistHelper must dispatch the same operation as before.

**Why this priority**: A changed menu number can run a destructive operation when the operator expects a safe one.

**Independent Test**: Regenerate the menu reference and compare the row number, name, and category columns.

**Acceptance Scenarios**:

1. **Given** the current menu table, **When** the menu reference regenerates, **Then** no menu number changes.
2. **Given** the current menu table, **When** the menu reference regenerates, **Then** no menu name changes.
3. **Given** the current menu table, **When** the menu reference regenerates, **Then** no menu category changes.

### User Story 2 - Replace tuple rows with named rows (Priority: P1)

A maintainer reads a menu row. The row must show each field by name.

**Why this priority**: Tuple positions hide the meaning of the handler and text fields.

**Independent Test**: Unit tests assert that all rows are `MenuEntry` instances.

**Acceptance Scenarios**:

1. **Given** the runtime menu table, **When** a test reads each row, **Then** each value is a `MenuEntry`.
2. **Given** the runtime menu table, **When** a caller needs the handler, **Then** it reads `handler`.
3. **Given** the runtime menu table, **When** a caller needs the menu text, **Then** it reads `title`.

### User Story 3 - Centralize repeated dependency blocks (Priority: P2)

A maintainer changes a shared dependency for site export, routing, or gateway template work. The maintainer must edit one factory.

**Why this priority**: Repeated dependency blocks can drift when one copy changes and another copy does not.

**Independent Test**: Text counts show one `SiteExportUtils(` block, one `RoutingDeps(` block, and one `GatewayTemplateConfigManager(` block.

**Acceptance Scenarios**:

1. **Given** the site export menu rows, **When** a row runs, **Then** the row builds `SiteExportUtils` through one factory.
2. **Given** the routing menu rows, **When** a row runs, **Then** the row builds `RoutingUtils` through one factory.
3. **Given** the gateway template menu rows, **When** a row runs, **Then** the row builds `GatewayTemplateConfigManager` through one factory.

### Edge Cases

- An unknown menu number fails closed in direct interactive mode.
- A non-numeric selection fails closed in direct interactive mode.
- An empty selection prints a retry prompt and does not exit.
- The destructive range boundaries keep the exact flag value.

## Requirements

### Functional Requirements

- **FR-001**: `menu_actions` MUST hold `MenuEntry` values. This criterion belongs to issue #1705.
- **FR-002**: Each menu row MUST expose `menu_id`, `handler`, `title`, `category`, `destructive`, and `supports_fast`. This criterion belongs to issue #1705.
- **FR-003**: The systematic test runner MUST read `supports_fast` from the row. It MUST NOT inspect the handler signature for fast mode. This criterion belongs to issue #1705.
- **FR-004**: Interactive and portal call sites MUST read `handler` and `title` by name. This criterion belongs to issue #1705.
- **FR-005**: The `destructive` flag MUST match the required destructive set: 154 through 187, 189 through 191, 194, and 206 through 208. This criterion belongs to issue #1705.
- **FR-006**: The count of `DESTRUCTIVE:` text markers in `MistHelper.py` MUST stay unchanged. This criterion belongs to issue #1705.
- **FR-007**: `SiteExportUtils` dependency wiring MUST appear one time. This criterion belongs to issue #1704.
- **FR-008**: `RoutingDeps` dependency wiring MUST appear one time. This criterion belongs to issue #1704.
- **FR-009**: `GatewayTemplateConfigManager` dependency wiring MUST appear one time. This criterion belongs to issue #1704.
- **FR-010**: The refactor MUST preserve EOF-safe input behavior. This criterion belongs to issue #1705.

### Key Entities

- **MenuEntry**: One immutable menu row. It contains the dispatch key, the callable, display text, safety category, destructive flag, and fast-mode flag.
- **SiteExportUtilsFactory**: A factory class under `GlobalImportManager`. It builds `SiteExportUtils` with the shared dependency set.
- **RoutingUtilsFactory**: A factory class under `GlobalImportManager`. It builds `RoutingUtils` with the shared dependency set.
- **GatewayTemplateConfigManagerFactory**: A factory class under `GlobalImportManager`. It builds the gateway template manager with the shared dependency set.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The menu table has 268 rows after the refactor.
- **SC-002**: The exact destructive flag set has 41 rows.
- **SC-003**: `SiteExportUtils(` count moves from 12 to 1.
- **SC-004**: `RoutingDeps(` count moves from 3 to 1.
- **SC-005**: `GatewayTemplateConfigManager(` count moves from 3 to 1.
- **SC-006**: `DESTRUCTIVE:` marker count stays 28 before and after.
- **SC-007**: The menu reference changes only the code expression column for 18 rows.
- **SC-008**: `tools.symbol_diff` reports no module-level name change in `MistHelper.py`.

## Assumptions

- The active base is `origin/main`, not the diverged local `main`.
- The menu category remains from `OperationRegistry`.
- The new `destructive` field records the production-destructive operation set that the issue names.
- The web portal static menu rows can hold `handler=None`, because that path lists metadata only.
