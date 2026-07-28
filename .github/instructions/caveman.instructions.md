---
description: "Use when: any conversational output in this repo. Caveman compression — drop fluff, keep substance. Source: https://github.com/JuliusBrussee/caveman"
applyTo: "**"
---

# Caveman Mode (Repo)

Respond terse. Keep all the technical substance. Remove only the fluff.

## Precedence: STE outranks caveman

Simplified Technical English (STE) outranks caveman compression. If the two rule
sets conflict, obey STE. STE is NON-NEGOTIABLE. Caveman is a preference.

- STE controls all documentation, code comments, commit messages, pull request
  text, error messages, printed output, and agent chat output.
- Caveman applies only after STE. Caveman removes filler, pleasantries, and
  hedging. Caveman must not break an STE rule.
- Resolve each known conflict as follows:
  - Keep the articles `a`, `an`, and `the` (STE Rule 4.5).
  - Write complete sentences. Do not write fragments (STE Rule 4.2).
  - Use one term for each concept, every time (STE Rule 1.11).
  - Use plain words. Do not use slang or jargon (STE Rule 1.10).
  - Use the active voice and simple tenses (STE Rules 3.2 and 3.6).
  - Do not use a semicolon (STE Rule 8.1).
- Caveman keeps the cut of filler, pleasantries, and hedging. Caveman loses the
  permission to drop articles, to write fragments, and to swap synonyms.

Full rules: `documentation/ASD-STE100_writing-guide.md`.

## Rules

Apply these rules only where they do not conflict with STE. See Precedence above.

- Drop the filler (just/really/basically), the pleasantries, and the hedging.
- Keep the articles and the complete sentences. STE Rules 4.5 and 4.2 require them.
- Keep the technical terms exact. Keep the code blocks unchanged.
- Use one term for each concept. Do not swap synonyms (STE Rule 1.11).
- Not: "Sure! I would be happy to help you with that."
- Yes: "The auth middleware has a bug. Change the token expiry check to `<=`."

## Levels

Default: `lite`. The `lite` level is the only level that obeys STE.

- **lite**: Drop the filler only. Keep the articles and the complete sentences.
- **full**, **ultra**, **wenyan**: These levels drop articles and permit
  fragments. They break STE Rules 4.2 and 4.5. Do not use them for agent output.

If a user asks for `full`, `ultra`, or `wenyan`, tell the user about the conflict.
Then use `lite`. Use a higher level only when the user states that STE is
suspended for the session.

Stop: "stop caveman" or "normal mode".

## Auto-Clarity (override caveman)

Drop caveman for:
- Security warnings.
- Irreversible / destructive actions (rm -rf, force-push, drop table, prod deploy).
- User confused -- clarify in full sentence.

Resume caveman after.

## Boundaries (NOT compressed)

- **Code**: written normal. Inline comments, docstrings, logging stay per project rules.
- **Commit messages**: Conventional Commits, full grammar.
- **PR descriptions**: full prose for reviewers.
- **Error messages / log output**: verbatim, no edit.
- **File paths, URLs, identifiers**: byte-preserved.

## Interaction with Repo Instructions

The order of precedence is:

1. `documentation/ASD-STE100_writing-guide.md` (STE). STE wins every conflict.
2. `.github/copilot-instructions.md` and `agents.md`. These files control the
   code artifacts, such as the inline comments, the action logging, and the
   5-Item Rule.
3. This file (caveman). Caveman compresses the chat prose only.

All NON-NEGOTIABLE conventions remain in full.
