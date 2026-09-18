# Domain skill package contract

## Purpose

This contract defines one generated Juniper domain skill package. A validator
must reject a package that breaks any required rule in this file.

## Directory layout

A domain skill package MUST use this layout.

```text
juniper-<domain>\
  SKILL.md
  INDEX.md
  sources.md
  documents\
    <document-slug>\
      INDEX.md
      00-overview.md
      01-<topic-slug>.md
      NN-<topic-slug>.md
```

Rules:

1. The package directory name MUST equal the `name` field in `SKILL.md`.
2. The package directory name MUST match `^juniper-[a-z0-9]+(-[a-z0-9]+)*$`.
3. A document directory name MUST match `^[a-z0-9]+(-[a-z0-9]+)*$`.
4. A topic file name MUST match `^[0-9][0-9]-[a-z0-9]+(-[a-z0-9]+)*\.md$`.
5. `00-overview.md` MUST exist in each document directory.
6. A package MUST NOT contain Markdown files outside the paths above.

## File size limits

| File | Soft limit | Hard limit |
| - | -: | -: |
| `SKILL.md` | 8 KB | 12 KB |
| Level 1 `INDEX.md` | 20 KB | 40 KB |
| `sources.md` | 20 KB | 40 KB |
| Level 2 `INDEX.md` | 6 KB | 10 KB |
| Topic file | 12 KB | 20 KB |

A validator MUST warn when a file exceeds the soft limit. A validator MUST fail
when a file exceeds the hard limit.

## `SKILL.md` frontmatter

`SKILL.md` MUST start with YAML frontmatter. The frontmatter MUST contain these
fields.

| Field | Type | Required | Rule |
| - | - | - | - |
| `name` | string | yes | Matches the package directory name. |
| `description` | string | yes | One paragraph, 250 to 1,200 characters. |
| `license` | string | yes | States the copyright-safe restatement rule. |
| `metadata` | map | yes | Holds the fields in the next table. |

The `metadata` map MUST contain these fields.

| Field | Type | Required | Rule |
| - | - | - | - |
| `feature` | string | yes | Value is `2925-juniper-skill-factory`. |
| `domain` | string | yes | The part after `juniper-` in `name`. |
| `documents` | integer | yes | Count of document directories. |
| `topics` | integer | yes | Count of topic files under `documents`. |
| `source_pages` | integer | yes | Total source pages in this domain. |
| `built` | string | yes | ISO 8601 date or date-time. |

The body of `SKILL.md` MUST contain these sections in this order.

1. The domain title.
2. A short instruction that tells the agent to read the needed topic.
3. A route table that maps question subjects to level 1 index rows.
4. The class mark table.
5. Answer rules.
6. Copyright rule.
7. Precedence statement.
8. Scope statement.

## Level 1 `INDEX.md` format

The level 1 `INDEX.md` MUST start with the heading `# <domain title> index`.
It MUST contain these sections in this order.

1. `## Route by subject`
2. `## Route by source document`
3. `## Life cycle coverage`
4. `## Coverage gaps`

The `Route by subject` table MUST use these columns.

| Column | Type | Rule |
| - | - | - |
| `Ask about` | string | Words an agent can see in a question. |
| `Read` | path | Relative path to a level 2 `INDEX.md` or a topic file. |
| `Life cycle` | array string | One or more life cycle tags. |

The `Route by source document` table MUST use these columns.

| Column | Type | Rule |
| - | - | - |
| `Document` | string | Human-readable source title. |
| `Slug` | string | Document directory name. |
| `Pages` | integer | Source page count. |
| `Read` | path | Relative path to the document `INDEX.md`. |

The `Life cycle coverage` table MUST use these columns.

| Column | Type | Rule |
| - | - | - |
| `Stage` | enum | `day0`, `day1`, `day2`, or `day2plus`. |
| `Topics` | integer | Count of topics with this tag. |
| `Status` | enum | `covered` or `gap`. |

The `Coverage gaps` section MUST state `No gaps found.` when all four stages
are covered. It MUST list each missing stage when a gap exists.

## Level 2 `INDEX.md` format

Each document directory MUST contain one level 2 `INDEX.md`. It MUST start with
`# <document title> index`. It MUST contain these sections in this order.

1. `## Source`
2. `## Topic route`
3. `## Life cycle map`
4. `## Citation keys`

The `Source` section MUST state the source document title, category, page count,
source file path, and source PDF path. The section MUST state when the source is
one part of a split part set.

The `Topic route` table MUST use these columns.

| Column | Type | Rule |
| - | - | - |
| `Ask about` | string | Question words that route to this topic. |
| `Topic` | string | Topic title. |
| `Read` | path | Relative path to the topic file. |
| `Life cycle` | array string | One or more life cycle tags. |

The `Life cycle map` table MUST use the same columns as the level 1 life cycle
table. Counts apply only to this document.

The `Citation keys` table MUST use these columns.

| Column | Type | Rule |
| - | - | - |
| `Key` | string | Citation key used by cards in this document. |
| `Source range` | string | Page range or section range. |
| `Topic` | path | Topic file that uses the key. |

## Topic file frontmatter

Each topic file MUST start with YAML frontmatter. The frontmatter MUST contain
these fields.

| Field | Type | Required | Rule |
| - | - | - | - |
| `topic` | string | yes | Short topic title. |
| `domain` | string | yes | Domain part without `juniper-`. |
| `document` | string | yes | Document slug. |
| `lifecycle` | array string | yes | One or more life cycle tags. |
| `sources` | array string | yes | One or more citation keys. |

The `lifecycle` values MUST come from `day0`, `day1`, `day2`, and `day2plus`.
The `sources` values MUST match the citation-key format below.

## Topic card format

The topic body MUST contain only headings, short lead text, and card lists. Each
card MUST be one Markdown list item.

A card MUST use this grammar.

```text
- <CLASS>: <restated fact>. [<CITATION-KEY>]
```

`<CLASS>` MUST be one of these values.

| Mark | Meaning |
| - | - |
| `MUST` | The source states a hard limit or a required practice. |
| `SHOULD` | The source recommends the practice and permits a judged exception. |
| `INFO` | The card states a fact that sets no limit. |

Rules:

1. A card MUST contain one fact.
2. A card MUST end with one or more citation keys in square brackets.
3. A card MUST NOT copy source prose unless the text is in an allowed verbatim
   class.
4. A card with a command or configuration block MUST still include a restated
   lead sentence and a citation key.
5. A card MUST use Simplified Technical English except for identifiers and other
   allowed verbatim classes.

## Citation-key format

A citation key MUST use one of these forms.

```text
[<DOCKEY> p.<page>]
[<DOCKEY> p.<start>-<end>]
[<DOCKEY> sec.<section-slug>]
[<DOCKEY> table.<table-slug>]
[<DOCKEY> fig.<figure-slug>]
```

Rules:

1. `<DOCKEY>` MUST match `^[A-Z0-9]{3,12}$`.
2. A page range MUST have a start page less than or equal to the end page.
3. A section, table, or figure slug MUST match `^[a-z0-9]+(-[a-z0-9]+)*$`.
4. Each key in a topic MUST appear in the level 2 `Citation keys` table.
5. Each key in a domain MUST appear in `sources.md`.

## `sources.md` format

`sources.md` MUST start with the heading `# Sources`. It MUST contain one table
with these columns.

| Column | Type | Rule |
| - | - | - |
| `Key` | string | Stable document key. |
| `Title` | string | Source document title. |
| `Category` | string | Harvester category. |
| `Pages` | integer | Source page count. |
| `Markdown` | path | Relative path under the harvest root. |
| `PDF` | path | Relative path under the PDF root. |

Each source document MUST appear once in `sources.md`. A split part set MUST use
one key for the complete source document and list each part in the Markdown path
cell.

## Validator requirements

A validator MUST fail the package when it finds any of these defects.

1. A required file is missing.
2. A path does not match its pattern.
3. Required frontmatter is missing or has the wrong type.
4. A file exceeds its hard size limit.
5. A topic has no life cycle tag.
6. A card lacks a class mark.
7. A card lacks a citation key.
8. A citation key does not resolve to `sources.md`.
9. The similarity guard checks zero files.
10. The similarity guard finds more than 12 consecutive shared prose words.
