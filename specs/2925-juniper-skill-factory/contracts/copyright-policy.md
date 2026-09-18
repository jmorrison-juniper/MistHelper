# Copyright policy contract

## Purpose

This contract defines the publishable-output rule for Juniper skill content. The
factory MUST create a skill set that restates protected source prose and keeps
only safe verbatim classes.

Warning: never copy Juniper prose into a topic file. Juniper Networks holds the
copyright of the source documents. A copied paragraph can make the skill set
unpublishable.

## Publishable-output rule

A topic file MAY state source facts. It MUST restate protected expression in new
words. A fact is not copyrightable. The expression of a fact is copyrightable.

The factory MUST apply this rule to all generated prose in these files.

1. `SKILL.md`
2. Level 1 `INDEX.md`
3. `sources.md`
4. Level 2 `INDEX.md`
5. Topic files

The factory MUST NOT store a paragraph, a procedure description, an overview, a
marketing claim, or a troubleshooting explanation copied from a Juniper source.

## Allowed verbatim classes

The factory MAY reproduce these items verbatim, because changing them can make
the answer wrong.

| Class | Examples | Rule |
| - | - | - |
| Command | `show interfaces terse` | Keep exact spelling and spacing. |
| Configuration line | `set interfaces ge-0/0/0 unit 0 family inet address 192.0.2.1/24` | Keep exact syntax. |
| Command output sample | Interface state table, alarm output | Keep exact output when needed to identify fields. |
| Identifier | `ge-0/0/0`, `JUNOS`, `SRX345` | Keep exact identifier text. |
| Model number | `EX4400-48P`, `MX480`, `AP45` | Keep exact model text. |
| Port name | `xe-0/0/0`, `WAN0` | Keep exact port text. |
| Numeric limit | `4096 VLANs`, `1000 routes` | Keep exact value and unit. |
| Standard name | `IEEE 802.1Q`, `FIPS 140-3` | Keep exact standard name. |
| Protocol name | `BGP`, `OSPF`, `EVPN`, `VXLAN` | Keep exact protocol name. |
| API path | `/api/v1/orgs/{org_id}/sites` | Keep exact path. |
| Error code | `HTTP 429`, `ERR_TIMEOUT` | Keep exact code. |

A topic MUST still restate the meaning of a verbatim block. The restated lead
sentence MUST carry the citation key.

## Text that must be restated

The factory MUST restate these source classes.

1. Concept explanations.
2. Marketing prose.
3. Procedure descriptions.
4. Warnings and cautions.
5. Troubleshooting narratives.
6. Best-practice explanations.
7. Product overview paragraphs.
8. Release note descriptions.
9. Architecture descriptions.
10. Case study business outcome prose.

The restatement MUST use Simplified Technical English. It MUST preserve the
technical meaning and the citation. It MUST NOT add facts that the source range
does not support.

## Similarity guard

The similarity guard measures the longest common prose run between generated
Markdown and the source Markdown. The guard MUST run before a package can be
published.

### Normalization

The guard MUST normalize prose in this order.

1. Remove YAML frontmatter.
2. Remove fenced code blocks.
3. Remove indented code blocks.
4. Remove inline code spans.
5. Remove Markdown links but keep link text.
6. Remove citation keys.
7. Remove table rows that contain mostly identifiers or numbers.
8. Convert text to lowercase.
9. Replace punctuation with spaces.
10. Collapse whitespace to one space.
11. Split the result into word tokens.

The guard MUST keep only tokens that contain at least one alphabetic character.
The guard MUST remove no source text outside the excluded classes above.

### Exclusions

The guard MUST exclude allowed verbatim classes before it compares text. It MUST
exclude only the specific token range that belongs to the allowed class. It MUST
NOT exclude the surrounding explanation.

The guard MUST exclude these Markdown regions.

1. Fenced code blocks.
2. Indented code blocks.
3. Inline code spans.
4. Tables whose header or cells are command output samples.
5. Citation lists in `sources.md`.

The guard MUST exclude these token patterns.

1. Interface names.
2. Model numbers.
3. API paths.
4. Protocol names.
5. Standards names.
6. Numeric values with units.
7. Error codes.
8. Configuration tokens that contain braces, brackets, slashes, or equal signs.

### Longest common run algorithm

For each generated Markdown file, the guard MUST compare the normalized token
stream to each source document that the file cites.

The guard MUST compute the longest consecutive token run that appears in both
streams. The implementation MAY use a suffix array, a rolling hash, or dynamic
programming. The result MUST be identical to an exact longest common substring
computed over word tokens.

The guard MUST warn on a file when the longest common prose run is 8 through 12
consecutive words. The factory writes the file and records it for review.

The guard MUST fail a file when the longest common prose run is greater than 12
consecutive words. A run of 7 words or less clears. A run of 8 through 12 words
warns. A run of 13 words fails.

### Threshold evidence

The rewriter agent tested the rule against a real Juniper source segment from
`guides/junos-beginners-guide.md` lines 4975 through 5050 on 2026-09-17.

| Sample | Longest run | Result |
| - | -: | - |
| Verbatim paragraph | 42 | Failed |
| Light edit of the paragraph | 14 | Failed |
| Genuine restatement | 1 | Cleared |
| Genuine restatement with verbatim CLI | 1 | Cleared |

The same test measured 30 genuine restatements of that source segment. The
longest honest run was 4 words. The median was 1 word. The mean was 1.37 words.
The 90th percentile was 2.1 words.

The warning threshold of 8 words is twice the measured honest maximum. It shows
the 8 through 12 word band without stopping the build. The hard threshold of 12
words still catches the measured light edit, which reached 14 words.

Caution: the evidence set holds 30 honest restatements. If a production run
creates many warnings, measure a larger honest set and move the warning
threshold with that evidence.

### Report format

The guard MUST report one row for each checked generated file.

| Field | Type | Rule |
| - | - | - |
| `generated_file` | path | Generated Markdown file. |
| `source_file` | path | Source Markdown file with the longest match. |
| `longest_run_words` | integer | Longest shared prose run. |
| `threshold_words` | integer | Always `12`. |
| `warn_threshold_words` | integer | Always `8`. |
| `status` | enum | `cleared`, `warned`, or `failed`. |
| `matched_text` | string | The matched normalized prose when status is `warned` or `failed`. |
| `generated_line` | integer | First generated line of the failed run. |
| `source_line` | integer | First source line of the failed run. |
| `excluded_regions` | integer | Count of excluded regions. |

The guard MUST also report a summary.

| Field | Type | Rule |
| - | - | - |
| `files_checked` | integer | Count of generated Markdown files checked. |
| `files_cleared` | integer | Count of generated Markdown files below 8 words. |
| `files_warned` | integer | Count of generated Markdown files with 8 through 12 words. |
| `files_failed` | integer | Count of generated Markdown files that failed. |
| `max_run_words` | integer | Largest run found in any checked file. |
| `source_documents_checked` | integer | Count of source Markdown files checked. |

Warning: the guard MUST fail when `files_checked` is zero. A zero-file pass can
publish unmeasured copied prose.

Warning: the guard MUST fail when a required cited source cannot be read. A
missing source prevents the guard from proving copyright safety.

## Restatement quality rule

A restated card MUST preserve these source facts when they exist.

1. Actor.
2. Action.
3. Condition.
4. Limit.
5. Exception.
6. Version or platform scope.
7. Warning or caution consequence.
8. Citation range.

A restated card MUST NOT preserve the source sentence structure when a different
structure can state the same fact. The factory MUST prefer short sentences and
one fact per card.

## Human source pointer rule

An answer MAY point an agent or a human operator to the source document when the
exact Juniper wording matters. The generated skill MUST NOT provide that exact
wording except for an allowed verbatim class.

Use this answer shape when exact wording matters.

```text
The skill restates the requirement. Read the Juniper source at [<KEY>] for the
exact vendor wording.
```

## Guard outcome rule

A package is publishable only when all of these checks pass.

1. Every generated Markdown file was checked.
2. Every cited source document was readable.
3. No generated file had a prose run longer than 12 words.
4. The report listed the count of checked files.
5. The report listed the maximum run length.
6. The report listed each failed run with line evidence.
