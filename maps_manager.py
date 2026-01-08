#!/usr/bin/env python3
"""
MapsManager - Standalone Interactive Map Viewer for Mist Networks

This module provides a standalone entry point for the Maps Manager functionality
that normally lives in MistHelper.py. It can be run independently or imported
by MistHelper for Menu 112 integration.

Architecture:
    - When imported by MistHelper.py: Uses the full MapsManager class from MistHelper
    - When run standalone: Imports MapsManager from MistHelper and provides CLI interface

Usage:
    Standalone:     python maps_manager.py [--org ORG_ID] [--site SITE_ID] [--viewer]
    As module:      Menu option 112 in MistHelper.py

Author: Joseph Morrison (jmorrison@juniper.net)
Version: 25.01.09.00.00
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging for standalone execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

def _check_and_import_mistapi():
    """Check and import mistapi with helpful error message if missing"""
    try:
        import mistapi
        return mistapi
    except ImportError:
        print("\n" + "=" * 60)
        print("MISSING DEPENDENCY: mistapi")
        print("=" * 60)
        print("\nThe 'mistapi' package is required but not installed.")
        print("\nInstall with:")
        print("  pip install mistapi")
        print("  or")
        print("  uv pip install mistapi")
        print("=" * 60)
        sys.exit(1)

def _check_visualization_dependencies():
    """Check for Plotly and Dash, return availability status"""
    plotly_available = False
    dash_available = False
    
    try:
        import plotly.graph_objects
        plotly_available = True
    except ImportError:
        pass
    
    try:
        from dash import Dash
        dash_available = True
    except ImportError:
        pass
    
    return plotly_available, dash_available

def _import_maps_manager():
    """Import MapsManager class from MistHelper.py"""
    try:
        from MistHelper import MapsManager
        logging.debug("MapsManager imported from MistHelper.py")
        return MapsManager
    except ImportError as e:
        print("\n" + "=" * 60)
        print("IMPORT ERROR")
        print("=" * 60)
        print(f"\nCould not import MapsManager from MistHelper.py")
        print(f"Error: {e}")
        print("\nEnsure MistHelper.py is in the same directory.")
        print("=" * 60)
        sys.exit(1)

# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MapsManager - Interactive Map Viewer for Mist Networks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python maps_manager.py                     # Interactive mode (menu)
    python maps_manager.py --viewer            # Launch interactive map viewer directly
    python maps_manager.py --org ORG_ID        # Specify organization
    python maps_manager.py --site SITE_ID      # Go directly to site
    python maps_manager.py --debug             # Enable debug logging
    
Environment Variables:
    MIST_API_TOKEN or MISTAPI_API_TOKEN        # API token (required)
    MIST_ORG_ID or MISTAPI_ORG_ID              # Default organization ID
        """
    )
    
    parser.add_argument('--org', '--org-id', dest='org_id',
                        help='Mist Organization ID')
    parser.add_argument('--site', '--site-id', dest='site_id',
                        help='Mist Site ID (skip site selection)')
    parser.add_argument('--map', '--map-id', dest='map_id',
                        help='Mist Map ID (skip map selection)')
    parser.add_argument('--viewer', action='store_true',
                        help='Launch interactive map viewer directly (Option 40)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--env', default='.env',
                        help='Path to .env file (default: .env)')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")
    
    print("\n" + "=" * 70)
    print("  MAPS MANAGER - Standalone Mode")
    print("  Interactive Map Viewer for Juniper Mist Networks")
    print("=" * 70)
    
    # Check visualization dependencies
    plotly_ok, dash_ok = _check_visualization_dependencies()
    if not plotly_ok or not dash_ok:
        print("\n  [!] Warning: Visualization dependencies missing")
        if not plotly_ok:
            print("      - plotly: NOT INSTALLED")
        else:
            print("      - plotly: OK")
        if not dash_ok:
            print("      - dash: NOT INSTALLED")
        else:
            print("      - dash: OK")
        print("\n  Install with: pip install plotly dash dash-bootstrap-components")
        
        if args.viewer:
            print("\n  Cannot launch viewer without dependencies. Exiting.")
            sys.exit(1)
        
        try:
            response = input("\n  Continue anyway? (limited functionality) [y/N]: ").strip().lower()
            if response != 'y':
                print("  Exiting...")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting...")
            sys.exit(0)
    else:
        print("\n  Visualization dependencies: OK")
    
    # Load environment variables
    mistapi = _check_and_import_mistapi()
    
    # Load .env file if exists
    env_path = args.env
    if os.path.exists(env_path):
        logging.info(f"Loading environment from {env_path}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            # Manual .env parsing
            with open(env_path, 'r') as env_file:
                for line in env_file:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
            logging.debug("Loaded .env manually (python-dotenv not installed)")
    
    # Get API credentials
    api_token = (
        os.environ.get('MIST_APITOKEN') or  # Legacy format (no underscore)
        os.environ.get('MIST_API_TOKEN') or  # Standard format
        os.environ.get('MISTAPI_API_TOKEN') or
        os.environ.get('MISTAPI_APITOKEN')
    )
    org_id = args.org_id or os.environ.get('MIST_ORG_ID') or os.environ.get('MISTAPI_ORG_ID') or os.environ.get('org_id')
    
    if not api_token:
        print("\n  [!] Error: No API token found.")
        print("  Set MIST_API_TOKEN in environment or .env file")
        print("  Or use: export MIST_API_TOKEN='your-token-here'")
        sys.exit(1)
    
    if not org_id:
        print("\n  [!] Error: No organization ID specified.")
        print("  Use --org ORG_ID or set MIST_ORG_ID in environment")
        sys.exit(1)
    
    # Initialize API session
    try:
        print("\n  Initializing Mist API session...")
        
        # Dynamically interrogate APISession signature to find correct token parameter
        import inspect
        apisession_cls = getattr(mistapi, 'APISession', None)
        if apisession_cls:
            try:
                sig_params = list(inspect.signature(apisession_cls).parameters.keys())
                logging.debug(f"mistapi.APISession accepted parameters: {sig_params}")
            except Exception:
                sig_params = []
        else:
            print("\n  [!] Error: mistapi.APISession not found")
            sys.exit(1)
        
        # Find the correct token parameter name
        token_param_names = [n for n in ['apitoken', 'api_token', 'token'] if n in sig_params]
        if not token_param_names:
            print("\n  [!] Error: Could not determine token parameter for mistapi")
            sys.exit(1)
        
        # Build session kwargs
        session_kwargs = {token_param_names[0]: api_token}
        if 'host' in sig_params:
            session_kwargs['host'] = 'api.mist.com'
        
        api_session = apisession_cls(**session_kwargs)
        logging.info(f"API session initialized with kwargs: {list(session_kwargs.keys())}")
        
        # Verify session by getting org info
        org_response = mistapi.api.v1.orgs.orgs.getOrg(api_session, org_id=org_id)
        if org_response.status_code != 200:
            print(f"\n  [!] Error: Could not access organization")
            print(f"      HTTP Status: {org_response.status_code}")
            if org_response.status_code == 401:
                print("      Check your API token is valid.")
            elif org_response.status_code == 403:
                print("      Your token may not have access to this organization.")
            sys.exit(1)
        
        org_name = org_response.data.get('name', 'Unknown')
        print(f"  Connected to: {org_name}")
        
    except Exception as e:
        print(f"\n  [!] Error initializing API session: {e}")
        logging.exception("API session initialization failed")
        sys.exit(1)
    
    # Import and initialize MapsManager from MistHelper
    MapsManager = _import_maps_manager()
    maps_manager = MapsManager(api_session, org_id)
    
    # Set site if specified
    if args.site_id:
        maps_manager.current_site_id = args.site_id
        # Try to get site name
        try:
            site_response = mistapi.api.v1.sites.sites.getSiteInfo(
                api_session, site_id=args.site_id
            )
            if site_response.status_code == 200:
                maps_manager.current_site_name = site_response.data.get('name', 'Unknown')
                print(f"  Site: {maps_manager.current_site_name}")
        except Exception:
            maps_manager.current_site_name = 'Unknown'
            print(f"  Site ID: {args.site_id}")
    
    # Launch directly to viewer or menu
    if args.viewer:
        print("\n  Launching Interactive Map Viewer...")
        print("=" * 70)
        
        # Ensure we have a site selected
        if not maps_manager.current_site_id:
            if not maps_manager.select_site():
                print("\n  [!] No site selected. Cannot launch viewer.")
                sys.exit(1)
        
        # Launch the interactive viewer (Menu option 40)
        maps_manager.interactive_map_viewer()
    else:
        # Run the full interactive menu
        print("=" * 70)
        maps_manager.run_interactive_menu()
    
    print("\n  Maps Manager session ended.")
    print("=" * 70)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

# When imported as a module, provide access to import MapsManager from MistHelper
def get_maps_manager_class():
    """Get the MapsManager class from MistHelper.py"""
    return _import_maps_manager()


if __name__ == "__main__":
    main()
