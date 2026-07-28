---
name: ste-writing
description: >-
  Apply the Simplified Technical English rules of ASD-STE100 to the text this project ships.
  Use it for the documentation, the README prose, the Markdown files, and the docstrings.
  Use it for the inline code comments, the log messages, and the error messages.
  Use it for the commit messages, the pull request text, the issue text, and the chat replies.
  Use it when the STE linter reports a violation. Use it when a file scores below 80.
  Use it when a user asks for text that a junior engineer can read without help.
  The skill states the core rules and the repair for each linter rule identifier.
  It also states the precedence above caveman compression and the self-check command.
---

# STE writing

Simplified Technical English (STE) is a controlled subset of English. STE makes
technical text clear and unambiguous for every reader. This repository treats
STE as NON-NEGOTIABLE.

This skill holds the rules you need for most text. The full rule set is in
[the STE writing guide](../../../documentation/ASD-STE100_writing-guide.md) at
`documentation/ASD-STE100_writing-guide.md`. Read that guide when you need a
rule that this skill does not state.

## Precedence

STE outranks every other style rule in this repository. If another rule set
conflicts with STE, obey STE.

The caveman compression rules are the known conflict. Caveman removes filler,
pleasantries, and hedging. Caveman must not drop an article, write a fragment,
swap a synonym, or use slang. The caveman `lite` level is the only level that
obeys STE.

## The eight defaults

Apply these defaults to every sentence you write.

1. Use one word for one meaning. Use one term for each concept, every time.
2. Use the active voice. Make the actor the subject of the sentence.
3. Use simple tenses. Do not use a perfect form or a progressive form.
4. Keep an instruction to 20 words. Keep a description to 25 words.
5. Write one instruction for each sentence. Start the sentence with the verb.
6. State the condition first, then the command. Write `If X, do Y`.
7. Keep the articles. Write complete sentences.
8. Use American spelling. Never change a quoted string or an identifier.

## Repair each linter violation

The linter reports a rule identifier for each violation. Apply the matching
repair.

| Rule identifier | Problem | Repair |
| - | - | - |
| STE-S1-WORD | The word is not in the approved dictionary. | Use the plain word that the linter suggests. If the word is a correct technical term, add it to `allowlist` under `[tool.ste_linter]` in `pyproject.toml`. |
| STE-S1-POS | The word is not used as its approved part of speech. | Do not use a noun as a verb. Write `Apply oil to the surface`, not `Oil the surface`. |
| STE-S2-NOUNCLUSTER | A multi-word noun stacks more than three words. | Break the stack with `of`, `on`, `in`, or `for`. Write `the handler that refreshes the token`, not `the token refresh handler`. |
| STE-S3-PASSIVE | The sentence uses the passive voice. | Name the actor and make the actor the subject. Write `The parser reads the file`, not `The file is read by the parser`. |
| STE-S3-TENSE | The sentence uses a complex tense. | Use a simple tense. Write `The parser read the file`, not `The parser has been reading the file`. |
| STE-S4-LEN | The sentence is too long. | Split the sentence into two sentences. |
| STE-S4-CONTRACTION | The text uses a contraction. | Write the full form. Use `do not`, `is not`, and `are not`. |
| STE-S6-PARA | The paragraph has more than six sentences. | Split the paragraph where the topic changes. |
| STE-S7-WARNING | A warning has no signal word or no stated consequence. | Start with `Warning` or with `Caution`. State the exact consequence. |
| STE-S8-SEMICOLON | The text uses a semicolon. | Write two sentences instead. |
| STE-S9-LATIN | The text uses a Latin abbreviation. | Write `for example`, `that is`, or `and so on`. |
| STE-S9-PHRASAL | The text uses a phrasal verb. | Use one precise verb. Write `start`, not `kick off`. |
| STE-S9-GENDER | The text uses a gendered word. | Use a neutral term such as `the operator` or `the engineer`. |

## Write a warning in three parts

A warning tells the reader about a risk. Build every warning from three parts.

1. Start with the signal word. Use `Warning` for harm, for data loss, or for an
   irreversible action. Use `Caution` for a recoverable action.
2. Give the command or the condition.
3. State the exact consequence.

Correct: `Warning: do not run this command on production. The command deletes
the users table, and no backup exists.`

Wrong: `Be careful with this command.`

## Check the text before you finish

Run the linter on every file you changed. The threshold is 80.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 <file>
```

These flags help:

- `--quiet` prints only the score line.
- `--format json` prints a machine-readable report.
- `--ignore STE-S3-PASSIVE` turns off one rule.
- `--select STE-S8-SEMICOLON` runs one rule alone.

The pre-commit hook grades every `*.md` file and every `*.py` file at the same
threshold. The `ste-lint` workflow grades the writing guide and the linter
README on each pull request.

## Scope

STE controls this text:

- The documentation, the README prose, and the specification prose.
- The inline code comments and the docstrings.
- The commit messages, the pull request text, and the issue text.
- The log messages, the error messages, and the printed output.
- The agent chat output.

STE never changes this text:

- A quoted string, an identifier, a file path, or a URL.
- A code block, a command, or a log line that you copy word for word.
- The name of a product or the name of a third party.
