# Complete Release Notes

MistHelper prepares each release body before the release action reads it.
Fitting releases keep every generated character and the original change order.
Oversized releases use a labeled summary instead of a partial change list.
Both modes contain the complete comparison and a CHANGELOG reference at the current tag.

## Body Limit

`softprops/action-gh-release@v3` applies `input.substring(0, 125000 - 1)` to every supplied body.
It applies this operation even when `generate_release_notes` is false.
JavaScript counts UTF-16 units, not Python Unicode code points.

The helper measures the complete candidate, including both links and the final newline.
It accepts at most **124999 UTF-16 units**.
This bound also guarantees fewer than **125000 Unicode code points**.
A character outside the Basic Multilingual Plane uses two UTF-16 units.
UTF-8 byte length does not replace either text measurement.

| Complete candidate in UTF-16 units | Output |
|---:|---|
| 124998 | Complete generated notes |
| 124999 | Complete generated notes |
| 125000 | Complete summary |
| 125001 | Complete summary |

Full mode preserves whitespace, Unicode, and line endings.
If the source lacks a final LF, the helper adds one.
It adds a blank line and the complete CHANGELOG footer.
Summary mode states that size limits prevent inclusion of the generated list.
It does not invent change claims or extract a partial list.
If the summary cannot fit, preparation fails without shortening a line or link.

## Required References

The generated source must contain one complete `Full Changelog` line.
The helper accepts plain, angle-bracket, and Markdown link forms.
It validates HTTPS, the exact `github.com` authority, the repository, and both decoded refs.
The current ref must match the release tag.
If `--previous-tag` is supplied, the comparison base must match it.
Missing, duplicate, conflicting, malformed, or misleading required links cause failure.
The helper does not guess an initial-release comparison.

The CHANGELOG destination is `https://github.com/<repository>/blob/<encoded-tag>/CHANGELOG.md`.
This link identifies the file at the release tag.
The helper does not use a moving branch or invent a heading anchor.

## Publication Source

The existing `publish` job checks out the exact tag before it downloads artifacts.
A later checkout can remove downloaded artifacts during cleanup.
The job prepares notes with Python 3.13 and the standard library.

Generation uses the read-only `POST /repos/{owner}/{repo}/releases/generate-notes` endpoint.
The step stores the complete response in `${{ runner.temp }}/generated-release-notes.json`.
Only the generation step receives `GH_TOKEN` through the existing job token.
It does not create a release, draft, tag, or uploaded artifact.
API errors remain visible, and failed requests stop the job.

`python -m scripts.release_body` writes `${{ runner.temp }}/release-body.md`.
The action reads that exact file through `body_path`.
The action uses `generate_release_notes: false` without another body source.
Required generation, preparation, or verification failure prevents publication.
Existing tag events, build jobs, dependencies, permissions, downloads, and artifact entries remain unchanged.

## Input and File Safety

The command requires `--source`, `--output`, `--tag`, and `--repository`.
It accepts optional `--previous-tag`.
This internal guard rejects help-only and incomplete invocations instead of reporting unverified success.
The runner must identify the exact tag-push event.
`RUNNER_TEMP` must identify an existing controlled directory.
Source and output paths must be absolute, distinct, and inside that directory.
The helper rejects traversal, linked paths, directory outputs, and unavailable output parents.

The source must contain a JSON object with a nonempty string `body`.
Optional identity fields must agree with the release and comparison.
Invalid JSON, duplicate fields, unreadable files, invalid UTF-8, and invalid Unicode cause failure.

The helper writes a secure temporary sibling.
It verifies exact UTF-8 bytes before and after atomic replacement.
It measures the actual final file before it returns status zero.
Required failures return status two.

Caution: an existing output file does not authorize publication.
A failed preparation can leave an old output, but the job stops before the publisher.

Logs report phases, mode, checked counts, source measurements, candidate measurements, and final measurements.
An unreadable source reports zero checked files.
A readable but invalid source reports one checked file.
Logs do not contain tokens, note contents, or raw response bodies.

## Offline Validation

Use the existing Python 3.13+ development environment.
Run these commands from the repository root:

```bash
rtk proxy python -m pytest tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py --cov=scripts.release_body --cov-branch --cov-report=term-missing --cov-fail-under=90
rtk proxy python -m ruff check scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py
rtk proxy python -m black --check scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py
rtk proxy python -m mypy --config-file pyproject.toml scripts/release_body.py
rtk proxy python -m bandit scripts/release_body.py
rtk proxy test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

The tests measure complete output at the exact boundaries and preserve both final links.
They cover the 216840-character source, astral Unicode, invalid inputs, file failures, and checked counts.
Workflow mutations prove the consumed source, output path, disabled generation, and fatal preparation policy.
The tests do not execute the release workflow or require a network connection.
The [issue validation guide](../specs/3431-complete-release-note-bodies/quickstart.md) lists the remaining checks.

Caution: do not publish a release, draft, tag, upload, or workflow dispatch to validate this repair.
