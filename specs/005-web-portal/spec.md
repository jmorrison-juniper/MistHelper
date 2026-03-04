# Feature Specification: Web Portal Interface

**Feature Branch**: `005-web-portal`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "I would like to use gunicorn to create a web interface for our script so instead of using the CLI or SSHing in, a user can interact and view the results, and/or download the data from the web portal. The web interface needs to support the ENV file for portal styling. It needs to use CSS style sheets, with different themes contained within, that we can set the default using the ENV, but a user can change them within browser. Look into my other local or remote repositories for inspiration, especially mist sitedashboard."

## Assumptions

- **Web framework**: Flask served via Gunicorn (WSGI), following the same pattern as MistSiteDashboard, MistCircuitStats, and MistGuestAuthorizations
- **Coexistence with SSH**: The web portal runs alongside the existing SSH service in the container; both access the same MistHelper backend and data directory
- **Port**: Web portal defaults to port 8055 (already reserved in the container for the Dash map viewer; web portal replaces/coexists with Dash on this port)
- **Authentication**: No login/auth for the web portal in MVP. The portal is already behind corporate network / container access controls. Future feature if needed.
- **Non-destructive only**: The web portal only exposes data extraction operations (menus 1-89). Destructive operations (90-100) remain CLI/SSH-only for safety.
- **Existing data**: The portal reads from the existing `data/` directory (CSV files, SQLite database) and can trigger new data extraction operations
- **Theme persistence**: User theme preferences stored in browser localStorage (no server-side session for theme)
- **Bootstrap 5**: UI framework, consistent with MistSiteDashboard's NOC-optimized dark mode approach
- **Template pattern**: Flask Jinja2 templates with separate CSS stylesheets, following MistSiteDashboard file structure
- **Gunicorn workers**: Default 2-4 worker processes for concurrent request handling; configurable via ENV

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Download Existing Data (Priority: P1)

A NOC engineer opens the web portal in a browser and sees a dashboard showing available data exports (CSV files and SQLite tables). They can browse the data inline in sortable tables and download any file with a single click, without needing to SSH into the container or use the CLI.

**Why this priority**: This is the core value proposition — making data accessible without CLI expertise. Junior NOC engineers can self-serve data without learning SSH or command-line tools.

**Independent Test**: Navigate to the portal URL, verify available data files are listed, click a file to preview its contents in a table, click download to get the CSV/SQLite file.

**Acceptance Scenarios**:

1. **Given** the portal is running and data files exist in the `data/` directory, **When** a user navigates to the portal home page, **Then** they see a list of available data exports with file names, sizes, and last-modified timestamps
2. **Given** a CSV file exists in the data directory, **When** a user clicks to preview it, **Then** the data renders in a sortable, searchable HTML table with pagination
3. **Given** a user is viewing the data list, **When** they click the download button for any file, **Then** the file downloads to their browser with the original filename
4. **Given** the SQLite database exists, **When** a user selects it, **Then** they see a list of available tables and can preview any table's contents

---

### User Story 2 - Run Data Extraction Operations (Priority: P2)

A NOC engineer wants to extract fresh data from the Mist API. They select an operation from a categorized menu in the web portal, the operation runs in the background, and they see real-time progress. When complete, the results appear in the data browser for viewing and download.

**Why this priority**: This transforms the portal from a passive file viewer into an active tool, replacing the need for CLI interaction for routine operations.

**Independent Test**: Select menu operation 1 (List Org Sites), confirm it runs, verify output appears in the data browser when complete.

**Acceptance Scenarios**:

1. **Given** the portal is running with valid API credentials, **When** a user browses the operations menu, **Then** they see all non-destructive operations (1-89) organized by category (Data Extraction, WebSocket Commands, Packet Captures, etc.)
2. **Given** a user selects an operation, **When** the operation starts, **Then** they see a progress indicator showing the operation is running
3. **Given** an operation completes, **When** the user views the results, **Then** the output data is available for preview and download
4. **Given** an operation requires input parameters (e.g., site selection), **When** the user starts it, **Then** the portal presents the required inputs as form fields before execution

---

### User Story 3 - Theme Customization (Priority: P3)

A NOC engineer using the portal in a dark control room wants to switch between visual themes. The portal ships with multiple CSS themes (dark NOC, light office, high-contrast accessibility). The default theme is set via the ENV file, but each user can switch themes in their browser and the preference persists across sessions.

**Why this priority**: Usability and accessibility are important but not blocking. The portal is functional without theme switching.

**Independent Test**: Open the portal, observe the default theme matches the ENV setting, click the theme switcher, verify the UI changes immediately, refresh the page, confirm the selected theme persists.

**Acceptance Scenarios**:

1. **Given** the ENV file sets `PORTAL_THEME=dark`, **When** a user opens the portal for the first time, **Then** the dark theme is applied
2. **Given** a user is viewing the portal, **When** they click the theme switcher and select "light", **Then** all UI elements update to the light theme without a page reload
3. **Given** a user has selected a theme, **When** they close and reopen the browser, **Then** their theme preference is still applied
4. **Given** no theme is configured in the ENV file, **When** a user opens the portal, **Then** the default theme (dark) is applied

---

### User Story 4 - Portal Branding via ENV (Priority: P4)

An administrator deploying MistHelper for their organization wants to customize the portal's branding — title, logo, accent color — through the ENV file without modifying code. This supports white-label deployments across different teams or customers.

**Why this priority**: Branding is a deployment-time configuration concern, not critical for functionality but important for organizational adoption.

**Independent Test**: Set `PORTAL_TITLE`, `PORTAL_LOGO_URL`, and `PORTAL_ACCENT_COLOR` in the ENV file, start the container, verify the portal reflects the custom branding.

**Acceptance Scenarios**:

1. **Given** the ENV file sets `PORTAL_TITLE=ACME Network Ops`, **When** a user opens the portal, **Then** the page title and header display "ACME Network Ops"
2. **Given** the ENV file sets `PORTAL_LOGO_URL` to a valid image URL, **When** the portal loads, **Then** the custom logo appears in the header
3. **Given** the ENV file sets `PORTAL_ACCENT_COLOR=#FF6B35`, **When** the portal loads, **Then** buttons, links, and highlights use the custom accent color
4. **Given** no branding ENV variables are set, **When** the portal loads, **Then** the default MistHelper branding is displayed

---

### User Story 5 - Container Integration (Priority: P2)

The web portal runs inside the existing MistHelper container alongside the SSH service. Gunicorn serves the Flask app on a configurable port. The container build, health checks, and compose files are updated to support both services.

**Why this priority**: Without container integration, the portal cannot be deployed. This is a prerequisite for all other stories to function in production.

**Independent Test**: Build the container, run it, verify both SSH (port 2200) and web portal (port 8055) are accessible and functional.

**Acceptance Scenarios**:

1. **Given** the updated container is built, **When** it starts, **Then** both SSH on port 2200 and the web portal on the configured port are accessible
2. **Given** the container is running, **When** a user accesses the web portal, **Then** the portal can read data from the shared `data/` directory
3. **Given** the container is running, **When** the health endpoint is queried, **Then** it returns healthy status for both services
4. **Given** the ENV file configures `WEB_PORT=9000`, **When** the container starts, **Then** the web portal is available on port 9000 instead of the default

---

### Edge Cases

- What happens when a data extraction operation is already running and the user tries to start another? The portal shows the running operation status and prevents duplicate runs of the same operation.
- How does the portal handle very large CSV files (>100MB)? Preview paginates and limits rows displayed (first 1000 rows), while full download remains available.
- What happens when the Mist API credentials are missing or invalid? The portal displays a clear error message on the operations page and still allows browsing/downloading existing data files.
- What happens when the data directory is empty (fresh deployment)? The portal shows a friendly empty state with guidance to run a data extraction operation.
- How does the portal handle concurrent users? Gunicorn worker processes handle multiple simultaneous browser sessions. Operations use file locks to prevent duplicate concurrent runs of the same operation.
- What happens if the user's browser does not support localStorage? Theme falls back to the ENV default on each page load; no error is shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST serve a web interface via Gunicorn on a configurable port (default 8055)
- **FR-002**: System MUST list all data files (CSV, SQLite) in the `data/` directory with file metadata (name, size, last modified)
- **FR-003**: System MUST allow users to preview CSV file contents in a sortable, searchable HTML table with pagination
- **FR-004**: System MUST allow users to preview SQLite database tables in a sortable, searchable HTML table with pagination
- **FR-005**: System MUST allow users to download any data file directly from the browser
- **FR-006**: System MUST display non-destructive menu operations (1-89) organized by category
- **FR-007**: System MUST execute selected operations in the background and report completion status to the user
- **FR-008**: System MUST support multiple CSS themes (minimum: dark, light, high-contrast)
- **FR-009**: System MUST read the default theme from the ENV file (`PORTAL_THEME` variable)
- **FR-010**: System MUST allow users to switch themes in the browser without page reload
- **FR-011**: System MUST persist user theme selection in browser localStorage
- **FR-012**: System MUST support portal branding via ENV variables (`PORTAL_TITLE`, `PORTAL_LOGO_URL`, `PORTAL_ACCENT_COLOR`)
- **FR-013**: System MUST provide a health check endpoint (`/health`) for container orchestration
- **FR-014**: System MUST coexist with the existing SSH service in the same container
- **FR-015**: System MUST NOT expose destructive operations (menus 90-100) through the web interface
- **FR-016**: System MUST use external CSS stylesheets (not inline styles) for all theming
- **FR-017**: System MUST provide a CSV export/download button for any table displayed in the portal

### Key Entities

- **Data File**: A CSV or SQLite file in the `data/` directory; attributes include name, path, size, last-modified timestamp, and type (csv/sqlite)
- **Operation**: A MistHelper menu operation (1-89); attributes include number, name, category, description, required inputs, and current execution status (idle/running/completed/failed)
- **Theme**: A named CSS stylesheet defining the portal's visual appearance; attributes include name, display label, and CSS file path
- **Portal Configuration**: ENV-driven settings controlling branding and behavior; attributes include title, logo URL, accent color, default theme, and web port

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can browse and download data files within 3 clicks from the portal home page
- **SC-002**: A data extraction operation can be initiated and monitored entirely through the web portal without using SSH or CLI
- **SC-003**: Theme changes apply instantly (under 200ms perceived) without page reload
- **SC-004**: The portal renders correctly on desktop browsers (Chrome, Firefox, Edge) at 1920x1080 and 1366x768 resolutions
- **SC-005**: The container starts both SSH and web portal services within 10 seconds of launch
- **SC-006**: The portal handles 5 concurrent browser sessions without errors or data corruption
- **SC-007**: All ENV branding variables take effect without code changes — configuration only
- **SC-008**: CSV files up to 50MB can be previewed in the browser with pagination (first 1000 rows load in under 3 seconds)
