---
status: draft
issue: 2925
audience: skill factory agents only
---

# Juniper documentation skill factory specification

## Problem

The Juniper document corpus is too large for a single skill. It is also too
large for one skill per source document. The current catalog contains 1,778
converted documents and 243,314 pages. The largest document contains 33,072
pages.

An agent host loads every installed skill name and description before a user
asks a question. A one-document skill set would spend the context budget before
the agent reads the question. The skill factory must convert the corpus into a
small set of domain skills.

## Goals

1. Build 12 to 25 domain skills from the Juniper corpus.
2. Give each domain skill a three-level document tree.
3. Make each skill answerable by agents, not by human readers.
4. Restate source facts in Simplified Technical English.
5. Cite each knowledge card with a stable citation key.
6. Store factory state in SQLite at `data\juniper_skills\factory.db`.
7. Make a crash lose no more than one source document of progress.

## Non-goals

1. Do not publish one skill for each source document.
2. Do not copy Juniper prose into topic files.
3. Do not build a search engine for a human reader.
4. Do not answer questions without a citation.
5. Do not change source documents in the harvest roots.
6. Do not implement Python code in this specification set.

## Users

The only user is an AI agent. A human can inspect the output, but the output is
not written for direct human navigation. The agent reads a skill description,
then reads one level 1 index, one level 2 index, and one topic file.

## User stories

### Story 1: Route a question to one domain

As an AI agent, I need a skill description that names the subjects in the
domain. I can then select one Juniper skill before I read the document tree.

Acceptance criteria:

- Each skill has a `name` that starts with `juniper-`.
- Each skill has a description that contains routing words from user questions.
- Each source document maps to exactly one domain.
- A fallback domain receives documents that match no earlier rule.

### Story 2: Find the correct topic with three reads

As an AI agent, I need a bounded hierarchy. I can then answer a question without
reading a large document.

Acceptance criteria:

- `SKILL.md` routes the agent to the correct level 1 row.
- The level 1 `INDEX.md` routes the agent to one document.
- The level 2 `INDEX.md` routes the agent to one topic file.
- The topic file stays at or below the hard size limit.

### Story 3: Answer with cited cards

As an AI agent, I need small knowledge cards with class marks. I can then state
whether a rule is required, recommended, or informational.

Acceptance criteria:

- Each card starts with `MUST`, `SHOULD`, or `INFO`.
- Each card ends with a citation key.
- The answer includes a citation for each rule.
- The answer states when the skill does not hold the fact.

### Story 4: Preserve copyright safety

As an AI agent, I need copyright-safe topics. I can then publish answers without
copying protected Juniper expression.

Acceptance criteria:

- Topic prose restates source facts.
- Commands, configuration, identifiers, numeric limits, and standard names can
  stay verbatim.
- The similarity guard reports the longest common prose run for each file.
- A guard that checks zero files fails.

### Story 5: Report life cycle coverage

As an AI agent, I need each topic tagged with a life cycle stage. I can then find
design, deploy, operate, and change guidance for each domain.

Acceptance criteria:

- Each topic has one or more of `day0`, `day1`, `day2`, and `day2plus`.
- Each domain index reports the count of topics in each stage.
- Each domain index reports any missing stage as a coverage gap.
- A gap does not stop the build.

## Functional requirements

1. The factory must read the locked interface contract before it writes output.
2. The factory must group split source parts into one document before it segments.
3. The factory must assign each document to exactly one domain.
4. The factory must use deterministic domain rules.
5. The factory must persist each `SourceDocument`, `PartSet`, `DomainSkill`,
   `Document`, `Topic`, `Card`, `Citation`, and `WorkItem`.
6. The factory must write each domain skill to the canonical store before it
   creates any distribution junction.
7. The factory must write no generated skill content outside the allowed skill
   paths.
8. The factory must reject a topic file that exceeds its hard size limit.
9. The factory must reject a `SKILL.md` file that lacks required frontmatter.
10. The factory must reject a card without a class mark or a citation key.
11. The factory must report the count of checked files in each guard.
12. The factory must fail any required guard that checks zero files.

## Acceptance criteria for the factory

1. The factory creates 12 to 25 domain skills.
2. The factory creates no one-document skill.
3. The factory maps all 1,778 catalog rows to exactly one domain.
4. The factory writes each generated skill with the package schema in
   `contracts\skill-package.md`.
5. The factory writes each topic with one or more life cycle tags.
6. The factory writes each card with a class mark and a citation key.
7. The factory writes each source document to `sources.md` one time per domain.
8. The factory records all work in `data\juniper_skills\factory.db`.
9. The factory can resume after a crash without reworking completed documents.
10. The factory produces a coverage gap report for each domain.
11. The similarity guard reports no prose run longer than 12 words.
12. The STE check scores each generated Markdown file at or above 80.

## Blockers and conflicts

No conflict exists with the locked interface contract.
