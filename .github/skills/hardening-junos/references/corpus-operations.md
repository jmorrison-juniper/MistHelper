# Corpus operations

This file tells a reader how to set the corpus root and search the corpus.
It also tells a reader how to refresh the index and read the gap register.
It also holds the archive code table.

The verified snapshot date is 2026-09-16.

## Source selection

Use this index to choose a source before you answer. Name the source document and the Junos train in each answer.

No `hardening-junos`, Junos security, or Junos hardening skill existed in the current `.github/skills/` folder on the `origin/main` worktree. The session skill list also had no Junos hardening skill. The repository has security text and Mist API safety rules, so this skill links those rules instead of copying all source text.

`documentation/foa` and `documentation/color-codes` are for fiber practice and color codes. They do not cover Junos hardening.

| ID | Title | Train or version | Path or URL | Use |
| - | - | - | - | - |
| R1 | MistHelper security and safety | Repository source | `documentation/security.md` | General security rules. |
| R2 | Global coding standards | Repository source | `.github/instructions/coding-standards.instructions.md` | Secret logging and suppression policy. |
| R3 | MistHelper instructions | Repository source | `.github/copilot-instructions.md` | `.env`, SSH, and destructive-review rules. |
| R4 | Operation registry | Repository source | `src/utils/operation_registry.py` | Current destructive menu classification. |
| R5 | ZTP password renderer | Repository source | `src/device/_utility_commands_action.py` | One-time ZTP password display rule. |
| R6 | SSH runner manager | Repository source | `src/ssh/ssh_runner_manager.py` | SSH credential collection and plan display. |
| R7 | Container SSH configuration | Repository source | `Dockerfile` | Port 2200 and `ForceCommand` behavior. |
| J1 | `root-authentication` statement | Introduced before Junos OS Release 7.4 | https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/root-authentication-edit-system.html | Root authentication methods. |
| J2 | `request system zeroize` command | Introduced before Junos OS Release 9.0 | https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/request-system-zeroize.html | Device reset and data removal behavior. |
| J3 | Local Junos command help | Repository source | `documentation/Junos show_command_help.json` | Local command-name check only. |

Use repository sources for MistHelper behavior. Use Juniper sources for Junos command effects. Use the local command help only to confirm that a command name exists in the staged command-help data.

Do not cite the converted corpus as complete. The full corpus stays outside the repository. This skill keeps a small source index and marks missing corpus details as unverified.

## The corpus root

The corpus stays outside this repository, because the files are verbatim vendor text. The
default corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives`. Set the
`JUNIPER_CORPUS_ROOT` variable to move it.

```powershell
$env:JUNIPER_CORPUS_ROOT = 'C:\Users\jmorrison\Downloads\juniper-doc-archives'
```

The root holds `extracted/` with the source PDF files, `markdown/` with the converted text, and
`archives/` with the compressed originals.

## The archive code table

The `archive` column of `references/corpus-index.csv` holds a code. This table gives the
directory of each code. The directory is relative to the corpus root. A row without a public URL
holds `-`.

The table uses 4 character codes because 165 directories repeat across 775 selected rows. The
average directory path is 53 characters. The code removes that repeated text and saves about
75 KB in the index.

Use this rule to assign a code. First, count selected index rows for each archive directory. Then
order directories by that count, from high to low. If two directories have the same count, order
those directories by the relative directory name. Keep an existing code on each rebuild. Assign
the next unused code only when a new directory appears.

This rule makes each code reproducible for the verified snapshot. The saved table makes each code
stable for the next rebuild.

Build both paths from an index row and this table.

```text
PDF path      = <directory> + "/" + <file> + ".pdf"
Markdown path = "markdown/" + <directory> + "/" + <file> + ".md"
```

| code | directory | train | url |
| - | - | - | - |
| A001 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/task/configuration` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A002 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/task/configuration` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A003 | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262` | 26.2 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip |
| A004 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/task/configuration` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A005 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/task/verify` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A006 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/concept` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A007 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/reference/general` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A008 | `extracted/junos-for-srx-doc-set-pdfs/junos-for-srx-doc-set-pdfs` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-for-srx-doc-set-pdfs.zip |
| A009 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/concept` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A010 | `extracted/juniper-webapp-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-webapp-doc-archives.zip |
| A011 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/concept` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A012 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/task/verify` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A013 | `extracted/juniper-firefly-vgw-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-firefly-vgw-doc-archives.zip |
| A014 | `extracted/strm-doc-archives/2013_2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/strm-doc-archives.zip |
| A015 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/task/operational` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A016 | `extracted/security-director-archives-21.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-21.1.zip |
| A017 | `extracted/security-director-archives-21.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-21.2.zip |
| A018 | `extracted/SRC-DOC-CD20x/SDX-DOC-CD/Documentation/SRC_20x_doc/sw-cweb-configuration/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD20x.tgz |
| A019 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/task/operational` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A020 | `extracted/jsa-doc-archives-7.3.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-7.3.2.zip |
| A021 | `extracted/juniper-junosphere-doc-archives/junosphere1.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-junosphere-doc-archives.zip |
| A022 | `extracted/juniper-ssg-series-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-ssg-series-doc-archives.zip |
| A023 | `extracted/security-director-archives-19.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-19.2.zip |
| A024 | `extracted/security-director-archives-19.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-19.3.zip |
| A025 | `extracted/security-director-archives-19.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-19.4.zip |
| A026 | `extracted/security-director-archives-20.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-20.1.zip |
| A027 | `extracted/security-director-archives-20.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-20.3.zip |
| A028 | `extracted/strm-doc-archives/2013_1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/strm-doc-archives.zip |
| A029 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-get-start/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A030 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-subscriber-subscription/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A031 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/reference/general` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A032 | `extracted/juniper-junosphere-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-junosphere-doc-archives.zip |
| A033 | `extracted/juniper-ns-series-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-ns-series-doc-archives.zip |
| A034 | `extracted/security-director-archives-18.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-18.1.zip |
| A035 | `extracted/security-director-archives-18.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-18.2.zip |
| A036 | `extracted/security-director-archives-18.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-18.3.zip |
| A037 | `extracted/security-director-archives-18.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-18.4.zip |
| A038 | `extracted/security-director-archives-19.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-19.1.zip |
| A039 | `extracted/SRC-DOC-CD20x/SDX-DOC-CD/Documentation/SRC_20x_doc/sw-sdx-get-start/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD20x.tgz |
| A040 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/reference/field-group` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A041 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/task/operational` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A042 | `extracted/jatp-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jatp-doc-archives.zip |
| A043 | `extracted/jsa-doc-archives-7.3.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-7.3.1.zip |
| A044 | `extracted/juniper-junosphere-doc-archives/junosphere2.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-junosphere-doc-archives.zip |
| A045 | `extracted/juniper-src-4.10-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/src/juniper-src-4.10-doc-archives.zip |
| A046 | `extracted/juniper-wandl-ip-mplsview-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-wandl-ip-mplsview-doc-archives.zip |
| A047 | `extracted/paragon-automation-onprem-archives-21.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/paragon-automation-onprem-archives-21.3.zip |
| A048 | `.` | - | - |
| A049 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-integration/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A050 | `extracted/SRC-DOC-CD20x/SDX-DOC-CD/Documentation/SRC_20x_doc/sw-sdx-monitor-trblshoot/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD20x.tgz |
| A051 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/reference/statement-hierarchy` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A052 | `extracted/active-assurance-archives-3.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-3.0.zip |
| A053 | `extracted/active-assurance-archives-3.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-3.2.zip |
| A054 | `extracted/corero-smartwall-archives-10.3.0/corero-smartwall-archives-10.3.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-10.3.0.zip |
| A055 | `extracted/jsa-doc-archives-2014.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.1.zip |
| A056 | `extracted/jsa-doc-archives-7.3.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-7.3.3.zip |
| A057 | `extracted/juniper-nsm-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-nsm-doc-archives.zip |
| A058 | `extracted/juniper-qfx-series-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-qfx-series-doc-archives.zip |
| A059 | `extracted/juniper-sbr-carrier-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-sbr-carrier-doc-archives.zip |
| A060 | `extracted/juniper-src-4.12-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/src/juniper-src-4.12-doc-archives.zip |
| A061 | `extracted/northstar-archives-4.2.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/northstar/northstar-archives-4.2.0.zip |
| A062 | `extracted/paragon-automation-onprem-archives-21.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/paragon-automation-onprem-archives-21.1.zip |
| A063 | `extracted/paragon-automation-onprem-archives-21.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/paragon-automation-onprem-archives-21.2.zip |
| A064 | `extracted/security-director-archives-21.3/security-director-archives-21.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-21.3.zip |
| A065 | `extracted/security-director-archives-22.1/Security Director22.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-22.1.zip |
| A066 | `extracted/security-director-archives-22.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-22.3.zip |
| A067 | `extracted/SRC-DOC-CD20x/SDX-DOC-CD/Documentation/SRC_20x_doc/sw-sdx-cli-user-guide/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD20x.tgz |
| A068 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/reference/statement-hierarchy` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A069 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/task/verify` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A070 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/example/simple` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A071 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/example/simple` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A072 | `extracted/TW_HardeningJunosDevices_2ndEd` | - | - |
| A073 | `extracted/U_Juniper_EX_Switches_Y26M07_STIG` | - | - |
| A074 | `extracted/active-assurance-archives-3.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-3.1.zip |
| A075 | `extracted/active-assurance-archives-3.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-3.3.zip |
| A076 | `extracted/bti7000-documentation/BTI7000-Documentation` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/bti-tcx/bti7000-documentation.zip |
| A077 | `extracted/contrail-cloud-archives-10` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/contrail-cloud-archives-10.zip |
| A078 | `extracted/corero-smartwall-archives-9.7.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-9.7.0.zip |
| A079 | `extracted/corero-smartwall-archives-9.7.2/corero-smartwall-archives-9.7.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-9.7.2.zip |
| A080 | `extracted/corero-smartwall-archives-9.7.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-9.7.3.zip |
| A081 | `extracted/corero-smartwall-archives-9.7.5` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-9.7.5.zip |
| A082 | `extracted/jsa-doc-archives-2014.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.2.zip |
| A083 | `extracted/jsa-doc-archives-2014.5` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.5.zip |
| A084 | `extracted/jsa-doc-archives-7.4.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-7.4.2.zip |
| A085 | `extracted/juniper-idp-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-idp-doc-archives.zip |
| A086 | `extracted/juniper-isg-series-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-isg-series-doc-archives.zip |
| A087 | `extracted/juniper-mbg-doc-archives-12.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-mbg-doc-archives-12.1.zip |
| A088 | `extracted/northstar-archives-6.0.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/northstar/northstar-archives-6.0.0.zip |
| A089 | `extracted/northstar-archives-6.1.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/northstar/northstar-archives-6.1.0.zip |
| A090 | `extracted/paragon-automation-onprem-archives-22.1/paragon-automation-onprem-archives-22.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/paragon-automation-onprem-archives-22.1.zip |
| A091 | `extracted/policy-enforcer-archives-20.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-20.1.zip |
| A092 | `extracted/policy-enforcer-archives-21.3/policy-enforcer-archives-21.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-21.3.zip |
| A093 | `extracted/security-director-insights-archives-22.1/security-director-insights-archives-22.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-insights-archives-22.1.zip |
| A094 | `extracted/Apstra_4.1_Docs/Apstra_4.1_Docs` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/apstra/Apstra_4.1_Docs.zip |
| A095 | `extracted/Apstra_40_Docs/Apstra_40_Docs` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/apstra/Apstra_40_Docs.zip |
| A096 | `extracted/DO_Configuring_Junos_Policies_Filters` | - | https://www.juniper.net/documentation/us/en/internal/day-one-books-archive/DO_Configuring_Junos_Policies_Filters.zip |
| A097 | `extracted/DO_EVPNSforDCI` | - | https://www.juniper.net/documentation/us/en/internal/day-one-books-archive/DO_EVPNSforDCI.zip |
| A098 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-cli-user-guide/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A099 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-monitor-trblshoot/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A100 | `extracted/SRC-DOC-CD10x/SDX-DOC-CD/Documentation/SRC_10x_doc/sw-sdx-solutions/download` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD10x.tgz |
| A101 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/example/simple` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A102 | `extracted/SRC-DOC-CD30x/SRC-30x-DOC-CD/Documentation/topics/reference/general` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD30x.tgz |
| A103 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/reference/field-group` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A104 | `extracted/SRC-DOC-CD31x/SRC-31x-DOC-CD/Documentation/topics/reference/statement-hierarchy` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD31x.zip |
| A105 | `extracted/SRC-DOC-CD32x/SRC-32x-DOC-CD/Documentation/topics/task/trouble` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/SRC-DOC-CD32x.zip |
| A106 | `extracted/TW_BGP_MVPNs` | - | https://www.juniper.net/documentation/us/en/internal/day-one-books-archive/TW_BGP_MVPNs.zip |
| A107 | `extracted/active-assurance-archives-3.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-3.4.zip |
| A108 | `extracted/active-assurance-archives-4.0/active-assurance-archives-4.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-4.0.zip |
| A109 | `extracted/active-assurance-archives-4.1/active-assurance-archives-4.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/active-assurance-archives-4.1.zip |
| A110 | `extracted/ai-scripts-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/ai-scripts-archives.zip |
| A111 | `extracted/anuta-atom-archives-10.6/anuta-atom-archives-10.6` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/anuta-atom/anuta-atom-archives-10.6.zip |
| A112 | `extracted/anuta-atom-archives-11.0/anuta-atom-archives-11.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/anuta-atom/anuta-atom-archives-11.0.zip |
| A113 | `extracted/anuta-atom-archives-11.8/anuta-atom-archives-11.8` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/anuta-atom/anuta-atom-archives-11.8.zip |
| A114 | `extracted/anuta-atom-archives-11.9/anuta-atom-archives-11.9` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/anuta-atom/anuta-atom-archives-11.9.zip |
| A115 | `extracted/connectivity-services-director-archives-4.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-4.0.zip |
| A116 | `extracted/connectivity-services-director-archives-4.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-4.1.zip |
| A117 | `extracted/connectivity-services-director-archives-4.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-4.2.zip |
| A118 | `extracted/connectivity-services-director-archives-5.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-5.0.zip |
| A119 | `extracted/connectivity-services-director-archives-5.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-5.1.zip |
| A120 | `extracted/connectivity-services-director-archives-5.3/connectivity-services-director-archives-5.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-5.3.zip |
| A121 | `extracted/connectivity-services-director-archives-5_2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/connectivity-services-director-archives-5_2.zip |
| A122 | `extracted/contrail-insights-archives/contrail-insights-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/contrail-insights-archives.zip |
| A123 | `extracted/contrail-networking-archives-20/contrail-networking-archives-20` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/contrail-networking-archives-20.zip |
| A124 | `extracted/contrail-networking-archives-5.1/contrail-networking-archives-5.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/contrail-networking-archives-5.1.zip |
| A125 | `extracted/corero-smartwall-archives-10.3.1/corero-smartwall-archives-10.3.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-10.3.1.zip |
| A126 | `extracted/corero-smartwall-archives-10.3.2/corero-smartwall-archives-10.3.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/corero-smartwall/corero-smartwall-archives-10.3.2.zip |
| A127 | `extracted/cso-doc-archives-3.2.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/cso-doc-archives-3.2.0.zip |
| A128 | `extracted/cso-doc-archives-4.0.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/cso-doc-archives-4.0.0.zip |
| A129 | `extracted/cso-doc-archives-5.1.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/cso-doc-archives-5.1.2.zip |
| A130 | `extracted/cso-doc-archives-5.3.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/cso-doc-archives-5.3.0.zip |
| A131 | `extracted/cso-doc-archives-6.1.0` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/contrail/cso-doc-archives-6.1.0.zip |
| A132 | `extracted/j-web-21.1/j-web-21.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/j-web/j-web-21.1.zip |
| A133 | `extracted/j-web-21.3/j-web-21.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/j-web/j-web-21.3.zip |
| A134 | `extracted/j-web-21.4/j-web-21.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/j-web/j-web-21.4.zip |
| A135 | `extracted/j-web-23.1/j-web-23.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/j-web/j-web-23.1.zip |
| A136 | `extracted/jcnr-23.1-archives/jcnr-23.1-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jcnr/jcnr-23.1-archives.zip |
| A137 | `extracted/jsa-doc-archives-2014.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.3.zip |
| A138 | `extracted/jsa-doc-archives-2014.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.4.zip |
| A139 | `extracted/jsa-doc-archives-2014.6` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.6.zip |
| A140 | `extracted/jsa-doc-archives-2014.7` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-2014.7.zip |
| A141 | `extracted/jsa-doc-archives-7.4.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa-doc-archives-7.4.1.zip |
| A142 | `extracted/jsa3800-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/jsa/jsa3800-archives.zip |
| A143 | `extracted/juniper-PDFs-junos-254/juniper-PDFs-junos-254` | 25.4 | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-254.zip |
| A144 | `extracted/juniper-mbg-doc-archives-11.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-mbg-doc-archives-11.4.zip |
| A145 | `extracted/juniper-src-4.7-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/src/juniper-src-4.7-doc-archives.zip |
| A146 | `extracted/juniper-src-4.9-doc-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/src/juniper-src-4.9-doc-archives.zip |
| A147 | `extracted/network-director-archives-6.1/Network Director6.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/network-director-archives-6.1.zip |
| A148 | `extracted/paragon-automation-onprem-archives-23.1/paragon-automation-onprem-archives-23.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/paragon/paragon-automation-onprem-archives-23.1.zip |
| A149 | `extracted/policy-enforcer-archives-18.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-18.1.zip |
| A150 | `extracted/policy-enforcer-archives-18.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-18.2.zip |
| A151 | `extracted/policy-enforcer-archives-18.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-18.3.zip |
| A152 | `extracted/policy-enforcer-archives-18.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-18.4.zip |
| A153 | `extracted/policy-enforcer-archives-19.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-19.1.zip |
| A154 | `extracted/policy-enforcer-archives-19.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-19.2.zip |
| A155 | `extracted/policy-enforcer-archives-19.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-19.3.zip |
| A156 | `extracted/policy-enforcer-archives-19.4` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-19.4.zip |
| A157 | `extracted/policy-enforcer-archives-20.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-20.3.zip |
| A158 | `extracted/policy-enforcer-archives-21.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-21.1.zip |
| A159 | `extracted/policy-enforcer-archives-21.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-21.2.zip |
| A160 | `extracted/policy-enforcer-archives-22.1/policy-enforcer-archives-22.1` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-22.1.zip |
| A161 | `extracted/policy-enforcer-archives-22.2/policy-enforcer-archives-22.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/policy-enforcer-archives-22.2.zip |
| A162 | `extracted/security-director-archives-22.2` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-archives-22.2.zip |
| A163 | `extracted/security-director-insights-archives-21.3/security-director-insights-archives-21.3` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/security-director-insights-archives-21.3.zip |
| A164 | `extracted/service-now-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-space/service-now-archives.zip |
| A165 | `extracted/virtual-chassis-fabric-archives/virtual-chassis-fabric-archives` | - | https://www.juniper.net/documentation/en_US/release-independent/downloads/virtual-chassis-fabric/virtual-chassis-fabric-archives.zip |

## Sources

The vendor text is not committed. The repository holds this distilled file instead. Rebuild
the source corpus with `python scripts/pdf_to_markdown.py`.

| Source | Where | Use |
| - | - | - |
| `selection-inventory.csv` | Corpus root | Download list, archive decision, Junos train, file size, and public URL. |
| `corpus-catalog.csv` | Corpus root | Converted document title, train, product, page count, source PDF, and security flag. |
| `manifest.json` | Corpus root | Download status, archive member count, file size, and extracted folder. |

A measured inventory holds 378 archive rows. A measured catalog holds
4006 converted document rows. The manifest records 292
downloaded archive entries.

## Rebuild the corpus

Use this procedure when the staged corpus is absent.

1. Set `JUNIPER_CORPUS_ROOT` to the corpus root.
2. Read `selection-inventory.csv` from the corpus root.
3. Download each row that has the decision `download` and a public URL.
4. If a row has no public URL, restore the hand added bundle from the operator archive.
5. Extract each archive below `extracted/` and keep the archive folder name.
6. Convert each PDF with `python scripts/pdf_to_markdown.py`.
7. Rebuild `references/corpus-index.csv` with the procedure in this file.

The measured converter speed is 2 to 3.5 pages each second for one worker. A full rebuild of
511,674 pages takes about 2 hours with 26 worker processes. Disk speed and PDF structure can
move that value.

Caution: do not commit the corpus. A commit can publish verbatim vendor text.
The repository must ship only distilled references.

## Rebuild the index

The index builder reads the YAML front matter of each Markdown file below `markdown/`. The front
matter gives `source_file`, `pages`, and sometimes `title`. It gives no train and no security
flag. Derive those two fields from the archive folder name and the catalog.

The measured field coverage comes from a 400 file sample.

| Field | Coverage | Index use |
| - | - | - |
| `source_file` | 100 percent | Confirms the `file` value. |
| `pages` | 100 percent | Supplies `pages`. |
| `creationDate` | 98.8 percent | Not used. |
| `modDate` | 98.5 percent | Not used. |
| `title` | 87.8 percent | Supplies `title`, cut to 70 characters. |
| `author` | 68.0 percent | Not used. |
| `subject` | 11.2 percent | Not used. |

Use this 7 step procedure.

1. Read the YAML front matter from each Markdown file below `markdown/`.
2. Set `file` from the name of the Markdown file, without the extension.
3. Set `title` from front matter, or from the file name when the field is absent.
4. Set `pages` from front matter, and reject a document below 200 characters for each page.
5. Set `train` from the archive folder name. For example, `juniper-PDFs-junos-262` gives `26.2`.
6. Set `archive` by looking up the relative archive directory in this table.
7. Set `group`, `origin`, and `gap`, then write the 8 columns with LF line endings.

The `group` value comes from the ordered keyword rule for the 8 checklist sections. The `origin`
value comes from the catalog security flag, the term list, or the checklist need list. The `gap`
value comes from the gap register.

Run the contract checks after each rebuild. The checks must prove that the index has 775 data rows,
8 columns, unique `file` values, valid archive codes, and no absolute path.

## Search the corpus

Use the index first, because it is small and committed.

1. Search `references/corpus-index.csv` for the control term.
2. Read the `archive` code from the matching row.
3. Read the archive directory from this table.
4. Build the Markdown path with the path rule above.
5. Open the Markdown file under the corpus root.

If the corpus is absent, use the curated reference file first. Then cite the public URL from this
table.

## Gap register

The `gap` column marks a known source gap.

| Value | Meaning | Reader action |
| - | - | - |
| `-` | No known gap. | Use the row normally. |
| `c` | The newest train has a corrupt copy. | Use the fallback train named by the gap note. |
| `s` | The conversion skipped an existing output. | Confirm that the Markdown file exists. |

Add a gap only after a rebuild proves it. A gap note must name the file, the archive code, the
observed problem, and the selected replacement.

## Acceptance checks

Run these checks after a rebuild.

1. Confirm that the archive table holds 165 codes.
2. Confirm that 162 codes carry a public URL.
3. Confirm that each index `archive` value exists in this table.
4. Confirm that no row cites an absolute path or a drive letter.
5. Confirm that no row cites a path below a gitignored reference directory.
6. Confirm that this file stays below 60 KB.
7. Run `python -m tools.ste_linter --min-score 80 .github\skills\hardening-junos\references\corpus-operations.md`.

Warning: do not run `podman volume prune`. That command deletes the stores that hold each capture
and upgrade run. The operator loses the stored records.

Warning: do not pass `-v` to a compose `down` command. That option deletes the stores that hold
each capture and upgrade run. The operator loses the stored records.
