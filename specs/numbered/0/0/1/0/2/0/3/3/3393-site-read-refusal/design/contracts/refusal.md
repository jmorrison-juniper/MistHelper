# Contract: Site read refusal

This contract defines the answers of the three routes that read the selected sites. It also names the answers that the T008 test must record below the SDK boundary.

## Routes

| Method and path | Handler | Route constant |
| - | - | - |
| POST `/api/org-upgrades/options` | `save_options` | `OPTIONS_API_PATH` (`org_upgrade.py` line 145) |
| GET `/upgrade/org/options` | `options_page` | `OPTIONS_PAGE_PATH` (line 144) |
| GET `/upgrade/org/confirm` | `confirm_page` | `CONFIRM_PAGE_PATH` (line 146) |

## Transport refusal

When a `RequestException` escapes the site list read inside a route, each route answers:

- Status: 503.
- Body: `{"error":{"code":"org_upgrade_site_read_failed","message":"The Mist cloud site read failed. Try again."}}`.
- Source: `SERVICE_UNAVAILABLE_STATUS` (`org_upgrade.py` line 229), `SITE_READ_FAILED` (line 230), and `SITE_READ_FAILED_MESSAGE` (line 231).

The contract test compares the whole body with this envelope (`tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` line 25 to line 30 and line 59).

## Invariants

- The body holds no transport text, no token, and no submitted option value.
- A refused save writes no plan, no nonce, and no saved option.
- A refused page read changes no saved plan and no session value.
- The browser keeps every entered value after a refused save (browser test line 75).

## Unchanged answers

- 400 `options_invalid` for invalid options and for each `BadOptionError` (`org_upgrade.py` lines 1226 and 1231).
- 404 `sites_required` for a missing site (lines 1151 and 1354).
- 400 `mode_required` when no organization context is active (lines 1143 and 1219).
- 503 `site_list_incomplete` for a partial site list (`select.py` lines 256 to 257 and 268, and the app handler at lines 1562 to 1583). The save does not catch this error. The app handler answers it for each route.

## Predicted answers below the SDK boundary

These predictions come from the source (analysis A-1). They are not observed. T008 replaces each prediction with the observed value.

| Case | Predicted status | Predicted code | Basis |
| - | - | - | - |
| Save, transport fault below mistapi | 400 | `options_invalid` with the unread-site message | `org_upgrade.py` lines 649, 755 to 758, 657 to 659, 1230 to 1231, `org_site_records.py` lines 41 to 44 and 183 to 185 |
| Options page, transport fault below mistapi | 503 | `site_list_incomplete` | `org_upgrade.py` lines 1146 and 520, `select.py` lines 992, 1019 to 1036, and 1562 to 1583, `mistapi\__api_request.py` lines 225 to 258 |
| Confirmation page, transport fault below mistapi | 503 | `site_list_incomplete` | `org_upgrade.py` line 1349, with the same basis as the options page |

The table holds predictions only. The T008 test supplies the observed values, and the contract is updated with them when T008 lands.
