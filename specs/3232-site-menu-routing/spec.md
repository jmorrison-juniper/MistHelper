# Feature Specification: Keep the site menu and the store plumbing out of the Execution Log

**Feature Branch**: `fix/3232-site-menu-routing` | **Created**: 2026-09-23 | **Status**: Implemented

**Input**: Issue #3232. "Every site-scoped run prints the 143-line site menu into the Execution Log."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site-scoped run shows its result, not the site menu (Priority: P1)

A NOC engineer picks a site from the pick list and runs menu 69. The Execution Log shows the WLAN export. It does not show the 143-line command-line site menu that the pick list already answered, and it does not show the database lines of the site cache refresh.

**Acceptance Scenarios**:

1. **Given** a site-scoped run, **When** the Execution Log renders, **Then** it holds no `Available Sites:` heading and no `[N] SiteName` row.
2. **Given** the same run, **When** the refresh writes the polyglot store, **Then** no `src.db`, `redis_writer`, or `redis_json_writer` INFO line and no `Polyglot write:` or `Polyglot DatabaseRouter initialized` line appears.
3. **Given** a site name that does not match, **When** the prompt logs `Site not found by name or index`, **Then** that line appears.
4. **Given** a database warning, **When** the log renders, **Then** the warning appears.

## Requirements *(mandatory)*

- **FR-001**: The portal MUST route the site menu heading and rows of `src.ui.prompt_utils` to the debug channel.
- **FR-002**: The portal MUST route INFO lines of the polyglot store to the debug channel, and it MUST keep every WARNING visible.
- **FR-003**: A numbered line from any other logger MUST stay in the Execution Log.
- **FR-004**: A test MUST fail when the menu calls in the source change shape.

## Out of scope

- The site list refresh on every site prompt. The perf agent owns that cost. The refresh lines that name `SiteList` stay visible, because for menu 1 they are the result.
