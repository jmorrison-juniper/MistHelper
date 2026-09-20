# Contract: Classification and Content Signals

This contract defines the slug categories, the precedence order, the content signal
taxonomy, the label form, the confidence threshold, the fallback, and the privacy
invariant.

## Slug categories (FR-020)

`SlugClassifier` matches the slug against a keyword map for these nine categories:

1. release notes
2. configuration guides
3. administration guides
4. installation guides
5. CLI reference
6. API
7. security and compliance
8. migration
9. design

When no keyword matches, the category is `uncategorized`.

## Precedence order (FR-021)

When a slug matches more than one category keyword, the classifier applies this fixed
order and returns the first match. The order is reproducible.

```text
release notes
> security and compliance
> migration
> installation guides
> configuration guides
> administration guides
> CLI reference
> API
> design
```

Example: a slug that matches both `install` and `config` returns
`installation guides`, because installation ranks above configuration.

## Content signal groups (FR-023, FR-023a)

`SignalScorer` scores the bounded sample against three groups. Each group scores by
keyword frequency in the sample.

| Group | Signals |
|-------|---------|
| `product_family` | EX, QFX, SRX, MX, ACX, PTX, Mist, Apstra, Junos Space, Paragon, Contrail |
| `task_type` | configuration, monitoring, troubleshooting, hardware installation, licensing, interoperability |
| `technology_domain` | routing, switching, security, wireless, automation, telemetry |

The taxonomy is not a fixed list of sub-categories. The label emerges from the signals
(FR-022a).

## Label form (FR-023b)

The label joins the highest-scoring signal from each group with a double underscore,
in this group order: product family, task type, technology domain.

```text
<product_family>__<task_type>__<technology_domain>
```

Examples: `srx__configuration__security`, `mx__monitoring__telemetry`.

When a group has no signal above zero, the label omits that group segment. The label
is always human-readable and reproducible for the same sample.

## Confidence threshold and fallback (FR-025, FR-025a)

- The default confidence threshold is a total score of `2.0` across the groups.
- When no group reaches the threshold, the scorer returns the fixed fallback label
  `unclassified-content` and empty scores.
- When the PDF yields no readable text, the scorer returns the same fallback label and
  empty scores, and the run continues without a crash (FR-025).
- The scorer never assigns a wrong label to a low-confidence document. The fallback is
  the safe result.

## Bounded sample (FR-022)

`ContentSampler` reads only the title page, the table-of-contents pages, and the first
few body pages, up to `--max-sample-pages` (default 8). The sampler reads the file on
the local machine and adds no network load.

## Privacy invariant (FR-024, SC-005)

1. The sampler returns the text as one local string.
2. The scorer reads the string, builds the `ContentAnalysisResult`, and returns it.
3. The string then goes out of scope. No layer writes it anywhere.
4. The store keeps only the label, the detected signal names, and the numeric scores.
5. The manifest keeps only the derived label.

An audit of the output tree, the store, and the manifest finds no body text.
