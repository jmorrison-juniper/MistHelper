# Feature Specification: Show a picker refusal inside the picker page

**Issue**: #3240
**Feature Branch**: `fix/3240-picker-refusal-page`
**Status**: Draft
**Found by**: the multi-site journey of #3200, finding F-upj-multisite-004

## Problem

The multi-site site picker sends a plain form post. If the operator selects no
site and clicks Continue, the route `choose_sites` answers the JSON envelope.
The browser then shows this text as the whole page:

`{"error":{"code":"sites_not_chosen","message":"Choose one or more sites for the multi-site operation."}}`

The page has no layout, no link, and no form. The operator must use the back
button to continue.

The mode picker and the organization picker have the same defect. Each post
answers the JSON envelope for a refusal, and a browser shows it as raw text.

## User Story 1 (P1): An empty site choice keeps the operator on the site page

**Acceptance scenarios**:

1. **Given** the multi-site site page with no site selected, **When** the
   operator clicks Continue, **Then** the site page opens again, and its
   message region shows "Choose one or more sites for the multi-site
   operation."
2. **Given** that refusal, **When** the operator selects a site and clicks
   Continue, **Then** the options page opens.
3. **Given** the options page after that refusal, **When** the operator goes
   back in the browser, **Then** the site page opens with no request to send
   the form again.
4. **Given** a site choice that names a site outside the organization, **When**
   the operator clicks Continue, **Then** the site page opens again with the
   sentence "The portal found no such site in this organization."

## User Story 2 (P2): A mode refusal returns the operator to the mode page

**Acceptance scenarios**:

1. **Given** the mode page with no mode selected, **When** the post arrives,
   **Then** the mode page opens again with the sentence "Choose a single-site
   or a multi-site operation."
2. **Given** a multi-site site page in one tab, **When** another tab changes
   the mode to single-site and the first tab clicks Continue, **Then** the mode
   page opens with the same sentence.

## User Story 3 (P3): An organization refusal returns the operator to the organization page

**Acceptance scenarios**:

1. **Given** an organization post that names no organization, **When** the
   post arrives, **Then** the organization page opens again with the refusal
   sentence.

## Functional requirements

- **FR-001**: If a browser page sends a picker post and the portal refuses it,
  the portal answers a 303 redirect to the picker page that can correct the
  choice.
- **FR-002**: The picker page shows the refusal sentence one time, in the
  shared message region, with the level `warning`. The region prints the
  prefix "Caution:", because the operator can correct the choice.
- **FR-003**: A script and a JSON client keep the JSON envelope, the code, and
  the status that the contract fixes.
- **FR-004**: A refusal changes no stored choice. The organization, the mode,
  the site set, and the saved upgrade options stay as they were.
- **FR-005**: Each refusal goes to the page that corrects its cause. A missing
  organization goes to the organization page. A missing mode goes to the mode
  page. A missing site or an unknown site goes to the site page.
- **FR-006**: The sentence on the page is the same sentence that the envelope
  holds, so the two clients read one text for one cause.

## Out of scope

- The Continue button stays enabled with no site selected. The server refusal
  gives the sentence, and the page needs no second rule in the script.
- The refusal pages of the other portal forms. The capture, upgrade, and
  multi-site forms send the request from the page script, and the script shows
  the refusal in the page already.

## Success criteria

- **SC-001**: A browser journey proves the in-page sentence and no JSON page
  for each user story.
- **SC-002**: Contract tests prove the redirect, the one-time sentence, and the
  unchanged JSON envelope for a script.
