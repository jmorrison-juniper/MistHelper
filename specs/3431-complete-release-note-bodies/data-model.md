# Data Model: Complete Release Note Bodies

This repair adds no database, retained application record, or uploaded artifact.
The command holds only transient release text and validated references.

## Release References

`ReleaseReferences` contains the repository, current tag, and optional previous tag.
The runner must identify `push`, `tag`, and the exact `refs/tags/<tag>` value.
The complete comparison supplies the previous ref when the caller omits it.
Both decoded refs must satisfy the conservative Git ref rules.

Resolution returns the original comparison URL, the pinned CHANGELOG URL, and the decoded previous ref.
The helper does not replace a URL with a different range.
The CHANGELOG destination uses the current tag rather than a moving branch.

## Generated Source

The source is a complete UTF-8 JSON object.
Its required `body` is a nonempty string.
Optional `name`, `repository`, `tag_name`, and `previous_tag_name` fields are strings.
Present identity fields must agree with the request and comparison.
The parser rejects duplicate keys and unsupported fields.
The title remains informational.

## Body and Measurements

The selected result contains the complete text and mode `full` or `summary`.
Each measurement is a typed pair of Unicode code points and UTF-16 units.
`ReleaseBody.measure` measures the same complete string under both rules.
`ReleaseBody.fits` requires both values below 125000.
The stricter UTF-16 bound prevents the action from changing the output.

Full mode preserves every generated character.
It adds only the required separator, pinned footer, and final LF.
Summary mode explains the size limit and contains both complete links.
No mode slices source text or a required reference.

## Files and Failures

Source and output are distinct absolute paths under the controlled runner directory.
The output parent must already exist.
Path validation rejects traversal and linked components before any write.
The command never deletes the source or an unrelated file.

The helper verifies temporary and final bytes against the selected text.
Only a verified final file permits status zero.
Required failures return status two.
An existing output can remain after failure, but workflow failure prevents publication.

## Checked Counts

The command counts a source file after a complete byte read.
An unreadable source reports zero checked files.
A readable invalid source reports one checked file.
JSON validation reports zero records before validation and one after success.
Comparison validation reports the number of complete comparison lines it examines.
Successful output verification reports two checked files: the temporary sibling and final path.

Logs report source, candidate, and final code-point and UTF-16 measurements.
Unavailable measurements do not claim success.
Fixed phase and failure messages contain no notes, tokens, or raw response bodies.
