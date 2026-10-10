# Contract: Portal Run Evidence Isolation

## Purpose

This contract defines which evidence can enter one portal operation run.

## Log evidence

1. The operation worker owns one stable thread identifier.
2. A handler accepts a record only when `LogRecord.thread` equals that identifier.
3. A rejected record does not change logs, counts, output files, or events.
4. An accepted record uses the existing main-log and debug-log routing.
5. Each published log event keeps the existing `run_id` payload.

## File evidence

1. A tracked write belongs to the scanner for the calling owner thread.
2. A thread without an active scanner cannot create tracked evidence.
3. A path tracked by two active owners is ambiguous.
4. An ambiguous path appears in neither run.
5. A scanner that overlaps another scanner cannot use timestamp fallback.
6. A scanner that never overlaps retains directory-mark and full-walk fallback.
7. Existing path containment, exclusion, runtime-file, and timestamp rules still apply.

## Completion evidence

1. A run succeeds with one or more approved output files.
2. A run can also succeed with an existing valid no-output reason.
3. A foreign or ambiguous file cannot satisfy completion.
4. Existing preview ordering applies only after ownership filtering.

## Concurrency

1. Independent menu operations continue in separate pool workers.
2. The implementation adds no global operation lock.
3. The file hooks can serve multiple active scanners.
4. One scanner can stop without disabling tracking for another scanner.
5. The final scanner restores the exact pre-capture hook values.

## Public compatibility

The following response and event fields remain unchanged:

- `run_id`
- `log_messages`
- `debug_messages`
- `dropped_log_count`
- `output_files`
- `dropped_output_file_count`
- `completion_message`
- `status`
- `progress_pct`

No public owner identifier is added.

## Failure behavior

- Ignore a foreign log record.
- Ignore an ownerless tracked write.
- Reject a path with multiple owners.
- Reject timestamp evidence after overlap.
- Continue cleanup after an operation exception.
- Fail the run when no approved output and no valid no-output reason exist.
