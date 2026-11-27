# Data Model: Unattended token skip for menu 247

Applicable: this change defines the entities, natural keys, and state transitions for one option outcome.

## Entities

| Entity | Natural key | Attributes | Source |
| - | - | - | - |
| Option | The menu number as a string, such as `247`. | Title, category, and skip reason from the registry. | Menu entry in `MistHelper.py` (RC-17). Registry row (RC-16). |
| Operator-only prompt context | The context string, such as `verify_self_email.token`. | Membership in `OperatorPromptPolicy.CONTEXTS`. No default answer for the token. | Token prompt context in the exporter (RC-13). |
| Option outcome | The run start time in UTC ISO 8601 form, plus the option number. | Outcome (pass, fail, or skip), test mode, duration, and reason. | Event fields in the emitter (RC-22 and RC-23). |
| Suite tally | The run. | Success count, error count, skip count (registry skips plus runtime skips), prompt harness failure count, and total time. | Tally dataclass at runner lines 132 to 141 (RC-58 covers the class list). |

The new names do not add an identifier. The natural keys above replace any artificial ID, as the constitution requires.

## State Transitions for One Option

| Start state | Event during the option | End state | Written event | Counter change |
| - | - | - | - | - |
| Started | The handler returns with no ERROR record. | Pass | `test_pass` (RC-06, line 519). | Success count plus one. |
| Started | The handler logs an ERROR record. | Fail | `test_fail` with a synthesized RuntimeError. | Error count plus one. |
| Started | PromptResolutionError is raised (RC-06, line 597). | Fail | `test_fail` with test mode `interactive-prompt`. | Error count plus one. Prompt harness failure count plus one. |
| Started | EOFError is raised (RC-06, line 603). | Fail | `test_fail` with test mode `interactive-cancelled`. | Error count plus one. Prompt harness failure count plus one. |
| Started | OperatorPromptRequired is raised (new). | Skip | `test_skip` with category `operator_prompt` and test mode `interactive-operator-prompt`. | Skip count plus one. Prompt harness failure count unchanged. |
| Started | Any other exception is raised (RC-06, line 609). | Fail | `test_fail` with the current test mode. | Error count plus one. |

## Invariants

- Each option writes one outcome event: pass, fail, or skip. A skip never writes a fail event.
- Exercised operations equal the success count plus the error count (RC-11).
- The skipped total equals the registry skip count plus the runtime skip count (RC-08).
- The coverage denominator equals the number of interactive options. It includes skipped options.
- A run with zero exercised operations has a failure verdict (RC-12).
