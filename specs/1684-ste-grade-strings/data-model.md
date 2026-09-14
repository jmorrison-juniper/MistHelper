# Data Model: Grade Python user text in the STE linter

## Python string span

A Python string span is a `ProseSpan` with these fields.

| Field | Value |
| - | - |
| `text` | The cleaned prose from the string literal. |
| `start_line` | The 1-based line of the call argument. |
| `kind` | `logging` or `user-facing`. |

The parser removes placeholders and quoted code tokens before it writes `text`.

## String grading configuration

`LinterConfig` holds these fields.

| Field | Default | Purpose |
| - | - | - |
| `grade_logging_strings` | `False` | Enables logging string spans. |
| `grade_user_facing_strings` | `False` | Enables print and prompt string spans. |
| `logging_call_names` | The six `logging.*` methods | Selects logging calls. |
| `user_facing_call_names` | `print`, `safe_input` | Selects user-facing calls. |

The command line can set the two Boolean fields to `True` for one run.
