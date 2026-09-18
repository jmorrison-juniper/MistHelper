# Skill package review checklist

Use this checklist for one finished Juniper domain skill package. The reviewer is
an AI agent. The agent MUST mark each item as pass, fail, or not applicable.

## Package identity

- [ ] The package directory name starts with `juniper-`.
- [ ] The package directory name matches the `name` field in `SKILL.md`.
- [ ] `SKILL.md` contains all required frontmatter fields.
- [ ] The `metadata.feature` value is `2925-juniper-skill-factory`.
- [ ] The package contains no Markdown file outside the required layout.

## Routing behavior

- [ ] The `description` names the domain subjects with question words.
- [ ] `SKILL.md` tells the agent to read the needed topic before it answers.
- [ ] The level 1 `INDEX.md` has a `Route by subject` table.
- [ ] The level 1 `INDEX.md` has a `Route by source document` table.
- [ ] Each document directory has a level 2 `INDEX.md`.
- [ ] Each level 2 `INDEX.md` routes each subject to a topic file.
- [ ] The package can answer a route request with no more than three file reads.

## Source coverage

- [ ] Every source document assigned to the domain appears in `sources.md`.
- [ ] Each source appears one time in `sources.md`.
- [ ] Each split part set uses one source key for the complete source document.
- [ ] Each topic citation resolves to `sources.md`.
- [ ] The package states when a source document has no usable topic.

## Topic quality

- [ ] Each topic file has required frontmatter.
- [ ] Each topic has one or more life cycle tags.
- [ ] Each topic file stays at or below the hard size limit.
- [ ] Each card starts with `MUST`, `SHOULD`, or `INFO`.
- [ ] Each card states one fact.
- [ ] Each card ends with one or more citation keys.
- [ ] Each command or configuration block has a restated lead sentence.
- [ ] Each warning starts with `Warning:` and states the harm.
- [ ] Each caution starts with `Caution:` and states the recoverable consequence.

## Life cycle coverage

- [ ] The level 1 `INDEX.md` reports topic counts for all four life cycle tags.
- [ ] The level 1 `INDEX.md` states `No life cycle coverage gaps were found.`
      when all stages have coverage.
- [ ] The level 1 `INDEX.md` lists each missing stage when a gap exists.
- [ ] The domain report states the count of topics checked.
- [ ] A zero-topic coverage report fails.

## Copyright safety

- [ ] Generated prose restates the source facts in new words.
- [ ] Verbatim text appears only in an allowed verbatim class.
- [ ] The similarity guard checked every generated Markdown file.
- [ ] The similarity guard reports `files_checked` greater than zero.
- [ ] The similarity guard reports `source_documents_checked` greater than zero.
- [ ] No generated file has more than 12 consecutive shared prose words.
- [ ] Each failed similarity row includes generated and source line evidence.

## Simplified Technical English

- [ ] The generated Markdown uses one term for each concept.
- [ ] Instructions use active voice and simple tenses.
- [ ] Instruction sentences stay at or below 20 words where practical.
- [ ] Description sentences stay at or below 25 words where practical.
- [ ] The text uses no semicolon.
- [ ] The text uses no Latin abbreviation.
- [ ] The text uses American spelling.
- [ ] The STE score is 80 or higher for each generated Markdown file.

## Persistence and resume evidence

- [ ] The factory recorded each `SourceDocument` in the SQLite database.
- [ ] The factory recorded each `DomainSkill` in the SQLite database.
- [ ] The factory recorded each `Document` in the SQLite database.
- [ ] The factory recorded each `Topic` in the SQLite database.
- [ ] The factory recorded each `Card` in the SQLite database.
- [ ] The factory recorded each `Citation` in the SQLite database.
- [ ] The factory recorded each `WorkItem` in the SQLite database.
- [ ] A crash after one document can resume without redoing completed documents.

## Final decision

The package passes only when all required checks pass. If a check fails, write
the failed item, the file path, the line number when known, and the repair needed.

Warning: do not approve a package when a required guard checks zero files. A
zero-file guard hides a failed build and can publish an empty skill.
