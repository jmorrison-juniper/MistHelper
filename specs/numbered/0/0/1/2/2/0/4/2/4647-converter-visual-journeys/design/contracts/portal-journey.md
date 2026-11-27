# Contract: Converter page journey

This contract defines the page that the journeys in `spec.md` test. It applies to `presentation/converter.html`, `presentation/converter.js`, and `presentation/converter.css`.

## Identity

- Route: `GET /cisco-config-converter/` returns the converter template (RC-18).
- Shell: the page extends the host base template (RC-08). It loads through the host shell and the host theme service.
- Themes: magenta, dark, light, and high-contrast (RC-34).

## Controls and test IDs

Existing IDs stay in place (RC-10, RC-11). New IDs are listed here. Keyboard order is the numbered order in the last column.

| Test ID | Element | Accessible name | Enabled when | Keyboard order |
| - | - | - | - | - |
| `cisco-converter` | Section | Page heading "Cisco Configuration Preview" | Always | Not focusable |
| `cisco-file` | File input | "Configuration file" | Always | 1 |
| `cisco-name` | Text input | "Template name" | Always | 2 |
| `cisco-type` | Select | "Template type" | Always | 3 |
| `cisco-preview` | Button | "Preview" | Form is complete and no preview runs | 4 |
| `cisco-status` | Status region | None, announced politely | Always | Not focusable |
| `cisco-review-summary` | Section with heading "Structured review" | Heading text | After a proposal appears. Focus target with tabindex -1. | Not in tab order |
| `cisco-gateway` | Definition list | "Gateway template" | After a proposal appears | Not focusable |
| `cisco-unsupported` | Table | "Unsupported items" | After a proposal appears | Not focusable |
| `cisco-gaps` | List | "Known gaps" | After a proposal appears | Not focusable |
| `cisco-review` | Button | "Review proposal" | Proposal shown and not reviewed | 5 |
| `cisco-confirm` | Text input | "Type EXPORT to confirm" | Proposal reviewed | 6 |
| `cisco-cancel` | Button | "Cancel confirmation" | Reviewed and the typed word is not empty | 7 |
| `cisco-export` | Button | "Export reviewed JSON" | Typed word equals `EXPORT` | 8 |
| `cisco-reset` | Button | "Reset" | Always | 9 |

## Status text

Each status starts with a word that names the outcome, so color is not needed to read it.

| State | Exact text |
| - | - |
| Idle | Select a file and enter a template name. |
| Previewing | Preparing the proposal. |
| Proposal shown | Proposal ready. Review the unsupported items and known gaps. |
| Reviewed | Proposal reviewed. Type EXPORT to confirm. |
| Wrong word | Type EXPORT exactly to enable export. |
| Confirmed | Export ready. Select Export reviewed JSON. |
| Exported | JSON exported. Mist was not changed. |
| Canceled | Canceled. The typed word was cleared. |
| Reset | Reset. Select a file to start again. |
| Server error | Error: followed by the message from the JSON `error` field |
| Non-JSON error | Error: The request failed. Create a new preview. |

## Focus rules

- After a successful preview, focus moves to `cisco-review-summary`.
- After a successful review, focus moves to `cisco-confirm`.
- After cancel, focus moves to `cisco-confirm`.
- After reset, focus moves to `cisco-file`.
- After export, focus stays on `cisco-export`.
- The focus outline is visible in each shipped theme. The stylesheet uses `var(--portal-focus-ring, currentColor)` for the outline color (RC-35 to RC-38).

## Text and storage rules

- The script writes user text with `textContent` only (RC-12). It never uses `innerHTML` (RC-15).
- The page writes no `localStorage` or `sessionStorage` key. The host theme service may write `misthelper-theme` (RC-32, RC-33).
- The page sends the CSRF header on review and export (RC-23).

## Layout rules

- At the phone viewport (390 by 844) and the desktop viewport (1440 by 900), the document has no horizontal overflow (RC-40).
- Long command text wraps. The stylesheet uses `overflow-wrap: anywhere` on the command cells.
- The stylesheet uses only `var(--portal-*)` tokens for color. It contains no color literal, no image, no font, and no `@keyframes` rule.
