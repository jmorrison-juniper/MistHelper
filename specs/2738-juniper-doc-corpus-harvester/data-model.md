# Phase 1 Data Model: Juniper Documentation Corpus Harvester

This document defines every entity, its fields, its validation rules, and its state
transitions. The privacy invariant is explicit: the content analysis record holds the
label, the detected signal names, and the numeric scores only. It holds no body text.

## 1. Enumerations

### HarvestStage

The stage of one document in the durable store. The stage drives the resume logic.

| Value | Meaning | Final |
|-------|---------|-------|
| `discovered` | The document is in the inventory. No PDF is resolved yet. | No |
| `resolved` | The companion PDF URL is known. | No |
| `downloaded` | The PDF file is on disk and starts with `%PDF`. | No |
| `classified` | The document has a category and, when needed, a sub-category. | Yes |
| `failed` | A per-document error stopped this document. The reason is recorded. | Yes |
| `dropped` | A superseded release note. The reason is recorded. | Yes |

A repeated run reprocesses a document only when its stage is not final, that is, when
the stage is `discovered`, `resolved`, or `downloaded`, or when the stage is `failed`
and the operator requests a retry.

### DocumentType

| Value | Meaning |
|-------|---------|
| `html_root` | An HTML document root that owns one companion PDF. |
| `direct_pdf` | A sitemap entry that already names a `.pdf` file. |

## 2. Dataclasses (in `src/juniper_docs/models.py`)

### ReleaseNoteKey (promoted, reused unchanged)

Identifies the train that one release note belongs to.

| Field | Type | Rule |
|-------|------|------|
| `product` | `str` | The product family segment of the root. Not empty. |
| `major` | `int` | The major version number, such as 23 in 23.4R1. |

### InventoryRecord

One document in the plan, before download.

| Field | Type | Rule |
|-------|------|------|
| `source_url` | `str` | The sitemap URL. Absolute. Unique in the inventory. |
| `root_slug` | `str` | The normalized document root path. Not empty. |
| `doc_type` | `DocumentType` | `html_root` or `direct_pdf`. |

**Validation**: The builder removes a URL that appears in more than one child sitemap
(FR-004). The builder maps a `/topics/` chapter URL to its parent root, so each
document appears once (FR-003).

### PdfCandidate

One `.pdf` reference found during resolution.

| Field | Type | Rule |
|-------|------|------|
| `url` | `str` | Absolute PDF URL. |
| `chosen` | `bool` | True for the selected companion PDF. |
| `reason` | `str` | The selection or rejection reason, such as `name-match`, `same-folder-first`, `largest`, or `rejected`. |

**Validation**: Exactly one candidate per document has `chosen = True`, unless the
document reaches `failed` with a `no PDF found` reason (FR-012).

### ContentAnalysisResult

The derived metadata for one uncategorized document. This record holds no body text.

| Field | Type | Rule |
|-------|------|------|
| `sub_category` | `str` | The human-readable label, or the fixed fallback `unclassified-content`. Not empty. |
| `detected_signals` | `tuple[str, ...]` | The names of the signals that scored above zero. May be empty for the fallback. |
| `scores` | `dict[str, float]` | A map from signal name to a numeric score. Empty for the fallback. |
| `is_fallback` | `bool` | True when no signal reached the confidence threshold or no text was readable. |

**Privacy invariant (FR-024, SC-005)**: This dataclass has no field for the extracted
text. The sampler returns the text as a local string. The scorer reads that string,
builds this result, and the string then goes out of scope. No layer writes the text to
disk, to the store, or to the manifest.

### ManifestEntry

The joined view of one document for the manifest render.

| Field | Type | Source |
|-------|------|--------|
| `source_url` | `str` | InventoryRecord |
| `resolved_pdf_url` | `str \| None` | Resolution |
| `category` | `str` | SlugClassifier |
| `sub_category` | `str \| None` | ContentAnalysisResult, when the category is `uncategorized` |
| `local_path` | `str \| None` | Download |
| `file_size` | `int \| None` | Download |
| `status` | `HarvestStage` | State store |
| `chosen_pdf` | `str \| None` | Resolution |
| `rejected_candidates` | `list[str]` | Resolution |
| `drop_reason` | `str \| None` | Release-note filter |

## 3. SQLite schema (in `src/juniper_docs/harvest/state_store.py`)

The store is the single source of truth. The manifest renders from these tables.

### Table `documents`

One row per document. The primary key is the natural business key `root_url`.

| Column | Type | Notes |
|--------|------|-------|
| `root_url` | TEXT PRIMARY KEY | The document root URL. |
| `doc_type` | TEXT NOT NULL | `html_root` or `direct_pdf`. |
| `stage` | TEXT NOT NULL | A `HarvestStage` value. |
| `resolved_pdf_url` | TEXT | Null until `resolved`. |
| `category` | TEXT | Null until `classified`. |
| `sub_category` | TEXT | Null unless the category is `uncategorized`. |
| `is_fallback` | INTEGER | 0 or 1. Null until analyzed. |
| `local_path` | TEXT | Null until `downloaded`. |
| `file_size` | INTEGER | Byte count. Null until `downloaded`. |
| `error_reason` | TEXT | Set when `stage = failed`. |
| `updated_at` | TEXT NOT NULL | UTC ISO timestamp of the last change. |

### Table `pdf_candidates`

The chosen and rejected candidates for a document with more than one PDF reference.

| Column | Type | Notes |
|--------|------|-------|
| `root_url` | TEXT NOT NULL | Foreign key to `documents.root_url`. |
| `url` | TEXT NOT NULL | The candidate URL. |
| `chosen` | INTEGER NOT NULL | 0 or 1. |
| `reason` | TEXT NOT NULL | Selection or rejection reason. |

### Table `content_scores`

The numeric scores for an uncategorized document. This table holds no body text.

| Column | Type | Notes |
|--------|------|-------|
| `root_url` | TEXT NOT NULL | Foreign key to `documents.root_url`. |
| `signal_group` | TEXT NOT NULL | `product_family`, `task_type`, or `technology_domain`. |
| `signal_name` | TEXT NOT NULL | The detected signal name. |
| `score` | REAL NOT NULL | The numeric score. |

### Table `dropped_release_notes`

Each release note that the filter dropped, with the reason (FR-009).

| Column | Type | Notes |
|--------|------|-------|
| `root_url` | TEXT PRIMARY KEY | The dropped release-note root. |
| `reason` | TEXT NOT NULL | For example `superseded-by-newer-train-member`. |

### Table `run_meta`

One row that records the schema version and the run totals for the summary.

| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT PRIMARY KEY | For example `schema_version` or `started_at`. |
| `value` | TEXT NOT NULL | The value. |

## 4. State transitions

```text
discovered ──resolve──> resolved ──download──> downloaded ──classify──> classified (final)
     │                      │                       │
     │                      │                       └──error──> failed (final)
     │                      └──no PDF found───────────────────> failed (final)
     │                      └──error──────────────────────────> failed (final)
     └──release-note filter──> dropped (final)
     └──error────────────────> failed (final)
```

**Durability rule (FR-033)**: The tool writes the PDF bytes to disk first. The tool
then updates the row to `downloaded` inside one transaction and commits. The tool
reads the row back to verify the commit. Only then does the tool count the document as
downloaded. The tool never reports a document complete until the file and the row are
both durable.

**Resume rule (FR-034)**: On start, the runner queries `documents` for any row whose
stage is not final. The runner continues each such document from its current stage. A
completed document is not re-downloaded (SC-003).

## 5. Output tree

```text
data/juniper_corpus/
├── harvest_state.db                 # The SQLite store (source of truth)
├── manifest.json                    # Rendered manifest (machine format)
├── manifest.csv                     # Rendered manifest (spreadsheet format)
├── release-notes/                   # Slug category folder
├── configuration-guides/
├── administration-guides/
├── installation-guides/
├── cli-reference/
├── api/
├── security-and-compliance/
├── migration/
├── design/
└── uncategorized/                   # Slug category with content sub-category folders
    ├── srx__configuration__security/
    ├── mx__monitoring__telemetry/
    └── unclassified-content/        # The fixed fallback sub-category
```

Every folder name and file name is Windows-safe. Every path is built with
`pathlib.Path` (FR-029, FR-030).
