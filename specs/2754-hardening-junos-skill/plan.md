# Implementation Plan: Hardening Junos Skill

**Branch**: `docs/2754-hardening-junos-skill` | **Date**: 2026-09-16 | **Spec**: `specs/2754-hardening-junos-skill/spec.md`

**Input**: Feature specification from `specs/2754-hardening-junos-skill/spec.md`

## Summary

Add one project skill at `.github/skills/hardening-junos/`.
The skill holds a router file, four Markdown references, and one index file.
The total size is 400 KB or less.

The skill answers a hardening question with a control, a Junos command, a reason, and a
citation. The curated references hold the answers. The index holds the location of each
source document. The converted corpus of 744 MB stays outside the repository.

A person measured every number in this plan on 2026-09-16.
The `Verified claims` section gives the command for each number.

## Technical Context

**Language/Version**: Markdown and CSV. Python 3.13 runs the verification commands only.

**Primary Dependencies**: The staged corpus at the corpus root, the DISA STIG bundle, the
hardening book, and the committed hardening checklist.

**Storage**: Git tracked Markdown and CSV files. No database. No binary file.

**Testing**: The STE linter at `--min-score 80`, plus the verification commands in
`quickstart.md`.

**Target Platform**: A Windows development worktree. A Linux agent reads the same files.

**Project Type**: Documentation and skill guidance. The skill ships no script.

**Performance Goals**: A reader finds a control and its source in less than 2 minutes.
An agent reads 12 KB before it selects a reference.

**Constraints**: 400 KB total, 90 KB for each file, 10 files or less, and 5 children or less
in each folder. No Juniper PDF file enters the repository. No bulk Juniper text enters the
repository.

**Scale/Scope**: 6 skill files, 67 baseline controls, 181 STIG rules, and 775 index rows.
The index covers 141,372 pages of source material.

## Constitution Check

*GATE: This gate passed before Phase 0. This gate passed again after Phase 1.*

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | Pass with one recorded violation | The skill folder holds 2 children. The `references/` folder holds 5 children. The parent `.github/skills/` grows from 5 children to 6. The `Complexity Tracking` section records this violation. The converter keeps 5 parameters, 5 blocks, and 25 lines for each method. |
| II. Class-Based Architecture | Pass | The converter keeps the classes `PdfMarkdownConverter` and `PdfMarkdownCommand`. The upgrade adds no wrapper function. |
| III. Safety-First | Pass | The skill changes no device. Each control that can remove access carries a recovery step. The skill refuses a live change request. The converter reads a file and writes a file. It takes no device action. |
| IV. Full Deployment Pipeline | Pass | The feature follows the branch, pull request, and squash merge rules. It adds one release-note fragment. |
| V. Observability and Logging | Pass | The converter keeps ASCII logging with `%s` formatting. |
| VI. Inline Comments | Pass | Every changed line of the converter carries a comment. |
| VII. Action Logging | Pass | The converter logs an `info` message before each action and a `debug` message after it. |
| Audience Standard | Pass | Each file targets a junior NOC engineer. Each Markdown file scores 80 or more on the STE linter. |
| Documentation rule | Pass | The skill folder ships documentation and one data file. The converter lives in `scripts/`, outside the skill. Section 7 gives the reason. |
| Vendor text rule | Pass | `.gitignore` line 28 ignores `documentation/references/`. The skill ships distilled text and cites a public URL. Section 3a states the rule. |

## Project Structure

### Documentation for this feature

```text
specs/2754-hardening-junos-skill/
├── spec.md              # Committed as ca35cf5a
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Entities and fields
├── quickstart.md        # Validation scenarios and commands
├── contracts/
│   ├── corpus-index.md      # The index file contract
│   ├── skill-interface.md   # The router and answer contract
│   └── gap-register.md      # The gap record contract
└── tasks.md             # Phase 2 output, not created by this command
```

### Files in the repository

```text
.github/skills/hardening-junos/
├── SKILL.md
└── references/
    ├── baseline-controls.md
    ├── stig-rules.md
    ├── corpus-index.csv
    ├── corpus-operations.md
    └── verification.md

scripts/pdf_to_markdown.py                    # Upgrade the committed converter
tests/test_pdf_to_markdown.py                 # New unit tests for the converter
pyproject.toml                                # Declare the PDF library
.gitignore                                    # Add the corpus root guard
.github/workflows/ste-lint.yml                # Add the skill files to the writing gate
changelog.d/issue-2754-hardening-junos-skill.md
```

**Structure Decision**: The skill copies the shape of `.github/skills/managing-mist-api/`.
That skill holds one router file and 5 reference files. It ships no script. The new skill
replaces one reference with the index file, because the corpus is outside the repository.

The skill folder holds documentation only. The converter lives in `scripts/`, which is outside
the skill. Section 7 gives the reason.

## 1. The file list and the size budget

The budget holds a margin for each file. The expected size comes from a measured count of
rows, controls, or rules.

| File | Budget | Expected | Rows or items | Content |
| - | - | - | - | - |
| `SKILL.md` | 12 KB | 11 KB | 8 routing rows | Front matter, routing table, safety rules, and the answer contract. |
| `references/baseline-controls.md` | 85 KB | 62 KB | 67 controls | One entry for each checklist item, with the Junos command, the reason, the risk, the recovery step, and the citation. |
| `references/stig-rules.md` | 60 KB | 50 KB | 181 rules | One condensed row for each DISA rule, plus the map to the 8 checklist sections. |
| `references/corpus-index.csv` | 85 KB | 70.0 KB | 775 rows | The document index. The `contracts/corpus-index.md` file holds its schema. |
| `references/corpus-operations.md` | 60 KB | 51 KB | 165 archive codes | The corpus root setting, the search procedure, the refresh procedure, the deduplication rule, the acceptance rules, the gap register, and the archive table of 28.8 KB with a public URL for each archive. |
| `references/verification.md` | 25 KB | 18 KB | 13 checks | The evidence commands and the acceptance scenarios. |
| **Total** | **327 KB** | **262 KB** | | The limit is 400 KB. |

The budget leaves 73 KB of headroom. The largest file stays below the 90 KB limit in FR-006.
The skill holds 6 files, which meets the limit of 10 files in FR-005.

Six files change outside the skill folder. They do not count against the 400 KB budget,
because SC-004 measures the skill folder. The six files are the converter, its test, the
dependency declaration, the `.gitignore` guard, the writing gate workflow, and the
release-note fragment. Section 7 covers the first three.

## 2. The index format

The index is one CSV file with a header row and 775 data rows.
The chosen column set measures **70.0 KB**. The archive table adds 28.8 KB in
`corpus-operations.md`, which gives 98.8 KB in total.

### Measured variants

A person built a catalog from the front matter of all 4,006 converted documents. A person then
measured the CSV size of each variant. The first 5 rows use CRLF line endings. The last 3 rows
use LF line endings, which the contract requires. LF saves 1 byte for each row.

| Variant | Rows | Columns | Size | Verdict |
| - | - | - | - | - |
| All documents, all 9 catalog columns | 4,006 | 9 | 1,202 KB | 3.0 times the whole budget |
| All documents, slim columns | 4,006 | 4 | 593 KB | 1.5 times the whole budget |
| Security subset, all 9 catalog columns | 718 | 9 | 224 KB | It fits, but it leaves 176 KB |
| Security subset, slim columns | 718 | 4 | 111 KB | It fits, and it leaves 289 KB |
| Security subset, lean columns | 718 | 3 | 109 KB | The third column saves only 2 KB |
| **Chosen: 775 rows with an archive code** | **775** | **8** | **70.0 KB** | **Selected** |
| The chosen set with a full `markdown_path` | 775 | 8 | 145.4 KB | Above the 90 KB file limit |
| The chosen set with an untruncated title | 775 | 8 | 70.6 KB | The cut to 70 characters saves 0.6 KB |

The slim column set is `title`, `train`, `pages`, and `markdown_path`. The lean column set
drops `pages`.

The measurement confirms Decision 1 of the specification. The full set of 4,006 documents does
not fit. Even the slim column set at 593 KB is larger than the whole budget, before the router
file and the reference files count against it. The security subset is the only scope that
fits.

The chosen set beats the lean variant by 39 KB. It also carries 57 more rows and 5 more
columns. The `markdown_path` column causes the difference. A full path costs 145.4 KB for 775
rows, because the average directory is 53 characters and the longest is 76 characters.

### Columns

| Column | Type | Example | Purpose |
| - | - | - | - |
| `file` | Text | `user-access` | The file name of the source PDF, without the extension. |
| `title` | Text | `Junos OS User Access and Authentication User Guide` | The document title, cut to 70 characters. |
| `group` | `G1` to `G8` | `G6` | The topic group. The 8 groups match the 8 sections of the committed checklist. |
| `train` | Text | `26.2` or `-` | The Junos train. The value is `-` when the archive is not a train archive. |
| `pages` | Integer | `1154` | The page count of the source PDF. |
| `archive` | `A001` to `A165` | `A006` | The archive code. The code table in `corpus-operations.md` gives the directory. |
| `origin` | `f`, `t`, or `e` | `t` | The reason that the row is in the index. |
| `gap` | `-`, `c`, or `s` | `-` | The gap flag. The gap register gives the detail. |

A reader builds the two paths from the row. The rule holds for all 775 rows.

- The PDF path is `<archive>/<file>.pdf`.
- The Markdown path is `markdown/<archive>/<file>.md`.

Both paths are relative to the corpus root, as FR-017 requires. The index holds no absolute
path.

### Row count and membership

A row enters the index when the document passes one of three rules and also passes the
quality floor.

| Rule | Code | Rows | Definition |
| - | - | - | - |
| Security flag | `f` | 710 | The corpus catalog marks the document as security relevant. |
| Term match | `t` | 38 | The file name holds one of the 28 terms in FR-007, and the flag is absent. |
| Checklist need | `e` | 27 | A named document that a checklist section needs. The term rule misses it. |
| **Total** | | **775** | |

The quality floor removes 8 documents. Each removed document gives less than 200 characters
for each page, which FR-027 forbids. The index records no row for them.

The checklist need rule is new. The plan adds it, because measurement shows that the term
rule alone misses the primary Junos source for 6 of the 8 checklist sections. The
`Decision 2` entry in `research.md` holds the evidence.

### Why the archive table is separate

The 775 rows hold only 165 distinct directories. A measured run gives 145.4 KB with a full
`markdown_path` column and 70.0 KB with a 4-character code. The code therefore saves 75.4 KB
and keeps the file below the 90 KB limit in FR-006. The Five-Item Rule also forbids a sixth
file in `references/`.

The table costs 28.8 KB, because it carries a fourth column. That column holds the public URL
of each archive, which follows the citation rule in section 3a. A measured run shows that 162
of the 165 archives have a URL in `selection-inventory.csv`. The 3 archives without a URL are
the bundles that a person added by hand.

## 3. The source of each reference file

The corpus feeds the curated files. This table names the primary source for each file. The
`Verified claims` section proves that each source exists.

Warning: no reference file may cite a path under `documentation/references/`. `.gitignore`
line 28 ignores that directory, because it holds verbatim vendor text. A clone does not
receive it, and a new worktree does not receive it. A measured test in this worktree gives
`Test-Path documentation\references` as `False`. Section 3a states the citation rule.

| Reference file | Primary sources | Method |
| - | - | - |
| `baseline-controls.md` | The Juniper hardening checklist poster, at <https://www.juniper.net/assets/kr/kr/local/pdf/books/tw-hardening-junos-devices-checklist.pdf>, for the 67 items and the 8 sections. The corpus copy is `extracted/TW_HardeningJunosDevices_2ndEd/TW_HardeningJunosDevices_2ndEd_Checklist.pdf`. `extracted/TW_HardeningJunosDevices_2ndEd/TW_HardeningJunosDevices_2ndEd.pdf` gives the reason of each control, at 152 pages. `AppendixB_MediumSecuritySampleConfig.rtf` gives the sample configuration. | An author writes one entry for each of the 67 items. The author confirms each Junos command against the newest train document in the table below. The author writes the command, not a copy of the book text. |
| `stig-rules.md` | The 3 XCCDF files in `extracted/U_Juniper_EX_Switches_Y26M07_STIG/`. The public download page is <https://public.cyber.mil/stigs/>. | A parser reads the `Rule` elements. It writes the identifier, the severity, the title, a one-line check, and a one-line fix. The full rule text stays in the XCCDF file. |
| `corpus-index.csv` | The front matter of each file under `markdown/`, and `markdown/_conversion-manifest.json`. | A build applies the 3 membership rules and the quality floor. It writes 775 rows. |
| `corpus-operations.md` | `extraction-report.json`, `selection-inventory.csv`, and `markdown/_conversion-manifest.json`. | The author writes the procedures. The author copies no document text. The archive table carries the public URL of each archive. |
| `verification.md` | This plan and `quickstart.md`. | The author writes the commands and the expected results. |

## 3a. The citation rule

`documentation/noc-runbooks/` holds 15 committed distilled runbooks that cite the same ignored
corpus. The new skill follows their convention.

| Element | Rule | Evidence from the precedent |
| - | - | - |
| The durable citation | The public URL of the document | `SSR_CONSOLE_HEALTH_CHECK.md` section 14 gives a `Source` and `Where` table of 8 public URLs. |
| The local copy | The relative path below the corpus root | The runbooks name `documentation/references/ssr/` and state that it is not committed. The new skill names the corpus root instead, because the Juniper corpus lives there. |
| The reason | A statement that the vendor text is not committed | `_shared_common.md` line 117 states it in one sentence. |
| The rebuild | The command that recreates the local copy | The runbooks name `python scripts/fetch_ssr_docs.py` and `python scripts/pdf_to_markdown.py`. |
| The offline use | A statement that a reader confirms a command against the local copy | `SSR_CONSOLE_HEALTH_CHECK.md` states it. |

Each reference file therefore ends with a `Sources` section. That section gives the document,
the train, and the public URL. The archive table in `corpus-operations.md` carries the public
URL of each archive. A measured run shows that 162 of the 165 archives have a URL in
`selection-inventory.csv`.

The skill cites 3 kinds of place. It never cites the fourth.

1. A public URL. Every reader can open it.
2. A path below the corpus root. A reader with the staged corpus can open it.
3. A committed repository path, such as `documentation/noc-runbooks/`.
4. A path below `documentation/references/`. The skill never cites this, because the path is
   ignored and absent after a clone.

### The Junos source for each checklist section

The author confirms each command against these documents. Train 26.2 is the newest train in
the corpus.

| Section | Primary Junos source | Train | Pages | In the index |
| - | - | - | - | - |
| 1. Administrative | `junos-install-upgrade.pdf`, `junos-os-release-notes-26.2r1.pdf` | 26.2 | 617, 208 | Yes, by the checklist need rule |
| 2. Physical security | `chassis.pdf`, `interfaces-ethernet-switches.pdf` | 26.2 | 220, 335 | Yes, by the checklist need rule |
| 3. Network security | `icmp.pdf`, `neighbor-discovery.pdf`, `denial-of-service.pdf` | 26.2 | 62, 72, 210 | Yes, by the checklist need rule |
| 4. Management services | `network-mgmt.pdf`, `time-mgmt.pdf`, `system-logs.pdf` | 26.2 and the SRX set | 1476, 420, 184 | Yes, by the checklist need rule |
| 5. Access security | `user-access.pdf`, `cli.pdf`, `netconf.pdf` | 26.2 | 1154, 339, 696 | Yes. `user-access.pdf` matches the term rule. |
| 6. User authentication | `user-access.pdf`, `network-access-protocols.pdf`, `pki.pdf` | 26.2 | 1154, 83, 168 | Yes, by the term rule |
| 7. Routing protocol | `bgp.pdf`, `ospf.pdf`, `is-is.pdf`, `routing-policy.pdf` | 26.2 | 1648, 796, 832, 2418 | Yes, by the checklist need rule |
| 8. Firewall filter | `routing-policy.pdf`, `denial-of-service.pdf`, `cos.pdf` | 26.2 | 2418, 210, 1089 | Yes, by the checklist need rule |

The hardening book is from 2015. A command in the book can be old. The author therefore
confirms each command against the 26.2 document before the author writes it. The reference
records both sources, as FR-042 requires.

## 4. Verification

Each check has one command. `quickstart.md` gives the full script for each check.
The tasks phase must not report success until every check passes.

| Check | Command | Expected result |
| - | - | - |
| V1. Writing standard | `python -m tools.ste_linter --min-score 80 @((Get-ChildItem .github/skills/hardening-junos -Recurse -Filter *.md).FullName)` | Exit code 0. Each of the 5 Markdown files scores 80 or more. |
| V2. Total size | `'{0:N0} KB' -f ((Get-ChildItem .github/skills/hardening-junos -Recurse -File \| Measure-Object Length -Sum).Sum / 1KB)` | 400 KB or less. |
| V3. File count and file size | `Get-ChildItem .github/skills/hardening-junos -Recurse -File \| Select-Object Name, Length` | 6 files. Each file is 90 KB or less. |
| V4. Folder width | `Get-ChildItem .github/skills/hardening-junos/references \| Measure-Object` | 5 children or less. |
| V5. Index shape | A `csv.DictReader` count of rows and columns | 775 rows and 8 columns. |
| V6. No absolute path | `Select-String -Path .github/skills/hardening-junos/references/corpus-index.csv -Pattern '[A-Za-z]:\\\|^/'` | No match. |
| V7. Citation resolution | A script that joins 50 sampled rows to the corpus root and tests each path | 50 of 50 paths exist. 0 broken paths. |
| V8. Index and manifest agreement | A script that compares each index row against `markdown/_conversion-manifest.json` | 0 missing files. 0 status mismatches. |
| V9. STIG coverage | A count of distinct rule identifiers in `stig-rules.md` | 181 identifiers. 25 high, 122 medium, and 34 low. |
| V10. Checklist coverage | A count of control identifiers in `baseline-controls.md` | 67 controls in 8 sections. Each control holds one citation. |
| V11. Corpus absent | Set the corpus root to a folder that does not exist. Ask 5 hardening questions. | 5 answers. Each answer states that the corpus is absent. 0 failures. |
| V12. Commit guard | `git check-ignore -v <corpus path>` and `git diff --cached --stat` | The guard matches the corpus path. The staged change holds no PDF file and no bulk text. |
| V13. No ignored citation | `Select-String -Path .github/skills/hardening-junos -Recurse -Pattern 'documentation/references'` | No match. The path is ignored, so a clone does not hold it. |
| V14. Python gates for the converter | `ruff check scripts/pdf_to_markdown.py`, `black --check scripts/pdf_to_markdown.py`, `mypy scripts/pdf_to_markdown.py`, `bandit -c pyproject.toml scripts/pdf_to_markdown.py`, and `pytest tests/test_pdf_to_markdown.py --cov` | 0 violations for each tool. Coverage is 80 percent or more. |
| V15. The converter output is correct | Convert 30 sample PDF files with the upgraded script. Test each output against the structural contract. | The front matter holds `source_file` and `pages`, and it holds each other field that the PDF metadata gives. The file holds at least 1 heading and 6 headings or less before the first page marker. The text gives 200 characters or more for each page. The file holds no ligature and no curly quotation mark. |

Warning: the STE linter returns exit code 2 when the file list holds a CSV file. Grade the
Markdown files only. A measured run on `documentation/APUpgradeSiteListSample.CSV` returned
exit code 2 and the message `only .md and .py files are graded`.

The index CSV gets check V5, V6, V7, and V8 instead of the writing gate. The CSV holds
document titles from the source PDF metadata. It holds no authored prose.

The plan adds the skill files to `.github/workflows/ste-lint.yml`. The workflow grades 2
files today, and its trigger covers `documentation/**/*.md` only. Without the change, SC-010
stays true at merge time but drifts later.

## 5. The gap register format

The gap register is a Markdown table in `references/corpus-operations.md`. It is not a
separate file, because the Five-Item Rule caps `references/` at 5 children.

| Column | Example | Purpose |
| - | - | - |
| `Document` | `virtual-chassis-ex-8200.pdf` | The file name of the document. |
| `Affected trains` | `25.2, 25.4, 26.2` | Each train where the file does not open. |
| `Reason` | `A zero run replaces the first 126,976 bytes. The page tree is gone.` | The measured cause. |
| `Fallback train` | `24.2` | The newest train with a readable copy. |
| `Risk to the reader` | `The answer can miss a change after train 24.2.` | The effect on an answer. |

The register holds 2 rows at delivery. Each row covers one document across 3 trains, which
gives 6 unreadable files in total. FR-045 and FR-046 require both rows.

| Document | Affected trains | Fallback train | Index gap flag |
| - | - | - | - |
| `virtual-chassis-ex-4200-4500.pdf` | 25.2, 25.4, 26.2 | 24.4 | `c` |
| `virtual-chassis-ex-8200.pdf` | 25.2, 25.4, 26.2 | 24.2 | `c` |

Neither document is in the index, because neither name matches a membership rule. The
register is corpus wide, not index wide. The skill states the gap when it cites either
document, as FR-047 requires.

FR-048 asks for the 3 documents that the conversion skipped. Measurement shows that the
`skipped` status does not mean a failure. All 3 files hold readable Markdown with a correct
page count. The register therefore records them in a second table with the state
`converted earlier`, and the plan records the correction in the deviation table below.

## 6. What stays outside the repository

The repository never receives these items.

| Item | Size | Where it stays |
| - | - | - |
| `markdown/` | 744 MB in 4,007 files | The corpus root |
| `extracted/` | 30,751 files, with 9,337 PDF files | The corpus root |
| `archives/` | 324 compressed originals | The corpus root |
| The provenance records | `manifest.json`, `selection-inventory.csv`, `extraction-report.json`, `corpus-catalog.csv`, `corpus-catalog.json`, and `markdown/_conversion-manifest.json` | The corpus root |
| The crawler and the catalog builder | Not measured | A temporary folder. The spec puts them out of scope. The procedures below replace them. |

The corpus root is a setting. The default value is
`C:\Users\jmorrison\Downloads\juniper-doc-archives`. `corpus-operations.md` states the setting
and how to change it. A `.gitignore` rule guards against an accidental commit.

### How a future reader rebuilds the index

The catalog builder is a throwaway script. The repository does not hold it, and it does not
need to. The converter is a different case, because `scripts/pdf_to_markdown.py` is committed
and section 7 covers it. `corpus-operations.md` therefore states the index procedure, and the
procedure needs no script. The input is the YAML front matter of each file under `markdown/`.

The front matter holds 7 fields at most. It holds `source_file` and `pages` in every file. It
holds `title`, `author`, `subject`, `creationDate`, and `modDate` when the PDF metadata gives
them. It holds no train and no security flag. The procedure below derives those two values
from the path and from the file name.

| Index column | Source | Derivation |
| - | - | - |
| `file` | The path of the Markdown file | The file name without the extension |
| `title` | The front matter field `title` | Cut to 70 characters. The build reads the file name when the field is absent, which happens in 12.2 percent of the files. |
| `pages` | The front matter field `pages` | Used without a change |
| `archive` | The path of the Markdown file | The parent directory, below `markdown/` |
| `train` | The name of the archive folder | `juniper-PDFs-junos-262` gives `26.2`. A folder with no train gives `-`. |
| `group` | The file name, then the title | The ordered keyword rule for the 8 sections |
| `origin` | The file name and the term list | `t` for a term match. `e` for a name in the checklist need list. `f` for the earlier security flag. |
| `gap` | The gap register | `c` or `s`, and `-` for every other row |

Steps:

1. Read the front matter of each file under `markdown/`. The corpus holds 4,006 files.
2. Count the characters of each file. Divide by `pages`. Drop a document below 200 characters
   for each page. A measured run drops 8 documents from the subset.
3. Apply the 3 membership rules. The result is 775 documents.
4. Assign one topic group to each document with the ordered keyword rule.
5. Build the archive code table. Order the codes by the row count of each directory.
6. Write the 8 columns in the fixed order, with LF line endings.
7. Run check V5 to V8. Record each new gap in the gap register.

The trains present after the deduplication are 21.1, 21.2, 21.3, 21.4, 22.1, 22.2, 23.2, 23.4,
24.2, 24.4, 25.2, 25.4, and 26.2.

### How a future reader rebuilds the corpus

A reader needs this procedure only when the corpus itself is gone.

1. Read `selection-inventory.csv` at the corpus root. It holds 378 archive rows. Each row
   gives the decision, the train, the size, the file name, and the download URL.
2. Download each archive from its URL. The Juniper documentation archive index page is the
   source when a URL fails.
3. Extract each archive. Keep the folder name, because the index archive code depends on it.
4. Convert each PDF to Markdown with `python scripts/pdf_to_markdown.py`. Section 7 states the
   required behavior of that command.
5. Rebuild the index with the procedure above.

A reader who has no corpus still gets an answer. The curated references carry the controls,
the commands, and the STIG rules. The skill then states that the source document is absent.

## 7. The committed converter

**Decision**: upgrade `scripts/pdf_to_markdown.py` so that the documented rebuild command
reproduces the staged corpus.

### Why

`.gitignore` lines 20 to 28 already promise this command to a reader. The comment states
`Rebuild the corpus with: python scripts/fetch_ssr_docs.py` and
`python scripts/pdf_to_markdown.py <downloaded.pdf>`. A promise that does not reproduce the
data is a defect. The repository convention also forbids a second implementation of the same
job, so a new converter under another name is not an option.

The alternative is to keep the script and state that a different converter produced the
corpus. That keeps the deliverable free of code. It also leaves the rebuild procedure unable
to reproduce the data, and it leaves the `.gitignore` promise false. The plan rejects it.

### The measured gap

| Behavior | The staged converter | `scripts/pdf_to_markdown.py` today | The upgraded script |
| - | - | - | - |
| Library | PyMuPDF 1.28.2, on one workstation | `pypdf`, which no requirements file declares | `pdfplumber` 0.11.10, which `pyproject.toml` declares |
| Output shape | YAML front matter, then the body | `# <stem>`, a `Source file:` line, then `## Page N` for each page | YAML front matter, then the body |
| Front matter | `source_file` and `pages` always. `title`, `author`, `subject`, `creationDate`, and `modDate` when the PDF metadata holds them. | None | The same rule |
| Headings | Detected from the font size | None. Each page gets one fixed heading. | Detected from the `size` key of each `char` object |
| Bullets | A glyph becomes a Markdown list item | Unchanged | A glyph becomes a list item |
| Running header and page number | Removed | Kept | Removed |
| Ligature and curly quotation mark | Normalized | Unchanged | Normalized |
| Throughput | 88.8 to 109.4 pages for each second | One file at a time, in one process | 18.0 to 21.6 pages for each second, across a worker pool |

A measurement of 400 staged files gives the field frequency of the front matter. `source_file`
and `pages` appear in 100 percent of the files. `creationDate` appears in 98.8 percent,
`modDate` in 98.5 percent, `title` in 87.8 percent, `author` in 68.0 percent, and `subject` in
11.2 percent. A PDF without an author gives no author. The contract therefore requires 2
fields always and 5 fields when the metadata holds them.

A flat page dump cannot satisfy FR-025 to FR-032. The upgrade therefore adds the front matter,
the heading detection, the glyph rules, the header removal, and the worker pool.

### Scope and rules

| Item | Rule |
| - | - |
| File | `scripts/pdf_to_markdown.py`, edited in place. No new module. |
| Class | Keep `PdfMarkdownConverter` and `PdfMarkdownCommand`. Add no wrapper function. |
| Five-Item Rule | 5 parameters, 5 blocks, and 25 lines for each method. Extract a helper when a method grows. |
| Inline comments | Every changed line carries a comment, from Principle VI. |
| Action logging | An `info` message before each action and a `debug` message after it, from Principle VII. |
| Workers | The worker count is a command-line option. The default is the processor count. |
| Test | `tests/test_pdf_to_markdown.py`, with a small PDF fixture. Coverage is 80 percent or more. |
| Dependency | `pdfplumber`, which `pyproject.toml` already declares. The script must not need an undeclared package, and it must not add PyMuPDF. |
| Rebuild | After the script passes its gates, the converter task rebuilds the corpus with it, so that one reader produces the whole corpus. |

### The library decision

**Decision: use `pdfplumber`. Do not add PyMuPDF to the repository.** Research Decision 15
holds the measurement and the reasons.

| Library | License | Font size access | Measured speed | Verdict |
| - | - | - | - | - |
| pdfplumber 0.11.10 | MIT, and `pyproject.toml` already declares it | Yes, through the `size` key of each `char` object | 18.0 to 21.6 pages for each second | Selected |
| PyMuPDF 1.28.2 | Dual Licensed, GNU Affero GPL 3.0 or an Artifex commercial license | Yes | 88.8 to 109.4 pages for each second | Rejected. The container image is a distribution. |
| pypdf 6.16.2 | BSD | No | Not measured | It cannot detect a heading. |

The selection adds no new dependency. It also removes the license risk, because
`.github/workflows/container-build.yml` sets `REGISTRY: ghcr.io` and `push: true`. A push to a
public registry is distribution, which is the condition that the AGPL acts on.

The cost is about 13 minutes. A full rebuild of 511,674 pages across 26 workers takes about
0.3 hours with `pdfplumber`, against about 5 minutes with PyMuPDF. A reader runs the rebuild
once.

### Two readers, one honest statement

The staged corpus came from PyMuPDF on one workstation. That use is local, it distributes
nothing, and it carries no license problem. It matches the way the repository generates
`data/ste_dictionary.json` locally and never commits it.

The committed converter uses `pdfplumber`. The two readers do not agree byte for byte. Check
V15 therefore tests the structural contract, not the bytes. When the converter lands, the
converter task rebuilds the corpus with `pdfplumber`, so that one reader produces all of it.

The rebuild can move a row across the quality floor, because a different reader gives a
different character count. A measurement of the character density shows 8 documents between
200 and 250 characters for each page, and 3 documents between 150 and 200. Up to 11 rows of
775 can move, which is 1.4 percent. The tasks phase measures the row count again after the
rebuild.

### Gates

The converter adds the 5 Python gates to the verification list. Check V14 gives the commands
for Ruff, Black, mypy, Bandit, and pytest. Check V15 proves that the output of 30 sample
documents satisfies the structural contract.

## Verified claims

A person ran each command on 2026-09-16 in the worktree at
`MistHelper-hardening-junos-skill`.

| Claim | Evidence command | Result |
| - | - | - |
| The corpus holds 4,007 converted Markdown files. | `(Get-ChildItem -Recurse -File -Filter *.md "<root>\markdown").Count` | `4007` |
| The conversion covered 511,674 pages. | Read `pages` in `markdown/_conversion-manifest.json` | `511674` |
| The conversion reports 4,004 converted and 3 skipped. | Read `status_counts` in the same file | `{'skipped': 3, 'converted': 4004}` |
| The deduplication skipped 5,330 duplicate copies. | Read `selection` in the same file | `duplicates_skipped: 5330` |
| A catalog of 4,006 rows exists at the corpus root. | `csv.DictReader` count of `corpus-catalog.csv` | `4006` rows and 9 columns |
| The catalog marks 718 documents as security relevant. | Count rows where `security` is `True` | `718` |
| The FR-007 term rule matches 734 file names. | Substring test of the 28 terms | `734` |
| The union of both rules gives 756 documents and 181.0 MB. | Union count and a sum of the `kb` column | `756` and `181.0 MB` |
| 8 selected documents fall below the character floor. | `chars / pages < 200` from the conversion manifest | `8` |
| The index holds 775 rows after the floor and the checklist need rule. | The full membership rule | `775` rows, 710 flag, 38 term, 27 checklist |
| The index costs 70.0 KB and needs 165 archive codes. | Write the rows to a buffer and measure the length | `70.0 KB` and `165` codes |
| An index of all 4,006 documents does not fit. | Measure the 9 column set and the slim column set | `1,202 KB` and `593 KB`, against a budget of 400 KB |
| The security subset fits in the budget. | Measure the 9 column set and the slim column set for 718 rows | `224 KB` and `111 KB` |
| The archive code saves 75.4 KB. | Measure the chosen column set with a full `markdown_path` | `145.4 KB` against `70.0 KB` |
| The cut of the title to 70 characters saves 0.6 KB. | Measure the chosen column set with a full title | `70.6 KB` against `70.0 KB` |
| LF line endings save 0.8 KB. | Measure the chosen column set with CRLF | `70.8 KB` against `70.0 KB` |
| The archive table costs 28.8 KB with the URL column. | Write the 165 rows as a Markdown table, with and without the URL | `11.1 KB` for 3 columns and `28.8 KB` for 4 columns |
| The path rule holds for every selected row. | Compare `markdown_path` against `markdown/` plus the PDF path | `0` failures |
| Only 48 index rows carry a Junos train. | Count rows where `train` is not empty | `48` of `775` |
| The STIG bundle holds 181 rules. | Count `Rule` elements in the 3 XCCDF files | `24` plus `55` plus `102` |
| The STIG severity split is 25 high, 122 medium, and 34 low. | Read the `severity` attribute of each rule | `{'high': 25, 'medium': 122, 'low': 34}` |
| The full STIG rule text is 485 KB. | Sum the title, check, and fix text length | `485.0 KB`, which is more than the whole budget |
| The checklist holds 8 sections. | `Select-String -Pattern '^## '` on the checklist | 8 numbered sections and 67 items |
| The existing skills score 96 or more on the STE linter. | `python -m tools.ste_linter --min-score 80` on 8 skill files | Scores from 96 to 99, exit code 0 |
| The STE linter rejects a CSV file. | Grade `documentation/APUpgradeSiteListSample.CSV` | Exit code 2, `unsupported_file_type` |
| `.github/skills/` holds 5 children today. | `Get-ChildItem .github/skills` | 5 folders |
| `managing-mist-api` holds 6 files and 143 KB. | `Get-ChildItem -Recurse -File` with a length sum | 1 router file and 5 reference files |
| The 2 corrupt documents have a readable fallback. | Read `corpus-catalog.csv` for both names | `24.4` and `24.2` |
| `documentation/references/` is ignored on purpose. | `git check-ignore -v documentation/references/hardening/hardening-junos-devices-checklist.md` | `.gitignore:28:documentation/references/` |
| No file below that path is committed. | `git ls-files documentation/references` | `0` files |
| A worktree does not receive the ignored path. | `Test-Path documentation\references` in this worktree | `False` |
| The distilled precedent is committed. | `git ls-files documentation/noc-runbooks` | `15` files |
| The runbooks cite a public URL, not a local path. | Read section 14 of `SSR_CONSOLE_HEALTH_CHECK.md` | A `Source` and `Where` table of 8 public URLs |
| `.gitignore` names the rebuild command. | Read `.gitignore` lines 20 to 28 | `python scripts/fetch_ssr_docs.py` and `python scripts/pdf_to_markdown.py <downloaded.pdf>` |
| The converter is committed. | `git ls-files scripts/pdf_to_markdown.py scripts/fetch_ssr_docs.py` | Both files are tracked |
| The committed converter writes a flat page dump. | Read `PdfMarkdownConverter._render` | It writes `# <stem>`, a `Source file:` line, and `## Page N` for each page. It writes no front matter. |
| The committed converter needs an undeclared package. | Read the module docstring and `pyproject.toml` | The docstring states `python -m pip install pypdf`. No requirements file declares it. |
| The staged corpus used PyMuPDF. | `importlib.metadata.version` for each library | `pymupdf 1.28.2`, `pypdf 6.16.2`, `pdfplumber 0.11.10` |
| PyMuPDF carries an AGPL license. | `importlib.metadata.metadata('pymupdf')['License']` | `Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License` |
| pdfplumber carries an MIT license. | Read the `License` classifier of the package metadata | `License :: OSI Approved :: MIT License` |
| The container workflow distributes the image. | Read `.github/workflows/container-build.yml` | `REGISTRY: ghcr.io` and `push: true` |
| `pyproject.toml` already declares pdfplumber. | Search `pyproject.toml` | `"pdfplumber>=0.11.0"` |
| pdfplumber gives the font size that the heading rule needs. | Read the `size` key of each `char` object across 12 pages of `pki.pdf` | The sizes `9.0, 10.0, 10.3, 11.0, 12.9, 14.0, 20.0, 26.0, 30.0`. **Superseded on 2026-09-16.** That 12 page sample gives a modal size of `9.0`, which is the front matter size. The whole 168 page document gives `10.0`, which is the body size. Research Decision 15 holds the correction. |
| pdfplumber is about 5 times slower. | Time both readers over the same 12 pages | `18.0` against `88.8` pages for each second. A second run gave `21.6` against `109.4`. |
| Only 2 front matter fields are always present. | Read the front matter of a 400 file sample | `source_file` and `pages` at 100 percent. `title` at 87.8 percent. `author` at 68.0 percent. `subject` at 11.2 percent. |
| Up to 11 index rows can move across the quality floor. | Band the character density of the selection | `8` documents between 200 and 250, and `3` between 150 and 200 |
| The staged conversion ran at about 1,612 pages for each second. | Divide `pages` by `seconds` in the conversion manifest | `511674 / 317.4`, across 26 workers |
| No test covers the converter today. | Search `tests/` for a converter test | `0` files, against 23 test files in the folder |
| 162 of the 165 archives have a public URL. | Join the archive list to `selection-inventory.csv` | `162` of `165`. The archive table costs 28.8 KB. |
| The repository runs 5 Python gates. | Read `documentation/quality-gates.md` | Ruff, Black, mypy, pytest with 80 percent coverage, and Bandit |

Total verified claims: 51.

## Deviations from the specification

The specification states counts from an earlier pass. Measurement on 2026-09-16 gives
different values. The plan keeps the specification intent and records the true number. The
tasks phase must update the specification counts or record an accepted variance.

| Item | Specification | Measured | Action |
| - | - | - | - |
| Security relevant documents | 757 (FR-019, SC-009) | 756 by the same union rule. The catalog holds 4,006 rows, because one document has no catalog row. | Use 775 index rows, which adds the 27 checklist need documents and removes 8 low quality documents. Record the change in the specification. |
| Security subset file count | 743 files and 181 MB | 756 files and 181.0 MB | Record the measured value. |
| Front matter fields | 8 fields, including `train`, `sha256`, `converter_version`, `converted_at`, and `status` (FR-025) | 7 fields, without those 5 | The index carries `train`, `pages`, and the gap flag. `corpus-operations.md` states the front matter contract for the next conversion run. A re-conversion of 4,007 files is out of scope. |
| Skipped documents | 3 documents that the conversion skipped (FR-048) | All 3 hold readable Markdown and a correct page count. The `skipped` status means that the output already existed. | Record all 3 in the gap register with the state `converted earlier`. |
| Fallback trains | Trains 21.1 to 24.4 hold a valid copy (FR-046) | The extraction report states 21.1 to 24.2 in one field and 21.1 to 24.4 in another. The catalog took one document from 24.2 and the other from 24.4. | Record the fallback train for each document, not one range for both. |
| Full STIG text | Each rule holds its check and its fix (SC-003) | The full text is 485 KB, which is more than the 400 KB budget | Ship a one-line check and a one-line fix for each rule. Point to the XCCDF file and the public DISA download for the full text. |
| The committed checklist | FR-011 and the dependency list name `documentation/references/hardening/hardening-junos-devices-checklist.md` as a committed file | The directory is ignored by `.gitignore` line 28, and `git ls-files` returns 0 files. The file exists on one workstation only. | Treat the checklist as vendor material at the corpus root. Cite the public URL and the corpus path. Never cite the ignored path. Update FR-011 in the specification. |
| The conversion script | The spec puts the conversion scripts out of scope and calls them temporary | `.gitignore` names `python scripts/pdf_to_markdown.py` as the rebuild command, and the script is committed | Upgrade the committed script. Section 7 states the scope and the gates. Update the out-of-scope list in the specification. |

## Risks and prerequisites

| Item | Effect | Action |
| - | - | - |
| The corpus is on one workstation. | A second user cannot open a cited document. | The skill states the corpus root setting and answers from the curated references. Check V11 proves the behavior. |
| The hardening book is from 2015. | A command can be old. | The author confirms each command against a train 26.2 document. The reference cites both. |
| The corpus is a snapshot. | A reader can believe that it describes the Juniper website today. | Each file states the snapshot date of 2026-09-16 and the source counts. |
| The title column comes from PDF metadata. | A title can be wrong. One measured title is `TO:`. | The index keeps the source title. `baseline-controls.md` gives the correct title in the citation. |
| The STIG bundle covers the EX switch. | A reader can apply a rule to an MX or SRX device without a test. | `stig-rules.md` states the platform limit in its first paragraph. |
| The converter upgrade adds Python code to the deliverable. | The 5 Python gates now apply, and the work grows. | Section 7 states the scope, the gates, and the library. The skill folder still holds documentation only. |
| The staged corpus and the committed converter use two different readers. | The output does not match byte for byte. | Check V15 tests the structural contract. The converter task rebuilds the corpus with `pdfplumber` after the gates pass. |
| A different reader gives a different character count. | A document can cross the 200 character floor in either direction. | A measurement finds 8 documents between 200 and 250, and 3 between 150 and 200. Up to 11 rows of 775 can move. The tasks phase measures the row count again after the rebuild. |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `.github/skills/` grows from 5 children to 6 children, which breaks the Five-Item Rule. | The agent runtime discovers a skill at `.github/skills/<name>/SKILL.md`. A skill must be a direct child of that folder. | A nested folder, such as `.github/skills/network/hardening-junos/`, hides the skill from discovery. A merge into `managing-mist-api` mixes two domains and breaks the 90 KB file limit. The remediation action is a separate issue that groups the 6 skills after the runtime supports a nested path. |
| The skill ships one CSV file, and the writing gate cannot grade it. | 775 rows in a Markdown table cost about 85 KB and approach the 90 KB file limit. The CSV costs 70.0 KB. | A Markdown table is larger and slower to parse. The CSV holds no authored prose, so checks V5 to V8 replace the writing gate for that file. |
| The feature folder `specs/2754-hardening-junos-skill/` holds 8 children. | The SpecKit template sets the layout. Every other feature folder in `specs/` uses the same names. | A nested folder breaks the SpecKit commands, which read `spec.md`, `plan.md`, and `tasks.md` at a fixed depth. This is established repository practice and grandfathered debt. |
