### Removed

- The 16 agent skills under `.github/skills/` left the repository. They now live
  at the user level in `~/.copilot/skills/`, where one copy serves every
  repository on the workstation. The `ste-lint` workflow, the container policy
  guardrail, the git-flow instruction, and `.gitignore` no longer point at the
  folder. Issue #3401 records the move.
