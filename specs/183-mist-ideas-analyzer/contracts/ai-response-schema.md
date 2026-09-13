# AI Response Contract: Per-Idea Analysis

**Feature**: 183-mist-ideas-analyzer | **Date**: 2026-04-09

## Request

The script sends a chat completion request to the configured AI backend with:
- **System prompt**: Defines MistHelper scope, classification labels, GUI-vs-API rules, and response schema
- **User message**: Contains the idea title, description, comments summary, and relevant API endpoint summaries from the local OpenAPI index

## Response Schema

```json
{
  "classification": "REPORT_EXPORT | API_ENHANCEMENT | HYBRID | GUI_ONLY | HARDWARE_FEATURE | ALREADY_SUPPORTED | UNCLASSIFIED",
  "confidence": "high | medium | low",
  "themes": ["string"],
  "rationale": "string",
  "misthelper_enhancement": "string | null",
  "possible_duplicate_titles": ["string"],
  "is_foundational": true,
  "unlocks": ["string"],
  "ai_inspired_ideas": [
    {
      "title": "string",
      "description": "string",
      "source_idea_title": "string",
      "rationale": "string"
    }
  ]
}
```

### Field Constraints

| Field | Required | Constraint |
| - | - | - |
| classification | Yes | Must be exactly one of the 7 enum values |
| confidence | Yes | Must be exactly one of: high, medium, low |
| themes | Yes | Non-empty list; at least 1 theme tag |
| rationale | Yes | Non-empty string; minimum 20 characters |
| misthelper_enhancement | No | Null for GUI_ONLY, HARDWARE_FEATURE, ALREADY_SUPPORTED, UNCLASSIFIED; string for REPORT_EXPORT, API_ENHANCEMENT, HYBRID |
| possible_duplicate_titles | Yes | May be empty list; titles must be verbatim from the CSV |
| is_foundational | Yes | Boolean |
| unlocks | Yes | May be empty list; titles must be verbatim from the CSV |
| ai_inspired_ideas | Yes | May be empty list; each object must have all 4 fields |

### Validation Behavior

- If `classification` is not a valid enum value: retry the request once with a reminder
- If JSON parsing fails entirely: retry the request once; on second failure, log error and skip the idea
- If `rationale` is empty or too short: accept but log warning

## Dedup Batch Request Contract

### Request

Single chat completion with all idea titles and description excerpts for duplicate detection.

### Response Schema

```json
{
  "duplicate_groups": [
    {
      "canonical_title": "string",
      "duplicate_titles": ["string"],
      "merge_confidence": "high | medium | low"
    }
  ]
}
```

### Field Constraints

| Field | Required | Constraint |
| - | - | - |
| duplicate_groups | Yes | List of groups; ideas not in any group are unique |
| canonical_title | Yes | Must be a verbatim title from the input |
| duplicate_titles | Yes | Non-empty list; all must be verbatim titles from the input |
| merge_confidence | Yes | high, medium, or low |

### Validation Behavior

- Titles not found in the input dataset: log warning and skip that entry
- If `merge_confidence` is "low": create `possible_duplicate_of` cross-reference instead of forced merge
