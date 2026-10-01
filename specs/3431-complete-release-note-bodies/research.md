# Research: Complete Release Note Bodies

## Publisher Limit

The inspected [action source](https://github.com/softprops/action-gh-release/blob/v3/src/github.ts) calls `truncateReleaseNotes` for every supplied body.
This operation also applies when automatic generation is false.
It returns `input.substring(0, 125000 - 1)`.
JavaScript counts UTF-16 units, while Python counts Unicode code points.
Therefore the exact final body must contain at most 124999 UTF-16 units.

Disabling generation alone does not repair the defect.
Measuring only the source ignores the appended footer.
UTF-8 byte length does not establish the action's string length.
Slicing any complete body violates the required policy.

## Actual Long-Gap Source

A read-only generate-notes request returned 216840 characters for `v26.05.21.19.37...v26.09.26.06.19`.
The source contains 1439 pull request entries and ends with the complete Full Changelog comparison.
The local revised helper produced a complete 401-character summary.
The summary contains both required links and the terminal LF.
No release, draft, tag, or uploaded artifact was created.

## Source and References

The [generate-notes endpoint](https://docs.github.com/en/rest/releases/releases#generate-release-notes-content-for-a-release) returns a suggested name and complete body.
It does not save the generated notes or create a release.
The existing publish token permission supports this request.
No reusable release-body helper exists in the inspected pinned devtools tree.

The complete comparison supplies the previous ref.
Validate its parsed components and decode refs once.
Do not guess the latest release or a missing comparison.
Keep the original validated URL in both modes.

The CHANGELOG headings use more than one version format.
A tag-pinned file link avoids an invalid guessed heading anchor.
The destination is `https://github.com/<repository>/blob/<encoded-tag>/CHANGELOG.md`.

## Output Policy

Keep every generated character when the complete candidate fits.
Otherwise, publish a labeled summary with a size-limit explanation and complete links.
Do not infer change claims or retain a partial change list.
Reject a summary that cannot fit.

Binary UTF-8 writes and reads preserve original line endings.
Verify a secure temporary sibling before replacement and the actual output afterward.
A failed command blocks publication even if an old file remains.

## Focused Implementation

The first implementation introduced an unnecessary nested validation and audit framework.
The revision keeps five semantic owners and direct checked-count logs.
It keeps the required source, reference, size, path, and output guards.
It uses the existing workflow failure boundary instead of another publication authorization system.

The workflow contract uses the existing YAML parser and bounded command inspection.
It does not implement another YAML engine or evaluate shell text.
Negative mutations prove that required failure handling and measured body ownership cannot regress.
