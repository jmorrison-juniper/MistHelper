# Release Body Contract

**Issue**: [#3431](https://github.com/jmorrison-juniper/MistHelper/issues/3431)

## Command

```text
python -m scripts.release_body
  --source <absolute-json-path>
  --output <absolute-markdown-path>
  --tag <current-tag>
  --repository <owner/repository>
  [--previous-tag <expected-base-ref>]
```

The runner must supply `GITHUB_EVENT_NAME=push`, `GITHUB_REF_TYPE=tag`, and the exact `GITHUB_REF=refs/tags/<tag>`.
`RUNNER_TEMP` must identify an existing controlled directory.
Both paths must remain inside that directory.
The paths must be distinct and contain no traversal or linked child components.
The output parent must already exist.

`ReleaseBodyCommand.run` returns zero only after final-file verification.
Required argument, input, reference, size, and file failures return two.
Unknown options produce a fixed argument error without repeating input values.

## Source

Require a JSON object with a nonempty string `body`.
Optional `name`, `repository`, `tag_name`, and `previous_tag_name` fields must be strings.
Reject duplicate fields, unsupported fields, invalid JSON, invalid UTF-8, and invalid Unicode.
Optional identity fields must match the release and comparison.
The title does not identify the release tag.

## References

Require one complete Full Changelog line.
Accept the plain, angle-bracket, and Markdown link forms.
Reject a missing, partial, duplicate, or conflicting required line.
Require HTTPS and the exact `github.com` authority without credentials, port, query, or fragment.
Require the expected repository, one three-dot range separator, and two valid decoded refs.
The current ref must match the current tag.
An explicit previous tag must match the comparison base.
Decode percent escapes once with strict UTF-8.
Reject traversal and malformed encodings.

Preserve the accepted comparison URL exactly.
Construct `https://github.com/<repository>/blob/<encoded-tag>/CHANGELOG.md`.
Do not invent a version-section anchor or guess a missing comparison.

## Complete Output

Full mode contains the complete source, unchanged.
If the source lacks a terminal LF, append one.
Then append one separator LF, the pinned footer, and one terminal LF.

The footer has this form:

```text
[CHANGELOG for `<tag>`](<pinned-CHANGELOG-URL>)
```

Summary mode contains these complete lines:

```text
## Release summary for `<tag>`

The full release body exceeds the publication size limit.
This summary replaces the generated list. It does not list every change.

**Full Changelog**: <original-validated-comparison>
[CHANGELOG for `<tag>`](<pinned-CHANGELOG-URL>)
```

The real summary includes the terminal LF.
It contains no partial change list or invented change claim.

## Measurement and Persistence

Count code points with `len(text)`.
Count UTF-16 units with `len(text.encode("utf-16-le", errors="strict")) // 2`.
Apply both measurements to the exact complete candidate.
Accept at most 124999 UTF-16 units and fewer than 125000 code points.
If the full candidate exceeds a limit, select the complete summary.
If the complete summary cannot fit, fail without shortening it.

Write strict UTF-8 to a secure temporary sibling.
Verify exact bytes before atomic replacement.
Verify exact bytes and final measurements again at the actual publisher path.
Detect incomplete writes and a missing final LF.
Remove only the command-owned temporary sibling during cleanup.
A cleanup failure retains a nonzero status.

## Observability

Report phases and actual checked counts.
An unreadable source reports zero checked files.
A readable invalid source reports one checked file.
Report both source, candidate, and final text measurements when available.
Do not log notes, tokens, raw arguments, raw responses, or original filesystem exception messages.

Caution: an existing output file does not authorize publication.
A failed command stops the workflow before the release action can read that file.
