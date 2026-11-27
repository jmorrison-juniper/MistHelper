# Contract: Run-Name Form

## Route

- Method: `POST`
- Path: `/labs/plan`
- Endpoint: `labs.plan`
- Request body: `application/x-www-form-urlencoded`.
- Fields: `run_name` (one value) and `csrf_token` (one value).

## Response Matrix

Each row is one request shape. The CSRF rows reuse the shared answer rule of record 4648 (L-12).

| Request | Accept | Status | Body |
| - | - | - | - |
| No `csrf_token` | `text/html` or absent | 400 | Flask-WTF HTML error page from the shared handler |
| No `csrf_token` | `application/json` | 400 | JSON with `error`, `code` set to `csrf_expired`, and `detail` |
| Valid token and one valid `run_name`, planner available with a valid plan | `text/html` | 200 | Page with `labs-result`, device rows, link rows, and `labs-fingerprint` |
| Valid token and one valid `run_name`, planner absent | `text/html` | 200 | Page with `labs-unavailable` and reason `planner_absent` |
| Valid token and one valid `run_name`, planner fails | `text/html` | 200 | Page with `labs-unavailable` and reason `planner_failed` |
| Valid token and one valid `run_name`, plan result violates a rule | `text/html` | 200 | Page with `labs-unavailable` and the matching reason code |
| Valid token and an extra field | `text/html` | 400 | Page with `labs-form-error` and no rows |
| Valid token and a repeated `run_name` | `text/html` | 400 | Page with `labs-form-error` and no rows |
| Valid token and an invalid `run_name` | `text/html` | 400 | Page with `labs-form-error` and no rows |
| Valid token and no `run_name` | `text/html` | 400 | Page with `labs-form-error` and no rows |
| `GET /labs/plan` | any | 405 | Flask default answer |

## Rules

- The shared CSRF protection runs before the view (L-3). The Labs code adds no CSRF handler (D-8).
- The view validates the field set before the run-name pattern (`data-model.md`, section "Validation Order").
- The page never echoes the submitted run name in an error message. The error names the rule only.
- The view logs the reason code and the field count. It logs no raw value (FR-022).

## Evidence

- `test_post_without_csrf_token_gets_shared_html_answer` (TR-05).
- `test_json_post_without_csrf_token_gets_csrf_expired_answer` (TR-06).
- `test_valid_run_name_renders_devices_links_and_fingerprint` (TR-07).
- `test_extra_field_gets_400_and_no_rows` (TR-08).
- `test_repeated_run_name_gets_400` (TR-09).
- `test_invalid_run_name_gets_400_with_error_panel` (TR-10).
- `test_planner_failure_renders_unavailable_with_200` (TR-11).
