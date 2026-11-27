# Data Model: Release Publication

Each entity lists its natural key, its attributes, its states, and its constraints. The source of each rule is named by its research row.

## ReleaseStamp

- **Natural key**: `value`, the text `YY.MM.DD.HH.MM` in UTC.
- **Attributes**: `value`, `date` (the UTC date in `YYYY-MM-DD`), and `tag` (the letter `v` plus `value`).
- **Constraints**: The value has five two-digit segments. It sorts after `26.11.21.06.27` (RC-02). No tag matches it when T003 runs (RC-04).
- **Derivation**: Quickstart Scenario 2 derives the value from the UTC clock.

## ReleaseTag

- **Natural key**: The tag name, which is the letter `v` plus the release stamp.
- **Target**: One commit, the release merge commit. The tag is an annotated tag object.
- **Constraints**: The name matches the trigger pattern `v*.*.*` of `release.yml` (RC-23). The name is unique among tags.
- **States**: `absent` (before OWN-001), `pushed` (after the owner pushes it), `peeled` (the remote shows the commit that the tag names).

## Fragment

- **Natural key**: The file name in `changelog.d/`. The forms appear in `changelog.d/README.md` lines 24 to 28 (RC-44).
- **Attributes**: `name`, `heading` (one line that starts with a number sign), `bullets` (one or more lines that start with a hyphen and a space), and `state`.
- **Constraints**: Each fragment has a heading and at least one bullet. The guard test checks both (RC-35 context). Fragment names are unique.
- **States on `main`**: `on-main` (present), `collected` (copied into the release section on the release branch), and `deleted` (removed on the release branch, so absent on `main` after the merge).
- **States for an open pull request**: `open-pr` (the fragment exists only on a pull request branch, for example `pr-4208.md`). An `open-pr` fragment is outside the release until it reaches `main`.

## Entry

- **Natural key**: The source fragment name.
- **Attributes**: `heading` (exactly three number signs), `source` (the fragment name), `order` (the position in ordinal name order), and `body` (the bullet lines, with link rewrites only).
- **Constraints**: The count of entries equals the count of collected fragments. The count equals the number in the section introduction (contract `changelog-section.md`).

## ReleaseSection

- **Natural key**: The release stamp in the heading.
- **Attributes**: `heading` (two number signs with the stamp and the UTC date), `introduction` (the collected count and the previous release tag `v26.11.21.06.27`), and `entries` (the ordered list of Entry records).
- **Position**: After the blank line at line 14 and before the `26.09.28.19.49` heading (RC-09 and RC-10).

## ReleasePullRequest

- **Natural key**: The pull request number. GitHub assigns it at T-PR.
- **Attributes**: `head` (`release/4756-release-publication`), `base` (`main`), `title` (the Conventional Commits title), `labels` (`chore` and `docs`, then `auto-merge` at T-MERGE), `checks` (the 15 required contexts), and `state`.
- **States**: `held` (the owner hold on PR 4208 is open), `open`, `checks-green`, `labeled`, and `merged` (one squash commit).
- **Constraints**: `main` requires strict up-to-date checks and linear history (RC-22). Only one release pull request holds the serial slot at a time (D-9).

## ReleaseMergeCommit

- **Natural key**: The commit SHA on `main` that the squash merge creates.
- **Attributes**: `sha`, `parent` (the commit at `main` before the merge), and `title` (the pull request title).
- **Relationship**: The release tag targets this commit (OWN-001). The OCI revision label must equal this SHA (FR-012).

## ReleaseAsset

- **Natural key**: The asset name.
- **Set of three**: One wheel named with the package version `2.1.0`. One source archive named with the package version `2.1.0`. One ZIP named with the word `misthelper`, a hyphen, the release stamp, and `.zip`.
- **Source**: `release.yml` derives the ZIP name from the tag (RC-25), and it attaches the globs (RC-28). The previous release shows the same naming pattern (RC-03).

## ContainerImageTag

- **Natural key**: The image reference, which is the repository `ghcr.io/jmorrison-juniper/misthelper` with a tag.
- **Tags**: The release stamp and `latest`.
- **Attributes**: `digest` (the manifest digest) and `labels` (the revision label and the version label).
- **States**: `none`, `pushed-by-merge-build` (the automatic stamp and `latest`, RC-30 and RC-31), and `pushed-by-release-build` (the release stamp and `latest`, RC-26). The release build moves `latest` last.
- **Constraints**: Both tags must share one digest (FR-012). The expected equal digest is an acceptance criterion, not a verified fact.

## OwnerHold

- **Natural key**: The pull request number.
- **Items**: 4741, 4701, 4659, 4619, 4617, 4615, 4607, 4605, 4547, 4493, 4404, 4358, 4322, and 4208 (owner comment 1).
- **States**: `merged` for 13 items (RC-17 context) and `open` for PR 4208 (RC-19).
- **Transition**: An item that merges or closes releases its part of the hold. The hold ends when PR 4208 merges or closes (D-6).

## Relationships

- A ReleaseSection holds one or more Entry records. Each Entry copies one collected Fragment.
- A ReleasePullRequest produces one ReleaseMergeCommit. A ReleaseTag targets that commit.
- A ReleaseTag starts the release workflow. The workflow produces the ReleaseAsset set and the ContainerImageTag pair.
- An OwnerHold item blocks the ReleasePullRequest until the item merges or closes.
