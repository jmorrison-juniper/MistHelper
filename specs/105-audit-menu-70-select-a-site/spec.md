# Feature Specification: Audit - Select a site (Menu #70)

**Feature Branch**: `105-audit-menu-70-select-a-site`  
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Create an AUDIT spec for MistHelper Menu #70: 'Select a site' — Function: PromptUtils.select_site_with_logging. Focus on selection UX, caching, logging, resilience to invalid input, testability. Document current implementation in MistHelper.py, identify issues, and define acceptance criteria for fixes."

## Summary

This is an AUDIT specification for the interactive menu item "Select a site" (Menu #70) implemented by PromptUtils.select_site_with_logging in MistHelper.py. The goal is to document the current implementation, identify gaps and risks in UX, caching, logging, input resilience and testability, and define measurable acceptance criteria and tests for required fixes.

This spec does not propose how to implement fixes (no implementation details) — it focuses on WHAT must change and WHY, and how to verify success.


## Current implementation (observed)

Key code paths in MistHelper.py (excerpted behavior):

- PromptUtils.select_site_with_logging():
  - Logs: "Prompting user to select a site from SiteList.csv..."
  - Calls PromptUtils.select_site_id_from_csv()
  - If site_id returned, logs: "! Selected site ID: {site_id}"
  - If None, logs an error: " No site selected. User may have entered an invalid value or cancelled the prompt." and returns None

- PromptUtils.select_site_id_from_csv(csv_file="SiteList.csv"):
  - Calls CacheUtils.check_and_generate_csv(csv_file, OrgSiteExporter.sites) to ensure SiteList.csv exists/fresh
  - Loads CSV via FilePathUtils.get_csv_path() and csv.DictReader
  - Displays sites to user as a numbered list (prints "Available Sites:" then "[index] name")
  - Uses input("Enter site index or name: ") and .strip()
  - Accepts either numeric index (converted to int and looked up) or exact name match (case-sensitive)
  - On valid choice prints selected site and logs at info
  - On invalid index/name prints message and returns None (logs warning)

Observed behavioral summary:
- Selection flow is CSV-driven: user sees a printed indexed list and types an index or exact name.
- Caching is delegated to CacheUtils.check_and_generate_csv; no explicit refresh interaction is offered to the user.
- Logging exists at INFO and WARNING/ERROR levels as described above.
- Input handling is a single-shot: invalid input returns None immediately (no retry loop or interactive re-prompt).
- select_site_id_from_csv uses direct input() calls, while other prompt helpers sometimes use InputUtils.safe_input(). This is inconsistent and affects testability.


## Key Concepts / Actors / Data / Constraints

- Actors:
  - CLI user (operator) who must select a site before running other actions
  - Automation (scripts) that may call PromptUtils.select_site_with_logging non-interactively

- Actions:
  - Present list of sites
  - Let user choose by index or by name
  - Validate input and return the selected site_id
  - Log the selection outcome
  - Use cached SiteList.csv where appropriate to reduce API calls

- Data:
  - SiteList.csv (cache of site id, name, address, etc.)
  - In-memory mapping(s): index -> site row, name -> site row

- Constraints and environment expectations:
  - CSV freshness is controlled by CacheUtils (project-wide policy)
  - Interactive selection must remain usable on terminals; support for automation is desirable
  - Function signature: returns str|None (site_id or None)


## Issues identified (gaps & risks)

1. Selection UX
   - No documented cancel option in the prompt text. The code returns None for invalid input but does not provide an explicit "cancel" token or guidance (e.g., 'c' or empty input) to abort.
   - Name matching is exact and case-sensitive. This causes unnecessary failures (UX friction) when users type names with different case or minor whitespace differences.
   - No partial or fuzzy match support (e.g., typing a substring), making large site lists cumbersome.
   - The displayed list shows indices but does not show any paging or search/filter options for orgs with many sites.

2. Caching
   - Caching is delegated to CacheUtils.check_and_generate_csv but the prompt provides no explicit way for the user to force a refresh (e.g., 'r' to refresh list) if the cached CSV is stale or missing a recently created site.
   - The UX does not surface whether the list shown is cached or freshly fetched; no TTL/freshness indicator is shown.

3. Logging
   - select_site_with_logging logs a generic error-level message when the user makes no selection or provides invalid input. Treating user input errors as ERROR may be too high-severity (should be INFO/WARNING depending on context).
   - No contextual logging about whether the CSV was generated from cache or API (useful for debugging and audit trails).
   - When selection succeeds, only the site_id is logged (no site name or human-readable context); correlating id->name in logs would aid operators.

4. Resilience to invalid input
   - The prompt is single-shot: invalid index or name returns None immediately. There is no re-prompt or guided correction path.
   - The function returns None for invalid input but callers may not distinguish between user-cancel and transient API/cache errors—there's no canonical sentinel or richer error information.

5. Testability
   - select_site_id_from_csv uses built-in input() directly, which is hard to stub in unit tests compared with using InputUtils.safe_input() or an injectable input function.
   - The function prints directly to stdout (print statements) and reads via input(); this makes unit tests noisy and harder to assert messages unless stdout is captured.
   - No small helper functions split logic (display, parse input, lookup) in a way that allows unit testing of each component independently.

6. Consistency / code hygiene
   - Inconsistent use of InputUtils.safe_input across prompt helpers; some use InputUtils.safe_input (which supports context and allow_empty) while select_site_id_from_csv uses raw input().
   - Name matching is exact; normalization is not performed (trim, casefold) as done in other selection helpers (some device selection logic normalizes MACs).


## Assumptions

- SiteList.csv is a CSV with at least columns 'id' and 'name'. CacheUtils.check_and_generate_csv will create it if absent.
- The function signature must remain: select_site_with_logging() -> str | None
- Backwards compatibility: callers (many other functions) expect None when no site selected; this should not change unless a migration plan is provided.
- The environment contains logging configured as in the project (so logged messages will be captured in script.log)


## Goals (WHAT changes are required)

1. Improve selection UX so users can reliably and easily choose sites in small and large organizations.
2. Make caching behavior explicit and offer a simple refresh option.
3. Adjust logging granularity and include helpful context (site name + id, cache/freshness indicator).
4. Improve resilience to invalid input — provide helpful error messages, at least one re-prompt, and a clear cancel option.
5. Make the selection logic testable via dependency injection or consistent use of InputUtils.safe_input and by separating display/parse/lookup into testable functions.


## User Scenarios & Testing (mandatory)

### User Story 1 - Quick select by index (Priority: P1)

As an operator running MistHelper interactively, I want to pick a site by entering its index from a short list so I can proceed quickly.

Why this priority: Primary/fast path used by most interactive operations.

Independent Test:
- Given a SiteList.csv with 5 entries, when the user types a valid index and presses Enter, then the function returns the expected site_id and logs the selection (site name + id).

Acceptance Scenarios:
1. Given SiteList.csv exists and contains >=1 row, When user enters the index shown in the printed list, Then return the corresponding site_id immediately and log INFO: selected site name and id.
2. Given user enters 'c' (or explicit cancel token), Then return None and log INFO: user cancelled site selection.

---

### User Story 2 - Robust name selection & forgiving matching (Priority: P1)

As an operator, I want to be able to type site names in a forgiving manner (case-insensitive, trimmed) so that minor differences do not block selection.

Why this priority: Name selection is common; exact-case matching is brittle and will cause frequent failures.

Independent Test:
- Test name inputs with different cases and surrounding whitespace return the correct site_id.

Acceptance Scenarios:
1. Given a site named "Main Office", When user types "main office" or " Main Office ", Then return the same site_id.
2. Given multiple sites match a case-insensitive substring, Then prompt the user with the narrowed list to disambiguate.

---

### User Story 3 - Cached list with explicit refresh (Priority: P2)

As an operator, I want to know if the site list is coming from cache and be able to force-refresh it if necessary.

Why this priority: Ensures operators are not surprised by missing new sites and can refresh when needed.

Independent Test:
- When cached SiteList.csv is used, the prompt shows "(cached, X minutes old)" and accepts 'r' to refresh and re-run listing.

Acceptance Scenarios:
1. When the cache is used and older than the freshness threshold, the UI shows a freshness indicator.
2. When the user enters 'r', the system regenerates the SiteList.csv from API and re-displays the list.

---

### User Story 4 - Clear handling of invalid input (Priority: P1)

As an operator, if I mistype a selection, I should get a clear message and be allowed to correct it (at least one re-prompt) or cancel.

Independent Test:
- Given invalid input, the function prints an explanatory message and re-prompts once; second invalid input returns None.

Acceptance Scenarios:
1. Given invalid selection, prompt the user again with guidance (e.g., "Enter a valid index, name, 'r' to refresh, or 'c' to cancel").
2. If the user again provides invalid input, return None and log a WARNING indicating invalid attempts.

---

### Edge Cases

- Very large orgs (hundreds+ sites): the printed list is long. UX must offer search/filter (substring) instead of printing entire list. If not implemented, document as a limitation and include acceptance criteria for graceful failure.
- Duplicate site names: name-based lookup must detect duplicates and disambiguate by asking the user to select by index or show additional context (site id or address).
- Script run non-interactively (STDIN closed): functions should fail gracefully (return None) and not block indefinitely.


## Functional Requirements (testable)

- FR-001: The selection prompt MUST accept an index number and return the corresponding site_id when valid.
- FR-002: The selection prompt MUST accept a site name in a case-insensitive, trimmed fashion and return the corresponding site_id when unambiguous.
- FR-003: If a name matches multiple sites, the system MUST present a disambiguation list and allow selection by index.
- FR-004: The prompt MUST accept a cancel token (e.g., 'c') and return None without logging an ERROR.
- FR-005: The prompt MUST accept a refresh token (e.g., 'r') that forces CacheUtils to regenerate SiteList.csv and re-display the list.
- FR-006: The function select_site_with_logging MUST log selection events with site name and id at INFO level, and user cancellations at INFO level. Invalid input attempts MUST be logged at WARNING level (not ERROR).
- FR-007: The selection logic MUST expose input handling via InputUtils.safe_input or accept an injectable input function to enable automated unit tests.
- FR-008: The prompt MUST indicate when the displayed list is cached and include cache age in minutes.
- FR-009: The function MUST not raise unhandled exceptions on malformed CSV, missing fields, or I/O errors; it MUST return None and log details at WARNING/ERROR as appropriate.


## Success Criteria (measurable & verifiable)

- SC-001: 100% of unit tests covering site-selection logic pass. Tests must include: valid index, valid name (case variations), duplicate-name disambiguation, cancel, refresh, cache-not-found handling, and non-interactive STDIN failure.
- SC-002: In manual acceptance testing with SiteList.csv of 50 sites, a user can successfully select a site by index or name within 3 interactions (attempts/re-prompts) in 95% of trials.
- SC-003: Logs contain both site name and site id for every successful selection (verify by scanning script.log entries for pattern "Selected site: <name> (ID: <id>)").
- SC-004: Cache freshness information is printed when SiteList.csv is used; the prompt shows age in minutes. Verify by creating a stale file (mtime older than threshold) and ensuring indicator appears.
- SC-005: The codebase has at least one unit test that asserts select_site_id_from_csv uses InputUtils.safe_input or accepts an injected input callable (so tests can stub responses).


## Key entities

- Site: { id: str, name: str, address?: str }
- SiteList.csv: cached list with rows containing at minimum id and name
- CacheUtils: module responsible for generating and validating CSV freshness
- InputUtils: helper for safe input (recommended for consistent prompts)


## Test Cases (proposed)

- TC-001: Valid index selection
  - Setup: SiteList.csv with 3 rows
  - Input: index '1' (via stubbed input)
  - Expect: returns site_id of row 1; log entry with site name+id at INFO

- TC-002: Valid name selection (case-insensitive)
  - Input: 'main office' vs stored 'Main Office'
  - Expect: returns site_id; INFO log

- TC-003: Duplicate-name disambiguation
  - Setup: Two rows with name 'Test Site' but different ids
  - Input: 'Test Site' -> expect disambiguation printed and then index chosen -> return correct site_id

- TC-004: Cancel
  - Input: 'c' -> expect None returned; INFO log: user cancelled

- TC-005: Refresh flow
  - Input: 'r' when cache exists -> expect CacheUtils called to refresh and list re-printed; then selection proceeds

- TC-006: Non-interactive stdin closed
  - Behavior: function must detect inability to prompt and return None quickly (no infinite blocking)


## Recommendations (high level, no implementation detail)

- Make input collection pluggable (use InputUtils.safe_input consistently or accept an injectable input function) to allow unit testing.
- Add user-facing tokens: 'c' to cancel, 'r' to refresh.
- Perform normalization for name matching (casefold + strip) and support substring search when exact match fails; if multiple matches, disambiguate by index.
- Surface cache freshness indicator in the prompt and log whether the list was served from cache or fetched fresh.
- Reduce log severity for user-driven non-errors (do not log invalid input as ERROR) and include site name + id in success logs.
- Add unit tests that cover the key flows listed in Test Cases.


## Acceptance Criteria (detailed, actionable)

1. The select_site_with_logging flow meets FR-001 through FR-009 (see Requirements section).
2. A new test suite exists that stubs input and verifies the behavior for the TC-xxx test cases above (unit tests run in CI).
3. Logging contains human-friendly selection entries: "Selected site: <name> (ID: <id>)" at INFO level for successes and "User cancelled site selection" at INFO for cancellations. Invalid input attempts logged at WARNING and limited to N attempts (configurable default 1 re-prompt).
4. The prompt indicates when the SiteList.csv is cached and its age in minutes; the user can press 'r' to force a refresh which triggers CacheUtils and re-displays the list.
5. The selection routine is non-blocking in non-interactive sessions (detects missing stdin and returns None within a short timeout), and callers are unaffected (they receive None and handle accordingly).


## Migration / Backwards-compatibility notes

- Existing callers expect select_site_with_logging() to return site_id or None. Keep this contract.
- Logging message text may change (to include site name) — this is additive; acceptance criteria require that site_id still be logged.


## Next steps / Implementation-ready artifacts

- Create small refactor PR that:
  - Replaces raw input() calls in select_site_id_from_csv with a stable input abstraction
  - Adds normalization and disambiguation logic
  - Adds cache-age indicator and refresh token
  - Adjusts logging levels and messages
  - Adds unit tests for the TC list


## SPEC READINESS

- This audit spec documents current state, issues, required functional changes, acceptance criteria and test cases.
- [SUCCESS] Spec ready for planning phase (/speckit.plan)


---

Appendix: Relevant code locations (for reviewer convenience)
- PromptUtils.select_site_with_logging: MistHelper.py lines ~10956-10970
- PromptUtils.select_site_id_from_csv: MistHelper.py lines ~10890-10944


