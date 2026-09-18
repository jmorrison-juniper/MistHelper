---
status: locked
issue: 2925
audience: the skill factory agents only
---

# Skill factory interface contract

This file locks the decisions that every component of the skill factory obeys.
An agent must not change a locked decision. If a decision blocks the work, the
agent records the conflict in issue #2925 and stops.

## 1. Why the factory does not make one skill for each document

The corpus holds 1,527 documents today, and it grows. An agent host loads the
`name` and the `description` of every installed skill into the context before
the first user word. One skill costs about 80 tokens of that budget. 1,527
skills cost about 122,000 tokens. That budget defeats the purpose of the
factory.

The factory therefore builds a small set of domain skills. Each domain skill
holds many documents. The target count is 12 through 25 domain skills.

## 2. The three-level hierarchy

```text
<domain-skill>/
  SKILL.md              Level 1. The router. An agent reads this file first.
  INDEX.md              Level 1. Every topic in the domain, one line each.
  sources.md            Level 1. One citation key for each source document.
  documents/
    <document-slug>/
      INDEX.md          Level 2. The chapter map and the life cycle map.
      00-overview.md    Level 3. One topic. The agent reads only what it needs.
      01-<topic>.md
      NN-<topic>.md
```

Level 1 answers "which document holds my subject". Level 2 answers "which
chapter holds my subject". Level 3 holds the knowledge. An agent reads at most
one file for each level, so a question costs three reads, not 33,072 pages.

## 3. Size limits

| File | Soft limit | Hard limit |
| - | -: | -: |
| `SKILL.md` | 8 KB | 12 KB |
| `INDEX.md` at level 1 | 20 KB | 40 KB |
| `INDEX.md` at level 2 | 6 KB | 10 KB |
| A topic file | 12 KB | 20 KB |

If a topic passes the hard limit, split it. A topic that an agent cannot read
in one step is a failed topic.

## 4. The `SKILL.md` frontmatter

```yaml
---
name: juniper-<domain>
description: >-
  One paragraph. It names every subject that routes to this skill. It uses the
  words that an agent sees in a user question. It states that the skill holds a
  document tree.
license: The topics restate Juniper Networks documentation. Juniper Networks
  holds the copyright of the source documents. This skill stores no source
  prose.
metadata:
  feature: 2925-juniper-skill-factory
  domain: <domain>
  documents: <count>
  topics: <count>
  source_pages: <count>
  built: <ISO 8601 date>
---
```

## 5. The life cycle tags

Every topic file carries one or more life cycle tags in its frontmatter. The
factory must cover all four for each domain. A domain that misses a stage
reports the gap in its level 1 `INDEX.md`.

| Tag | Stage | The topic answers |
| - | - | - |
| `day0` | Design and select | Which architecture and which hardware fits the requirement. |
| `day1` | Deploy and install | How to rack, cable, image, and configure the first time. |
| `day2` | Operate and maintain | How to monitor, verify, troubleshoot, and repair. |
| `day2plus` | Change and scale | How to upgrade, migrate, extend, and automate a change. |

## 6. The topic file shape

```yaml
---
topic: <short name>
domain: <domain>
document: <document-slug>
lifecycle: [day0, day2]
sources: [JUNOS-BEG p.66-71]
---
```

The body holds knowledge cards. One card is one list item. A card starts with a
class mark and ends with a citation key.

| Mark | Meaning |
| - | - |
| `MUST` | The source states a hard limit or a required practice. |
| `SHOULD` | The source recommends the practice and permits a judged exception. |
| `INFO` | The card states a fact that sets no limit. |

## 7. The copyright rule

Warning: never copy source prose into a topic file. Juniper Networks holds the
copyright of every source document. A copied paragraph makes the skill set
unpublishable.

The factory restates a fact in its own words. A fact is not copyrightable. The
expression of a fact is copyrightable. These items stay verbatim, because they
are not prose and an altered copy is a wrong answer:

- A command, a configuration line, and a command output sample.
- An identifier, a model number, a port name, and a numeric limit.
- A standard name and a protocol name.

The similarity guard measures the longest verbatim prose run. The threshold is
a maximum of 12 consecutive words shared with the source, outside the verbatim
classes above. The guard reports the measured count for every file it checked.
A guard that checks zero files fails.

## 8. Simplified Technical English

Every word of every generated file obeys `documentation/ASD-STE100_writing-guide.md`.
The `ste-writing` skill holds the short form. STE outranks every other style
rule. Never alter a quoted string or an identifier to satisfy STE.

## 9. The canonical store and the distribution paths

The canonical store is its own git repository at:

```text
C:\Users\jmorrison\juniper-agent-skills
```

That path sits outside OneDrive on purpose. OneDrive would sync hundreds of
megabytes on every build.

The installer publishes each domain skill by Windows directory junction. A
junction needs no administrator right.

| Target | Path |
| - | - |
| GitHub Copilot CLI and applications | `%USERPROFILE%\.copilot\skills\<name>` |
| Claude | `%USERPROFILE%\.claude\skills\<name>` |
| This repository for VS Code | `.github\skills\<name>` |

Caution: a junction inside the repository makes git read the store contents.
Add the junction name to `.gitignore` in the same step that creates it.

## 10. The source roots

The factory reads these roots. Each one grows while the factory runs.

| Root | Holds |
| - | - |
| `C:\Users\jmorrison\Downloads\juniper-harvest-md` | The current converted corpus and the manifests. |
| `C:\Users\jmorrison\Downloads\juniper-doc-archives\markdown` | An earlier conversion pass. |
| `C:\Users\jmorrison\Downloads\juniper-doc-archives\markdown2` | A second earlier conversion pass. |
| `<repo>\data\juniper_corpus` | The source PDFs that the converter reads. |

## 11. The known converter defects

The segmenter must repair these two defects. Both are measured, not assumed.

1. Inline code styling moved a styled word to the next line. The prose reads
   "lines that have in them", and the word `ge` sits alone on the next line.
2. Cover art produced single-word lines, and the heading detector read 25
   marketing lines as `##` headings. The real structure of
   `guides/junos-beginners-guide.md` starts at line 1059.

## 12. The split part sets

The converter splits a large PDF into several Markdown files with no common
rule. The inventory must group the parts of one document before the segmenter
reads them. Two files that share a `source_file` front matter value belong to
one document. A `-2` or a `-<hash>` suffix in the file name signals a part.

## 13. The shared state

The factory keeps its work queue in SQLite at:

```text
<repo>\data\juniper_skills\factory.db
```

No component holds state only in memory. A crash must lose no more than one
document of progress.

## 14. File ownership during the parallel build

Each agent writes only inside its own path. An agent that needs a change
outside its path records the request in issue #2925.

| Agent | Owns |
| - | - |
| `skill-contract` | `specs/2925-juniper-skill-factory/**` |
| `universal-install` | `src/juniper_skills/install/**`, `scripts/juniper_skills/**` |
| `corpus-inventory` | `src/juniper_skills/inventory/**` |
| `github-tracking` | `src/juniper_skills/tracking/**` |
| `speckit-harness` | `src/juniper_skills/speckit/**` |
| `segmenter` | `src/juniper_skills/segment/**` |
| `rewriter` | `src/juniper_skills/rewrite/**` |
| `orchestrator` | `src/juniper_skills/orchestrate/**` |
| `watcher` | `src/juniper_skills/watch/**` |

Every agent may add its own tests under `tests/unit/juniper_skills/<area>/`.
