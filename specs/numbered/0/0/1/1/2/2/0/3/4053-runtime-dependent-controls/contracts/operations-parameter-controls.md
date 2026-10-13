# Operations Parameter Controls Contract

## Read Menu Parameters

The existing `GET /api/operations/parameters/<menu_number>` endpoint returns the controls that the browser must render.

Menu 91 returns one optional text control named `manufacturer`.

Menu 195 returns controls for the prompts that may run. The file controls reflect the current server-side CSV and TSV candidates. The primary file control is absent when zero or one candidate exists. If there are no candidates, menu 195 returns an empty parameter list.

Every rendered control has a stable `data-testid` derived from its parameter name. Each menu 91 and 195 control also names the `InputUtils.safe_input` context that receives its answer.

## Start Menu 195

The existing `POST /api/operations/run` request carries menu 91 and 195 answers in `parameters.input_context_answers`. The object keys match the contexts returned by the parameter endpoint.

The service checks context names, required values, and choice values against current controls before it starts a worker. If a file choice is stale or a value is invalid, the service returns an error and starts no operation. It fills omitted optional values with their safe defaults.

The existing positional answer format remains unchanged for other menus. A skipped conditional prompt cannot consume another prompt's answer.

## Safe Choices

- Quit is the initial post-table choice. Save requires an explicit selection.
- The portal batch write-back gate accepts only no. The CLI provides the per-site confirmation required for writes.
- The service rejects affirmative portal answers before a worker starts. It does not convert them into successful read-only runs.
- Each site still requires its existing approval. A missing browser context raises `EOFError` and fails the operation.
- Correction-report saving keeps its existing no default.
- Empty or exhausted answers do not authorize a write.
