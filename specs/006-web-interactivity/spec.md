# Feature Specification: Web Portal Interactivity

**Feature Branch**: `006-web-interactivity`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: "Why can't we support interactive? That's like, the majority of the point of this program. Please add this capability. Also the preview button is worthless, we need to either get rid of it, or make it so it gives a popup viewer to view the data within the file without leaving the current page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Interactive Operations from the Browser (Priority: P1)

A NOC engineer opens the web portal Operations page and selects an interactive operation (e.g., Menu 71 — "View device inventory for a selected site"). Instead of seeing an error ("Operation requires interactive input"), the portal presents a guided form: first a site selector dropdown populated from the organization's sites, then (if the operation requires it) a device selector dropdown populated from that site's devices. The engineer makes their selections, clicks Run, and sees the operation execute with real-time progress in the Execution Log — just like non-interactive operations already work.

This covers the ~35 interactive operations (menus 5-10, 29-34, 49-53, 68-74, 80-81, 84-89 interactive; 62, 79 CLI-only) that currently fail in the web portal. These operations represent the majority of MistHelper's value — site-specific data extraction, device diagnostics, packet captures, and WebSocket commands.

**Why this priority**: Without interactive support, the web portal can only run ~25 org-wide bulk exports. The remaining ~35 operations (site/device-specific) are the primary reason NOC engineers use MistHelper. This is the core gap.

**Independent Test**: Navigate to Operations page, select Menu 71 (View device inventory for a selected site), see a site dropdown appear, select a site, click Run, and see inventory results appear in the Execution Log.

**Acceptance Scenarios**:

1. **Given** the user selects an interactive operation (e.g., Menu 31 — site devices), **When** the operation detail panel loads, **Then** a site selector dropdown appears populated with all organization sites (names and IDs).
2. **Given** the user has selected a site in the dropdown, **When** the operation also requires a device selection, **Then** a second dropdown appears populated with devices from that site.
3. **Given** the user has filled all required parameter fields, **When** they click Run, **Then** the operation executes with their selections pre-applied (no interactive prompts during execution), and real-time log output appears in the Execution Log.
4. **Given** the user selects a packet capture operation (Menu 9), **When** the parameter panel loads, **Then** additional fields appear for capture type, duration, packet count, and filter options — all as form controls instead of text prompts.
5. **Given** the user runs an interactive operation that completes successfully, **When** the operation finishes, **Then** any output files appear as downloadable links and are visible in the Data Browser.

---

### User Story 2 - Modal Data Preview (Priority: P1)

A NOC engineer is on the Data Browser page (or on the Operations page viewing results). They click a Preview button next to a CSV file. Instead of being navigated away or seeing a cramped inline panel that pushes content around, a full-screen modal overlay appears showing the file contents in a sortable, searchable, paginated table. The engineer can browse the data, search for specific rows, export the view as CSV, and close the modal to return exactly where they were — no page navigation, no lost context.

This also applies to JSON, LOG, and SQLite files. SQLite files show a table list in the modal, and clicking a table name shows that table's contents within the same modal.

**Why this priority**: Equal to US1. The current preview panel is an inline div that disrupts the page layout, is easy to miss, and provides a poor experience. A modal is the standard pattern for previewing content without losing context.

**Independent Test**: Go to Data Browser, click Preview on a CSV file, see a full-screen modal with sortable table, search within it, close it, confirm the page state is unchanged.

**Acceptance Scenarios**:

1. **Given** the user is on the Data Browser page, **When** they click Preview on a CSV file, **Then** a modal overlay appears covering the full viewport with the file contents displayed as a sortable, searchable table.
2. **Given** the preview modal is open, **When** the user types in the modal search box, **Then** the table filters to matching rows in real time.
3. **Given** the preview modal is open, **When** the user clicks a column header, **Then** the table sorts by that column (ascending/descending toggle).
4. **Given** the preview modal is open showing a large file, **When** the user scrolls through pages, **Then** pagination controls (Previous/Next/page number) navigate through the data without closing the modal.
5. **Given** the preview modal is open, **When** the user clicks "Export CSV," **Then** the currently visible/filtered data downloads as a CSV file.
6. **Given** the preview modal is open, **When** the user clicks Close (or presses Escape, or clicks outside the modal), **Then** the modal closes and the underlying page is exactly as it was.
7. **Given** the user clicks Preview on a SQLite database file, **When** the modal opens, **Then** it shows a list of tables with row counts; clicking a table name loads that table's content into the same modal.
8. **Given** the user clicks Preview on a JSON or LOG file, **When** the modal opens, **Then** the content is displayed in a readable format (formatted JSON or log lines).

---

### User Story 3 - Operation Results Preview in Modal (Priority: P2)

After a NOC engineer runs an operation from the Operations page and it completes, the output files list appears. The engineer clicks Preview on one of the output files and sees the same modal data viewer (from US2) showing the operation results — without navigating to the Data Browser page.

**Why this priority**: Bridges the gap between running operations and viewing results. Lower priority because the Data Browser modal (US2) must exist first.

**Independent Test**: Run operation 11 (List Sites), wait for completion, click Preview on the output CSV in the results area, see the modal with site data.

**Acceptance Scenarios**:

1. **Given** an operation has completed with output files listed, **When** the user clicks Preview on an output file, **Then** the modal data viewer opens showing that file's contents.
2. **Given** the modal is showing operation results, **When** the user closes it, **Then** they return to the Operations page with the Execution Log still visible.

---

### Edge Cases

- What happens when the site list is empty (new org with no sites)? The site dropdown shows an empty state message: "No sites found in this organization."
- What happens when a device list is empty (site with no devices of the required type)? The device dropdown shows: "No devices found at this site."
- What happens when preview is clicked on an extremely large CSV (100K+ rows)? The modal loads paginated data (first 50 rows) with server-side pagination, preventing browser memory issues.
- What happens when the user clicks Run without selecting a required parameter? The Run button remains disabled until all required fields are filled, with clear visual indicators on missing fields.
- What happens when a parameter API call fails (e.g., site list fetch times out)? An error message appears in the parameter area with a Retry button.
- What happens when the user clicks Preview on a corrupt or empty file? The modal shows a friendly error: "Unable to preview this file" with the option to download it instead.
- What happens when an interactive operation has many sequential prompts (e.g., packet capture with ~15 inputs)? All parameters are presented as a single form before execution — the user fills everything out, then clicks Run once.

## Requirements *(mandatory)*

### Functional Requirements

**Interactive Operations:**

- **FR-001**: System MUST present parameter input forms for interactive operations instead of failing with an error message.
- **FR-002**: System MUST provide a site selector control populated with all organization sites (name and ID) for operations that require site selection.
- **FR-003**: System MUST provide a device selector control that dynamically populates based on the selected site, filtered by device type (AP, switch, gateway) as required by the operation.
- **FR-004**: System MUST provide appropriate form controls for all interactive parameters (dropdowns for selections, number inputs for durations/counts, dropdowns with Yes/No options for binary choices, text fields for free-form input like MAC addresses).
- **FR-005**: System MUST inject user-selected parameter values into the operation execution context so that input prompts receive the pre-filled answers without user interaction during execution.
- **FR-006**: System MUST keep the Run button disabled until all required parameters are populated, with visual indicators on unfilled required fields.
- **FR-007**: System MUST continue to block destructive operations (menu 90+) from web portal execution regardless of parameter support.
- **FR-008**: System MUST mark truly interactive operations (free-form CLI sessions, continuous loops) as "CLI-only" with a message directing users to SSH access.

**Modal Data Preview:**

- **FR-009**: System MUST display file previews in a full-viewport modal overlay instead of an inline panel.
- **FR-010**: Modal MUST support CSV files with sortable columns, searchable rows, pagination, and CSV export.
- **FR-011**: Modal MUST support SQLite files by showing a table list first, then table contents when a table is selected.
- **FR-012**: Modal MUST support JSON and LOG files with formatted display.
- **FR-013**: Modal MUST close via close button, Escape key, or clicking outside the modal area.
- **FR-014**: Modal MUST preserve the underlying page state when opened and closed (no navigation, no scroll position loss).
- **FR-015**: System MUST provide preview capability from both the Data Browser page and the Operations page (output files after completion).

### Key Entities

- **Operation Parameter**: A named input that an interactive operation requires before execution. Has a type (site, device, client, text, number, choice), an optional dependency (e.g., device depends on site), and validation rules. Yes/no options use the `choice` type with two static options.
- **Parameter Form**: The collection of all parameters required by a specific operation, rendered as a web form in the operation detail panel.
- **Preview Modal**: A full-viewport overlay component that displays file contents with search, sort, pagination, and export capabilities.
- **Site**: An organizational grouping with a name and UUID, fetched from the Mist API or cached data. Used as the primary parameter for most interactive operations.
- **Device**: A network device (AP, switch, gateway) belonging to a site, identified by MAC address and name. Used as a secondary parameter filtered by site and device type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All ~35 interactive operations (menus 5-10, 29-34, 49-53, 68-74, 80-81, 84-89) can be executed from the web portal without errors, compared to zero today. CLI-only operations (62, 79) show a message directing users to SSH.
- **SC-002**: Users can complete any interactive operation (select parameters and run) in under 60 seconds, matching the CLI experience.
- **SC-003**: File preview opens in under 2 seconds for files up to 10MB, displaying the first page of results.
- **SC-004**: Users can preview, search, and export data without navigating away from their current page.
- **SC-005**: 100% of file types currently listed in the Data Browser (CSV, JSON, LOG, SQLite) are previewable through the modal.
- **SC-006**: The parameter form correctly maps all required inputs for every interactive operation — no operation fails due to missing or mistyped parameters.

## Assumptions

- **Site list caching**: The site list will be fetched from the existing cached data or the Mist API. The web portal will expose an endpoint that returns the site list for dropdown population.
- **Device list**: Device lists will be fetched per-site from the Mist API. The web portal will expose an endpoint that returns devices filtered by type for a given site.
- **Input injection mechanism**: Rather than modifying every input call in the main codebase, the system will use a thread-local input queue to intercept input calls and provide pre-filled responses from the web form. This avoids touching the main application code extensively.
- **Parameter discovery**: Operation parameter requirements will be defined in a configuration mapping (operation number to list of required parameters with types), maintained in the web portal codebase. This is a one-time manual mapping effort based on the ~35 interactive operations.
- **Modal component**: The preview modal will use the modal component already bundled as a vendor asset, requiring no additional dependencies.
- **CLI-only operations**: Operations 62 (Troubleshoot) and 79 (CLI Shell) are truly interactive (free-form ongoing input, not pre-fillable parameters). They will be marked as "CLI-only" with a clear message explaining they require SSH access. Operations 75-78 are non-interactive and already work without parameters. All other interactive operations use predictable, pre-fillable parameter patterns.
- **Packet capture operations (9-10)**: These have the most parameters (~15 inputs) but all are pre-fillable (dropdowns, numbers, Yes/No choice dropdowns). They will render as a multi-section form.
