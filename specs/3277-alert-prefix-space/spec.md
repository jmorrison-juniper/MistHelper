# Feature Specification: Put a space after the signal word of each alert

**Issue**: #3277
**Feature Branch**: `fix/3277-alert-prefix-space`
**Status**: Implemented
**Found by**: the cross-cut journey of #3200, screenshot `signin-03-wrong-browser-token.png`

## Problem

Section 12 of `portal.css` prints a signal word before each alert, so the
level reads without color. The four values were `"Note:"`, `"Done:"`,
`"Caution:"`, and `"Warning:"`, with no trailing space.

`portal.js` writes an alert sentence as plain text with no leading space. The
function `showSigninError` sets `textContent` on the sign-in region. The
region is a block with the class `flash-danger`, so the signal word and the
sentence sit on one line. The alert then read
`Warning:The portal could not sign you in`.

A sentence that the server renders starts with template white space, so it
read correctly. A flash item is a flex box with a gap, so it also read
correctly on the screen.

## User Story (P4): An operator reads the signal word and the sentence as two words

**Acceptance scenarios**:

1. **Given** the browser-token mode of the sign-in page, **When** the cloud
   refuses the token, **Then** the alert reads `Warning: The portal could not
   sign you in`.
2. **Given** any signed-in page, **When** a page script writes a message
   through `showFlash` at any of the four levels, **Then** the region reads
   the signal word, one space, and the sentence.
3. **Given** a flash item, **When** the page paints it, **Then** the gap
   between the signal word and the sentence does not change.

## Requirements

- **FR-001**: Each of the four signal word values MUST end with one space.
- **FR-002**: A flash item and a failure alert MUST keep their current look.
  A browser removes a space at the end of a line, so the flex item and the
  block prefix show no change.
- **FR-003**: The hidden region guard of issue #2008 MUST still build no
  content for a hidden region.

## Non-goals

- The wording of the refusal sentence. The token modes name an address and a
  password that they do not have. Issue #3290 holds that defect.
- The weight of the signal word. A flash item prints it in bold, and the
  sign-in region does not. That difference existed before this change.
