# CLI Contract: Dictionary Extractor and Quality Harness

**Feature**: 1027-ste-dict-extractor | **Phase**: 1

## Extractor command

```text
python -m tools.ste_linter.dictionary.extract PDF [--output PATH]
```

### Arguments

- `PDF`: The path to the licensed ASD-STE100 PDF.

### Options

| Option | Default | Description |
| - | - | - |
| `--output` | data/ste_dictionary.json | The output JSON path (git-ignored). |
| `--start-page` | 155 | The first page to scan for real entries. |

### Exit codes

- `0`: The tool wrote the dictionary.
- `1`: The PDF is missing or unreadable, or pdfplumber is not installed.

### Output

A JSON object:

```json
{
  "version": "1.0",
  "entries": [
    {
      "keyword": "accuracy",
      "part_of_speech": "n",
      "approved": false,
      "alternatives": ["precision"],
      "approved_meaning": ""
    }
  ]
}
```

The tool prints a one-line summary: the number of entries, the approved count, and
the not-approved count. It reminds the operator that the file is git-ignored.

## Quality harness command

```text
python -m tools.ste_linter.dictionary.quality DICTIONARY GOLDEN
```

### Harness arguments

- `DICTIONARY`: The path to the extracted dictionary JSON.
- `GOLDEN`: The path to the golden-set JSON.

### Harness output

A report with the per-field accuracy scores and every mismatch:

```text
Golden entries: 35
  keyword found:      35/35
  part of speech:     34/35
  approved status:    35/35
  alternatives:       33/35
Field accuracy: 97.1%

Mismatches:
  adopt        alternatives  expected [use]  actual [operate]
```

### Harness exit codes

- `0`: The field accuracy meets or beats the target.
- `1`: The field accuracy is below the target.

## Behavior contract

- Neither tool raises an unhandled exception for a readable input.
- The extractor produces the same output for the same PDF every run.
- The harness produces the same report for the same inputs every run.
