# Interface Test Identifier Contract

**Feature**: 1823-upgrade-capture-portal

## Why this contract exists

The specification holds a Stability contract. It requires a stable test identifier
on every control that a test drives. Without one, a test selects by visible text
or by a CSS class, and a small wording change or a style change breaks the test
for no real reason.

The specification also requires a failed interface test to produce a screenshot
and a trace.

## Rules

1. Every control that a test drives carries a `data-testid` attribute.
2. The value is lower case with hyphens. It holds no space and no brand name.
3. The value never changes for a wording change, a style change, or a layout
   change.
4. A test selects by `data-testid` only. A test never selects by visible text, by
   a CSS class, or by an element position.
5. A dynamic row appends a stable key. A device row uses the MAC address. A
   capture row uses the capture identifier.
6. A value appears once for each page. A repeated value belongs to a row and
   carries its key.

## Playwright settings

| Setting | Value | Reason |
| --- | --- | --- |
| `screenshot` | `only-on-failure` | The specification requires a screenshot on failure |
| `trace` | `retain-on-failure` | The specification requires a trace on failure |
| `testIdAttribute` | `data-testid` | Makes `getByTestId` match this contract |
| `baseURL` | `http://127.0.0.1:8056` | The default portal port |

The existing `gunicorn_server` fixture at `tests/e2e/conftest.py:56-99` has no
consumer today. The new tests give it one, or the new tests add their own fixture
for port 8056.

---

## Identifier list

### Sign in and organization

| Identifier | Control |
| --- | --- |
| `signin-email` | Email field |
| `signin-password` | Password field |
| `signin-submit` | Sign-in button |
| `signin-error` | Error message region |
| `twofactor-code` | Second factor field |
| `twofactor-submit` | Second factor button |
| `org-search` | Organization filter field |
| `org-search-submit` | The submit control of the filter form |
| `org-row-{org_id}` | One organization row |
| `org-select-{org_id}` | The choose button in that row |
| `org-page-next` | Next page |
| `org-page-previous` | Previous page |
| `signout-button` | Sign-out control |

### Site selection

| Identifier | Control |
| --- | --- |
| `site-search` | Site filter field |
| `site-row-{site_id}` | One site row |
| `site-lock-state-{site_id}` | The lock state cell |
| `site-open-{site_id}` | The open button |
| `inventory-table` | The device table |
| `inventory-row-{mac}` | One device row |
| `inventory-count-total` | Total device count |
| `site-capture-link` | The link from the inventory view to the capture page |

### Lock

| Identifier | Control |
| --- | --- |
| `lock-banner` | The lock state banner |
| `lock-state-message` | The sentence that names the lock state |
| `lock-cooldown` | The remaining wait before a takeover |
| `lock-take-button` | Take the lock |
| `lock-confirm-warning` | The warning above the field |
| `lock-confirm-input` | The field for the word `CONFIRM` |
| `lock-confirm-submit` | The takeover button |
| `lock-release-button` | Release the lock |
| `lock-error` | The lock error region |

`lock-state-message` holds one sentence for each of the three lock states. WCAG
1.4.1 refuses color as the only signal, so the sentence names the state and a test
reads the sentence.

`lock-cooldown` stays hidden while the site is free. The script opens it on the
first refusal and writes the remaining seconds into a `data-lock-cooldown-value`
element inside it. That inner attribute is a script hook, not a test hook.

### Capture

| Identifier | Control |
| --- | --- |
| `capture-tier-select` | Tier 2 or tier 3 choice |
| `capture-start-button` | Start a capture |
| `capture-refresh-button` | The manual refresh control on the capture page |
| `capture-progress` | The progress region |
| `capture-progress-percent` | The percent value |
| `capture-section-{name}` | One section state, such as `capture-section-devices` |
| `capture-verified-badge` | The read-back result |
| `capture-partial-warning` | The partial capture warning |
| `capture-identifier` | The capture identifier value |
| `capture-size-bytes` | The stored size value |
| `capture-error` | The capture error region |
| `capture-device-table` | The device table of a completed capture |
| `capture-device-row-{mac}` | One device row, such as `capture-device-row-0011220000aa` |
| `capture-client-wired-table` | The wired client table |
| `capture-client-wireless-table` | The wireless client table |
| `capture-client-row-{mac}` | One client row of either client table |
| `capture-export-csv` | The download of the capture as a comma-separated file |
| `capture-export-json` | The download of the capture as a JSON file |

FR-026 requires the three tables. Each table renders on every page render, even
for a capture that holds no row. A site with no device of a type is a valid
capture, so the table shows an empty state row and the page shows no error.

The address in a row identifier is the address without a separator and in lower
case, which is the key of the device index. Each chassis member holds its own
index entry, so each member holds its own row.

The two download controls appear once the portal verified the capture. A capture
the portal never read back offers no download, because the file could hold rows
that never reached the store.

`capture-identifier` and `capture-size-bytes` sit in the Result card, and that
card sits outside `capture-progress`. The script must read both through the
document and never through the progress region. Issue #2093 records the failure
that a region search caused.

### Upgrade

| Identifier | Control |
| --- | --- |
| `upgrade-version-select-{mac}` | Target version for one device |
| `upgrade-version-select-all` | Apply one version to every matching model |
| `upgrade-reboot-toggle` | The reboot option |
| `upgrade-junos-file-action-toggle` | The Junos file action option |
| `upgrade-strategy-select` | The strategy option |
| `upgrade-options-save-button` | Save the chosen options |
| `upgrade-target-table` | The target table on the options page |
| `upgrade-target-row-{mac}` | One target row |
| `upgrade-warning-list` | The warning list from the plan |
| `upgrade-confirm-input` | The field for the word `CONFIRM` |
| `upgrade-start-button` | Start the upgrade |
| `upgrade-lock-banner` | The lost lock warning on the progress page |
| `upgrade-state` | The run state value |
| `upgrade-run-table` | The device table on the progress page |
| `upgrade-refresh-button` | The manual refresh control on the progress page |
| `upgrade-phase-{name}` | One cascade phase, such as `upgrade-phase-switches` |
| `upgrade-phase-progress-{name}` | The settled count for that phase |
| `upgrade-device-state-{mac}` | The state cell for one device |
| `upgrade-device-version-check-{mac}` | The version check badge for one device (FR-051) |

`upgrade-target-table` and `upgrade-run-table` are two different tables. The
target table lists what the run will do. The run table lists what the run has
done. A test that watches progress selects the run table.

The target table belongs to the options page alone. An earlier version of this
row named the confirm page too. The confirm page holds the warning list, the
confirm field, and the start button, and it holds no table.

`upgrade-lock-banner` carries no element in any template. The script builds it and
inserts it as the first child of the run region, because the progress page holds
no banner for a lost lock and the content security policy blocks an inline script.
The banner also carries a `data-run-lock-banner` attribute. That attribute is a
script hook, and it stops a second poll from adding a second banner. A test
selects `upgrade-lock-banner` instead.

A device row in the run table also carries a `data-run-device-row` attribute. That
attribute is a script hook for the 30-second poll, not a test hook. A test selects
`upgrade-device-state-{mac}` instead.

The version check badge inside `upgrade-device-version-check-{mac}` carries a
`data-run-version-check` attribute with the same MAC address. That attribute is a
script hook, not a test hook. The badge holds no `data-run-field`, because the
poll replaces the whole text of every field cell and would drop the badge. The
badge shows one of three words: `Version matches`, `Version mismatch`, or
`Awaiting version`. WCAG 1.4.1 refuses color as the only signal, so a test reads
the word and never the class.

### Stop

| Identifier | Control |
| --- | --- |
| `stop-button` | Open the stop dialog |
| `stop-confirm-input` | The field for the word `STOP` |
| `stop-confirm-submit` | The stop button |
| `stop-outcome` | The outcome region |
| `stop-outcome-cancelled` | The cancelled device list |
| `stop-outcome-writing` | The list of devices that will finish |
| `stop-outcome-no-cancel` | The list of devices with no cancel path |
| `stop-outcome-message` | The plain sentence for the operator |

### Comparison

| Identifier | Control |
| --- | --- |
| `compare-before-select` | The pre-check choice |
| `compare-after-select` | The post-check choice |
| `compare-run-button` | Run the comparison |
| `compare-statistics` | The statistics region |
| `compare-stat-{name}` | One statistic, such as `compare-stat-clients-moved` |
| `compare-device-table` | The device difference table |
| `compare-device-row-{mac}` | One device row |
| `compare-client-table` | The client difference table |
| `compare-client-row-{mac}` | One client row |
| `compare-filter-{outcome}` | A filter, such as `compare-filter-missing` |
| `compare-export-csv` | Download as CSV |
| `compare-export-json` | Download as JSON |

### History

| Identifier | Control |
| --- | --- |
| `history-table` | The history table |
| `history-row-{capture_id}` | One history row |
| `history-open-{capture_id}` | Open that capture |
| `history-page-next` | Next page |
| `history-page-previous` | Previous page |

### Shared

| Identifier | Control |
| --- | --- |
| `theme-select` | The theme picker |
| `nav-sites` | Navigation to the site list |
| `nav-history` | Navigation to the history |
| `flash-message` | The message region |
| `csrf-meta` | The meta tag that holds the token |
