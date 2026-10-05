### Adopt the two-file agent instructions

- **Added**: `AGENTS.md` at the repository root holds the generic agent rules. It is a byte-for-byte
  copy of `templates/agent-instructions/AGENTS.md` in `misthelper-devtools` at commit `d00c9af1`
  (jmorrison-juniper/misthelper-devtools#49). The `ste-lint.yml` workflow now grades `AGENTS.md`,
  `.github/copilot-instructions.md`, `CLAUDE.md`, and `README.md` with `.ste-linter.toml` on each
  pull request.
- **Changed**: `.github/copilot-instructions.md` holds the rules that apply to MistHelper only, and
  `CLAUDE.md` is a pointer to the two instruction files. Spec Kit writes its generated technology
  context to `.specify/memory/agent-context.md`, so it cannot overwrite the instruction files.
- **Removed**: `agents.md` and the `.github/instructions/` folder. Each rule from those files now
  lives in `AGENTS.md` or in `.github/copilot-instructions.md`, and the guardrail tests read the
  new files.
