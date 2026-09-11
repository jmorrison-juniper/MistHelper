# UI Contract: Stale and Bulk Run Controls

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Version**: 2

This contract defines the history page, run page, and browser state.

## 1. History Run Row

| Element | Behavior | Test identifier |
| - | - | - |
| Selection checkbox | Selects one visible run. | `history-run-select-{run_id}` |
| Last update age | Shows a short age or `unknown`. | `history-run-age-{run_id}` |
| Stale badge | Shows `Stale` only for a stale run. | `history-run-stale-{run_id}` |

A final run can show an old age and no stale badge. Text and shape identify the
stale state. Color is not the only signal.

## 2. Browser Selection

The page stores candidate identifiers in `sessionStorage`.

```text
upgrade-run-selection:<organization-id>:<history-scope>
```

Rules:

1. Reload, back, and forward restore the candidate list.
2. Another tab keeps an independent candidate list.
3. Restore never submits an action.
4. A clear control removes the current candidate list.
5. The browser refuses a 51st candidate.
6. Stored identifiers do not define visible counts.
7. Confirmation cannot open before an authoritative preview.

## 3. Authoritative Preview

When the operator selects cancel or retry, the browser calls the preview
endpoint before it displays phrase input.

The server removes identifiers outside the current organization and history
scope. The browser then replaces `sessionStorage` with the returned identifiers.

The dialog uses only server values:

- Ordered run identifiers.
- Total run count.
- Total site count.
- Per-site counts.
- Exact phrase.
- Signed preview token.

If the preview returns no visible run, the dialog does not open.

## 4. Bulk Action Bar

| Element | Required content | Test identifier |
| - | - | - |
| Region | Candidate run count and visible warning. | `bulk-run-action-bar` |
| Candidate count | Browser candidate count. | `bulk-run-count` |
| Cancel control | Requests a cancel preview. | `bulk-cancel-button` |
| Retry control | Requests a retry preview. | `bulk-retry-button` |
| Clear control | Clears current candidates. | `bulk-clear-button` |
| Limit message | Explains the 50-run limit. | `bulk-selection-limit` |

The bar does not claim a site count before preview.

## 5. Confirmation Dialog

| Element | Required content | Test identifier |
| - | - | - |
| Dialog | Server action and exact counts. | `bulk-confirm-dialog` |
| Action text | Cancel or retry text. | `bulk-confirm-action` |
| Run count | Authoritative run count. | `bulk-confirm-run-count` |
| Site count | Authoritative site count. | `bulk-confirm-site-count` |
| Site list | One server row for each site. | `bulk-confirm-site-{site_id}` |
| Removed notice | Count of pruned hidden identifiers. | `bulk-preview-removed` |
| Phrase label | Exact server phrase. | `bulk-confirm-phrase` |
| Phrase input | Operator text. | `bulk-confirm-input` |
| Submit control | Disabled until exact match. | `bulk-confirm-submit` |
| Close control | Closes without a request. | `bulk-confirm-close` |

The request includes the signed preview token. A preview mismatch or expiry
closes the phrase step and requires a new preview.

## 6. Bulk Result Panel

| Element | Required content | Test identifier |
| - | - | - |
| Region | Action identifier and class totals. | `bulk-result-panel` |
| Summary count | One value for each class. | `bulk-result-count-{classification}` |
| Result row | Run, site, class, reason, message, and link. | `bulk-result-{run_id}` |
| Class text | One of the four class names. | `bulk-result-class-{run_id}` |
| Run link | Opens the source or new run. | `bulk-result-open-{run_id}` |
| Refresh control | Reads the action only. | `bulk-result-refresh` |

The panel lists every requested run exactly once. It includes
`not_processed`, `not_processed_after_site_guard_loss`, and
`processing_interrupted` outcomes.

After response loss, the page claims no success. It offers the read-only
refresh control. A later read can show `processing` or the recovered complete
result.

## 7. Run Page

| Element | Required content | Test identifier |
| - | - | - |
| Age | Same age rule as the history row. | `run-last-update-age` |
| Stale badge | `Stale` only for a stale run. | `run-stale-badge` |
| Reconcile region | Action and evidence warning. | `run-reconcile-controls` |
| Reconcile input | Typed phrase. | `run-reconcile-input` |
| Reconcile submit | Starts one reconciliation. | `run-reconcile-submit` |
| Reconcile result | Shows one action outcome. | `run-reconcile-result` |

The reconcile region appears only for stale pre-cloud or stale `stopping`.
The exact phrase is `RECONCILE <run_id>`.

The reconciliation control submits no preview token. It creates one durable
single-run action.

The `stopping` warning states that the portal only reads evidence. It states
that the portal sends no new stop request.

## 8. Durable Actor Behavior

A renewed browser session for the same normalized actor can read the same
action result.

Another actor receives `action_not_found`. The page does not reveal another
actor's existence, identity, request, or result.

## 9. Keyboard and Focus

1. A keyboard user can reach each row checkbox.
2. The action bar follows the table in tab order.
3. Preview completion moves focus to the dialog title.
4. Closing returns focus to the opening control.
5. A completed request moves focus to the result heading.
6. Each result class appears as text.
7. An error region uses an alert role.

## 10. Responsive Viewports

The required widths are 360, 768, and 1280 pixels.

At 360 pixels:

- The table can scroll horizontally.
- The checkbox remains the first visible column.
- The action bar wraps.
- The dialog stays inside the viewport.
- The phrase input uses the available width.
- Result identifiers wrap without covering a control.

## 11. Browser Workflows

| Workflow | Expected result |
| - | - |
| Hidden stored ID | Preview removes it before phrase entry. |
| Duplicate ID | Preview refuses the request. |
| One site | One confirmation uses exact server counts. |
| Multiple sites | Each item receives a current guard check. |
| Guard loss | Later writes for that site stop. |
| Mixed eligibility | Other valid sites continue. |
| Session renewal | The same durable actor can read the result. |
| Another actor | The result endpoint returns 404. |
| Network failure | The page offers a read-only refresh. |
| Reload | Candidates return and no action repeats. |
| Multiple tabs | Candidate lists remain independent. |
| Responsive viewport | All controls remain usable. |
