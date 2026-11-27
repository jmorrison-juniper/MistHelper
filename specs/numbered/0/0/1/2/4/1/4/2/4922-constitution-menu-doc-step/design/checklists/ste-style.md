# Writing Style Checklist: Menu step names the generated pages

**Purpose**: Check the changed prose against the Simplified Technical English rules in `AGENTS.md`.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Sentence Rules

- [x] Each instruction in the changed text holds 20 words or fewer. The step 5 sentences hold 12, 6, and 11 words.
- [x] Each description in the changed text holds 25 words or fewer. The README bullet sentences hold 17, 9, and 5 words. The Sync Impact Report rationale holds 20 words.
- [x] Each instruction uses the imperative form, with the condition first when a condition applies. The rule file step has one instruction and one negative instruction of 8 words.
- [x] The changed text uses the active voice and a simple tense.
- [x] The changed text holds no semicolon.
- [x] The changed text holds no contraction.
- [x] The changed text holds no Latin abbreviation of the kinds that `AGENTS.md` forbids.
- [x] The changed text uses American spelling.
- [x] Each safety statement in the plan starts with `Warning:` or `Caution:`. The rollback section holds one of each.

## Terms

- [x] One term names one concept. "Generated menu pages" names the two generated pages in step 5 and in the fragment.
- [x] One term names the README role. "Start guide" appears in the README bullet.
- [ ] Not measured in this stage: the `ste-linter` score of each changed file. The gate runs in T-LOCAL-GATES, which records the score. This stage runs no gate.
