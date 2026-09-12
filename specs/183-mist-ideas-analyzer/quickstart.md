# Quickstart: Mist Ideas Analyzer

**Feature**: 183-mist-ideas-analyzer | **Date**: 2026-04-09

## Prerequisites

- Python 3.13+
- `openai>=1.0` and `python-dotenv` installed (included in `requirements.txt`)
- At least one AI backend configured in `.env` (see Configuration below)
- `mist_ideas.csv` in the project root

## Configuration

Add one of these AI backend configurations to your `.env` file:

```env
# Option 1 (preferred): GitHub Models
GITHUB_TOKEN=ghp_your_token_here

# Option 2: AVA MCP
AVA_API_URL=https://your-ava-endpoint.example.com

# Option 3: Generic OpenAI-compatible
AI_API_KEY=sk-your-key-here
AI_API_BASE_URL=https://api.openai.com/v1
```

The script auto-detects which backend is available in priority order: GitHub Models > AVA MCP > Generic.

## Usage

```powershell
# Basic run (analyzes all ideas, uses cache for previously analyzed ideas)
python scripts/mist_ideas_analyzer.py

# Force re-analysis of all ideas (ignore cache)
python scripts/mist_ideas_analyzer.py --refresh

# Rebuild the API index from local OpenAPI spec (only needed if spec file changes)
python scripts/mist_ideas_analyzer.py --refresh-index

# Specify a different CSV input file
python scripts/mist_ideas_analyzer.py --input path/to/other.csv
```

## Output Files

All output is written to the `data/` directory:

| File | Format | Description |
| - | - | - |
| `mist_ideas_analysis.md` | Markdown | Primary human-readable report with executive summary |
| `mist_ideas_analysis.json` | JSON | Machine-readable full structured analysis |
| `mist_ideas_analysis.csv` | CSV | Flat table with one row per idea cluster |

## Cache

Cached AI responses are stored in `data/mist_ideas_cache/`:
- `api_index.json` — pre-indexed OpenAPI endpoint lookup (built from `documentation/mist-api-openapi3json.json`)
- `{content_hash}.json` — per-idea AI response cache files

Delete the cache directory to force a complete re-analysis, or use `--refresh` to re-analyze while keeping the cache directory structure.

## Running Tests

```powershell
pytest tests/test_mist_ideas_analyzer.py -v
```
