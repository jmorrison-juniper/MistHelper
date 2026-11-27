# Implementation Plan: Menu step names the generated pages

**Branch**: `docs/4922-constitution-menu-doc-step` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/4/2/4922-constitution-menu-doc-step/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record omits the contracts folder. The section Contracts explains why.

## Summary

Amend step 5 and the README bullet of the constitution. Amend step 1 of "Add a menu operation" in the rule file. Add one guard method and one changelog fragment. The change edits Markdown and one guard test module. It changes no runtime code.

## Technical Context

- **Language/Version**: Markdown for the guidance files. Python 3.15 for the guard test, the minimum that `.github/copilot-instructions.md` sets.
- **Primary Dependencies**: pytest for the guard test. Ruff and Black for the test module. `ste-linter` from `misthelper-devtools` for the STE gate.
- **Storage**: None.
- **Testing**: The guard class, the STE gate, and the test quality ratchet. The commands are in `design/quickstart.md`.
- **Target Platform**: Windows 11, macOS, and Linux. The guard builds paths with `pathlib.Path`.
- **Project Type**: Governance text and one guard test module.
- **Performance Goals**: None. The guard reads two Markdown files.
- **Constraints**: STE rules in `AGENTS.md`. LF line endings, as the constitution, the rule file, and the changelog README use. No new direct child in `tests/guardrails/`.
- **Scale/Scope**: Four files change. One record folder is added. Five guard cases are added.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule | Pass | The change adds no direct child to `tests/guardrails/`, which holds 79 children (RC-28). The new method joins `TestPolicyStaysStated`, which holds four methods now and five after the change. The module keeps its top-level children. The record folder holds five children or fewer. |
| II. Class-Based Architecture | Pass | The new method sits in an existing class. The change adds no standalone wrapper function. |
| III. Safety-First | Pass | The change reads no operator input and runs no operation. It adds no secret and no destructive command. |
| IV. Full Deployment Pipeline | Pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run each step in order. The agent does not merge without authorization. |
| V. Observability and Logging | Pass | The change adds no runtime log. The guard asserts text and logs nothing. |
| VI. Inline Comments | Pass (planned) | Each executable line of the new method carries an inline comment on the same line. |
| VII. Action Logging | Pass | The change adds no runtime action. The guard method performs file reads and assertions only. |
| Mist Cloud transport | Not applicable | The change calls no Mist REST endpoint and no mistapi function. |
| Container runtime | Not applicable | The change starts no container. |
| File paths | Pass | The guard builds each path with `Path`. No path uses a hardcoded separator. |
| Data directory | Not applicable | The change writes no product output. |
| Database keys and operational store | Not applicable | The change stores no data. |
| Adding New Menu Operations | Pass | The change amends step 5 only. Steps 1 to 4, 6, and 7 stay as written. |
| Documentation | Pass | The README bullet and the rule file change in this pull request. The README stays a start guide. |
| Release notes | Pass | One fragment is added. Decision D-6 explains the choice. |
| Governance amendment procedure | Pass | The version increments as PATCH. `Last Amended` changes to 2026-11-26. The Sync Impact Report changes. No template names the README menu step, so no template changes. |
| Compliance review and Complexity Tracking | Pass | The existing debt in `tests/guardrails/` is recorded in Complexity Tracking. The change adds no new debt. |
| Conventional Commits | Pass (planned) | The commit subject and the pull request title use the prefix `docs(constitution):`. |

## Architecture

Three guidance surfaces describe the menu procedure.

- The constitution (`.specify/memory/constitution.md`) governs the procedure. Its step 5 and its README bullet change.
- The rule file (`.github/copilot-instructions.md`) gives the same procedure to agents. Its step 1 changes.
- The changelog policy (`changelog.d/README.md`) and constitution step 6 require one fragment for each change.

The generated pages hold the menu list.

- `scripts/generate_menu_wiki.py` writes `documentation/wiki/Menu-Reference.md` and `documentation/menu_reference.md` (RC-12, RC-13).
- The `menu_reference_drift` job in `.github/workflows/ci.yml` compares both pages after the generator runs (RC-16).
- `scripts/menu_api_map/__main__.py` runs as a module (RC-17).

The guard reads the guidance files by path. The new method checks required and forbidden text inside a slice that starts and ends at a marker.

## File-by-File Change Map

| Path | Action | Change |
| --- | --- | --- |
| `.specify/memory/constitution.md` | Modify | Replace the Sync Impact Report fields (lines 4 to 24). Replace step 5 (lines 352 and 353). Replace the README bullet (lines 400 and 401). Replace the footer (line 562). |
| `.github/copilot-instructions.md` | Modify | Replace step 1 under "Add a menu operation" (line 242). |
| `tests/guardrails/test_changelog_fragment_policy.py` | Modify | Add one parametrized method at the end of `TestPolicyStaysStated`, after line 264. |
| `changelog.d/issue-4922-constitution-menu-doc-step.md` | Add | One release-note fragment. |
| `specs/numbered/0/0/1/2/4/1/4/2/4922-constitution-menu-doc-step/` | Add | This record. |

Unchanged on purpose: `README.md`, `documentation/operator-guide.md`, `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `scripts/generate_menu_wiki.py`, `.github/workflows/ci.yml`, `.github/workflows/ste-lint.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, and the historical spec records.

## Exact Text

Each block replaces the lines named in the heading. Keep the line endings as LF.

### Step 5 (constitution lines 352 and 353)

```text
5. **Update the generated menu pages** — Run `python scripts/generate_menu_wiki.py` and
   `python -m scripts.menu_api_map`, then commit the changed pages. The pages are
   `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md`. Add operator
   notes to `documentation/operator-guide.md` when the operation needs operator steps.
```

### README bullet (constitution lines 400 and 401)

```text
- **README.md**: Short start guide. It states what MistHelper is, shows how to start the
  container, and links to every other page. It holds no menu number and no per-operation text.
  Operator details live in `documentation/operator-guide.md`.
```

### Rule file step 1 (line 242)

```text
1. Add operator notes to `documentation/operator-guide.md` when the operation needs operator steps. Do not add a menu number to `README.md`.
```

### Sync Impact Report fields (lines 4 to 24, from `Version change` to `Follow-up actions`)

```text
  Version change: 1.9.0 -> 1.9.1 (PATCH)
  Bump rationale: PATCH, because the amendment corrects the menu step and the
    README bullet to match the README rule of issue #4916.
  Modified principles: None.
  Modified sections:
    - Development Workflow & Quality Gates: the menu step and the README bullet
      name the generated menu pages and the operator guide.
  Added sections: None.
  Removed sections: None.
  Templates requiring updates:
    - .specify/templates/plan-template.md: no update required.
    - .specify/templates/spec-template.md: no update required.
    - .specify/templates/tasks-template.md: no update required.
    - .specify/templates/checklist-template.md: no update required.
    - .specify/templates/agent-file-template.md: no update required.
    - .specify/templates/constitution-template.md: no update required.
  Related files updated simultaneously:
    - .github/copilot-instructions.md: step 1 of "Add a menu operation".
    - changelog.d/issue-4922-constitution-menu-doc-step.md: the release-note fragment.
    - tests/guardrails/test_changelog_fragment_policy.py: the guard cases for the menu step.
  Follow-up actions: Issue #4915 tracks the stale operation count in the operator guide.
```

### Footer (constitution line 562)

```text
**Version**: 1.9.1 | **Ratified**: 2026-03-05 | **Last Amended**: 2026-11-26
```

### Changelog fragment (new file)

```text
### Menu step names the generated pages

- **Changed**: The constitution and the agent instruction file name the generated menu pages and the operator guide for a new menu operation. They no longer name the README menu table. Issue #4922.
```

## Guard Cases

Add one method at the end of `TestPolicyStaysStated` in `tests/guardrails/test_changelog_fragment_policy.py`.

- **Name**: `test_menu_step_and_version_record_stay_stated`.
- **Parameters**: five, in this order: `relative_path`, `start_marker`, `end_marker`, `required_text`, and `forbidden_text`. The method stays within the five-parameter limit.
- **Cases**: the five rows of the table below, each with a case ID.
- **Body**: read the file as UTF-8 text. Find the start marker, and fail with the case ID when the marker is absent. Cut the text at the end marker. When the end marker is `None`, keep the rest of the text. Assert that each required text appears in the cut. Assert that each forbidden text is absent from the cut.
- **Limits**: at most three logical blocks and 25 lines. Each executable line carries an inline comment.

| Case ID | `relative_path` | `start_marker` | `end_marker` | `required_text` | `forbidden_text` |
| --- | --- | --- | --- | --- | --- |
| `menu-step` | `.specify/memory/constitution.md` | `5. **Update` | `6. **Release Note**` | `scripts/generate_menu_wiki.py`, `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `documentation/operator-guide.md` | `menu table`, `Update README`, `operation count` |
| `readme-bullet` | `.specify/memory/constitution.md` | `- **README.md**:` | `- **AGENTS.md**` | `holds no menu number`, `no per-operation text`, `documentation/operator-guide.md` | `MUST be updated for` |
| `rule-file-step` | `.github/copilot-instructions.md` | `### Add a menu operation` | `2. Run` | `documentation/operator-guide.md`, `Do not add a menu number to` | `menu table`, `Update the operation count` |
| `footer-version` | `.specify/memory/constitution.md` | `**Version**:` | `None` | `**Version**: 1.9.1`, `**Last Amended**: 2026-11-26` | none |
| `sync-report` | `.specify/memory/constitution.md` | `Version change:` | `Bump rationale:` | `1.9.0 -> 1.9.1 (PATCH)` | `(MINOR)` |

Each case fails on the unchanged text. The `menu-step` case fails because step 5 still names the README table. The `readme-bullet` case fails because the bullet still says MUST. The `rule-file-step` case fails because line 242 still names the README table. The `footer-version` and `sync-report` cases fail because the version is still 1.9.0.

## Dependencies

- No new package and no new tool. The guard uses pytest. The STE gate uses `ste-linter`, which `requirements-dev.txt` supplies through `misthelper-devtools`.
- The change depends on issue #4916, which is closed. Its README state is on `main` (RC-09).
- The change does not depend on issue #4915.

## Risks and Mitigations

- **A marker changes in a later edit**: The guard fails and names the case ID. The editor repairs the marker in the same pull request.
- **The STE score of `.github/copilot-instructions.md` falls below 80**: T-LOCAL-GATES runs the STE gate. The author repairs the sentence and runs the gate again.
- **The constitution is outside the CI STE list**: A low score does not block CI. T-LOCAL-GATES measures the score, and the pull request body reports it (D-9).
- **A reviewer contests the PATCH class**: The removed MUST came from the README rule. The Sync Impact Report and the pull request body state the reason (D-5). The reviewer can change the class before the merge.
- **The changelog rules conflict**: Constitution step 6 requires a fragment for each change. Rule 4 of `changelog.d/README.md` exempts an internal-only change. D-6 follows the constitution, and `analysis.md` records the conflict.
- **Historical records quote the old step**: The records stay unchanged (D-8). The constitution and the rule file give the current step.

## Rollback

1. Close the pull request before the merge. Delete the branch `docs/4922-constitution-menu-doc-step`.
2. After the merge, open a new issue for the revert. Branch from `main`, revert the four files, and open a new pull request.
   Caution: revert all four files in one commit. A partial revert leaves the two guidance files in conflict.
3. Warning: do not force-push `main`. A force-push removes commits of other changes, and no run reports the loss.

## Contracts

Omitted. The change adds no menu, CLI, API, or output interface. The required and forbidden text of each guard case, in the table above, defines the contract.

## Complexity Tracking

Existing debt that the change touches or avoids. None of it is new debt.

| Item | Kind | Why it stays | Remediation |
| --- | --- | --- | --- |
| `tests/guardrails/` holds 79 direct children (RC-28) | Grandfathered | The change adds no direct child there. | A follow-up issue moves the guard modules into a compliant package. This change does not move them. |
| `tests/guardrails/test_changelog_fragment_policy.py` holds more than five top-level definitions | Grandfathered | The change adds a method to `TestPolicyStaysStated`. The class holds four methods now and five after the change, which the rule allows. | The same follow-up issue splits the module. |

New design that needs a reason.

| Item | Why it is needed | Simpler alternative rejected because |
| --- | --- | --- |
| The guard reads marker slices and exact phrases | A slice limits each check to one step or one bullet. | A full-sentence match breaks on a reworded sentence. A Markdown parser adds a dependency. |
| One parametrized method holds five cases | It keeps the class at five methods. | A new class adds a top-level child to a module that already holds more than five. A new file adds a direct child to a noncompliant folder. |
