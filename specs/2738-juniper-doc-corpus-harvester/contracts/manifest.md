# Contract: Manifest

The manifest is an operational artifact. `ManifestWriter` renders it from the SQLite
store to `data/juniper_corpus/manifest.json` and `data/juniper_corpus/manifest.csv`.
The manifest describes local files and run state. It is not collected Mist API data,
so it does not route through `DataExporter` (see research.md, section 10).

## Coverage rule

Every document in the inventory appears in the manifest with a final status. The
coverage is 100 percent (SC-004).

## JSON entry schema

```json
{
  "source_url": "https://www.juniper.net/documentation/us/en/software/...",
  "resolved_pdf_url": "https://www.juniper.net/documentation/us/en/software/....pdf",
  "category": "uncategorized",
  "sub_category": "srx__configuration__security",
  "local_path": "data/juniper_corpus/uncategorized/srx__configuration__security/....pdf",
  "file_size": 734003,
  "status": "classified",
  "chosen_pdf": "https://www.juniper.net/.../whole-document.pdf",
  "rejected_candidates": [
    "https://www.juniper.net/.../chapter-1.pdf",
    "https://www.juniper.net/.../chapter-2.pdf"
  ],
  "drop_reason": null
}
```

## Field rules

| Field | Type | Rule |
|-------|------|------|
| `source_url` | string | Always present. The sitemap URL. |
| `resolved_pdf_url` | string or null | Null for a `no PDF found` document. |
| `category` | string | One of the nine categories or `uncategorized` (FR-020). |
| `sub_category` | string or null | Present only when `category` is `uncategorized`. |
| `local_path` | string or null | Null until the file is downloaded. |
| `file_size` | integer or null | The byte count. Null until downloaded. |
| `status` | string | A final `HarvestStage`: `classified`, `failed`, or `dropped`. |
| `chosen_pdf` | string or null | The selected companion PDF URL (FR-010b). |
| `rejected_candidates` | array of string | Each rejected `.pdf` reference (FR-010b). |
| `drop_reason` | string or null | Present only for a dropped release note (FR-009). |

## Privacy rule

The manifest has no field for extracted body text. An audit of `manifest.json`,
`manifest.csv`, and the output tree finds only the label, the detected signal names,
and the numeric scores (FR-024, SC-005). The scores appear in the store; the manifest
carries the derived `sub_category` label.

## CSV form

The CSV holds one row per document. It flattens `rejected_candidates` into a single
semicolon-joined cell so a spreadsheet can open it. Every other column matches the
JSON field of the same name.

## Dropped release notes

Each dropped release note appears as a manifest entry with `status = dropped` and a
non-null `drop_reason`. The manifest therefore holds the full audit trail: kept
documents, failed documents, and dropped release notes (FR-028).
