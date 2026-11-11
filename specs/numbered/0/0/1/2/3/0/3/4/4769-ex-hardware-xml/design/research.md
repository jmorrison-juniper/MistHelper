# Research: Native EX Hardware Collection

**Feature**: [spec.md](../spec.md)
**Updated**: 2026-11-11 for issue #4770.

## Fixed Native Commands

XML selection runs this command once per currently online EX switch:

```text
show chassis hardware detail | display xml | no-more
```

JSON selection runs this separate command once:

```text
show chassis hardware detail | display json | no-more
```

BOTH runs XML, then JSON, with separate captures and completion checks.
The user explicitly requires native JSON rather than XML conversion.

## Official Evidence

- The [chassis hardware reference](https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/show-chassis-hardware.html) identifies `show chassis hardware detail` as a view-privilege operational command.
- The [output filtering guide](https://www.juniper.net/documentation/us/en/software/junos/cli/topics/topic-map/filtering-operational-command.html) documents native `display xml`, native `display json`, and the pagination-prevention filter `no-more`.

## Observed Runtime Evidence

An authorized online-target probe received an initial banner and prompt in three frames.
Both native commands accepted the final `| no-more`.
The XML reply ended with a routing-engine marker, `{master:0}`, before the final CLI prompt.
The previous parser included that marker in the XML document and rejected the result as malformed.
The native JSON response contained a top-level `chassis-inventory` array.
A subsequent current Mist statistics read returned `connected` for two targets.
Further live shell tests must repeat this status check first.

## Current Status and Readiness

Read complete SDK `listSiteDevicesStats` pages rather than trusting device inventory for online status.
Only explicit `connected` status permits a target.
Preview excludes offline and unknown devices with separate counts.
Dispatch repeats the uncached status read before opening a shell.
A failed status read is unknown, and it cannot dispatch a command.

The collector requires a complete CLI prompt and a quiet interval.
It rejects banners, XML tags, and partial command echoes as prompts.
Each native command has a fresh bounded capture.
The next command cannot start until the previous command returns to the same prompt.

## Native Output Validation

Remove only verified terminal framing, command echo, and the recognized routing-engine marker.
Parse XML without DTD or entity declarations.
Require native JSON to contain a nonempty `chassis-inventory` array with chassis content.
Preserve native document text rather than serializing parsed JSON again.
Reject secret-bearing output instead of saving a modified document.
Inspect parsed credential fields and values instead of applying generic log path redaction to native documents.

## Proven Artifact Validation Failure

The deployed production batch collector captured complete native documents through the verified prompt.
The validator rejected both formats because the generic log redactor matched legitimate slash-containing hardware text and namespace URLs.
The supplied transcript independently matched the filesystem-path rule in two XML descriptions and the native JSON.
Anonymized regression fixtures reproduced both failures before the repair.

The candidate validator ran in a separate diagnostic process without changing container files or portal workers.
The production collector sent XML, then JSON, to one target with fresh `connected` status checks.
The artifact writer saved 6,079 XML bytes and 13,584 JSON bytes.
Both saved files matched their native captures and passed independent XML and JSON parsing.
The completed manifest reported durable storage and no partial outcome.
This evidence does not replace acceptance of the redeployed portal.

## Independent Failures and Durable Files

Stage and publish each successful format separately.
A malformed native reply fails that format without removing another successful file.
If completion is unproven, stop further commands and retain previous successful files.
The manifest records target states and separate format states.

Hardware files and partial manifests remain under a unique `data/websocket-streams/<run_id>` directory.
Session expiry and restart cleanup must not delete these durable directories.
Existing run and per-file quotas remain in force. A new run cannot overwrite a previous run.
After session expiry, the mounted data directory provides filesystem access.
