# Implementation and verification

## Contents

1. [Verify a platform claim](#verify-a-platform-claim)
2. [Source selection](#source-selection)
3. [Indexed corpus set](#indexed-corpus-set)
4. [Coverage decisions](#coverage-decisions)
5. [Confirmed procedures](#confirmed-procedures)
6. [Offline acceptance checks](#offline-acceptance-checks)
7. [Skill limits](#skill-limits)

## Verify a platform claim

Use this procedure before you answer from this skill.

1. Open `references/corpus-index.csv`.
2. Find the row for the product, topic, or file name.
3. Build the source path under `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
4. Open the Markdown file.
5. Search for the task heading.
6. Confirm that the nearest `<!-- page N -->` marker supports the page number.
7. Confirm that the source text supports the claim.
8. Name the source document, release, and page in the answer.
9. If the source does not support the claim, mark the claim as unverified.
10. If the action can affect the fabric or many devices, add a warning first.

Caution: the repository does not hold the Juniper corpus. If the corpus root is
absent, use only the curated references and state that the source cannot be
rechecked locally.

## Source selection

Use this source order:

1. Use `workspaces-21.2` for current detailed Junos Space platform procedures.
2. Use `software-guide-junos-space-platform-21.1` for platform overviews and architecture.
3. Use `network-director-api-reference` for Network Director API access.
4. Use `network-director-pwp-4.0` for Network Director UI modes.
5. Use `connectivity-services-director-user-guide-5.3` for Connectivity Services Director procedures.
6. Use `connectivity-services-director-api-pwp-5.3` for Connectivity Services Director API details.
7. Use older releases only when a target environment runs that release.
8. Use release notes only when a release note changes the target procedure.

Do not cite a path below `documentation/references/`. That path is ignored by
Git, and a cloned repository does not include it.

## Indexed corpus set

The manifest has 163 documents. This skill indexes 8 documents. Each row resolves
to an existing Markdown file under the corpus root.

The selected set covers these areas:

- Junos Space platform fabric, database, roles, device management, templates, and images.
- Network Director topology, fault, monitor, deployment, and API use.
- Connectivity Services Director service views, deployment, service orders, and API use.

The pass stopped after those 8 documents because later rows repeat older
releases, release notes, or application subsets. The newest selected user guides
and API references cover the requested subject.

## Coverage decisions

### Junos Space platform

The platform references cover the fabric node, high availability, appliance
initial configuration, virtual appliance requirements, platform upgrade, database
backup and restore, user roles, domains, sessions, and API access profiles.

### Device management

The fleet reference covers discovery profiles, profile runs, connection status,
managed status, resync, system of record behavior, template creation, template
assignment, template deployment, image import, image staging, checksum
validation, and image deployment.

### Network Director

The application reference covers topology view, Fault mode, Monitor mode, Deploy
mode, deployment job results, Network Director API roles, and REST client
requirements.

### Connectivity Services Director

The application reference covers Service View, Device View, Custom Group View,
Topology View, Deploy mode, change requests, SNMP trap configuration, service
orders, audits, performance management, and REST resource families.

## Confirmed procedures

This skill includes 23 procedures confirmed in the staged corpus.

| Procedure | Source page |
| - | - |
| Deploy a hardware fabric node | Platform guide 21.1, pages 54 and 55 |
| Deploy a virtual appliance | Platform guide 21.1, pages 55 and 56 |
| Upgrade the platform | Platform guide 21.1, pages 62 and 63 |
| Back up the database | Workspaces guide 21.1, pages 1158 through 1161 |
| Restore the database | Workspaces guide 21.1, pages 1159 through 1161 |
| Assign roles and domains | Platform guide 21.1, pages 68 through 70 |
| Manage user sessions | Workspaces guide 21.1, pages 965 through 969 |
| Create an API access profile | Workspaces guide 21.1, pages 961 and 962 |
| Create a device discovery profile | Workspaces guide 21.1, pages 85 through 96 |
| Run a device discovery profile | Workspaces guide 21.1, pages 96 and 97 |
| Check device adoption status | Platform guide 21.1, pages 79 and 80 |
| Resync a managed device | Workspaces guide 21.1, pages 306 and 307 |
| Create a quick template | Workspaces guide 21.1, pages 366 through 373 |
| Assign a device template | Workspaces guide 21.1, pages 354 through 356 |
| Deploy a template | Workspaces guide 21.1, pages 356 and 357 |
| Review and deploy pending configuration | Workspaces guide 21.1, pages 147 through 159 |
| Import a device image | Workspaces guide 21.1, pages 473 and 474 |
| Stage a device image | Workspaces guide 21.1, pages 478 through 481 |
| Deploy a device image | Workspaces guide 21.1, pages 499 through 504 |
| Use Network Director topology view | Network Director guide 4.0, pages 218 through 223 |
| Use Network Director fault and monitor views | Network Director guide 4.0, pages 1422 through 1427 and 1243 through 1248 |
| Use Connectivity Services Director deploy mode | CSD guide 5.3, pages 890 through 906 |
| Use REST APIs | CSD API guide 5.3, pages 40 through 42, and Network Director API 5.3, pages 4 through 6 |

## Offline acceptance checks

Run these checks before you use the skill in a pull request.

```powershell
python -m tools.ste_linter --min-score 80 .github\skills\junos-space-platform\SKILL.md
python -m tools.ste_linter --min-score 80 .github\skills\junos-space-platform\references\platform-administration.md
python -m tools.ste_linter --min-score 80 .github\skills\junos-space-platform\references\fleet-operations.md
python -m tools.ste_linter --min-score 80 .github\skills\junos-space-platform\references\director-applications-and-api.md
python -m tools.ste_linter --min-score 80 .github\skills\junos-space-platform\references\verification.md
```

The CSV check must confirm that each indexed path resolves under the corpus
root. The size check must confirm that the whole skill is below 400 KB.

## Skill limits

This skill is a distilled operational guide. It is not a substitute for a change
plan, release notes, or a lab test.

Warning: do not execute a fabric change, database restore, mass configuration
deployment, or image upgrade from this summary alone. A wrong action can affect
all managed devices or customer services.

If a user asks for a release that is not in the selected index, search the
manifest and read that release before you answer. If a user asks for a live
change, use the repository workflow and require explicit approval.
