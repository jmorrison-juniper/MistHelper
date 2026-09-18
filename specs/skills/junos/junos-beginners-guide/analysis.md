# SpecKit catalog

## Installed settings

- `extensions.yml`: present
- `feature.json`: present
- `init-options.json`: present
- `integration.json`: present

## Commands

| Command | Installed | Consumes | Emits |
| - | - | - | - |
| `speckit.analyze` | yes | spec.md, plan.md, tasks.md, and constitution | read-only analysis report |
| `speckit.checklist` | yes | spec.md, plan.md, tasks.md, and checklist template | checklists/*.md |
| `speckit.clarify` | yes | spec.md | updated spec.md |
| `speckit.companion.after-implement` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.after-plan` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.after-specify` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.after-tasks` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.auto` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.classify` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.implement` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.living-adopt` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.living-coverage` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.living-drift` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.living-move` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.living-sync` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.mark-complete` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.plan` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.resume` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.specify` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.status` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.companion.tasks` | no | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.constitution` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.converge` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.git.commit` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.git.feature` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.git.initialize` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.git.remote` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.git.validate` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |
| `speckit.implement` | yes | current feature artifacts and extension state | checked tasks and source changes |
| `speckit.plan` | yes | spec.md, constitution, and plan template | plan.md, research.md, data-model.md, quickstart.md, and contracts |
| `speckit.specify` | yes | feature text and spec template | spec.md |
| `speckit.tasks` | yes | spec.md, plan.md, research.md, data-model.md, contracts, and tasks template | tasks.md |
| `speckit.taskstoissues` | yes | current feature artifacts and extension state | .spec-context.json or extension-specific state |

## Templates

- `.specify\templates\agent-file-template.md`
- `.specify\templates\checklist-template.md`
- `.specify\templates\constitution-template.md`
- `.specify\templates\plan-template.md`
- `.specify\templates\spec-template.md`
- `.specify\templates\tasks-template.md`

## Scripts

- `.specify\scripts\powershell\check-prerequisites.ps1`
- `.specify\scripts\powershell\common.ps1`
- `.specify\scripts\powershell\create-new-feature.ps1`
- `.specify\scripts\powershell\setup-plan.ps1`
- `.specify\scripts\powershell\setup-tasks.ps1`
- `.specify\scripts\powershell\update-agent-context.ps1`

## Extensions

- `.specify\extensions\.registry`
- `.specify\extensions\extensions\.registry`
- `.specify\extensions\extensions\git\commands\speckit.git.commit.md`
- `.specify\extensions\extensions\git\commands\speckit.git.feature.md`
- `.specify\extensions\extensions\git\commands\speckit.git.initialize.md`
- `.specify\extensions\extensions\git\commands\speckit.git.remote.md`
- `.specify\extensions\extensions\git\commands\speckit.git.validate.md`
- `.specify\extensions\extensions\git\config-template.yml`
- `.specify\extensions\extensions\git\extension.yml`
- `.specify\extensions\extensions\git\git-config.yml`
- `.specify\extensions\extensions\git\README.md`
- `.specify\extensions\extensions\git\scripts\bash\auto-commit.sh`
- `.specify\extensions\extensions\git\scripts\bash\create-new-feature.sh`
- `.specify\extensions\extensions\git\scripts\bash\git-common.sh`
- `.specify\extensions\extensions\git\scripts\bash\initialize-repo.sh`
- `.specify\extensions\extensions\git\scripts\powershell\auto-commit.ps1`
- `.specify\extensions\extensions\git\scripts\powershell\create-new-feature.ps1`
- `.specify\extensions\extensions\git\scripts\powershell\git-common.ps1`
- `.specify\extensions\extensions\git\scripts\powershell\initialize-repo.ps1`
- `.specify\extensions\git\commands\speckit.git.commit.md`
- `.specify\extensions\git\commands\speckit.git.feature.md`
- `.specify\extensions\git\commands\speckit.git.initialize.md`
- `.specify\extensions\git\commands\speckit.git.remote.md`
- `.specify\extensions\git\commands\speckit.git.validate.md`
- `.specify\extensions\git\config-template.yml`
- `.specify\extensions\git\extension.yml`
- `.specify\extensions\git\git-config.yml`
- `.specify\extensions\git\README.md`
- `.specify\extensions\git\scripts\bash\auto-commit.sh`
- `.specify\extensions\git\scripts\bash\create-new-feature.sh`
- `.specify\extensions\git\scripts\bash\git-common.sh`
- `.specify\extensions\git\scripts\bash\initialize-repo.sh`
- `.specify\extensions\git\scripts\powershell\auto-commit.ps1`
- `.specify\extensions\git\scripts\powershell\create-new-feature.ps1`
- `.specify\extensions\git\scripts\powershell\git-common.ps1`
- `.specify\extensions\git\scripts\powershell\initialize-repo.ps1`


# Living-spec judgement

The living-spec machinery is a good fit for skill packages.
The source corpus changes when the upstream converter re-converts a PDF.
Each generated package stores a source path and a source hash in `.spec-context.json`.
A drift command can compare the stored hash with the current file hash.
It can then mark the package for regeneration.

Evidence: `.specify/extensions.yml` registers companion hooks after each core step.
This checkout does not contain `.specify/extensions/companion/`.
The harness records that gap and writes the Companion-compatible context directly.

# Specification Analysis Report

Status: PASS

| ID | Category | Severity | Location | Summary | Recommendation |
| - | - | - | - | - | - |
| None | None | None | None | No issues found. | No action required. |

## Metrics

- Total Requirements: 5
- Total Tasks: 6
- Critical Issues Count: 0
