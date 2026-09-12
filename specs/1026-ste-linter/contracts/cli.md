# CLI Contract: STE Linter

**Feature**: 1026-ste-linter | **Phase**: 1

## Command

```text
python -m tools.ste_linter [OPTIONS] PATH [PATH ...]
ste-linter [OPTIONS] PATH [PATH ...]
```

## Arguments

- `PATH`: One or more file paths. The tool grades `.md` and `.py` files. It skips
  other file types with a note.

## Options

| Option | Type | Default | Description |
| - | - | - | - |
| `--format` | text or json | text | The report format |
| `--min-score` | integer | none | The pass threshold from 0 to 100 |
| `--dictionary` | path | data/ste_dictionary.json | The dictionary file path |
| `--config` | path | pyproject.toml | The configuration file path |
| `--select` | list | all | Only run these rule identifiers |
| `--ignore` | list | none | Do not run these rule identifiers |
| `--quiet` | flag | off | Print only the score line |
| `--version` | flag | off | Print the version and exit |

## Exit codes

- `0`: Every graded file scored at or above `--min-score`, or no threshold was set.
- `1`: At least one file scored below `--min-score`.
- `2`: A usage error, for example a path that does not exist.

## Text output (example)

```text
documentation/example.md
  Score: 82/100  (words graded: 640, dictionary: skipped)
  Sections: 1-words 95 | 3-verbs 70 | 4-sentences 88 | 5-procedural 60
  Violations (7):
    L12  STE-S3-PASSIVE  warning  Passive voice. Name the actor and use the active voice.
    L18  STE-S1-LEN      error    Sentence has 27 words. The limit is 20 for a step.
    ...
```

## JSON output (schema)

```json
{
  "version": "1.0",
  "results": [
    {
      "path": "documentation/example.md",
      "score": 82,
      "word_count": 640,
      "dictionary_used": false,
      "sections": [
        { "section": "1-words", "score": 95, "penalty": 0.05, "violation_count": 1 }
      ],
      "violations": [
        {
          "rule_id": "STE-S3-PASSIVE",
          "section": "3-verbs",
          "severity": "warning",
          "path": "documentation/example.md",
          "line": 12,
          "column": 0,
          "message": "Passive voice. Name the actor and use the active voice.",
          "suggestion": "Rewrite so the actor is the subject."
        }
      ]
    }
  ],
  "summary": { "files": 1, "min_score": null, "passed": true }
}
```

## Behavior contract

- The tool never raises an unhandled exception for a readable file. A parse problem
  becomes a note in the report, not a crash.
- The score and the report are the same for the same input on repeated runs.
- When no threshold is set, the exit code is 0 even for a low score.
- When the dictionary file is absent, `dictionary_used` is false and the report
  says the dictionary checks were skipped.
