# Implementation Plan: Complete Release Note Bodies

**Branch**: `jmorrison-juniper-complete-release-note-bodies`

**Issue**: [#3431](https://github.com/jmorrison-juniper/MistHelper/issues/3431)

**Spec**: [spec.md](spec.md)

## Summary

Keep complete generated notes when the final body fits.
Otherwise, use a labeled, complete summary with both required links.
Measure the complete final text and the actual UTF-8 output file.
Never slice a body or shorten a link.

The action cuts every supplied body at 124999 UTF-16 units.
Disabling automatic generation alone does not remove this operation.
The helper accepts at most 124999 units and fewer than 125000 code points.

## Technical Context

Use Python 3.13 and the standard library.
Use existing pytest, pytest-cov, and PyYAML for offline tests.
Add no dependency or runtime service.
Store one generated JSON response and one verified Markdown file under `RUNNER_TEMP`.
Verify a temporary sibling before atomic replacement and verify the final path afterward.

The inspected source base is `92a31012577fd3fa8089c901660656b457d1fa14`.
Only the existing publish job changes.
All other jobs, events, permissions, artifact lists, and required statuses remain unchanged.

## Constitution Check

Use semantic classes without standalone delegation wrappers.
Keep methods within five parameters and 25 lines.
Use explicit input validation and ASCII action logs.
Do not log tokens, notes, or raw API responses.

The required script, test, and documentation locations enter existing directories with more than five children.
This file placement is a scope exception.
Do not restructure unrelated directories or amend the constitution.
Use concise purpose comments for non-obvious logic.
This repair follows the approved file scope without an unrelated directory restructure.
It does not claim full compliance with every general placement or comment provision.
No shared rule, exclusion, baseline, threshold, or suppression changes.

## Design Revision

The first implementation used a large nested validation and audit framework.
The revised implementation removes that framework.
The revision keeps every requirement from issue #3431 and the required guard evidence.
It uses specific exceptions, direct measurements, and the existing workflow failure boundary.
A failed command never authorizes an existing output file.

## Class Ownership

| Class | Responsibility |
|---|---|
| `ReleaseBodyError` | Report fixed validation reasons without input contents. |
| `ReleaseReferences` | Validate the repository, tag event, decoded refs, comparison, and pinned CHANGELOG destination. |
| `ReleaseNotesSource` | Read complete bytes, validate JSON, and check optional source metadata. |
| `ReleaseBody` | Measure complete text, select a complete body, and verify the actual output file. |
| `ReleaseBodyCommand` | Parse fixed arguments, validate controlled paths, report checked counts, and return the command status. |

## Interfaces

The command is `python -m scripts.release_body`.
It requires `--source`, `--output`, `--tag`, and `--repository`.
It accepts optional `--previous-tag`.
The tag event and `RUNNER_TEMP` supply the existing runner context.
The command returns zero only after final-file verification.
Required failures return two.

The source must contain a nonempty string `body`.
Its single complete Full Changelog line supplies the previous ref.
The comparison must match the repository and current tag.
Both output modes retain that exact URL.
The CHANGELOG link names the file at the encoded current tag without an invented anchor.

## Workflow Integration

Check out the exact tag before artifact downloads.
Set up Python 3.13 without installing dependencies.
Capture the complete read-only generate-notes response in the runner temporary directory.
Prepare the body from that exact input.
Set `body_path` to that exact output and `generate_release_notes` to false.
Keep API errors visible.
Required failures stop the job before publication.

## Validation

Tests measure complete output at 124998, 124999, 125000, and 125001 units.
Tests cover the 216840-character source, astral Unicode, complete links, and final line endings.
Negative tests prove input, reference, output, and workflow failures with checked counts.
Run the existing compile, lint, format, type, security, coverage, link, STE, and test-quality checks.
Do not publish or dispatch a release to validate this repair.

The [validation guide](quickstart.md) lists exact commands.
The [body contract](contracts/release-body.md) and [workflow contract](contracts/workflow.md) define accepted behavior.
The [tasks](tasks.md) record implementation and validation evidence.

## Delivery Boundary

Work only in this isolated app worktree.
Commit locally after validation.
Wait at queue position 11 until the parent supplies a full verified base.
Then rebase, repeat validation, push once, and create the templated pull request.
Wait for every required check, the title check, CodeQL, and the strict base.
Use a protected exact-head squash without an admin bypass or branch deletion.
Verify the exact merged main tree locally.
