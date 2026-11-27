# Contract: Labs Page

## Route

- Method: `GET`
- Path: `/labs/`
- Endpoint: `labs.page`
- Response: HTML, HTTP 200.

## Content Order

1. A title that reads "Labs preview" with the offline statement.
2. The capability status panel. Attribute: `data-testid="labs-capability-status"`.
3. The example panel with the default run name. Attribute: `data-testid="labs-example"`.
4. The run-name form. Attribute: `data-testid="labs-run-name-form"`. The form posts to `POST /labs/plan`.
5. The run-name input. Name: `run_name`. Attribute: `data-testid="labs-run-name-input"`. The input carries a visible label.
6. The hidden CSRF field. Name: `csrf_token`. The template renders it with `csrf_token()`.
7. The submit button. Attribute: `data-testid="labs-submit"`.
8. One result area. It holds one of these attributes: `labs-result`, `labs-unavailable`, or `labs-form-error`.

## Copy Rules

- Use ASCII characters only.
- Use plain words for a junior network operations engineer (FR-026).
- State that the preview is offline and that it contacts no cloud service, device, or provider.
- Name each reason in one plain sentence. Do not show a code alone.

## Forbidden Content

- A deploy, apply, execute, or provider button.
- Raw planner output or raw JSON.
- A form field other than `run_name` and `csrf_token`.
- A token, a secret, or a credential value in markup.

## Navigation

After T014, the navigation holds one `nav-labs` anchor. It follows the `nav-websockets` anchor and links to `url_for('labs.page')`.

## Evidence

- `test_page_shows_status_example_and_plain_offline_copy` (TR-03).
- `test_page_marks_interactive_elements_and_carries_csrf_field` (TR-04).
- Browser journey step 1 (TB-01).
