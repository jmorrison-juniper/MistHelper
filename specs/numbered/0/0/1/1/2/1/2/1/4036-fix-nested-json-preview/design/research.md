# Research: Nested JSON Result Preview

## Scope and evidence

The specification and its evidence record confirm the failure mode. A nested JSON preview request is routed to `data.preview_table`, while a synthetic download request succeeds. This planning task does not repeat the reproduction or make application changes.

## Decisions

### Distinguish file selection from SQLite table selection

**Decision**: The implementation must treat a browsable file's complete relative path as a file selection. It must reserve table selection for an explicit SQLite file-and-table request.

**Rationale**: Flask currently dispatches the nested file request to the table route. The selected handler interprets the last path segment as a table name. The complete file selection must reach the file-preview path instead.

**Alternatives considered**:

- Keep route selection unchanged and alter JSON parsing. Rejected because the wrong handler runs before JSON parsing.
- Remove the SQLite table route. Rejected because the specification requires existing SQLite behavior.
- Change path validation. Rejected because the confirmed defect is route selection, and the path guard must remain unchanged.

### Preserve the existing preview and security contracts

**Decision**: Keep JSON representation, ordering, pagination, error handling, path restrictions, and output-list membership unchanged.

**Rationale**: The specification limits the change to selection of nested browsable files. Existing table behavior and path checks are required protections.

**Alternatives considered**:

- Redesign result listing or the browser's selection workflow. Rejected because the output list already contains the file and download succeeds.
- Add new JSON shapes or file types. Rejected because the specification preserves current supported formats and presentation.

### Validate the defect at the route boundary

**Decision**: Add a Flask test-client regression case using a nested temporary JSON file. Also exercise a nested SQLite table request and existing path-denial cases.

**Rationale**: Service-level parsing tests do not prove which Flask route receives a nested request. A route-level test covers the confirmed dispatch error.

**Alternatives considered**:

- Test only `DataBrowserService`. Rejected because the service does not reproduce route precedence.
- Use a live portal or Mist Cloud. Rejected because temporary local fixtures prove the behavior without production data or credentials.

### Add one user-facing release fragment

**Decision**: Add `changelog.d/issue-4036-nested-json-preview.md` with a short note that nested JSON result files can be previewed in the Results panel.

**Rationale**: The repository uses issue-specific fragments in `changelog.d/`.

**Alternatives considered**:

- Change the shared changelog. Rejected because the repository convention uses a unique fragment per change.
- Add the fragment during planning. Rejected because this workflow ends after Phase 1 design and does not implement application changes.

## Dependency and integration findings

- Flask and pytest are existing project dependencies. No dependency change is needed.
- The affected integration is the existing `/api/data/preview/` route family and its SQLite table route.
- The matching download endpoint remains a comparison path and must not change.
- No unresolved technical unknown remains in the planning scope. The exact code-level selection mechanism remains an implementation choice constrained by the decisions above.
