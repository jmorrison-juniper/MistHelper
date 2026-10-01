# Release Workflow Contract

The contract reads `.github/workflows/release.yml`.
It does not execute shell commands or publish a release.

## Existing Boundary

Keep only `push` with `tags: ['v*.*.*']`.
Keep the existing absence of a concurrency block.
Keep the five existing jobs and the publish dependencies.
Keep permissions, build behavior, artifact downloads, and release artifact entries unchanged.
Do not change another workflow or a required status.

## Publish Order

1. Check out the exact tag before downloads.
2. Set up Python 3.13 without a dependency install.
3. Download the existing Python artifacts.
4. Download the existing standalone bundle.
5. Generate the complete source JSON.
6. Prepare the complete measured body.
7. Publish only that measured file.

Generation uses the fixed read-only `gh api --method POST` generate-notes endpoint.
Supply the tag as a quoted environment value through `--raw-field`.
Capture the complete response at `${RUNNER_TEMP}/generated-release-notes.json`.
Keep API failures visible and return a failing step status.
Only generation receives the existing job token.

Preparation consumes that exact source through `python -m scripts.release_body`.
It writes `${RUNNER_TEMP}/release-body.md`.
The publisher consumes `${{ runner.temp }}/release-body.md` through `body_path`.
The publisher must use `generate_release_notes: false`.
It must not supply an inline body or append generated notes.

Required generation and preparation cannot skip, continue after failure, or mask a failing status.
No later writer can replace the verified body.
An existing file never substitutes for successful preparation.

## Offline Proof

Use the existing safe YAML parser.
Normalize its Boolean interpretation of the unquoted `on` key.
Fail on unreadable input, malformed YAML, or a non-mapping document.
Inspect actual job and step mappings.
Inspect the consumed helper arguments with `shlex`, without shell execution.
Check the exact bounded generation command and its failure branch.

Mutation tests must fail for another source, output, helper, generation policy, or failure override.
They must fail for reordered steps and changed tag-only execution.
The positive test reads the actual workflow from this worktree.
The read operation reports its actual checked file count.
The policy operation reports its actual job, step, and publisher counts.

The final difference must also prove that all four non-publish job mappings remain unchanged.
No real release, draft, tag, upload, or workflow dispatch belongs to this proof.
