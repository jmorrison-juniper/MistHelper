# Contract: State Store and Durability

The state store is a single SQLite database at `data/juniper_corpus/harvest_state.db`.
The store is the single source of truth for the run. This contract defines the schema,
the durability rules, and the fail-closed behavior.

## Schema (DDL)

```sql
CREATE TABLE IF NOT EXISTS documents (
    root_url          TEXT PRIMARY KEY,   -- Natural business key
    doc_type          TEXT NOT NULL,      -- html_root | direct_pdf
    stage             TEXT NOT NULL,      -- discovered|resolved|downloaded|classified|failed|dropped
    resolved_pdf_url  TEXT,               -- Null until resolved
    category          TEXT,               -- Null until classified
    sub_category      TEXT,               -- Null unless category is uncategorized
    is_fallback       INTEGER,            -- 0 or 1, null until analyzed
    local_path        TEXT,               -- Null until downloaded
    file_size         INTEGER,            -- Byte count, null until downloaded
    error_reason      TEXT,               -- Set when stage = failed
    updated_at        TEXT NOT NULL       -- UTC ISO timestamp
);

CREATE TABLE IF NOT EXISTS pdf_candidates (
    root_url  TEXT NOT NULL,              -- FK to documents.root_url
    url       TEXT NOT NULL,              -- Candidate PDF URL
    chosen    INTEGER NOT NULL,           -- 0 or 1
    reason    TEXT NOT NULL               -- name-match|same-folder-first|largest|rejected
);

CREATE TABLE IF NOT EXISTS content_scores (
    root_url      TEXT NOT NULL,          -- FK to documents.root_url
    signal_group  TEXT NOT NULL,          -- product_family|task_type|technology_domain
    signal_name   TEXT NOT NULL,          -- Detected signal name
    score         REAL NOT NULL           -- Numeric score, never any body text
);

CREATE TABLE IF NOT EXISTS dropped_release_notes (
    root_url  TEXT PRIMARY KEY,           -- Dropped release-note root
    reason    TEXT NOT NULL               -- Reason for the drop
);

CREATE TABLE IF NOT EXISTS run_meta (
    key    TEXT PRIMARY KEY,              -- schema_version | started_at | ...
    value  TEXT NOT NULL                  -- The value
);
```

The `content_scores` table has no text column by design. The store never holds the
extracted body text (FR-024, SC-005).

## Connection settings

| Pragma | Value | Reason |
|--------|-------|--------|
| `journal_mode` | `WAL` | A crash-safe write and safe concurrent reads. |
| `synchronous` | `FULL` | The commit reaches durable storage before it returns. |
| `foreign_keys` | `ON` | The child tables reference `documents`. |

## Durability rules

1. **File before state.** The tool writes the PDF bytes to disk first. The tool then
   sets `stage = downloaded` in one transaction and commits (FR-033).
2. **Verified write.** After the commit, the tool reads the row back and confirms the
   stage before it counts the document complete.
3. **No false complete.** The tool never reports a document complete until the file
   and the row are both durable.
4. **Single transaction per change.** Each stage change is one transaction, so an
   interrupted write leaves the row at its earlier stage, not a half state.

## Fail-closed behavior

| Condition | Behavior |
|-----------|----------|
| The database file is locked. | The tool retries a bounded number of times, then stops and reports the lock. It reports no progress it cannot confirm. |
| The database file is damaged. | The tool stops and reports the corruption. The operator restores from `harvest_state.db.bak` or starts a cold run. |
| The disk is full or the folder is read-only. | The tool records the failure for the current document and stops in a clean state. |

## Backup, recovery, and retention

- **Backup.** Before a schema migration, the tool copies the database file to
  `harvest_state.db.bak`.
- **Recovery.** After a crash, the WAL file replays on the next open. A partial PDF
  file is not marked complete, so the next run downloads it again.
- **Retention.** The store persists across runs. The operator deletes the
  `data/juniper_corpus/` tree to force a full cold run.

## Resume query

```sql
-- Documents the next run must still process
SELECT root_url, stage FROM documents
WHERE stage IN ('discovered', 'resolved', 'downloaded')
   OR (stage = 'failed' AND :retry_failed = 1);
```

The runner continues each returned document from its current stage. A `classified` or
`dropped` document is never reprocessed (FR-034, SC-003).
