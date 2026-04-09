# Standalone Maps Manager

The Maps Manager (Menu 112, Option 40) can be run independently using `maps_manager.py`.

## Quick Start

```powershell
# Launch directly into interactive map viewer
python maps_manager.py --viewer

# Launch with specific site
python maps_manager.py --site YOUR_SITE_ID --viewer

# Full interactive menu
python maps_manager.py

# Debug mode
python maps_manager.py --debug --viewer
```

## Command Line Options

| Flag | Description |
|------|-------------|
| `--org ORG_ID` | Specify organization ID (overrides .env) |
| `--site SITE_ID` | Skip site selection, go directly to site |
| `--map MAP_ID` | Skip map selection (requires --site) |
| `--viewer` | Launch interactive Plotly/Dash map viewer directly |
| `--debug` | Enable debug logging |
| `--env PATH` | Path to .env file (default: .env) |

## Environment Variables

The standalone module reads from `.env` or environment variables:

- `MIST_API_TOKEN` or `MISTAPI_API_TOKEN` - API token (required)
- `MIST_ORG_ID` or `MISTAPI_ORG_ID` - Default organization ID

## Architecture

The `maps_manager.py` module imports `MapsManager` from `MistHelper.py`, maintaining a single source of truth. This avoids code duplication while enabling:

- Independent execution without loading the full MistHelper
- Direct access to the interactive map viewer for quick visualization
- Container-friendly deployment with minimal dependencies
