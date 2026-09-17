# Contract: The gap register

**File**: The `Gap register` section of
`.github/skills/hardening-junos/references/corpus-operations.md`

**Consumers**: The agent that cites a document. The engineer who refreshes the corpus.

**Date**: 2026-09-16

## Why the register is a section and not a file

The Five-Item Rule caps `references/` at 5 children. The folder already holds the 5 files that
the routing table needs. The register is 2 KB, so a section is enough.

## Table 1: Unreadable documents

| Column | Type | Rule |
| - | - | - |
| `Document` | Text | The file name of the source PDF. |
| `Affected trains` | List | Each train where the file does not open. |
| `Reason` | Text | The measured cause. 2 sentences or less. |
| `Fallback train` | Text | The newest train with a readable copy. |
| `Risk to the reader` | Text | The effect on an answer. |

Delivered rows:

| Document | Affected trains | Reason | Fallback train | Risk to the reader |
| - | - | - | - | - |
| `virtual-chassis-ex-4200-4500.pdf` | 25.2, 25.4, 26.2 | Juniper publishes the file with a zero run of 1,048,576 bytes. The page tree is gone. | 24.4 | An answer can miss a change after train 24.4. |
| `virtual-chassis-ex-8200.pdf` | 25.2, 25.4, 26.2 | Juniper publishes the file with a zero run of 126,976 bytes. The page tree is gone. | 24.2 | An answer can miss a change after train 24.2. |

Two documents fail in 3 trains each, which gives 6 unreadable files. FR-045 and FR-046 require
both rows.

Evidence: `extraction-report.json` holds the field `corrupt_pdfs_in_juniper_source` and the
field `corrupt_pdf_resolution`. The ZIP file passes its CRC check, so the damage is not a
download fault. The live Juniper site serves the same damaged bytes.

## Table 2: Documents with an earlier conversion

| Column | Type | Rule |
| - | - | - |
| `Document` | Text | The file name of the source PDF. |
| `State` | Text | `converted earlier`. |
| `Evidence` | Text | The Markdown size and the page count in the front matter. |
| `Risk to the reader` | Text | The effect on an answer. |

Delivered rows:

| Document | State | Evidence | Risk to the reader |
| - | - | - | - |
| `AWS_vSRX_Cookbook22.pdf` | converted earlier | 224,947 bytes, 132 pages | The manifest reports `pages: 0`. A reader who trusts the manifest alone believes that the file is missing. |
| `2001701 ... DoDIN APL Approval Memo DTR9.pdf` | converted earlier | 5,617 bytes, 2 pages | The same manifest effect. The PDF metadata title is `TO:`, which is not a real title. |
| `_source-archives-index.pdf` | converted earlier | 60,284 bytes | The file is an index of archives, not a Juniper manual. It is not in the index. |

FR-048 requires a record for all 3. Decision 8 in `research.md` gives the measured cause.

## Rules

| # | Rule | Source |
| - | - | - |
| R1 | The register lists each document that the skill cannot read from its newest train. | FR-043 |
| R2 | Each row holds the 5 fields of Table 1. | FR-044 |
| R3 | The skill states the gap and the fallback train when it cites a listed document. | FR-047 |
| R4 | A refresh adds a row for each new failure. | FR-043 |
| R5 | A row leaves the register only when a later train gives a readable copy. | FR-038 |
| R6 | A listed document that is also in the index carries the `gap` flag `c` or `s`. | This contract |

Neither corrupt document is in the index today. Neither file name matches a membership rule.
The register is corpus wide, and the index is subset wide.

## Refresh behavior

1. Convert the new train.
2. Compare the status of each document against the register.
3. Add a row when a document fails in the new train.
4. Update the `Fallback train` value when the fallback changes.
5. Remove a row when the new train gives a readable copy. Record the removal in the release
   note.

## Non-goals

- The register holds no repair procedure. The 2 corrupt documents are not repairable. The
  extraction report records 5 failed repair attempts.
- The register holds no copy of the document text.
