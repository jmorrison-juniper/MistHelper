# UI Contract: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Rendering**: Flask with Jinja templates
**Browser code**: `src/upgrade_portal/app/assets/static/js/portal.js`

## 1. The Rendering Rule

The server renders every page. The browser runs one plain JavaScript file. The
portal uses no React, no TypeScript, and no bundler.

Every template extends `layout.html`. Every template fills the blocks `title`,
`heading`, and `content`.

Every value passes through a `default` filter first. A template must render even
when a route supplies no value.

## 2. The Page Sequence

| Step | Path | Template |
| - | - | - |
| Sign in | `/auth/signin` | `auth/signin.html` |
| Second factor | `/auth/twofactor` | `auth/twofactor.html` |
| Pick the organization | `/select/org` | `select/orgs.html` |
| Pick the mode | `/select/mode` | `select/mode.html` |
| Pick the sites | `/select/site` | `select/sites.html` |
| Capture a pre-check | `/captures/new` | `capture/capture.html` |
| Set the options | `/upgrade/org/options` | `upgrade/org_options.html` |
| Confirm the job | `/upgrade/org/confirm` | `upgrade/org_confirm.html` |
| Watch the job | `/upgrade/org/jobs/<upgrade_id>` | `upgrade/org_progress.html` |
| Compare the captures | `/compare` | `review/compare.html` |

The blueprint `org_upgrade` serves the three organization pages. The route
module is `src/upgrade_portal/app/routes/org_upgrade.py`.

The single-site sequence keeps `select/inventory.html`, `upgrade/options.html`,
`upgrade/confirm.html`, and `upgrade/progress.html`.

## 3. The Style Rule

The organization pages use the same classes as the single-site pages.

| Element | Class |
| - | - |
| A card | `portal-card` |
| A card title | `portal-card-title` |
| A card note | `portal-card-note` |
| A table | `portal-table` inside `portal-table-scroll` |
| A button | `portal-button` with `portal-button-primary` or `portal-button-danger` |
| An option group | `bubble-group` with `bubble-option` |
| A badge | `portal-badge` with `badge-verified`, `badge-partial`, or `badge-unknown` |
| A monospace cell | `cell-mono` |

The portal adds no second color system. The portal adds no second icon set.

## 4. The Mode Picker

`select/mode.html` already exists. It carries `data-testid="mode-picker"`.

| Control | Test identifier | Value |
| - | - | - |
| The single-site option | `mode-single-site` | `single_site` |
| The multi-site option | `mode-multi-site` | `multi_site` |
| The continue button | `mode-continue` | — |

The form posts to `/select/mode` with the field `mode`. The page shows the
organization name in the card note.

## 5. The Site Picker

`select/sites.html` already serves both modes. The template reads
`selected_mode`.

| Mode | Heading | Action cell |
| - | - | - |
| `single_site` | `Find a site` | An `Open` link |
| `multi_site` | `Select sites` | A checkbox |

| Control | Test identifier |
| - | - |
| The search input | `site-search` |
| The table | `site-table` |
| One row | `site-row-<site_id>` |
| The lock cell | `site-lock-state-<site_id>` |
| The open link | `site-open-<site_id>` |
| The checkbox | `site-select-<site_id>` |
| The form | `multi-site-form` |
| The continue button | `multi-site-continue` |

The lock cell names the state in words. The three words are `Free`, `Locked`,
and `Unknown`. The cell never uses color alone, because color alone fails
WCAG 1.4.1.

The filter runs in the browser. `portal.js` reads `data-filter-target` and hides
each row that does not match `data-filter-text`.

## 6. The Options Page

`upgrade/org_options.html` already exists. It carries
`data-testid="org-upgrade-options"`.

| Control | Test identifier | Field |
| - | - | - |
| The version input | `org-upgrade-version` | `version` |
| The canary option | `org-strategy-canary` | `strategy` |
| The big bang option | `org-strategy-big_bang` | `strategy` |
| The RRM option | `org-strategy-rrm` | `strategy` |
| The phases input | `org-upgrade-canary-phases` | `canary_phases` |
| The failure input | `org-upgrade-max-failures` | `max_failure_percentage` |
| The start input | `org-upgrade-start-time` | `start_time` |
| The review button | `org-upgrade-review` | — |
| The site table | `org-upgrade-site-summary` | — |

### Required changes

Add a `serial` option, because `OrgUpgradeBody` accepts four strategies and the
page offers three.

Add a `force` control, because `OrgUpgradeBody` accepts the force flag inside
the version record.

Add a pre-check column to the site table. The column shows `Verified`,
`Partial`, `Missing`, or `Unknown`.

Add a capture link for each site with no verified pre-check.

Hide the phases input when the strategy is not `canary`. `portal.js` already
holds `filterAdvancedUpgradeControls` for this pattern.

Hide the failure input when the strategy is `big_bang`.

## 7. The Confirmation Page

`upgrade/org_confirm.html` already exists. It carries
`data-testid="org-upgrade-confirm"`.

| Control | Test identifier | Field |
| - | - | - |
| The confirmation input | `org-upgrade-confirmation` | `confirmation` |
| The start button | `org-upgrade-start` | — |
| The back link | — | — |

The route `org_upgrade.submit_upgrade` reads the same field name. The two agree
today.

### Confirmation gate

Keep the field name `confirmation` until a change updates both lanes. The
single-site page uses `confirm`, and one name is better. Change both sides in
one task.

The input uses `data-confirm-word`, `data-confirm-target`, and
`data-confirm-hint-for`. The start button is disabled in the markup. The shared
`applyConfirmGate` function enables it only after an exact match. One Jinja
variable supplies the visible word and the gate word.

### The impact block

The page names the organization, the site count, the device count, the firmware
version, and the strategy.

The page holds a danger alert. The alert states two consequences. The upgrade
can interrupt network service at every selected site. A cancellation does not
restore an upgraded access point.

## 8. The Progress Page

`upgrade/org_progress.html` already exists. It carries
`data-testid="org-upgrade-progress"`.

| Element | Test identifier |
| - | - |
| The job card | `org-upgrade-progress` |
| The status card | `org-upgrade-status` |
| The site table | `org-upgrade-site-progress` |
| The refresh link | `org-upgrade-refresh` |

### Required changes

The page keeps the refresh link. `portal.js` reloads the page on the configured
interval until the job reaches a final state.

Read the job identifier from `data-upgrade-id`. Read the poll interval from
`data-poll-seconds`.

The site table includes total, upgraded, and failed columns. The route reads
these counts from each nested site entry.

Add a comparison link for each site after the post-check finishes.

Add a cancel control with `data-testid="org-upgrade-cancel"`. The control posts
the field `confirmation` with the word `CANCEL`.

## 9. The Browser Contract

`portal.js` holds these helpers. The organization pages reuse them.

| Helper | Purpose |
| - | - |
| `getCsrfToken` | Reads the token from the page |
| `withCsrf` | Adds the token to a request header |
| `fetchJson` | Sends a request and reads the error envelope |
| `showRequestError` | Paints a refusal in the flash region |
| `applyConfirmGate` | Enables a button after an exact typed word |
| `paintConfirmHint` | Paints the hint beside the input |
| `applyTableFilter` | Hides a row that does not match |
| `initTableSorting` | Sorts a table by a column |
| `startLockBeat` | Keeps a site lock alive |
| `handleLockRefusal` | Paints a lock refusal |

### Rules

- The script holds no confirmation word. The script reads
  `data-confirm-word`.
- The script holds no path. The template supplies each path in a data attribute.
- The script sends the CSRF token with every write.
- The script stops a poll on HTTP 401.
- The script stops a poll on a final job state.

## 10. Accessibility Rules

- Every input keeps a visible label. A placeholder alone fails a screen reader.
- Every table keeps a caption with the class `visually-hidden`.
- Every state shows a word, not a color alone.
- Every checkbox label names the site for a screen reader.
- The confirmation hint uses `aria-live` so a screen reader reads the change.

## 11. Test Identifier Rules

- Every control that a test drives carries a `data-testid` attribute.
- A row identifier ends with the site identifier.
- A new identifier starts with `org-upgrade-` on an organization page.
- A test never selects an element by a CSS class.

## 12. Success Criteria

- The operator moves from the organization to the job with the same page style.
- The organization pages use no new class and no new color.
- The confirmation gate behaves the same on both confirmation pages.
- The progress page names every failed access point.
- A screen reader reads every state as a word.
