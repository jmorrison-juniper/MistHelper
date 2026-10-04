# Research: The multi-site check result uses correct grammar for each count

**Issue**: #3453

## Decision 1: Change the subject of the first sentence

**Decision**: The first sentence becomes "The target version runs on M of T
device" for the total 1, and "The target version runs on M of T devices" for
each other total.

**Rationale**: The old sentence had two words that depend on a count. The
noun depends on the total, and the verb depends on the matched count. The
common case of one device gives "0 of 1 device run the target version" with
the correct rule for each word. That text is correct, but an operator reads
it as an error.

The new subject is "the target version". The subject is singular for each
count, so the verb "runs" never changes. Only the noun depends on a count.
One rule is easier to test than two rules.

**Alternatives considered**:

- Keep the old sentence, and change both the noun and the verb. Issue #3453
  shows this form in its table. The result "0 of 1 device run" reads badly,
  so this change does not use it.
- Write "No device runs the target version" for a matched count of 0. This
  removes the total from the sentence, and it adds one more branch.

## Decision 2: Drop the word "the" from the unread sentence

**Decision**: The unread sentence becomes "The portal could not read U of T
device" for the total 1, and "devices" for each other total.

**Rationale**: The old text "1 of the 1 devices" is wrong. The text "1 of the
1 device" is also strange. The text "1 of 1 device" reads correctly, and it
matches the first sentence.

## Decision 3: Keep the rule inside the check class

**Decision**: A new static method of `OrgReconcileCheck` returns "device" or
"devices" for a total.

**Rationale**: `stop.py` has a private function with the same rule. A private
function of another module is not a public contract, so this change does not
import it. A shared plural helper for all modules is out of scope.

## Finding: The places that show or store the text

| Place | Role |
| - | - |
| `src/interfaces/portals/upgrade_portal/upgrade/org_reconcile.py`, `_summary` | Writes the text. |
| `src/interfaces/portals/upgrade_portal/upgrade/org_reconcile.py`, `OrgUncertainChild.view` | Reads the stored text for the page. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_progress.html`, line 251 | Shows the text after "Last check". |
| The JSON answer of the check route | Returns the verdict of each child job. |

## Finding: The tests that read the old text

| Test | Reads |
| - | - |
| `tests/contract/upgrade_portal/test_org_child_controls_routes.py`, line 700 | The stored text of a real check. |
| `tests/e2e/upgrade_portal/test_org_recovery_controls.py`, line 183 | The page text of a real check. |
| `tests/unit/firmware/test_aggregate_child_controls.py`, lines 179 and 199 | A stand-in text only. |
| `tests/unit/upgrade_portal/test_org_child_controls.py`, lines 308 and 310 | A stand-in text only. |

The two stand-in files test how the service stores a summary. They do not
test the grammar. This change updates their text, so no test file keeps the
old grammar as an example.