# Data Model: Portal Run Evidence Isolation

## Operation run

An operation run remains the existing in-memory dictionary.
Its public response fields do not change.

### Existing public fields

| Field | Type | Rule |
| - | - | - |
| `run_id` | string | Unique portal run identifier |
| `status` | string | `pending`, `running`, `completed`, or `failed` |
| `log_messages` | bounded deque | Owner-thread user-facing records only |
| `debug_messages` | bounded deque | Owner-thread internal records only |
| `dropped_log_count` | integer | Discards from this run only |
| `output_files` | bounded deque | Unambiguous owned files or valid single-run fallback files |
| `dropped_output_file_count` | integer | Discards from this run only |
| `completion_message` | string or null | Success evidence or an honest no-output reason |

### New private field

| Field | Type | Rule |
| - | - | - |
| `_owner_thread_id` | integer | Set once in the worker before capture and removed or ignored after capture |

## Run log handler

| State | Type | Rule |
| - | - | - |
| `_run` | operation run | The only run that this handler can mutate |
| `_event_bus` | event bus or null | Publishes existing run-scoped payloads |
| `_owner_thread_id` | integer | Must equal `LogRecord.thread` before any evidence action |

### State transition

1. Create the handler in the worker thread.
2. Attach it to the root logger.
3. Ignore each foreign-thread record.
4. Route each owner-thread record through existing rules.
5. Remove the handler in `finally`.

## Output scanner

| State | Type | Rule |
| - | - | - |
| `_owner_thread_id` | integer | Stable owner for one scan lifetime |
| `_write_candidates` | set of paths | Paths opened by this owner |
| `_ambiguous_write_candidates` | set of paths | Paths tracked by more than one active owner |
| `_overlap_detected` | boolean | True after any concurrent scanner overlap |
| `_started_at` | integer nanoseconds | Existing filesystem-clock start mark |
| `_directory_marks` | map | Existing single-run fallback state |
| `_directory_entries` | map | Existing single-run fallback state |

### Class state

| State | Type | Rule |
| - | - | - |
| `_active_scanners` | map from thread identifier to scanner | At most one scanner per active owner |
| `_tracking_lock` | reentrant lock | Guards registry, ambiguity, and hook state |
| `_original_open` | callable | Exact `builtins.open` value before first install |
| `_original_path_open` | callable | Exact `Path.open` value before first install |
| `_hooks_installed` | boolean | True while at least one scanner is active |

## Ownership rules

1. A log record has one owner when its thread equals the handler owner.
2. A tracked write has one owner when the calling thread has one active scanner.
3. A tracked path is ambiguous when more than one active owner tracks it.
4. A timestamp-only path is ambiguous when a scanner had any overlap.
5. An ownerless event contributes no run evidence during overlap.
6. A single scanner can use the existing timestamp fallback.

## Validation rules

- Reject duplicate active scanner registration for one owner.
- Reject tracked attribution when the calling thread has no active scanner.
- Reject ambiguous paths from every affected scanner.
- Reject directory and full-walk fallback after overlap.
- Keep path containment, exclusion, runtime-file, timestamp, and cap checks unchanged.
- Restore hooks only when the active scanner map is empty.

## No schema changes

The feature adds no database table, migration, environment variable, or durable coordination record.
