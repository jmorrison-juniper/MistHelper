# Canonical files in the Juniper corpus

The harvester stores one new payload for each SHA256 digest within a corpus.
Different URLs, names, or categories can refer to that payload.
Each source URL keeps its own record in the state and both manifests.

## Find a document

Read `manifest.json` or `manifest.csv` in the corpus directory.
Use `local_path` to open the document.
Do not construct a file path from its category and original name.
A shared file can reside in another source record's category.

| Field | Meaning |
| - | - |
| `source_url` | The original inventory URL and natural document key. |
| `resolved_pdf_url` | The selected PDF URL for this source. |
| `original_pdf_name` | The original basename of that PDF URL. |
| `content_sha256` | The full digest of the stored original bytes. |
| `local_path` | The canonical file that this source record uses. |
| `category`, `sub_category` | The independent classification for this source. |
| `chosen_pdf`, `rejected_candidates` | The original resolution history. |
| `file_size`, `status`, `error_reason` | The byte count and recorded operation outcome. |

The fields extend the existing manifest format.
The manifest still contains one entry for each source URL.
The harvester does not create pointer PDFs, symbolic links, or converted copies.
It keeps the original payload bytes and the existing `%PDF` response check.

## Understand the counts

`downloaded` means that the operation published a new complete physical payload.
`skipped` means that the operation reused a verified canonical payload.
A new URL still requires a response fetch before the harvester can compare its bytes.
That reuse prevents another disk write, not the preceding transfer.

An existing valid URL association can skip the response fetch.
This rule also applies to an alias after a restart.
The summary's `total_bytes` counts each recorded canonical path once.
It does not measure all historical files that remain in the directory.

## Resume and verify files

The allocator discovers corpus paths once for each lifetime.
It stores hash metadata in the existing `harvest_state.db`.
On restart, it checks the real corpus root, path, size, device, inode, modification time, and change time.
An unchanged identity permits reuse without another full stored-file hash.
On Windows, the tool uses the native file change clock, not creation time.
An unavailable change clock causes an explicit failure.

The allocator reads new or changed files in blocks of at most 1 MiB.
It does not hash the full corpus for each download.
The existing HTTP client still holds one response body in memory.
The metadata cache does not hold document bodies.

A missing or changed canonical file cannot produce a successful resume skip.
The runner checks classified records before it accepts their files.
It restores a verified payload or records an explicit failure.
Successful recovery repairs every alias of that digest.

Caution: a cache, database, or file verification failure stops successful completion.
Read the reported error before you repeat the operation.
The harvester does not disable required metadata writes.
An interrupted `.part` file never counts as a complete payload.

## State migration and path operations

Schema version 2 preserves the natural source URL keys and all existing records.
It adds nullable digest/name fields and a path-keyed metadata cache.
Before migration, the store creates a SQLite backup that includes committed WAL data.
It retains an existing backup and chooses another backup name when necessary.
An unknown schema version fails without migration.

The first canonical payload can enter its classification folder.
Later aliases do not move it to match another category.
Reclassification can update each alias's label while it keeps the shared path.
Manual sorting moves a shared payload once and updates every affected source path.
Its default dry run writes nothing.

## Historical limits

This repair prevents new duplicate writes.
It does not delete, rename, or consolidate historical corpus files.
It does not prove removal of the 351 copies or recovery of the reported 1.32 GB.
Those measurements require authorized access to the original corpus.
Issue [#2977](https://github.com/jmorrison-juniper/MistHelper/issues/2977) remains open for that acceptance.

PDF usability validation belongs to issue [#3024](https://github.com/jmorrison-juniper/MistHelper/issues/3024).
This repair changes neither the crawl sources nor the parser dependencies.
