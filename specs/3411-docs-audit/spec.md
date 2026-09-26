# Feature Specification: Correct the documents and map each menu option to its Mist API endpoints

**Issue**: #3411
**Feature Branch**: `feat/3411-docs-audit`
**Status**: Draft
**Requested by**: the repository owner on 2026-09-26

## Problem

The README, the wiki, and the internal documents state old counts, old paths,
and old class names. The wiki home page states 209 operations. The registry
holds 270 entries. The agent instructions state that `MistHelper.py` has 6,054
lines. The file has 8,071 lines. Several Mermaid diagrams show classes and flows
that the code no longer has.

No document tells a reader which Mist API endpoints a menu option calls. A
developer who wants to copy a pattern must read the code of each handler.

## User Story 1 (P1): An operator reads a correct README and a correct wiki

**Why this priority**: The README and the wiki are the first pages that a new
NOC engineer reads. A wrong count or a wrong path costs trust at once.

**Independent test**: Compare each count, path, port, and command in the README
and the wiki with the tree.

**Acceptance scenarios**:

1. **Given** the README and the wiki pages, **When** a reader compares a count
   with `src/utils/operation_registry.py`, **Then** the count agrees.
2. **Given** a path, a port, or a command in a page, **When** the reader looks
   for it in the tree, `compose.yml`, or the argument parser, **Then** it
   exists.

## User Story 2 (P1): A developer finds the endpoints of each menu option

**Why this priority**: The owner asked for this map by name. Other engineers
use it as a set of examples for the Mist API.

**Independent test**: Open the map, pick five menu options, and compare each
row with the handler code.

**Acceptance scenarios**:

1. **Given** the map index, **When** a developer opens a category page,
   **Then** each menu option of that category shows its handler, its SDK
   functions, the HTTP method and path of each function, and a link to the
   Juniper API document.
2. **Given** a category page, **When** the developer views it on GitHub,
   **Then** Mermaid diagrams show the menu options and their endpoints.
3. **Given** a menu option that calls no Mist API, **When** the developer reads
   its row, **Then** the row states that the analysis found no Mist API call.

## User Story 3 (P2): A maintainer reads correct architecture diagrams

**Independent test**: Run the Mermaid lint and the diagram reference lint, and
compare each named class and flow with the code.

**Acceptance scenarios**:

1. **Given** a diagram under `documentation/diagrams/`, **When** the reference
   lint runs, **Then** every class name in the diagram exists in the tree.
2. **Given** a diagram that shows a flow, **When** a maintainer reads the code
   of that flow, **Then** the steps and the actors agree.

## User Story 4 (P2): An agent reads correct instruction files

**Independent test**: Compare each fact in `.github/copilot-instructions.md`,
`agents.md`, and `CLAUDE.md` with the tree.

**Acceptance scenarios**:

1. **Given** an agent instruction file, **When** it names a count, a path, or a
   line number, **Then** the fact agrees with the tree, or the text names the
   command that gives the current value.

## User Story 5 (P3): A drift guard finds a stale endpoint map

**Independent test**: Change a handler so that it calls a new SDK function, and
run the check mode of the map tool.

**Acceptance scenarios**:

1. **Given** a code change that changes the endpoints of a menu option,
   **When** the map tool runs in check mode, **Then** it fails and names the
   stale file.
2. **Given** the generated pages and an unchanged tree, **When** the check mode
   runs, **Then** it passes and states how many menu options and files it
   checked.

## Edge cases

- A handler reaches the API through a class that forwards unknown attributes
  with `__getattr__`. The analysis follows the forward by method name.
- A handler starts a web application. The analysis follows the route
  functions of that application.
- A module selects an SDK function at run time, for example with `getattr` or
  with `pkgutil`. A curated table in the tool names these cases and states the
  reason.
- Shared request helpers, such as the rate limiter and the site picker, reach
  the same endpoints from many menu options. The map lists these endpoints one
  time in a shared section, and each row names the helpers that it uses.

## Functional requirements

- **FR-001**: A tool reads the menu registry of `MistHelper.py` and follows each
  handler through the source tree with static analysis only. It imports no
  project module and calls no API.
- **FR-002**: The tool resolves each SDK function to its HTTP method, its path,
  and its Juniper document link. It reads these values from an SDK index file
  in the repository. The index records the `mistapi` version.
- **FR-003**: A refresh command builds the SDK index from the installed
  `mistapi` package.
- **FR-004**: The tool writes an index page and one page for each menu category
  under `documentation/menu-api/`. It writes matching wiki pages under
  `documentation/wiki/`.
- **FR-005**: Each category page holds Mermaid diagrams in groups of no more
  than 15 menu options. Every diagram passes the Mermaid lint.
- **FR-006**: Each page states the limits of static analysis. The map can hold
  a conditional call, and it can miss a call that the code builds at run time.
- **FR-007**: A check mode compares the generated pages with the files on disk.
  If a page differs, the check fails and names the page. The
  `menu_reference_drift` CI job runs the check mode.
- **FR-008**: Each changed Markdown file scores 80 or more on the STE linter.
- **FR-009**: Each diagram passes the Mermaid lint and the diagram reference
  lint.
- **FR-010**: Each count, path, port, and command in the audited documents
  agrees with the tree.

## Out of scope

- `CHANGELOG.md` and the old `specs/` folders keep their text, because that
  text records past work.
- `documentation/ASD-STE100_writing-guide.md` keeps its text. It is the
  authority for the style.
- The agent instruction files get factual corrections only. Their rules do not
  change.

## Success criteria

- **SC-001**: Each count in the README and the wiki agrees with the registry.
- **SC-002**: At least 260 of the 270 menu options show one or more endpoints.
  Each other option states the reason that it has none.
- **SC-003**: A check of ten menu options by hand finds no wrong endpoint.
- **SC-004**: The check mode finishes in less than 60 seconds on a CI runner.
- **SC-005**: Every required check passes on the pull request.
