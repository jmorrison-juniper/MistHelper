# Phase 0 Research: Hardening Junos Skill

**Feature**: `docs/2754-hardening-junos-skill` | **Date**: 2026-09-16

This file resolves each unknown in the technical context. A person measured every number on
2026-09-16. The corpus root was `C:\Users\jmorrison\Downloads\juniper-doc-archives`.

## Decision 1: Use a measured membership rule, not the estimate of 757

**Decision**: The index holds 775 rows. A row enters the index when the document passes one
of three rules and also passes the quality floor.

**Rationale**: The specification states 757 security relevant documents. Measurement gives
four different numbers from four different rules.

| Rule | Count | Markdown size |
| - | - | - |
| The catalog `security` flag | 718 | Not measured alone |
| The FR-007 terms against the file name | 734 | 179.4 MB |
| The FR-007 terms against the file name or the title | 1,073 | Not measured |
| The flag or the FR-007 terms, which is the union | 756 | 181.0 MB |

The union reproduces the size of 181 MB in the specification. It gives 756 documents, not
757. The catalog holds 4,006 rows, and the corpus holds 4,007 unique documents. The missing
row is `_source-archives-index.pdf`, which is an index of archives and not a Juniper manual.
The difference of one row comes from that file.

The plan therefore uses the union rule, adds the checklist need rule from Decision 2, and
removes 8 documents that fail the quality floor in FR-027. The result is 775 rows.

**Alternatives considered**:

- Use the flag alone. Rejected, because FR-007 states the term list and a reader cannot
  reproduce the flag.
- Use the term list against the title as well. Rejected, because the count grows to 1,073 and
  the index grows above the 90 KB limit. The extra rows are mostly release notes.
- Keep the number 757 and select an arbitrary 757 rows. Rejected, because no rule produces
  that set. A reader could not rebuild it.

## Decision 2: Add a checklist need rule for 27 named documents

**Decision**: A named list of Junos platform documents enters the index, even when the file
name matches no term in FR-007.

**Rationale**: The term rule selects 22 of the 135 documents in the train 26.2 archive.
Measurement shows that the term rule misses the primary Junos source for 6 of the 8 checklist
sections.

| Missed document | Pages | Checklist section that needs it | Why the term rule misses it |
| - | - | - | - |
| `routing-policy.pdf` | 2,418 | 7 and 8, the firewall filter and the routing protocol | The name holds no term. The corpus holds no file named `firewall-filter.pdf`. |
| `network-mgmt.pdf` | 1,476 | 4, the management services | The name uses `mgmt`, and the term list holds `management`. |
| `time-mgmt.pdf` | 420 | 4, the NTP control | The name holds no term. |
| `junos-install-upgrade.pdf` | 617 | 1, the recommended Junos version | The name holds no term. |
| `icmp.pdf` | 62 | 3, the ICMP controls | The name holds no term. |
| `bgp.pdf`, `ospf.pdf`, `is-is.pdf` | 1,648, 796, 832 | 7, the route authentication | The names hold no term. |

Without the extra rule, the skill cites no Junos source for 6 sections. SC-002 then fails.
The rule adds 27 rows and about 2.5 KB. The `origin` column marks each added row with `e`, so
a reader can see why the row is present.

**Alternatives considered**:

- Widen the term list. Rejected, because a term such as `policy` or `mgmt` adds hundreds of
  rows from other products. A test with the title match gave 1,073 rows.
- Leave the sections without a Junos source. Rejected, because SC-002 requires one citation
  for each of the 67 items.
- Search the full unique set at answer time. Rejected as the only method, because FR-023
  requires the security subset first. The second search area stays available for a question
  outside the domain.

## Decision 3: Store the index as CSV with an archive code

**Decision**: The index is a CSV file with 8 columns. A 4-character archive code replaces the
directory path. The code table lives in `corpus-operations.md`.

**Rationale**: The 775 rows hold only 165 distinct directories. The average directory is 53
characters, and the longest is 76 characters. A measurement of each candidate gives these
sizes. The first 3 rows come from a catalog build over all 4,006 converted documents.

| Format | Rows | Measured size | Verdict |
| - | - | - | - |
| All documents, all 9 catalog columns | 4,006 | 1,202 KB | 3.0 times the whole budget |
| All documents, slim columns | 4,006 | 593 KB | 1.5 times the whole budget |
| Security subset, all 9 catalog columns | 718 | 224 KB | It fits, and it leaves 176 KB |
| Security subset, slim columns | 718 | 111 KB | It fits, and it leaves 289 KB |
| Security subset, lean columns | 718 | 109 KB | The saving over the slim set is 2 KB |
| CSV with an archive code | 775 | 70.0 KB, plus 28.8 KB for the archive table | Selected |
| CSV with a full path in each row | 775 | 145.4 KB | Above the 90 KB limit |
| A Markdown table with an archive code | 775 | About 85 KB | Near the limit, and it grows on any edit |

The archive code is the reason for the saving. The `markdown_path` column costs 75.4 KB for
775 rows. The chosen set beats the lean variant by 39 KB, and it still carries 5 more columns
and 57 more rows.

Two smaller measurements support the format. A cut of the title to 70 characters saves 0.6 KB.
LF line endings save 0.8 KB against CRLF, which is 1 byte for each row.

The path rule holds for all 775 rows. The PDF path is `<archive>/<file>.pdf`. The Markdown
path is `markdown/<archive>/<file>.md`. A test of the rule against the catalog gave 0
failures.

**Alternatives considered**:

- A second CSV file for the code table. Rejected, because `references/` would then hold 6
  children and break the Five-Item Rule.
- A comment block at the top of the CSV. Rejected, because a standard CSV reader fails on it.

## Decision 4: Condense each STIG rule to one row

**Decision**: `stig-rules.md` gives the identifier, the severity, the title, a one-line check,
and a one-line fix for each of the 181 rules. The full text stays in the XCCDF file.

**Rationale**: The full rule text is too large for the skill. A measurement of the 3 XCCDF
files gives these sizes.

| Field | Characters | Size |
| - | - | - |
| Title | 25,675 | 25.1 KB |
| Check | 295,946 | 289.0 KB |
| Fix | 174,998 | 170.9 KB |
| Total | 496,619 | 485.0 KB |

The full text is 485 KB. The whole skill budget is 400 KB. A condensed row of about 280
characters gives 181 rows in about 50 KB. The rule severity split is 25 high, 122 medium, and
34 low.

DISA publishes the STIG for public download, so the file is not Juniper material. The
reference still points to the XCCDF file at the corpus root and to the public DISA download,
so a reader can open the full check text.

**Alternatives considered**:

- Ship the full check and fix text. Rejected, because 485 KB breaks FR-005 and FR-006.
- Ship the high severity rules only. Rejected, because SC-003 requires all 181 rules.
- Split the rules across 3 files, one for each rule set. Rejected, because `references/`
  would hold 7 children and break the Five-Item Rule.

## Decision 5: Treat the train as an optional field

**Decision**: The `train` column holds a Junos train when the archive is a train archive.
Otherwise it holds `-`. The skill states the archive when no train exists.

**Rationale**: Only 48 of the 775 index rows carry a train. The other 727 rows come from a
product archive, such as `SRC-DOC-CD31x` or `junos-for-srx-doc-set-pdfs`. Those archives
carry a product version, not a Junos train.

FR-042 requires the skill to state the train of each cited document. A literal reading fails
for 727 rows. The skill therefore states one of two facts.

- The Junos train, when the index holds one.
- The archive name and its product version, and the statement that the document has no Junos
  train.

The deduplication rule in FR-037 still applies. The conversion already removed 5,330 duplicate
copies and kept the newest readable copy. The index inherits that result and holds one row for
each document name.

**Alternatives considered**:

- Infer a train from the document date. Rejected, because a product document has no train,
  and a guess would be wrong.
- Drop the train column. Rejected, because 48 rows carry a real train and FR-020 requires the
  field.

## Decision 6: Record the front matter gap instead of a re-conversion

**Decision**: The index carries the train, the page count, and the gap flag. The front matter
contract for the next conversion run lives in `corpus-operations.md`.

**Rationale**: FR-025 requires 8 front matter fields. The staged Markdown holds 7 fields, and
5 of the required fields are absent.

| Field | Present in the staged Markdown |
| - | - |
| `source_file`, `title`, `pages` | Yes |
| `author`, `subject`, `creationDate`, `modDate` | Yes, and FR-025 does not require them |
| `train`, `sha256`, `converter_version`, `converted_at`, `status` | No |

A re-conversion of 4,007 files takes 317 seconds of machine time, but it also needs the
converter, which the specification puts out of scope. The index supplies the missing facts for
every indexed document, so the skill loses nothing. The next conversion run adds the fields.

**Alternatives considered**:

- Re-convert the corpus now. Rejected, because the converter is out of scope and the work is
  not needed for an answer.
- Write the fields into 775 staged files. Rejected, because the corpus is outside the
  repository and a second user would not receive the change.

## Decision 7: The skill ships no script, and the repository converter stays in `scripts/`

**Decision**: The skill folder holds documentation and one data file. It holds no Python file
and no PowerShell file. The converter work happens in `scripts/pdf_to_markdown.py`, which is
outside the skill.

**Rationale**: The repository skills hold documentation only. `managing-mist-api` holds 1
router file and 5 reference files. `optimizing-python` holds 1 router file and 4 reference
files. FR-024 also forbids a dependency on an outside conversion script. The converter is not
outside the repository, because the repository already commits it. Decision 14 covers the
upgrade.

A written procedure works with the tools that the agent already holds. It does not break when
a tool version changes. The agent writes its own throwaway code when it rebuilds the index.

**Alternatives considered**:

- Ship a search helper script inside the skill. Rejected, because the agent already holds a
  search tool, and a script needs a test, a lint gate, and inline comments under Principle VI.
- Ship an index builder script inside the skill. Rejected for the same reason. The refresh
  procedure states the 3 membership rules, the quality floor, and the column list, which is
  enough to rebuild the index.
- Move the converter into the skill folder. Rejected, because `.gitignore` names
  `scripts/pdf_to_markdown.py`, and the repository forbids a second implementation of one job.

## Decision 8: Correct the record of the 3 skipped documents

**Decision**: The gap register records all 3 documents with the state `converted earlier`.

**Rationale**: FR-048 calls them documents that the conversion skipped. Measurement shows a
different cause. All 3 hold a Markdown file with correct front matter and a correct page
count.

| Document | Markdown size | Pages in the front matter |
| - | - | - |
| `AWS_vSRX_Cookbook22.pdf` | 224,947 bytes | 132 |
| `2001701 ... DoDIN APL Approval Memo DTR9.pdf` | 5,617 bytes | 2 |
| `_source-archives-index.pdf` | 60,284 bytes | Not a Juniper manual |

The `skipped` status means that the output already existed when the run started. The manifest
records `pages: 0` for a skipped file, because the run did not open the PDF again. A reader
who trusts the status alone would believe that 3 documents are missing. The register states
the true cause.

**Alternatives considered**:

- Record them as failures. Rejected, because the files are readable and the record would be
  false.
- Omit them. Rejected, because FR-048 requires a record.

## Decision 9: State the corpus root as a setting and answer without it

**Decision**: `corpus-operations.md` names one setting for the corpus root. The default value
is `C:\Users\jmorrison\Downloads\juniper-doc-archives`.

**Rationale**: The corpus is 26.1 GB on one workstation. A second user clones the repository
and receives the skill only. FR-016 requires the setting, and SC-007 requires an answer when
the corpus is absent.

The curated references carry the 67 controls and the 181 STIG rules. Neither needs the corpus
at answer time. The index gives the title, the train, the page count, and the path, so the
skill can still name the source document. The skill then states that the file is absent.

**Alternatives considered**:

- Require the corpus. Rejected, because SC-007 forbids a failure.
- Store the corpus root in a repository file that a user edits. Rejected, because a user
  change would appear in every later difference. The setting lives in the skill text, and a
  user states the root in the request.

## Decision 10: Grade the Markdown files and check the CSV another way

**Decision**: The writing gate grades the 5 Markdown files. The index CSV gets 4 structural
checks.

**Rationale**: A measured run proves that the STE linter rejects a CSV file. The command
`python -m tools.ste_linter --min-score 80 documentation/APUpgradeSiteListSample.CSV` returns
exit code 2 and the message `only .md and .py files are graded`. A file list that holds the
CSV therefore fails the gate for the wrong reason.

The CSV holds no authored prose. Its `title` column holds the title from the PDF metadata of
the source document. Checks V5 to V8 test the row count, the column count, the absence of an
absolute path, and the resolution of each path.

The existing skills score 96 to 99 on the linter, so the threshold of 80 is comfortable.

**Alternatives considered**:

- Grade the CSV with a lowered threshold. Rejected, because the tool skips the file type.
- Rewrite the index as Markdown to make it gradable. Rejected, because of the size and because
  the linter would grade Juniper titles, not authored text.

## Decision 11: Follow the ignored vendor corpus policy that the repository already runs

**Decision**: The skill never cites a path below `documentation/references/`. It cites a public
URL first and the corpus root path second.

**Rationale**: An earlier draft of this plan reported that the hardening checklist was lost,
and it made the file a prerequisite. That report was wrong. The file is present on one
workstation. It is in no commit, because the whole directory is ignored on purpose.

```text
git check-ignore -v documentation/references/hardening/hardening-junos-devices-checklist.md
.gitignore:28:documentation/references/
```

`.gitignore` lines 20 to 28 state the reason. The directory holds verbatim vendor text under
Juniper copyright. The comment states that the distilled runbooks under
`documentation/noc-runbooks/` are committed instead. `git ls-files documentation/references`
returns 0 files. `git ls-files documentation/noc-runbooks` returns 15 files.

The repository therefore already runs the policy that the specification proposes. Verbatim
vendor text stays out. Distilled text goes in.

A second measurement makes the citation rule necessary. `Test-Path documentation\references`
in this worktree returns `False`. Git does not materialize an ignored directory into a new
worktree or a fresh clone. A citation to that path would be broken for every reader except the
author.

**Alternatives considered**:

- Commit the checklist Markdown at that path. Rejected, because `.gitignore` line 28 blocks it
  and the copyright reason still holds.
- Commit the checklist under another name outside the ignored path. Rejected, because the file
  is a verbatim conversion of a Juniper poster. The skill distills it instead.
- Keep the prerequisite. Rejected, because the premise was false.

## Decision 12: Quote a source in a short extract only

**Decision**: A reference file states a control in its own words. It quotes a source in a
short extract with a citation.

**Rationale**: FR-014 forbids a bulk copy of Juniper text. The Juniper documents carry a 2015
or later copyright. The corpus holds 767 million characters of converted text. A copy of even
one chapter would be a bulk copy. `.gitignore` line 28 applies the same rule to the older
vendor corpus, which makes this repository practice and not only a specification rule.

A control needs the Junos command, the reason, and the risk. The author writes those from the
source. The Junos command itself is configuration syntax, not prose. The citation gives the
document, the train, and the page, so a reader can confirm the statement.

The DISA STIG text is a United States Government work and not Juniper material. The plan still
condenses it, because of the size limit in Decision 4.

**Alternatives considered**:

- Copy the checklist chapters. Rejected under FR-014 and under the `.gitignore` policy.
- Give no source text at all. Rejected, because a junior engineer needs the exact command.

## Decision 13: Follow the citation style of the committed runbooks

**Decision**: Each reference file ends with a `Sources` section. That section gives the
document, the train, and a public URL. The archive table carries the public URL of each
archive.

**Rationale**: `documentation/noc-runbooks/` holds 15 committed distilled documents that cite
the same ignored corpus. Their convention is measured, not assumed.

| Element | The runbook text |
| - | - |
| The sources table | Section 14 of `SSR_CONSOLE_HEALTH_CHECK.md` gives a `Source` and `Where` table with 8 public URLs. |
| The local copy | `_shared_common.md` line 117 names `documentation/references/ssr/` and states that it is not committed. |
| The reason | The same line states that the directory holds verbatim vendor text. |
| The rebuild | Both files name `python scripts/fetch_ssr_docs.py` and `python scripts/pdf_to_markdown.py`. |
| The offline use | Section 14 states that a reader confirms a command against the local copy without network access. |

The new skill uses the same 5 elements. It names the corpus root in place of
`documentation/references/ssr/`, because the Juniper corpus lives at the corpus root. A
measured run shows that 162 of the 165 archives in the index have a public URL in
`selection-inventory.csv`, so the table can carry a durable citation for almost every row.

**Alternatives considered**:

- Cite the corpus path alone. Rejected, because a reader without the corpus then has no way to
  reach the source.
- Cite the public URL alone. Rejected, because the corpus answers an offline question, and the
  runbooks keep both.

## Decision 14: Upgrade the committed converter

**Decision**: Upgrade `scripts/pdf_to_markdown.py` so that the documented rebuild command
produces a corpus that satisfies the acceptance rules.

**Rationale**: `.gitignore` lines 20 to 28 already promise that command to a reader. The
promise is false today. The committed script writes a flat page dump. A measurement of the two
converters gives this gap.

| Behavior | The staged converter | The committed script |
| - | - | - |
| Library | PyMuPDF 1.28.2 | `pypdf`, which no requirements file declares |
| Front matter | 2 fields always, and 5 more when the metadata gives them | None |
| Headings | Detected from the font size | One fixed heading for each page |
| Bullet glyph | Becomes a list item | Unchanged |
| Running header and page number | Removed | Kept |
| Ligature and curly quotation mark | Normalized | Unchanged |
| Throughput | 511,674 pages in 317.4 seconds across 26 workers | One file at a time, in one process |

A promise that does not reproduce the data is a defect. The repository convention also forbids
a second implementation of one job, so a new converter under another name is not an option.

The cost is real. The deliverable gains committed code, so the 5 Python gates now apply. The
plan records the gates as check V14 and the structural test as check V15. Decision 15 selects
the library, and Decision 16 states why the test compares structure and not bytes.

**Alternatives considered**:

- Keep the script and state that a different converter produced the corpus. Rejected. It keeps
  the deliverable free of code, but it leaves the rebuild procedure unable to reproduce the
  corpus and leaves the `.gitignore` promise false.
- Write a second converter under a new name. Rejected, because the repository forbids a
  duplicate implementation.

## Decision 15: Use pdfplumber. Do not add PyMuPDF

**Decision**: The upgraded converter uses `pdfplumber`. The repository does not declare
PyMuPDF.

**Rationale**: Heading detection needs the font size of each text span. `pypdf` does not give
it, so the current dependency cannot reproduce the corpus. Two candidates give it, and a
measurement settles the choice.

| Library | License | Font size | Measured speed | Declared in `pyproject.toml` |
| - | - | - | - | - |
| pdfplumber 0.11.10 | MIT | Yes, through the `size` key of each `char` object | 18.0 to 21.6 pages for each second | Yes |
| PyMuPDF 1.28.2 | Dual Licensed, GNU Affero GPL 3.0 or an Artifex commercial license | Yes | 88.8 to 109.4 pages for each second | No |
| pypdf 6.16.2 | BSD | No | Not measured | No |

Three reasons select `pdfplumber`.

1. It removes the AGPL exposure from a distributed container image.
   `.github/workflows/container-build.yml` sets `REGISTRY: ghcr.io` and `push: true`. A push to
   a public registry is distribution, which is the condition that the AGPL acts on.
2. It adds no dependency. `pyproject.toml` already declares `pdfplumber>=0.11.0` for the
   ASD-STE100 dictionary work.
3. The speed cost is small for this task. `pdfplumber` is about 5 times slower. A full rebuild
   of 511,674 pages across 26 workers takes about 0.3 hours, against about 5 minutes with
   PyMuPDF. A reader runs the rebuild once.

A measurement proves that `pdfplumber` gives the needed input. A scan of 12 pages of `pki.pdf`
returns the font sizes 9.0, 10.0, 10.3, 11.0, 12.9, 14.0, 20.0, 26.0, and 30.0. The modal size
is 9.0, which is the body text. A larger size promotes a heading.

**Alternatives considered**:

- PyMuPDF with a commercial license. Rejected, because the cost and the process are larger
  than the 15 minute saving.
- PyMuPDF under the AGPL. Rejected, because the container image is a distribution.
- Keep `pypdf` and drop the heading rule. Rejected, because FR-028 and FR-029 need the font
  size.

## Decision 16: State that two readers produced the two corpora

**Decision**: The plan states plainly that the staged corpus came from PyMuPDF, and that the
committed converter uses `pdfplumber`. The acceptance test compares structure, not bytes.

**Rationale**: A person produced the staged corpus with PyMuPDF on one workstation. That use
is local, and it distributes nothing, so it carries no license problem. It matches the way the
repository generates `data/ste_dictionary.json` locally and never commits it.

The consequence is honest and small. Two readers do not agree byte for byte. A test that
demands identical bytes would fail for a correct converter. Check V15 therefore tests the
structural contract of a 30 file sample.

A second consequence needs a record. The quality floor in FR-027 counts characters, and a
different reader gives a different character count. A measurement of the character density of
the selection shows the size of the risk.

| Characters for each page | Documents | Effect of a reader change |
| - | - | - |
| Under 150 | 5 | They stay excluded. |
| 150 to 200 | 3 | They can enter the index. |
| 200 to 250 | 8 | They can leave the index. |
| 250 to 400 | 54 | No practical risk |
| 400 or more | 686 | No risk |

Up to 11 rows of 775 can move, which is 1.4 percent. The row count of 775 is therefore a
measurement against the staged corpus. The tasks phase measures it again after the rebuild.

**Alternatives considered**:

- Rebuild the corpus before the plan lands. Rejected, because the rebuild needs the upgraded
  converter, which the tasks phase writes.
- Keep the PyMuPDF corpus forever. Rejected, because two readers then produce one corpus. The
  converter task rebuilds the corpus with `pdfplumber`, so that one reader produces all of it.
