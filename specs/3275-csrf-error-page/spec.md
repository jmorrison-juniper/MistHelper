# Feature Specification: Answer a refused browser form post with an error page

**Issue**: #3275
**Feature Branch**: `fix/3275-csrf-page`
**Status**: Implemented
**Found by**: the cross-cut journey of #3200, screenshot `history-comparison-errors-10-csrf-post-refusal-checked.png`

## Problem

Every form post of the portal carries a security token. If the token check
fails, `csrf_error_response` in `security.py` answers the JSON envelope with
the code `csrf_missing`. A browser shows that envelope as raw text. The
operator reads `{"error":{"code":"csrf_missing",...}}` and finds no way back to
the form.

An operator meets this refusal when the session ends while a form is open.
A container restart is one example, because each restart signs every operator
out (#3213). A second sign-in in another tab is a second example, because the
new session makes the old token of the first tab invalid.

The sign-in routes and the selection routes already give a browser form post a
page and give the portal script JSON. Each module holds its own copy of that
rule in `wants_browser_page`. The token check does not use the rule.

## User Story (P3): An operator recovers from a refused form

**Acceptance scenarios**:

1. **Given** a browser form post with no valid token, **When** the portal
   refuses the post, **Then** the portal answers status 400 with an HTML error
   page.
2. **Given** that error page, **When** the operator reads it, **Then** the page
   states the cause, shows the code `csrf_missing`, and gives a link back to the
   form page.
3. **Given** a session that ended, **When** the operator follows the link back,
   **Then** the portal opens the sign-in form.
4. **Given** a session that is still valid, **When** the operator follows the
   link back and sends the form again, **Then** the portal accepts the form.
5. **Given** a post from the portal script or from a JSON client, **When** the
   token check fails, **Then** the portal answers the JSON envelope as before.

## Requirements

- **FR-001**: A browser form post that fails the token check MUST receive
  status 400 and `error.html` with the content type `text/html`.
- **FR-002**: The error page MUST show the status code 400, the code
  `csrf_missing`, and a sentence that tells the operator to open the form again.
- **FR-003**: The error page MUST link back to the form page when the browser
  names that page in the `Referer` header. The link MUST name a path of this
  portal that answers `GET`.
- **FR-004**: The page MUST omit the link back when the `Referer` header is
  absent, names another host, names a path that starts with two slashes, or
  names a path that answers no `GET` request. The link to the site list stays.
- **FR-005**: A post that carries `X-Requested-With: XMLHttpRequest`, and a
  post that states no preference for HTML, MUST keep the JSON envelope with the
  status 400 and the code `csrf_missing`.
- **FR-006**: The token check, the sign-in routes, and the selection routes
  MUST read one rule that separates a browser page from a script. The rule
  lives once, in `factory.py`.
- **FR-007**: The page MUST NOT show the refused token. The log line MUST name
  the fault class only.
- **FR-008**: The header of the error page MUST show its page links and the
  sign-out control only when the request holds a live session. A refused post
  after a restart holds no session.

## Non-goals

- The status code. The contract binds status 400 to a missing token, and a page
  keeps it.
- The error handler for an unknown URL. Issue #3274 holds that change.
- The check in `org_upgrade.py`. That module reads the `Accept` header without
  the script header, and no form post of this issue reaches it.
