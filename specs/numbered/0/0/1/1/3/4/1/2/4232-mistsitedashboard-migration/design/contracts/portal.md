# Portal contract: Site health dashboard

## Proposed navigation

Add a Site health tab only after B05 and B06 close.
Use the existing portal on port 8055 and existing theme.
No second application or source container is permitted.
The current offline slice registers no route or browser control.

| Proposed view | Information and interaction | Future browser test |
| --- | --- | --- |
| Organization | Site search, WiFi/Wired/WAN tabs, periods, metric cards, worst-100 table, site links | `tests/e2e/web_portal/test_site_health_organization.py` |
| Site | Heading, device cards, service cards, periods, then sortable device tables | `tests/e2e/web_portal/test_site_health_site.py` |
| Wireless clients | Summary counts, session history, SSID/band/search filters, client details, export | `tests/e2e/web_portal/test_site_health_clients.py` |
| Wired clients | Port/VLAN/MAC/address fields, search, session details, export | `tests/e2e/web_portal/test_site_health_clients.py` |
| Gateway WAN | Port address/speed/traffic, expandable VPN and BGP tables, peer percentages | `tests/e2e/web_portal/test_site_health_gateway.py` |
| WiFi SLE | Metrics, classifiers, impact bars, distribution, affected clients/devices/WLANs | `tests/e2e/web_portal/test_site_health_sle.py` |
| Wired SLE | Metrics, DHCP and other classifiers, affected switches/clients | `tests/e2e/web_portal/test_site_health_sle.py` |
| WAN SLE | Metrics, application/interface/gateway distribution and failures | `tests/e2e/web_portal/test_site_health_sle.py` |

These are planned paths, not delivered tests.
Confirm compliant placement before creating them.

## Inputs and states

Use validated organization and site UUIDs from the server session.
Allow only enumerated categories, verified periods, and discovered safe metric identifiers.
Whitelist export columns. Neutralize spreadsheet formulas and escape all displayed data.
Do not expose arbitrary response fields, credential fields, or raw error bodies through dynamic columns.
Use explicit `loading`, `ready`, `empty`, `partial`, `unavailable`, `stale`, `denied`, and `error` states.
Never label missing data healthy.

Period choices remain B03 until verified.
The proposed canonical organization periods are 24 hours, seven days, and two weeks.
Retain short site periods only after their contracts pass.
Manual refresh preserves scope, period, category, sorting, and filters.
Older request generations cannot overwrite a newer selection.

Use score text with green at 80 percent or above, yellow at 50 percent or above, and red below 50 percent.
These source presentation thresholds are not service guarantees.
Keep missing scores uncolored and label their cause.
Keyboard controls and text labels must provide the same meaning without color.
Use the MistHelper theme, not source branding or protected images.

## Browser identifiers and access

Use stable `data-testid` values such as `site-health-site-select`, `site-health-category-wifi`,
`site-health-period`, `site-health-refresh`, `site-health-retry`, and `site-health-export`.
Use `site-health-impact-dialog` for affected items and retain a keyboard-accessible close control.
Test 390-pixel and 1440-pixel viewports.
Retain screenshots or traces under ignored `test-artifacts/` on failure.
Block all external network access in offline browser tests.

Existing portal middleware restricts network addresses and applies CSRF and security headers.
It does not provide per-user authentication.
Do not advertise per-user authorization or expose sensitive data until B05 closes.
Test denied pages, data, refresh, and export through the same security boundary.
No browser request may contain the Mist token.
