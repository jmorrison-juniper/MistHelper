# Implementation Plan: Upgrade Spec Kit scaffolding to 1.4.3 and keep the routed layout

**Branch**: `chore/4869-speckit-1-4-3` | **Issue**: #4869 | **Spec**: `spec.md`

## Summary

Move the Spec Kit scaffolding from 1.1.2 to 1.4.3 in the parts that do not carry the routed layout. Keep the routed core, the git extension, and the companion extension unchanged. Record each kept file and its reason.

## Technical Context

- Language: PowerShell 7 scripts, Markdown skill files, and JSON markers.
- Line endings: `.gitattributes` stores `.ps1` files with LF in the index and with CRLF in the working tree. Markdown and JSON files use LF.
- Source of the 1.4.3 content: the output of `specify integration upgrade --force` in a scratch clone of the repository. The plan copies this output for each file that it takes.
- Merge base for the local edits: the pristine 1.1.2 content. The plan verifies it against the integration manifest hash for each file that it merges.

## Decisions for Each Managed File

| File | Decision | Reason |
| - | - | - |
| `.specify/init-options.json`, `.specify/integration.json` | Use 1.4.3 | Version markers |
| `.specify/integrations/*.manifest.json` | Use 1.4.3 | Manifests match the CLI output. Kept files differ on purpose. |
| `scripts/powershell/check-prerequisites.ps1` | Merge, keep the local docs block | Local `-NoPersist` call and local docs paths |
| `scripts/powershell/setup-plan.ps1` | Merge, no conflict | Local `-NoPersist` call and five-children guard |
| `scripts/powershell/setup-tasks.ps1` | Merge, keep the local docs block | Local `-NoPersist` call and five-children guard |
| `scripts/powershell/resolve-template.ps1` | Merge, no conflict | Local edit only |
| `scripts/powershell/common.ps1` | Keep the repository version, add `ConvertTo-AsciiJson` | Routed core stays |
| `scripts/powershell/create-new-feature.ps1` | Keep the repository version | Routed numbering |
| `scripts/powershell/markdown_sections.py` | Use 1.4.3 (new file) | Helper file in the 1.4.3 set |
| `templates/constitution-template.md` | Use 1.4.3 | No local edit |
| `templates/checklist-template.md`, `plan-template.md`, `spec-template.md`, `tasks-template.md` | Keep the repository version | Routed rules |
| `skills/speckit-analyze`, `speckit-checklist`, `speckit-clarify`, `speckit-constitution`, `speckit-converge`, `speckit-implement` | Use 1.4.3 | No local edit |
| `skills/speckit-plan`, `speckit-specify`, `speckit-tasks` | Merge, no conflict | Local edit only |
| `skills/speckit-git-*`, `skills/speckit-taskstoissues` | Keep the repository version | Git extension 1.0.0 |
| `agents/speckit.git.*` | Keep the repository version | Git extension 1.0.0 |
| `extensions/git/**`, `extensions/.registry`, `extensions.yml` | Keep the repository version | Git extension and companion registry |
| `.specify/.gitignore` | Do not add | It would ignore `feature.json` |

## Verification Plan

1. Parse each changed `.ps1` file. Expect zero errors.
2. Parse each changed JSON file. Expect no error.
3. Run the four setup scripts in the worktree with `SPECIFY_FEATURE` set to this feature. Expect exit 0 and JSON output.
4. Run `create-new-feature.ps1 -DryRun`. Expect a path under `specs/numbered/`.
5. Run the guardrail tests that cover `.specify`, the skills, and the changelog policy. Record the examined counts.
6. Run `ste-linter` on the new spec files when the tool is available.
7. Confirm that `git status` reports no change to `.specify/feature.json`.

## Constitution Check

- Five children at most for each structural directory. The feature directory contains three files.
- No secret in any file.
- The helper for JSON writes only ASCII characters.
- The routed core does not change.
