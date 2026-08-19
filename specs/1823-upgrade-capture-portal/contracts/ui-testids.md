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
| `org-row-{org_id}` | One organization row |
| `org-select-{org_id}` | The choose button in that row |
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

### Lock

| Identifier | Control |
| --- | --- |
| `lock-banner` | The lock state banner |
| `lock-take-button` | Take the lock |
| `lock-confirm-input` | The field for the word `CONFIRM` |
| `lock-confirm-submit` | The takeover button |
| `lock-release-button` | Release the lock |
| `lock-error` | The lock error region |

### Capture

| Identifier | Control |
| --- | --- |
| `capture-tier-select` | Tier 2 or tier 3 choice |
| `capture-start-button` | Start a capture |
| `capture-progress` | The progress region |
| `capture-progress-percent` | The percent value |
| `capture-section-{name}` | One section state, such as `capture-section-devices` |
| `capture-verified-badge` | The read-back result |
| `capture-partial-warning` | The partial capture warning |
| `capture-size-bytes` | The stored size value |
| `capture-error` | The capture error region |

### Upgrade

| Identifier | Control |
| --- | --- |
| `upgrade-version-select-{mac}` | Target version for one device |
| `upgrade-version-select-all` | Apply one version to every matching model |
| `upgrade-reboot-toggle` | The reboot option |
| `upgrade-strategy-select` | The strategy option |
| `upgrade-target-table` | The target table |
| `upgrade-target-row-{mac}` | One target row |
| `upgrade-warning-list` | The warning list from the plan |
| `upgrade-confirm-input` | The field for the word `UPGRADE` |
| `upgrade-start-button` | Start the upgrade |
| `upgrade-state` | The run state value |
| `upgrade-phase-{name}` | One cascade phase, such as `upgrade-phase-switches` |
| `upgrade-phase-progress-{name}` | The settled count for that phase |
| `upgrade-device-state-{mac}` | The state cell for one device |

### Stop

| Identifier | Control |
| --- | --- |
| `stop-button` | Open the stop dialog |
| `stop-confirm-input` | The field for the word `STOP` |
| `stop-confirm-submit` | The stop button |
| `stop-outcome` | The outcome region |
| `stop-outcome-cancelled` | The cancelled device list |
| `stop-outcome-writing` | The list of devices that will finish |
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
