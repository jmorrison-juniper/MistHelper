# Research: Runtime-Dependent Portal Controls

## Current State

- Current main is commit `58a786c59148f60493bb7ea74b589290a9dd7b28`.
- No open pull request owns the planned source or test files.
- PR #4123 merged the menu 195 exhausted-input repair, and issue #4121 is closed.
- The existing E2E contract tests prove that menus 94, 95, and 96 have their site and device controls.
- Menus 91 and 195 have no `PARAMETER_REGISTRY` entries. The browser therefore returns an empty parameter list for each menu.
- Menu 91 fetches the manufacturer list before its prompt, and its parser accepts a number only.
- Menu 195 prompts for a primary file only when more than one candidate exists. It may then ask for an authority file, a business name, a save-or-quit choice, a write-back confirmation, and a correction-report choice.
- Menu 195 already stops safely when the post-table answer queue is empty. Its write-back gate declines unless the answer is explicitly affirmative.

## Decisions

### Keep the existing registry and prompt queue

**Decision**: Add the menu entries to `PARAMETER_REGISTRY` and build the menu 195 control list when the existing parameter service responds.

**Rationale**: This keeps one parameter source and keeps the current prompt handlers. A new route or a second parameter registry would duplicate ownership.

**Alternatives considered**: Add a route-layer control resolver. Rejected because it would place a second parameter source before the existing registry.

### Use optional manufacturer text and exact file names

**Decision**: Offer menu 91 an optional text field. Let its parser accept an exact manufacturer name and preserve its numeric command-line selection. Use exact file basenames for browser CSV choices and preserve numeric command-line selections.

**Rationale**: The manufacturer list exists only after the operation fetches data. A server-side file list exists when menu 195 controls are built. Exact names avoid mapping a stale browser file choice to a different numbered file.

**Alternatives considered**: Fetch manufacturers when the browser form loads. Rejected because it would add an API request and duplicate the operation fetch. Use a static positional CSV number. Rejected because candidates can change between form build and operation start.

### Validate menu 195 answers before execution

**Decision**: Compare the submitted answer count and choice values with the current menu 195 controls before starting a worker.

**Rationale**: A stale form, malformed request, or file-list change must not shift one browser answer into a later prompt.

**Alternatives considered**: Accept every positional value and rely on each prompt to reject it. Rejected because a retry loop could consume the next control's answer.

### Keep optional writes explicit

**Decision**: Provide safe negative defaults for save, write-back, and correction-report controls. Preserve the existing write-back confirmation.

**Rationale**: The operation changes Mist only after an explicit affirmative answer. Browser defaults must not authorize that change.

**Alternatives considered**: Trigger write-back from a filled correction field. Rejected because a form value is not a clear operator confirmation.

## Out of Scope

- Menus 94 through 96, which already have working controls.
- Issue #4121, which is closed through PR #4123.
- Menus 94 through 96 or any unrelated bug issue.
- New API calls, route adapters, input architectures, or broad rewrites.
