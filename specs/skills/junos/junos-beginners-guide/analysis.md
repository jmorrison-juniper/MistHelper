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
| `speckit.companion.after-implement` | yes | active feature tasks.md and lifecycle hook state | .spec-context.json lifecycle history and status |
| `speckit.companion.after-plan` | yes | active feature directory and lifecycle hook state | .spec-context.json lifecycle history and status |
| `speckit.companion.after-specify` | yes | active feature directory and lifecycle hook state | .spec-context.json lifecycle history and status |
| `speckit.companion.after-tasks` | yes | active feature directory and lifecycle hook state | .spec-context.json lifecycle history and status |
| `speckit.companion.auto` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.classify` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.implement` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.living-adopt` | yes | living-specs registry, capability specs, git history, and changed files | capability spec files and living-specs registry updates |
| `speckit.companion.living-coverage` | yes | living-specs registry, capability specs, git history, and changed files | read-only requirement coverage report |
| `speckit.companion.living-drift` | yes | living-specs registry, capability specs, git history, and changed files | read-only drift report |
| `speckit.companion.living-move` | yes | living-specs registry, capability specs, git history, and changed files | capability spec files and living-specs registry updates |
| `speckit.companion.living-sync` | yes | living-specs registry, capability specs, git history, and changed files | reviewable living spec edits and synced context names |
| `speckit.companion.mark-complete` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.plan` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.resume` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.specify` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.status` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
| `speckit.companion.tasks` | yes | active feature artifacts, .spec-context.json, and companion config | .spec-context.json progress or pipeline output |
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
- `.specify\extensions\companion\commands\speckit.companion.after-implement.md`
- `.specify\extensions\companion\commands\speckit.companion.after-plan.md`
- `.specify\extensions\companion\commands\speckit.companion.after-specify.md`
- `.specify\extensions\companion\commands\speckit.companion.after-tasks.md`
- `.specify\extensions\companion\commands\speckit.companion.auto.md`
- `.specify\extensions\companion\commands\speckit.companion.classify.md`
- `.specify\extensions\companion\commands\speckit.companion.implement.md`
- `.specify\extensions\companion\commands\speckit.companion.living-adopt.md`
- `.specify\extensions\companion\commands\speckit.companion.living-coverage.md`
- `.specify\extensions\companion\commands\speckit.companion.living-drift.md`
- `.specify\extensions\companion\commands\speckit.companion.living-move.md`
- `.specify\extensions\companion\commands\speckit.companion.living-sync.md`
- `.specify\extensions\companion\commands\speckit.companion.mark-complete.md`
- `.specify\extensions\companion\commands\speckit.companion.plan.md`
- `.specify\extensions\companion\commands\speckit.companion.resume.md`
- `.specify\extensions\companion\commands\speckit.companion.specify.md`
- `.specify\extensions\companion\commands\speckit.companion.status.md`
- `.specify\extensions\companion\commands\speckit.companion.tasks.md`
- `.specify\extensions\companion\extension.yml`
- `.specify\extensions\companion\LICENSE`
- `.specify\extensions\companion\scripts\capture.py`
- `.specify\extensions\companion\scripts\check-coverage.py`
- `.specify\extensions\companion\scripts\companion_config.py`
- `.specify\extensions\companion\scripts\derive-from-files.py`
- `.specify\extensions\companion\scripts\drift.py`
- `.specify\extensions\companion\scripts\living_spec_fold.py`
- `.specify\extensions\companion\scripts\record-living-specs.py`
- `.specify\extensions\companion\scripts\register-capability.py`
- `.specify\extensions\companion\scripts\relocate-capability.py`
- `.specify\extensions\companion\scripts\resolve-spec-paths.py`
- `.specify\extensions\companion\scripts\spec_context.py`
- `.specify\extensions\companion\scripts\spec_deltas.py`
- `.specify\extensions\companion\scripts\status-context.py`
- `.specify\extensions\companion\scripts\task_sync.py`
- `.specify\extensions\companion\scripts\write-context.py`
- `.specify\extensions\companion\workflows\speckit-companion.workflow.yml`
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
The real companion extension contains lifecycle writers, drift checks, coverage checks, and living-spec fold-back.
The harness invokes `write-context.py` when the extension exists.
Living-spec commands fit the tracking model, but the current resolver reads repository-relative paths.
The Juniper source roots are outside this repository.
The factory must bridge that gap with source hashes or a registry that names those roots.

# Specification Analysis Report

Status: PASS

| ID | Category | Severity | Location | Summary | Recommendation |
| - | - | - | - | - | - |
| None | None | None | None | No issues found. | No action required. |

## Metrics

- Total Requirements: 5
- Total Tasks: 6
- Critical Issues Count: 0
