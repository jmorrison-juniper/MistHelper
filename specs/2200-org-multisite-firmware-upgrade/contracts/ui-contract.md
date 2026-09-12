# UI Contract: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Rendering**: Flask, Jinja, and plain JavaScript

## 1. Flow

The portal uses one continuous sequence:

`organization -> mode -> sites -> options -> confirmation -> progress`

The operator does not enter a separate flow for each device family.

## 2. User Terms

Use these terms in controls, headings, tables, warnings, and status messages:

- AP
- Switch
- Gateway

Do not ask the operator to choose Junos or SSR as the primary family. The
planner classifies gateways after selection.

The confirmation and progress pages can show `Junos gateway` or `SSR gateway`
as route details.

## 3. Organization Page

The organization page selects one organization. A mode or site change cannot
change the organization silently.

The next page is the mode page.

## 4. Mode Page

The mode page offers `single_site` and `multi_site`.

Issue #2475 uses `multi_site`. The page clears old site and target state when
the operator changes the mode.

## 5. Sites Page

The sites page shows sites from the selected organization only.

Each row shows:

- The site name.
- The site identifier.
- The lock state.
- A selection control.

The page rejects an empty selection. It also rejects duplicate site
identifiers.

## 6. Options Page

The options page lists the inventory of the selected sites. It groups controls
under AP, switch, and gateway headings.

Each target row shows:

- A selection control.
- The site name.
- The device name.
- The model.
- The current version.
- The UI family.

The page shows only relevant options for each selected family.

The page marks Mist Edge as unsupported. The operator cannot include it in the
plan.

## 7. Confirmation Page

The confirmation page shows the complete immutable plan.

The page includes:

- The organization.
- The selected sites.
- The selected target count.
- One section for each child.
- The UI family and planned family.
- The route and scope.
- The target count and identifiers.
- The firmware version and schedule.
- The route warnings.

The page states that APs use one organization child. It states that switches
and Junos gateways use site children. It states that SSR gateways use the
existing organization SSR route.

The start button remains disabled until the operator types `CONFIRM` exactly.
The server performs the same check.

Warning: a firmware upgrade can interrupt service at several sites. A
cancellation does not restore firmware that a device already installed.

## 8. Progress Page

The progress page shows one aggregate card and one child table.

The aggregate card shows:

- The operation identifier.
- The organization.
- The site count.
- The target count.
- The aggregate state.
- The last update time.

Each child row shows:

- The child identifier.
- AP, switch, or gateway.
- The planned family.
- The route and scope.
- The site when the route uses a site.
- The target count.
- The cloud job identifier.
- The submit status.
- The error.
- The cancel status.

The page uses distinct words for `failed`, `unknown`, and `not_submitted`.
Color alone does not communicate a state.

## 9. Partial Submission

The progress page must remain useful after a partial submission.

It shows accepted children with their cloud identities. It shows failed
children with their errors. It shows uncertain children as `Unknown`. It shows
untouched children as `Not submitted`.

The page does not offer a retry control for an unknown child.

## 10. Cancellation

The cancel control requires the exact text `CANCEL`.

The page shows the cancel result for each child. It uses these visible terms:

- Not requested
- Not available
- Cancel requested
- Cancelled
- Cancel failed
- Cancel outcome unknown

The page does not state that cancellation rolls back firmware.

## 11. Browser Safety

- Every write includes a CSRF token.
- The browser stores no API token.
- A page refresh sends read requests only.
- A poll sends read requests only.
- The browser never retries a write.
- The server remains authoritative for ownership and scope checks.
- The server remains authoritative for replay prevention.

## 12. Accessibility

- Every input has a visible label.
- Every table has a caption.
- Every status uses text.
- Every error uses an alert region.
- The confirmation hint uses `aria-live`.
- Keyboard users can complete the full sequence.

## 13. Test Identifiers

Use stable identifiers for these controls:

| Element | Test identifier |
| - | - |
| Mode picker | `mode-picker` |
| Multi-site option | `mode-multi-site` |
| Site form | `multi-site-form` |
| Options page | `org-upgrade-options` |
| AP target group | `org-upgrade-family-ap` |
| Switch target group | `org-upgrade-family-switch` |
| Gateway target group | `org-upgrade-family-gateway` |
| Confirmation page | `org-upgrade-confirm` |
| Confirmation input | `org-upgrade-confirmation` |
| Start button | `org-upgrade-start` |
| Progress page | `org-upgrade-progress` |
| Child table | `org-upgrade-children` |
| Cancel control | `org-upgrade-cancel` |

Each child row uses `org-upgrade-child-<child_id>`.

## 14. Playwright Contract

Playwright tests cover the six-page sequence. They use synthetic inventory and
network stand-ins.

The tests cover AP-only, switch-only, gateway-only, and mixed plans. They cover
stale confirmation, duplicate submission, partial results, unknown results,
browser reload, and cancellation.

No Playwright test sends a live Mist write.
