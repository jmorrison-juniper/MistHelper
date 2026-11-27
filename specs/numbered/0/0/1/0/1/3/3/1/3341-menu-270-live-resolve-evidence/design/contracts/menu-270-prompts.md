# Contract: Menu 270 Prompt Order

The web portal row holds seven controls in the order of the seven prompts (research row 23). The menu and the portal use these same prompt names.

## Controls in Prompt Order

| Prompt | Control name | Purpose in mode 3 |
| - | - | - |
| 1 | `marvis_mode` | Selects the mode. The live check answers `3`. |
| 2 | `marvis_category` | Selects the category of the actions. |
| 3 | `marvis_subcategory` | Selects the subcategory of the actions. |
| 4 | `marvis_resolution_code` | Selects the resolution code. The approved attempt used `suggested`. |
| 5 | `marvis_comment` | Gives the comment of the run. |
| 6 | `marvis_confirmation` | Takes the typed text RESOLVE followed by the count (row 17). The live check types `RESOLVE 1`. |
| 7 | `marvis_alarm_ack_confirmation` | Takes the optional acknowledge text. The live check leaves it blank. |

## Rules for the Live Check

- Answer each prompt in order.
- Prompt 7 accepts a blank answer. The live check leaves it blank (FR-004).
- A wrong answer at prompt 6 sends no request (test 12 in the test set of `tasks.md`).
- A blank answer at prompt 6 sends no request (test 22 in the test set of `tasks.md`).
