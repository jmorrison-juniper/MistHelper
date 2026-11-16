# Dependency record model

## Requested update

Each update has an issue, original pull request, package name, requested version, and original revision.
The specification is the authority for the issue mapping.
The research record holds exact recovery references.

## Resolved package

Each lock entry has a package identity, version, source, dependency edges, and available distribution records.
Direct declarations must accept the locked version.
The requested five versions must resolve exactly.
Unrelated package versions must remain unchanged unless resolution requires a documented change.

## Generated installation list

Each export contains package pins, platform markers, dependency annotations, and the generation command.
The runtime export excludes development-only packages.
The development export includes runtime and development packages.
Both must equal fresh locked exports byte for byte.

## Validation state

An item is pending, passed, failed, or blocked.
A blocked authenticated smoke does not become passed because an offline container succeeds.
A local recovery reference does not establish remote preservation.
