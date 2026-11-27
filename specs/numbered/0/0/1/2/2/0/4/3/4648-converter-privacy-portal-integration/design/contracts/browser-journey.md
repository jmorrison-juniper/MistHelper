# Contract: Real-Portal Browser Journey

## Scope

Tasks T011 only. The module holds four tests. The journey uses the real portal factory and the existing Playwright setup. It starts after the registration (task T009) and the navigation entry (task T010).

## Server

- Build the app with `WebPortalApp.create_app`, using the same arguments as the `flask_app` fixture (`tests/e2e/conftest.py` lines 273 to 277).
- Serve the app with `werkzeug.serving.make_server("127.0.0.1", 0, app)` in a daemon thread. The pattern appears in `tests/e2e/web_portal/test_portal_smoke.py` lines 27 to 37.
- Stop the server in teardown with `shutdown` and `server_close`.
- Set `pytest.mark.timeout(120)` on each test. The value matches `E2E_TIMEOUT_SECONDS` in `tests/e2e/conftest.py` line 33.

## Steps and selectors

| Step | Action | Selector | Source |
| - | - | - | - |
| 1 | Open the portal home page | `/` | Route from the factory |
| 2 | Open the converter from the navigation bar | `[data-testid="nav-cisco-converter"]` | Task T010 |
| 3 | Confirm that the converter section appears | `[data-testid="cisco-converter"]` | `converter.html` line 4 |
| 4 | Set the input file | `[data-testid="cisco-file"]` | `converter.html` line 11 |
| 5 | Enter the template name | `[data-testid="cisco-name"]` | `converter.html` line 13 |
| 6 | Select the template type | `[data-testid="cisco-type"]` | `converter.html` line 15 |
| 7 | Start the preview | `[data-testid="cisco-preview"]` | `converter.html` line 19 |
| 8 | Confirm that the review button is enabled | `[data-testid="cisco-review"]` | `converter.html` line 23 |
| 9 | Approve the proposal | `[data-testid="cisco-review"]` | `converter.html` line 23 |
| 10 | Export and check the download | `[data-testid="cisco-export"]` | `converter.html` line 24 |
| 11 | Submit an invalid file | `[data-testid="cisco-status"]` shows text | `converter.html` line 21 |

## Test functions

- `test_nav_entry_opens_converter_in_real_portal` covers steps 1 to 3.
- `test_upload_preview_review_export_in_real_portal` covers steps 4 to 10.
- `test_invalid_upload_shows_safe_error` covers step 11.
- `test_evidence_path_stays_under_test_artifacts` checks the evidence helper.

## Evidence

- On failure, save a screenshot with `page.screenshot` under `test-artifacts/cisco-portal/`.
- The evidence helper keeps every path under that folder. Git ignores the folder (`.gitignore` line 107).

## Out of scope

Visual journeys, themes, and keyboard checks belong to issue #4647.
