# Contract: UnattendedInteractiveInputProvider.answer

**Location**: `src/foundation/support/menu_testing/interactive_test_runner.py`. The class starts at line 84, and the method starts at line 104 (rows RC-01 and RC-02 in `design/research.md`).

**Signature** (unchanged): `answer(prompt: str, default_value: str = "", allow_empty: bool = True, context: str = "unknown") -> str`

## Inputs

- `prompt`: The prompt text. The rule table reads it with the context.
- `default_value`: The default answer. A non-empty value wins.
- `allow_empty`: Whether an empty answer is valid for an optional prompt with no rule.
- `context`: The prompt context. The operator-only check reads this value.

## Outputs and Errors

| Condition | Result |
| - | - |
| `default_value` is non-empty | Returns `default_value`. |
| `context` is in `OperatorPromptPolicy.CONTEXTS`, and `default_value` is empty | Raises `OperatorPromptRequired`. No rule runs. |
| No rule matches, and `allow_empty` is true | Returns an empty string (RC-02). |
| No rule matches, and `allow_empty` is false | Raises `PromptResolutionError` (RC-03). |

## Logs

- Before the operator-only raise, the method writes one info line. The line names the option and the context. The line never names a token value.
- The existing info line before each answer and the existing debug line after each answer stay in place.

## Invariants

- The provider never generates a token value.
- The provider does not restore the input seam. The runner owns the restore (RC-05).
- Only the context list decides an operator-only stop. The option number never decides it.

## Compatibility

Every context outside the list keeps its current answer. The signature does not change.
