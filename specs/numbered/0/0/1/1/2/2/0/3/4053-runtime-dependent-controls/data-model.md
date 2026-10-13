# Data Model: Runtime-Dependent Portal Controls

## Browser Parameter

| Field | Meaning | Validation |
| --- | --- | --- |
| `name` | Stable form field and prompt identity | Unique within one menu form |
| `label` | Text shown to the operator | Non-empty |
| `param_type` | Browser control type | `choice` or `text` for this repair |
| `answer_context` | `InputUtils.safe_input` prompt that receives the value | Matches one current prompt context |
| `required` | Whether the browser must submit a value | Required for primary file and post-table choice |
| `options` | Allowed choice values and labels | Each submitted choice must match a current value |
| `default` | Safe initial selection | Quit, skip, or no for optional actions |

## Menu 91 Manufacturer Answer

The optional answer is an exact manufacturer name or an existing numeric selection. An empty value means all manufacturers. An unknown name does not select a different manufacturer.

## Menu 195 Address-File Choice

The candidate set contains current CSV and TSV basenames from `data/`. The primary-file control appears only when more than one candidate exists. The authority-file control appears when at least one candidate exists and includes a skip choice. The operation confirms each submitted basename against its current candidate set.

## Menu 195 Conditional Answers

Each form value maps to its prompt context, not to a fixed queue position:

1. Primary file, when multiple candidates exist.
2. Authority file, when candidates exist.
3. Business name, when `BUSINESS_NAME` is empty.
4. Save or quit.
5. Write-back approval, with no as the safe default.
6. Correction-report save remains an existing prompt with no as the safe default.

The operation may skip prompts based on the selected action and audit results. It must not use an answer for a different prompt. Per-site write-back still needs a separate approval and an unanswered browser prompt uses no.
