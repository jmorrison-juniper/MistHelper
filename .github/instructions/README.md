# The instructions folder

Every file here carries `applyTo: "**"`. Copilot applies each one to every
request in this repository.

## Which file belongs here

Apply one test: can a cloud agent act on the file?

A cloud agent runs on a GitHub runner. It reads this repository. It cannot read
a local VS Code profile, a local shell, or a local tool.

| Answer | Location | Reason |
| - | - | - |
| Yes | This folder | The cloud agent and every machine read it. |
| No | The VS Code user profile | The rule controls the local editor only. A copy here costs tokens on every request and changes nothing. |

## The files here

| File | Authority |
| - | - |
| `git-flow-multi-agent.instructions.md` | The branch model, the rules for parallel agents, and the rules that protect the GitHub Actions minute balance. |
| `coding-standards.instructions.md` | The autonomous workflow, the 5-Item Rule, the inline comments, the action logging, and the quality gates. |
| `caveman.instructions.md` | The compression rules for chat prose. STE outranks this file. |

## The files that stay in the user profile

These files live only in `%APPDATA%\Code\User\prompts\`. Do not copy one into a
repository.

| File | Reason |
| - | - |
| `copilot-token-efficiency.instructions.md` | The model choice, the MCP servers, and the chat session. A cloud agent makes none of these choices. |
| `rtk.instructions.md` | A local command line proxy. |
| `vscode-tool-use.instructions.md` | The local editor tools. |
| `git-workflow.instructions.md` | Retired. `git-flow-multi-agent.instructions.md` replaces it. |

## One file mirrors a user-profile file

`coding-standards.instructions.md` also exists in the user profile. The profile
copy serves the 11 other repositories on this machine that hold no instructions
folder. The repository copy serves the cloud agents and every other machine.

Caution: do not delete either copy. A delete of the profile copy strips the
standards from every other project. A delete of the repository copy leaves the
cloud agents with no standards.

If you change one copy, change the other in the same pull request. State the
mirror in the pull request body.

The mirror costs about 2,900 tokens on each local request. To remove that cost,
add the file to the other repositories first, then delete the profile copy.
