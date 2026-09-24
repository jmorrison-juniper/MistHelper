# Feature Specification: Answer a browser page view of a fault with the error page

**Issue**: #3274
**Feature Branch**: `fix/3274-unknown-url-page`
**Status**: Implemented
**Found by**: the cross-cut journey of #3200, screenshots `upj-crosscut/unknown-url-error-page-01-unknown-url.png` and `upj-crosscut/history-comparison-errors-06-unknown-url.png`

## Problem

A browser that opens an unknown URL of the portal reads a raw JSON body. The
body is the error envelope `{"error":{"code":"not_found",...}}`. The page has
no portal layout and no link back to the site list.

`register_error_handlers` in `factory.py` binds `handle_error` to each status
code. `handle_error` always answers `json_error(status)`. The shared page
`error.html` exists, and #3276 added the builder `error_page`, but no fault
handler uses it.

The same handler answers every other fault that reaches the router or a route:
a method that a path refuses (405) and an unexpected fault (500). A person
reads raw JSON for each one.

The address allow list in `security.py` raises `abort(403)`, so it also
reaches this handler. A blocked address must keep the short envelope, because
the guard answers before any page of the portal.

## User Story (P3): An operator recovers from a wrong address

**Acceptance scenarios**:

1. **Given** a signed-in operator, **When** the operator opens a path that no
   route serves, **Then** the portal answers status 404 with the HTML error
   page and a link to the site list.
2. **Given** that page, **When** the operator follows the link, **Then** the
   portal opens the site list.
3. **Given** a browser with no session, **When** it opens a path that no route
   serves, **Then** the page shows no page links and no sign-out control.
4. **Given** a browser page view of a path that refuses the method, **When**
   the portal answers, **Then** the answer is the error page with status 405
   and the `Allow` header.
5. **Given** a JSON client, the portal script, or a client with no `Accept`
   header, **When** the same fault occurs, **Then** the portal answers the JSON
   envelope as before.

## Requirements

- **FR-001**: A browser page view of a path that no route serves MUST receive
  status 404 and `error.html` with the content type `text/html`, the status
  code 404, and the code `not_found`.
- **FR-002**: That page MUST state that the portal holds no page at the
  address, and it MUST hold the link to the site list.
- **FR-003**: A browser request with a method that the path refuses MUST
  receive status 405, the error page, and the `Allow` header. The header MUST
  name the same methods as the header of the JSON answer.
- **FR-004**: A browser page view that meets an unexpected fault MUST receive
  status 500 and the error page. The page MUST NOT show the fault class, the
  fault text, a file path, or a stack trace.
- **FR-005**: Each status that `register_error_handlers` binds MUST give a
  browser page view the error page with the same status and the code of
  `ERROR_CODES`.
- **FR-006**: A JSON client, the portal script, a client that sends
  `Accept: */*`, and a client with no `Accept` header MUST keep the JSON
  envelope with the same status, code, and sentence as before.
- **FR-007**: The fault handler MUST read the rule `wants_browser_page` of
  `factory.py`, the rule that the token check reads (#3275).
- **FR-008**: The page MUST NOT repeat the requested path, because the path is
  client text.
- **FR-009**: A request from an address outside the allow list MUST keep the
  JSON envelope with status 403, even from a browser. The answer MUST NOT write
  a session cookie. A page names the portal and writes that cookie through its
  token fields.

## Non-goals

- The JSON sentence of a 404 answer. A script reads the code, so the envelope
  keeps "The portal found no such record."
- The status code of any fault. A page keeps the status of the envelope.
- The session guard. A guarded page with no session still sends a browser to
  the sign-in form (#3214).
