# Standalone Maps Manager

The Maps Manager is menu 142 in MistHelper. It also runs on its own from
`src/maps/maps_manager.py`.

## Quick Start

```powershell
# Through the MistHelper menu
python MistHelper.py -M 142

# Standalone. Launches the interactive viewer by default.
python src/maps/maps_manager.py

# Standalone with the operations menu instead of the viewer
python src/maps/maps_manager.py --menu

# Standalone against a specific organization
python src/maps/maps_manager.py --org YOUR_ORG_ID

# Debug mode
python src/maps/maps_manager.py --debug
```

## Command Line Options

| Flag | Description |
|------|-------------|
| `--menu` | Show the operations menu instead of launching the viewer directly |
| `--org ORG_ID` | Organization ID to use. Optional. |
| `--debug` | Enable debug logging |
| `--test` | Run a systematic test of the safe operations |

## Environment Variables

The standalone module reads from `.env` or environment variables:

- `MIST_API_TOKEN` or `MISTAPI_API_TOKEN` - API token (required)
- `MIST_ORG_ID` or `MISTAPI_ORG_ID` - Default organization ID

## Architecture

The `src/maps/maps_manager.py` module holds the `MapsManager` class.
`MistHelper.py` reaches it through `src/refactors/maps_manager_launcher.py`, so
both entry points share one implementation. This enables:

- Independent execution without loading the full MistHelper
- Direct access to the interactive map viewer for quick visualization
- Container-friendly deployment with minimal dependencies
