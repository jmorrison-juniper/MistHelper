# Contract: The corpus index

**File**: `.github/skills/hardening-junos/references/corpus-index.csv`

**Consumers**: The agent that reads the skill. A person who searches the corpus.

**Date**: 2026-09-16

## Format

| Property | Value |
| - | - |
| Format | CSV, from RFC 4180 |
| Encoding | UTF-8 without a byte order mark |
| Line ending | LF. CRLF adds 1 byte for each row, which is 0.8 KB. |
| Separator | A comma |
| Quotation | A double quotation mark, only when a field holds a comma or a quotation mark |
| Header | One header row with the 8 column names |
| Data rows | 78, measured against the shipped index. |
| Size | 6.9 KB measured. The budget is 85 KB. |



## Correction on 2026-09-16

The old contract required exactly 775 data rows. The shipped index holds 78 data rows at
6.9 KB. The old rule matched each file name against the term list across all 4,006 converted
documents. It returned 738 rows, but only 43 rows named a Junos train, which is 6 percent.

The shipped rule selects the Junos device archive first, then selects each security document.
The corpus holds 315 unique Junos device documents after deduplication. Of those documents,
78 carry a security subject. The shipped index holds 46 train rows, which is 59 percent.
All 8 topic groups hold at least one row.

The 14 index checks pass with the new count. One check proves that each row resolves to both
a Markdown file and a source PDF. Keep every invariant except the old I1 count.

## Regeneration input

The catalog builder is a throwaway script. The repository does not hold it. A reader rebuilds
the file from the YAML front matter of each document under `markdown2/`. The PDF conversion
uses the committed `scripts/pdf_to_markdown.py`. The rebuilt corpus writes to `markdown2/`.

| Front matter field | Present | Index column |
| - | - | - |
| `source_file` | 100 percent | It confirms the `file` value. |
| `pages` | 100 percent | `pages` |
| `creationDate` | 98.8 percent | Not used |
| `modDate` | 98.5 percent | Not used |
| `title` | 87.8 percent | `title`, cut to 70 characters |
| `author` | 68.0 percent | Not used |
| `subject` | 11.2 percent | Not used |
| `train` | Absent | Derived from the name of the archive folder |
| `status`, `sha256`, `converter_version`, `converted_at` | Absent | Derived from the conversion manifest |

A measurement of a 400 file sample gives each percentage. A PDF without a title gives no
title, so a build must read the file name when the `title` field is absent.

The plan holds the full procedure in the section `How a future reader rebuilds the index`.

## Columns

The order of the columns is fixed.

```text
file,title,group,train,pages,archive,origin,gap
```

| # | Column | Type | Allowed values | Example |
| - | - | - | - | - |
| 1 | `file` | Text | 1 to 80 characters. No path separator. No extension. | `user-access` |
| 2 | `title` | Text | 0 to 70 characters | `Junos OS User Access and Authentication User Guide` |
| 3 | `group` | Text | `G1` to `G8` | `G6` |
| 4 | `train` | Text | A train such as `26.2`, or `-` | `26.2` |
| 5 | `pages` | Integer | 1 or more | `1154` |
| 6 | `archive` | Text | `A001` to `A165` | `A006` |
| 7 | `origin` | Text | `f`, `t`, or `e` | `t` |
| 8 | `gap` | Text | `-`, `c`, or `s` | `-` |

### The `origin` values

| Value | Meaning | Rows |
| - | - | - |
| `f` | The corpus catalog marks the document as security relevant. | 710 |
| `t` | The file name holds one of the 28 terms in FR-007. | 38 |
| `e` | A checklist section needs the document. The term rule misses it. | 27 |

### The `gap` values

| Value | Meaning |
| - | - |
| `-` | No gap. |
| `c` | A newer train holds a corrupt copy. The gap register gives the fallback train. |
| `s` | The conversion run reported `skipped`, because the output already existed. |

## Path rule

A reader builds both paths from the row and the archive code table.

```text
PDF path      = <directory of archive> + "/" + <file> + ".pdf"
Markdown path = "markdown2/" + <directory of archive> + "/" + <file> + ".md"
```

Both paths are relative to the corpus root. A test of this rule against all 78 selected rows
gave 0 failures.

Example:

```text
Row:      user-access,Junos OS User Access and Authentication User Guide,G6,26.2,1154,A006,t,-
A006:     extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262
PDF:      extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/user-access.pdf
Markdown: markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/user-access.md
```

## The archive table

The table lives in `references/corpus-operations.md`. It holds 165 rows and costs 28.8 KB.

| Column | Type | Example |
| - | - | - |
| `code` | Text | `A006` |
| `directory` | Text | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262` |
| `train` | Text | `26.2` |
| `url` | Text | `https://www.juniper.net/documentation/en_US/...` |

Rules:

- Each `archive` value in the index must exist in the table.
- Each directory is relative to the corpus root.
- The table holds no absolute path.
- The table holds no path below `documentation/references/`. `.gitignore` line 28 ignores that
  directory, so a clone does not hold it.
- The `url` column holds the public download URL of the archive. A measured run fills 162 of
  the 165 rows. A row without a URL holds `-`.

## Invariants

The tasks phase must prove each invariant. `quickstart.md` gives the command.

| # | Invariant | Source |
| - | - | - |
| I1 | The file holds 78 data rows and 8 columns. | FR-019 |
| I2 | Each `file` value is unique. | FR-036 |
| I3 | No field holds an absolute path, a drive letter, or a leading slash. | FR-017 |
| I4 | Each `group` value is one of `G1` to `G8`. | FR-021 |
| I5 | Each `archive` value exists in the archive table. | This contract |
| I6 | Each `pages` value equals the page count in the conversion manifest. | FR-026 |
| I7 | Each indexed document gives 200 characters or more for each page. | FR-027 |
| I8 | Each row resolves to a Markdown file when the corpus is present. | SC-006 |
| I9 | Each of the 8 groups holds at least 1 row. | FR-021 |
| I10 | The file is 90 KB or less. | FR-006 |
| I11 | No field names a path below `documentation/references/`. | `.gitignore` line 28 |

## Change rules

- A refresh rebuilds the file. A refresh does not edit a single row by hand.
- A refresh keeps the column order.
- A new train adds no new row when the document name already exists. It updates the `train`
  value of the existing row.
- A removed document keeps its row until the refresh proves that the corpus no longer holds
  it.

## Non-goals

- The index holds no summary, no abstract, and no extract of the document text.
- The index holds no URL.
- The index holds no file hash. The next conversion run adds a hash to the front matter.
