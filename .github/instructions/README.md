# The instructions folder

Every file here carries `applyTo: "**"`. Copilot applies each one to every
request in this repository.

## The files

| File | Authority |
| - | - |
| `git-flow-multi-agent.instructions.md` | The branch model, the rules for parallel agents, and the rules that protect the GitHub Actions minute balance. |
| `coding-standards.instructions.md` | The autonomous workflow, the 5-Item Rule, the inline comments, the action logging, and the quality gates. |
| `copilot-token-efficiency.instructions.md` | The model choice, the context limits, and the prompt discipline. |
| `caveman.instructions.md` | The compression rules for chat prose. STE outranks this file. |

## Two files mirror a user-profile file

`coding-standards.instructions.md` and `copilot-token-efficiency.instructions.md`
also exist in the VS Code user profile:

```text
%APPDATA%\Code\User\prompts\
```

The profile copy serves every other workspace on the machine. The repository
copy serves the cloud agents and every other machine, because neither one can
read a local profile.

Caution: do not delete the profile copy. A delete strips the standards from
every other project on the machine. Do not delete the repository copy either. A
delete leaves the cloud agents with no standards at all.

If you change one copy, change the other in the same pull request. State the
mirror in the pull request body.

## The retired file

`git-workflow.instructions.md` no longer exists. The profile still holds a copy,
and that copy is stale. `git-flow-multi-agent.instructions.md` replaces it and
adds the Actions minute rules. If the two disagree, obey the file in this
folder.
