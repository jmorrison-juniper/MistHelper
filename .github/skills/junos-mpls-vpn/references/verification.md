# Implementation and verification

Use this reference to prove a source, audit a command, and report limits.

## Contents

1. [Source set](#source-set)
2. [Citation rule](#citation-rule)
3. [Command verification method](#command-verification-method)
4. [Confirmed command count](#confirmed-command-count)
5. [Dropped commands](#dropped-commands)
6. [Skill limits](#skill-limits)
7. [Offline acceptance checks](#offline-acceptance-checks)
8. [Sources](#sources)

## Source set

The manifest is outside the repository at this path:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives\skill-manifests\junos-mpls-vpn.json
```

The staged corpus root is:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives
```

The manifest lists 6 documents and 7,069 pages. The corpus index in this skill
has one row for each document. Each row resolves to a real Markdown file under
the corpus root.

## Citation rule

Cite the public Juniper URL first. Then cite the staged Markdown path and page.
Use this public URL for the six staged 26.2 PDF guides:

```text
https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
```

Do not cite `documentation/references/`. That path is ignored by Git.

## Command verification method

Each command in the three reference files came from an exact text search across
the six staged Markdown files. The search read concrete examples only. It did
not accept an angle bracket placeholder as proof.

For a new command, use this method:

1. Open `references/corpus-index.csv`.
2. Select the document that matches the service.
3. Search the staged Markdown file for a concrete command.
4. Count the page marker before the match.
5. Cite the document, train, staged path, and page.
6. If no concrete command exists, mark the command as unverified.

Warning: never invent a Junos command. An invented command on a production PE can
interrupt customer traffic or block rollback.

## Confirmed command count

This skill confirms 82 unique concrete command lines.

| Reference | Confirmed commands |
| - | -: |
| MPLS core | 36 |
| VPN services | 24 |
| EVPN and VXLAN | 26 |

The total count deduplicates repeated `set` and `show` lines across all references.
The per-reference count deduplicates only inside that reference.

## Dropped commands

These candidate commands were not added because the exact command was not found
in the six staged files during this build:

| Dropped command | Reason |
| - | - |
| `show vpls connections` | No exact match appeared in the staged source set. |
| `show l2circuit connections` | No exact match appeared in the staged source set. |
| `set protocols mpls label-switched-path pe1-pe2 fast-reroute` | No exact LSP fast-reroute form appeared in the staged source set. |
| `set protocols mpls traffic-engineering mpls-forwarding` | No exact match appeared in the staged source set. |

Use a new corpus search before you add one of these commands later.

## Skill limits

This skill distils the staged documents. It does not replace the platform
release notes, CLI help on a live device, or a reviewed change plan.

Segment routing coverage is limited to the commands that appear in the MPLS
guide. The source set does not include a separate segment routing guide.

The OVSDB and VXLAN content names the staged guides and one verified show
command. Use the controller documentation before you change controller-owned
state.

## Offline acceptance checks

Run these checks from the worktree root after a change to this skill:

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-mpls-vpn\SKILL.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-mpls-vpn\references\mpls-core.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-mpls-vpn\references\vpn-services.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-mpls-vpn\references\evpn-vxlan.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-mpls-vpn\references\verification.md
```

Run a CSV and path check with a short Python script. The check must report six
rows and six readable files.

## Sources

| ID | Title | Train | Public URL | Staged path |
| - | - | - | - | - |
| M1 | Junos OS MPLS Applications User Guide | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/mpls.md` |
| E1 | Junos OS EVPN User Guide | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/evpn.md` |
| E2 | Junos OS EVPN User Guide snapshot | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/evpn-vxlan.md` |
| O1 | Junos OS OVSDB and VXLAN User Guide for MX Series Routers and EX9200 Switches | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ovsdb-vxlan.md` |
| O2 | Junos OS OVSDB-VXLAN User Guide for QFX Series Switches | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ovsdb-vxlan-qfx.md` |
| O3 | Junos OS OVSDB and VXLAN User Guide for QFX Series Switches | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ovsdb-vxlan-contrail.md` |
