# Skill factory data model

## Purpose

This data model defines the entities that the Juniper skill factory persists.
The canonical database is SQLite at `data\juniper_skills\factory.db`.

The factory MUST persist enough state to resume after a crash. A crash MUST lose
no more than one source document of progress.

## Entity relationship summary

```text
SourceDocument 1--many PartSet
SourceDocument 1--many Document
DomainSkill 1--many Document
Document 1--many Topic
Topic 1--many Card
Card many--many Citation
SourceDocument 1--many Citation
WorkItem references one SourceDocument, Document, Topic, or DomainSkill
```

## `SourceDocument`

A `SourceDocument` represents one logical Juniper source document from the
catalog. A split source still has one `SourceDocument` row.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `source_id` | string | yes | Primary key in `source_documents`. |
| `catalog_file` | string | yes | Catalog `file` value. |
| `title` | string | yes | Catalog or frontmatter title. |
| `category` | string | yes | Harvester category. |
| `pages` | integer | yes | Catalog page count. |
| `kb` | real | yes | Catalog size in KB. |
| `parts` | integer | yes | Catalog part count. |
| `markdown_path` | string | yes | Path under the harvest root. |
| `source_pdf` | string | yes | Path under the PDF root when known. |
| `source_file` | string | no | Shared source file from frontmatter. |
| `domain_name` | string | yes | Assigned `DomainSkill.name`. |
| `matched_rule` | string | yes | Domain rule that assigned the source. |
| `matched_signal` | string | yes | Signal text that matched the rule. |
| `content_hash` | string | yes | Hash of all source parts. |
| `created_at` | string | yes | ISO 8601 date-time. |
| `updated_at` | string | yes | ISO 8601 date-time. |

Relationships:

- One `SourceDocument` has one or more `PartSet` rows.
- One `SourceDocument` can produce one or more generated `Document` rows.
- One `SourceDocument` owns one or more `Citation` rows.

## `PartSet`

A `PartSet` represents one physical Markdown part of a logical source document.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `part_id` | string | yes | Primary key in `part_sets`. |
| `source_id` | string | yes | Foreign key to `source_documents`. |
| `part_index` | integer | yes | Order within the source document. |
| `markdown_path` | string | yes | Markdown file path under the harvest root. |
| `source_file` | string | no | Frontmatter source file value. |
| `slug_suffix` | string | no | Split suffix such as `-2` or a hash. |
| `pages` | integer | no | Page count for this part when known. |
| `content_hash` | string | yes | Hash of this part. |
| `segment_status` | enum | yes | `pending`, `done`, `failed`, or `skipped`. |

Relationships:

- Each `PartSet` belongs to one `SourceDocument`.
- The segmenter reads `PartSet` rows in `part_index` order.

## `DomainSkill`

A `DomainSkill` represents one generated `juniper-<domain>` skill package.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `domain_name` | string | yes | Primary key in `domain_skills`. |
| `display_title` | string | yes | Human-readable title for headings. |
| `description` | string | yes | Skill frontmatter description. |
| `document_count` | integer | yes | Count of assigned source documents. |
| `topic_count` | integer | yes | Count of generated topics. |
| `source_pages` | integer | yes | Total source pages in the domain. |
| `fallback` | boolean | yes | True only for `juniper-general-reference`. |
| `coverage_status` | enum | yes | `covered`, `gap`, or `unmeasured`. |
| `package_path` | string | yes | Canonical store path. |
| `built_at` | string | no | ISO 8601 date-time for the last build. |

Relationships:

- One `DomainSkill` owns many generated `Document` rows.
- One `DomainSkill` owns domain coverage gap rows.

## `Document`

A `Document` represents one generated document directory inside a domain skill.
It usually maps to one `SourceDocument`.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `document_id` | string | yes | Primary key in `documents`. |
| `source_id` | string | yes | Foreign key to `source_documents`. |
| `domain_name` | string | yes | Foreign key to `domain_skills`. |
| `document_slug` | string | yes | Directory name under `documents`. |
| `title` | string | yes | Generated document title. |
| `index_path` | string | yes | Path to level 2 `INDEX.md`. |
| `topic_count` | integer | yes | Count of topic files. |
| `day0_count` | integer | yes | Count of topics tagged `day0`. |
| `day1_count` | integer | yes | Count of topics tagged `day1`. |
| `day2_count` | integer | yes | Count of topics tagged `day2`. |
| `day2plus_count` | integer | yes | Count of topics tagged `day2plus`. |
| `build_status` | enum | yes | `pending`, `done`, `failed`, or `skipped`. |

Relationships:

- One `Document` belongs to one `DomainSkill`.
- One `Document` comes from one `SourceDocument`.
- One `Document` owns many `Topic` rows.

## `Topic`

A `Topic` represents one generated topic file.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `topic_id` | string | yes | Primary key in `topics`. |
| `document_id` | string | yes | Foreign key to `documents`. |
| `domain_name` | string | yes | Foreign key to `domain_skills`. |
| `topic_slug` | string | yes | File slug without number prefix. |
| `topic_title` | string | yes | Frontmatter `topic` value. |
| `topic_path` | string | yes | Path to generated topic file. |
| `lifecycle_tags` | string | yes | JSON array of life cycle tags. |
| `source_ranges` | string | yes | JSON array of source page or section ranges. |
| `routing_keywords` | string | yes | JSON array of routing keywords. |
| `byte_size` | integer | yes | Generated file size in bytes. |
| `ste_score` | real | no | STE linter score when measured. |
| `similarity_max_run` | integer | no | Longest shared prose run. |
| `build_status` | enum | yes | `pending`, `done`, `failed`, or `skipped`. |

Relationships:

- One `Topic` belongs to one `Document`.
- One `Topic` owns many `Card` rows.
- One `Topic` can use many `Citation` rows.

## `Card`

A `Card` represents one knowledge card in a topic file.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `card_id` | string | yes | Primary key in `cards`. |
| `topic_id` | string | yes | Foreign key to `topics`. |
| `class_mark` | enum | yes | `MUST`, `SHOULD`, or `INFO`. |
| `card_text` | string | yes | Restated fact without citation brackets. |
| `citation_keys` | string | yes | JSON array of citation keys. |
| `source_quote_hash` | string | no | Hash of the source range used for rewrite checks. |
| `similarity_run` | integer | no | Longest shared prose run for this card. |
| `sort_order` | integer | yes | Order in the topic file. |

Relationships:

- One `Card` belongs to one `Topic`.
- One `Card` references one or more `Citation` rows.

## `Citation`

A `Citation` represents one source reference used by generated cards.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `citation_id` | string | yes | Primary key in `citations`. |
| `source_id` | string | yes | Foreign key to `source_documents`. |
| `domain_name` | string | yes | Foreign key to `domain_skills`. |
| `document_id` | string | no | Foreign key to `documents`. |
| `key` | string | yes | Citation key without brackets. |
| `source_range` | string | yes | Page, section, table, or figure range. |
| `source_path` | string | yes | Source Markdown path. |
| `source_line_start` | integer | no | First source line when known. |
| `source_line_end` | integer | no | Last source line when known. |
| `source_url` | string | no | Public source URL when known. |

Relationships:

- One `Citation` belongs to one `SourceDocument`.
- Many `Card` rows can reference one `Citation`.

## `WorkItem`

A `WorkItem` represents one resumable unit of factory work.

| Field | Type | Required | Persistence |
| - | - | - | - |
| `work_item_id` | string | yes | Primary key in `work_items`. |
| `work_type` | enum | yes | `inventory`, `segment`, `rewrite`, `validate`, `publish`, or `report`. |
| `target_type` | enum | yes | `source`, `domain`, `document`, `topic`, or `package`. |
| `target_id` | string | yes | Primary key of the target entity. |
| `status` | enum | yes | `pending`, `in_progress`, `done`, `failed`, or `blocked`. |
| `attempts` | integer | yes | Number of attempts. |
| `last_error` | string | no | Last error message with no secret data. |
| `locked_by` | string | no | Agent or process that owns active work. |
| `locked_at` | string | no | ISO 8601 date-time. |
| `created_at` | string | yes | ISO 8601 date-time. |
| `updated_at` | string | yes | ISO 8601 date-time. |

Relationships:

- A `WorkItem` references one target entity by `target_type` and `target_id`.
- The orchestrator uses `WorkItem` rows to resume after a crash.

## Persistence rules

1. The factory MUST write all entities to `data\juniper_skills\factory.db`.
2. The factory MUST use transactions for each source document.
3. The factory MUST commit a transaction after each source document finishes.
4. The factory MUST set a work item to `in_progress` before it writes output.
5. The factory MUST set a work item to `done` only after validation passes.
6. The factory MUST store errors without tokens, passwords, or source prose.
7. The factory MUST use stable primary keys derived from source IDs and slugs.
8. The factory MUST not store generated state only in memory.

## Suggested indexes

The SQLite database SHOULD define these indexes.

| Table | Index fields | Reason |
| - | - | - |
| `source_documents` | `domain_name`, `category` | Domain reports query these fields. |
| `part_sets` | `source_id`, `part_index` | The segmenter reads parts in order. |
| `documents` | `domain_name`, `document_slug` | The builder finds package paths. |
| `topics` | `document_id`, `topic_slug` | The validator resolves topic paths. |
| `cards` | `topic_id`, `sort_order` | The writer preserves card order. |
| `citations` | `source_id`, `key` | The validator resolves citations. |
| `work_items` | `status`, `work_type` | The orchestrator finds ready work. |

## Resume rule

When the factory starts, it MUST read `work_items`. It MUST return stale
`in_progress` rows to `pending` when the lock owner is gone. It MUST then run
pending work in dependency order.

Warning: do not treat missing database rows as completed work. Missing rows can
make the factory skip documents and publish an incomplete skill package.
