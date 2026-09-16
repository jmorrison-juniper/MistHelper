# Feature Specification: Hardening Junos Skill

**Feature Branch**: `docs/2754-hardening-junos-skill`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Create a feature specification for a new project skill named `hardening-junos` in the MistHelper repository. A Juniper documentation corpus of 26.1 GB is staged outside the git repository. The specification must decide the corpus scope, the storage split, the retrieval design, the conversion quality criteria, and the deduplication rule."

## Summary

This feature adds one project skill named `hardening-junos` to `.github/skills/`.
The skill helps a junior NOC engineer to harden a Junos device.
It gives an answer, the Junos command, and the source document for that answer.

A Juniper documentation corpus is staged on disk outside the git repository.
The corpus is too large to live inside the repository.
The skill therefore holds curated guidance and an index.
The bulk text stays on disk.

### Decision summary

| Question | Decision | Short reason |
| - | - | - |
| Corpus scope | Index the 757 security relevant unique documents. Keep the full set of 4,007 unique documents as a second search area. | The security subset covers the skill domain. The remainder answers an adjacent question. |
| Storage split | The repository receives the skill files only, and the total is 400 KB or less. The converted Markdown stays outside the repository. | The largest existing skill is 140 KB. The converted text is 744 MB. The repository is OneDrive synced. The text is also copyrighted. |
| Retrieval | A router file, a curated reference set, one index file, and a written search procedure. This mirrors `managing-mist-api`. | An agent reads a small router first. It opens only the reference that the task needs. |
| Conversion quality | Ten acceptance rules, a per-page character yield floor, and a manual audit of 30 documents. | The converter has a known weakness on cover pages. |
| Deduplication | The newest readable train wins. The index records the train. A changed document records the train that it supersedes. | A document repeats across trains 21.1 to 26.2. The newest copy is not always readable. |

### Corpus facts

A person measured these values on 2026-09-16.

| Item | Value |
| - | - |
| Staged corpus size | 26.1 GB |
| Extracted files | 30,751 |
| PDF files | 9,337 |
| PDF pages | About 2,650,000 |
| Unique document names | 4,007 |
| Duplicate copies across trains | 5,330, which is 57 percent |
| Converted Markdown files | 4,004 converted, 3 skipped |
| Converted Markdown size | 744 MB |
| Security relevant documents | 757 |
| Security relevant Markdown size | 181 MB |
| DISA STIG rule sets | 3, which are L2S V2R5, NDM V2R5, and RTR V2R1 |
| DISA STIG rules | 181, which are 24 plus 55 plus 102 |
| Largest existing skill | `managing-mist-api`, at 140 KB in 6 files |

DISA is the Defense Information Systems Agency.
STIG is a Security Technical Implementation Guide.
A train is a Junos release family, such as 26.2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a hardening answer with its source (Priority: P1)

A junior NOC engineer must harden the management plane of an EX switch.
The engineer asks the skill how to protect the management interface.
The skill gives the control, the Junos configuration, the reason, and the source document.
The engineer can open the source document to confirm the answer.

**Why this priority**: This is the primary value of the skill.
Without it, the engineer must read about 2,650,000 pages.
This story alone is a usable product.

**Independent Test**: Ask the skill five hardening questions that cover five different
checklist sections. Confirm that each answer gives a control, a Junos command, and a source
citation. Confirm that each citation points to a real document.

**Acceptance Scenarios**:

1. **Given** the skill is installed, **When** the engineer asks how to secure the management
   plane, **Then** the skill gives the control, the Junos configuration, the reason, and the
   source document with its train.
2. **Given** an answer cites a source, **When** the engineer opens the cited path, **Then**
   the document exists and holds the cited material.
3. **Given** a question has no source in the skill or the corpus, **When** the engineer asks
   it, **Then** the skill states that it has no source and gives no invented answer.
4. **Given** the engineer asks for a Junos command, **When** the skill answers, **Then** the
   skill states the platform and the Junos train that the command applies to.

---

### User Story 2 - Check a configuration against the baseline (Priority: P2)

A junior NOC engineer holds a Junos configuration file.
The engineer asks the skill to compare the configuration against the hardening baseline.
The skill reports each item that passes, each item that fails, and each item that it cannot
judge. The skill maps each failed item to the matching DISA STIG rule.

**Why this priority**: This story turns the reference material into a repeatable review.
It needs the guidance from Story 1, so it comes second.

**Independent Test**: Give the skill the medium security sample configuration from Appendix B
of the hardening book. Confirm that the skill reports a result for all 67 checklist items.
Confirm that no item is silently absent.

**Acceptance Scenarios**:

1. **Given** a Junos configuration file, **When** the engineer asks for a baseline review,
   **Then** the skill reports pass, fail, or not-assessable for each of the 67 checklist items.
2. **Given** a failed item, **When** the skill reports it, **Then** the skill gives the
   matching DISA STIG rule identifier and its severity, if a match exists.
3. **Given** an item that the configuration file cannot show, **When** the skill reports it,
   **Then** the skill marks the item not-assessable and states the evidence that it needs.
4. **Given** a review result, **When** the engineer reads it, **Then** the skill states that
   the review is advice and that it changed no device.

---

### User Story 3 - Find a source document in the staged corpus (Priority: P3)

A junior NOC engineer needs the full Juniper document behind a control.
The engineer asks the skill where to find it.
The skill gives the document title, the train, and the path below the corpus root.
The skill states when the corpus is not present on the machine.

**Why this priority**: The curated guidance answers most questions.
Deep research needs the corpus. This story supports the harder questions.

**Independent Test**: Ask the skill for the source of ten controls. Confirm that each path
points to a file below the corpus root. Then remove the corpus root. Confirm that the skill
reports the corpus as absent and still answers from its curated references.

**Acceptance Scenarios**:

1. **Given** the corpus is present, **When** the engineer asks for a source document, **Then**
   the skill gives the title, the train, the page count, and the relative path.
2. **Given** the corpus is absent, **When** the engineer asks for a source document, **Then**
   the skill states that the corpus is absent, gives the document title and train, and
   continues to answer from its curated references.
3. **Given** a topic outside the security subset, **When** the engineer asks for a source,
   **Then** the skill searches the full unique document set and states that the result comes
   from outside the security subset.
4. **Given** a document that is available only from an older train, **When** the skill cites
   it, **Then** the skill states the train and the reason for the older train.

---

### User Story 4 - Refresh the corpus and record the change (Priority: P4)

An engineer adds a new Junos train to the staged corpus.
The engineer asks the skill how to refresh the index.
The skill states the refresh procedure, the deduplication rule, and the acceptance rules.
The engineer records each new gap in the gap register.

**Why this priority**: The corpus becomes old. This story keeps the skill true over time.
The skill works without it for at least one release cycle.

**Independent Test**: Add one train to the corpus. Follow the written refresh procedure.
Confirm that the index records the new train. Confirm that the gap register is still correct.

**Acceptance Scenarios**:

1. **Given** a new train is staged, **When** the engineer follows the refresh procedure,
   **Then** the index records the new train for each document that the train supersedes.
2. **Given** a document is unreadable in the newest train, **When** the engineer refreshes the
   index, **Then** the index keeps the newest readable train and the gap register records the
   failure.
3. **Given** a refresh is complete, **When** the engineer measures the repository, **Then**
   the repository growth is 400 KB or less.

---

### Edge Cases

- **The corpus root is absent.** The skill must state that the corpus is absent. The skill
  must continue to answer from its curated references. The skill must not stop with an error.
- **A document exists only in an older train.** The skill must cite the train. The skill must
  state why it used an older train.
- **A PDF is unrepairable.** Six PDF files are unrepairable. The skill must read the gap
  register, state the gap, and cite the readable fallback train.
- **Two trains disagree.** The skill must give the newest readable statement first. The skill
  must state that an older train differs. The skill must give both trains.
- **The converter makes spurious headings.** A cover page can make a run of false headings.
  The acceptance rules must find this condition before the index accepts the file.
- **A question falls outside the security subset.** The skill must search the full unique
  document set. The skill must state that the answer comes from outside the security subset.
- **A user asks the skill to change a live device.** The skill must refuse without explicit
  approval. The skill gives configuration text. A human applies it.
- **A user asks the skill to commit the corpus.** The skill must refuse. The repository must
  not receive the bulk Markdown or the PDF files.
- **The corpus root holds a partial conversion.** The skill must compare the index against the
  conversion manifest. The skill must report the count of the missing files.
- **A DISA STIG rule has no Juniper source.** The skill must give the STIG rule alone. The
  skill must state that it found no matching Juniper document.
- **A cited control can remove access to the device.** The skill must give the recovery step
  before the engineer applies the control.

## Requirements *(mandatory)*

### Functional Requirements

#### Skill structure and size

- **FR-001**: The repository MUST hold the skill at `.github/skills/hardening-junos/`.
- **FR-002**: The skill MUST hold one router file with the name `SKILL.md`. That file MUST be
  12 KB or less.
- **FR-003**: The router file MUST hold YAML front matter with a `name` field, a `description`
  field, and an `argument-hint` field. This matches each existing skill in the repository.
- **FR-004**: The skill MUST hold its detail in a `references/` folder. This matches
  `managing-mist-api` and `optimizing-python`.
- **FR-005**: The skill MUST hold 10 files or less. The total size MUST be 400 KB or less.
- **FR-006**: No single file in the skill MUST be more than 90 KB.

#### Corpus scope

- **FR-007**: The skill MUST index the 757 security relevant unique documents. A security
  relevant document is a document with a name that matches one of these terms: security,
  harden, auth, access, firewall, filter, nac, radius, tacacs, 802.1X, cert, pki, crypto,
  ipsec, vpn, stig, fips, common criteria, aaa, login, password, user, admin, management,
  snmp, syslog, ntp, and ssh.
- **FR-008**: The skill MUST NOT index all 9,337 PDF files. A duplicate copy gives no new fact.
- **FR-009**: The skill MUST treat the other unique documents as a second search area. The
  skill MUST state when an answer comes from that second area.
- **FR-010**: The skill MUST use the DISA STIG bundle for the EX switch as a primary source.
  The bundle holds 3 rule sets and 181 rules.
- **FR-011**: The skill MUST use the book `TW_HardeningJunosDevices_2ndEd` and the committed
  checklist at `documentation/references/hardening/hardening-junos-devices-checklist.md` as
  its baseline.

#### Storage split

- **FR-012**: The repository MUST hold only these items: the router file, the reference files,
  and the index file.
- **FR-013**: The converted Markdown MUST stay outside the repository. The PDF files MUST stay
  outside the repository.
- **FR-014**: The repository MUST NOT receive a bulk copy of Juniper text. The skill MUST
  quote a source only in a short extract with a citation. The Juniper documents are
  copyrighted.
- **FR-015**: The repository MUST hold a guard that stops an accidental commit of the corpus.
  A `.gitignore` rule is sufficient.
- **FR-016**: The skill MUST define one corpus root setting. The default value MUST be
  `C:\Users\jmorrison\Downloads\juniper-doc-archives`. A user MUST be able to change it.
- **FR-017**: Each path in the index MUST be relative to the corpus root. The index MUST NOT
  hold an absolute path.

#### Retrieval

- **FR-018**: The router file MUST hold a routing table. Each row MUST give a task, a
  reference file, and the required result. This matches `managing-mist-api`.
- **FR-019**: The skill MUST hold one index file. That file MUST list the 757 security
  relevant documents.
- **FR-020**: Each index row MUST hold these fields: document title, source file name, train,
  relative path, page count, topic group, and gap flag.
- **FR-021**: The index MUST give each document one topic group. The topic groups MUST match
  the 8 sections of the committed checklist.
- **FR-022**: The skill MUST state a written search procedure. The procedure MUST explain how
  to search the staged Markdown for a term.
- **FR-023**: The search procedure MUST tell the reader to search the security subset first.
  It MUST tell the reader to search the full unique set second.
- **FR-024**: The skill MUST NOT depend on a conversion script outside the repository. The
  skill MUST work from the index, the references, and the staged Markdown.

#### Conversion quality

- **FR-025**: Each converted Markdown file MUST hold YAML front matter. The front matter MUST
  hold these fields: `source_file`, `title`, `pages`, `train`, `sha256`, `converter_version`,
  `converted_at`, and `status`.
- **FR-026**: The `pages` value in the front matter MUST equal the page count of the source
  PDF.
- **FR-027**: A converted file MUST give 200 characters or more for each page. A file below
  that floor MUST get the status `review`. A file with the status `review` MUST NOT enter the
  index.
- **FR-028**: The converter MUST make 6 headings or less before the first page marker. A cover
  page that breaks this limit MUST become plain text.
- **FR-029**: A heading MUST NOT break across two lines. The converter MUST join a heading
  that a line break divides.
- **FR-030**: The converter MUST remove a repeated running header. The converter MUST remove a
  page number line.
- **FR-031**: The converter MUST change a bullet glyph to a Markdown list item. The converter
  MUST normalize a ligature and a curly quotation mark.
- **FR-032**: The converter MUST keep a command block and a table as readable text. A
  configuration example MUST stay in the correct order.
- **FR-033**: The conversion MUST write a manifest. The manifest MUST hold one row for each
  source file with its status, page count, and character count.
- **FR-034**: A person MUST audit 30 converted documents by hand. The audit MUST cover 10
  documents from the security subset, 10 documents with many tables, and 10 documents with a
  complex cover page.
- **FR-035**: The audit MUST record a pass or a fail for each of these 5 checks: correct
  title, correct page count, no spurious heading run, readable command text, and readable
  table text.

#### Deduplication and train record

- **FR-036**: The index MUST hold one row for each unique document name. The index MUST NOT
  hold a second row for the same document from a different train.
- **FR-037**: The deduplication rule MUST select the newest readable train. A train is
  readable when the PDF opens and the conversion status is `converted`.
- **FR-038**: When the newest train is unreadable, the rule MUST use the next newest readable
  train. The index MUST record the train that it used.
- **FR-039**: The index MUST record the newest train that holds the document, even when the
  skill uses an older train. The reader must see the difference.
- **FR-040**: When a document changes between trains, the index MUST keep the newest readable
  train. The index MUST record the older train in a `supersedes` field.
- **FR-041**: A change is genuine when the page count differs by more than 2 percent. A change
  is also genuine when the content hash differs and the title is the same. The refresh
  procedure MUST state this test.
- **FR-042**: The skill MUST state the train of each cited document in its answer.

#### Known gaps

- **FR-043**: The skill MUST hold a gap register. The gap register MUST list each document
  that the skill cannot read from its newest train.
- **FR-044**: Each gap row MUST hold these fields: document name, affected trains, the reason,
  the fallback train, and the risk to the reader.
- **FR-045**: The gap register MUST record the two virtual chassis documents,
  `virtual-chassis-ex-4200-4500.pdf` and `virtual-chassis-ex-8200.pdf`. Juniper publishes them
  with a prefix of zeros in trains 25.2, 25.4, and 26.2. Their page trees are gone.
- **FR-046**: The gap register MUST record the readable fallback trains for those two
  documents. Trains 21.1 to 24.4 hold a valid copy.
- **FR-047**: When the skill answers from a document in the gap register, the skill MUST state
  the gap and the fallback train in that answer.
- **FR-048**: The gap register MUST record the 3 documents that the conversion skipped.

#### Safety and writing standard

- **FR-049**: The skill MUST NOT change a device. The skill gives configuration text and the
  reason. A human applies the change.
- **FR-050**: The skill MUST mark each hardening control that can remove access to a device. A
  management filter and an authentication change are examples. The skill MUST state the
  recovery step for each marked control.
- **FR-051**: Each file in the skill MUST follow Simplified Technical English. Each file MUST
  score 80 or more on the repository STE linter.
- **FR-052**: Each file in the skill MUST be written for a junior NOC engineer.
- **FR-053**: The skill MUST state its verified snapshot date and the corpus counts that it
  describes. The counts describe local documents. They do not describe the current Juniper
  website.

### Key Entities

- **Skill**: The `hardening-junos` folder in `.github/skills/`. It holds a router file, a
  reference set, and an index. Its total size is 400 KB or less.
- **Corpus root**: The folder on disk that holds the staged Juniper documents. It is outside
  the git repository. Each index path is relative to it.
- **Source document**: One Juniper PDF and its converted Markdown file. It has a title, a
  train, a page count, a content hash, and a status.
- **Train**: A Junos release family, from 21.1 to 26.2. A document can appear in many trains.
- **Index entry**: One row for one unique document. It holds the title, the train, the
  relative path, the page count, the topic group, and the gap flag.
- **Baseline control**: One item from the 67-item hardening checklist. It has a section, a
  Junos configuration, a reason, a risk, and a source citation.
- **STIG rule**: One rule from a DISA rule set. It has a rule identifier, a severity, a check,
  and a fix. The 3 sets hold 181 rules.
- **Gap record**: One row for a document that the skill cannot read from its newest train. It
  holds the reason, the fallback train, and the risk.
- **Conversion manifest**: The record of one conversion run. It holds one row for each source
  file with its status, page count, and character count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A junior NOC engineer finds a hardening control, its Junos configuration, and
  its source document in less than 2 minutes.
- **SC-002**: All 67 checklist items have at least one source citation. No item is without a
  source.
- **SC-003**: All 181 DISA STIG rules appear in the skill. Each rule has its identifier, its
  severity, its check, and its fix.
- **SC-004**: The repository grows by 400 KB or less. The skill holds 10 files or less.
- **SC-005**: The repository receives no converted corpus file. A review of the commit finds
  0 bytes of bulk Juniper text.
- **SC-006**: Each citation in the skill points to a real file. A test of 50 sample citations
  finds 0 broken paths when the corpus is present.
- **SC-007**: The skill answers from its curated references when the corpus is absent. A test
  with the corpus root removed gives 0 failures.
- **SC-008**: The manual audit of 30 documents finds 27 documents or more that pass all 5
  checks. That is 90 percent.
- **SC-009**: The index holds one row for each of the 757 security relevant documents. It
  holds 0 second rows for the same document name.
- **SC-010**: Each file in the skill scores 80 or more on the repository STE linter.
- **SC-011**: A reviewer who does not know the corpus follows the refresh procedure and adds a
  train without help.
- **SC-012**: The skill states the train for 100 percent of its citations.
- **SC-013**: The skill marks 100 percent of the controls that can remove access, and gives a
  recovery step for each one.

## Decisions and Reasons

### Decision 1: Index the security subset. Keep the rest as a second search area

The skill indexes the 757 security relevant unique documents.

The corpus holds 9,337 PDF files, but only 4,007 names are unique. About 57 percent of the
files repeat the same document across trains 21.1 to 26.2. A duplicate gives no new fact.

The security subset covers the domain of this skill. It converts to 181 MB in 743 files. The
other documents cover routing, MPLS, EVPN, and hardware installation. A hardening question
rarely needs them. A few questions do need them. A firewall filter on a routing protocol is
an example. The skill therefore keeps the full unique set as a second search area, and states
when it uses that area.

### Decision 2: The repository holds the skill only

The largest existing skill is `managing-mist-api`, at 140 KB in 6 files. Each skill in
`.github/skills/` is between 6 KB and 140 KB, and holds 1 to 6 files.

These are the measured conversion sizes.

| Scope | Files | Size | Times the largest skill |
| - | - | - | - |
| All PDF files | 9,337 | About 3.6 GB | About 26,000 |
| Unique documents | 4,007 | 744 MB | About 5,400 |
| Security subset | 743 | 181 MB | About 1,300 |

Even the smallest scope is about 1,300 times the largest skill. No scope fits in the
repository.

Three more reasons support the split.

1. The repository is OneDrive synced. A bulk addition makes a real sync risk.
2. The Juniper documents are copyrighted. The repository must not hold a bulk copy.
3. An agent cannot read 181 MB. A small curated reference set is more useful than a large one.

The repository therefore receives the router file, the reference set, and the index. The
budget is 400 KB. That is about 2.9 times `managing-mist-api`. That is a fair size for a skill
that carries an index.

### Decision 3: An index and a written search procedure, not a helper script

`managing-mist-api` holds a router file and 5 reference files. It holds no script. The
`hardening-junos` skill uses the same shape.

The skill adds one index file, because the corpus is outside the repository. The index gives
the agent the document title, the train, and the relative path. The agent then reads only the
document that the task needs.

The skill states a written search procedure instead of a committed script. A written procedure
gives three benefits. It works with the tools that the agent already has. It does not break
when a tool version changes. It keeps the skill to 10 files or less.

### Decision 4: Ten acceptance rules for the conversion

The converter already works. It finds a heading from the font size. It changes a bullet glyph
to a list item. It removes a repeated running header and a page number. It normalizes a
ligature and a curly quotation mark. It writes YAML front matter with the source path, the
title, and the page count.

The converter has one known weakness. A cover page and display text can make a run of spurious
headings. The staged output shows a real example. One heading breaks across two lines, and
three headings appear in four lines of cover text.

The acceptance rules in FR-025 to FR-035 target that weakness. Two rules are structural: the
heading limit before the first page marker, and the split heading rule. One rule is
quantitative: the floor of 200 characters for each page. One rule is human: the audit of 30
documents.

### Decision 5: The newest readable train wins

A document repeats across trains 21.1 to 26.2. The index must hold one row for each document.

The rule selects the newest readable train. A readable train is a train where the PDF opens
and the conversion status is `converted`.

The rule needs a fallback, because the newest copy is not always readable. The staged
conversion shows this. It took `virtual-chassis-ex-8200.pdf` from train 24.2. It took
`virtual-chassis-ex-4200-4500.pdf` from train 24.4. It did not take them from train 26.2,
because the copies in trains 25.2, 25.4, and 26.2 are unrepairable.

The index records the train that the skill used. It also records the newest train that holds
the document. A reader can then see that a document is older than the newest train.

A document can also change between trains. The test in FR-041 separates a genuine change from
a reprint. A page count that differs by more than 2 percent is a genuine change. A different
content hash with the same title is also a genuine change. The index records the older train
in a `supersedes` field. The skill can then state that an older train differs.

## Assumptions

- The staged corpus stays at `C:\Users\jmorrison\Downloads\juniper-doc-archives` on the
  primary workstation. The skill makes the root a setting, so another user can change it.
- The skill must work when the corpus is absent. A second user who clones the repository has
  the curated references but not the corpus. That user still gets a useful answer.
- The committed checklist at
  `documentation/references/hardening/hardening-junos-devices-checklist.md` is correct. It
  holds 67 items in 8 sections. This feature does not change it.
- The hardening book is from 2015. Some commands changed after that date. The skill checks a
  command against a recent train before it gives that command.
- The DISA STIG bundle covers the EX switch. The skill states that limit. A rule can still
  guide an MX or an SRX device. The skill does not claim that it is tested there.
- The conversion scripts are temporary. They are not part of this feature, and the repository
  does not hold them. This specification defines the skill and its data contract only.
- The corpus is a snapshot. It describes Juniper documents as of the stated date. It does not
  describe the current Juniper website.
- The index uses a compact machine-readable format, so that 757 rows stay below 90 KB.
- The skill gives advice. A human reviews and applies each change. This follows the
  Safety-First principle in the project constitution.

## Out of Scope

- The conversion scripts and the crawler. They live in a temporary folder.
- A change to the committed hardening checklist.
- A live connection to a Junos device or to the Mist cloud.
- An automatic device repair.
- Support for a platform other than MX, EX, SRX, and QFX.
- A rule set from a body other than DISA and Juniper.
- A copy of the corpus in the repository, in a package, or in a container image.

## Dependencies

- The staged corpus at the corpus root, with its `manifest.json`, `selection-inventory.csv`,
  and `extraction-report.json` provenance records.
- The DISA STIG bundle at `extracted/U_Juniper_EX_Switches_Y26M07_STIG/`.
- The book `TW_HardeningJunosDevices_2ndEd` and the sample configuration in its Appendix B.
- The committed checklist at `documentation/references/hardening/`.
- The repository STE linter and its threshold of 80.
- The existing skill pattern at `.github/skills/managing-mist-api/`.
