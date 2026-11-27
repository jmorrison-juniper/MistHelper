# Contract: Structured Review Page

The version 2 controls share the page of version 1 at `/cisco-config-converter/`. The page keeps every version 1 control and adds one section. The section has its own script, `presentation/proposal_review.js`, which loads after `converter.js`.

## Placement

- The section sits below the version 1 controls.
- The section holds the test ID `cisco-structured`.
- Version 1 test IDs keep their current names: `cisco-upload`, `cisco-file`, `cisco-name`, `cisco-type`, `cisco-preview`, `cisco-status`, `cisco-proposal`, `cisco-review`, and `cisco-export`.

## New Test IDs

| Test ID | Element | Behavior |
| - | - | - |
| `cisco-structured` | Section | Holds the version 2 controls and the result sections. |
| `cisco-structured-preview` | Button | Posts the source to `/cisco-config-converter/v2/preview`. It is enabled when a file and a name exist. |
| `cisco-structured-review` | Button | Posts the proposal to `/cisco-config-converter/v2/review`. It stays disabled until a preview succeeds. |
| `cisco-structured-export` | Button | Posts the proposal to `/cisco-config-converter/v2/export` and downloads the response. It stays disabled until a review succeeds. |
| `cisco-structured-status` | Paragraph with `role="status"` and `aria-live="polite"` | Shows plain text status or the server error text. |
| `cisco-scope` | List | One item for each scope field. Null hardware and target fields show `Not selected`. |
| `cisco-object-changes` | List | One item for each object change. |
| `cisco-omissions` | List | One item for each omission. |
| `cisco-unresolved` | Paragraph | Shows `None` when the list is empty. Otherwise it shows one item for each mapping. |
| `cisco-verification` | List | Three items: the local schema result, the cloud state result, and the reason. |

## Request Rules

- The preview request builds a `FormData` object from `#cisco-file`, `#cisco-name`, and `#cisco-type`. It adds the `csrf_token` value from the hidden input inside `#cisco-upload`.
- The preview request does not submit the `#cisco-upload` form. The version 1 submit handler owns that form.
- The review and export requests send the proposal object as JSON. They send the `X-CSRFToken` header from the `csrf-token` meta tag.
- The export downloads the same object that the review request sent. The file name is `cisco-proposal-v2.json`.

## State Rules

- The page keeps the last proposal in memory only.
- A change in `#cisco-upload` resets the version 2 state. The reset disables review and export and clears the result sections.
- A failed request shows the server `error` text in `cisco-structured-status`.
- The page stores no source text, no proposal, and no digest in browser storage.

## Rendering Rules

- Each value uses `textContent`. The script never uses `innerHTML` for a value from the server or from the source.
- Each entry in a list is one list item.
- The page uses plain words for an operator in a network operations center.

## Accessibility Rules

- Each control is a native button with visible text.
- Status changes never use color alone. Each status is a sentence.
- Keyboard focus stays on the button that started the action after each update.
