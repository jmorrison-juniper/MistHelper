# Contract: Release Artifacts

This contract defines the outputs that the owner publishes and verifies. The owner creates them. The release workflow creates the assets and the image (RC-23 to RC-28).

## Tag

- The name is the letter `v` plus the release stamp.
- The tag is an annotated tag object.
- The tag targets the release merge commit on `main`. It does not target the current `main` head at the time of the push.
- The release workflow runs for a tag that matches `v*.*.*` (RC-23).
- No tag with the same name exists before the push (RC-04).

## Release Title

- The title has three parts: the tag, a space, a hyphen, and a space, then a summary.
- The summary has 12 words or fewer.
- The owner writes the summary. The agent does not write it.

## Release Body

- The generated notes come from `scripts/release_body.py` (RC-38).
- The body keeps the compare link line that names the previous and the new release.
- The body keeps the CHANGELOG link line that names `CHANGELOG.md` at the tag (RC-38, line 91).
- When the full body exceeds 125,000 code points, the script writes the summary form instead (RC-39). The owner keeps that form.

## Assets

The release holds exactly three assets.

| Asset | Name rule | Source |
| - | - | - |
| Wheel | The package name `misthelper`, the package version `2.1.0`, and the wheel tags for any Python 3 build | `pyproject.toml` version at line 3 (RC-41). The release workflow attaches the wheel (RC-28). |
| Source archive | The package name `misthelper`, the package version `2.1.0`, and the suffix `.tar.gz` | The same package version (RC-41). |
| Standalone ZIP | The word `misthelper`, a hyphen, the release stamp, and the suffix `.zip` | The workflow derives the stamp from the tag (RC-25). |

## Container Image

- The repository is `ghcr.io/jmorrison-juniper/misthelper`.
- The tags are the release stamp and `latest` (RC-26).
- The stamp tag and the `latest` tag share one manifest digest. This is the acceptance rule of FR-012, and it is not a verified fact.
- The revision label `org.opencontainers.image.revision` equals the release merge commit SHA.
- The version label `org.opencontainers.image.version` is recorded as observed. The Containerfile sets `2.1.0` (RC-42). The label source after the build is unverified (U-3).
- The workflow pushes by default (RC-53).

## Ordering

- A merge to `main` dispatches the container build before the tag exists (RC-31 and RC-30).
- The release build runs after the tag push and moves `latest` again.
- The owner checks the final state of `latest` after the release build.
