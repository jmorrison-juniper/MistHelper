import subprocess
import sys
import concurrent.futures
import sqlite3
import os
from datetime import datetime, timezone

# List of required packages (pip names)
required_packages = [
    "mistapi",
    "websocket-client",
    "pyte",
    "requests",
    "prettytable",
    "tqdm",
    "sshkeyboard",
    "numpy",
    "python-dotenv"
]

# Mapping from pip package name to import name (if different)
import_name_map = {
    "websocket-client": "websocket",
    "python-dotenv": "dotenv",
    "prettytable": "prettytable",
    "tqdm": "tqdm",
    "sshkeyboard": "sshkeyboard",
    "numpy": "numpy",
    "mistapi": "mistapi",
    "pyte": "pyte",
    "requests": "requests"
}

def ensure_single_package_is_installed_and_up_to_date(package_name):
    """
    Ensures a single package is installed and up to date.
    """
    import_name = import_name_map.get(package_name, package_name)
    try:
        # Try importing the package to check if it's already installed
        __import__(import_name)
    except ImportError:
        # Install the package if not found
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # Try upgrading the package to the latest version
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Silently ignore upgrade errors
        pass

def ensure_all_required_packages_are_ready_with_status_bar(package_list):
    """
    Checks if each package is installed and up to date.
    Installs or upgrades as needed, showing a status bar.
    Uses multithreading for faster processing.
    """
    print("🔍 Checking and updating dependencies...", end="", flush=True)
    total = len(package_list)
    completed = [0]

    def update_status_bar():
        print(f"\r🔍 Checking and updating dependencies... ({completed[0]}/{total})", end="", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, total)) as executor:
        futures = [executor.submit(ensure_single_package_is_installed_and_up_to_date, pkg) for pkg in package_list]
        for future in concurrent.futures.as_completed(futures):
            completed[0] += 1
            update_status_bar()

    print("\r✅ Dependencies are ready.                      ")

# Check for --skip-deps flag early (before main argument parsing)
skip_deps = "--skip-deps" in sys.argv or "--help" in sys.argv or "-h" in sys.argv or "--test" in sys.argv

# Run the version check and upgrade for all dependencies (unless skipped)
if not skip_deps:
    ensure_all_required_packages_are_ready_with_status_bar(required_packages)

# Import all dependencies after ensuring installation
import mistapi
import csv
import ast
import json
import time
import logging
import os
import argparse
import inspect
import websocket
import threading
import re
import shutil
import pyte
import requests
import numpy as np
import math
from prettytable import PrettyTable
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
from sshkeyboard import listen_keyboard, stop_listening
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timestamp example usage
current_timestamp = {"timestamp": datetime.now(timezone.utc).isoformat()}


log_handler = RotatingFileHandler(
    filename='script.log',
    maxBytes=1_000_000_000,  # ~1 GB
    backupCount=2,           # Keep only the most recent log file
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[log_handler]
)

_api_usage_cache = {
    "timestamp": 0,
    "used": 0,
    "limit": 5000,
    "last_updated": 0,
    "perceived_requests": 0,
    "initialized": False 
}

current_epoch = int(time.time()) # Get the current epoch timestamp
past_epoch = current_epoch - 24 * 3600 # 24 hours * 3600 seconds/hour

device_type=str("all")
csv_file="stuff.csv"
fields = ["key", "display", "description"]

# Global state for integral control and JSON persistence
tuning_data_file = "tuning_data.json"

# Initialize API session with environment file
apisession = mistapi.APISession(env_file=".env",console_log_level=20,logging_log_level=20)
apisession.login()

org_id=None

# Load .env variables early so freshness can be set via .env
load_dotenv()
CSV_FRESHNESS_MINUTES = int(os.getenv("CSV_FRESHNESS_MINUTES", "15"))  # Default to 15 if not set

# Global configuration for output format (CSV or SQLite)
# Default to CSV for general use, can be overridden by CLI flag
OUTPUT_FORMAT = "csv"  # Valid values: "csv", "sqlite"
DATABASE_PATH = os.path.join("data", "mist_data.db")  # Path to hybrid SQLite database with natural primary keys

# ============================================================================
# ENDPOINT PRIMARY KEY STRATEGY CONFIGURATION
# ============================================================================
# This configuration determines how each API endpoint's data should be stored in SQLite
# with proper primary keys to eliminate artificial api_id fields and enable efficient queries
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # Type 1: Natural primary key using API id field (for entity APIs)
    # These APIs return objects with stable UUID identifiers that make perfect primary keys
    'getOrgInventory': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'site_id', 'mac', 'serial', 'model', 'type'],
        'unique_constraints': [],
        'description': 'Organization device inventory with stable UUID identifiers'
    },
    'listOrgSites': {
        'type': 'natural_pk', 
        'primary_key': ['id'],
        'indexes': ['org_id', 'name', 'country_code', 'address'],
        'unique_constraints': [],
        'description': 'Organization sites with stable UUID identifiers'
    },
    'listSiteDevices': {
        'type': 'natural_pk',
        'primary_key': ['id'], 
        'indexes': ['site_id', 'mac', 'serial', 'model', 'type', 'name'],
        'unique_constraints': [],
        'description': 'Site devices with stable UUID identifiers'
    },
    'getOrgDevices': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'site_id', 'mac', 'serial', 'model', 'type'],
        'unique_constraints': [],
        'description': 'Organization devices with stable UUID identifiers'
    },
    
    # Template and configuration entities
    'listOrgGatewayTemplates': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name', 'type'],
        'unique_constraints': [],
        'description': 'Gateway templates with stable UUID identifiers'
    },
    'listOrgNetworkTemplates': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name'],
        'unique_constraints': [],
        'description': 'Network templates with stable UUID identifiers'
    },
    'listOrgRfTemplates': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name', 'band'],
        'unique_constraints': [],
        'description': 'RF templates with stable UUID identifiers'
    },
    'listOrgSiteTemplates': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name'],
        'unique_constraints': [],
        'description': 'Site templates with stable UUID identifiers'
    },
    'listOrgAptemplates': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name'],
        'unique_constraints': [],
        'description': 'AP templates with stable UUID identifiers'
    },
    'listOrgSecPolicies': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name'],
        'unique_constraints': [],
        'description': 'Security policies with stable UUID identifiers'
    },
    'listOrgPsks': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name', 'ssid'],
        'unique_constraints': [],
        'description': 'Pre-shared keys with stable UUID identifiers'
    },
    'listOrgWebhooks': {
        'type': 'natural_pk',
        'primary_key': ['id'],
        'indexes': ['org_id', 'name', 'type'],
        'unique_constraints': [],
        'description': 'Webhooks with stable UUID identifiers'
    },
    
    # Type 2: Composite primary key for event and log APIs
    # These APIs return time-series data that requires composite keys for uniqueness
    'searchOrgAlarms': {
        'type': 'composite_pk',
        'primary_key': ['id', 'org_id', 'timestamp'],
        'indexes': ['org_id', 'timestamp', 'severity', 'type', 'site_id'],
        'unique_constraints': [],
        'description': 'Organization alarms with composite key for time-series data'
    },
    'searchOrgDeviceEvents': {
        'type': 'composite_pk',
        'primary_key': ['id', 'device_id', 'timestamp'],
        'indexes': ['device_id', 'timestamp', 'type', 'org_id', 'site_id'],
        'unique_constraints': [],
        'description': 'Device events with composite key for uniqueness'
    },
    'searchOrgClientEvents': {
        'type': 'composite_pk',
        'primary_key': ['id', 'site_id', 'timestamp'],
        'indexes': ['site_id', 'timestamp', 'type', 'client_mac', 'device_id'],
        'unique_constraints': [],
        'description': 'Client events with composite key for uniqueness'
    },
    'searchOrgSystemEvents': {
        'type': 'composite_pk',
        'primary_key': ['id', 'org_id', 'timestamp'],
        'indexes': ['org_id', 'timestamp', 'type'],
        'unique_constraints': [],
        'description': 'System events with composite key for uniqueness'
    },
    
    # Type 3: Composite key for statistics and metrics APIs
    # These APIs return aggregated data that benefits from composite keys
    'listOrgDevicesStats': {
        'type': 'composite_pk',
        'primary_key': ['device_id', 'timestamp'],
        'indexes': ['device_id', 'timestamp', 'org_id', 'site_id', 'type'],
        'unique_constraints': [],
        'description': 'Organization device statistics with composite key for metrics'
    },
    'searchSiteDeviceStats': {
        'type': 'composite_pk',
        'primary_key': ['device_id', 'timestamp'],
        'indexes': ['device_id', 'timestamp', 'site_id', 'type'],
        'unique_constraints': [],
        'description': 'Site device statistics with composite key for metrics'
    },
    'searchSiteClientStats': {
        'type': 'composite_pk',
        'primary_key': ['client_mac', 'timestamp'],
        'indexes': ['client_mac', 'timestamp', 'site_id', 'device_id'],
        'unique_constraints': [],
        'description': 'Site client statistics with composite key for metrics'
    },
    'searchOrgSwOrGwPorts': {
        'type': 'composite_pk',
        'primary_key': ['device_id', 'port_id', 'timestamp'],
        'indexes': ['device_id', 'port_id', 'timestamp', 'org_id'],
        'unique_constraints': [],
        'description': 'Switch/gateway port statistics with composite key'
    },
    'searchSitePortStats': {
        'type': 'composite_pk',
        'primary_key': ['device_id', 'port_id', 'timestamp'],
        'indexes': ['device_id', 'port_id', 'timestamp', 'site_id'],
        'unique_constraints': [],
        'description': 'Site port statistics with composite key'
    },
    'searchOrgPeerPathStats': {
        'type': 'composite_pk',
        'primary_key': ['from_device', 'to_device', 'timestamp'],
        'indexes': ['from_device', 'to_device', 'timestamp', 'org_id'],
        'unique_constraints': [],
        'description': 'Peer path statistics with composite key'
    },
    
    # Type 4: Client search APIs (special handling for large datasets)
    'searchOrgWirelessClients': {
        'type': 'composite_pk',
        'primary_key': ['mac', 'timestamp'],
        'indexes': ['mac', 'timestamp', 'site_id', 'device_id', 'ssid'],
        'unique_constraints': [],
        'description': 'Wireless client data with composite key for time-series'
    },
    'searchOrgWiredClients': {
        'type': 'composite_pk',
        'primary_key': ['mac', 'timestamp'],
        'indexes': ['mac', 'timestamp', 'site_id', 'device_id', 'port_id'],
        'unique_constraints': [],
        'description': 'Wired client data with composite key for time-series'
    },
    
    # Type 5: License and summary APIs (often aggregated data)
    'getOrgLicensesSummary': {
        'type': 'auto_increment_with_unique',
        'primary_key': ['misthelper_internal_id'],
        'indexes': ['org_id', 'sku', 'type'],
        'unique_constraints': [],
        'description': 'License summary data (aggregated, no stable primary key)'
    },
    
    # Default fallback strategy for unclassified endpoints
    # Uses auto-increment with unique constraint on API id field if present
    'default': {
        'type': 'auto_increment_with_unique',
        'primary_key': ['misthelper_internal_id'],
        'indexes': [],  # Will be determined at runtime based on available fields
        'unique_constraints': [],  # Will be applied if 'id' field exists in data
        'description': 'Fallback strategy with auto-increment primary key and unique constraint on API id'
    }
}

def check_and_generate_csv(file_name, generate_function, freshness_minutes=None):
    """
    Checks if a CSV file exists and is fresh (modified within the last `freshness_minutes`).
    If not, it runs the `generate_function` to regenerate the file.
    freshness_minutes is now settable via the .env file as CSV_FRESHNESS_MINUTES.
    """
    logging.debug(f"ENTRY: check_and_generate_csv(file_name={file_name}, generate_function={generate_function.__name__}, freshness_minutes={freshness_minutes})")
    
    if freshness_minutes is None:
        freshness_minutes = CSV_FRESHNESS_MINUTES
        
    # Get the full path to the CSV file in the data directory
    full_file_path = get_csv_file_path(file_name)
    
    # Check if the file already exists
    if os.path.exists(full_file_path):
        try:
            # Get the last modified time of the file
            file_mtime = datetime.fromtimestamp(os.path.getmtime(full_file_path))
            logging.debug(f"File I/O: Successfully read modification time for {full_file_path}: {file_mtime}")
            
            # Check if the file is still fresh
            if datetime.now() - file_mtime < timedelta(minutes=freshness_minutes):
                # Log that the cached file is being used
                logging.info(f"✅ Using cached {file_name} (fresh)")
                logging.debug(f"EXIT: check_and_generate_csv - using cached file")
                return True
            else:
                # Log that the file is stale and will be regenerated
                logging.info(f"♻️ {file_name} is older than {freshness_minutes} minutes. Regenerating...")
        except OSError as e:
            logging.error(f"File I/O: Failed to read modification time for {full_file_path}: {e}")
            logging.info(f"📄 {file_name} exists but cannot read metadata. Regenerating...")
    else:
        # Log that the file does not exist and will be generated
        logging.info(f"📄 {file_name} not found. Generating...")

    # Call the function to generate the file
    logging.info(f"🔄 Running {generate_function.__name__} to generate {file_name}...")
    try:
        generate_function()
        logging.info(f"✅ {file_name} generated or refreshed.")
        logging.debug(f"EXIT: check_and_generate_csv - file generated successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to generate {file_name} using {generate_function.__name__}: {e}")
        logging.debug(f"EXIT: check_and_generate_csv - generation failed")
        return False

def prepare_data_and_write_csv(data, filename, sort_key=None):
    """
    Flattens, sanitizes, optionally sorts, and writes data to a CSV file.
    """
    # Flatten nested dictionaries and lists
    data = flatten_nested_fields_in_list(data)
    
    # Escape multiline strings for CSV compatibility
    data = escape_multiline_strings_for_csv(data)
    
    # Sort data by the specified key if provided
    if sort_key:
        data = sorted(data, key=lambda x: x.get(sort_key, ""))
    
    # Write the processed data to a CSV file
    save_data_to_output(data, filename)

def display_dict_list_as_pretty_table(data, fields=None, sortby=None):
    """
    Displays a PrettyTable from a list of dictionaries.
    """
    # Return early if there's no data to display
    if not data:
        return

    # Use provided fields or extract all unique keys
    fields = fields or get_all_unique_dict_keys(data)

    # Initialize the PrettyTable with field names
    table = PrettyTable()
    table.field_names = fields

    # Set the sort column if it's valid
    if sortby and sortby in fields:
        table.sortby = sortby

    # Add each row of data to the table
    for item in data:
        row = [item.get(field, "") for field in fields]
        table.add_row(row)

    # Log the table as a string (debug mode only)
    logging.debug("\n" + table.get_string())

def interactive_fetch_device_data_to_csv(fetch_function, filename, description, device_type="all", site_id=None, device_id=None):
    """
    Fetches data for a specific device (by site_id/device_id if provided, else prompts user),
    writes the result to a CSV file, and displays it as a PrettyTable.
    """
    # Use provided site_id or prompt user
    if not site_id:
        site_id = prompt_select_site_id_from_csv()
        if not site_id:
            return

    # Use provided device_id or prompt user
    if not device_id:
        device_id = prompt_select_device_id_from_inventory(site_id, device_type=device_type)
        if not device_id:
            return

    # Log the action being performed
    logging.info(f"{description} for device ID: {device_id}")

    # Fetch data using the provided function
    stats = fetch_function(apisession, site_id, device_id).data

    # Flatten and sanitize the data
    stats = flatten_nested_fields_in_list([stats])
    stats = escape_multiline_strings_for_csv(stats)

    # Write the data to a CSV file
    save_data_to_output(stats, filename)

    # Display the data in a table
    display_dict_list_as_pretty_table(stats)

def process_and_merge_csv_for_sfp_address():
    """
    Processes OrgDevicePortStats.csv and AllDevicesWithSiteInfo.csv to merge SFP transceiver info
    with site and device address/location, outputting a new merged CSV.
    Only ports with a non-empty transceiver model are included.
    """
    logging.debug(f"ENTRY: process_and_merge_csv_for_sfp_address()")
    
    # Automatically generate missing files if needed
    org_port_stats_path = get_csv_file_path('OrgDevicePortStats.csv')
    devices_with_site_info_path = get_csv_file_path('AllDevicesWithSiteInfo.csv')
    
    if not os.path.exists(org_port_stats_path):
        print("⚠️ OrgDevicePortStats.csv not found. Generating it now...")
        logging.info("OrgDevicePortStats.csv not found. Generating it now...")
        export_device_port_stats_to_csv()

    if not os.path.exists(devices_with_site_info_path):
        print("⚠️ AllDevicesWithSiteInfo.csv not found. Generating it now...")
        logging.info("AllDevicesWithSiteInfo.csv not found. Generating it now...")
        export_devices_with_site_info_to_csv()

    try:
        # Load site and device info, keyed by MAC address
        logging.debug(f"File I/O: Reading {devices_with_site_info_path}")
        with open(devices_with_site_info_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            site_info = {
                row['mac']: {
                    'site_name': row.get('site_name', ''),
                    'site_address': row.get('site_address', ''),
                    'device_name': row.get('name', '')
                } for row in reader
            }
        logging.info(f"File I/O: Successfully loaded {len(site_info)} device entries from {devices_with_site_info_path}")

        # Merge with port stats, skipping rows with blank/null transceiver model
        merged_data = []
        logging.debug(f"File I/O: Reading {org_port_stats_path}")
        with open(org_port_stats_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                mac = row.get('mac')
                transceiver_model = row.get('xcvr_model', '').strip()
                if mac in site_info and transceiver_model:
                    merged_data.append({
                        'site_name': site_info[mac]['site_name'],
                        'site_address': site_info[mac]['site_address'],
                        'device_name': site_info[mac]['device_name'],
                        'port_id': row.get('port_id', ''),
                        'transceiver_part_number': row.get('xcvr_part_number', ''),
                        'transceiver_model': transceiver_model,
                        'transceiver_serial_number': row.get('xcvr_serial', '')
                    })
        logging.info(f"File I/O: Successfully processed port stats, found {len(merged_data)} ports with transceivers")

        # Write output to new CSV (this will automatically go to data folder via save_data_to_output)
        output_file = 'MergedTransceiverData.csv'
        save_data_to_output(merged_data, output_file)
        logging.info(f"File I/O: Successfully wrote {len(merged_data)} rows to {output_file}")
        print(f"✅ Merged data written to {output_file}")
        logging.debug(f"EXIT: process_and_merge_csv_for_sfp_address - success")
        
    except FileNotFoundError as e:
        logging.error(f"File I/O: Required CSV file not found: {e}")
        print(f"❌ Required CSV file not found: {e}")
        logging.debug(f"EXIT: process_and_merge_csv_for_sfp_address - file not found")
        raise
    except csv.Error as e:
        logging.error(f"File I/O: CSV processing error: {e}")
        print(f"❌ CSV processing error: {e}")
        logging.debug(f"EXIT: process_and_merge_csv_for_sfp_address - CSV error")
        raise
    except Exception as e:
        logging.error(f"File I/O: Unexpected error during CSV merge: {e}")
        print(f"❌ Unexpected error during CSV merge: {e}")
        logging.debug(f"EXIT: process_and_merge_csv_for_sfp_address - unexpected error")
        raise

def get_csv_file_path(filename):
    """
    Helper function to ensure consistent CSV file paths in the data directory.
    
    Args:
        filename (str): The CSV filename (with or without path)
    
    Returns:
        str: Full path to the CSV file in the data directory
    """
    # Ensure data directory exists
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # If filename already includes a path, use it as-is
    if os.path.dirname(filename):
        return filename
    
    # Otherwise, place it in the data directory
    return os.path.join(data_dir, filename)

def validate_site_id(site_id, function_name="unknown"):
    """
    Validates that site_id is not None or empty before making API calls.
    
    Args:
        site_id: The site ID to validate
        function_name: Name of the calling function for logging
    
    Returns:
        bool: True if valid, False otherwise
    
    Raises:
        ValueError: If site_id is None or empty
    """
    if site_id is None:
        error_msg = f"❌ site_id is None in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    if isinstance(site_id, str) and site_id.strip() == "":
        error_msg = f"❌ site_id is empty string in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    return True

def validate_device_id(device_id, function_name="unknown"):
    """
    Validates that device_id is not None or empty before making API calls.
    
    Args:
        device_id: The device ID to validate
        function_name: Name of the calling function for logging
    
    Returns:
        bool: True if valid, False otherwise
    
    Raises:
        ValueError: If device_id is None or empty
    """
    if device_id is None:
        error_msg = f"❌ device_id is None in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    if isinstance(device_id, str) and device_id.strip() == "":
        error_msg = f"❌ device_id is empty string in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    return True

def create_missing_csv_template(filename, headers=None, sample_data=None):
    """
    Creates a basic CSV file placeholder in the correct location.
    
    Args:
        filename (str): Name of the CSV file to create
        headers (list): List of header names (optional)
        sample_data (list): Optional list of sample data rows (optional)
    
    Returns:
        str: Full path to the created file
    """
    file_path = get_csv_file_path(filename)
    
    try:
        # Just create an empty file in the correct location
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if headers:
                writer = csv.writer(f)
                writer.writerow(headers)
            # Don't write sample data - user will add their own content
        
        logging.info(f"Created template file: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Failed to create template file {filename}: {e}")
        raise

def safe_api_call(api_function, *args, **kwargs):
    """
    Safely calls an API function and handles common error conditions.
    
    Args:
        api_function: The API function to call
        *args: Arguments to pass to the API function
        **kwargs: Keyword arguments to pass to the API function
    
    Returns:
        tuple: (success: bool, data: any, error: str)
    """
    try:
        response = api_function(*args, **kwargs)
        
        if not hasattr(response, 'data'):
            return False, None, "Response has no data attribute"
        
        if response.data is None:
            return False, None, "Response data is None"
        
        return True, response.data, None
        
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            return False, None, f"Endpoint not found (404): {error_str}"
        elif "403" in error_str:
            return False, None, f"Access denied (403): {error_str}"
        elif "429" in error_str:
            return False, None, f"Rate limited (429): {error_str}"
        else:
            return False, None, f"API error: {error_str}"

def get_cached_or_prompted_org_id():
    import os
    global org_id
    # 1. Check global variable
    if org_id:
        logging.info(f"✅ Using org_id from global variable: {org_id}")
        return org_id
    # 2. Check environment variable (set by dotenv or OS)
    org_id_env = os.environ.get("org_id") or os.environ.get("ORG_ID")
    if org_id_env:
        org_id = org_id_env
        logging.info(f"✅ Loaded org_id from environment: {org_id}")
        return org_id
    # 3. Fallback: Try to load from .env manually (rarely needed)
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("org_id="):
                    org_id = line.strip().split("=", 1)[1].strip().strip('"')
        if org_id:
            logging.info(f"✅ Loaded org_id from .env: {org_id}")
            return org_id
    except FileNotFoundError:
        logging.warning("⚠️ .env file not found.")
    # 4. Prompt if still not set
    logging.info("🔍 No org_id found in .env or CLI. Prompting user...")
    org_id_list = mistapi.cli.select_org(apisession)
    org_id = org_id_list[0]
    return org_id

def flatten_dict_recursively(d, parent_key='', sep='_'):
    """
    Recursively flattens a nested dictionary, joining keys with `sep`.
    Lists of dicts are flattened with indexed keys.
    Non-dict lists are joined as comma-separated strings.
    All keys are converted to strings for CSV/JSON compatibility.
    """
    items = []
    for k, v in d.items():
        k_str = str(k)
        new_key = f"{parent_key}{sep}{k_str}" if parent_key else k_str
        # If the value is a dictionary, recurse
        if isinstance(v, dict):
            items.extend(flatten_dict_recursively(v, new_key, sep=sep).items())
        # If the value is a list
        elif isinstance(v, list):
            if all(isinstance(i, dict) for i in v):
                # If all items are dicts, flatten each with an index
                for idx, item in enumerate(v):
                    items.extend(flatten_dict_recursively(item, f"{new_key}{sep}{idx}", sep=sep).items())
            else:
                # Otherwise, join list items as a comma-separated string
                items.append((new_key, ','.join(map(str, v))))
        else:
            # Base case: not a dict or list, just add the value
            items.append((new_key, v))
    # Uncomment the next line to enable debug logging of the flattening process
    # logging.debug(f"Flattened dict at key '{parent_key}': {dict(items)}")
    return dict(items)

def flatten_nested_fields_in_list(data):
    """
    Flattens all nested fields in a list of dictionaries.
    - Attempts to parse stringified dicts/lists.
    - Recursively flattens nested dicts and lists of dicts.
    - Joins non-dict lists as comma-separated strings.
    """
    flattened = []
    for entry in data:
        new_entry = {}
        for key, value in entry.items():
            # Try to parse stringified dicts/lists
            if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                try:
                    value = ast.literal_eval(value)
                    logging.debug(f"Parsed stringified value for key '{key}': {value}")
                except Exception:
                    try:
                        value = json.loads(value)
                        logging.debug(f"JSON loaded value for key '{key}': {value}")
                    except Exception:
                        # Leave as string if parsing fails
                        logging.debug(f"Failed to parse value for key '{key}', leaving as string.")

            # Flatten if it's a dict or list of dicts
            if isinstance(value, dict):
                # Recursively flatten nested dict
                flat = flatten_dict_recursively(value, parent_key=key)
                new_entry.update(flat)
                logging.debug(f"Flattened dict for key '{key}': {flat}")
            elif isinstance(value, list):
                if all(isinstance(i, dict) for i in value):
                    # Flatten each dict in the list with an index
                    for idx, item in enumerate(value):
                        flat = flatten_dict_recursively(item, parent_key=f"{key}_{idx}")
                        new_entry.update(flat)
                        logging.debug(f"Flattened dict in list for key '{key}_{idx}': {flat}")
                else:
                    # Join non-dict lists as comma-separated strings
                    new_entry[key] = ','.join(map(str, value))
                    logging.debug(f"Joined list for key '{key}': {new_entry[key]}")
            else:
                # Base case: not a dict or list, just add the value
                new_entry[key] = value
        flattened.append(new_entry)
    return flattened

def format_marvis_data_for_csv(api_response_data, analysis_type="generic"):
    """
    Optimized formatter for Marvis API responses to create readable CSV files.
    
    Args:
        api_response_data: Raw API response data from Marvis troubleshoot calls
        analysis_type: Type of analysis ("client", "device", "network", "sites")
    
    Returns:
        List of dictionaries optimized for CSV readability
    """
    try:
        # Handle different response structures
        if not api_response_data:
            logging.warning("Empty Marvis API response received")
            return []
        
        # Ensure we have a list to work with
        if not isinstance(api_response_data, list):
            data_list = [api_response_data]
        else:
            data_list = api_response_data
        
        formatted_data = []
        
        for item in data_list:
            if not isinstance(item, dict):
                logging.warning(f"Unexpected data type in Marvis response: {type(item)}")
                continue
            
            # Handle organization sites SLE data specially for readability
            if analysis_type == "sites" and "results" in item and isinstance(item["results"], list):
                logging.info(f"Processing organization sites SLE data with {len(item['results'])} sites")
                
                # Create one row per site instead of flattening all sites into one massive row
                for idx, site_data in enumerate(item["results"]):
                    site_row = {}
                    
                    # Add metadata from parent response
                    for meta_key in ["start", "end", "limit", "page", "total"]:
                        if meta_key in item:
                            site_row[meta_key] = item[meta_key]
                    
                    # Add site index for reference
                    site_row["site_index"] = idx
                    
                    # Add site data with clean column names
                    if isinstance(site_data, dict):
                        for key, value in site_data.items():
                            # Use clean column names instead of results_X_key format
                            clean_key = key.replace("-", "_")  # Replace hyphens for CSV compatibility
                            site_row[clean_key] = value
                    
                    formatted_data.append(site_row)
                
                logging.info(f"Converted {len(item['results'])} sites into {len(formatted_data)} readable rows")
                
            else:
                # Handle single troubleshoot results (client, device, network)
                formatted_row = {}
                
                # Add top-level metadata
                for key, value in item.items():
                    if key == "results" and isinstance(value, list):
                        # Handle results array - flatten each result with cleaner naming
                        for idx, result in enumerate(value):
                            if isinstance(result, dict):
                                for result_key, result_value in result.items():
                                    # Use clean column names: result_0_category instead of results_0_category
                                    clean_key = f"result_{idx}_{result_key.replace('-', '_')}"
                                    formatted_row[clean_key] = result_value
                            else:
                                formatted_row[f"result_{idx}"] = str(result)
                    elif isinstance(value, dict):
                        # Flatten nested dicts with clean naming
                        for nested_key, nested_value in value.items():
                            clean_key = f"{key}_{nested_key}".replace("-", "_")
                            formatted_row[clean_key] = nested_value
                    elif isinstance(value, list):
                        # Join lists as comma-separated values
                        formatted_row[key] = ",".join(map(str, value))
                    else:
                        # Direct assignment for simple values
                        formatted_row[key] = value
                
                if formatted_row:  # Only add if we have data
                    formatted_data.append(formatted_row)
        
        # Apply final CSV-friendly formatting
        formatted_data = escape_multiline_strings_for_csv(formatted_data)
        
        logging.info(f"Marvis data formatting complete: {len(formatted_data)} rows for {analysis_type} analysis")
        return formatted_data
        
    except Exception as e:
        logging.error(f"Error formatting Marvis data for CSV: {e}")
        # Fall back to old method if new formatting fails
        logging.info("Falling back to legacy flattening method")
        fallback_data = [api_response_data] if not isinstance(api_response_data, list) else api_response_data
        fallback_data = flatten_nested_fields_in_list(fallback_data)
        fallback_data = escape_multiline_strings_for_csv(fallback_data)
        return fallback_data

def convert_list_values_to_csv_strings(data):
    """
    Converts all list, tuple, or set values in a list of dictionaries to comma-separated strings.
    Adds debug logging for each conversion.
    """
    for entry in data:
        for key, value in entry.items():
            if isinstance(value, (list, tuple, set)):
                # Log the conversion for debugging
                logging.debug(f"Converting list/tuple/set at key '{key}' to string: {value}")
                entry[key] = ','.join(map(str, value))
    return data

def get_all_unique_dict_keys(data):
    """
    Returns a sorted list of all unique keys present in a list of dictionaries.
    Useful for determining CSV fieldnames or PrettyTable columns.
    """
    fields = set()
    for entry in data:
        # Add all keys from each dictionary to the set
        fields.update(entry.keys())
    # Log the discovered unique keys for debugging
    logging.debug(f"Discovered unique keys: {fields}")
    # Convert all keys to strings for sorting and CSV compatibility
    return sorted(str(f) for f in fields)

def escape_multiline_strings_for_csv(data):
    """
    Escapes multiline strings in a list of dictionaries for CSV compatibility.
    - Joins list values as comma-separated strings.
    - Replaces newline characters in strings with '\\n' and removes carriage returns.
    """
    for entry in data:
        for key, value in entry.items():
            if isinstance(value, list):
                # Convert list to comma-separated string for CSV compatibility
                logging.debug(f"Converting list at key '{key}' to string: {value}")
                entry[key] = ','.join(map(str, value))
            elif isinstance(value, str):
                # Replace newlines and carriage returns in strings
                if '\n' in value or '\r' in value:
                    logging.debug(f"Escaping newlines in string at key '{key}': {repr(value)}")
                entry[key] = value.replace('\n', '\\n').replace('\r', '')
    return data

def write_dict_list_to_csv(data, csv_file):
    """
    Writes a list of dictionaries to a CSV file.
    - Escapes multiline strings for CSV compatibility.
    - Determines all unique fields for the CSV header.
    - Writes each row, filling missing fields with empty strings.
    - Uses data directory for container persistence.
    """
    logging.debug(f"ENTRY: write_dict_list_to_csv(data_rows={len(data) if data else 0}, csv_file={csv_file})")
    
    if not data:
        logging.warning(f"No data provided to write to {csv_file}")
        logging.debug(f"EXIT: write_dict_list_to_csv - no data to write")
        return
        
    # Ensure data directory exists and construct proper file path
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # If csv_file doesn't already include a path, place it in the data directory
    if not os.path.dirname(csv_file):
        csv_file_path = os.path.join(data_dir, csv_file)
    else:
        csv_file_path = csv_file
        
    logging.debug(f"Preparing to write {len(data)} rows to {csv_file_path}...")
    data = escape_multiline_strings_for_csv(data)
    fields = get_all_unique_dict_keys(data)
    logging.debug(f"CSV fields determined: {fields}")

    try:
        logging.debug(f"File I/O: Attempting to open {csv_file_path} for writing")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            logging.debug(f"File I/O: Successfully wrote CSV header to {csv_file_path}")
            
            for idx, row in enumerate(data):
                writer.writerow({field: row.get(field, "") for field in fields})
                if idx < 3:  # Log the first few rows for debugging
                    logging.debug(f"Row {idx} written: {row}")
                    
        logging.info(f"File I/O: Successfully wrote {len(data)} rows to {csv_file_path}")
        logging.debug(f"EXIT: write_dict_list_to_csv - success")
        
    except PermissionError as e:
        logging.error(f"File I/O: Permission denied when writing to {csv_file_path}: {e}")
        print(f"❌ Cannot write to {csv_file_path}. Is it open in another program?")
        logging.debug(f"EXIT: write_dict_list_to_csv - permission error")
        raise
    except OSError as e:
        logging.error(f"File I/O: OS error when writing to {csv_file_path}: {e}")
        logging.debug(f"EXIT: write_dict_list_to_csv - OS error")
        raise
    except Exception as e:
        logging.error(f"File I/O: Unexpected error when writing to {csv_file}: {e}")
        logging.debug(f"EXIT: write_dict_list_to_csv - unexpected error")
        raise


def determine_api_function_name_from_context():
    """
    Attempts to determine the API function name from the current call stack.
    This helps identify which endpoint strategy to use for table schema.
    
    Returns:
        str: The API function name if found, else 'unknown'
    """
    import inspect
    
    # Look through the call stack for known API function patterns
    frame = inspect.currentframe()
    try:
        while frame:
            function_name = frame.f_code.co_name
            # Check if this looks like an API function name
            if any(pattern in function_name for pattern in [
                'getOrg', 'listOrg', 'searchOrg', 'getSite', 'listSite', 'searchSite'
            ]):
                logging.debug(f"Detected API function name from stack: {function_name}")
                return function_name
            frame = frame.f_back
    except Exception as e:
        logging.debug(f"Error determining API function name: {e}")
    finally:
        del frame
    
    return 'unknown'

def get_endpoint_strategy(api_function_name, data_fields):
    """
    Determines the appropriate database schema strategy for an API endpoint.
    
    Args:
        api_function_name (str): Name of the API function being called
        data_fields (list): List of field names in the data
    
    Returns:
        dict: Strategy configuration including primary key, indexes, etc.
    """
    # First check if we have a specific strategy for this endpoint
    if api_function_name in ENDPOINT_PRIMARY_KEY_STRATEGIES:
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_function_name].copy()
        logging.debug(f"Using configured strategy for {api_function_name}: {strategy['type']}")
        return strategy
    
    # If no specific strategy, use intelligent defaults based on data structure
    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES['default'].copy()
    
    # Enhance default strategy based on available fields
    if 'id' in data_fields:
        # If data has an 'id' field, use it as unique constraint
        strategy['unique_constraints'] = ['id']
        strategy['indexes'] = ['id']
        logging.debug(f"Enhanced default strategy for {api_function_name}: adding unique constraint on 'id'")
    
    # Add common indexes for frequently queried fields
    common_index_fields = ['org_id', 'site_id', 'device_id', 'timestamp', 'mac', 'serial']
    for field in common_index_fields:
        if field in data_fields and field not in strategy['indexes']:
            strategy['indexes'].append(field)
    
    logging.debug(f"Using enhanced default strategy for {api_function_name}: {strategy}")
    return strategy

def build_create_table_sql(table_name, fields, strategy):
    """
    Builds the CREATE TABLE SQL statement based on the endpoint strategy.
    
    Args:
        table_name (str): Name of the table to create
        fields (list): List of field names from the data
        strategy (dict): Strategy configuration for this endpoint
    
    Returns:
        str: Complete CREATE TABLE SQL statement
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Sanitize table name
    safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
    if not safe_table_name or safe_table_name[0].isdigit():
        safe_table_name = f"table_{safe_table_name}"
    
    # Start building SQL
    if strategy['type'] == 'natural_pk':
        # Use API id field(s) as primary key
        pk_fields = strategy['primary_key']
        sql_parts = [f"CREATE TABLE IF NOT EXISTS {safe_table_name} ("]
        
        # Add all fields, with primary key fields getting special treatment
        field_definitions = []
        for field in fields:
            safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            if field in pk_fields:
                field_definitions.append(f"{safe_field} TEXT NOT NULL")
            else:
                field_definitions.append(f"{safe_field} TEXT")
        
        # Add metadata fields
        field_definitions.append("misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP")
        field_definitions.append("misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP")
        
        sql_parts.append(", ".join(field_definitions))
        
        # Add primary key constraint
        pk_constraint = f"PRIMARY KEY ({', '.join(pk_fields)})"
        sql_parts.append(f", {pk_constraint}")
        
        sql_parts.append(")")
        create_sql = "".join(sql_parts)
        
    elif strategy['type'] == 'composite_pk':
        # Use composite primary key
        pk_fields = strategy['primary_key']
        sql_parts = [f"CREATE TABLE IF NOT EXISTS {safe_table_name} ("]
        
        field_definitions = []
        for field in fields:
            safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            if field in pk_fields:
                field_definitions.append(f"{safe_field} TEXT NOT NULL")
            else:
                field_definitions.append(f"{safe_field} TEXT")
        
        # Add metadata fields
        field_definitions.append("misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP")
        field_definitions.append("misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP")
        
        sql_parts.append(", ".join(field_definitions))
        
        # Add composite primary key constraint
        available_pk_fields = [f for f in pk_fields if f in fields]
        if available_pk_fields:
            pk_constraint = f"PRIMARY KEY ({', '.join(available_pk_fields)})"
            sql_parts.append(f", {pk_constraint}")
        
        sql_parts.append(")")
        create_sql = "".join(sql_parts)
        
    else:  # auto_increment_with_unique
        # Use auto-increment primary key with unique constraints
        sql_parts = [f"CREATE TABLE IF NOT EXISTS {safe_table_name} ("]
        
        field_definitions = ["misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT"]
        
        for field in fields:
            safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            field_definitions.append(f"{safe_field} TEXT")
        
        # Add metadata fields
        field_definitions.append("misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP")
        field_definitions.append("misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP")
        
        sql_parts.append(", ".join(field_definitions))
        
        # Add unique constraints if specified
        unique_fields = [f for f in strategy['unique_constraints'] if f in fields]
        if unique_fields:
            for field in unique_fields:
                safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
                sql_parts.append(f", UNIQUE({safe_field})")
        
        sql_parts.append(")")
        create_sql = "".join(sql_parts)
    
    logging.debug(f"Generated CREATE TABLE SQL for {safe_table_name}: {create_sql[:100]}...")
    return create_sql

def build_indexes_sql(table_name, fields, strategy):
    """
    Builds CREATE INDEX SQL statements for the specified strategy.
    
    Args:
        table_name (str): Name of the table
        fields (list): Available fields in the data
        strategy (dict): Strategy configuration
    
    Returns:
        list: List of CREATE INDEX SQL statements
    """
    safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
    if not safe_table_name or safe_table_name[0].isdigit():
        safe_table_name = f"table_{safe_table_name}"
    
    index_sqls = []
    
    # Create indexes for fields specified in strategy
    for field in strategy.get('indexes', []):
        if field in fields:
            safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            index_name = f"idx_{safe_table_name}_{safe_field}"
            index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {safe_table_name} ({safe_field})"
            index_sqls.append(index_sql)
    
    return index_sqls

def write_dict_list_to_sqlite_database_inside_container(data, table_name, api_function_name=None):
    """
    Writes a list of dictionaries to a SQLite database table using hybrid primary key strategies.
    This new implementation eliminates artificial api_id fields and uses proper business keys.
    Follows NASA/JPL coding standards with comprehensive logging and error handling.
    
    Args:
        data (list): List of dictionaries containing the data to write
        table_name (str): Name of the database table to write to
        api_function_name (str, optional): Name of the API function for strategy selection
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Entry logging with enhanced input validation
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.debug(f"ENTRY: write_dict_list_to_sqlite_database_inside_container(data_rows={len(data) if data else 0}, table_name={table_name}, api_function_name={api_function_name}) at {timestamp}")
    
    # Input validation - Check if data is provided and is a list
    if not data:
        logging.warning(f"No data provided to write to table {table_name} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - no data to write")
        return False
        
    if not isinstance(data, list):
        logging.error(f"Invalid data type: expected list, got {type(data)} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - invalid data type")
        return False
        
    # Input validation - Check table name
    if not table_name or not isinstance(table_name, str):
        logging.error(f"Invalid table name: {table_name} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - invalid table name")
        return False
    
    # Determine API function name if not provided
    if not api_function_name:
        api_function_name = determine_api_function_name_from_context()
        
    logging.debug(f"Processing {len(data)} rows for table {table_name} using API function {api_function_name} at {timestamp}")
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created database directory: {db_dir} at {timestamp}")
        except OSError as e:
            logging.error(f"Failed to create database directory {db_dir}: {e} at {timestamp}")
            logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - directory creation failed")
            return False
    
    # Process data to handle formatting for database storage
    try:
        processed_data = escape_multiline_strings_for_csv(data)
        logging.debug(f"Successfully processed data for SQLite compatibility at {timestamp}")
    except Exception as e:
        logging.error(f"Failed to process data: {e} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - data processing failed")
        return False
    
    # Get all unique fields and determine strategy
    try:
        fields = get_all_unique_dict_keys(processed_data)
        if not fields:
            logging.error(f"No fields found in data for table {table_name} at {timestamp}")
            logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - no fields")
            return False
        
        strategy = get_endpoint_strategy(api_function_name, fields)
        logging.info(f"Using hybrid SQLite strategy '{strategy['type']}' for table {table_name}: {strategy['description']}")
        logging.debug(f"Database fields determined: {fields} at {timestamp}")
        logging.debug(f"Endpoint {api_function_name} mapped to {strategy['type']} strategy - eliminates need for artificial api_id fields")
        
    except Exception as e:
        logging.error(f"Failed to determine fields and strategy: {e} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - field determination failed")
        return False
    
    # Database operations with comprehensive error handling
    connection = None
    try:
        # Connect to SQLite database
        logging.debug(f"Attempting to connect to database: {DATABASE_PATH} at {timestamp}")
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        logging.info(f"Successfully connected to database: {DATABASE_PATH} at {timestamp}")
        
        # Create table with strategy-appropriate schema
        create_table_sql = build_create_table_sql(table_name, fields, strategy)
        cursor.execute(create_table_sql)
        logging.debug(f"Table {table_name} created/verified with hybrid {strategy['type']} schema - using natural business keys from API")
        
        # Create indexes for performance
        index_sqls = build_indexes_sql(table_name, fields, strategy)
        for index_sql in index_sqls:
            cursor.execute(index_sql)
        if index_sqls:
            logging.debug(f"Created {len(index_sqls)} performance indexes for table {table_name} with {strategy['type']} strategy")
        
        # Determine insert strategy based on schema type
        if strategy['type'] in ['natural_pk', 'composite_pk']:
            # Use REPLACE for natural and composite keys to handle updates gracefully
            insert_mode = "INSERT OR REPLACE"
            logging.debug(f"Using REPLACE mode for {strategy['type']} strategy - enables efficient upsert operations with natural keys")
        else:
            # Clear table for auto-increment strategy (fallback for unclassified endpoints)
            cursor.execute(f"DELETE FROM {re.sub(r'[^a-zA-Z0-9_]', '_', table_name)}")
            insert_mode = "INSERT"
            logging.debug(f"Cleared existing data and using INSERT mode for auto-increment fallback strategy")
        
        # Prepare field mapping
        safe_fields = []
        for field in fields:
            safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            safe_fields.append(safe_field)
        
        # Add metadata fields
        safe_fields.extend(["misthelper_created_time", "misthelper_updated_time"])
        
        # Insert data rows
        current_time = datetime.now(timezone.utc).isoformat()
        successful_inserts = 0
        
        for idx, row in enumerate(processed_data):
            try:
                # Prepare values for insertion
                values = []
                for field in fields:
                    value = row.get(field, "")
                    # Convert value to string for TEXT storage
                    if value is None:
                        value = ""
                    else:
                        value = str(value)
                    values.append(value)
                
                # Add metadata values
                values.extend([current_time, current_time])
                
                # Create parameterized query for safety
                placeholders = ", ".join(["?"] * len(values))
                safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
                if not safe_table_name or safe_table_name[0].isdigit():
                    safe_table_name = f"table_{safe_table_name}"
                
                insert_sql = f"{insert_mode} INTO {safe_table_name} ({', '.join(safe_fields)}) VALUES ({placeholders})"
                
                cursor.execute(insert_sql, values)
                successful_inserts += 1
                
                # Log first few rows for debugging
                if idx < 3:
                    logging.debug(f"Row {idx} inserted into {table_name} using {insert_mode} at {timestamp}")
                    
            except Exception as e:
                logging.error(f"Failed to insert row {idx} into {table_name}: {e} at {timestamp}")
                # Continue with other rows rather than failing completely
                continue
        
        # Commit transaction
        connection.commit()
        logging.info(f"Successfully wrote {successful_inserts}/{len(processed_data)} rows to table {table_name} in database {DATABASE_PATH} using {strategy['type']} strategy at {timestamp}")
        
        # Verify data was written
        safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        if not safe_table_name or safe_table_name[0].isdigit():
            safe_table_name = f"table_{safe_table_name}"
        cursor.execute(f"SELECT COUNT(*) FROM {safe_table_name}")
        row_count = cursor.fetchone()[0]
        logging.info(f"Database verification: {row_count} rows confirmed in table {table_name} at {timestamp}")
        
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - success")
        return True
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error when writing to {table_name}: {e} at {timestamp}")
        if connection:
            try:
                connection.rollback()
                logging.debug(f"Transaction rolled back for table {table_name} at {timestamp}")
            except Exception as rollback_error:
                logging.error(f"Failed to rollback transaction: {rollback_error} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - SQLite error")
        return False
        
    except Exception as e:
        logging.error(f"Unexpected error when writing to table {table_name}: {e} at {timestamp}")
        if connection:
            try:
                connection.rollback()
                logging.debug(f"Transaction rolled back for table {table_name} at {timestamp}")
            except Exception as rollback_error:
                logging.error(f"Failed to rollback transaction: {rollback_error} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - unexpected error")
        return False
        
    finally:
        # Always close database connection (safety-critical: resource cleanup)
        if connection:
            try:
                connection.close()
                logging.debug(f"Database connection closed for table {table_name} at {timestamp}")
            except Exception as e:
                logging.error(f"Failed to close database connection: {e} at {timestamp}")


def write_data_with_format_selection(data, filename_or_table, format_override=None, api_function_name=None):
    """
    Writes data to either CSV or SQLite database based on global OUTPUT_FORMAT or override.
    Follows NASA/JPL coding standards with comprehensive logging.
    
    Args:
        data (list): List of dictionaries containing the data to write
        filename_or_table (str): CSV filename or database table name
        format_override (str): Optional override for output format ("csv" or "sqlite")
        api_function_name (str, optional): Name of the API function for SQLite strategy selection
    
    Returns:
        bool: True if successful, False otherwise
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.debug(f"ENTRY: write_data_with_format_selection(data_rows={len(data) if data else 0}, filename_or_table={filename_or_table}, format_override={format_override}, api_function_name={api_function_name}) at {timestamp}")
    
    # Determine output format (format_override takes precedence over global setting)
    output_format = format_override if format_override else OUTPUT_FORMAT
    
    # Input validation
    if not data:
        logging.warning(f"No data provided for output to {filename_or_table} at {timestamp}")
        logging.debug(f"EXIT: write_data_with_format_selection - no data")
        return False
        
    if output_format not in ["csv", "sqlite"]:
        logging.error(f"Invalid output format: {output_format}. Must be 'csv' or 'sqlite' at {timestamp}")
        logging.debug(f"EXIT: write_data_with_format_selection - invalid format")
        return False
    
    try:
        if output_format == "csv":
            # Ensure CSV files have .csv extension
            csv_filename = filename_or_table if filename_or_table.endswith('.csv') else f"{filename_or_table}.csv"
            logging.info(f"Writing {len(data)} rows to CSV file: {csv_filename} at {timestamp}")
            write_dict_list_to_csv(data, csv_filename)
            logging.debug(f"EXIT: write_data_with_format_selection - CSV success")
            return True
        else:  # sqlite
            # Convert filename to table name (remove .csv extension if present)
            table_name = filename_or_table
            if table_name.endswith('.csv'):
                table_name = table_name[:-4]  # Remove .csv extension
            
            logging.info(f"Writing {len(data)} rows to SQLite table: {table_name} using API function {api_function_name} at {timestamp}")
            result = write_dict_list_to_sqlite_database_inside_container(data, table_name, api_function_name=api_function_name)
            logging.debug(f"EXIT: write_data_with_format_selection - SQLite {'success' if result else 'failed'}")
            return result
            
    except Exception as e:
        logging.error(f"Failed to write data to {filename_or_table} in {output_format} format: {e} at {timestamp}")
        logging.debug(f"EXIT: write_data_with_format_selection - exception")
        return False


def save_data_to_output(data, filename, api_function_name=None):
    """
    Wrapper function to replace write_dict_list_to_csv calls.
    Routes to appropriate output format based on global OUTPUT_FORMAT setting.
    
    Args:
        data (list): List of dictionaries containing the data to write
        filename (str): CSV filename or database table name
        api_function_name (str, optional): Name of the API function for SQLite strategy selection
    """
    return write_data_with_format_selection(data, filename, api_function_name=api_function_name)

def fetch_and_display_api_data(title, api_call, filename, sort_key=None, display_fields=None, **kwargs):
    """
    Fetches data using the provided API call, processes it (flattening, sorting, escaping),
    writes it to a CSV file, and displays it in a PrettyTable. Adds detailed logging.
    Handles API rate limiting (HTTP 429) by saving partial results and exiting gracefully.
    """
    import http.client

    logging.debug(f"ENTRY: fetch_and_display_api_data(title={title}, api_call={api_call.__name__}, filename={filename}, sort_key={sort_key}, display_fields={display_fields}, kwargs={kwargs})")
    
    logging.info(f"Starting data fetch: {title}")
    print(title)
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id}")
    smoothed = None

    rawdata = []
    try:
        # Call the API and get all paginated results
        logging.debug(f"Making API call: {api_call.__name__} with kwargs: {kwargs}")
        response = api_call(apisession, org_id, **kwargs)
        smoothed, delay = get_rate_limited_delay(smoothed)
        logging.debug(f"Applying rate limit delay: {delay:.2f}s")
        time.sleep(delay)
        
        try:
            rawdata = mistapi.get_all(response=response, mist_session=apisession)
            logging.debug(f"API call successful, retrieved {len(rawdata) if rawdata else 0} raw records")
        except Exception as e:
            # Remove references to device_id and site_id, which are not defined in this scope
            logging.error(f"Exception occurred during API data retrieval: {e}")
            print(f"❌ Exception occurred during API call: {e}")
            # Handle HTTP 429 (rate limit exceeded)
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code == 429:
                logging.warning("API rate limit (HTTP 429) reached. Saving partial results and exiting.")
                if rawdata:
                    save_data_to_output(rawdata, filename, api_function_name=api_call.__name__)
                    logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows) using {api_call.__name__} strategy.")
                logging.debug(f"EXIT: fetch_and_display_api_data - rate limited")
                return
            else:
                logging.debug(f"EXIT: fetch_and_display_api_data - API error")
                raise

        if rawdata is None:
            logging.warning(f"⚠️ No data returned from API for {title}. Skipping.")
            logging.debug(f"EXIT: fetch_and_display_api_data - no data")
            return

        logging.info(f"Fetched {len(rawdata)} raw records from API.")

        # Filter out non-dict entries (defensive)
        data = [entry for entry in rawdata if isinstance(entry, dict)]
        logging.debug(f"Filtered to {len(data)} dict records.")

        # Sort data if a sort key is provided
        if sort_key:
            data = sorted(data, key=lambda x: x.get(sort_key, ""))
            logging.debug(f"Data sorted by key: {sort_key}")

        # Flatten nested fields for CSV compatibility
        data = flatten_nested_fields_in_list(data)
        logging.debug("Flattened all nested fields.")

        # Escape multiline strings for CSV
        data = escape_multiline_strings_for_csv(data)
        logging.debug("Escaped multiline strings.")

        # Determine all unique fields for CSV and table display
        fields = get_all_unique_dict_keys(data)
        logging.debug(f"Unique fields for CSV/table: {fields}")

        # Write processed data to output with API function name for strategy selection
        save_data_to_output(data, filename, api_function_name=api_call.__name__)
        logging.info(f"Data written to {filename} ({len(data)} rows) using {api_call.__name__} strategy.")

        # Prepare and display PrettyTable
        table = PrettyTable()
        table.field_names = display_fields if display_fields else fields
        table.valign = "t"
        for item in tqdm(data, desc="Processing", unit="record"):
            row = [item.get(field, "") for field in table.field_names]
            table.add_row(row)
        logging.debug("\n" + table.get_string())
        logging.debug(f"EXIT: fetch_and_display_api_data - success")

    except Exception as e:
        logging.error(f"❌ Error during data fetch for {title}: {e}")
        # Always save whatever data was collected so far
        if rawdata:
            save_data_to_output(rawdata, filename, api_function_name=api_call.__name__)
            logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows) using {api_call.__name__} strategy.")
        logging.debug(f"EXIT: fetch_and_display_api_data - error")
        raise

def prompt_select_device_id_from_inventory(site_id, device_type="all", csv_filename="SiteInventory.csv"):
    """
    Prompts the user to select a device by index or name from the device inventory at a given site.
    Returns the corresponding device ID, or None if not found.
    """
    # Fetch device inventory for the specified site and device type
    rawdata = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type=device_type).data
    if not rawdata:
        print("No devices found for the selected site.")
        logging.warning(f"No devices found for site_id: {site_id} with device_type: {device_type}")
        return None

    # Sort, flatten, and sanitize the inventory data for display and CSV export
    inventory = sorted(rawdata, key=lambda x: x.get("model", ""))
    inventory = flatten_nested_fields_in_list(inventory)
    inventory = escape_multiline_strings_for_csv(inventory)
    save_data_to_output(inventory, csv_filename)
    logging.info(f"Device inventory for site_id {site_id} written to {csv_filename}")

    # Prepare PrettyTable for user selection
    table = PrettyTable()
    table.field_names = ["Index", "name", "mac", "model", "serial"]
    index_to_device = {}
    name_to_device = {}

    # Populate the table and lookup dictionaries
    for idx, item in enumerate(inventory):
        table.add_row([idx, item.get("name", ""), item.get("mac", ""), item.get("model", ""), item.get("serial", "")])
        index_to_device[idx] = item
        name_to_device[item.get("name", "")] = item

    print(table)
    logging.info("Displayed device selection table to user.")

    user_input = input("Enter the index or name of the device to view device: ").strip()
    logging.debug(f"User input for device selection: {user_input}")

    # Try index selection
    if user_input.isdigit():
        idx = int(user_input)
        if idx in index_to_device:
            device_id = index_to_device[idx].get("id")
            logging.info(f"User selected device by index: {idx} (device_id: {device_id})")
            return device_id
        else:
            logging.error("❌ Invalid index.")
            return None

    # Try name selection
    if user_input in name_to_device:
        device_id = name_to_device[user_input].get("id")
        logging.info(f"User selected device by name: {user_input} (device_id: {device_id})")
        return device_id

    logging.error("❌ Device not found by name or index.")
    return None

def show_site_device_inventory(site_id, device_type="all", csv_filename="SiteInventory.csv"):
    """
    Fetches and displays the device inventory for a given site.
    - site_id: The ID of the site to fetch inventory for.
    - device_type: The type of device to filter (default: "all").
    - csv_filename: The filename to write the inventory CSV to.
    """
    logging.info(f"Fetching device inventory for site_id={site_id}, device_type={device_type}")
    rawdata = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type=device_type).data
    if not rawdata:
        print("No devices found for the selected site.")
        logging.warning(f"No devices found for site_id={site_id} with device_type={device_type}")
        return

    # Sort inventory by model for easier viewing
    inventory = sorted(rawdata, key=lambda x: x.get("model", ""))
    # Flatten nested fields for CSV and table compatibility
    inventory = flatten_nested_fields_in_list(inventory)
    # Escape multiline strings for CSV compatibility
    inventory = escape_multiline_strings_for_csv(inventory)
    # Get all unique fields for CSV/table columns
    fields = get_all_unique_dict_keys(inventory)
    # Write inventory to CSV
    save_data_to_output(inventory, csv_filename)
    logging.info(f"Device inventory written to {csv_filename} ({len(inventory)} rows)")

    # Prepare PrettyTable for display
    table = PrettyTable()
    table.field_names = fields

    # Attempt to sort the table by 'model' if present
    if "model" in fields:
        try:
            table.sortby = "model"
        except Exception as e:
            logging.warning(f"⚠️ Could not sort table by 'model': {e}")

    # Add each device as a row in the table
    for item in inventory:
        row = [item.get(field, "") for field in fields]
        table.add_row(row)

    # Log the table output for reference (debug mode only)
    logging.debug("\n" + table.get_string())

def prompt_select_site_id_from_csv(csv_file="SiteList.csv"):
    """
    Prompts the user to select a site by index or name from SiteList.csv.
    Returns the corresponding site ID.
    """
    # Ensure the site list CSV is fresh or generate it if missing/stale
    check_and_generate_csv(csv_file, export_all_sites_to_csv)

    # Get the full path to the CSV file in the data directory
    csv_file_path = get_csv_file_path(csv_file)
    
    # Load the site list from CSV
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = list(csv.DictReader(file))
        index_to_site = {i: row for i, row in enumerate(reader)}
        name_to_site = {row["name"]: row for row in reader if "name" in row}

    # Display available sites to the user
    print("\nAvailable Sites:")
    for idx, row in index_to_site.items():
        print(f"[{idx}] {row.get('name', 'Unnamed')}")

    user_input = input("\nEnter site index or name: ").strip()
    logging.debug(f"User input for site selection: {user_input}")

    # Try index selection
    if user_input.isdigit():
        idx = int(user_input)
        if idx in index_to_site:
            site_id = index_to_site[idx].get("id")
            print(f"✅ Selected site: {index_to_site[idx].get('name')} (ID: {site_id})")
            logging.info(f"User selected site by index: {idx} (site_id: {site_id})")
            return site_id
        else:
            print("❌ Invalid index.")
            logging.warning(f"Invalid site index entered: {idx}")
            return None

    # Try name selection
    if user_input in name_to_site:
        site_id = name_to_site[user_input].get("id")
        print(f"✅ Selected site: {user_input} (ID: {site_id})")
        logging.info(f"User selected site by name: {user_input} (site_id: {site_id})")
        return site_id

    print("❌ Site not found by name or index.")
    logging.warning(f"Site not found by name or index: {user_input}")
    return None

def prompt_and_log_site_selection():
    """
    Prompts the user to select a site from the CSV list and logs the selection.
    """
    logging.info("Prompting user to select a site from SiteList.csv...")
    site_id = prompt_select_site_id_from_csv()
    if site_id:
        logging.info(f"✅ Selected site ID: {site_id}")
        # You can store or use the selected site_id as needed here
    else:
        logging.error("❌ No site selected. User may have entered an invalid value or cancelled the prompt.")

def prompt_site_selection():
    """
    Prompts the user to select a site and returns the site_id.
    Uses the existing CSV-based site selection functionality.
    """
    return prompt_select_site_id_from_csv()

def prompt_device_selection(site_id, device_type="all"):
    """
    Prompts the user to select a device from the specified site and returns the device_id.
    
    Args:
        site_id (str): The site ID to filter devices by
        device_type (str): Filter by device type ("all", "switch", "gateway", "ap")
    
    Returns:
        str: The selected device ID or None if no selection made
    """
    return prompt_select_device_id_from_inventory(site_id, device_type)

def export_site_specific_data(api_call, data_type, sort_key="name", **api_kwargs):
    """
    Generic function to export site-specific data to CSV.
    
    Args:
        api_call: The mistapi function to call
        data_type: Description of the data type (e.g., "port stats", "clients")
        sort_key: Field to sort results by
        **api_kwargs: Additional arguments to pass to the API call
    
    Returns:
        None
    """
    logging.info(f"Starting export of site {data_type}...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    try:
        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, get_cached_or_prompted_org_id())
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except Exception as e:
        logging.error(f"Error getting site name: {e}")
        site_name = site_id
    
    logging.info(f"Exporting {data_type} for site: {site_name}")
    
    # Create filename from data_type
    safe_data_type = data_type.replace(" ", "").replace("-", "").title()
    safe_site_name = site_name.replace(" ", "_").replace("-", "_")
    filename = f"Site{safe_data_type}_{safe_site_name}.csv"
    
    # For site-specific API calls, we need to use a custom approach since
    # fetch_and_display_api_data expects org_id as the second parameter
    try:
        logging.debug(f"Making site-specific API call: {api_call.__name__} with site_id: {site_id}")
        response = api_call(apisession, site_id, limit=1000, **api_kwargs)
        
        rawdata = mistapi.get_all(response=response, mist_session=apisession)
        if rawdata is None:
            logging.warning(f"⚠️ No data returned from API for {data_type} at site {site_name}. Skipping.")
            return

        logging.info(f"Fetched {len(rawdata)} raw records for {data_type} from site {site_name}.")

        # Sort data if a sort key is provided
        if sort_key:
            rawdata = sorted(rawdata, key=lambda x: x.get(sort_key, ""))

        # Flatten nested fields for CSV compatibility
        data = flatten_nested_fields_in_list(rawdata)
        
        # Escape multiline strings for CSV
        data = escape_multiline_strings_for_csv(data)

        # Write processed data to output
        save_data_to_output(data, filename)
        logging.info(f"Site {data_type} data written to {filename} ({len(data)} rows).")

        # Display the data in a table
        fields = get_all_unique_dict_keys(data)
        table = PrettyTable()
        table.field_names = fields
        table.valign = "t"
        for item in tqdm(data, desc="Processing", unit="record"):
            row = [item.get(field, "") for field in table.field_names]
            table.add_row(row)
        print(table)
        logging.info("Site data displayed in table format.")
        
    except Exception as e:
        logging.error(f"❌ Error during site {data_type} export for {site_name}: {e}")
        raise

def export_org_specific_data(api_call, data_type, sort_key="name", **api_kwargs):
    """
    Generic function to export organization-specific data to CSV.
    
    Args:
        api_call: The mistapi function to call
        data_type: Description of the data type (e.g., "licenses", "templates")
        sort_key: Field to sort results by
        **api_kwargs: Additional arguments to pass to the API call
    
    Returns:
        None
    """
    logging.info(f"Starting export of organization {data_type}...")
    
    # Create filename from data_type
    safe_data_type = data_type.replace(" ", "").replace("-", "").title()
    filename = f"Org{safe_data_type}.csv"
    
    fetch_and_display_api_data(
        title=f"Organization {data_type.title()}:",
        api_call=api_call,
        filename=filename,
        sort_key=sort_key,
        limit=1000,
        **api_kwargs
    )

def export_open_org_alarms_to_csv():
    """
    Fetches all open organization alarms from the past 24 hours and writes them to OrgAlarms.csv.
    """
    logging.debug("ENTRY: export_open_org_alarms_to_csv()")
    logging.info("Starting search for all open org alarms in the past 24 hours...")
    
    try:
        fetch_and_display_api_data(
            title="Search all Org Alarms:",
            api_call=mistapi.api.v1.orgs.alarms.searchOrgAlarms,
            filename="OrgAlarms.csv",
            limit=1000,
            duration="24h",
            status="open"
        )
        logging.info("Completed export_open_org_alarms_to_csv and wrote results to OrgAlarms.csv.")
        logging.debug("EXIT: export_open_org_alarms_to_csv - success")
    except Exception as e:
        logging.error(f"Failed to export open org alarms: {e}")
        logging.debug("EXIT: export_open_org_alarms_to_csv - error")
        raise

def export_recent_device_events_to_csv():
    """
    Export all device events from the past 24 hours to OrgDeviceEvents.csv.
    """
    logging.info("Search Org Device Events:")
    org_id = get_cached_or_prompted_org_id()
    # Calculate start and end epoch times for the last 24 hours
    end_time = int(time.time())
    start_time = end_time - 24 * 3600
    # Call the Mist API to search for device events in the last 24 hours
    response = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
        apisession, org_id, device_type="all", limit=1000, start=start_time, end=end_time
    )
    # Retrieve all paginated results
    rawdata = mistapi.get_all(response=response, mist_session=apisession)
    events = rawdata
    logging.info(f"Fetched {len(events)} device events from the past 24 hours.")
    # Write the events to a CSV file
    save_data_to_output(events, "OrgDeviceEvents.csv")
    logging.info(f"Device events written to OrgDeviceEvents.csv ({len(events)} rows).")
    # Optionally log the first few events for debugging
    if events:
        logging.debug("Sample device events: %s", json.dumps(events[:3], indent=2))

def export_all_org_device_events_52w_to_csv():
    """
    Export all org device events from the last 52 weeks to OrgDeviceEvents_52w.csv.
    Fetches all data into memory, then writes to CSV in one operation.
    """
    logging.info("Exporting all org device events from the last 52 weeks...")
    org_id = get_cached_or_prompted_org_id()
    # Use Mist API to search for device events in the last 52 weeks
    # Use duration=52w, do NOT use last_by
    response = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
        apisession, org_id, device_type="all", limit=1000, duration="52w"
    )
    # Retrieve all paginated results into memory
    events = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"Fetched {len(events)} device events from the last 52 weeks.")
    # Flatten and sanitize for CSV
    events = flatten_nested_fields_in_list(events)
    events = escape_multiline_strings_for_csv(events)
    # Write all data to CSV in one operation
    save_data_to_output(events, "OrgDeviceEvents_52w.csv")
    logging.info("✅ All org device events (52w) exported to OrgDeviceEvents_52w.csv.")

def export_audit_logs_to_csv(full_history=False, duration=None):
    """
    Export organization audit logs to OrgAuditLogs.csv.
    Fetches all pages using mistapi.get_all.
    If full_history is True, pulls all audit logs (start=0).
    If False, pulls only the last 24 hours.
    If duration is provided, uses it as the duration parameter.
    """
    logging.debug(f"ENTRY: export_audit_logs_to_csv(full_history={full_history}, duration={duration})")
    logging.info("Starting export of organization audit logs...")
    
    try:
        org_id = get_cached_or_prompted_org_id()

        # Always include limit=1000 to reduce number of API calls
        kwargs = {"limit": 1000}

        if duration:
            kwargs["duration"] = duration
            logging.info(f"Exporting audit logs for duration: {duration}")
        elif not full_history:
            end_time = int(time.time())
            start_time = end_time - 24 * 3600
            kwargs["start"] = start_time
            kwargs["end"] = end_time
            logging.info("Exporting only last 24 hours of audit logs.")
        else:
            kwargs["start"] = 0
            logging.info("Exporting full audit log history (start=0).")

        # Call the API and fetch all pages
        logging.debug(f"Making API call with parameters: {kwargs}")
        response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(apisession, org_id, **kwargs)
        rawdata = mistapi.get_all(response=response, mist_session=apisession)

        if not rawdata:
            logging.warning("⚠️ No audit logs returned from API.")
            logging.debug("EXIT: export_audit_logs_to_csv - no data")
            return

        # Flatten and sanitize for CSV
        data = flatten_nested_fields_in_list(rawdata)
        data = escape_multiline_strings_for_csv(data)
        save_data_to_output(data, "OrgAuditLogs.csv")
        logging.info("Completed export_audit_logs_to_csv and wrote results to OrgAuditLogs.csv.")
        logging.debug("EXIT: export_audit_logs_to_csv - success")
        
    except Exception as e:
        logging.error(f"Failed to export audit logs: {e}")
        logging.debug("EXIT: export_audit_logs_to_csv - error")
        raise

def export_all_sites_to_csv():
    """
    Fetches and exports the list of all sites in the organization.
    Output format determined by global OUTPUT_FORMAT setting.
    Uses fetch_and_display_api_data to handle API call and output writing.
    """
    logging.info("Starting export of organization site list...")
    fetch_and_display_api_data(
        title="Site List:",
        api_call=mistapi.api.v1.orgs.sites.listOrgSites,
        filename="SiteList",  # Format-agnostic filename (no extension)
        sort_key="name",  # or "site_id" if preferred
        limit=1000
    )
    output_desc = "SQLite table" if OUTPUT_FORMAT == "sqlite" else "CSV file"
    logging.info(f"Completed export_all_sites and wrote results to {output_desc}.")

def export_all_sites_list_to_csv():
    """
    Uses the 'list' sites API endpoint (not 'search') to export all sites to SiteList_ListAPI.csv,
    but only if the file does not already exist.
    """
    output_file = "SiteList_ListAPI.csv"
    if os.path.exists(output_file):
        logging.info(f"✅ Using cached {output_file} (already exists)")
        print(f"✅ Using cached {output_file} (already exists)")
        return

    logging.info("Fetching all sites using the 'list' sites API endpoint...")
    print("Fetching all sites using the 'list' sites API endpoint...")
    org_id = get_cached_or_prompted_org_id()
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    if not sites:
        logging.warning("⚠️ No sites returned from API.")
        print("⚠️ No sites returned from API.")
        return
    # Flatten and sanitize for CSV
    sites = flatten_nested_fields_in_list(sites)
    sites = escape_multiline_strings_for_csv(sites)
    save_data_to_output(sites, output_file)
    logging.info(f"✅ Sites exported to {output_file}")
    print(f"✅ Sites exported to {output_file}")

def export_device_inventory_to_csv():
    """
    Fetches and exports the full inventory of devices in the organization to OrgInventory.csv.
    Uses fetch_and_display_api_data to handle API call, CSV writing, and table display.
    """
    logging.info("Starting export of organization device inventory...")
    fetch_and_display_api_data(
        title="Org Inventory:",
        api_call=mistapi.api.v1.orgs.inventory.getOrgInventory,
        filename="OrgInventory.csv",
        sort_key="model",
        limit=1000
    )
    logging.info("Completed export_device_inventory_to_csv and wrote results to OrgInventory.csv.")

def export_device_stats_to_csv():
    """
    Export statistics for all devices in the organization to OrgDeviceStats.csv.
    Uses fetch_and_display_api_data to handle API call, CSV writing, and table display.
    """
    logging.info("Starting export of organization device statistics...")  # Log start
    fetch_and_display_api_data(
        title="Org Device Stats:",
        api_call=mistapi.api.v1.orgs.stats.listOrgDevicesStats,
        filename="OrgDeviceStats.csv",
        sort_key="type",
        type="all",
        limit=1000
    )

def export_device_port_stats_to_csv():
    """
    Export port-level statistics for all switches and gateways in the organization to OrgDevicePortStats.csv.
    Uses fetch_and_display_api_data to handle API call, CSV writing, and table display.
    """
    logging.info("Starting export of organization device port statistics...")  # Log start of function
    fetch_and_display_api_data(
        title="Org Device Port Stats:",
        api_call=mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
        filename="OrgDevicePortStats.csv",
        sort_key="mac",
        limit=1000
    )

def export_vpn_peer_stats_to_csv():
    """
    Export VPN peer path statistics for the organization to OrgVPNPeerStats.csv.
    Uses fetch_and_display_api_data to handle API call, CSV writing, and table display.
    """
    logging.info("Starting export of organization VPN peer path statistics...")  # Log start of function
    fetch_and_display_api_data(
        title="Org VPN Peer Stats:",
        api_call=mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
        filename="OrgVPNPeerStats.csv",
        sort_key="mac",
        limit=1000
    )

def export_site_port_stats_to_csv():
    """Export port statistics for a specific site to SitePortStats.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.stats.searchSitePortStats,
        data_type="port stats",
        sort_key="mac"
    )

def export_site_device_virtual_chassis_to_csv():
    """
    Export virtual chassis information for switches at a specific site.
    Prompts user to select a site and device, then exports VC details.
    """
    logging.info("Starting export of site device virtual chassis information...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get device selection (filtered for switches)
    device_id = prompt_device_selection(site_id, device_type="switch")
    if not device_id:
        logging.error("No switch device selected. Exiting.")
        return
    
    # Get device name for display
    response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id)
    devices = mistapi.get_all(response=response, mist_session=apisession)
    device_name = next((dev["name"] for dev in devices if dev["id"] == device_id), device_id)
    
    logging.info(f"Exporting virtual chassis information for device: {device_name}")
    
    try:
        # Make API call to get virtual chassis information
        response = mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(apisession, site_id, device_id)
        
        if response.data:
            # Convert to list format for CSV processing
            vc_data = [response.data] if isinstance(response.data, dict) else response.data
            
            # Process and save the data
            flattened = flatten_nested_fields_in_list(vc_data)
            sanitized = escape_multiline_strings_for_csv(flattened)
            
            filename = f"VirtualChassis_{device_name.replace(' ', '_')}.csv"
            save_data_to_output(sanitized, filename)
            
            logging.info(f"✅ Virtual chassis information exported to {filename}")
            
            # Display summary
            if sanitized:
                print(f"\n📊 Virtual Chassis Summary for {device_name}:")
                print(f"   • Records exported: {len(sanitized)}")
                if 'members' in sanitized[0]:
                    print(f"   • VC members: {sanitized[0].get('members', 'N/A')}")
                if 'preprovisioned' in sanitized[0]:
                    print(f"   • Preprovisioned: {sanitized[0].get('preprovisioned', 'N/A')}")
                print(f"   • Data saved to: {filename}")
        else:
            logging.warning(f"⚠️ No virtual chassis data returned for device {device_name}")
            print(f"⚠️ No virtual chassis data found for device {device_name}")
            
    except Exception as e:
        logging.error(f"❌ Failed to export virtual chassis information: {e}")
        print(f"❌ Failed to export virtual chassis information: {e}")

def export_organization_templates_to_csv():
    """
    Export all organization templates (gateway, network, RF, site, AP) to CSV files.
    """
    logging.info("Starting export of organization templates...")
    
    # Gateway templates
    try:
        fetch_and_display_api_data(
            title="Gateway Templates:",
            api_call=mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates,
            filename="OrgGatewayTemplates.csv",
            sort_key="name",
            limit=1000
        )
    except Exception as e:
        logging.error(f"Failed to export gateway templates: {e}")
    
    # Network templates
    try:
        fetch_and_display_api_data(
            title="Network Templates:",
            api_call=mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
            filename="OrgNetworkTemplates.csv",
            sort_key="name",
            limit=1000
        )
    except Exception as e:
        logging.error(f"Failed to export network templates: {e}")
    
    # RF templates
    try:
        fetch_and_display_api_data(
            title="RF Templates:",
            api_call=mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates,
            filename="OrgRfTemplates.csv",
            sort_key="name",
            limit=1000
        )
    except Exception as e:
        logging.error(f"Failed to export RF templates: {e}")
    
    # Site templates
    try:
        fetch_and_display_api_data(
            title="Site Templates:",
            api_call=mistapi.api.v1.orgs.sitetemplates.listOrgSiteTemplates,
            filename="OrgSiteTemplates.csv",
            sort_key="name",
            limit=1000
        )
    except Exception as e:
        logging.error(f"Failed to export site templates: {e}")
    
    # AP templates
    try:
        fetch_and_display_api_data(
            title="AP Templates:",
            api_call=mistapi.api.v1.orgs.aptemplates.listOrgAptemplates,
            filename="OrgApTemplates.csv",
            sort_key="name",
            limit=1000
        )
    except Exception as e:
        logging.error(f"Failed to export AP templates: {e}")
    
    logging.info("✅ Organization templates export completed")

def export_site_clients_to_csv():
    """
    Export client statistics for a specific site to SiteClients.csv.
    Prompts user to select a site and exports connected client information.
    """
    logging.info("Starting export of site client statistics...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting client statistics for site: {site_name}")
    
    fetch_and_display_api_data(
        title=f"Site Clients for {site_name}:",
        api_call=mistapi.api.v1.sites.stats.searchSiteClientStats,
        filename=f"SiteClients_{site_name.replace(' ', '_')}.csv",
        sort_key="mac",
        site_id=site_id,
        limit=1000
    )

def export_site_devices_to_csv():
    """
    Export device list for a specific site to SiteDevices.csv.
    Prompts user to select a site and exports device information.
    """
    logging.info("Starting export of site device list...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting device list for site: {site_name}")
    
    fetch_and_display_api_data(
        title=f"Site Devices for {site_name}:",
        api_call=mistapi.api.v1.sites.devices.listSiteDevices,
        filename=f"SiteDevices_{site_name.replace(' ', '_')}.csv",
        sort_key="name",
        site_id=site_id,
        limit=1000
    )

def export_site_device_stats_to_csv():
    """
    Export device statistics for a specific site to SiteDeviceStats.csv.
    Prompts user to select a site and exports device statistics.
    """
    logging.info("Starting export of site device statistics...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting device statistics for site: {site_name}")
    
    fetch_and_display_api_data(
        title=f"Site Device Stats for {site_name}:",
        api_call=mistapi.api.v1.sites.stats.searchSiteDeviceStats,
        filename=f"SiteDeviceStats_{site_name.replace(' ', '_')}.csv",
        sort_key="mac",
        site_id=site_id,
        limit=1000
    )

def export_org_wireless_clients_to_csv():
    """Export wireless client statistics for the entire organization to OrgWirelessClients.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.clients.searchOrgWirelessClients,
        data_type="wireless clients",
        sort_key="mac"
    )

def export_org_wired_clients_to_csv():
    """Export wired client statistics for the entire organization to OrgWiredClients.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients,
        data_type="wired clients",
        sort_key="mac"
    )

def export_org_security_events_to_csv():
    """Export security policies and site-level rogue events for the organization to OrgSecurityEvents.csv."""
    logging.info("Starting export of organization security policies and rogue events...")
    
    # First export security policies
    logging.info("Fetching organization security policies...")
    fetch_and_display_api_data(
        title="Organization Security Policies:",
        api_call=mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies,
        filename="OrgSecurityPolicies",
        sort_key="name",
        limit=1000
    )
    
    # Then collect rogue events from all sites
    logging.info("Fetching rogue events from all sites...")
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    
    all_rogue_events = []
    org_id = get_cached_or_prompted_org_id()
    
    try:
        # Load sites
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            sites = list(csv.DictReader(f))
            
        for site in tqdm(sites, desc="Sites", unit="site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unknown Site")
            
            if not site_id:
                continue
                
            try:
                # Get rogue events for this site
                response = mistapi.api.v1.sites.rogues.searchSiteRogueEvents(
                    apisession, site_id, duration="7d", limit=1000
                )
                events = mistapi.get_all(response=response, mist_session=apisession)
                
                # Add site context to each event
                for event in events:
                    event["site_id"] = site_id
                    event["site_name"] = site_name
                    
                all_rogue_events.extend(events)
                logging.info(f"✅ Fetched {len(events)} rogue events from site: {site_name}")
                
            except Exception as e:
                logging.warning(f"⚠️ Failed to fetch rogue events from site {site_name}: {e}")
                continue
                
            # Rate limiting
            time.sleep(0.5)
                
    except Exception as e:
        logging.error(f"Failed to process sites for rogue events: {e}")
        
    # Save rogue events if any were found
    if all_rogue_events:
        flattened = flatten_nested_fields_in_list(all_rogue_events)
        sanitized = escape_multiline_strings_for_csv(flattened)
        save_data_to_output(sanitized, "OrgRogueEvents")
        logging.info(f"✅ {len(all_rogue_events)} rogue events exported to OrgRogueEvents")
        print(f"✅ Security data exported: OrgSecurityPolicies and {len(all_rogue_events)} rogue events")
    else:
        logging.info("No rogue events found across all sites")
        print("✅ Security policies exported, no rogue events found")

def export_org_rogue_clients_to_csv():
    """Export rogue client detections from all sites to OrgRogueClients.csv."""
    logging.info("Starting export of rogue clients from all sites...")
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    
    all_rogue_clients = []
    
    try:
        # Load sites
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            sites = list(csv.DictReader(f))
            
        for site in tqdm(sites, desc="Sites", unit="site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unknown Site")
            
            if not site_id:
                continue
                
            try:
                # Get rogue clients for this site
                response = mistapi.api.v1.sites.insights.listSiteRogueClients(
                    apisession, site_id, duration="7d", limit=1000
                )
                clients = mistapi.get_all(response=response, mist_session=apisession)
                
                # Add site context to each client
                for client in clients:
                    client["site_id"] = site_id
                    client["site_name"] = site_name
                    
                all_rogue_clients.extend(clients)
                logging.info(f"✅ Fetched {len(clients)} rogue clients from site: {site_name}")
                
            except Exception as e:
                logging.warning(f"⚠️ Failed to fetch rogue clients from site {site_name}: {e}")
                continue
                
            # Rate limiting
            time.sleep(0.5)
                
    except Exception as e:
        logging.error(f"Failed to process sites for rogue clients: {e}")
        return
        
    # Save rogue clients
    if all_rogue_clients:
        flattened = flatten_nested_fields_in_list(all_rogue_clients)
        sanitized = escape_multiline_strings_for_csv(flattened)
        save_data_to_output(sanitized, "OrgRogueClients")
        logging.info(f"✅ {len(all_rogue_clients)} rogue clients exported to OrgRogueClients")
        print(f"✅ {len(all_rogue_clients)} rogue clients exported to OrgRogueClients")
    else:
        logging.info("No rogue clients found across all sites")
        print("ℹ️ No rogue clients detected across all sites")

def export_org_rogue_aps_to_csv():
    """Export rogue AP detections from all sites to OrgRogueAPs.csv."""
    logging.info("Starting export of rogue APs from all sites...")
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    
    all_rogue_aps = []
    
    try:
        # Load sites
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            sites = list(csv.DictReader(f))
            
        for site in tqdm(sites, desc="Sites", unit="site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unknown Site")
            
            if not site_id:
                continue
                
            try:
                # Get rogue APs for this site
                response = mistapi.api.v1.sites.insights.listSiteRogueAPs(
                    apisession, site_id, duration="7d", limit=1000
                )
                aps = mistapi.get_all(response=response, mist_session=apisession)
                
                # Add site context to each AP
                for ap in aps:
                    ap["site_id"] = site_id
                    ap["site_name"] = site_name
                    
                all_rogue_aps.extend(aps)
                logging.info(f"✅ Fetched {len(aps)} rogue APs from site: {site_name}")
                
            except Exception as e:
                logging.warning(f"⚠️ Failed to fetch rogue APs from site {site_name}: {e}")
                continue
                
            # Rate limiting
            time.sleep(0.5)
                
    except Exception as e:
        logging.error(f"Failed to process sites for rogue APs: {e}")
        return
        
    # Save rogue APs
    if all_rogue_aps:
        flattened = flatten_nested_fields_in_list(all_rogue_aps)
        sanitized = escape_multiline_strings_for_csv(flattened)
        save_data_to_output(sanitized, "OrgRogueAPs")
        logging.info(f"✅ {len(all_rogue_aps)} rogue APs exported to OrgRogueAPs")
        print(f"✅ {len(all_rogue_aps)} rogue APs exported to OrgRogueAPs")
    else:
        logging.info("No rogue APs found across all sites")
        print("ℹ️ No rogue APs detected across all sites")

def export_org_licenses_to_csv():
    """Export license information for the organization to OrgLicenses.csv."""
    logging.info("Starting export of organization licenses...")
    
    # Create filename from data_type
    filename = "OrgLicenses.csv"
    
    fetch_and_display_api_data(
        title="Organization Licenses:",
        api_call=mistapi.api.v1.orgs.licenses.getOrgLicensesSummary,
        filename=filename,
        sort_key="type"
        # Note: no limit parameter as this function doesn't accept it
    )

def export_org_psks_to_csv():
    """Export PSK (Pre-Shared Key) information for the organization to OrgPsks.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.psks.listOrgPsks,
        data_type="psks",
        sort_key="name"
    )

def export_org_webhooks_to_csv():
    """Export webhook configuration for the organization to OrgWebhooks.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.webhooks.listOrgWebhooks,
        data_type="webhooks",
        sort_key="name"
    )

def export_org_wlans_to_csv():
    """Export WLAN configuration for the organization to OrgWlans.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.wlans.listOrgWlans,
        data_type="wlans",
        sort_key="ssid"
    )

def export_org_api_tokens_to_csv():
    """Export API token information for the organization to OrgApiTokens.csv."""
    logging.info("Starting export of organization api tokens...")
    
    # Create filename from data_type
    filename = "OrgApiTokens.csv"
    
    fetch_and_display_api_data(
        title="Organization Api Tokens:",
        api_call=mistapi.api.v1.orgs.apitokens.listOrgApiTokens,
        filename=filename,
        sort_key="name"
        # Note: no limit parameter as this function doesn't accept it
    )

def export_org_admins_to_csv():
    """Export administrator information for the organization to OrgAdmins.csv."""
    logging.info("Starting export of organization admins...")
    
    # Create filename from data_type  
    filename = "OrgAdmins.csv"
    
    fetch_and_display_api_data(
        title="Organization Admins:",
        api_call=mistapi.api.v1.orgs.admins.listOrgAdmins,
        filename=filename,
        sort_key="name"
        # Note: no limit parameter as this function doesn't accept it
    )

def export_org_sso_to_csv():
    """Export SSO (Single Sign-On) information for the organization to OrgSso.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.ssos.listOrgSsos,
        data_type="sso",
        sort_key="name"
    )

def export_org_usage_to_csv():
    """Export license usage information for the organization to OrgUsage.csv."""
    logging.info("Starting export of organization license usage...")
    
    fetch_and_display_api_data(
        title="Organization License Usage:",
        api_call=mistapi.api.v1.orgs.licenses.getOrgLicensesBySite,
        filename="OrgUsage",
        sort_key="site_id"
    )
    
    logging.info("✅ License usage data exported to OrgUsage")
    print("✅ License usage data exported to OrgUsage")

def export_org_msp_to_csv():
    """Export MSP (Managed Service Provider) information for the organization to OrgMsp.csv."""
    logging.warning("ℹ️ MSP data is available only at MSP level, not organization level")
    print("ℹ️ MSP data is available only at MSP level, not organization level")
    print("💡 To access MSP data, use the Mist API MSP endpoints directly:")
    print("   - GET /api/v1/msps (list MSPs)")
    print("   - GET /api/v1/msps/{msp_id} (get MSP details)")
    print("   - GET /api/v1/msps/{msp_id}/orgs (list organizations under MSP)")
    print("   This organization-level export is not applicable for MSP data.")

def export_org_mx_edges_to_csv():
    """Export MX Edge information for the organization to OrgMxEdges.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.mxedges.listOrgMxEdges,
        data_type="mx edges",
        sort_key="name"
    )

def export_org_network_templates_to_csv():
    """Export network template information for the organization to OrgNetworkTemplates.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
        data_type="network templates",
        sort_key="name"
    )

def export_org_rf_templates_to_csv():
    """Export RF template information for the organization to OrgRfTemplates.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates,
        data_type="rf templates",
        sort_key="name"
    )

def export_org_ap_templates_to_csv():
    """Export AP template information for the organization to OrgApTemplates.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
        data_type="ap templates",
        sort_key="name",
        type="ap"
    )

def export_org_switch_templates_to_csv():
    """Export switch template information for the organization to OrgSwitchTemplates.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
        data_type="switch templates",
        sort_key="name",
        type="switch"
    )

def export_site_wlans_to_csv():
    """Export WLAN configuration for a specific site to SiteWlans.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.wlans.listSiteWlans,
        data_type="wlans",
        sort_key="ssid"
    )

def export_site_beacons_to_csv():
    """Export beacon information for a specific site to SiteBeacons.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.beacons.listSiteBeacons,
        data_type="beacons",
        sort_key="name"
    )

def export_site_maps_to_csv():
    """Export map information for a specific site to SiteMaps.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.maps.listSiteMaps,
        data_type="maps",
        sort_key="name"
    )

def export_site_zones_to_csv():
    """Export zone information for a specific site to SiteZones.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.zones.listSiteZones,
        data_type="zones",
        sort_key="name"
    )

def export_site_insights_to_csv():
    """Export insights information for a specific site to SiteInsights.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.insights.listSiteInsights,
        data_type="insights",
        sort_key="timestamp"
    )

def continuous_data_collection_loop():
    """
    Continuously collect core organizational data as specified in script needs.txt.
    This runs the 5 key API calls in a loop with proper rate limiting:
    1. Site list
    2. Organization inventory
    3. Organization device stats
    4. Organization device port stats
    5. VPN peer path stats
    """
    logging.info("Starting continuous data collection loop...")
    print("🔄 Starting continuous data collection loop...")
    print("   This will collect core organizational data every 5 seconds")
    print("   Press CTRL+C to stop or create 'stop_loop.txt' file")
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            print(f"\n📊 Loop iteration {loop_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check for stop file
            if os.path.exists("stop_loop.txt"):
                print("🛑 Stop file detected. Ending continuous loop.")
                os.remove("stop_loop.txt")
                break
            
            try:
                # 1. Site list
                print("  📍 Collecting site list...")
                export_all_sites_to_csv()
                time.sleep(0.75)  # Rate limiting
                
                # 2. Organization inventory
                print("  📦 Collecting organization inventory...")
                export_device_inventory_to_csv()
                time.sleep(0.75)
                
                # 3. Organization device stats
                print("  📈 Collecting organization device stats...")
                export_device_stats_to_csv()
                time.sleep(0.75)
                
                # 4. Organization device port stats
                print("  🔌 Collecting organization device port stats...")
                export_device_port_stats_to_csv()
                time.sleep(0.75)
                
                # 5. VPN peer path stats
                print("  🔗 Collecting VPN peer path stats...")
                export_vpn_peer_stats_to_csv()
                time.sleep(0.75)
                
                print(f"  ✅ Loop {loop_count} completed successfully")
                
            except KeyboardInterrupt:
                print("\n⚠️  Keyboard interrupt detected. Stopping loop...")
                break
            except Exception as e:
                logging.error(f"Error in continuous loop iteration {loop_count}: {e}")
                print(f"  ❌ Error in loop {loop_count}: {e}")
                print("  🔄 Continuing to next iteration...")
                time.sleep(5)  # Wait longer on error
                
    except KeyboardInterrupt:
        print("\n🛑 Continuous data collection loop stopped by user.")
    except Exception as e:
        logging.error(f"Fatal error in continuous loop: {e}")
        print(f"💥 Fatal error in continuous loop: {e}")
    
    print("🏁 Continuous data collection loop ended.")

# === NAC (Network Access Control) Functions ===

def export_org_nac_clients_to_csv():
    """Export NAC client information for the organization to OrgNacClients.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClients,
        data_type="nac clients",
        sort_key="mac"
    )

def export_org_nac_tags_to_csv():
    """Export NAC tags/policies for the organization to OrgNacTags.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nactags.listOrgNacTags,
        data_type="nac tags",
        sort_key="name"
    )

def export_org_nac_portals_to_csv():
    """Export NAC portals configuration for the organization to OrgNacPortals.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nacportals.listOrgNacPortals,
        data_type="nac portals",
        sort_key="name"
    )

def export_org_nac_rules_to_csv():
    """Export NAC rules/policies for the organization to OrgNacRules.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nacrules.listOrgNacRules,
        data_type="nac rules",
        sort_key="name"
    )

def export_org_nac_events_to_csv():
    """Export NAC events for the organization to OrgNacEvents.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents,
        data_type="nac events",
        sort_key="timestamp",
        duration="24h"
    )

# === Statistics & Analytics Functions ===

def export_org_assets_to_csv():
    """Export asset tracking statistics for the organization to OrgAssets.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.stats.searchOrgAssets,
        data_type="assets",
        sort_key="name"
    )

def export_org_bgp_peers_to_csv():
    """Export BGP peer statistics for the organization to OrgBgpPeers.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.stats.searchOrgBgpPeers,
        data_type="bgp peers",
        sort_key="peer_ip"
    )

def export_org_tunnel_stats_to_csv():
    """Export tunnel statistics for the organization to OrgTunnelStats.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.stats.searchOrgTunnels,
        data_type="tunnel stats",
        sort_key="name"
    )

def export_org_site_stats_to_csv():
    """Export site-level statistics for the organization to OrgSiteStats.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.stats.listOrgSitesStats,
        data_type="site stats",
        sort_key="name"
    )

def export_org_mxedge_stats_to_csv():
    """Export MX Edge statistics for the organization to OrgMxEdgeStats.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.stats.listOrgMxEdgesStats,
        data_type="mx edge stats",
        sort_key="name"
    )

# === Configuration & Management Functions ===

def export_org_alarm_templates_to_csv():
    """Export alarm template configurations for the organization to OrgAlarmTemplates.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.alarmtemplates.listOrgAlarmTemplates,
        data_type="alarm templates",
        sort_key="name"
    )

def export_org_security_intel_profiles_to_csv():
    """Export security intelligence profiles for the organization to OrgSecurityIntelProfiles.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles,
        data_type="security intel profiles",
        sort_key="name"
    )

def export_org_invites_to_csv():
    """Export pending admin invitations for the organization to OrgInvites.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.invites.listOrgInvites,
        data_type="invites",
        sort_key="email"
    )

def export_org_events_to_csv():
    """Export general organization events to OrgEvents.csv."""
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.events.searchOrgEvents,
        data_type="events",
        sort_key="timestamp",
        duration="24h"
    )

# === Site-Level Functions ===

def export_site_system_events_to_csv():
    """Export system events for a specific site to SiteSystemEvents.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.events.searchSiteSystemEvents,
        data_type="system events",
        sort_key="timestamp",
        duration="24h"
    )

def export_site_fast_roam_events_to_csv():
    """Export fast roam events for a specific site to SiteFastRoamEvents.csv."""
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.events.searchSiteFastRoamEvents,
        data_type="fast roam events",
        sort_key="timestamp",
        duration="24h"
    )

def interactive_display_site_inventory():
    """
    Prompts the user to select a site and displays its device inventory.
    """
    logging.info("Prompting user to select a site for device inventory view...")
    print("Select a Site to View Device Inventory:")
    site_id = prompt_select_site_id_from_csv()
    if site_id:
        logging.info(f"User selected site_id: {site_id} for inventory display.")
        show_site_device_inventory(site_id)
    else:
        logging.warning("No site selected or invalid input provided for site selection.")

def interactive_display_device_stats(site_id=None, device_id=None):
    """
    Fetches and displays detailed statistics for a specific device (by site_id/device_id if provided, else prompts user).
    """
    logging.info("Prompting user to select a device for detailed statistics view...")
    interactive_fetch_device_data_to_csv(
        fetch_function=mistapi.api.v1.sites.stats.getSiteDeviceStats,
        filename="DeviceStats.csv",
        description="Fetching detailed stats",
        site_id=site_id,
        device_id=device_id
    )
    logging.info("Completed interactive_display_device_stats execution.")

def interactive_display_device_tests():
    """
    Prompts user to select a gateway device and displays its synthetic test stats.
    """
    logging.info("Prompting user to select a gateway device for synthetic test stats view...")
    # Call the interactive_fetch_device_data_to_csv helper with the appropriate Mist API function
    interactive_fetch_device_data_to_csv(
        fetch_function=mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest,
        filename="DeviceTestResults.csv",
        description="Fetching synthetic test stats",
        device_type="gateway"
    )
    logging.info("Completed interactive_display_device_tests execution.")

def interactive_display_device_config():
    """
    Prompts user to select a device and displays its configuration details.
    """
    logging.info("Prompting user to select a device for configuration details view...")  # Log start
    # Call the interactive_fetch_device_data_to_csv helper with the appropriate Mist API function
    interactive_fetch_device_data_to_csv(
        fetch_function=mistapi.api.v1.sites.devices.getSiteDevice,
        filename="DeviceConfig.csv",
        description="Fetching device configuration"
    )
    logging.info("Completed interactive_display_device_config execution.")  # Log completion

def export_all_devices_to_csv():
    """
    Fetches and exports a list of all devices in the organization to OrgDevices.csv.
    Uses fetch_and_display_api_data to handle API call, CSV writing, and table display.
    """
    logging.info("Starting export of all organization devices...")  # Log start of function
    fetch_and_display_api_data(
        title="Org Devices:",
        api_call=mistapi.api.v1.orgs.devices.listOrgDevices,
        filename="OrgDevices.csv",
        sort_key="type"
    )
    logging.info("Completed export_all_devices_to_csv and wrote results to OrgDevices.csv.")  # Log completion

def fetch_all_site_settings_from_api(apisession, org_id, limit=1000):
    """
    Fetches configuration settings for all sites in the organization.

    Args:
        apisession: The Mist API session object.
        org_id: The organization ID.
        limit: (Unused) Maximum number of sites to fetch per API call.

    Returns:
        List of dictionaries, each containing the settings for a site.
    """
    logging.info("Fetching all site settings...")

    # Use mistapi.get_all to ensure pagination is handled for all sites
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)

    all_configs = []
    for site in tqdm(sites, desc="Sites", unit="site"):
        site_id = site.get("id")
        site_name = site.get("name", "Unnamed Site")
        try:
            # Fetch the site settings using the Mist API
            config = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id).data
            config["site_id"] = site_id
            config["site_name"] = site_name
            all_configs.append(config)
            logging.info(f"✅ Fetched config for site: {site_name} (ID: {site_id})")
        except Exception as e:
            logging.warning(f"⚠️ Failed to fetch config for {site_name} (ID: {site_id}): {e}")

    logging.info(f"Fetched settings for {len(all_configs)} sites.")
    return all_configs

def export_site_settings_to_csv():
    """
    Fetches and exports configuration settings for all sites in the organization to AllSiteConfigs.csv.
    Adds detailed logging at each step.
    """
    logging.info("Starting export of all site configuration settings...")  # Log start
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id} for site settings export.")

    # Fetch all site settings using the helper function
    data = fetch_all_site_settings_from_api(apisession, org_id, limit=1000)
    if data:
        logging.info(f"Fetched settings for {len(data)} sites. Flattening and sanitizing data...")
        # Flatten nested fields for CSV compatibility
        data = flatten_nested_fields_in_list(data)
        # Escape multiline strings for CSV compatibility
        data = escape_multiline_strings_for_csv(data)
        # Write the processed data to a CSV file
        save_data_to_output(data, "AllSiteConfigs.csv")
        logging.info("✅ Site configs saved to AllSiteConfigs.csv")
    else:
        logging.warning("⚠️ No site configs found.")

def export_nac_event_definitions_to_csv():
    """
    Export NAC (Network Access Control) event definitions to NacEventDefinitions.csv.
    """
    logging.info("Exporting NAC Event Log Definitions...")  # Log start of function
    print("NAC Event Log Definitions:")
    rawdata = mistapi.api.v1.const.nac_events.listNacEventsDefinitions(apisession).data
    # Write the NAC event definitions to a CSV file
    save_data_to_output(rawdata, "NacEventDefinitions.csv")
    logging.info("✅ NAC event definitions exported to NacEventDefinitions.csv")  # Log completion

def export_client_event_definitions_to_csv():
    """
    Export client event log definitions to ClientEventDefinitions.csv.
    """
    logging.info("Exporting client event log definitions...")  # Log start of function
    print("Client Event Log Definitions:")
    rawdata = mistapi.api.v1.const.client_events.listClientEventsDefinitions(apisession).data
    save_data_to_output(rawdata, "ClientEventDefinitions.csv")
    logging.info("✅ Client event definitions exported to ClientEventDefinitions.csv")  # Log completion

def export_device_event_definitions_to_csv():
    """
    Export device event log definitions to DeviceEventDefinitions.csv.
    """
    logging.info("Exporting device event log definitions...")  # Log start of function
    print("Device Event Log Definitions:")
    rawdata = mistapi.api.v1.const.device_events.listDeviceEventsDefinitions(apisession).data
    # Write the device event definitions to a CSV file
    save_data_to_output(rawdata, "DeviceEventDefinitions.csv")
    logging.info("✅ Device event definitions exported to DeviceEventDefinitions.csv")  # Log completion

def export_mist_edge_event_definitions_to_csv():
    """
    Export Mist Edge event log definitions to MistEdgeEventDefinitions.csv.
    """
    logging.info("Exporting Mist Edge event log definitions...")  # Log start of function
    print("Mist Edge Event Log Definitions:")
    rawdata = mistapi.api.v1.const.mxedge_events.listMxEdgeEventsDefinitions(apisession).data
    save_data_to_output(rawdata, "MistEdgeEventDefinitions.csv")
    logging.info("✅ Mist Edge event definitions exported to MistEdgeEventDefinitions.csv")  # Log completion

def export_other_device_event_definitions_to_csv():
    """
    Export other device event log definitions to OtherEventDefinitions.csv.
    """
    logging.info("Exporting other device event log definitions...")  # Log start of function
    print("Other Event Log Definitions:")
    # Fetch the other device event definitions using the Mist API
    rawdata = mistapi.api.v1.const.otherdevice_events.listOtherDeviceEventsDefinitions(apisession).data
    # Write the event definitions to a CSV file
    save_data_to_output(rawdata, "OtherEventDefinitions.csv")
    logging.info("✅ Other device event definitions exported to OtherEventDefinitions.csv")  # Log completion

def export_system_event_definitions_to_csv():
    """
    Export system event log definitions to SystemEventDefinitions.csv.
    """
    logging.info("Exporting system event log definitions...")  # Log start of function
    print("System Event Log Definitions:")
    rawdata = mistapi.api.v1.const.system_events.listSystemEventsDefinitions(apisession).data
    # Write the system event definitions to a CSV file
    save_data_to_output(rawdata, "SystemEventDefinitions.csv")
    logging.info("✅ System event definitions exported to SystemEventDefinitions.csv")  # Log completion

def export_alarm_definitions_to_csv():
    """
    Export alarm log definitions to AlarmDefinitions.csv and display in a PrettyTable.
    Adds logging for each step.
    """
    logging.info("Exporting alarm log definitions...")  # Log start of function
    print("Alarm Log Definitions:")
    # Fetch alarm definitions from the Mist API
    rawdata = mistapi.api.v1.const.alarm_defs.listAlarmDefinitions(apisession).data
    logging.info(f"Fetched {len(rawdata)} alarm definitions from API.")
    # Sort alarm definitions by 'key'
    alarm_defs = sorted(rawdata, key=lambda x: x.get("key", ""))
    # Write alarm definitions to CSV
    save_data_to_output(alarm_defs, "AlarmDefinitions.csv")
    logging.info("Alarm definitions written to AlarmDefinitions.csv")
    # Prepare PrettyTable for display
    table = PrettyTable()
    table.field_names = ["Key", "Display", "Group", "Severity", "Fields"]
    for alarm in alarm_defs:
        # Add each alarm definition as a row in the table
        table.add_row([
            alarm.get("key"),
            alarm.get("display"),
            alarm.get("group"),
            alarm.get("severity"),
            ", ".join(alarm.get("fields", [])) if isinstance(alarm.get("fields"), list) else alarm.get("fields")
        ])
    logging.debug("\n" + table.get_string())  # Log the table output (debug mode only)

def export_gateway_synthetic_tests_to_csv():
    """
    Collects and exports synthetic test stats for all gateways in the organization.
    Iterates through all sites with gateways, fetches synthetic test stats for each gateway device,
    and writes the results to AllGatewaySyntheticTests.csv.
    """
    logging.info("[INFO] Collecting synthetic test stats for all gateways in the org...")
    org_id = get_cached_or_prompted_org_id()
    site_ids = get_site_ids_with_gateway_devices(apisession, org_id)
    all_stats = []
    smoothed = None

    if not site_ids:
        logging.warning("[WARN] No sites with gateways found. Exiting export_gateway_synthetic_tests_to_csv.")
        return

    for site_id in tqdm(site_ids, desc="Sites", unit="site"):
        try:
            # Validate site_id before making API calls
            validate_site_id(site_id, "export_gateway_synthetic_tests_to_csv")
            
            response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="gateway")
            devices = mistapi.get_all(response=response, mist_session=apisession)
            logging.info(f"[INFO] Found {len(devices)} gateway devices at site {site_id}.")
            for device in tqdm(devices, desc=f"Site {site_id}", unit="device", leave=False):
                device_id = device.get("id")
                device_name = device.get("name", "")
                try:
                    # Validate device_id before making API calls
                    validate_device_id(device_id, "export_gateway_synthetic_tests_to_csv")
                    
                    stats = mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(apisession, site_id, device_id).data
                    stats["site_id"] = site_id
                    stats["site_name"] = device.get("site_name", "")
                    stats["device_id"] = device_id
                    stats["device_name"] = device_name
                    all_stats.append(stats)
                    logging.info(f"[INFO] Collected synthetic test stats for device {device_name} ({device_id}) at site {site_id}.")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to fetch test stats for device {device_id} at site {site_id}: {e}")
                smoothed, delay = get_rate_limited_delay(smoothed)
                logging.info(f"[INFO] Sleeping for {delay}.")
                time.sleep(delay)
        except Exception as e:
            logging.warning(f"⚠️ Failed to list devices for site {site_id}: {e}")

    if all_stats:
        filename = "AllGatewaySyntheticTests.csv"
        flattened = flatten_nested_fields_in_list(all_stats)
        sanitized = escape_multiline_strings_for_csv(flattened)
        save_data_to_output(sanitized, filename)
        logging.info(f"✅ Synthetic test results saved to {filename} ({len(all_stats)} records).")
    else:
        logging.warning("⚠️ No synthetic test results found. CSV not created.")

def get_site_ids_with_gateway_devices(apisession, org_id):
    """
    Fetches all sites in the organization that have at least one gateway device.

    Args:
        apisession: The Mist API session object.
        org_id: The organization ID.

    Returns:
        List of site IDs that have at least one gateway device.
    """
    logging.info("[INFO] Fetching org inventory to find sites with gateways...")
    # Fetch the full org inventory (all devices)
    response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)
    devices = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"[INFO] Retrieved {len(devices)} devices from org inventory.")

    # Collect unique site_ids for devices of type 'gateway'
    gateway_sites = {device["site_id"] for device in devices if device.get("type") == "gateway" and "site_id" in device}
    logging.info(f"[INFO] Found {len(gateway_sites)} sites with at least one gateway.")

    return list(gateway_sites)

def export_gateway_test_results_by_site_to_csv():
    """
    Export all synthetic test results (including speed tests) for all sites with gateways.
    Fetches test results for each site with at least one gateway device and writes them to a CSV.
    """
    logging.info("[INFO] Searching all test results (including speed tests) for sites with gateways...")
    org_id = get_cached_or_prompted_org_id()
    site_ids = get_site_ids_with_gateway_devices(apisession, org_id)
    all_results = []
    smoothed = None  # Initialize smoothed variable for dynamic delay

    if not site_ids:
        logging.warning("⚠️ No sites with gateways found.")
        return

    for site_id in tqdm(site_ids, desc="Sites", unit="site"):
        try:
            # Validate site_id before making API calls
            validate_site_id(site_id, "export_gateway_test_results_to_csv")
            
            # Fetch synthetic test results for the current site
            response = mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest(
                apisession, site_id
            )
            if not hasattr(response, "data"):
                logging.warning(f"⚠️ No data attribute in response for site {site_id}")
                continue

            # Extract results from the response
            results = response.data.get("results", []) if isinstance(response.data, dict) else []
            logging.info(f"[{site_id}] Retrieved {len(results)} test results.")

            for result in results:
                result["site_id"] = site_id  # Annotate result with site_id
                all_results.append(result)
            smoothed, delay = get_rate_limited_delay(smoothed)
            time.sleep(delay)
        except Exception as e:
            logging.warning(f"⚠️ Failed to fetch test results for site {site_id}: {e}")
    
    if all_results:
        filename = "AllGatewayTestResults.csv"
        # Flatten nested fields for CSV compatibility
        flattened = flatten_nested_fields_in_list(all_results)
        # Escape multiline strings for CSV compatibility
        sanitized = escape_multiline_strings_for_csv(flattened)
        # Write the processed data to a CSV file
        save_data_to_output(sanitized, filename)
        logging.info(f"✅ All test results saved to {filename} ({len(all_results)} records).")
    else:
        logging.warning("⚠️ No test results found. CSV not created.")

def export_sites_with_location_to_csv():
    """
    Export a list of sites with all available fields to SitesWithLocations.csv.
    """
    logging.info("Listing Sites with Full Info:")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id} for site location export.")

    # Fetch all sites in the organization
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"Fetched {len(sites)} sites from the organization.")

    # Flatten and sanitize all site data
    flattened_sites = flatten_nested_fields_in_list(sites)
    sanitized_sites = escape_multiline_strings_for_csv(flattened_sites)

    # Write to CSV
    save_data_to_output(sanitized_sites, "SitesWithLocations.csv")
    logging.info("✅ Full site data written to SitesWithLocations.csv")

def export_gateways_with_site_info_to_csv():
    """
    Fetches all gateway devices in the organization, enriches them with site and address info,
    and exports the result to GatewaysWithSiteInfo.csv. Also logs and displays a summary table.
    """
    logging.info("Fetching Gateways with Site Info...")
    org_id = get_cached_or_prompted_org_id()

    # Fetch site list and build a lookup dictionary for site info
    site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=site_response, mist_session=apisession)
    site_lookup = {
        site["id"]: {
            "name": site.get("name", ""),
            "address": site.get("address", "")
        } for site in sites
    }
    logging.debug(f"Loaded {len(site_lookup)} sites for lookup.")

    # Fetch org inventory (all devices)
    inv_response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id)
    inventory = mistapi.get_all(response=inv_response, mist_session=apisession)
    logging.debug(f"Loaded {len(inventory)} devices from org inventory.")

    def split_address(address):
        """
        Splits a full address string into street, city, state, zip, and country.
        Returns empty strings if parsing fails.
        """
        try:
            parts = address.split(", ")
            street = parts[0]
            city = parts[1]
            state_zip = parts[2].split()
            state = state_zip[0]
            zip_code = state_zip[1]
            country = parts[3]
            return street, city, state, zip_code, country
        except Exception as e:
            logging.debug(f"Failed to split address '{address}': {e}")
            return address, "", "", "", ""

    # Filter for gateways and enrich with site info
    gateways = []
    for device in tqdm(inventory, desc="Processing Gateways", unit="device"):
        if device.get("type") == "gateway":
            site_id = device.get("site_id")
            site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})
            device["site_name"] = site_info["name"]
            device["site_address"] = site_info["address"]
            street, city, state, zip_code, country = split_address(site_info["address"])
            device["street"] = street
            device["city"] = city
            device["state"] = state
            device["zip_code"] = zip_code
            device["country"] = country
            gateways.append(device)
    logging.info(f"Enriched {len(gateways)} gateway devices with site info.")

    # Flatten nested fields and escape multiline strings for CSV compatibility
    gateways = flatten_nested_fields_in_list(gateways)
    gateways = escape_multiline_strings_for_csv(gateways)
    gateways = sorted(gateways, key=lambda x: x.get("site_name", ""))
    save_data_to_output(gateways, "GatewaysWithSiteInfo.csv")
    logging.info("Gateway data written to GatewaysWithSiteInfo.csv")

    # Display a summary table in logs
    table = PrettyTable()
    table.field_names = ["name", "mac", "model", "serial", "site_name", "street", "city", "state", "zip_code", "country"]
    for gw in gateways:
        table.add_row([
            gw.get("name", ""),
            gw.get("mac", ""),
            gw.get("model", ""),
            gw.get("serial", ""),
            gw.get("site_name", ""),
            gw.get("street", ""),
            gw.get("city", ""),
            gw.get("state", ""),
            gw.get("zip_code", ""),
            gw.get("country", "")
        ])
    logging.debug("\n" + table.get_string())  # Log the table output (debug mode only)

def export_devices_with_site_info_to_csv():
    """
    Fetches all devices in the organization, enriches them with site and address info,
    and exports the result to AllDevicesWithSiteInfo.csv. Also logs and displays a summary table.
    """
    logging.info("Fetching All Devices with Site Info...")  # Log start of function
    org_id = get_cached_or_prompted_org_id()

    # Fetch all sites and build a lookup dictionary for site info
    site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)
    sites = mistapi.get_all(response=site_response, mist_session=apisession)
    site_lookup = {
        site["id"]: {
            "name": site.get("name", ""),
            "address": site.get("address", "")
        } for site in sites
    }
    logging.debug(f"Loaded {len(site_lookup)} sites for lookup.")

    # Fetch org inventory (all devices)
    inv_response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)
    inventory = mistapi.get_all(response=inv_response, mist_session=apisession)
    logging.debug(f"Loaded {len(inventory)} devices from org inventory.")

    def split_address(address):
        """
        Splits a full address string into street, city, state, zip, and country.
        Returns empty strings if parsing fails.
        """
        try:
            parts = address.split(", ")
            street = parts[0]
            city = parts[1]
            state_zip = parts[2].split()
            state = state_zip[0]
            zip_code = state_zip[1]
            country = parts[3]
            return street, city, state, zip_code, country
        except Exception as e:
            logging.debug(f"Failed to split address '{address}': {e}")
            return address, "", "", "", ""

    enriched_devices = []
    for device in tqdm(inventory, desc="Processing Devices", unit="device"):
        site_id = device.get("site_id")
        site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})
        device["site_name"] = site_info["name"]
        device["site_address"] = site_info["address"]
        street, city, state, zip_code, country = split_address(site_info["address"])
        device["street"] = street
        device["city"] = city
        device["state"] = state
        device["zip_code"] = zip_code
        device["country"] = country
        enriched_devices.append(device)
        logging.debug(f"Enriched device {device.get('name', '')} ({device.get('mac', '')}) with site info.")

    # Flatten nested fields and escape multiline strings for CSV compatibility
    enriched_devices = flatten_nested_fields_in_list(enriched_devices)
    enriched_devices = escape_multiline_strings_for_csv(enriched_devices)
    enriched_devices = sorted(enriched_devices, key=lambda x: x.get("site_name", ""))
    save_data_to_output(enriched_devices, "AllDevicesWithSiteInfo.csv")
    logging.info(f"All device data written to AllDevicesWithSiteInfo.csv ({len(enriched_devices)} records).")

    # Display a summary table in logs
    table = PrettyTable()
    table.field_names = ["name", "mac", "model", "serial", "type", "site_name", "street", "city", "state", "zip_code", "country"]
    for dev in enriched_devices:
        table.add_row([
            dev.get("name", ""),
            dev.get("mac", ""),
            dev.get("model", ""),
            dev.get("serial", ""),
            dev.get("type", ""),
            dev.get("site_name", ""),
            dev.get("street", ""),
            dev.get("city", ""),
            dev.get("state", ""),
            dev.get("zip_code", ""),
            dev.get("country", "")
        ])
    logging.debug("\n" + table.get_string())  # Log the table output for reference (debug mode only)

def generate_support_package():
    logging.info("Generating support package for each site...")

    # List of required CSV files and their generation functions
    required_files = [
        ("OrgAlarms.csv", export_open_org_alarms_to_csv),
        ("OrgDeviceEvents.csv", export_recent_device_events_to_csv),
        ("SiteList.csv", export_all_sites_to_csv),
        ("OrgDevices.csv", export_all_devices_to_csv),
        ("OrgDeviceStats.csv", export_device_stats_to_csv),
        ("OrgDevicePortStats.csv", export_device_port_stats_to_csv),
        ("AllGatewayTestResults.csv", export_gateway_test_results_by_site_to_csv),
    ]

    # Ensure all required files are fresh or regenerate them
    for filename, func in required_files:
        logging.debug(f"Checking freshness of {filename}...")
        check_and_generate_csv(filename, func)  # freshness_minutes now comes from .env

    # Ensure SiteList.csv is generated before loading
    check_and_generate_csv('SiteList.csv', export_all_sites_to_csv)

    # Load the pulled data into dictionaries
    logging.debug("Loading CSV data into dictionaries for support package assembly...")
    site_data = load_csv_grouped_by_key('SiteList.csv', 'id')
    alarms_data = load_csv_grouped_by_key('OrgAlarms.csv', 'site_id')
    events_data = load_csv_grouped_by_key('OrgDeviceEvents.csv', 'site_id')
    devices_data = load_csv_grouped_by_key('OrgDevices.csv', 'name')
    device_stats_data = load_csv_grouped_by_key('OrgDeviceStats.csv', 'site_id')
    port_stats_data = load_csv_grouped_by_key('OrgDevicePortStats.csv', 'site_id')

    # Load speedtest data if available
    gateway_test_results_path = get_csv_file_path('AllGatewayTestResults.csv')
    if os.path.exists(gateway_test_results_path):
        logging.debug("Loading AllGatewayTestResults.csv for speedtest data...")
        speedtest_data = load_csv_grouped_by_key('AllGatewayTestResults.csv', 'site_id')
    else:
        logging.warning("⚠️ AllGatewayTestResults.csv not found. Skipping speedtest data.")
        speedtest_data = {}

    # Create a support package for each site with alarms or events
    for site_id, site_info in site_data.items():
        # Only generate support package if there are alarms or events for the site
        if not alarms_data.get(site_id) and not events_data.get(site_id):
            logging.info(f"Skipping site {site_id} — no alarms or events.")
            continue

        logging.info(f"Generating support package for site: {site_id}")
        # Gather all relevant data for the site
        support_data = {
            'alarms': alarms_data.get(site_id, []),
            'events': events_data.get(site_id, []),
            'devices': devices_data.get(site_id, []),
            'device_stats': device_stats_data.get(site_id, []),
            'port_stats': port_stats_data.get(site_id, []),
            'speedtests': speedtest_data.get(site_id, []),
        }

        support_package_filename = f"SupportPackage_{site_id}.csv"
        logging.debug(f"Writing support package to {support_package_filename}...")
        write_support_data_to_csv(support_data, support_package_filename)
        logging.info(f"Support package written for site {site_id}.")

    logging.info("✅ Support packages generated for applicable sites.")
    logging.info("✅ Support packages generated for all sites!")

def load_csv_grouped_by_key(filename, key):
    """
    Loads CSV data into a dictionary keyed by the specified column.
    Each key maps to a list of rows (as dictionaries) that share the same key value.
    Adds logging for file loading and key distribution.
    """
    logging.info(f"Loading CSV file '{filename}' into dictionary keyed by '{key}'...")
    csv_file_path = get_csv_file_path(filename)
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)  # Create a CSV reader
        data_dict = {}  # Initialize an empty dictionary
        row_count = 0
        for row in reader:
            data_key = row.get(key)  # Get the value to use as the key
            if data_key is None:
                logging.warning(f"Row missing key '{key}': {row}")
                continue
            if data_key not in data_dict:
                data_dict[data_key] = []  # Initialize a list for this key
            data_dict[data_key].append(row)  # Add the row to the dictionary
            row_count += 1
        logging.info(f"Loaded {row_count} rows from '{filename}'. Found {len(data_dict)} unique keys for '{key}'.")
    return data_dict  # Return the dictionary

def write_support_data_to_csv(data, filename):
    """
    Writes the support package data (a dict of lists of dicts) to a CSV file.
    Each section in 'data' is a list of dictionaries. All unique keys across all sections are used as CSV columns.
    """
    logging.debug(f"Preparing to write support package to {filename}...")

    fieldnames = set()  # Initialize a set to collect all field names
    # Collect all unique field names from all sections
    for section_name, section in data.items():
        logging.debug(f"Processing section '{section_name}' with {len(section)} rows.")
        for row in section:
            fieldnames.update(row.keys())  # Add all keys to the fieldnames set
    fieldnames = sorted(fieldnames)  # Sort the fieldnames for consistent column order

    logging.debug(f"Final CSV fieldnames: {fieldnames}")

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)  # Create a CSV writer
        writer.writeheader()  # Write the header row
        row_count = 0
        for section_name, section in data.items():
            for row in section:
                writer.writerow(row)  # Write each row to the CSV file
                row_count += 1
        logging.info(f"Wrote {row_count} rows to {filename} for support package.")

    logging.info(f"Support package written to {filename}")  # Log completion of the file write

def poll_marvis_actions():
    """
    Interactive Marvis (VNA - Virtual Network Assistant) troubleshooting function that allows users to:
    1. Perform targeted troubleshooting for specific clients
    2. Perform targeted troubleshooting for specific devices
    3. Analyze network connectivity issues
    4. View Marvis insights and recommendations
    
    This function guides users through the Marvis troubleshooting process step by step,
    using guided selection workflows instead of manual MAC address entry.
    """
    logging.info("🔍 Starting Marvis (VNA) troubleshooting workflow...")
    logging.debug("MARVIS DEBUG: Entering poll_marvis_actions() function")
    print("🔍 Starting Marvis (VNA - Virtual Network Assistant) Troubleshooting")
    print("=" * 65)
    print()
    
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id} for Marvis troubleshooting")
    logging.debug(f"MARVIS DEBUG: Session state - authenticated: {apisession is not None}")

    print("📋 Marvis AI Troubleshooting Options:")
    print("1. Troubleshoot client connectivity issues (guided client selection)")
    print("2. Diagnose device performance problems (guided device selection)") 
    print("3. Analyze network connectivity issues (site-level analysis)")
    print("4. View organization Marvis insights and capabilities")
    print("5. Exit")
    print()
    
    choice = input("Select an option (1-5): ").strip()
    logging.debug(f"MARVIS DEBUG: User selected option: {choice}")
    
    if choice == "1":
        logging.debug("MARVIS DEBUG: Calling troubleshoot_client_connectivity()")
        troubleshoot_client_connectivity()
    elif choice == "2":
        logging.debug("MARVIS DEBUG: Calling troubleshoot_device_performance()")
        troubleshoot_device_performance()
    elif choice == "3":
        logging.debug("MARVIS DEBUG: Calling troubleshoot_network_connectivity()")
        troubleshoot_network_connectivity()
    elif choice == "4":
        logging.debug("MARVIS DEBUG: Calling view_marvis_insights()")
        view_marvis_insights()
    elif choice == "5":
        logging.debug("MARVIS DEBUG: User chose to exit")
        print("Exiting Marvis troubleshooting.")
        return
    else:
        print("❌ Invalid option selected.")
        logging.warning(f"MARVIS DEBUG: Invalid troubleshooting option selected: {choice}")
        logging.debug("MARVIS DEBUG: Exiting poll_marvis_actions() due to invalid choice")

def prompt_client_selection(site_id=None):
    """
    Prompts the user to select a client from available wireless or wired clients.
    
    Args:
        site_id (str, optional): If provided, searches within the specific site.
                                If None, searches across the entire organization.
    
    Returns:
        tuple: (client_mac, client_type, site_id) or (None, None, None) if no selection made
    """
    import time
    print("\n📱 Client Selection")
    print("=" * 30)
    
    # If no site_id provided, decide between site-specific or org-wide search
    if not site_id:
        scope_choice = input("Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ").strip().lower()
        if scope_choice == 's':
            site_id = prompt_site_selection()
            if not site_id:
                print("❌ No site selected.")
                return None, None, None
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        all_clients = []
        
        if site_id:
            # Site-specific client search
            print(f"🔍 Searching for clients in selected site...")
            
            # Get wireless clients for the site
            try:
                wireless_response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(apisession, site_id, limit=1000)
                wireless_clients = mistapi.get_all(response=wireless_response, mist_session=apisession) or []
                for client in wireless_clients:
                    client['client_type'] = 'wireless'
                    client['source_site_id'] = site_id
                all_clients.extend(wireless_clients)
                logging.info(f"Found {len(wireless_clients)} wireless clients in site")
            except Exception as e:
                logging.warning(f"Could not fetch wireless clients for site: {e}")
            
            # Get wired clients for the site (if API supports it)
            try:
                wired_response = mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(apisession, site_id, limit=1000)
                wired_clients = mistapi.get_all(response=wired_response, mist_session=apisession) or []
                for client in wired_clients:
                    client['client_type'] = 'wired'
                    client['source_site_id'] = site_id
                all_clients.extend(wired_clients)
                logging.info(f"Found {len(wired_clients)} wired clients in site")
            except Exception as e:
                logging.warning(f"Could not fetch wired clients for site (may not be supported): {e}")
                
        else:
            # Organization-wide client search
            print(f"🔍 Searching for clients across organization...")
            
            # Get wireless clients org-wide
            try:
                wireless_response = mistapi.api.v1.orgs.clients.searchOrgWirelessClients(apisession, org_id, limit=1000)
                wireless_clients = mistapi.get_all(response=wireless_response, mist_session=apisession) or []
                for client in wireless_clients:
                    client['client_type'] = 'wireless'
                all_clients.extend(wireless_clients)
                logging.info(f"Found {len(wireless_clients)} wireless clients in organization")
            except Exception as e:
                logging.warning(f"Could not fetch wireless clients for org: {e}")
            
            # Get wired clients org-wide
            try:
                wired_response = mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients(apisession, org_id, limit=1000)
                wired_clients = mistapi.get_all(response=wired_response, mist_session=apisession) or []
                for client in wired_clients:
                    client['client_type'] = 'wired'
                all_clients.extend(wired_clients)
                logging.info(f"Found {len(wired_clients)} wired clients in organization")
            except Exception as e:
                logging.warning(f"Could not fetch wired clients for org: {e}")
        
        if not all_clients:
            print("❌ No clients found.")
            return None, None, None
        
        # Sort clients by hostname, then MAC
        all_clients = sorted(all_clients, key=lambda x: (x.get('hostname', ''), x.get('mac', '')))
        
        # Prepare table for selection
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["#", "Hostname", "MAC Address", "Type", "IP Address", "SSID/VLAN", "Site", "Status"]
        table.align["#"] = "r"
        table.align["Hostname"] = "l"
        table.align["MAC Address"] = "l"
        table.align["Type"] = "c"
        table.align["IP Address"] = "l"
        table.align["SSID/VLAN"] = "l"
        table.align["Site"] = "l"
        table.align["Status"] = "c"
        # Set max widths for better formatting
        table.max_width["Hostname"] = 20
        table.max_width["IP Address"] = 16
        table.max_width["SSID/VLAN"] = 15
        table.max_width["Site"] = 15
        index_to_client = {}
        
        # Fetch site list once and cache it
        sites_cache = {}
        try:
            print("📍 Loading site information...")
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
            sites = mistapi.get_all(response=sites_response, mist_session=apisession)
            sites_cache = {site["id"]: site["name"] for site in sites}
            logging.info(f"Cached {len(sites_cache)} sites for client display")
        except Exception as e:
            logging.warning(f"Could not fetch sites for display: {e}")
        
        for idx, client in enumerate(all_clients):
            # Get site name from cache
            site_name = ""
            if 'site_id' in client and client['site_id'] in sites_cache:
                site_name = sites_cache[client['site_id']]
            elif 'site_id' in client:
                site_name = client['site_id']  # Fallback to site ID if name not found
            
            # Determine connection status
            status = "🟢" if client.get('connected', True) else "🔴"
            if 'last_seen' in client:
                last_seen = client.get('last_seen', 0)
                current_time = int(time.time())
                if current_time - last_seen > 300:  # More than 5 minutes ago
                    status = "🟡"
            
            # Format hostname/name
            hostname = client.get('hostname', client.get('name', ''))
            if not hostname or hostname in ['[]', '']:
                hostname = 'Unknown'
            if len(hostname) > 20:
                hostname = hostname[:17] + "..."
            
            # Format IP address - handle both strings and arrays
            ip_address = client.get('ip', '')
            if isinstance(ip_address, list):
                if ip_address:
                    ip_address = ip_address[0]  # Take first IP if multiple
                else:
                    ip_address = 'N/A'
            elif not ip_address or ip_address == '[]':
                ip_address = 'N/A'
            
            # Format SSID/VLAN - handle both strings and arrays
            ssid_vlan = client.get('ssid', client.get('vlan', ''))
            if isinstance(ssid_vlan, list):
                if ssid_vlan:
                    ssid_vlan = str(ssid_vlan[0])  # Take first value if multiple
                else:
                    ssid_vlan = 'N/A'
            elif not ssid_vlan or ssid_vlan == '[]':
                ssid_vlan = 'N/A'
            
            if len(ssid_vlan) > 15:
                ssid_vlan = ssid_vlan[:12] + "..."
            
            # Format site name with better truncation
            if len(site_name) > 15:
                site_name = site_name[:12] + "..."
            
            table.add_row([
                idx,
                hostname,
                client.get('mac', 'Unknown'),
                client.get('client_type', 'unknown')[:8],
                ip_address,
                ssid_vlan,
                site_name,
                status
            ])
            index_to_client[idx] = client
        
        print(f"\n📋 Found {len(all_clients)} clients:")
        print(table)
        
        # Show summary statistics
        wireless_count = sum(1 for c in all_clients if c.get('client_type') == 'wireless')
        wired_count = sum(1 for c in all_clients if c.get('client_type') == 'wired')
        print(f"\n📊 Summary: {wireless_count} wireless, {wired_count} wired clients")
        
        # Show legend
        print("\n🟢 = Online  🟡 = Recently seen  🔴 = Offline")
        print("---" * 20)
        
        # Get user selection
        try:
            max_index = len(all_clients) - 1
            user_input = input(f"\n🔍 Enter client index (0-{max_index}) or 'q' to quit: ").strip()
                
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("👋 Exiting client selection...")
                return None, None, None
                
            idx = int(user_input)
            if 0 <= idx <= max_index:
                selected_client = index_to_client[idx]
                client_mac = selected_client.get('mac')
                client_type = selected_client.get('client_type', 'unknown')
                client_site_id = selected_client.get('site_id', site_id)
                hostname = selected_client.get('hostname', selected_client.get('name', 'Unknown'))
                
                print(f"\n✅ Selected client:")
                print(f"   📱 Name: {hostname}")
                print(f"   🔗 MAC: {client_mac}")
                print(f"   📡 Type: {client_type}")
                if client_site_id and client_site_id in sites_cache:
                    print(f"   🏢 Site: {sites_cache[client_site_id]}")
                
                logging.info(f"User selected client: MAC={client_mac}, type={client_type}, site={client_site_id}")
                return client_mac, client_type, client_site_id
            else:
                print(f"❌ Invalid index. Please enter a number between 0 and {max_index}.")
                return None, None, None
                
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit.")
            return None, None, None
            
    except Exception as e:
        logging.error(f"Error during client selection: {e}")
        print(f"❌ Error searching for clients: {e}")
        return None, None, None

def troubleshoot_client_connectivity():
    """
    Troubleshoot client connectivity issues using Marvis AI.
    Uses guided client selection instead of manual MAC address entry.
    """
    print("\n🔍 Client Connectivity Troubleshooting")
    print("=" * 50)
    
    # Use guided client selection
    client_mac, client_type, site_id = prompt_client_selection()
    if not client_mac:
        print("❌ No client selected. Returning to main menu.")
        return
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        print(f"🔍 Running Marvis AI analysis for client {client_mac}...")
        print(f"   📱 Client Type: {client_type}")
        if site_id:
            print(f"   🏢 Site ID: {site_id}")
        
        logging.info(f"Starting Marvis client troubleshooting for MAC: {client_mac}, type: {client_type}, site: {site_id}")
        
        # Prepare parameters for troubleshoot call
        params = {"mac": client_mac}
        if site_id:
            params["site_id"] = site_id
            
        # Add client type parameter for proper troubleshooting context
        if client_type in ["wired", "wireless"]:
            params["type"] = client_type
            logging.debug(f"MARVIS DEBUG: Added type parameter: {client_type}")
        
        logging.debug(f"MARVIS DEBUG: About to call troubleshootOrg with params: {params}")
        
        # Call Marvis troubleshoot endpoint
        response = mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(apisession, org_id, **params)
        
        if response.data:
            print("✅ Marvis AI analysis completed!")
            print(f"📊 Analysis results available.")
            
            # Save results to CSV with optimized formatting
            data = format_marvis_data_for_csv(response.data, "client")
            
            filename = f"MarvisInsights_Client_{client_mac.replace(':', '')}_{client_type}.csv"
            save_data_to_output(data, filename)
            print(f"📄 Results saved to {filename}")
            
            # Display summary
            if isinstance(response.data, dict):
                if 'results' in response.data:
                    print("\n🔍 Marvis Analysis Summary:")
                    for result in response.data.get('results', []):
                        print(f"  • {result.get('description', 'Analysis result')}")
                        if result.get('action'):
                            print(f"    💡 Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    print("\n🤖 Marvis Insights:")
                    insights = response.data.get('insights', [])
                    for insight in insights:
                        print(f"  • {insight.get('description', insight)}")
                else:
                    print(f"\n📊 Analysis Data: {len(data)} items processed")
        else:
            print("ℹ️ No specific connectivity issues found for this client.")
            print("💡 This could indicate the client is functioning normally.")
            
    except Exception as e:
        logging.error(f"Failed to troubleshoot client {client_mac}: {e}")
        print(f"❌ Failed to troubleshoot client: {e}")
        print("💡 This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - The client is not currently active or found")
        print("   - Insufficient permissions for Marvis troubleshooting")
        print("   - API connectivity issues")

def troubleshoot_device_performance():
    """
    Troubleshoot device performance issues using Marvis AI.
    Uses guided site and device selection workflow.
    """
    logging.debug("MARVIS DEBUG: Entering troubleshoot_device_performance()")
    print("\n🔍 Device Performance Troubleshooting")
    print("=" * 50)
    
    # Get site selection first
    site_id = prompt_site_selection()
    if not site_id:
        print("❌ No site selected.")
        logging.debug("MARVIS DEBUG: No site selected for device troubleshooting")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected site_id: {site_id}")
    
    # Get device selection
    device_id = prompt_device_selection(site_id)
    if not device_id:
        print("❌ No device selected.")
        logging.debug("MARVIS DEBUG: No device selected")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected device_id: {device_id}")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id}")
    
    try:
        # Get device MAC address from device ID
        print(f"🔍 Looking up device details...")
        logging.debug(f"MARVIS DEBUG: About to get device details for device_id: {device_id} in site: {site_id}")
        
        device_response = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
        logging.debug(f"MARVIS DEBUG: Device lookup response status: {device_response.status if hasattr(device_response, 'status') else 'unknown'}")
        
        if not device_response.data:
            print("❌ Could not retrieve device details.")
            logging.debug("MARVIS DEBUG: Device response data is None")
            return
            
        logging.debug(f"MARVIS DEBUG: Device data keys: {list(device_response.data.keys()) if isinstance(device_response.data, dict) else 'not a dict'}")
        
        device_mac = device_response.data.get('mac')
        device_name = device_response.data.get('name', 'Unknown Device')
        
        logging.debug(f"MARVIS DEBUG: Device MAC: {device_mac}")
        logging.debug(f"MARVIS DEBUG: Device name: {device_name}")
        
        if not device_mac:
            print("❌ Could not determine device MAC address.")
            logging.debug("MARVIS DEBUG: Device MAC is None or empty")
            return
        
        print(f"🔍 Running Marvis AI performance analysis...")
        print(f"   📟 Device: {device_name} ({device_mac})")
        print(f"   🏢 Site ID: {site_id}")
        
        logging.info(f"Starting Marvis device performance analysis for device: {device_name} (MAC: {device_mac})")
        logging.debug(f"MARVIS DEBUG: About to call troubleshootOrg with mac={device_mac}, site_id={site_id}")
        
        # Call Marvis troubleshoot endpoint for device using MAC address
        response = mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(
            apisession, org_id, 
            mac=device_mac, 
            site_id=site_id
        )
        
        logging.debug(f"MARVIS DEBUG: Device troubleshoot response status: {response.status if hasattr(response, 'status') else 'unknown'}")
        logging.debug(f"MARVIS DEBUG: Device response data type: {type(response.data)}")
        logging.debug(f"MARVIS DEBUG: Device response data is None: {response.data is None}")
        
        if response.data:
            logging.debug(f"MARVIS DEBUG: Device response data keys: {list(response.data.keys()) if isinstance(response.data, dict) else 'not a dict'}")
            logging.debug(f"MARVIS DEBUG: Device response data: {json.dumps(response.data, indent=2, default=str)}")
            
            print("✅ Marvis AI device analysis completed!")
            
            # Save results to CSV with optimized formatting
            data = format_marvis_data_for_csv(response.data, "device")
            logging.debug(f"MARVIS DEBUG: Formatted device data length: {len(data) if data else 0}")
            
            filename = f"MarvisInsights_Device_{device_mac.replace(':', '')}_{device_name.replace(' ', '_')}.csv"
            save_data_to_output(data, filename)
            print(f"📄 Results saved to {filename}")
            
            # Display summary if available
            if isinstance(response.data, dict):
                if 'results' in response.data:
                    results = response.data.get('results', [])
                    logging.debug(f"MARVIS DEBUG: Found {len(results)} device results")
                    print("\n🔍 Device Performance Analysis:")
                    for result in results:
                        print(f"  • {result.get('description', 'Analysis result')}")
                        if result.get('action'):
                            print(f"    💡 Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    print("\n🤖 Marvis Device Insights:")
                    insights = response.data.get('insights', [])
                    logging.debug(f"MARVIS DEBUG: Found {len(insights)} device insights")
                    for insight in insights:
                        print(f"  • {insight.get('description', insight)}")
                else:
                    logging.debug("MARVIS DEBUG: No results or insights in device response")
                    print(f"\n📊 Analysis Data: {len(data)} items processed")
            
        else:
            logging.debug("MARVIS DEBUG: Device response data is None or empty")
            print("ℹ️ No performance issues detected for this device.")
            print("💡 This could indicate the device is operating within normal parameters.")
            
    except Exception as e:
        logging.error(f"MARVIS DEBUG: Exception in troubleshoot_device_performance: {e}")
        logging.error(f"MARVIS DEBUG: Exception type: {type(e)}")
        logging.error(f"MARVIS DEBUG: Exception traceback: ", exc_info=True)
        print(f"❌ Failed to troubleshoot device: {e}")
        print("💡 This may indicate:")
        print("   - The device is not found or not supported by Marvis")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - Insufficient permissions for device troubleshooting")
    
    logging.debug("MARVIS DEBUG: Exiting troubleshoot_device_performance()")

def troubleshoot_network_connectivity():
    """
    Troubleshoot general network connectivity issues using Marvis AI.
    Provides site-level network analysis and insights.
    """
    logging.debug("MARVIS DEBUG: Entering troubleshoot_network_connectivity()")
    print("\n🔍 Network Connectivity Troubleshooting")
    print("=" * 50)
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        print("❌ No site selected.")
        logging.debug("MARVIS DEBUG: No site selected, exiting network troubleshooting")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected site_id: {site_id}")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id}")
    
    try:
        print(f"🔍 Running Marvis AI network analysis...")
        print(f"   🌐 Analyzing site-level connectivity")
        print(f"   🏢 Site ID: {site_id}")
        
        logging.info(f"Starting Marvis network connectivity analysis for site: {site_id}")
        logging.debug(f"MARVIS DEBUG: About to call mistapi.api.v1.orgs.troubleshoot.troubleshootOrg with org_id={org_id}, site_id={site_id}")
        
        # Call Marvis troubleshoot endpoint for site
        response = mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(
            apisession, org_id, 
            site_id=site_id
        )
        
        logging.debug(f"MARVIS DEBUG: API response received. Status: {response.status if hasattr(response, 'status') else 'unknown'}")
        logging.debug(f"MARVIS DEBUG: Response data type: {type(response.data)}")
        logging.debug(f"MARVIS DEBUG: Response data is None: {response.data is None}")
        
        if response.data:
            logging.debug(f"MARVIS DEBUG: Response data keys: {list(response.data.keys()) if isinstance(response.data, dict) else 'not a dict'}")
            logging.debug(f"MARVIS DEBUG: Response data length: {len(response.data) if hasattr(response.data, '__len__') else 'no length'}")
            logging.debug(f"MARVIS DEBUG: Full response data structure: {json.dumps(response.data, indent=2, default=str) if response.data else 'None'}")
            
            print("✅ Marvis AI network analysis completed!")
            
            # Save results to CSV with optimized formatting
            logging.debug("MARVIS DEBUG: About to format data for CSV")
            data = format_marvis_data_for_csv(response.data, "network")
            logging.debug(f"MARVIS DEBUG: Formatted data length: {len(data) if data else 0}")
            logging.debug(f"MARVIS DEBUG: Formatted data sample: {data[:1] if data else 'empty'}")
            
            filename = f"MarvisInsights_Network_{site_id}.csv"
            save_data_to_output(data, filename)
            print(f"📄 Results saved to {filename}")
            logging.debug(f"MARVIS DEBUG: Saved data to {filename}")
            
            # Display summary if available
            if isinstance(response.data, dict):
                logging.debug("MARVIS DEBUG: Response data is a dict, checking for results/insights")
                if 'results' in response.data:
                    results = response.data.get('results', [])
                    logging.debug(f"MARVIS DEBUG: Found 'results' key with {len(results)} items")
                    print("\n🔍 Network Connectivity Analysis:")
                    for idx, result in enumerate(results):
                        logging.debug(f"MARVIS DEBUG: Processing result {idx}: {result}")
                        description = result.get('description', 'Analysis result') if isinstance(result, dict) else str(result)
                        print(f"  • {description}")
                        if isinstance(result, dict) and result.get('action'):
                            print(f"    💡 Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    insights = response.data.get('insights', [])
                    logging.debug(f"MARVIS DEBUG: Found 'insights' key with {len(insights)} items")
                    print("\n🤖 Marvis Network Insights:")
                    for idx, insight in enumerate(insights):
                        logging.debug(f"MARVIS DEBUG: Processing insight {idx}: {insight}")
                        description = insight.get('description', insight) if isinstance(insight, dict) else str(insight)
                        print(f"  • {description}")
                else:
                    logging.debug("MARVIS DEBUG: No 'results' or 'insights' keys found in response data")
                    logging.debug(f"MARVIS DEBUG: Available keys in response: {list(response.data.keys())}")
                    print(f"\n📊 Analysis Data: {len(data)} items processed")
                    if response.data:
                        print(f"🔍 Raw response keys: {list(response.data.keys())}")
                        # Show some raw data for debugging
                        for key, value in list(response.data.items())[:5]:
                            print(f"   {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                logging.debug(f"MARVIS DEBUG: Response data is not a dict, type: {type(response.data)}")
                print(f"\n📊 Raw response: {str(response.data)[:200]}{'...' if len(str(response.data)) > 200 else ''}")
            
        else:
            logging.debug("MARVIS DEBUG: Response data is None or empty")
            print("ℹ️ No network connectivity issues detected for this site.")
            print("💡 This indicates the network is operating within normal parameters.")
            
    except Exception as e:
        logging.error(f"MARVIS DEBUG: Exception in troubleshoot_network_connectivity: {e}")
        logging.error(f"MARVIS DEBUG: Exception type: {type(e)}")
        logging.error(f"MARVIS DEBUG: Exception traceback: ", exc_info=True)
        print(f"❌ Failed to troubleshoot network: {e}")
        print("💡 This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - The site has no devices or insufficient data for analysis")
        print("   - Insufficient permissions for network troubleshooting")
    
    logging.debug("MARVIS DEBUG: Exiting troubleshoot_network_connectivity()")

def view_marvis_insights():
    """
    View available Marvis (VNA) insights and capabilities for the organization.
    This provides information about Marvis availability and organizational insights.
    """
    print("\n📊 Marvis (VNA) Insights & Capabilities")
    print("=" * 50)
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        print("🔍 Checking Marvis availability and organizational insights...")
        
        # Try to get organization info to check Marvis capabilities
        org_response = mistapi.api.v1.orgs.orgs.getOrg(apisession, org_id)
        
        if org_response.data:
            org_info = org_response.data
            print(f"✅ Organization: {org_info.get('name', 'Unknown')}")
            
            # Check for Marvis-related features
            features = org_info.get('features', [])
            marvis_features = [f for f in features if any(keyword in f.lower() for keyword in ['marvis', 'vna', 'insight'])]
            
            if marvis_features:
                print("\n🤖 Marvis/VNA Features Available:")
                for feature in marvis_features:
                    print(f"  • {feature}")
            else:
                print("\nℹ️ No specific Marvis/VNA features detected in organization settings.")
            
            # Try to get organization-level insights if available
            try:
                print("\n� Attempting to retrieve organization-level insights...")
                
                # Try different insight endpoints that might be available
                insight_endpoints = [
                    ("Organization Sites SLE", lambda: mistapi.api.v1.orgs.insights.getOrgSitesSle(apisession, org_id)),
                ]
                
                insights_found = False
                for endpoint_name, endpoint_func in insight_endpoints:
                    try:
                        logging.debug(f"MARVIS DEBUG: Testing endpoint: {endpoint_name}")
                        response = endpoint_func()
                        logging.debug(f"MARVIS DEBUG: {endpoint_name} response status: {response.status if hasattr(response, 'status') else 'unknown'}")
                        logging.debug(f"MARVIS DEBUG: {endpoint_name} response data type: {type(response.data)}")
                        logging.debug(f"MARVIS DEBUG: {endpoint_name} response data is None: {response.data is None}")
                        
                        if response.data:
                            insights_data = response.data if isinstance(response.data, list) else [response.data]
                            logging.debug(f"MARVIS DEBUG: {endpoint_name} insights data length: {len(insights_data)}")
                            logging.debug(f"MARVIS DEBUG: {endpoint_name} full response: {json.dumps(response.data, indent=2, default=str)[:1000]}...")
                            
                            if insights_data:
                                print(f"\n📊 {endpoint_name}:")
                                for insight in insights_data[:5]:  # Show first 5 insights
                                    description = insight.get('description', insight.get('type', insight.get('name', str(insight))))
                                    print(f"  • {description}")
                                
                                if len(insights_data) > 5:
                                    print(f"  ... and {len(insights_data) - 5} more insights")
                                
                                # Save insights to CSV with optimized formatting
                                if "Sites SLE" in endpoint_name:
                                    # Use optimized formatting for Sites SLE data
                                    formatted_insights = format_marvis_data_for_csv(response.data, "sites")
                                else:
                                    # Use legacy formatting for other insight types
                                    formatted_insights = flatten_nested_fields_in_list(insights_data)
                                    formatted_insights = escape_multiline_strings_for_csv(formatted_insights)
                                
                                filename = f"MarvisInsights_{endpoint_name.replace(' ', '_')}.csv"
                                save_data_to_output(formatted_insights, filename)
                                print(f"  📄 Full insights saved to {filename}")
                                insights_found = True
                    except Exception as e:
                        error_message = str(e)
                        if "404" in error_message:
                            logging.debug(f"Endpoint {endpoint_name} not available for this organization (404): {e}")
                        elif "403" in error_message:
                            logging.debug(f"Access denied to {endpoint_name} (403): {e}")
                        else:
                            logging.debug(f"Could not fetch {endpoint_name}: {e}")
                        continue
                
                if not insights_found:
                    print("\nℹ️ No organization-level insights currently available.")
                
            except Exception as e:
                logging.warning(f"Could not retrieve organization insights: {e}")
                print(f"⚠️ Could not retrieve insights: {e}")
            
            print("\n💡 Marvis (VNA - Virtual Network Assistant) Usage Guide:")
            print("   🎯 Targeted Troubleshooting:")
            print("     • Use client troubleshooting for specific device connectivity issues")
            print("     • Use device troubleshooting for AP, switch, or gateway performance")
            print("     • Use network troubleshooting for site-wide connectivity analysis")
            print()
            print("   📋 Requirements:")
            print("     • Marvis must be enabled for your organization")
            print("     • Devices must be actively managed and reporting data")
            print("     • Sufficient data history for meaningful analysis")
            print()
            print("   🔧 Best Practices:")
            print("     • Run troubleshooting when issues are actively occurring")
            print("     • Provide specific timeframes when prompted")
            print("     • Review saved CSV files for detailed analysis results")
            
        else:
            print("❌ Could not retrieve organization information.")
            
    except Exception as e:
        logging.error(f"Failed to get Marvis insights: {e}")
        print(f"❌ Failed to get Marvis insights: {e}")
        print("💡 This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - Insufficient permissions to view organization details")
        print("   - API connectivity issues")
        print("   - Organization may not have Marvis licensing")
        print()
        print("🔗 Contact your Mist administrator to:")
        print("   • Verify Marvis/VNA licensing and enablement")
        print("   • Confirm user permissions for AI troubleshooting")
        print("   • Check organization feature settings")

def export_current_guest_users_to_csv():
    """
    Export all current guest users in the org to OrgCurrentGuests.csv
    """
    logging.info("Exporting all current guest users in the org...")  # Log start of function
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id} for current guest export.")

    # Call the Mist API to get current guest authorizations
    response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(apisession, org_id, limit=1000)
    guests = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"Fetched {len(guests)} current guest users from API.")

    # Flatten nested fields for CSV compatibility
    guests = flatten_nested_fields_in_list(guests)
    # Escape multiline strings for CSV compatibility
    guests = escape_multiline_strings_for_csv(guests)

    # Write the processed data to a CSV file
    save_data_to_output(guests, "OrgCurrentGuests.csv")
    logging.info("✅ Current guests exported to OrgCurrentGuests.csv")  # Log completion

def export_historical_guest_users_to_csv():
    """
    Export all guest users from the last 7 days to OrgHistoricalGuests.csv
    """
    logging.info("Exporting all guest users from the last 7 days...")  # Log start of function
    org_id = get_cached_or_prompted_org_id()
    # Calculate epoch for 7 days ago
    end_time = int(time.time())
    start_time = end_time - 7 * 24 * 3600
    logging.debug(f"Fetching guest authorizations from {start_time} to {end_time} (epoch seconds).")
    # Call the Mist API to get guest authorizations in the last 7 days
    response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(
        apisession, org_id, limit=1000, start=start_time, end=end_time
    )
    guests = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"Fetched {len(guests)} historical guest users from API.")
    # Flatten nested fields for CSV compatibility
    guests = flatten_nested_fields_in_list(guests)
    # Escape multiline strings for CSV compatibility
    guests = escape_multiline_strings_for_csv(guests)
    # Write the processed data to a CSV file
    save_data_to_output(guests, "OrgHistoricalGuests.csv")
    logging.info("✅ Historical guests exported to OrgHistoricalGuests.csv")  # Log completion

def export_switch_vc_stats_to_csv():
    """
    Export virtual chassis stats (including stacking cable info) for all switches in the org.
    """
    logging.info("Exporting all switch virtual chassis stats...")

    # Ensure OrgInventory.csv is fresh
    check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)

    # Load OrgInventory.csv and filter for switches that are virtual chassis (`vc_mac` present and not empty)
    inventory_path = get_csv_file_path("OrgInventory.csv")
    with open(inventory_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        switches = [row for row in reader if row.get("type") == "switch" and row.get("vc_mac", "").strip()]

    if not switches:
        logging.warning("No switches found in OrgInventory.csv.")
        return

    all_vc_stats = []

    for switch in tqdm(switches, desc="Switches", unit="switch"):
        site_id = switch.get("site_id")
        device_id = switch.get("id")
        name = switch.get("name", "")
        mac = switch.get("mac", "")
        model = switch.get("model", "")
        serial = switch.get("serial", "")

        # Log which switch is being processed
        logging.debug(f"Processing switch: name={name}, id={device_id}, site_id={site_id}, mac={mac}, model={model}, serial={serial}")

        if not site_id or not device_id:
            logging.warning(f"Skipping switch with missing site_id or device_id: name={name}, mac={mac}")
            continue

        try:
            # Get VC stats for this switch (returns a flat dict)
            vc_stats = mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(apisession, site_id, device_id).data
            logging.debug(f"Fetched VC stats for switch {name} ({device_id}): {vc_stats}")
            # Merge all switch info and VC info into a single dictionary
            entry = {**switch, **vc_stats}
            all_vc_stats.append(entry)
        except Exception as e:
            logging.warning(f"Failed to fetch VC stats for switch {name} ({device_id}): {e}")

    # Flatten and write to CSV
    logging.info(f"Flattening and sanitizing {len(all_vc_stats)} VC stats entries for CSV export.")
    all_vc_stats = flatten_nested_fields_in_list(all_vc_stats)
    all_vc_stats = escape_multiline_strings_for_csv(all_vc_stats)
    save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv")
    logging.info(f"✅ Switch VC stats exported to OrgSwitchVCStats.csv ({len(all_vc_stats)} records).")
    # Optionally log a preview of the data
    if all_vc_stats:
        logging.debug(f"Sample VC stats row: {all_vc_stats[0]}")
        # Display a summary PrettyTable for quick inspection
        table = PrettyTable()
        summary_fields = ["name", "mac", "model", "serial", "site_id", "vc_mac", "status", "members_0_vc_role", "members_1_vc_role"]
        table.field_names = [f for f in summary_fields if f in all_vc_stats[0]]

        for row in all_vc_stats:
            table.add_row([row.get(f, "") for f in table.field_names])
        logging.debug("\n" + table.get_string())  # Log the table output (debug mode only)

def prompt_select_site_and_device_ids(site_id=None, device_id=None):
    """
    Returns site_id and device_id, either from arguments or via interactive prompts.
    """
    if not site_id:
        site_id = prompt_select_site_id_from_csv()
        if not site_id:
            print("❌ No site selected.")
            return None, None

    if not device_id:
        device_id = prompt_select_device_id_from_inventory(site_id, device_type="all")
        if not device_id:
            print("❌ No device selected.")
            return None, None

    return site_id, device_id

def create_shell_session(site_id, device_id):
    """
    Creates a shell session and returns the WebSocket URL.
    """
    try:
        resp = mistapi.api.v1.sites.devices.createSiteDeviceShellSession(apisession, site_id, device_id)
        shell_data = resp.data

        return shell_data.get("url")
    except Exception as e:
        print(f"❌ Failed to create shell session: {e}")
        return None

def run_interactive_shell(shell_url, debug=False):
    if debug:
        websocket.enableTrace(True)

    print("🔌 Connecting to WebSocket shell...")
    ws = websocket.create_connection(shell_url)
    print("🟢 Connected.")

    screen = pyte.Screen(80, 40)
    stream = pyte.Stream(screen)

    def _resize():
        cols, rows = shutil.get_terminal_size()
        resize_msg = json.dumps({'resize': {'width': cols, 'height': rows}})
        if debug:
            print(f"[DEBUG] Sending resize: {resize_msg}")
        ws.send(resize_msg)

    def _ws_in():
        while ws.connected:
            try:
                data = ws.recv()
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                if debug:
                    print(f"[DEBUG] Raw recv: {repr(data)}")
                if data:
                    stream.feed(data)
                    for y in sorted(screen.dirty):
                        sys.stdout.write(f"\x1b[{y+1};1H")  # Move cursor to line y+1
                        sys.stdout.write(screen.display[y] + "\x1b[K")  # Clear to end of line
                    sys.stdout.flush()
                    screen.dirty.clear()
            except Exception as e:
                print(f'\n## Connection lost: {e} ##')
                return
    def _ws_out(key):
        if ws.connected:
            keymap = {
                "enter": "\n", "space": " ", "tab": "\t",
                "up": "\x00\x1b[A", "down": "\x00\x1b[B",
                "left": "\x00\x1b[D", "right": "\x00\x1b[C",
                               "backspace": "\x08"
            }
            if key == "~":
                print('\n## Exit from shell ##')
                ws.sock.shutdown(2)
                ws.sock.close()
                stop_listening()
                return
            k = keymap.get(key, key)
            data = f"\00{k}"
            data_byte = bytearray(map(ord, data))
            if debug:
                print(f"[DEBUG] Sending: {repr(data)}")
            try:
                ws.send_binary(data_byte)
            except Exception as e:
                print(f'\n## Send failed: {e} ##')
                return

    _resize()
    threading.Thread(target=_ws_in).start()

    # Wake up Juniper SSR prompt
   
    time.sleep(1)
    ws.send_binary(bytearray(map(ord, "\00\n\n")))
    if debug:
        print("[DEBUG] Sent wakeup sequence to Juniper SSRs")

    listen_keyboard(on_release=_ws_out, delay_second_char=0, delay_other_chars=0, lower=False)


    _resize()
    threading.Thread(target=_ws_in).start()

    # Wake up Juniper SSR prompt
    time.sleep(1)
    ws.send_binary(bytearray(map(ord, "\00\n\n")))
    if debug:
        print("[DEBUG] Sent wakeup sequence to Juniper SSRs")

    listen_keyboard(on_release=_ws_out, delay_second_char=0, delay_other_chars=0, lower=False)

def launch_cli_shell(site_id=None, device_id=None, debug=False):
    site_id, device_id = prompt_select_site_and_device_ids(site_id, device_id)
    if not site_id or not device_id:
        return
    shell_url = create_shell_session(site_id, device_id)
    if shell_url:
        run_interactive_shell(shell_url, debug=debug)

def listen_for_command_output(mist_host, mist_apitoken, site_id, device_id, session_id, timeout=30, idle_timeout=3, debug=False):
    if debug:
        websocket.enableTrace(True)

    ws_url = f"wss://{mist_host}/api-ws/v1/stream"
    headers = [f"Authorization: Token {mist_apitoken}"]
    subscribe_msg = {
        "subscribe": f"/sites/{site_id}/devices/{device_id}/cmd"
    }

    output_lines = []
    buffer = ""
    last_message_time = time.time()

    def on_message(ws, message):
        nonlocal last_message_time, buffer, output_lines
        last_message_time, buffer = _handle_ws_message(message, session_id, buffer, output_lines, debug)

    def on_close(ws, *args):
        _handle_ws_close(output_lines, debug)

    def on_error(ws, error):
        logging.error(f"❌ WebSocket error: {error}")

    def on_open(ws):
        logging.info("🔓 WebSocket opened. Subscribing...")
        ws.send(json.dumps(subscribe_msg))

    ws = websocket.WebSocketApp(
        ws_url,
        header=headers,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    def run_ws():
        ws.run_forever()

    ws_thread = threading.Thread(target=run_ws)
    ws_thread.start()

    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)
        if time.time() - last_message_time > idle_timeout and output_lines:
            logging.info("⏹️ Idle timeout reached. Closing WebSocket.")
            ws.close()
            break

    if ws.keep_running:
        logging.warning("⏱️ Timeout waiting for ARP output.")
        ws.close()

def _handle_ws_message(message, session_id, buffer, output_lines, debug=False):
    """Handle incoming WebSocket message with comprehensive error logging."""
    last_message_time = time.time()
    try:
        if debug:
            logging.debug(f"WebSocket raw message received: {message}")

        msg = json.loads(message)
        data_str = msg.get("data", "{}")
        data_obj = json.loads(data_str) if isinstance(data_str, str) else data_str
        inner_data = data_obj.get("data", {})
        if isinstance(inner_data, str):
            inner_data = json.loads(inner_data)

        if inner_data.get("session") == session_id:
            raw_output = inner_data.get("raw", "")
            buffer += raw_output
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                output_lines.append(line)
            if debug:
                logging.debug(f"Processed WebSocket data: {len(raw_output)} chars, buffer size: {len(buffer)}")

    except json.JSONDecodeError as e:
        logging.error(f"WebSocket message JSON decode error: {e}")
        if debug:
            logging.debug(f"Invalid JSON content: {message}")
    except KeyError as e:
        logging.warning(f"WebSocket message missing expected key: {e}")
        if debug:
            logging.debug(f"Message structure: {message}")
    except Exception as e:
        logging.error(f"Unexpected error parsing WebSocket message: {e}")
        if debug:
            logging.exception("Full WebSocket message parsing error:")

    return last_message_time, buffer

def _handle_ws_close(output_lines, debug=False):
    logging.info("🔌 WebSocket closed.")
    if output_lines:
        compiled_output = "\n".join(output_lines)
        _save_output_to_file(compiled_output)
        export_arp_output_to_csv("arp_output_raw.txt")


        print("\n📥 ARP Output Received:\n")
        rows = compiled_output.split("\n")
        parsed_rows = [row.split("\t") for row in rows if row.strip()]
        max_cols = max(len(row) for row in parsed_rows)
        for row in parsed_rows:
            while len(row) < max_cols:
                row.append("")
        table = PrettyTable()
        table.field_names = [f"Col {i+1}" for i in range(max_cols)]
        for row in parsed_rows:
            table.add_row(row)

        if debug:
            print(table)
            logging.info(f"📥 Compiled ARP Output:\n{compiled_output}")
            logging.debug("\n" + table.get_string())
        else:
            print(f"✅ ARP output received with {len(parsed_rows)} rows.")
    else:
        print("⚠️ No ARP output received for this session.")
        logging.warning("⚠️ No ARP output received for this session.")

def export_arp_output_to_csv(txt_filename="arp_output_raw.txt", csv1="arp_dataset1.csv", csv2="arp_dataset2.csv"):
    try:
        with open(txt_filename, "r", encoding="utf-8") as f:
            raw_text = f.read()

        lines = raw_text.splitlines()
        dataset1 = []
        dataset2 = []
        current_dataset = dataset1

        for line in lines:
            if "Total" in line:
                current_dataset = dataset2
            else:
                # Split on tabs and clean each field
                columns = [col.strip() for col in line.split("\t") if col.strip()]
                if columns:
                    current_dataset.append(columns)

        with open(csv1, 'w', newline='', encoding='utf-8') as f1:
            writer = csv.writer(f1)
            writer.writerows(dataset1)

        with open(csv2, 'w', newline='', encoding='utf-8') as f2:
            writer = csv.writer(f2)
            writer.writerows(dataset2)

        print(f"✅ Saved {len(dataset1)} rows to {csv1}")
        print(f"✅ Saved {len(dataset2)} rows to {csv2}")

    except Exception as e:
        print(f"❌ Failed to export ARP output to CSV: {e}")

def _save_output_to_file(compiled_output, filename="arp_output_raw.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(compiled_output)
        logging.info(f"📄 ARP output saved to {filename}")
    except Exception as e:
        logging.error(f"❌ Failed to save ARP output to file: {e}")

def trigger_arp_command(mist_host, mist_apitoken, site_id, device_id):
    url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"
    headers = {'Authorization': f'Token {mist_apitoken}'}
    response = requests.post(url, headers=headers, json={})

    if response.status_code == 200:
        session_id = response.json().get("session")
        print(f"✅ ARP command triggered. Session ID: {session_id}")
        return session_id
    else:
        print(f"❌ Failed to trigger ARP command: {response.status_code}")
        print(response.text)
        return None

def run_arp_via_websocket(site_id=None, device_id=None):
    if not site_id or not device_id:
        site_id, device_id = prompt_select_site_and_device_ids(site_id, device_id)
    if not site_id or not device_id:
        return

    # Retrieve mist_host and mist_apitoken from the apisession or environment
    mist_host = getattr(apisession, "host", None) or os.getenv("MIST_HOST")
    mist_apitoken = getattr(apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")

    if not mist_host or not mist_apitoken:
        print("❌ Mist host or API token not found in session or environment.")
        return

    print("🔌 Subscribing to WebSocket stream...")
    session_id = trigger_arp_command(mist_host, mist_apitoken, site_id, device_id)
    if session_id:
        listen_for_command_output(mist_host.replace("api.", "api-ws."), mist_apitoken, site_id, device_id, session_id)

def loop_refresh_core_datasets(delay=None, debug=False):
    """
    Continuously refreshes core datasets with optional dynamic delay based on API usage.
    If delay is None, it will be calculated dynamically to avoid exceeding API limits.
    Loop can be stopped gracefully by creating a file named 'stop_loop.txt'.
    """
    logging.info("🔁 Starting continuous data refresh loop...")
    smoothed = None  # Initialize smoothed delay tracker
    get_cached_or_prompted_org_id()  # Ensure org_id is loaded from .env if not already

    try:
        while True:
            if os.path.exists("stop_loop.txt"):
                logging.info("🛑 Stop signal detected (stop_loop.txt). Exiting loop.")
                break

            export_all_sites_to_csv()
            export_device_inventory_to_csv()
            export_device_stats_to_csv()
            export_device_port_stats_to_csv()
            export_vpn_peer_stats_to_csv()
            logging.info("✅ All datasets refreshed.")

            # Determine delay
            if delay is not None:
                actual_delay = delay
            else:
                smoothed, actual_delay = get_rate_limited_delay(smoothed)

            logging.info(f"⏳ Sleeping for {actual_delay:.2f} seconds...")
            time.sleep(actual_delay)

    except KeyboardInterrupt:
        logging.info("🛑 Loop interrupted by user (Ctrl+C). Exiting gracefully.")

def load_pid_tuning_data():
    """Load PID tuning data from file with comprehensive logging."""
    logging.debug(f"ENTRY: load_pid_tuning_data()")
    
    if os.path.exists(tuning_data_file):
        try:
            logging.debug(f"File I/O: Attempting to read PID tuning data from {tuning_data_file}")
            with open(tuning_data_file, 'r') as f:
                data = json.load(f)
            
            # Validate and clean error history
            if "error" in data and isinstance(data["error"], list):
                cleaned_errors = []
                for err in data["error"]:
                    if isinstance(err, (int, float)) and not (math.isnan(err) or math.isinf(err)):
                        cleaned_errors.append(float(err))
                data["error"] = cleaned_errors
            else:
                data["error"] = []
                
            logging.debug(f"File I/O: Successfully loaded PID tuning data from {tuning_data_file}")
            logging.debug(f"EXIT: load_pid_tuning_data - loaded from file")
            return data
        except json.JSONDecodeError as e:
            logging.error(f"File I/O: Failed to parse JSON in {tuning_data_file}: {e}. Using defaults.")
        except OSError as e:
            logging.error(f"File I/O: OS error reading {tuning_data_file}: {e}. Using defaults.")
        except Exception as e:
            logging.error(f"File I/O: Unexpected error reading {tuning_data_file}: {e}. Using defaults.")
    else:
        logging.debug(f"File I/O: {tuning_data_file} does not exist, using defaults")
        
    logging.debug(f"EXIT: load_pid_tuning_data - using defaults")
    return {"k_p": 0.1, "k_i": 0.0005, "error": [], "integral": 0.0}

def save_pid_tuning_data(data):
    """Save PID tuning data to file with comprehensive logging."""
    logging.debug(f"ENTRY: save_pid_tuning_data(data_keys={list(data.keys()) if data else []})")
    
    try:
        logging.debug(f"File I/O: Attempting to write PID tuning data to {tuning_data_file}")
        with open(tuning_data_file, 'w') as f:
            json.dump(data, f, indent=2)
        logging.debug(f"File I/O: Successfully wrote PID tuning data to {tuning_data_file}")
        logging.debug(f"EXIT: save_pid_tuning_data - success")
    except OSError as e:
        logging.error(f"File I/O: OS error writing to {tuning_data_file}: {e}")
        logging.debug(f"EXIT: save_pid_tuning_data - OS error")
        raise
    except Exception as e:
        logging.error(f"File I/O: Unexpected error writing to {tuning_data_file}: {e}")
        logging.debug(f"EXIT: save_pid_tuning_data - unexpected error")
        raise

def adjust_gains(data):
    """
    Adjusts PID gains based on the trend of recent errors.
    If error is increasing (positive trend), increase gains.
    If error is decreasing (negative trend), decrease gains.
    """
    recent_errors = data["error"][-10:]
    if not recent_errors:
        return

    error_trend = sum(recent_errors) / len(recent_errors)

    if error_trend > 0:
        data["k_p"] *= 1.05
        data["k_i"] *= 1.05
    elif error_trend < 0:
        data["k_p"] *= 0.95
        data["k_i"] *= 0.95

    # Clamp gains to prevent runaway values
    data["k_p"] = min(max(data["k_p"], 1e-6), 1.0)
    data["k_i"] = min(max(data["k_i"], 1e-8), 0.01)

def compute_dynamic_alpha(errors, min_alpha=0.1, max_alpha=0.9):
    """
    Computes a dynamic smoothing factor alpha based on the standard deviation of recent errors.
    """
    if len(errors) < 2:
        return 0.3  # default fallback
    
    try:
        # Ensure errors is a list of numbers and convert to numpy array safely
        recent_errors = errors[-10:]
        # Convert to float64 explicitly to avoid type conversion issues
        error_array = np.array(recent_errors, dtype=np.float64)
        std_dev = np.std(error_array)
        normalized = min(std_dev / 50, 1.0)  # adjust divisor to control sensitivity
        alpha = min_alpha + (max_alpha - min_alpha) * normalized
        return round(alpha, 3)
    except Exception as e:
        logging.warning(f"Failed to compute dynamic alpha: {e}. Using fallback value.")
        return 0.3

    """
    Launches a shell session, runs 'show route 0.0.0.0 | display json | no-more',
    and saves the output to ws.log.
    """
    logging.info("Launching shell to run 'show route 0.0.0.0'...")
    site_id, device_id = prompt_select_site_and_device_ids()
    if not site_id or not device_id:
        return

    shell_url = create_shell_session(site_id, device_id)
    if not shell_url:
        logging.error("❌ Could not create shell session.")
        return

    try:
        ws = websocket.create_connection(shell_url)
        print("🟢 Connected to shell session.")
        time.sleep(1)
        command = "show route 0.0.0.0 | display json | no-more\n"
        ws.send_binary(bytearray(map(ord, f"\00{command}")))

        output_lines = []
        while True:
            data = ws.recv()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            output_lines.append(data)
            print(data, end="")
            if "DONE!" in data or "mist@" in data:
                break
        ws.close()

        with open("ws.log", "w", encoding="utf-8") as f:
            f.write("".join(output_lines))
        print("✅ WebSocket output saved to ws.log")

    except Exception as e:
        print(f"❌ Error during shell session: {e}")

def export_gateway_templates_to_csv():
    """template_lookup = {t["id"]: t.get("name", "Unknown") for t in templates if "id" in t}
    Fetches and exports all gateway templates in the organization to OrgGatewayTemplates.csv.
    """
    logging.info("Starting export of gateway templates...")
    fetch_and_display_api_data(
        title="Org Gateway Templates:",
        api_call=mistapi.api.v1.orgs.gateway_templates.listOrgGatewayTemplates,
        filename="OrgGatewayTemplates.csv",
        sort_key="name",
        limit=1000
    )
    logging.info("✅ Gateway templates exported to OrgGatewayTemplates.csv.")

def show_dhcp_security_binding():
    """
    Launches a shell session and runs 'show dhcp-security binding' on the selected device.
    Saves output to ws_dhcp.log.
    """
    logging.info("Launching shell to run 'show dhcp-security binding'...")
    site_id, device_id = prompt_select_site_and_device_ids()
    if not site_id or not device_id:
        return

    shell_url = create_shell_session(site_id, device_id)
    if not shell_url:
        logging.error("❌ Could not create shell session.")
        return

    try:
        ws = websocket.create_connection(shell_url)
        print("🟢 Connected to shell session.")
        time.sleep(1)
        command = "show dhcp-security binding | display json | no-more\nDONE!"
        ws.send_binary(bytearray(map(ord, f"\00{command}")))

        output_lines = []
        while True:
            data = ws.recv()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            output_lines.append(data)
            print(data, end="")
            if "DONE!" in data:
                break
        ws.close()

        with open("ws_dhcp.log", "w", encoding="utf-8") as f:
            f.write("".join(output_lines))
        print("✅ DHCP security binding output saved to ws_dhcp.log")

    except Exception as e:
        print(f"❌ Error during shell session: {e}")

def show_vlans():
    """
    Launches a shell session and runs 'show vlans' on the selected device.
    Saves output to ws_vlans.log.
    """
    logging.info("Launching shell to run 'show vlans'...")
    site_id, device_id = prompt_select_site_and_device_ids()
    if not site_id or not device_id:
        return

    shell_url = create_shell_session(site_id, device_id)
    if not shell_url:
        logging.error("âŒ Could not create shell session.")
        return

    try:
        ws = websocket.create_connection(shell_url)
        print("Connected to shell session.")
        time.sleep(1)
        command = "show vlans | display json | no-more\nDONE!"
        ws.send_binary(bytearray(map(ord, f"\00{command}")))

        output_lines = []
        while True:
            data = ws.recv()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            output_lines.append(data)
            print(data, end="")
            if "DONE!" in data:
                break
        ws.close()

        with open("ws_vlans.log", "w", encoding="utf-8") as f:
            f.write("".join(output_lines))
        print("VLANs output saved to ws_vlans.log")

    except Exception as e:
        print(f"Error during shell session: {e}")

def append_delay_metrics_log(delay_metrics, api_cache, tuning_data, filename="delay_metrics.json", max_entries=100):
    """
    Appends delay metrics, API cache, and tuning data to a JSON file.
    Each call writes a new line with a timestamped entry.
    Maintains only the last max_entries (default 100) to prevent unlimited file growth.
    """
    logging.debug(f"ENTRY: append_delay_metrics_log(filename={filename}, max_entries={max_entries})")
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "delay_metrics": delay_metrics,
        "api_cache": api_cache,
        "tuning_data": tuning_data
    }
    
    try:
        # Read existing entries if file exists
        existing_entries = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            existing_entries.append(json.loads(line))
                logging.debug(f"File I/O: Loaded {len(existing_entries)} existing entries from {filename}")
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"File I/O: Failed to read existing entries from {filename}: {e}. Starting fresh.")
                existing_entries = []
        
        # Add new entry and keep only the last max_entries
        existing_entries.append(log_entry)
        if len(existing_entries) > max_entries:
            existing_entries = existing_entries[-max_entries:]
            logging.debug(f"File I/O: Trimmed to last {max_entries} entries")
        
        # Write all entries back to file
        logging.debug(f"File I/O: Writing {len(existing_entries)} entries to {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            for entry in existing_entries:
                json.dump(entry, f)
                f.write("\n")
        
        logging.debug(f"File I/O: Successfully updated delay metrics in {filename}")
        logging.debug(f"EXIT: append_delay_metrics_log - success")
    except OSError as e:
        logging.error(f"File I/O: OS error writing delay metrics to {filename}: {e}")
        logging.debug(f"EXIT: append_delay_metrics_log - OS error")
    except Exception as e:
        logging.error(f"File I/O: Failed to write delay metrics to {filename}: {e}")
        logging.debug(f"EXIT: append_delay_metrics_log - error")

def export_gateway_device_configs_to_csv(debug=False, fast=False):
    """
    Fetches and exports configuration details for all gateway devices across all sites in the organization
    to AllSiteGatewayConfigs.csv. Also generates a filtered CSV with selected fields and port info.
    """
    logging.info("Starting export of all gateway device configurations...")
    org_id = get_cached_or_prompted_org_id()
    data = fetch_gateway_device_configs_from_api(apisession, org_id, fast=fast)
    if not data:
        logging.warning("⚠️ No device configs found.")
        return

    # Flatten and sanitize the data
    flattened = flatten_nested_fields_in_list(data)
    sanitized = escape_multiline_strings_for_csv(flattened)

    # Write full dataset to CSV
    save_data_to_output(sanitized, "AllSiteGatewayConfigs.csv")
    logging.info("✅ Device configs saved to AllSiteGatewayConfigs.csv")

    # Identify port config columns (excluding _vpn_paths_)
    base_columns = ["mac", "name"]
    port_columns = [
        col for col in sanitized[0].keys()
        if re.match(r"(?i)port_config_ge-0/0/\d+_.*", col) and "_vpn_paths_" not in col
    ]
    columns_to_keep = base_columns + port_columns

    # Filter rows where any port column has non-empty value
    filtered_rows = [
        {col: row.get(col, "") for col in columns_to_keep}
        for row in sanitized
        if any(row.get(col) not in [None, "", "null"] for col in port_columns)
    ]

    # Write filtered dataset to CSV
    if not filtered_rows:
        logging.warning("⚠️ No rows matched the port config filter. FilteredGatewayPortConfigs.csv will be empty.")
        filtered_csv_path = get_csv_file_path("FilteredGatewayPortConfigs.csv")
        with open(filtered_csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("No matching data found.\n")
    else:
        if debug:
            logging.debug(f"Sample filtered row: {filtered_rows[0]}")
        save_data_to_output(filtered_rows, "FilteredGatewayPortConfigs.csv")
        logging.info("✅ Filtered gateway port configs saved to FilteredGatewayPortConfigs.csv")

def fetch_gateway_device_configs_from_api(apisession, org_id, fast=False, max_workers=None):
    """
    Fetches configuration details for all gateway devices in the org using org inventory.
    If `fast` is True, fetches each device config concurrently using a thread per device.
    
    Args:
        apisession: Authenticated Mist API session.
        org_id: Organization ID.
        fast (bool): If True, enables high-concurrency mode.
        max_workers (int): Optional override for number of concurrent threads.
    
    Returns:
        List of device configuration dictionaries.
    """
    logging.info("Fetching org inventory to find gateway devices...")
    try:
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)
        inventory = mistapi.get_all(response=response, mist_session=apisession)
    except Exception as e:
        logging.error(f"❌ Failed to fetch org inventory: {e}")
        return []

    logging.info(f"Found {len(inventory)} total devices in org inventory.")

    # Load site names from SiteList.csv for enrichment
    site_name_lookup = {}
    try:
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            site_name_lookup = {row.get("id"): row.get("name", "Unnamed Site") for row in reader}
    except Exception as e:
        logging.warning(f"⚠️ Failed to load SiteList.csv for site names: {e}")

    # Filter for gateway devices and build work list
    work_items = []
    for device in inventory:
        if device.get("type") == "gateway":
            site_id = device.get("site_id")
            device_id = device.get("id")
            if site_id and device_id:
                site_name = site_name_lookup.get(site_id, "Unknown")
                work_items.append((site_id, device_id, site_name))

    logging.info(f"Prepared {len(work_items)} gateway device config API calls.")

    def fetch_config(site_id, device_id, site_name):
        try:
            config = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id).data
            config["site_id"] = site_id
            config["site_name"] = site_name
            logging.info(f"✅ Fetched config for device {device_id} at site {site_name}")
            return config
        except Exception as e:
            logging.warning(f"⚠️ Failed to fetch config for device {device_id} at site {site_name}: {e}")
            return None
    all_device_configs = []

    if fast:
        max_threads = max_workers or os.cpu_count() or 8
        logging.info(f"🚀 Fast mode enabled: launching {len(work_items)} tasks with up to {max_threads} threads.")
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(fetch_config, sid, did, sname) for sid, did, sname in work_items]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching Configs", unit="device"):
                result = future.result()
                if result:
                    all_device_configs.append(result)
    else:
        logging.info("🐢 Fast mode disabled: using sequential rate-limited execution.")
        smoothed = None
        for site_id, device_id, site_name in tqdm(work_items, desc="Fetching Configs", unit="device"):
            smoothed, delay = get_rate_limited_delay(smoothed)
            logging.info(f"[INFO] Sleeping for {delay:.2f} seconds.")
            time.sleep(delay)
            result = fetch_config(site_id, device_id, site_name)
            if result:
                all_device_configs.append(result)

    logging.info(f"✅ Completed fetching {len(all_device_configs)} gateway device configs.")
    return all_device_configs

def get_rate_limited_delay(smoothed_delay=None):
    """
    Calculates an appropriate delay for API rate limiting using PID control.
    Includes comprehensive logging for tuning and backoff mechanisms.
    """
    logging.debug(f"ENTRY: get_rate_limited_delay(smoothed_delay={smoothed_delay})")
    
    global _api_usage_cache
    tuning_data = load_pid_tuning_data()
    logging.debug(f"Loaded PID tuning data: k_p={tuning_data.get('k_p')}, k_i={tuning_data.get('k_i')}, integral={tuning_data.get('integral')}")

    # Reset gains if out of bounds
    if tuning_data["k_p"] < 1e-6 or tuning_data["k_i"] < 1e-8 or tuning_data["k_p"] > 1.0 or tuning_data["k_i"] > 0.01:
        logging.warning(f"PID gains out of bounds, resetting: k_p={tuning_data['k_p']}, k_i={tuning_data['k_i']}")
        tuning_data["k_p"] = 0.1
        tuning_data["k_i"] = 0.001

    k_p = float(tuning_data["k_p"])
    k_i = float(tuning_data["k_i"])
    delay_integral = float(tuning_data.get("integral", 0.0))
    error_history = tuning_data.get("error", [])

    try:
        now = datetime.now(timezone.utc)
        current_time = time.time()
        elapsed = current_time - _api_usage_cache["last_updated"]
        previous_elapsed = float(_api_usage_cache.get("previous_elapsed", elapsed))

        # Hybrid refresh trigger: every 60s, every 100 requests, or top of the hour
        refresh_needed = (
            not _api_usage_cache["initialized"]
            or _api_usage_cache["perceived_requests"] >= 100
            or elapsed > 60
            or (now.minute == 0 and now.second < 5)
        )
        
        if refresh_needed:
            logging.debug(f"Refreshing API usage cache - elapsed: {elapsed:.1f}s, perceived_requests: {_api_usage_cache['perceived_requests']}")
            try:
                usage = mistapi.api.v1.self.usage.getSelfApiUsage(apisession).data
                _api_usage_cache["used"] = usage.get("requests", 0)
                _api_usage_cache["limit"] = usage.get("request_limit", 5000)
                _api_usage_cache["last_updated"] = current_time
                _api_usage_cache["perceived_requests"] = 0
                _api_usage_cache["initialized"] = True
                logging.debug(f"API usage refreshed: {_api_usage_cache['used']}/{_api_usage_cache['limit']} requests")
            except Exception as api_e:
                logging.warning(f"Failed to refresh API usage data: {api_e}. Using cached values.")
        else:
            estimated_growth = round((_api_usage_cache["limit"] / 3600) * elapsed)
            _api_usage_cache["used"] += estimated_growth
            _api_usage_cache["last_updated"] = current_time
            _api_usage_cache["perceived_requests"] += 1
            logging.debug(f"Using estimated API usage: {_api_usage_cache['used']}/{_api_usage_cache['limit']} requests")

        used = min(_api_usage_cache["used"], _api_usage_cache["limit"])
        limit = _api_usage_cache["limit"]

        seconds_elapsed = now.minute * 60 + now.second + now.microsecond / 1_000_000
        seconds_remaining = max(3600 - seconds_elapsed, 1)
        ideal_used = (seconds_elapsed / 3600) * limit
        error = used - ideal_used

        # Detect hour boundary and decay integral
        if seconds_elapsed < previous_elapsed:
            logging.info("🕒 Hour boundary crossed. Resetting integral.")
            logging.debug(f"Before reset: delay_integral={delay_integral} (type: {type(delay_integral)})")
            delay_integral *= 0.5
            logging.debug(f"After reset: delay_integral={delay_integral} (type: {type(delay_integral)})")

        _api_usage_cache["previous_elapsed"] = seconds_elapsed

        remaining_requests = max(limit - used, 1)
        base_delay = min(seconds_remaining / remaining_requests, 10)

        unsat_delay = base_delay + k_p * error + k_i * delay_integral
        sat_delay = max(min(unsat_delay, 10), 0.01)

        # Log backoff calculation details
        if sat_delay > 2.0:
            logging.warning(f"High delay calculated: {sat_delay:.3f}s (base: {base_delay:.3f}s, error: {error:.1f}, used: {used}/{limit})")
        elif sat_delay > 1.0:
            logging.info(f"Moderate delay calculated: {sat_delay:.3f}s (used: {used}/{limit})")
        else:
            logging.debug(f"Normal delay calculated: {sat_delay:.3f}s (used: {used}/{limit})")

        # Adaptive back_calc_gain
        back_calc_gain = min(max(abs(sat_delay - unsat_delay) / 10, 0.01), 0.5)

        # Decaying integral update
        decay_factor = 0.98
        delay_integral = delay_integral * decay_factor + back_calc_gain * (sat_delay - unsat_delay)
        delay_integral = max(min(delay_integral, 1000), -1000)

        # Ensure error is a valid number before adding to history
        if isinstance(error, (int, float)) and not (math.isnan(error) or math.isinf(error)):
            error_history.append(float(error))
        else:
            logging.warning(f"Invalid error value: {error}. Skipping addition to error history.")
        
        # Clean error_history before computing alpha to ensure all values are numeric
        cleaned_error_history = []
        for err in error_history:
            try:
                # Try to convert to float
                if err is not None:
                    float_val = float(err)
                    # Check if it's a valid finite number
                    if not (math.isnan(float_val) or math.isinf(float_val)):
                        cleaned_error_history.append(float_val)
            except (ValueError, TypeError):
                # Skip values that can't be converted to float
                continue
        
        logging.debug(f"About to call compute_dynamic_alpha with cleaned_error_history={cleaned_error_history} (length: {len(cleaned_error_history)})")
        alpha = compute_dynamic_alpha(cleaned_error_history)
        logging.debug(f"compute_dynamic_alpha returned: {alpha} (type: {type(alpha)})")

        smoothed_delay = sat_delay if smoothed_delay is None else alpha * sat_delay + (1 - alpha) * smoothed_delay
        delay_in_seconds = max(smoothed_delay, 0.01)

        logging.info(f"Rate limiting: sleeping for {delay_in_seconds:.3f} seconds")

        # Save updated tuning data using cleaned error history
        tuning_data["error"] = cleaned_error_history[-20:]  # Use cleaned history and keep only last 20 entries
        tuning_data["integral"] = delay_integral
        tuning_data["back_calc_gain"] = back_calc_gain
        adjust_gains(tuning_data)
        save_pid_tuning_data(tuning_data)

        delay_metrics = {
            "used": used,
            "limit": limit,
            "error": error,
            "base_delay": base_delay,
            "unsat_delay": unsat_delay,
            "final_delay": delay_in_seconds,
            "alpha": alpha
        }
        append_delay_metrics_log(delay_metrics, _api_usage_cache, tuning_data)

        logging.debug(f"EXIT: get_rate_limited_delay - delay: {delay_in_seconds:.3f}s")
        return smoothed_delay, delay_in_seconds

    except Exception as e:
        logging.error(f"Failed to calculate dynamic delay: {e}. Using default 500ms fallback delay.")
        logging.debug(f"EXIT: get_rate_limited_delay - error fallback")
        return smoothed_delay, 0.5

def export_combined_inventory_with_site_info():
    """
    Combines fresh AllDevicesWithSiteInfo data into multiple CSV files
    grouped by calendar week based on 'created_time' field.
    Also generates a summary report with device counts per week.
    """
    from collections import defaultdict

    # Load environment variables
    load_dotenv()
    END_CUSTOMER_NAME = os.getenv("END_CUSTOMER_NAME")
    END_CUSTOMER_ACCOUNT_ID = os.getenv("END_CUSTOMER_ACCOUNT_ID")

    # Always regenerate fresh data
    export_devices_with_site_info_to_csv()

    # Load the enriched device + site info
    devices_with_site_info_path = get_csv_file_path("AllDevicesWithSiteInfo.csv")
    with open(devices_with_site_info_path, mode="r", encoding="utf-8") as f:
        site_configs = list(csv.DictReader(f))

    # Create a subfolder for weekly CSV files
    output_folder = "CombinedInventory_ByWeek"
    os.makedirs(output_folder, exist_ok=True)

    # Initialize data structures for weekly grouping and summary
    weekly_data = defaultdict(list)
    summary_data = defaultdict(int)

    # Process each device entry
    for device in site_configs:
        try:
            created_time = int(device.get("created_time", 0))
            created_date = datetime.fromtimestamp(created_time, tz=timezone.utc)
            year, week, _ = created_date.isocalendar()
            week_key = f"{year}_Week_{week:02d}"

            weekly_data[week_key].append({
                "Full Site": device.get("site_name", ""),
                "System Serial Number": device.get("serial", ""),
                "System Model Number": device.get("model", ""),
                "End Customer Name": END_CUSTOMER_NAME,
                "Address Line 1": device.get("street", ""),
                "Address Line 2": "",
                "City": device.get("city", ""),
                "State": device.get("state", ""),
                "Country": device.get("country", "US"),
                "Zip Code / Postal Code": device.get("zip_code", ""),
                "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID
            })

            summary_data[(year, week)] += 1
        except Exception as e:
            logging.warning(f"⚠️ Skipping device due to error: {e}")

    # Define output CSV columns
    fieldnames = [
        "Full Site", "System Serial Number", "System Model Number", "End Customer Name",
        "Address Line 1", "Address Line 2", "City", "State", "Country",
        "Zip Code / Postal Code", "End Customer Account ID"
    ]

    # Write weekly CSV files
    for week_key, rows in weekly_data.items():
        output_file = os.path.join(output_folder, f"{week_key}.csv")
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    # Write summary report
    summary_file = os.path.join(output_folder, "CombinedInventory_Summary.csv")
    with open(summary_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Week", "Device Count"])
        for (year, week), count in sorted(summary_data.items()):
            writer.writerow([year, week, count])

    print("✅ CombinedInventory_ByWeek folder and summary report have been generated.")

def normalize_zip_code(zip_code):
    """
    Normalizes a zip code to compare only the first 5 digits:
    - Removes everything after and including a dash
    - If only 4 digits before dash, prepends a '0'
    - Returns first 5 digits only
    """
    if not zip_code:
        return ""
    
    # Convert to string and strip whitespace
    zip_str = str(zip_code).strip()
    
    # Remove everything after and including a dash
    if '-' in zip_str:
        zip_str = zip_str.split('-')[0]
    
    # Remove any non-digit characters
    zip_digits = ''.join(filter(str.isdigit, zip_str))
    
    # If only 4 digits, prepend a '0'
    if len(zip_digits) == 4:
        zip_digits = '0' + zip_digits
    
    # Return first 5 digits
    return zip_digits[:5]

def compare_inventory_with_csv():
    """
    Compares combined inventory data with site info against a user-selected CSV file.
    Shows items where zip code and serial number don't match between the datasets.
    Skips items that aren't in the comparison CSV file.
    Normalizes zip codes to compare only first 5 digits with proper formatting.
    """
    from collections import defaultdict
    import glob

    # Load environment variables
    load_dotenv()
    END_CUSTOMER_NAME = os.getenv("END_CUSTOMER_NAME")
    END_CUSTOMER_ACCOUNT_ID = os.getenv("END_CUSTOMER_ACCOUNT_ID")

    print("🔍 Comparing inventory data with external CSV file...")
    
    # Always regenerate fresh data (same as option 41)
    export_devices_with_site_info_to_csv()

    # Load the enriched device + site info
    devices_with_site_info_path = get_csv_file_path("AllDevicesWithSiteInfo.csv")
    with open(devices_with_site_info_path, mode="r", encoding="utf-8") as f:
        site_configs = list(csv.DictReader(f))

    # Find all CSV files in the data directory
    data_dir = "data"
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    # Remove path prefix and exclude our source file
    csv_files = [os.path.basename(f) for f in csv_files if os.path.basename(f) != "AllDevicesWithSiteInfo.csv"]
    
    if not csv_files:
        print("❌ No CSV files found in the data directory for comparison.")
        print(f"   Please place comparison CSV files in the '{data_dir}' folder.")
        logging.error("No CSV files found for comparison in data directory.")
        return

    # Present CSV files to user for selection
    print("\n📋 Available CSV files for comparison:")
    print("=" * 60)
    for idx, csv_file in enumerate(csv_files):
        print(f"[{idx}] {csv_file}")
    
    try:
        user_input = input(f"\nEnter the index (0-{len(csv_files)-1}) of the CSV file to compare against: ").strip()
        selected_index = int(user_input)
        
        if selected_index < 0 or selected_index >= len(csv_files):
            print("❌ Invalid index selected.")
            logging.error(f"Invalid CSV file index selected: {selected_index}")
            return
            
        comparison_file = csv_files[selected_index]
        print(f"✅ Selected comparison file: {comparison_file}")
        logging.info(f"User selected comparison file: {comparison_file}")
        
    except ValueError:
        print("❌ Invalid input. Please enter a numeric index.")
        logging.error("Invalid numeric input for CSV file selection.")
        return
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        logging.info("CSV comparison operation cancelled by user.")
        return

    # Load the comparison CSV file
    try:
        comparison_file_path = get_csv_file_path(comparison_file)
        with open(comparison_file_path, mode="r", encoding="utf-8") as f:
            comparison_data = list(csv.DictReader(f))
    except Exception as e:
        print(f"❌ Error reading comparison file {comparison_file}: {e}")
        logging.error(f"Error reading comparison file {comparison_file}: {e}")
        return

    print(f"📊 Loaded {len(site_configs)} devices from AllDevicesWithSiteInfo.csv")
    print(f"📊 Loaded {len(comparison_data)} records from {comparison_file}")

    # Create lookup dictionaries for comparison data
    # Try common field names for serial number and zip code
    comparison_serials = {}
    comparison_zip_lookup = {}
    
    # Detect field names in comparison CSV
    if not comparison_data:
        print("❌ Comparison CSV file is empty.")
        return
        
    comparison_headers = comparison_data[0].keys()
    
    # Try to find serial number field
    serial_field = None
    for header in comparison_headers:
        if any(term in header.lower() for term in ['serial', 'sn', 'system serial']):
            serial_field = header
            break
    
    # Try to find zip code field  
    zip_field = None
    for header in comparison_headers:
        if any(term in header.lower() for term in ['zip', 'postal', 'zip code', 'postal code']):
            zip_field = header
            break

    # Try to find address fields
    address_field = None
    city_field = None
    state_field = None
    country_field = None
    
    for header in comparison_headers:
        if any(term in header.lower() for term in ['address', 'street', 'address line']):
            address_field = header
        elif any(term in header.lower() for term in ['city']):
            city_field = header
        elif any(term in header.lower() for term in ['state']):
            state_field = header
        elif any(term in header.lower() for term in ['country']):
            country_field = header

    if not serial_field:
        print("❌ Could not find serial number field in comparison CSV.")
        print("   Looked for fields containing: 'serial', 'sn', 'system serial'")
        print(f"   Available fields: {list(comparison_headers)}")
        logging.error(f"Serial field not found in {comparison_file}. Available fields: {list(comparison_headers)}")
        return
        
    if not zip_field:
        print("❌ Could not find zip code field in comparison CSV.")
        print("   Looked for fields containing: 'zip', 'postal', 'zip code', 'postal code'")
        print(f"   Available fields: {list(comparison_headers)}")
        logging.error(f"Zip field not found in {comparison_file}. Available fields: {list(comparison_headers)}")
        return

    print(f"✅ Using serial field: '{serial_field}'")
    print(f"✅ Using zip field: '{zip_field}'")
    if address_field:
        print(f"✅ Using address field: '{address_field}'")
    if city_field:
        print(f"✅ Using city field: '{city_field}'")
    if state_field:
        print(f"✅ Using state field: '{state_field}'")
    if country_field:
        print(f"✅ Using country field: '{country_field}'")

    # Build lookup dictionaries from comparison data
    comparison_address_lookup = {}  # serial -> full address info from comparison CSV
    for row in comparison_data:
        serial = row.get(serial_field, "").strip()
        zip_code = row.get(zip_field, "").strip()
        if serial:
            # Normalize zip code for comparison
            normalized_zip = normalize_zip_code(zip_code)
            comparison_serials[serial] = normalized_zip
            # Store full address info for diff report
            comparison_address_lookup[serial] = {
                "Address": row.get(address_field, "") if address_field else "",
                "City": row.get(city_field, "") if city_field else "",
                "State": row.get(state_field, "") if state_field else "",
                "Country": row.get(country_field, "") if country_field else "",
                "Zip": zip_code
            }

    print(f"📋 Built comparison lookup with {len(comparison_serials)} serial numbers")

    # Process device data and find mismatches
    mismatched_items = []
    diff_report_items = []
    skipped_count = 0
    
    for device in site_configs:
        device_serial = device.get("serial", "").strip()
        device_zip = device.get("zip_code", "").strip()
        
        # Skip if device serial not in comparison file
        if device_serial not in comparison_serials:
            skipped_count += 1
            continue
            
        # Get normalized zip code from comparison file
        comparison_zip = comparison_serials[device_serial]
        
        # Normalize device zip code for comparison
        device_zip_normalized = normalize_zip_code(device_zip)
        
        # Check if normalized zip codes don't match
        if device_zip_normalized != comparison_zip:
            try:
                created_time = int(device.get("created_time", 0))
                created_date = datetime.fromtimestamp(created_time, tz=timezone.utc)
                year, week, _ = created_date.isocalendar()
                week_key = f"{year}_Week_{week:02d}"

                # Standard mismatch item (existing format)
                mismatched_item = {
                    "Week": week_key,
                    "Full Site": device.get("site_name", ""),
                    "System Serial Number": device_serial,
                    "System Model Number": device.get("model", ""),
                    "End Customer Name": END_CUSTOMER_NAME,
                    "Address Line 1": device.get("street", ""),
                    "Address Line 2": "",
                    "City": device.get("city", ""),
                    "State": device.get("state", ""),
                    "Country": device.get("country", "US"),
                    "Current Zip Code": device_zip,
                    "Current Zip Normalized": device_zip_normalized,
                    "Comparison Zip Code": comparison_zip,
                    "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                    "Mismatch Type": "Zip Code Mismatch"
                }
                mismatched_items.append(mismatched_item)

                # Diff report item (showing both address sets)
                comparison_address = comparison_address_lookup.get(device_serial, {})
                diff_item = {
                    "Week": week_key,
                    "Full Site": device.get("site_name", ""),
                    "System Serial Number": device_serial,
                    "System Model Number": device.get("model", ""),
                    "End Customer Name": END_CUSTOMER_NAME,
                    "Mist_Address_Line_1": device.get("street", ""),
                    "Mist_City": device.get("city", ""),
                    "Mist_State": device.get("state", ""),
                    "Mist_Country": device.get("country", "US"),
                    "Mist_Zip_Code": device_zip,
                    "Mist_Zip_Normalized": device_zip_normalized,
                    "Comparison_Address": comparison_address.get("Address", ""),
                    "Comparison_City": comparison_address.get("City", ""),
                    "Comparison_State": comparison_address.get("State", ""),
                    "Comparison_Country": comparison_address.get("Country", ""),
                    "Comparison_Zip_Code": comparison_address.get("Zip", ""),
                    "Comparison_Zip_Normalized": comparison_zip,
                    "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                    "Mismatch Type": "Zip Code Mismatch"
                }
                diff_report_items.append(diff_item)
            except Exception as e:
                logging.warning(f"⚠️ Skipping device due to error: {e}")

    # Display results
    print(f"\n📊 Comparison Results:")
    print(f"   ✅ Devices processed: {len(site_configs)}")
    print(f"   ⏭️  Devices skipped (not in comparison file): {skipped_count}")
    print(f"   ❌ Zip code mismatches found: {len(mismatched_items)}")

    if mismatched_items:
        print(f"\n🔍 Zip Code Mismatches (comparing normalized 5-digit codes):")
        print("=" * 110)
        for idx, item in enumerate(mismatched_items[:10]):  # Show first 10
            print(f"[{idx+1:2}] Serial: {item['System Serial Number']:<15} | "
                  f"Current: {item['Current Zip Code']:<10} | "
                  f"Normalized: {item['Current Zip Normalized']:<6} | "
                  f"Expected: {item['Comparison Zip Code']:<6} | "
                  f"Site: {item['Full Site']}")
        
        if len(mismatched_items) > 10:
            print(f"   ... and {len(mismatched_items) - 10} more mismatches")
            
        # Optionally save to CSV
        save_choice = input(f"\n💾 Save {len(mismatched_items)} mismatched items to CSV files? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes']:
            base_filename = comparison_file.replace('.csv', '')
            
            # Save standard mismatch report (existing format)
            output_file1 = f"ZipCodeMismatches_vs_{base_filename}.csv"
            fieldnames1 = [
                "Week", "Full Site", "System Serial Number", "System Model Number", 
                "End Customer Name", "Address Line 1", "Address Line 2", "City", 
                "State", "Country", "Current Zip Code", "Current Zip Normalized", "Comparison Zip Code", 
                "End Customer Account ID", "Mismatch Type"
            ]
            
            with open(output_file1, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames1)
                writer.writeheader()
                writer.writerows(mismatched_items)
            
            # Save diff report (side-by-side address comparison)
            output_file2 = f"AddressDiff_vs_{base_filename}.csv"
            fieldnames2 = [
                "Week", "Full Site", "System Serial Number", "System Model Number", 
                "End Customer Name", "Mist_Address_Line_1", "Mist_City", "Mist_State", "Mist_Country",
                "Mist_Zip_Code", "Mist_Zip_Normalized", "Comparison_Address", "Comparison_City", 
                "Comparison_State", "Comparison_Country", "Comparison_Zip_Code", "Comparison_Zip_Normalized",
                "End Customer Account ID", "Mismatch Type"
            ]
            
            with open(output_file2, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames2)
                writer.writeheader()
                writer.writerows(diff_report_items)
            
            print(f"✅ Standard mismatches saved to: {output_file1}")
            print(f"✅ Address diff report saved to: {output_file2}")
            logging.info(f"Saved {len(mismatched_items)} mismatched items to {output_file1}")
            logging.info(f"Saved {len(diff_report_items)} diff items to {output_file2}")
    else:
        print("🎉 No zip code mismatches found! All items match the comparison file.")

def export_gateway_templates_to_csv():
    """
    Fetches all gateway templates for the organization and exports them to OrgGatewayTemplates.csv.
    """
    logging.info("Exporting gateway templates for the organization...")
    org_id = get_cached_or_prompted_org_id()
    # Fetch gateway templates using the Mist API
    response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(apisession, org_id)
    templates = getattr(response, "data", [])
    if not templates:
        logging.warning("No gateway templates found for this organization.")
        print("No gateway templates found for this organization.")
        return
    # Flatten and sanitize for CSV
    templates = flatten_nested_fields_in_list(templates)
    templates = escape_multiline_strings_for_csv(templates)
    save_data_to_output(templates, "OrgGatewayTemplates.csv")
    logging.info("✅ Gateway templates exported to OrgGatewayTemplates.csv")
    print("✅ Gateway templates exported to OrgGatewayTemplates.csv")

def export_gateways_with_wan_overrides_to_csv(fast=False):
    """
    Generates a CSV report of gateways with ports that are overridden from their template configuration.
    This helps identify outliers that need to be corrected back to template compliance.
    
    Report includes for OVERRIDDEN ports only:
    - Gateway Router Device Name  
    - Port descriptions/labels for ge-0/0/0, ge-0/0/1, ge-0/0/2
    - Port status (up/down)
    - Port admin status (disabled/enabled)
    - Port gateway IP address
    - Port IP address
    - Port netmask
    - Port config type (DHCP or STATIC)
    - Port name/number
    - Whether port is overridden from template (always "Yes" for filtered results)
    """
    logging.info("🔍 Identifying gateway ports with template overrides (outliers for compliance correction)...")

    # Ensure required CSVs are fresh
    check_and_generate_csv("AllSiteGatewayConfigs.csv", lambda: export_gateway_device_configs_to_csv(fast=fast))
    check_and_generate_csv("SiteList_ListAPI.csv", export_all_sites_list_to_csv)
    check_and_generate_csv("OrgGatewayTemplates.csv", export_gateway_templates_to_csv)

    # Load data
    with open(get_csv_file_path("AllSiteGatewayConfigs.csv"), encoding="utf-8") as f:
        configs = list(csv.DictReader(f))
    with open(get_csv_file_path("SiteList_ListAPI.csv"), encoding="utf-8") as f:
        sites = list(csv.DictReader(f))
    with open(get_csv_file_path("OrgGatewayTemplates.csv"), encoding="utf-8") as f:
        templates = list(csv.DictReader(f))

    # Create lookups for site and template names
    site_lookup = {site.get("id"): site.get("name", "Unknown Site") for site in sites}
    # Create site to gateway template ID mapping from SiteList
    site_to_template_id = {site.get("id"): site.get("gatewaytemplate_id", "") for site in sites}
    template_lookup = {t.get("id"): t.get("name", "Unknown Template") for t in templates}
    
    # Debug template lookup
    logging.debug(f"[DEBUG] Created template lookup with {len(template_lookup)} templates")
    for template_id, template_name in list(template_lookup.items())[:3]:  # Show first 3 for debugging
        logging.debug(f"[DEBUG] Template: {template_id} -> {template_name}")

    overridden_port_info = []
    target_ports = ["ge-0/0/0", "ge-0/0/1", "ge-0/0/2"]

    # OPTIMIZATION: First pass - identify devices with overrides without fetching stats
    logging.info("📋 First pass: Identifying devices with port overrides...")
    devices_with_overrides = {}  # device_id -> (device_info, overridden_port_names)
    
    for row in configs:
        device_name = row.get("name", "").strip()
        site_id = row.get("site_id", "").strip()
        device_id = row.get("id", "").strip()
        site_name = site_lookup.get(site_id, "Unknown Site")
        # Get template ID from site-level gateway template assignment
        template_id = site_to_template_id.get(site_id, "")
        template_name = template_lookup.get(template_id, "No Template") if template_id else "No Template"
        
        # Debug template lookup for this device
        if template_id:
            if template_id in template_lookup:
                logging.debug(f"[DEBUG] Device {device_name}: site_id='{site_id}' -> template_id='{template_id}' -> template_name='{template_name}'")
            else:
                logging.warning(f"[WARN] Device {device_name}: Template ID '{template_id}' not found in gateway templates (orphaned assignment)")
                template_name = f"Missing Template ({template_id[:8]}...)"
        else:
            logging.debug(f"[DEBUG] Device {device_name}: No gatewaytemplate_id found for site {site_id}")
        
        if not device_name or not site_id or not device_id:
            continue

        # Check each target port for overrides using CSV data only
        device_overridden_ports = []
        for port_name in target_ports:
            # Check if port is overridden from template by looking for port_config fields in the CSV
            port_config_fields = [col for col in row if col.startswith(f"port_config_{port_name}_")]
            
            # Check for non-empty values (excluding vpn_paths which are template-inherited)
            override_fields = []
            for field in port_config_fields:
                value = row.get(field, "").strip().lower()
                if value not in ["", "null", "none"] and "_vpn_paths_" not in field:
                    override_fields.append(f"{field}={value}")
            
            is_overridden = len(override_fields) > 0
            if is_overridden:
                device_overridden_ports.append(port_name)
        
        # If this device has any overridden ports, mark it for API calls
        if device_overridden_ports:
            devices_with_overrides[device_id] = {
                "device_name": device_name,
                "site_id": site_id,
                "site_name": site_name,
                "template_id": template_id,
                "template_name": template_name,
                "row_data": row,
                "overridden_ports": device_overridden_ports
            }

    logging.info(f"📊 Found {len(devices_with_overrides)} devices with port overrides out of {len(configs)} total gateway devices")
    
    if not devices_with_overrides:
        logging.info("🎉 No template overrides found - all gateways are compliant with their assigned templates!")
        # Still create empty CSV file with proper headers
        output_file = "GatewayOverriddenPorts.csv"
        fieldnames = [
            "gateway_device_name", "site_name", "template_name", "port_name", "port_description",
            "port_status", "port_admin_status", "port_gateway_ip", "port_ip_address", "port_netmask",
            "port_config_type", "port_usage", "overridden_from_template",
            "device_id", "site_id", "template_id"
        ]
        output_path = get_csv_file_path(output_file)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        print(f"✅ Gateway override report written to {output_file}")
        print("🎉 No template overrides found - all gateways are compliant with their assigned templates!")
        return

    # OPTIMIZATION: Second pass - fetch device configs and stats only for devices with overrides
    logging.info(f"🔍 Second pass: Fetching device configs and stats for {len(devices_with_overrides)} devices with overrides...")
    device_data_cache = {}  # device_id -> (port_configs, interface_stats)
    
    for device_id, device_info in devices_with_overrides.items():
        device_name = device_info["device_name"]
        site_id = device_info["site_id"]
        
        # Fetch live device info from getSiteDevice API for current config
        try:
            resp = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
            device_data = getattr(resp, "data", {})
            port_configs = device_data.get("port_config", {})
        except Exception as e:
            logging.warning(f"[WARN] Could not fetch device config for {device_name} ({device_id}): {e}")
            port_configs = {}

        # Fetch live device stats for current port status 
        try:
            stats_resp = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id)
            stats_data = getattr(stats_resp, "data", {})
            interface_stats = stats_data.get("if_stat", {})
        except Exception as e:
            # Handle 403 Forbidden and other errors gracefully
            if "403" in str(e) or "Forbidden" in str(e):
                logging.warning(f"[WARN] Insufficient permissions to fetch device stats for {device_name} ({device_id}): 403 Forbidden")
            else:
                logging.warning(f"[WARN] Could not fetch device stats for {device_name} ({device_id}): {e}")
            interface_stats = {}

        device_data_cache[device_id] = (port_configs, interface_stats)

    # Third pass: Process only the overridden ports with their stats
    logging.info("📝 Third pass: Processing overridden ports with live data...")
    for device_id, device_info in devices_with_overrides.items():
        device_name = device_info["device_name"]
        site_id = device_info["site_id"]
        site_name = device_info["site_name"]
        template_id = device_info["template_id"]
        template_name = device_info["template_name"]
        row = device_info["row_data"]
        overridden_ports = device_info["overridden_ports"]
        
        port_configs, interface_stats = device_data_cache.get(device_id, ({}, {}))

        # Process each overridden port
        for port_name in overridden_ports:
            port_config = port_configs.get(port_name, {})
            interface_stat = interface_stats.get(port_name, {})
            
            # Get port config fields from CSV for override details
            port_config_fields = [col for col in row if col.startswith(f"port_config_{port_name}_")]
            
            # Extract port configuration details
            ip_config = port_config.get("ip_config", {})
            usage = port_config.get("usage", "")
            description = port_config.get("description", "")
            disabled = port_config.get("disabled", False)
            
            # Extract IP configuration details
            port_ip = ip_config.get("ip", "")
            netmask = ip_config.get("netmask", "")
            gateway_ip = ip_config.get("gateway", "")
            config_type = ip_config.get("type", "")
            
            # Convert config type to human readable
            if config_type == "dhcp":
                config_type_display = "DHCP"
            elif config_type == "static":
                config_type_display = "STATIC"
            else:
                config_type_display = config_type.upper() if config_type else "UNKNOWN"
            
            # Extract port status from interface stats
            port_status = "down"
            if interface_stat:
                # Check the "up" field from if_stat which is the actual port status
                if interface_stat.get("up", False):
                    port_status = "up"
            
            # Admin status
            admin_status = "disabled" if disabled else "enabled"
            
            # Create detailed port entry for overridden port
            port_entry = {
                "gateway_device_name": device_name,
                "site_name": site_name,
                "template_name": template_name,
                "port_name": port_name,
                "port_description": description,
                "port_status": port_status,
                "port_admin_status": admin_status,
                "port_gateway_ip": gateway_ip,
                "port_ip_address": port_ip,
                "port_netmask": netmask,
                "port_config_type": config_type_display,
                "port_usage": usage,
                "overridden_from_template": "Yes",
                "device_id": device_id,
                "site_id": site_id,
                "template_id": template_id
            }
            
            # Add the overridden port to our results
            overridden_port_info.append(port_entry)

    # Write to CSV with only overridden port information
    output_file = "GatewayOverriddenPorts.csv"
    save_data_to_output(overridden_port_info, output_file)

    # Calculate summary statistics
    total_gateways_processed = len(configs)
    devices_with_overrides_count = len(devices_with_overrides) if 'devices_with_overrides' in locals() else 0
    if overridden_port_info:
        gateways_with_overrides = len(set(entry["device_id"] for entry in overridden_port_info))
    else:
        gateways_with_overrides = 0
    total_overridden_ports = len(overridden_port_info)

    logging.info(f"✅ Gateway override report written to {output_file} with {total_overridden_ports} overridden ports from {gateways_with_overrides} gateway devices.")
    logging.info(f"🚀 API Optimization: Made device config/stats calls for only {devices_with_overrides_count} devices instead of all {total_gateways_processed} devices")
    print(f"✅ Gateway override report written to {output_file}")
    print(f"📊 Found {total_overridden_ports} overridden ports across {gateways_with_overrides} of {total_gateways_processed} gateway devices")
    print(f"🚀 API Optimization: Only fetched live data for {devices_with_overrides_count} devices with overrides (saved {total_gateways_processed - devices_with_overrides_count} unnecessary API calls)")
    print(f"🔍 Target ports analyzed: {', '.join(target_ports)}")
    print(f"📋 These are outliers that may need correction to match template configuration")
    
    if total_overridden_ports == 0:
        print("🎉 No template overrides found - all gateways are compliant with their assigned templates!")

def convert_virtual_chassis_to_virtual_mac():
    """
    Presents a list of sites first, then shows switches that are virtual chassis at the selected site,
    lets the user select one, and calls the Mist API to convert the device to a virtual MAC.
    """
    print("\n🔥 DESTRUCTIVE: Virtual Chassis to Virtual MAC Conversion")
    print("=" * 60)
    
    # First, prompt for site selection
    site_id = prompt_site_selection()
    if not site_id:
        print("❌ No site selected.")
        return
    
    # Get site name for display
    site_name = "Unknown Site"
    try:
        org_id = get_cached_or_prompted_org_id()
        site_response = mistapi.api.v1.sites.getSite(apisession, site_id)
        if site_response.data:
            site_name = site_response.data.get('name', site_id)
    except Exception as e:
        logging.warning(f"Could not fetch site name for {site_id}: {e}")
    
    print(f"\n📍 Selected Site: {site_name} ({site_id})")
    
    # Ensure OrgInventory.csv is fresh
    check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)

    # Load OrgInventory.csv and filter for switches at the selected site with a non-empty id 
    inventory_path = get_csv_file_path("OrgInventory.csv")
    with open(inventory_path, mode="r", encoding="utf-8") as file:
        reader = list(csv.DictReader(file))
        switches = [
            row for row in reader
            if (row.get("type") == "switch" 
                and row.get("id", "").strip()
                and row.get("site_id") == site_id)
        ]

    if not switches:
        print(f"❌ No virtual chassis switches found at site '{site_name}'.")
        print("💡 Virtual chassis switches must have a device ID assigned.")
        logging.warning(f"No virtual chassis switches found at site {site_id}.")
        return

    # Display indexed list to user
    print(f"\n🔌 Available Virtual Chassis Switches at '{site_name}':")
    print("-" * 80)
    index_to_device = {}
    name_to_device = {}
    for idx, sw in enumerate(switches):
        print(f"[{idx}] {sw.get('name', ''):20} MAC: {sw.get('mac', ''):17} Model: {sw.get('model', ''):10} Serial: {sw.get('serial', ''):15} ID: {sw.get('id', '')}")
        index_to_device[idx] = sw
        name_to_device[sw.get("name", "")] = sw

    user_input = input(f"\nEnter the index or switch name to convert to virtual MAC [0-{len(switches)-1}]: ").strip()

    # Resolve user input
    selected = None
    if user_input.isdigit():
        idx = int(user_input)
        selected = index_to_device.get(idx)
    else:
        selected = name_to_device.get(user_input)

    if not selected:
        print("❌ Switch not found by index or name.")
        logging.warning(f"Switch not found: {user_input}")
        return

    device_id = selected.get("id")
    if not device_id:
        print("❌ Missing device_id for selected switch.")
        logging.warning("Missing device_id for selected switch.")
        return

    # Confirmation prompt for destructive operation
    print(f"\n⚠️  DESTRUCTIVE OPERATION WARNING ⚠️")
    print(f"You are about to convert switch '{selected.get('name', '')}' to virtual MAC.")
    print(f"Site: {site_name}")
    print(f"Device ID: {device_id}")
    print(f"MAC: {selected.get('mac', '')}")
    print(f"This operation cannot be undone!")
    
    confirm = input("\nType 'CONVERT' to proceed or anything else to cancel: ").strip()
    if confirm != "CONVERT":
        print("❌ Operation cancelled.")
        return

    print(f"🔄 Converting switch '{selected.get('name', '')}' (device_id: {device_id}) at site '{site_name}' to virtual MAC...")
    try:
        # Call the Mist API to convert to virtual MAC
        resp = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(apisession, site_id, device_id)
        # Show the result to the user, including error details if present
        if hasattr(resp, "status_code") and resp.status_code >= 400:
            print(f"❌ Conversion failed (HTTP {resp.status_code}): {getattr(resp, 'data', '')}")
            logging.error(f"Conversion to virtual MAC failed for device {device_id} at site {site_id}. Response: {getattr(resp, 'data', '')}")
        elif isinstance(getattr(resp, "data", None), dict) and "detail" in resp.data:
            print(f"❌ Conversion failed: {resp.data['detail']}")
            logging.error(f"Conversion to virtual MAC failed for device {device_id} at site_id {site_id}. Detail: {resp.data['detail']}")
        else:
            print("✅ Conversion to virtual MAC triggered successfully!")
            print("💡 Check the device status in the Mist UI to monitor progress.")
            logging.info(f"Conversion to virtual MAC triggered for device {device_id} at site {site_id}. Response: {getattr(resp, 'data', '')}")
    except Exception as e:
        print(f"❌ Failed to convert to virtual MAC: {e}")
        logging.error(f"Failed to convert to virtual MAC: {e}")

def convert_virtual_chassis_by_site_list():
    """
    Reads site names from VCConvert.CSV (no header), finds all virtual chassis switches 
    in those sites, displays them to the user for confirmation, and converts them all 
    if the user confirms.
    """
    logging.info("Starting bulk virtual chassis to virtual MAC conversion by site list...")
    
    # Check if VCConvert.CSV exists
    csv_file = "VCConvert.CSV"
    csv_file_path = get_csv_file_path(csv_file)
    if not os.path.exists(csv_file_path):
        print(f"❌ File '{csv_file}' not found.")
        print(f"   Please create this file at: {csv_file_path}")
        print("   This file should contain site names (one per line, no header).")
        
        # Offer to create a basic file
        user_input = input("   Would you like to create an empty file to get started? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            try:
                template_path = create_missing_csv_template("VCConvert.CSV")
                print(f"✅ Empty file created at: {template_path}")
                print("   Please edit the file to add your site names and run the script again.")
            except Exception as e:
                print(f"❌ Failed to create file: {e}")
        
        logging.error(f"VCConvert.CSV file not found.")
        return

    # Read site names from CSV (no header)
    site_names = []
    try:
        with open(csv_file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    site_names.append(row[0].strip())
    except Exception as e:
        print(f"❌ Error reading {csv_file}: {e}")
        logging.error(f"Error reading VCConvert.CSV: {e}")
        return

    if not site_names:
        print(f"❌ No site names found in {csv_file}.")
        logging.warning("No site names found in VCConvert.CSV.")
        return

    print(f"📋 Loaded {len(site_names)} site names from {csv_file}:")
    for idx, site_name in enumerate(site_names):
        print(f"  [{idx+1}] {site_name}")

    # Ensure required CSVs are fresh
    check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)

    # Load site list to get site IDs
    site_name_to_id = {}
    try:
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                site_name_to_id[row.get("name", "")] = row.get("id", "")
    except Exception as e:
        print(f"❌ Error reading SiteList.csv: {e}")
        logging.error(f"Error reading SiteList.csv: {e}")
        return

    # Find site IDs for the specified site names
    target_site_ids = []
    missing_sites = []
    for site_name in site_names:
        site_id = site_name_to_id.get(site_name)
        if site_id:
            target_site_ids.append(site_id)
        else:
            missing_sites.append(site_name)

    if missing_sites:
        print(f"⚠️ Warning: The following sites were not found in the organization:")
        for site in missing_sites:
            print(f"   - {site}")

    if not target_site_ids:
        print("❌ No valid sites found. Exiting.")
        logging.error("No valid sites found for VC conversion.")
        return

    # Load inventory and filter for virtual chassis switches in target sites
    switches_to_convert = []
    try:
        inventory_path = get_csv_file_path("OrgInventory.csv")
        with open(inventory_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("type") == "switch" and 
                    row.get("site_id") in target_site_ids and 
                    row.get("id", "").strip()):
                    
                    # Get site name for display
                    site_name = next((name for name, id_ in site_name_to_id.items() if id_ == row.get("site_id")), "Unknown Site")
                    row["site_name"] = site_name
                    switches_to_convert.append(row)
    except Exception as e:
        print(f"❌ Error reading OrgInventory.csv: {e}")
        logging.error(f"Error reading OrgInventory.csv: {e}")
        return

    if not switches_to_convert:
        print("❌ No virtual chassis switches found in the specified sites.")
        logging.warning("No virtual chassis switches found in target sites.")
        return

    # Display switches that will be converted
    print(f"\n🔍 Found {len(switches_to_convert)} virtual chassis switches to convert:")
    print("=" * 100)
    for idx, switch in enumerate(switches_to_convert):
        print(f"[{idx+1:2}] Site: {switch.get('site_name', ''):25} | "
              f"Name: {switch.get('name', ''):20} | "
              f"MAC: {switch.get('mac', ''):17} | "
              f"Model: {switch.get('model', ''):12} | "
              f"Serial: {switch.get('serial', '')}")

    # Ask for user confirmation
    print(f"\n⚠️ This will convert {len(switches_to_convert)} virtual chassis switches to virtual MAC.")
    print("💡 This operation cannot be undone easily.")
    
    confirm = input("\n🤔 Do you want to proceed with the conversion? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Conversion cancelled by user.")
        logging.info("Virtual chassis conversion cancelled by user.")
        return

    # Proceed with conversions
    print(f"\n🚀 Starting conversion of {len(switches_to_convert)} switches...")
    successful_conversions = 0
    failed_conversions = 0

    for idx, switch in enumerate(switches_to_convert):
        site_id = switch.get("site_id")
        device_id = switch.get("id")
        switch_name = switch.get("name", "")
        site_name = switch.get("site_name", "")
        
        print(f"\n[{idx+1}/{len(switches_to_convert)}] Converting '{switch_name}' at site '{site_name}'...")
        
        try:
            # Call the Mist API to convert to virtual MAC
            resp = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(apisession, site_id, device_id)
            
            # Check the response
            if hasattr(resp, "status_code") and resp.status_code >= 400:
                print(f"❌ Conversion failed (HTTP {resp.status_code}): {getattr(resp, 'data', '')}")
                logging.error(f"Conversion failed for {switch_name} at {site_name}. HTTP {resp.status_code}: {getattr(resp, 'data', '')}")
                failed_conversions += 1
            elif isinstance(getattr(resp, "data", None), dict) and "detail" in resp.data:
                print(f"❌ Conversion failed: {resp.data['detail']}")
                logging.error(f"Conversion failed for {switch_name} at {site_name}. Detail: {resp.data['detail']}")
                failed_conversions += 1
            else:
                print(f"✅ Conversion triggered successfully.")
                logging.info(f"Conversion triggered for {switch_name} at {site_name}. Response: {getattr(resp, 'data', '')}")
                successful_conversions += 1
                
        except Exception as e:
            print(f"❌ Exception during conversion: {e}")
            logging.error(f"Exception during conversion of {switch_name} at {site_name}: {e}")
            failed_conversions += 1

    # Summary
    print(f"\n📊 Conversion Summary:")
    print(f"   ✅ Successful conversions: {successful_conversions}")
    print(f"   ❌ Failed conversions: {failed_conversions}")
    print(f"   📊 Total switches processed: {len(switches_to_convert)}")
    
    if successful_conversions > 0:
        print(f"\n💡 Note: Successful conversions may take a few minutes to complete.")
        print(f"   Monitor the devices in the Mist portal to confirm the conversion status.")
    
    logging.info(f"Bulk VC conversion completed: {successful_conversions} successful, {failed_conversions} failed")

def check_virtual_chassis_conversion_status():
    """
    Check all switches in the organization to determine if they have been converted to virtual MAC addresses.
    Virtual chassis switches that have been converted to virtual MAC will have vc_mac starting with "020003".
    Non-converted virtual chassis switches will have different vc_mac prefixes.
    
    This function:
    1. Uses cached OrgInventory.csv or generates fresh data
    2. Filters for switches with vc_mac (virtual chassis candidates)
    3. Checks vc_mac prefix to determine conversion status
    4. Exports results to VirtualChassisConversionStatus.csv
    5. Displays summary statistics
    """
    print("\n🔍 Virtual Chassis to Virtual MAC Conversion Status Check")
    print("=" * 70)
    print("📋 Checking all switches for virtual chassis conversion status...")
    print("💡 Converted switches have vc_mac starting with '020003'")
    
    logging.info("Starting virtual chassis conversion status check...")
    
    # Ensure OrgInventory.csv is fresh
    check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)
    
    # Load inventory and filter for switches with vc_mac (virtual chassis switches)
    switches_with_vc_mac = []
    try:
        inventory_path = get_csv_file_path("OrgInventory.csv")
        with open(inventory_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("type") == "switch" and 
                    row.get("vc_mac", "").strip()):
                    switches_with_vc_mac.append(row)
                    
    except Exception as e:
        print(f"❌ Error reading OrgInventory.csv: {e}")
        logging.error(f"Error reading OrgInventory.csv: {e}")
        return
    
    if not switches_with_vc_mac:
        print("❌ No switches with vc_mac found in the organization.")
        print("💡 Only virtual chassis switches have vc_mac assigned.")
        logging.warning("No switches with vc_mac found.")
        return
    
    # Load site information for display
    site_id_to_name = {}
    try:
        check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                site_id_to_name[row.get("id", "")] = row.get("name", "Unknown Site")
    except Exception as e:
        logging.warning(f"Could not load site names: {e}")
    
    # Analyze conversion status
    converted_switches = []
    not_converted_switches = []
    
    for switch in switches_with_vc_mac:
        vc_mac = switch.get("vc_mac", "")
        site_id = switch.get("site_id", "")
        site_name = site_id_to_name.get(site_id, "Unknown Site")
        
        # Create enhanced switch record with analysis
        enhanced_switch = switch.copy()
        enhanced_switch["site_name"] = site_name
        
        # Check if vc_mac starts with "020003" (converted to virtual MAC)
        if vc_mac.startswith("020003"):
            enhanced_switch["conversion_status"] = "CONVERTED"
            enhanced_switch["conversion_notes"] = "vc_mac starts with 020003 - converted to virtual MAC"
            converted_switches.append(enhanced_switch)
        else:
            enhanced_switch["conversion_status"] = "NOT_CONVERTED"
            enhanced_switch["conversion_notes"] = f"vc_mac starts with {vc_mac[:6]} - not converted to virtual MAC"
            not_converted_switches.append(enhanced_switch)
    
    # Combine all switches for export
    all_switches = converted_switches + not_converted_switches
    
    # Display summary
    total_switches = len(all_switches)
    converted_count = len(converted_switches)
    not_converted_count = len(not_converted_switches)
    
    print(f"\n📊 Virtual Chassis Conversion Status Summary:")
    print(f"   🔧 Total virtual chassis switches: {total_switches}")
    print(f"   ✅ Converted to virtual MAC: {converted_count}")
    print(f"   ⏳ Not converted: {not_converted_count}")
    
    if converted_count > 0:
        print(f"\n✅ Converted Switches (vc_mac starts with '020003'):")
        for switch in converted_switches[:10]:  # Show first 10
            print(f"   • {switch.get('name', 'Unnamed'):20} | Site: {switch.get('site_name', ''):25} | vc_mac: {switch.get('vc_mac', '')[:8]}...")
        if len(converted_switches) > 10:
            print(f"   ... and {len(converted_switches) - 10} more")
    
    if not_converted_count > 0:
        print(f"\n⏳ Not Converted Switches (vc_mac does NOT start with '020003'):")
        for switch in not_converted_switches[:10]:  # Show first 10
            print(f"   • {switch.get('name', 'Unnamed'):20} | Site: {switch.get('site_name', ''):25} | vc_mac: {switch.get('vc_mac', '')[:8]}...")
        if len(not_converted_switches) > 10:
            print(f"   ... and {len(not_converted_switches) - 10} more")
    
    # Export to CSV
    try:
        # Flatten any nested fields for CSV export
        flattened_switches = flatten_nested_fields_in_list(all_switches)
        sanitized_switches = escape_multiline_strings_for_csv(flattened_switches)
        
        # Save to CSV
        filename = "VirtualChassisConversionStatus.csv"
        save_data_to_output(sanitized_switches, filename)
        
        print(f"\n💾 Results exported to: {filename}")
        print(f"   📁 Location: {get_csv_file_path(filename)}")
        
        # Log results
        logging.info(f"Virtual chassis conversion status check completed:")
        logging.info(f"  Total switches: {total_switches}")
        logging.info(f"  Converted: {converted_count}")
        logging.info(f"  Not converted: {not_converted_count}")
        logging.info(f"  Results exported to {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting results: {e}")
        logging.error(f"Error exporting conversion status results: {e}")
    
    print(f"\n💡 Usage Notes:")
    print(f"   • Use option 92 to convert individual switches")
    print(f"   • Use option 93 for bulk conversion by site list")
    print(f"   • Virtual chassis switches without '020003' vc_mac prefix can be converted")

def export_site_wifi_clients_to_csv(site_id=None):
    """
    Exports all currently connected WiFi clients and their session data for a selected site to SiteWiFiClients.CSV.
    Fetches both wireless client data and wireless client session data, then merges them based on MAC address.
    If site_id is not provided, prompts user to select from site list.
    
    The merged data includes:
    - Current client information (if available)
    - Session data for each client (prefixed with 'session_')
    - Session count for clients with multiple sessions
    - Sessions without corresponding current clients (marked as 'session_only')
    """
    logging.info("Starting export of site WiFi clients...")
    
    # Ensure required CSVs are fresh
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    
    # Get site_id if not provided
    if not site_id:
        site_id = prompt_select_site_id_from_csv("SiteList.csv")
        if not site_id:
            logging.error("❌ No site selected.")
            print("❌ No site selected.")
            return
    
    # Get site name for display
    site_name = "Unknown Site"
    try:
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("id") == site_id:
                    site_name = row.get("name", "Unknown Site")
                    break
    except Exception as e:
        logging.warning(f"⚠️ Failed to load site name from SiteList.csv: {e}")
    
    logging.info(f"Fetching WiFi clients for site: {site_name} (ID: {site_id})")
    print(f"🔍 Fetching WiFi clients for site: {site_name}")
    
    try:
        # Call the Mist API to search for wireless clients at the site
        logging.info("Fetching wireless clients data...")
        client_response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(apisession, site_id, limit=1000)
        clients = mistapi.get_all(response=client_response, mist_session=apisession)
        
        # Call the Mist API to search for wireless client sessions at the site
        logging.info("Fetching wireless client sessions data...")
        session_response = mistapi.api.v1.sites.clients.searchSiteWirelessClientSessions(apisession, site_id, limit=1000)
        sessions = mistapi.get_all(response=session_response, mist_session=apisession)
        
        if not clients and not sessions:
            logging.warning("⚠️ No WiFi clients or sessions found at this site.")
            print("⚠️ No WiFi clients or sessions found at this site.")
            # Create empty CSV with headers
            wifi_clients_path = get_csv_file_path("SiteWiFiClients.CSV")
            with open(wifi_clients_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["site_id", "site_name", "message"])
                writer.writerow([site_id, site_name, "No WiFi clients or sessions found"])
            return
        
        # Create a dictionary to store session data by MAC address for easy lookup
        sessions_by_mac = {}
        if sessions:
            for session in sessions:
                mac = session.get("mac")
                if mac:
                    # If multiple sessions exist for the same MAC, store them in a list
                    if mac in sessions_by_mac:
                        if not isinstance(sessions_by_mac[mac], list):
                            sessions_by_mac[mac] = [sessions_by_mac[mac]]
                        sessions_by_mac[mac].append(session)
                    else:
                        sessions_by_mac[mac] = session
        
        # Merge client data with session data based on MAC address
        enriched_clients = []
        processed_macs = set()
        
        # Process clients and merge with matching sessions
        if clients:
            for client in clients:
                client_mac = client.get("mac")
                # Add site information
                client["site_id"] = site_id
                client["site_name"] = site_name
                client["data_source"] = "client"
                
                # Merge with session data if available
                if client_mac and client_mac in sessions_by_mac:
                    session_data = sessions_by_mac[client_mac]
                    if isinstance(session_data, list):
                        # Multiple sessions - merge with the most recent one
                        latest_session = max(session_data, key=lambda x: x.get("start_time", 0))
                        for key, value in latest_session.items():
                            if key not in client:  # Don't overwrite client data
                                client[f"session_{key}"] = value
                        client["session_count"] = len(session_data)
                    else:
                        # Single session
                        for key, value in session_data.items():
                            if key not in client:  # Don't overwrite client data
                                client[f"session_{key}"] = value
                        client["session_count"] = 1
                    processed_macs.add(client_mac)
                else:
                    client["session_count"] = 0
                
                enriched_clients.append(client)
        
        # Add any sessions that don't have corresponding client data
        if sessions:
            for session in sessions:
                session_mac = session.get("mac")
                if session_mac and session_mac not in processed_macs:
                    # This is a session without a corresponding current client
                    session["site_id"] = site_id
                    session["site_name"] = site_name
                    session["data_source"] = "session_only"
                    session["session_count"] = 1
                    # Prefix session-specific fields to avoid conflicts
                    session_data = {}
                    for key, value in session.items():
                        if key not in ["site_id", "site_name", "data_source", "session_count"]:
                            session_data[f"session_{key}"] = value
                        else:
                            session_data[key] = value
                    enriched_clients.append(session_data)
        
        if not enriched_clients:
            logging.warning("⚠️ No data to export after processing.")
            print("⚠️ No data to export after processing.")
            return
        
        # Flatten and sanitize the data for CSV
        flattened = flatten_nested_fields_in_list(enriched_clients)
        sanitized = escape_multiline_strings_for_csv(flattened)
        
        # Write to CSV
        save_data_to_output(sanitized, "SiteWiFiClients.CSV")
        
        client_count = len(clients) if clients else 0
        session_count = len(sessions) if sessions else 0
        total_records = len(enriched_clients)
        
        logging.info(f"✅ WiFi data exported to SiteWiFiClients.CSV ({client_count} clients, {session_count} sessions, {total_records} total records)")
        print(f"✅ WiFi data exported to SiteWiFiClients.CSV")
        print(f"   📊 {client_count} current clients, {session_count} sessions, {total_records} total records from {site_name}")
        
    except Exception as e:
        logging.error(f"❌ Failed to fetch WiFi data for site {site_id}: {e}")
        print(f"❌ Failed to fetch WiFi data: {e}")

def reboot_devices_by_gateway_template_list():
    """
    Reboots all devices associated with branch templates listed in GatewayTemplateRebootList.CSV.
    Logs the result of each reboot command to GatewayTemplateRebootResults.CSV.
    """
    import csv
    import os
    from datetime import datetime, timezone

    logging.info("[46] Starting reboot_devices_by_gateway_template_list")

    # Step 1: Check if the reboot list file exists
    reboot_list_path = get_csv_file_path("GatewayTemplateRebootList.CSV")
    if not os.path.exists(reboot_list_path):
        logging.error("❌ GatewayTemplateRebootList.CSV not found.")
        print("❌ GatewayTemplateRebootList.CSV not found.")
        print(f"   Please create this file at: {reboot_list_path}")
        print("   This file should contain template names to reboot, one per line.")
        
        # Offer to create a basic file
        user_input = input("   Would you like to create an empty file to get started? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            try:
                template_path = create_missing_csv_template("GatewayTemplateRebootList.CSV")
                print(f"✅ Empty file created at: {template_path}")
                print("   Please edit the file to add your template names and run the script again.")
            except Exception as e:
                print(f"❌ Failed to create file: {e}")
        return

    # Step 2: Ensure required CSVs are fresh
    check_and_generate_csv("OrgDevices.csv", export_all_devices_to_csv)
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    check_and_generate_csv("OrgGatewayTemplates.csv", export_gateway_templates_to_csv)
    check_and_generate_csv("AllSiteGatewayConfigs.csv", lambda: export_gateway_device_configs_to_csv(fast=True))

    # Step 3: Load template name to ID mapping from OrgGatewayTemplates.csv
    template_name_to_id = {}
    try:
        gateway_templates_path = get_csv_file_path("OrgGatewayTemplates.csv")
        with open(gateway_templates_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                tid = row.get("id", "").strip()
                if name and tid:
                    template_name_to_id[name] = tid
        logging.info(f"Loaded {len(template_name_to_id)} gateway templates from OrgGatewayTemplates.csv")
    except Exception as e:
        logging.error(f"❌ Failed to load gateway templates: {e}")
        print(f"❌ Failed to load gateway templates: {e}")
        return

    if not template_name_to_id:
        logging.warning("⚠️ No gateway templates found in OrgGatewayTemplates.csv")
        print("⚠️ No gateway templates found in OrgGatewayTemplates.csv")
        return

    # Step 4: Load reboot list of template names
    reboot_template_names = set()
    try:
        reboot_list_path = get_csv_file_path("GatewayTemplateRebootList.CSV")
        with open(reboot_list_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    reboot_template_names.add(row[0].strip())
        logging.info(f"Loaded {len(reboot_template_names)} template names from reboot list: {reboot_template_names}")
    except Exception as e:
        logging.error(f"❌ Failed to load reboot template list: {e}")
        print(f"❌ Failed to load reboot template list: {e}")
        return

    # Step 5: Map template names to IDs and show matches/mismatches
    reboot_template_ids = set()
    for name in reboot_template_names:
        if name in template_name_to_id:
            reboot_template_ids.add(template_name_to_id[name])
            logging.info(f"✅ Found template '{name}' with ID '{template_name_to_id[name]}'")
        else:
            logging.warning(f"⚠️ Template '{name}' not found in OrgGatewayTemplates.csv")
            print(f"⚠️ Template '{name}' not found in available templates")

    if not reboot_template_ids:
        logging.error("❌ No matching template IDs found for reboot")
        print("❌ No matching template IDs found for reboot")
        print("Available templates:")
        for name, tid in template_name_to_id.items():
            print(f"  - {name} ({tid})")
        return

    logging.info(f"Proceeding with {len(reboot_template_ids)} template IDs: {reboot_template_ids}")

    # Step 6: First find sites that use the target gateway template IDs and create site-to-template mapping
    sites_using_templates = set()
    site_to_template_mapping = {}  # Maps site_id to (template_id, template_name, site_name)
    template_id_to_name = {tid: name for name, tid in template_name_to_id.items()}  # Reverse lookup
    
    try:
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gateway_template_id = row.get("gatewaytemplate_id", "").strip()
                if gateway_template_id in reboot_template_ids:
                    site_id = row.get("id", "").strip()
                    site_name = row.get("name", "").strip()
                    template_name = template_id_to_name.get(gateway_template_id, "Unknown Template")
                    sites_using_templates.add(site_id)
                    site_to_template_mapping[site_id] = (gateway_template_id, template_name, site_name)
                    logging.info(f"Found site '{site_name}' (ID: {site_id}) using gateway template '{template_name}' (ID: {gateway_template_id})")
    except Exception as e:
        logging.error(f"❌ Failed to load site list: {e}")
        print(f"❌ Failed to load site list: {e}")
        return

    if not sites_using_templates:
        logging.warning("⚠️ No sites found using the specified gateway templates")
        print("⚠️ No sites found using the specified gateway templates")
        return

    logging.info(f"Found {len(sites_using_templates)} sites using target templates: {sites_using_templates}")

    # Step 7: Load AllSiteGatewayConfigs and filter gateway devices by site_id
    reboot_targets = []
    try:
        gateway_configs_path = get_csv_file_path("AllSiteGatewayConfigs.csv")
        with open(gateway_configs_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                device_site_id = row.get("site_id", "").strip()
                device_type = row.get("type", "").strip()
                device_id = row.get("id", "").strip()
                device_name = row.get("name", "").strip()
                
                # Debug logging for the first few devices
                logging.debug(f"Checking device '{device_name}' (ID: {device_id}) in site '{device_site_id}' of type '{device_type}'")
                
                # Only target gateway devices in sites that use our target templates
                if device_site_id in sites_using_templates and device_type == "gateway":
                    template_id, template_name, site_name = site_to_template_mapping.get(device_site_id, ("unknown", "Unknown Template", "Unknown Site"))
                    reboot_targets.append({
                        "device_id": device_id,
                        "device_name": device_name,
                        "site_id": device_site_id,
                        "site_name": site_name,
                        "template_id": template_id,
                        "template_name": template_name
                    })
                    logging.info(f"Found gateway device '{device_name}' (ID: {device_id}) in site '{site_name}' (ID: {device_site_id}) using template '{template_name}' (ID: {template_id})")
    except Exception as e:
        logging.error(f"❌ Failed to load gateway configs: {e}")
        print(f"❌ Failed to load gateway configs: {e}")
        return

    if not reboot_targets:
        logging.warning("⚠️ No gateway devices found in sites using the specified templates")
        print("⚠️ No gateway devices found in sites using the specified templates")
        
        # Provide debug information
        logging.info(f"Sites using target templates: {sites_using_templates}")
        print(f"Debug: Sites using target templates: {list(sites_using_templates)}")
        
        # Count devices by type in target sites
        device_counts = {}
        try:
            with open(get_csv_file_path("AllSiteGatewayConfigs.csv"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    device_site_id = row.get("site_id", "").strip()
                    device_type = row.get("type", "").strip()
                    if device_site_id in sites_using_templates:
                        device_counts[device_type] = device_counts.get(device_type, 0) + 1
            
            if device_counts:
                logging.info(f"Device types found in target sites: {device_counts}")
                print(f"Debug: Device types found in target sites: {device_counts}")
            else:
                logging.warning("No devices found in any of the target sites")
                print("Debug: No devices found in any of the target sites")
        except Exception as e:
            logging.error(f"Failed to analyze devices in target sites: {e}")
        
        return

    logging.info(f"Found {len(reboot_targets)} gateway devices to reboot")
    
    # Step 8: Display devices and get user confirmation
    print("\n" + "=" * 100)
    print("🚨 DEVICE REBOOT CONFIRMATION REQUIRED 🚨")
    print("=" * 100)
    print(f"\n📋 The following {len(reboot_targets)} gateway devices will be REBOOTED:")
    print("-" * 100)
    
    # Group devices by template for better display
    devices_by_template = {}
    for target in reboot_targets:
        template_name = target['template_name']
        if template_name not in devices_by_template:
            devices_by_template[template_name] = []
        devices_by_template[template_name].append(target)
    
    # Display devices grouped by template
    for template_name, devices in devices_by_template.items():
        print(f"\n🔧 Template: {template_name}")
        print(f"   📊 {len(devices)} devices affected:")
        for device in devices:
            print(f"      • {device['device_name']} (ID: {device['device_id']}) at site '{device['site_name']}'")
    
    # Display critical warnings in a cleaner format
    warning_lines = [
        "🛑 CRITICAL WARNING - READ CAREFULLY:",
        "• This action will REBOOT network gateway devices",
        "• Network connectivity will be TEMPORARILY LOST during reboot",
        "• Users may experience service interruptions",
        "• Remote sites may become inaccessible during reboot",
        "• This is a DISRUPTIVE network operation",
        "• Ensure you have alternative access methods if needed",
        "• The script owner bears NO LIABILITY for any consequences",
        "• Proceed only if you understand and accept these risks"
    ]
    
    print("\n" + "⚠️" * 50)
    for line in warning_lines:
        print(line)
    print("⚠️" * 50)
    
    print(f"\n📊 Summary:")
    print(f"   • Total devices to reboot: {len(reboot_targets)}")
    print(f"   • Templates involved: {len(devices_by_template)}")
    print(f"   • Sites affected: {len(set(target['site_name'] for target in reboot_targets))}")
    
    # Get user confirmation with liability waiver
    print(f"\n🤔 Do you want to proceed with rebooting {len(reboot_targets)} gateway devices?")
    print("   Type 'REBOOT' (all caps) to confirm, or anything else to cancel:")
    print("   By typing 'REBOOT', you acknowledge and accept all risks and liability.")
    
    try:
        user_input = input(">>> ").strip()
        if user_input != "REBOOT":
            print("❌ Reboot operation cancelled by user.")
            logging.info("Gateway reboot operation cancelled by user input")
            return
        else:
            print("✅ User confirmed reboot operation. Proceeding...")
            logging.info(f"🔥 LIABILITY WAIVER ACCEPTED: User confirmed gateway reboot operation for {len(reboot_targets)} devices")
            logging.info(f"User input: '{user_input}' - User accepts full responsibility and liability for network disruption")
            # Log detailed device list for audit trail
            device_list = [f"{d['device_name']} ({d['device_id']}) at {d['site_name']}" for d in reboot_targets]
            logging.info(f"Devices to be rebooted: {device_list}")
    except KeyboardInterrupt:
        print("\n❌ Reboot operation cancelled by user (Ctrl+C).")
        logging.info("Gateway reboot operation cancelled by user interrupt")
        return
    except Exception as e:
        print(f"❌ Error getting user input: {e}")
        logging.error(f"Error getting user input for reboot confirmation: {e}")
        return

    print("\n🚀 Starting device reboot operations...")
    print("=" * 50)

    # Step 9: Reboot each device and log results
    results = []
    for device in reboot_targets:
        status = ""
        try:
            logging.info(f"Rebooting device '{device['device_name']}' (ID: {device['device_id']})")
            print(f"🔄 Rebooting {device['device_name']} at {device['site_name']}...")
            resp = mistapi.api.v1.sites.devices.restartSiteDevice(
                apisession,
                device["site_id"],
                device["device_id"],
                body={"timestamp": datetime.now(timezone.utc).isoformat()}
            )
            # Handle different possible response formats
            if hasattr(resp, "data") and resp.data:
                if isinstance(resp.data, dict):
                    status = resp.data.get("status", f"SUCCESS - Response: {resp.data}")
                else:
                    status = f"SUCCESS - Data: {resp.data}"
            elif hasattr(resp, "status_code"):
                status = f"SUCCESS - HTTP {resp.status_code}"
            else:
                status = f"SUCCESS - Response: {str(resp)}"
            print(f"   ✅ Reboot command sent successfully")
            logging.info(f"✅ Reboot command sent for '{device['device_name']}': {status}")
        except Exception as e:
            status = f"ERROR: {e}"
            print(f"   ❌ Failed to send reboot command: {e}")
            logging.error(f"❌ Failed to reboot '{device['device_name']}': {e}")

        results.append({
            "Template ID": device["template_id"],
            "Template Name": device["template_name"],
            "Device ID": device["device_id"],
            "Device Name": device["device_name"],
            "Site ID": device["site_id"],
            "Site Name": device["site_name"],
            "Status": status
        })

    # Step 10: Write results to CSV
    try:
        results_csv_path = get_csv_file_path("GatewayTemplateRebootResults.CSV")
        with open(results_csv_path, "w", newline='', encoding="utf-8") as f:
            fieldnames = ["Template ID", "Template Name", "Device ID", "Device Name", "Site ID", "Site Name", "Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n📊 Operation completed!")
        print(f"   ✅ Reboot commands sent to {len(results)} devices")
        print(f"   📝 Results logged to GatewayTemplateRebootResults.CSV")
        logging.info(f"✅ Reboot results written to GatewayTemplateRebootResults.CSV ({len(results)} entries)")
    except Exception as e:
        logging.error(f"❌ Failed to write results to CSV: {e}")
        print(f"❌ Failed to write results to CSV: {e}")


def check_firmware_upgrade_status():
    """
    Check current firmware upgrade status across the organization.
    
    This function provides comprehensive upgrade status monitoring with:
    1. Device-level firmware status from device statistics (fwupdate field)
    2. Site-level upgrade operations and history
    3. Organization-wide upgrade tracking
    4. Current version vs. available version comparison
    5. Upgrade progress monitoring for active operations
    6. Failed upgrade identification and retry status
    7. Bulk status export to CSV for analysis
    8. Interactive site/device filtering options
    
    Reports include:
    - Current firmware versions and upgrade status per device
    - Active upgrade operations with progress tracking
    - Failed upgrades with error details and retry information
    - Upgrade history and completion statistics
    - Version mismatch identification across sites
    """
    logging.info("Starting firmware upgrade status check...")
    logging.debug("Option 60: check_firmware_upgrade_status() initiated")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id}")
    
    print("🔍 Firmware Upgrade Status Check")
    print("=" * 60)
    
    # Step 1: Choose scope (organization-wide or specific site)
    print("\n📊 Select status check scope:")
    print("   [1] Organization-wide status (all sites and devices)")
    print("   [2] Specific site status")
    print("   [3] Active upgrade operations only")
    print("   [4] Failed upgrades only")
    
    while True:
        try:
            scope_choice = input("Select scope (1-4): ").strip()
            if scope_choice in ['1', '2', '3', '4']:
                logging.debug(f"User selected scope: {scope_choice}")
                break
            else:
                print("❌ Invalid selection. Please choose 1-4.")
                logging.debug(f"Invalid scope selection: {scope_choice}")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user.")
            return
    
    site_filter = None
    if scope_choice == '2':
        # Get specific site selection
        logging.debug("User selected specific site mode")
        site_filter = prompt_site_selection()
        if not site_filter:
            print("❌ No site selected. Exiting.")
            logging.warning("No site selected in specific site mode")
            return
        logging.debug(f"Selected site filter: {site_filter}")
    
    # Step 2: Fetch device statistics to get current firmware status
    print(f"\n📡 Fetching device statistics...")
    logging.debug(f"Fetching device statistics with scope: {scope_choice}, site_filter: {site_filter}")
    all_device_stats = []
    upgrade_results = []
    
    try:
        if site_filter:
            # Single site mode
            print(f"   📍 Fetching stats for selected site...")
            logging.debug(f"Fetching stats for single site: {site_filter}")
            stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                apisession, 
                site_filter,
                limit=1000
            )
            site_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
            all_device_stats.extend(site_stats)
            
            print(f"   ✅ Retrieved stats for {len(site_stats)} devices at selected site")
            logging.info(f"Retrieved stats for {len(site_stats)} devices at site {site_filter}")
        else:
            # Organization-wide mode
            print(f"   🌐 Fetching organization-wide device statistics...")
            logging.debug(f"Fetching organization-wide stats for org: {org_id}")
            stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
                apisession, 
                org_id,
                limit=1000
            )
            org_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
            all_device_stats.extend(org_stats)
            
            print(f"   ✅ Retrieved stats for {len(org_stats)} devices organization-wide")
            logging.info(f"Retrieved stats for {len(org_stats)} devices organization-wide")
            
    except Exception as e:
        print(f"❌ Failed to fetch device statistics: {e}")
        logging.error(f"Failed to fetch device statistics: {e}")
        return
    
    if not all_device_stats:
        print("⚠️ No device statistics found.")
        return
    
    # Step 3: Process device firmware status
    print(f"\n🔍 Analyzing firmware status for {len(all_device_stats)} devices...")
    
    firmware_status_summary = {
        'total_devices': 0,
        'devices_with_fwupdate': 0,
        'upgrade_in_progress': 0,
        'upgrade_failed': 0,
        'upgrade_completed': 0,
        'upgrade_unknown': 0,
        'devices_by_status': {},
        'devices_by_version': {},
        'devices_by_model': {}
    }
    
    # Get site information for enrichment
    print(f"   📋 Fetching site information for device enrichment...")
    try:
        sites_resp = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
        all_sites = mistapi.get_all(response=sites_resp, mist_session=apisession)
        site_lookup = {site.get('id'): site.get('name', 'Unknown') for site in all_sites}
    except Exception as e:
        logging.warning(f"Failed to fetch site information: {e}")
        site_lookup = {}
    
    for device_stats in all_device_stats:
        device_id = device_stats.get('id', 'Unknown')
        device_name = device_stats.get('name', 'Unnamed')
        device_mac = device_stats.get('mac', 'Unknown')
        device_model = device_stats.get('model', 'Unknown')
        device_type = device_stats.get('type', 'Unknown')
        device_version = device_stats.get('version', 'Unknown')
        site_id = device_stats.get('site_id', 'Unknown')
        site_name = site_lookup.get(site_id, 'Unknown Site')
        last_seen = device_stats.get('last_seen', 0)
        
        # Process fwupdate status
        fwupdate = device_stats.get('fwupdate', {})
        if fwupdate:
            firmware_status_summary['devices_with_fwupdate'] += 1
            
            fw_status = fwupdate.get('status', 'unknown')
            fw_progress = fwupdate.get('progress', 0)
            fw_timestamp = fwupdate.get('timestamp', 0)
            fw_status_id = fwupdate.get('status_id', 0)
            fw_will_retry = fwupdate.get('will_retry', False)
            
            # Categorize by status
            if fw_status == 'inprogress':
                firmware_status_summary['upgrade_in_progress'] += 1
            elif fw_status == 'failed':
                firmware_status_summary['upgrade_failed'] += 1
            elif fw_status == 'upgraded':
                firmware_status_summary['upgrade_completed'] += 1
            else:
                firmware_status_summary['upgrade_unknown'] += 1
            
            # Track status distribution
            if fw_status not in firmware_status_summary['devices_by_status']:
                firmware_status_summary['devices_by_status'][fw_status] = 0
            firmware_status_summary['devices_by_status'][fw_status] += 1
            
            # Format timestamps for display
            fw_time_str = "Unknown"
            if fw_timestamp:
                try:
                    fw_time_str = datetime.fromtimestamp(fw_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    fw_time_str = str(fw_timestamp)
            
            last_seen_str = "Unknown"
            if last_seen:
                try:
                    last_seen_str = datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    last_seen_str = str(last_seen)
        else:
            fw_status = "no_upgrade_info"
            fw_progress = 0
            fw_timestamp = 0
            fw_status_id = 0
            fw_will_retry = False
            fw_time_str = "N/A"
            last_seen_str = "Unknown"
            if last_seen:
                try:
                    last_seen_str = datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    last_seen_str = str(last_seen)
        
        # Track version distribution
        if device_version not in firmware_status_summary['devices_by_version']:
            firmware_status_summary['devices_by_version'][device_version] = 0
        firmware_status_summary['devices_by_version'][device_version] += 1
        
        # Track model distribution
        if device_model not in firmware_status_summary['devices_by_model']:
            firmware_status_summary['devices_by_model'][device_model] = 0
        firmware_status_summary['devices_by_model'][device_model] += 1
        
        firmware_status_summary['total_devices'] += 1
        
        # Apply scope filtering
        include_device = True
        if scope_choice == '3':  # Active upgrades only
            include_device = fw_status == 'inprogress'
        elif scope_choice == '4':  # Failed upgrades only
            include_device = fw_status == 'failed'
        
        if include_device:
            upgrade_results.append({
                'Site ID': site_id,
                'Site Name': site_name,
                'Device ID': device_id,
                'Device Name': device_name,
                'Device MAC': device_mac,
                'Device Model': device_model,
                'Device Type': device_type,
                'Current Version': device_version,
                'Last Seen': last_seen_str,
                'FW Upgrade Status': fw_status,
                'FW Progress %': fw_progress,
                'FW Status ID': fw_status_id,
                'FW Will Retry': fw_will_retry,
                'FW Timestamp': fw_time_str,
                'Timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    # Step 4: Display summary statistics
    print(f"\n📊 Firmware Status Summary:")
    print(f"   • Total devices analyzed: {firmware_status_summary['total_devices']}")
    print(f"   • Devices with upgrade info: {firmware_status_summary['devices_with_fwupdate']}")
    print(f"   • Upgrades in progress: {firmware_status_summary['upgrade_in_progress']}")
    print(f"   • Upgrades completed: {firmware_status_summary['upgrade_completed']}")
    print(f"   • Upgrades failed: {firmware_status_summary['upgrade_failed']}")
    print(f"   • Unknown status: {firmware_status_summary['upgrade_unknown']}")
    
    if firmware_status_summary['devices_by_status']:
        print(f"\n📋 Status Distribution:")
        for status, count in sorted(firmware_status_summary['devices_by_status'].items()):
            print(f"   • {status}: {count} devices")
    
    print(f"\n📦 Version Distribution:")
    sorted_versions = sorted(firmware_status_summary['devices_by_version'].items(), 
                           key=lambda x: x[1], reverse=True)
    for version, count in sorted_versions[:10]:  # Show top 10 versions
        print(f"   • {version}: {count} devices")
    if len(sorted_versions) > 10:
        print(f"   ... and {len(sorted_versions) - 10} more versions")
    
    print(f"\n🔧 Model Distribution:")
    sorted_models = sorted(firmware_status_summary['devices_by_model'].items(), 
                          key=lambda x: x[1], reverse=True)
    for model, count in sorted_models[:10]:  # Show top 10 models
        print(f"   • {model}: {count} devices")
    if len(sorted_models) > 10:
        print(f"   ... and {len(sorted_models) - 10} more models")
    
    # Step 5: Check for active upgrade operations
    print(f"\n🔍 Checking for active upgrade operations...")
    active_upgrades = []
    
    # Check stored upgrade IDs from option 90
    upgrade_tracking_file = "ActiveUpgrades.json"
    stored_upgrades = []
    
    if os.path.exists(upgrade_tracking_file):
        try:
            with open(upgrade_tracking_file, 'r', encoding='utf-8') as f:
                stored_upgrades = json.load(f)
            
            if stored_upgrades:
                print(f"   💾 Found {len(stored_upgrades)} stored upgrade operations from ActiveUpgrades.json")
                
                # Filter to current org_id
                org_upgrades = [u for u in stored_upgrades if u.get('org_id') == org_id]
                if org_upgrades:
                    print(f"   🎯 {len(org_upgrades)} upgrades match current organization")
                    
                    # Check status of each stored upgrade
                    for upgrade_record in org_upgrades:
                        upgrade_id = upgrade_record.get('upgrade_id')
                        site_id = upgrade_record.get('site_id')
                        site_name = upgrade_record.get('site_name', 'Unknown')
                        
                        if upgrade_id and site_id:
                            try:
                                # Get specific upgrade details
                                upgrade_resp = mistapi.api.v1.sites.devices.getSiteDeviceUpgrade(
                                    apisession, site_id, upgrade_id
                                )
                                
                                if upgrade_resp and hasattr(upgrade_resp, 'data') and upgrade_resp.data:
                                    upgrade_details = upgrade_resp.data
                                    status = upgrade_details.get('status', 'Unknown')
                                    strategy = upgrade_details.get('strategy', 'Unknown')
                                    target_version = upgrade_details.get('target_version', 'Unknown')
                                    
                                    print(f"      ✅ Upgrade {upgrade_id[:8]}... at site '{site_name}': Status = {status}")
                                    
                                    active_upgrades.append({
                                        'upgrade_id': upgrade_id,
                                        'site_id': site_id,
                                        'site_name': site_name,
                                        'status': status,
                                        'strategy': strategy,
                                        'target_version': target_version,
                                        'source': 'stored_tracking',
                                        'details': upgrade_details
                                    })
                                else:
                                    print(f"      ⚠️ Upgrade {upgrade_id[:8]}... at site '{site_name}': No longer active or not found")
                                    
                            except Exception as e:
                                print(f"      ❌ Failed to check upgrade {upgrade_id[:8]}... at site '{site_name}': {e}")
                                logging.warning(f"Failed to check stored upgrade {upgrade_id}: {e}")
                else:
                    print(f"   ℹ️ No stored upgrades match current organization ID")
        except Exception as e:
            print(f"   ⚠️ Failed to read stored upgrade tracking data: {e}")
            logging.warning(f"Failed to read stored upgrade tracking: {e}")
    else:
        print(f"   � No stored upgrade tracking file found (ActiveUpgrades.json)")
    
    # Check organization audit logs for recent upgrade events
    try:
        print(f"   📋 Searching organization audit logs for recent upgrade events...")
        
        # Search for upgrade-related audit events in the last 24 hours
        end_time = int(time.time())
        start_time = end_time - (24 * 60 * 60)  # 24 hours ago
        
        audit_resp = mistapi.api.v1.orgs.logs.listOrgAuditLogs(
            apisession, 
            org_id,
            start=start_time,
            end=end_time,
            limit=1000
        )
        
        audit_logs = mistapi.get_all(response=audit_resp, mist_session=apisession)
        
        if audit_logs:
            upgrade_events = []
            for log_entry in audit_logs:
                message = log_entry.get('message', '').lower()
                if any(keyword in message for keyword in ['upgrade', 'firmware', 'version']):
                    upgrade_events.append(log_entry)
            
            if upgrade_events:
                print(f"      ✅ Found {len(upgrade_events)} upgrade-related audit events in last 24 hours")
                
                # Show recent upgrade events
                for event in upgrade_events[-5:]:  # Show last 5 events
                    timestamp = event.get('timestamp', 0)
                    try:
                        event_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        event_time = 'Unknown'
                    
                    admin_name = event.get('admin_name', 'Unknown')
                    message = event.get('message', 'No message')
                    site_name = event.get('site_name', 'Organization')
                    
                    print(f"         • {event_time} | {admin_name} | {site_name}: {message}")
            else:
                print(f"      ℹ️ No upgrade-related events found in recent audit logs")
        else:
            print(f"      ℹ️ No audit logs retrieved for the last 24 hours")
            
    except Exception as e:
        print(f"   ⚠️ Failed to search organization audit logs: {e}")
        logging.warning(f"Failed to search org audit logs for upgrades: {e}")
    
    # Check organization-level device events for upgrade activity
    try:
        print(f"   📋 Searching organization device events for upgrade activity...")
        
        # Search for device upgrade events
        device_events_resp = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
            apisession,
            org_id,
            type="SYSTEM_UPGRADE_COMPLETED,SYSTEM_UPGRADE_FAILED,SYSTEM_UPGRADE_STARTED",
            start=start_time,
            end=end_time,
            limit=50
        )
        
        device_events = mistapi.get_all(response=device_events_resp, mist_session=apisession)
        
        if device_events:
            print(f"      ✅ Found {len(device_events)} device upgrade events in last 24 hours")
            
            # Group events by type
            events_by_type = {}
            for event in device_events:
                event_type = event.get('type', 'Unknown')
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                events_by_type[event_type].append(event)
            
            for event_type, type_events in events_by_type.items():
                print(f"         • {event_type}: {len(type_events)} events")
                
                # Show a few recent events of this type
                for event in type_events[-3:]:  # Show last 3 of each type
                    timestamp = event.get('timestamp', 0)
                    try:
                        event_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        event_time = 'Unknown'
                    
                    device_name = event.get('device_name', 'Unknown Device')
                    site_name = event.get('site_name', 'Unknown Site')
                    
                    print(f"           - {event_time} | {device_name} at {site_name}")
        else:
            print(f"      ℹ️ No device upgrade events found in last 24 hours")
            
    except Exception as e:
        print(f"   ⚠️ Failed to search device upgrade events: {e}")
        logging.warning(f"Failed to search device upgrade events: {e}")
    
    # Check organization-level upgrades if not filtering by site (legacy approach)
    if not site_filter and not active_upgrades:
        try:
            print(f"   📡 Note: Organization-level upgrade tracking requires specific upgrade IDs")
            print(f"        • Use the stored upgrade tracking above for ongoing operations")
            print(f"        • Or check individual sites below for comprehensive status")
        except Exception as e:
            logging.warning(f"Failed to check org-level upgrades: {e}")
    
    # Check site-level upgrades
    sites_to_check = [site_filter] if site_filter else list(site_lookup.keys())
    
    for site_id in sites_to_check[:5]:  # Limit to first 5 sites for performance
        try:
            site_name = site_lookup.get(site_id, 'Unknown')
            print(f"   📍 Checking site '{site_name}' for active upgrades...")
            
            upgrades_resp = mistapi.api.v1.sites.devices.listSiteDeviceUpgrades(apisession, site_id)
            site_upgrades = mistapi.get_all(response=upgrades_resp, mist_session=apisession)
            
            if site_upgrades:
                print(f"      ✅ Found {len(site_upgrades)} upgrade operations")
                for upgrade in site_upgrades:
                    upgrade_id = upgrade.get('id', 'Unknown')
                    upgrade_status = upgrade.get('status', 'Unknown')
                    upgrade_strategy = upgrade.get('strategy', 'Unknown')
                    target_version = upgrade.get('target_version', 'Unknown')
                    start_time = upgrade.get('start_time', 0)
                    enable_p2p = upgrade.get('enable_p2p', False)
                    counts = upgrade.get('counts', {})
                    
                    start_time_str = "Unknown"
                    if start_time:
                        try:
                            start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            start_time_str = str(start_time)
                    
                    active_upgrades.append({
                        'site_id': site_id,
                        'site_name': site_name,
                        'upgrade_id': upgrade_id,
                        'status': upgrade_status,
                        'strategy': upgrade_strategy,
                        'target_version': target_version,
                        'start_time': start_time_str,
                        'enable_p2p': enable_p2p,
                        'total_devices': counts.get('total', 0),
                        'downloaded': counts.get('downloaded', 0),
                        'download_requested': counts.get('download_requested', 0),
                        'rebooted': counts.get('rebooted', 0),
                        'reboot_in_progress': counts.get('reboot_in_progress', 0),
                        'failed': counts.get('failed', 0),
                        'skipped': counts.get('skipped', 0),
                        'source': 'site_lookup',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
            else:
                print(f"      ℹ️ No upgrade operations found")
                
        except Exception as e:
            print(f"      ❌ Failed to check upgrades for site {site_id}: {e}")
            logging.warning(f"Failed to check upgrades for site {site_id}: {e}")
    
    # Step 6: Export results to CSV
    timestamp_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if upgrade_results:
        device_status_file = f"FirmwareUpgradeStatus_{timestamp_suffix}.csv"
        fieldnames = ['Site ID', 'Site Name', 'Device ID', 'Device Name', 'Device MAC', 
                     'Device Model', 'Device Type', 'Current Version', 'Last Seen',
                     'FW Upgrade Status', 'FW Progress %', 'FW Status ID', 'FW Will Retry',
                     'FW Timestamp', 'Timestamp']
        
        try:
            save_data_to_output(upgrade_results, device_status_file, fieldnames)
            print(f"\n✅ Device firmware status exported to: data/{device_status_file}")
            print(f"   📊 {len(upgrade_results)} device records exported")
            logging.info(f"Exported {len(upgrade_results)} device firmware status records to data/{device_status_file}")
            
        except Exception as e:
            print(f"❌ Failed to export device status: {e}")
            logging.error(f"Failed to export device status: {e}")
    
    if active_upgrades:
        upgrade_ops_file = f"ActiveUpgradeOperations_{timestamp_suffix}.csv"
        upgrade_fieldnames = ['site_id', 'site_name', 'upgrade_id', 'status', 'strategy',
                             'target_version', 'start_time', 'enable_p2p', 'total_devices',
                             'downloaded', 'download_requested', 'rebooted', 'reboot_in_progress',
                             'failed', 'skipped', 'source', 'timestamp']
        
        try:
            # Normalize the active_upgrades data for CSV export
            mapped_upgrades = []
            for upgrade in active_upgrades:
                # Handle both direct field access and details field extraction
                details = upgrade.get('details', {})
                counts = details.get('counts', {}) if details else {}
                
                # Extract or use existing start_time
                start_time = upgrade.get('start_time') or details.get('start_time', 0)
                start_time_str = start_time  # Use as-is if already formatted
                if isinstance(start_time, (int, float)) and start_time > 0:
                    try:
                        start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        start_time_str = str(start_time)
                elif not start_time_str:
                    start_time_str = "Unknown"
                
                # Extract or use existing enable_p2p
                enable_p2p = upgrade.get('enable_p2p')
                if enable_p2p is None and details:
                    enable_p2p = details.get('enable_p2p', 'Unknown')
                
                mapped_upgrade = {
                    'site_id': upgrade.get('site_id', 'Unknown'),
                    'site_name': upgrade.get('site_name', 'Unknown'),
                    'upgrade_id': upgrade.get('upgrade_id', 'Unknown'),
                    'status': upgrade.get('status', 'Unknown'),
                    'strategy': upgrade.get('strategy', 'Unknown'),
                    'target_version': upgrade.get('target_version', 'Unknown'),
                    'start_time': start_time_str,
                    'enable_p2p': enable_p2p,
                    'total_devices': upgrade.get('total_devices') or counts.get('total', 0),
                    'downloaded': upgrade.get('downloaded') or counts.get('downloaded', 0),
                    'download_requested': upgrade.get('download_requested') or counts.get('download_requested', 0),
                    'rebooted': upgrade.get('rebooted') or counts.get('rebooted', 0),
                    'reboot_in_progress': upgrade.get('reboot_in_progress') or counts.get('reboot_in_progress', 0),
                    'failed': upgrade.get('failed') or counts.get('failed', 0),
                    'skipped': upgrade.get('skipped') or counts.get('skipped', 0),
                    'source': upgrade.get('source', 'unknown'),
                    'timestamp': upgrade.get('timestamp') or datetime.now(timezone.utc).isoformat()
                }
                mapped_upgrades.append(mapped_upgrade)
            
            with open(upgrade_ops_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=upgrade_fieldnames)
                writer.writeheader()
                writer.writerows(mapped_upgrades)
            
            print(f"✅ Active upgrade operations exported to: {upgrade_ops_file}")
            print(f"   🔄 {len(active_upgrades)} upgrade operations exported")
            logging.info(f"Exported {len(active_upgrades)} active upgrade operations to {upgrade_ops_file}")
            
        except Exception as e:
            print(f"❌ Failed to export upgrade operations: {e}")
            logging.error(f"Failed to export upgrade operations: {e}")
    
    # Step 7: Summary and recommendations
    print(f"\n📋 Summary and Recommendations:")
    
    if firmware_status_summary['upgrade_failed'] > 0:
        print(f"   ⚠️ {firmware_status_summary['upgrade_failed']} devices have failed upgrades")
        print(f"   💡 Check failed devices for retry eligibility or manual intervention")
    
    if firmware_status_summary['upgrade_in_progress'] > 0:
        print(f"   🔄 {firmware_status_summary['upgrade_in_progress']} devices currently upgrading")
        print(f"   ⏱️ Monitor progress and avoid disrupting these devices")
    
    if len(firmware_status_summary['devices_by_version']) > 3:
        print(f"   📦 Multiple firmware versions detected ({len(firmware_status_summary['devices_by_version'])} different versions)")
        print(f"   🎯 Consider standardizing on a consistent firmware version")
    
    if active_upgrades:
        print(f"   🚀 {len(active_upgrades)} active upgrade operations found")
        print(f"   👀 Monitor upgrade progress in exported CSV files")
    else:
        print(f"   ✅ No active upgrade operations detected")
    
    print(f"\n🔍 Status check complete. Check exported CSV files for detailed analysis.")
    logging.info("Firmware upgrade status check completed successfully")


def get_auto_upgrade_time_settings():
    """
    Helper function to get auto-upgrade time scheduling settings from user input.
    Returns a dictionary with time_of_day and optionally day_of_week settings.
    """
    time_settings = {}
    
    # Time of day configuration
    while True:
        try:
            print(f"   🕐 Enter upgrade time (24-hour format, e.g., 02:00, 14:30):")
            time_input = input("   Time of day (default=02:00): ").strip() or "02:00"
            
            # Validate time format
            try:
                # Try to parse the time to validate format
                datetime.strptime(time_input, "%H:%M")
                time_settings["time_of_day"] = time_input
                print(f"   ✅ Upgrade time set to: {time_input}")
                break
            except ValueError:
                print(f"   ❌ Invalid time format. Please use HH:MM (24-hour format)")
                
        except KeyboardInterrupt:
            print("\n   ❌ Time configuration cancelled")
            time_settings["time_of_day"] = "02:00"  # Default fallback
            break
    
    # Day of week configuration
    print(f"\n   📅 Select upgrade schedule:")
    print(f"      [1] Every day (recommended for most environments)")
    print(f"      [2] Specific day of week")
    
    try:
        schedule_choice = input("   Select option (1-2, default=1): ").strip() or "1"
        
        if schedule_choice == "2":
            # Specific day selection
            days = {
                "1": ("sun", "Sunday"),
                "2": ("mon", "Monday"), 
                "3": ("tue", "Tuesday"),
                "4": ("wed", "Wednesday"),
                "5": ("thu", "Thursday"),
                "6": ("fri", "Friday"),
                "7": ("sat", "Saturday")
            }
            
            print(f"   📅 Select day of week:")
            for key, (day_value, day_name) in days.items():
                print(f"      [{key}] {day_name}")
            
            day_choice = input("   Select day (1-7): ").strip()
            if day_choice in days:
                day_value, day_name = days[day_choice]
                time_settings["day_of_week"] = day_value
                print(f"   ✅ Upgrade day set to: {day_name}")
            else:
                print(f"   ⚠️ Invalid selection, defaulting to every day")
                # Don't set day_of_week (None means every day)
        else:
            # Every day (don't set day_of_week)
            print(f"   ✅ Upgrade schedule: Every day at {time_settings.get('time_of_day', '02:00')}")
            
    except KeyboardInterrupt:
        print("\n   ❌ Schedule configuration cancelled, defaulting to every day")
    
    return time_settings


def bulk_upgrade_ap_firmware_by_site():
    """
    Advanced bulk upgrade AP firmware for APs at selected site(s).
    
    This function provides comprehensive firmware upgrade capabilities with:
    1. Bulk site mode: Reads APUpgradeSiteList.CSV for multi-site upgrades
    2. Single site mode: Interactive site selection (fallback if CSV not found)
    3. Automatic site name-to-ID resolution via organization lookup
    4. Firmware version selection per model across all sites
    5. Advanced upgrade strategies (big_bang, canary, rrm, serial) - default: RRM
    6. P2P firmware sharing options (default: enabled)
    7. Scheduling and failure threshold controls
    8. Device filtering and selection rules
    9. Progress monitoring and rollback options
    10. Comprehensive safety measures and audit logging
    11. Per-site upgrade execution with unified reporting
    
    File Format for APUpgradeSiteList.CSV (headerless, one site name per line):
    Main Office
    Branch Office A
    Remote Site B
    
    Note: Site names must exactly match those in the Mist organization.
    """
    logging.info("Starting advanced bulk AP firmware upgrade by site...")
    logging.debug("Option 90: bulk_upgrade_ap_firmware_by_site() initiated")
    
    # Step 0: Ensure org_id is properly set
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id}")
    
    # Step 1: Check for bulk site upgrade file or get single site selection
    bulk_upgrade_file = "APUpgradeSiteList.CSV"
    bulk_upgrade_file_path = get_csv_file_path(bulk_upgrade_file)
    sites_to_upgrade = []
    
    if os.path.exists(bulk_upgrade_file_path):
        print(f"🔍 Found {bulk_upgrade_file} - Loading sites for bulk upgrade...")
        logging.info(f"Found {bulk_upgrade_file} file, proceeding with bulk site upgrade")
        logging.debug(f"Bulk upgrade file path: {os.path.abspath(bulk_upgrade_file_path)}")
        
        # First, get all sites in the organization for reverse lookup
        print(f"   📡 Fetching organization sites for name-to-ID lookup...")
        logging.debug("Fetching organization sites for name-to-ID mapping")
        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
            all_org_sites = mistapi.get_all(response=response, mist_session=apisession)
            logging.debug(f"Retrieved {len(all_org_sites)} organization sites")
            
            # Build lookup dictionary: site_name -> site_id
            site_name_to_id = {}
            for site in all_org_sites:
                site_name = site.get("name", "").strip()
                site_id = site.get("id", "").strip()
                if site_name and site_id:
                    site_name_to_id[site_name] = site_id
            
            logging.info(f"Built lookup table for {len(site_name_to_id)} organization sites")
            logging.debug(f"Site name mappings: {list(site_name_to_id.keys())[:10]}...")  # Log first 10 site names
            
        except Exception as e:
            print(f"❌ Failed to fetch organization sites: {e}")
            logging.error(f"Failed to fetch organization sites for lookup: {e}")
            return
        
        # Read site names from file (headerless format)
        try:
            logging.debug(f"Reading site names from {bulk_upgrade_file_path}")
            with open(bulk_upgrade_file_path, 'r', encoding='utf-8') as f:
                site_names = []
                for line_num, line in enumerate(f, 1):
                    site_name = line.strip()
                    if site_name:  # Skip empty lines
                        site_names.append(site_name)
                        logging.debug(f"Line {line_num}: Added site '{site_name}'")
            
            if not site_names:
                print(f"❌ No site names found in {bulk_upgrade_file}")
                logging.error(f"No site names found in {bulk_upgrade_file}")
                return
            
            print(f"   📋 Read {len(site_names)} site names from file")
            logging.info(f"Read {len(site_names)} site names from file: {site_names}")
            
            # Resolve site names to site IDs
            sites_to_upgrade = []
            missing_sites = []
            
            for site_name in site_names:
                if site_name in site_name_to_id:
                    site_id = site_name_to_id[site_name]
                    sites_to_upgrade.append({
                        'name': site_name,
                        'id': site_id
                    })
                    logging.debug(f"Resolved site '{site_name}' to ID: {site_id}")
                else:
                    missing_sites.append(site_name)
                    logging.warning(f"Site '{site_name}' not found in organization")
            
            # Report results
            if missing_sites:
                print(f"   ⚠️ Warning: {len(missing_sites)} site(s) not found in organization:")
                for missing_site in missing_sites:
                    print(f"      • '{missing_site}'")
                print(f"   💡 Available sites in organization:")
                available_names = sorted(site_name_to_id.keys())
                for name in available_names[:10]:  # Show first 10 as examples
                    print(f"      • '{name}'")
                if len(available_names) > 10:
                    print(f"      ... and {len(available_names) - 10} more")
                    
            if not sites_to_upgrade:
                print(f"❌ No valid sites found - none of the names in {bulk_upgrade_file} match organization sites")
                logging.error(f"No valid sites found in {bulk_upgrade_file}")
                return
            
            print(f"✅ Successfully resolved {len(sites_to_upgrade)} site(s) for bulk upgrade:")
            for site in sites_to_upgrade:
                print(f"   • {site['name']} (ID: {site['id']})")
            
            logging.info(f"Resolved {len(sites_to_upgrade)} sites for bulk upgrade from {bulk_upgrade_file}")
            
        except Exception as e:
            print(f"❌ Failed to read {bulk_upgrade_file}: {e}")
            logging.error(f"Failed to read {bulk_upgrade_file}: {e}")
            return
    else:
        print(f"📋 {bulk_upgrade_file} not found - Single site mode")
        print(f"   💡 To enable bulk upgrade mode, create '{bulk_upgrade_file}' in the data/ folder")
        print(f"   📝 File format: one site name per line (no header)")
        logging.info(f"{bulk_upgrade_file} not found, proceeding with single site selection")
        
        # Single site selection (existing behavior)
        site_id = prompt_site_selection()
        if not site_id:
            logging.error("No site selected. Exiting.")
            print("❌ No site selected. Exiting.")
            return
        
        # Get site name for display
        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
            logging.info(f"Selected site: {site_name} (ID: {site_id})")
        except Exception as e:
            logging.error(f"Failed to get site name: {e}")
            site_name = site_id
        
        # Convert single site to list format for unified processing
        sites_to_upgrade = [{
            'name': site_name,
            'id': site_id
        }]
    
    # Step 2: Get all APs across all selected sites
    all_aps = []
    all_sites_aps = {}  # Track APs per site
    
    print(f"\n🔍 Fetching APs across {len(sites_to_upgrade)} site(s)...")
    logging.debug(f"Starting AP discovery across {len(sites_to_upgrade)} sites")
    
    for site_info in sites_to_upgrade:
        site_id = site_info['id']
        site_name = site_info['name']
        
        try:
            print(f"   📡 Fetching APs at site '{site_name}'...")
            logging.debug(f"Fetching APs for site: {site_name} (ID: {site_id})")
            response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="ap")
            site_aps = mistapi.get_all(response=response, mist_session=apisession)
            
            if site_aps:
                # Add site info to each AP for tracking
                for ap in site_aps:
                    ap['_site_id'] = site_id
                    ap['_site_name'] = site_name
                
                all_aps.extend(site_aps)
                all_sites_aps[site_id] = {
                    'name': site_name,
                    'aps': site_aps,
                    'count': len(site_aps)
                }
                
                print(f"      ✅ Found {len(site_aps)} APs at '{site_name}'")
                logging.info(f"Found {len(site_aps)} APs at site {site_name} (ID: {site_id})")
                logging.debug(f"AP models at {site_name}: {list(set(ap.get('model', 'Unknown') for ap in site_aps))}")
            else:
                print(f"      ⚠️ No APs found at site '{site_name}'")
                logging.warning(f"No APs found at site {site_name} (ID: {site_id})")
                all_sites_aps[site_id] = {
                    'name': site_name,
                    'aps': [],
                    'count': 0
                }
                
        except Exception as e:
            print(f"      ❌ Failed to fetch APs for site '{site_name}': {e}")
            logging.error(f"Failed to fetch APs for site {site_id} ({site_name}): {e}")
            all_sites_aps[site_id] = {
                'name': site_name,
                'aps': [],
                'count': 0,
                'error': str(e)
            }
    
    if not all_aps:
        print("❌ No APs found across any selected sites.")
        logging.warning("No APs found across any selected sites")
        return
    
    total_aps = len(all_aps)
    sites_with_aps = len([s for s in all_sites_aps.values() if s['count'] > 0])
    
    print(f"\n📊 AP Discovery Summary:")
    print(f"   • Total APs found: {total_aps}")
    print(f"   • Sites with APs: {sites_with_aps}/{len(sites_to_upgrade)}")
    
    for site_id, site_data in all_sites_aps.items():
        site_name = site_data['name']
        ap_count = site_data['count']
        if 'error' in site_data:
            print(f"   • {site_name}: {ap_count} APs (Error: {site_data['error']})")
        else:
            print(f"   • {site_name}: {ap_count} APs")
    
    logging.info(f"Total AP discovery: {total_aps} APs across {sites_with_aps} sites")
    
    # Use all_aps for the rest of the processing (existing variable name)
    aps = all_aps
    
    # Debug: Log the structure of the first AP to see available fields
    if aps and len(aps) > 0:
        sample_ap = aps[0]
        available_fields = list(sample_ap.keys()) if isinstance(sample_ap, dict) else []
        logging.debug(f"Sample AP device structure - Available fields: {available_fields}")
        
        # Check if version field exists in device config (it typically doesn't)
        if 'version' in sample_ap:
            logging.debug(f"Found version in device config: {sample_ap.get('version')}")
        else:
            logging.debug("No version field in device config - will need to use device stats")
    
    # Step 3: Group APs by model and get current firmware versions from device stats
    aps_by_model = {}
    ap_versions = {}  # Cache for AP versions {device_id: version}
    
    print(f"\n🔍 Getting current firmware versions from device statistics...")
    
    # For multi-site upgrades, we need to fetch stats per site
    all_ap_stats = []
    stats_lookup = {}
    
    for site_id, site_data in all_sites_aps.items():
        if site_data['count'] == 0:
            continue  # Skip sites with no APs
            
        site_name = site_data['name']
        site_aps = site_data['aps']
        
        print(f"   📡 Fetching device statistics for {len(site_aps)} APs at '{site_name}'...")
        
        try:
            stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                apisession, 
                site_id, 
                type="ap",
                limit=1000
            )
            site_ap_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
            
            if site_ap_stats:
                all_ap_stats.extend(site_ap_stats)
                
                # Build lookup for this site's devices
                for stats in site_ap_stats:
                    device_id = stats.get("id") or stats.get("device_id") or stats.get("mac")
                    if device_id:
                        stats_lookup[device_id] = stats
                
                logging.info(f"Retrieved stats for {len(site_ap_stats)} devices at site {site_name}")
            else:
                logging.warning(f"No device stats returned for site {site_name}")
                
        except Exception as e:
            logging.error(f"Failed to fetch bulk device stats for site {site_name}: {e}")
            print(f"   ❌ Failed to fetch stats for site '{site_name}': {e}")
            # Continue with other sites
    
    if all_ap_stats:
        logging.info(f"Retrieved stats for {len(all_ap_stats)} total devices via bulk API calls across {len(sites_to_upgrade)} sites")
        logging.debug(f"Stats lookup built with {len(stats_lookup)} entries")
        
        # Log sample stats structure for debugging
        if len(all_ap_stats) > 0:
            sample_stats = all_ap_stats[0]
            available_fields = list(sample_stats.keys()) if isinstance(sample_stats, dict) else []
            logging.debug(f"Sample device stats structure - Available fields: {available_fields}")
            
            # Look for version-related fields in bulk stats
            version_fields = [field for field in available_fields if 'version' in field.lower()]
            if version_fields:
                logging.debug(f"Version-related fields in bulk stats: {version_fields}")
            else:
                logging.debug("No version fields found in bulk stats data")
    else:
        logging.warning("No device stats retrieved from any site")
        print(f"   ⚠️ No device statistics retrieved - falling back to individual calls")
    
    # Process each AP device
    for ap in aps:
        model = ap.get("model", "Unknown")
        device_id = ap.get("id")
        device_mac = ap.get("mac")
        ap_site_id = ap.get("_site_id")  # Site info added during discovery
        ap_site_name = ap.get("_site_name")
        
        if model not in aps_by_model:
            aps_by_model[model] = []
        aps_by_model[model].append(ap)
        
        # Get current firmware version from device stats
        current_version = "Unknown"
        
        if device_id:
            # First try to use the bulk stats lookup
            stats_data = None
            for lookup_key in [device_id, device_mac]:  # Try both ID and MAC as keys
                if lookup_key and lookup_key in stats_lookup:
                    stats_data = stats_lookup[lookup_key]
                    logging.debug(f"Found stats for device {ap.get('name', 'Unnamed')} using key {lookup_key}")
                    break
            
            # If bulk lookup failed, fall back to individual API call
            if not stats_data and ap_site_id:
                try:
                    logging.debug(f"Bulk lookup failed for device {device_id}, making individual API call to site {ap_site_name}")
                    stats_resp = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, ap_site_id, device_id)
                    stats_data = getattr(stats_resp, "data", {})
                except Exception as e:
                    logging.warning(f"Could not get individual stats for device {device_id} at site {ap_site_name}: {e}")
                    stats_data = {}
            
            # Extract version from stats data
            if isinstance(stats_data, dict):
                # Enhanced debugging for first device only to avoid log spam
                if ap == aps[0]:  # Only debug first AP device
                    available_fields = list(stats_data.keys())
                    logging.debug(f"First device {ap.get('name', 'Unnamed')} (ID: {device_id}) stats fields: {available_fields}")
                    
                    # Look for version-related fields
                    version_fields = [field for field in available_fields if 'version' in field.lower()]
                    if version_fields:
                        logging.debug(f"Version-related fields found: {version_fields}")
                        for field in version_fields:
                            logging.debug(f"Field '{field}': {stats_data.get(field)}")
                
                # Extract version using standard field
                current_version = stats_data.get("version", "Unknown")
                logging.debug(f"Device {ap.get('name', 'Unnamed')} (ID: {device_id}) at site {ap_site_name} version: {current_version}")
            else:
                logging.debug(f"Stats data for device {device_id} is not a dict: {type(stats_data)}")
        
        ap_versions[device_id] = current_version
    
    # Summary of API optimization
    bulk_stats_count = len([v for v in ap_versions.values() if v != "Unknown"])
    individual_calls_needed = len([v for v in ap_versions.values() if v == "Unknown"])
    
    print(f"   ✅ Retrieved {bulk_stats_count} device versions via bulk API call")
    if individual_calls_needed > 0:
        print(f"   ⚠️ {individual_calls_needed} devices required individual calls")
    
    logging.info(f"API optimization: {bulk_stats_count} versions from bulk call, {individual_calls_needed} individual calls needed")
    
    print(f"\n📊 AP Models found across {len(sites_to_upgrade)} site(s):")
    for model, devices in aps_by_model.items():
        # Get current versions for this model from our cached stats
        current_versions = set()
        for device in devices:
            device_id = device.get("id")
            current_version = ap_versions.get(device_id, "Unknown")
            current_versions.add(current_version)
        
        # Format current versions display
        if current_versions and "Unknown" not in current_versions:
            current_versions_sorted = sorted(current_versions, reverse=True)
            versions_text = ", ".join(current_versions_sorted)
            print(f"   • {model}: {len(devices)} devices (Current versions: {versions_text})")
        else:
            print(f"   • {model}: {len(devices)} devices (Current versions: Unknown)")
            
        # Show individual device details with site information for better visibility
        if len(sites_to_upgrade) > 1:
            # Multi-site mode - show site grouping
            devices_by_site = {}
            for device in devices:
                site_name = device.get("_site_name", "Unknown Site")
                if site_name not in devices_by_site:
                    devices_by_site[site_name] = []
                devices_by_site[site_name].append(device)
            
            for site_name, site_devices in devices_by_site.items():
                print(f"      📍 {site_name} ({len(site_devices)} devices):")
                for device in site_devices:
                    device_name = device.get("name", "Unnamed")
                    device_mac = device.get("mac", "Unknown")
                    device_id = device.get("id")
                    device_version = ap_versions.get(device_id, "Unknown")
                    print(f"         - {device_name} (MAC: {device_mac}): v{device_version}")
        else:
            # Single site mode - show devices directly
            for device in devices:
                device_name = device.get("name", "Unnamed")
                device_mac = device.get("mac", "Unknown")
                device_id = device.get("id")
                device_version = ap_versions.get(device_id, "Unknown")
                print(f"      - {device_name} (MAC: {device_mac}): v{device_version}")
    
    # Step 4: Get available firmware versions for each model
    print(f"\n🔍 Fetching available firmware versions...")
    logging.debug("Fetching available firmware versions from API")
    try:
        versions_response = mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions(apisession, org_id)
        available_versions = versions_response.data
        logging.info(f"Retrieved firmware versions for organization")
        
        # Log raw response for debugging
        if available_versions:
            total_versions = len(available_versions) if isinstance(available_versions, list) else 0
            logging.debug(f"Raw firmware API response contains {total_versions} version entries")
            if total_versions > 0 and isinstance(available_versions, list):
                sample_version = available_versions[0]
                logging.debug(f"Sample version entry structure: {sample_version}")
                
                # Debug: Check if we have "models" vs "model" field
                has_models = any(v.get("models") for v in available_versions[:5] if isinstance(v, dict))
                has_model = any(v.get("model") for v in available_versions[:5] if isinstance(v, dict))
                logging.debug(f"Firmware API field analysis: has_models={has_models}, has_model={has_model}")
                
                # Debug: Check available metadata fields
                if isinstance(sample_version, dict):
                    available_fields = list(sample_version.keys())
                    logging.debug(f"Available firmware metadata fields: {available_fields}")
        else:
            logging.warning("No firmware versions returned from API")
            
    except Exception as e:
        logging.error(f"Failed to fetch available firmware versions: {e}")
        print(f"❌ Failed to fetch available firmware versions: {e}")
        return
    
    # Step 5: Let user select firmware version for each model
    upgrade_plan = {}
    print(f"\n🎯 Firmware Version Selection:")
    print("=" * 60)
    
    # Show current version summary across all APs
    print(f"📋 Current Firmware Status Summary:")
    all_current_versions = {}
    for model, devices in aps_by_model.items():
        for device in devices:
            device_id = device.get("id")
            version = ap_versions.get(device_id, "Unknown")
            
            if version not in all_current_versions:
                all_current_versions[version] = []
            all_current_versions[version].append(f"{device.get('name', 'Unnamed')} ({model})")
    
    for version, device_list in sorted(all_current_versions.items(), reverse=True):
        print(f"   📦 Version {version}: {len(device_list)} devices")
        for device_info in device_list:
            print(f"      • {device_info}")
    print()
    
    # Show summary of what was found
    if available_versions:
        total_raw_versions = len(available_versions) if isinstance(available_versions, list) else 0
        print(f"📊 Found {total_raw_versions} firmware entries from API")
        logging.info(f"Processing {total_raw_versions} raw firmware version entries for {len(aps_by_model)} AP models")
        
        # Debug: Show what models are available in firmware data
        all_firmware_models = set()
        model_version_ranges = {}  # Track version ranges per model
        
        if isinstance(available_versions, list):
            for version_info in available_versions:
                if isinstance(version_info, dict):
                    # Try both "models" (plural) and "model" (singular) fields
                    models = version_info.get("models", [])
                    model = version_info.get("model")
                    version_num = version_info.get("version", "Unknown")
                    
                    target_models = models if models else ([model] if model else [])
                    
                    for target_model in target_models:
                        all_firmware_models.add(target_model)
                        
                        # Track version ranges for compatibility analysis
                        if target_model not in model_version_ranges:
                            model_version_ranges[target_model] = []
                        model_version_ranges[target_model].append(version_num)
        
        site_models = set(aps_by_model.keys())
        
        logging.debug(f"Models found at site: {sorted(site_models)}")
        logging.debug(f"Models with firmware available: {sorted(all_firmware_models)}")
        
        # Check for model matches
        matching_models = site_models.intersection(all_firmware_models)
        missing_models = site_models - all_firmware_models
        
        if matching_models:
            logging.info(f"Models with firmware available: {sorted(matching_models)}")
        if missing_models:
            logging.warning(f"Models without specific firmware versions: {sorted(missing_models)}")
            print(f"⚠️  Models without specific firmware versions: {', '.join(sorted(missing_models))}")
        
        # Analyze version compatibility across models using API data
        if len(matching_models) > 1:
            print(f"\n🔍 Version Compatibility Analysis (API-based):")
            print(f"   Analyzing firmware compatibility across {len(matching_models)} AP models...")
            
            # Build comprehensive model-to-versions mapping from API data
            api_model_versions = {}
            all_versions_in_api = set()
            
            for model in matching_models:
                if model in model_version_ranges:
                    model_versions = set(model_version_ranges[model])
                    api_model_versions[model] = model_versions
                    all_versions_in_api.update(model_versions)
            
            # Find versions that are compatible across multiple models
            version_compatibility = {}  # version -> set of compatible models
            
            for version in all_versions_in_api:
                compatible_models = set()
                for model, model_versions in api_model_versions.items():
                    if version in model_versions:
                        compatible_models.add(model)
                
                if len(compatible_models) > 1:  # Version works with multiple models
                    version_compatibility[version] = compatible_models
            
            # Sort versions by compatibility (most compatible first)
            if version_compatibility:
                sorted_by_compatibility = sorted(
                    version_compatibility.items(),
                    key=lambda x: (len(x[1]), tuple(map(int, x[0].split("."))) if x[0].replace(".", "").isdigit() else (0,)),
                    reverse=True
                )
                
                print(f"   🤝 Cross-compatible versions (work with multiple models):")
                for version, compatible_models in sorted_by_compatibility[:10]:  # Show top 10
                    model_list = ", ".join(sorted(compatible_models))
                    coverage = f"{len(compatible_models)}/{len(matching_models)}"
                    if len(compatible_models) == len(matching_models):
                        print(f"      ⭐ {version}: ALL models ({model_list}) - UNIVERSAL")
                    elif len(compatible_models) >= len(matching_models) * 0.7:  # 70%+ coverage
                        print(f"      ✅ {version}: {coverage} models ({model_list}) - HIGH COMPATIBILITY")
                    else:
                        print(f"      📋 {version}: {coverage} models ({model_list})")
                
                # Highlight universal versions
                universal_versions = [v for v, models in version_compatibility.items() if len(models) == len(matching_models)]
                if universal_versions:
                    sorted_universal = sorted(universal_versions, key=lambda x: tuple(map(int, x.split("."))) if x.replace(".", "").isdigit() else (0,), reverse=True)
                    print(f"\n   🌟 UNIVERSAL versions (compatible with ALL {len(matching_models)} models):")
                    print(f"      {', '.join(sorted_universal[:5])}{' ...' if len(sorted_universal) > 5 else ''}")
                    print(f"   💡 Recommendation: Use universal version for simplified management")
                    logging.info(f"Found {len(universal_versions)} universal versions across all models")
                else:
                    print(f"\n   ⚠️  NO universal versions found - mixed-version upgrade required")
                    print(f"   💡 Recommendation: Select optimal version per model based on compatibility matrix above")
                    logging.warning("No universal firmware versions found across all AP models")
            else:
                print(f"   ⚠️  NO cross-compatible versions found - each model has unique firmware options")
                logging.warning("No cross-compatible versions found between models")
            
            # Show model-specific version counts for context
            print(f"\n   📋 Model-specific firmware availability:")
            for model in sorted(matching_models):
                if model in api_model_versions:
                    versions = api_model_versions[model]
                    sorted_versions = sorted(versions, key=lambda x: tuple(map(int, x.split("."))) if x.replace(".", "").isdigit() else (0,), reverse=True)
                    latest_version = sorted_versions[0] if sorted_versions else "Unknown"
                    oldest_version = sorted_versions[-1] if len(sorted_versions) > 1 else latest_version
                    
                    if len(sorted_versions) > 1:
                        range_text = f"{oldest_version} to {latest_version}"
                    else:
                        range_text = latest_version
                    
                    print(f"      • {model}: {len(versions)} versions ({range_text})")
        
        elif len(matching_models) == 1:
            model = list(matching_models)[0]
            print(f"\n📋 Single model environment: {model}")
            if model in model_version_ranges:
                versions = model_version_ranges[model]
                print(f"   📦 {len(versions)} firmware versions available for {model}")
            else:
                print(f"   ⚠️  No specific firmware versions found for {model}")
    
    
    for model, devices in aps_by_model.items():
        # Filter available versions for this specific model only
        raw_model_versions = []
        if available_versions and isinstance(available_versions, list):
            for version_info in available_versions:
                if isinstance(version_info, dict):
                    # Check both "models" (plural) and "model" (singular) fields
                    models = version_info.get("models", [])
                    single_model = version_info.get("model")
                    
                    # Only include versions that explicitly list this model
                    if model in models or single_model == model:
                        raw_model_versions.append(version_info)
        
        # Deduplicate versions by version number while preserving metadata
        version_dict = {}
        for version_info in raw_model_versions:
            version_num = version_info.get("version", "Unknown")
            if version_num not in version_dict:
                version_dict[version_num] = version_info
            else:
                # Merge metadata from duplicate entries, preferring non-empty values
                existing = version_dict[version_num]
                for key in ["release_date", "recommended", "package_url"]:
                    if not existing.get(key) and version_info.get(key):
                        existing[key] = version_info.get(key)
        
        # Convert back to list and sort by version (newest first, assuming semantic versioning)
        model_versions = list(version_dict.values())
        try:
            # Sort by version number (descending) - handle different version formats
            model_versions.sort(key=lambda x: tuple(map(int, x.get("version", "0.0.0").split("."))), reverse=True)
        except ValueError:
            # Fallback to string sorting if version parsing fails
            model_versions.sort(key=lambda x: x.get("version", ""), reverse=True)
        
        if not model_versions:
            print(f"⚠️  No firmware versions found for model '{model}' - skipping {len(devices)} devices")
            print(f"   (This model may not have specific firmware versions listed, or no updates available)")
            logging.warning(f"No firmware versions found for model {model} - checked {len(raw_model_versions)} entries before deduplication")
            continue
        
        logging.debug(f"Model {model}: Found {len(raw_model_versions)} raw entries, {len(model_versions)} unique versions after deduplication")
        
        print(f"\n🔧 Model: {model} ({len(devices)} devices)")
        
        # Show current versions of devices using cached stats
        current_versions = set()
        for device in devices:
            device_id = device.get("id")
            current_version = ap_versions.get(device_id, "Unknown")
            current_versions.add(current_version)
        
        if current_versions and "Unknown" not in current_versions:
            current_versions_sorted = sorted(current_versions, reverse=True)
            print(f"   Current versions in use: {', '.join(current_versions_sorted)}")
        else:
            print(f"   Current versions in use: Unknown")
        
        # Check if this model has version compatibility constraints
        if len(aps_by_model) > 1:
            model_version_count = len(model_versions)
            all_other_models = [m for m in aps_by_model.keys() if m != model]
            
            # Estimate version compatibility with other models
            compatibility_note = ""
            if model_version_count < 10:  # Fewer versions might indicate older/constrained model
                compatibility_note = f" (Limited version range - may have compatibility constraints)"
            elif model_version_count > 30:  # Many versions might indicate newer/flexible model
                compatibility_note = f" (Wide version range available)"
            
            if compatibility_note:
                print(f"   Model compatibility: {model_version_count} versions available{compatibility_note}")
                if len(all_other_models) > 0:
                    print(f"   💡 Note: Different models may support different version ranges")
        
        # Display available versions with index - now model-specific and deduplicated
        print(f"   Available firmware versions for {model} ({len(model_versions)} found):")
        
        # Build cross-compatibility information if multiple models present
        other_models = [m for m in aps_by_model.keys() if m != model]
        cross_compatibility = {}
        
        if other_models and 'model_version_ranges' in locals():
            # Check which versions from this model are also available for other models
            for version_info in model_versions:
                version_num = version_info.get("version", "Unknown")
                compatible_models = []
                
                # Check each other model to see if they also support this version
                for other_model in other_models:
                    if other_model in model_version_ranges:
                        if version_num in model_version_ranges[other_model]:
                            compatible_models.append(other_model)
                
                if compatible_models:
                    cross_compatibility[version_num] = compatible_models
        
        for idx, version in enumerate(model_versions):
            version_num = version.get("version", "Unknown")
            is_recommended = version.get("recommended", False)
            
            # Build version display with indicators
            indicators = []
            
            if is_recommended:
                indicators.append("RECOMMENDED")
            
            # Check if this version is currently in use
            if version_num in current_versions:
                indicators.append("CURRENT")
            
            # Check cross-compatibility with other models
            if version_num in cross_compatibility:
                compatible_models = cross_compatibility[version_num]
                if len(compatible_models) == len(other_models):
                    indicators.append("UNIVERSAL")  # Works with all other models
                elif len(compatible_models) >= len(other_models) * 0.7:  # 70%+ compatibility
                    indicators.append("HIGH COMPAT")
                else:
                    indicators.append("SOME COMPAT")
            elif other_models:  # Only show if there are other models to be compatible with
                indicators.append("MODEL SPECIFIC")
            
            # Format indicators
            indicator_text = f" [{', '.join(indicators)}]" if indicators else ""
            
            # Show cross-compatibility details for better user understanding
            compat_detail = ""
            if version_num in cross_compatibility:
                compatible_models = cross_compatibility[version_num]
                if len(compatible_models) > 0:
                    compat_detail = f" (also works with: {', '.join(compatible_models)})"
            
            print(f"      [{idx}] {version_num}{indicator_text}{compat_detail}")
            
            # Log version details for debugging
            logging.debug(f"Model {model} version {idx}: {version_num}, recommended: {is_recommended}, cross_compatible: {cross_compatibility.get(version_num, [])}")
        
        # Add guidance about cross-compatibility if multiple models present
        if other_models and cross_compatibility:
            universal_versions = [v for v, models in cross_compatibility.items() if len(models) == len(other_models)]
            if universal_versions:
                print(f"   💡 UNIVERSAL versions work with all models: {', '.join(universal_versions[:3])}")
            else:
                high_compat_versions = [v for v, models in cross_compatibility.items() if len(models) >= len(other_models) * 0.7]
                if high_compat_versions:
                    print(f"   💡 HIGH COMPATIBILITY versions work with most models: {', '.join(high_compat_versions[:3])}")
        
        print()  # Add blank line for readability
        
        # Get user selection
        while True:
            try:
                user_input = input(f"Select firmware version for {model} (0-{len(model_versions)-1}, or 's' to skip): ").strip().lower()
                
                if user_input == 's':
                    print(f"⏭️  Skipping firmware upgrade for {model}")
                    logging.info(f"User chose to skip firmware upgrade for model {model}")
                    break
                
                version_idx = int(user_input)
                if 0 <= version_idx < len(model_versions):
                    selected_version = model_versions[version_idx]
                    version_num = selected_version.get("version", "Unknown")
                    is_recommended = selected_version.get("recommended", False)
                    is_current = version_num in current_versions
                    
                    # Provide feedback about the selection
                    selection_notes = []
                    if is_recommended:
                        selection_notes.append("RECOMMENDED")
                    if is_current:
                        selection_notes.append("CURRENT")
                    
                    notes_text = f" ({', '.join(selection_notes)})" if selection_notes else ""
                    
                    upgrade_plan[model] = {
                        "version": version_num,
                        "version_info": selected_version,
                        "devices": devices
                    }
                    print(f"✅ Selected version {version_num} for {model}{notes_text}")
                    logging.info(f"User selected firmware version {version_num} for model {model} (recommended: {is_recommended}, current: {is_current})")
                    break
                else:
                    print(f"❌ Invalid selection. Please enter a number between 0 and {len(model_versions)-1}, or 's' to skip.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number or 's' to skip.")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user.")
                logging.info("Bulk AP firmware upgrade cancelled by user interrupt")
                return
    
    if not upgrade_plan:
        print("❌ No firmware upgrades selected. Exiting.")
        logging.info("No firmware upgrades selected by user")
        return
    
    # Step 5.5: Upgrade Plan Summary and Compatibility Validation
    print(f"\n📋 Upgrade Plan Summary:")
    print("=" * 60)
    
    total_devices_to_upgrade = 0
    selected_versions = set()
    models_in_plan = list(upgrade_plan.keys())
    
    for model, plan_info in upgrade_plan.items():
        version = plan_info["version"]
        device_count = len(plan_info["devices"])
        total_devices_to_upgrade += device_count
        selected_versions.add(version)
        
        print(f"   🔧 {model}: {device_count} devices → firmware {version}")
    
    print(f"\n📊 Summary:")
    print(f"   • Total models: {len(upgrade_plan)}")
    print(f"   • Total devices: {total_devices_to_upgrade}")
    print(f"   • Firmware versions: {len(selected_versions)}")
    
    # Highlight coordination considerations for mixed-version upgrades
    if len(selected_versions) > 1:
        sorted_versions = sorted(selected_versions, key=lambda x: tuple(map(int, x.split("."))) if x.replace(".", "").isdigit() else (0,), reverse=True)
        print(f"\n⚠️  Multi-Version Upgrade Detected:")
        print(f"   📦 Versions selected: {', '.join(sorted_versions)}")
        
        # Analyze if any selected versions are cross-compatible
        if 'model_version_ranges' in locals():
            # Check if any of the selected versions could have been universal
            could_be_universal = []
            for version in selected_versions:
                compatible_count = 0
                for model in models_in_plan:
                    if model in model_version_ranges and version in model_version_ranges[model]:
                        compatible_count += 1
                
                if compatible_count == len(models_in_plan):
                    could_be_universal.append(version)
            
            if could_be_universal:
                print(f"   🔍 Analysis: Version(s) {', '.join(could_be_universal)} could work with ALL models")
                print(f"   💭 Consider: You chose model-specific versions despite universal options available")
                print(f"      This may be optimal for performance/features per model")
            else:
                print(f"   🔍 Analysis: No single version compatible with all selected models")
                print(f"   💡 Multi-version upgrade is necessary due to model firmware constraints")
        
        print(f"\n   📋 Coordination considerations:")
        print(f"      • Each model will upgrade to its optimal version")
        print(f"      • Network features may vary between firmware versions")
        print(f"      • Monitor compatibility for shared network functions")
        print(f"      • Consider upgrade timing to minimize impact")
        
        logging.info(f"Multi-version upgrade plan: {len(selected_versions)} different versions across {len(models_in_plan)} models")
        
        # Ask user for confirmation on mixed-version upgrade
        print(f"\n🤔 Proceed with multi-version upgrade plan?")
        confirm_mixed = input("   Continue? (y/n, default=y): ").strip().lower() or "y"
        if confirm_mixed not in ['y', 'yes']:
            print("❌ Mixed-version upgrade cancelled by user.")
            logging.info("Mixed-version upgrade cancelled by user")
            return
        else:
            print("✅ Multi-version upgrade plan confirmed.")
    else:
        single_version = list(selected_versions)[0]
        print(f"\n✅ Single-Version Upgrade:")
        print(f"   📦 All {len(models_in_plan)} model(s) will upgrade to firmware {single_version}")
        
        # Analyze if this version is truly universal or if users just happened to select the same version
        if len(models_in_plan) > 1 and 'model_version_ranges' in locals():
            universal_compatibility = True
            for model in models_in_plan:
                if model not in model_version_ranges or single_version not in model_version_ranges[model]:
                    universal_compatibility = False
                    break
            
            if universal_compatibility:
                print(f"   🌟 Excellent choice: {single_version} is UNIVERSAL (compatible with all models)")
                print(f"   💡 Unified firmware version simplifies management and ensures feature consistency")
            else:
                print(f"   ⚠️  Note: Selected version may not be verified as compatible with all models")
                print(f"   💡 Proceed with caution and monitor compatibility during upgrade")
        else:
            print(f"   💡 Consistent firmware version across all AP models")
        
        logging.info(f"Single-version upgrade plan: all models upgrading to {single_version}")
    
    print(f"\n🚀 Ready to proceed with advanced configuration...")
    logging.info(f"Upgrade plan validated: {total_devices_to_upgrade} devices across {len(models_in_plan)} models")
    
    # Step 6: Advanced Configuration Options
    print(f"\n⚙️ Advanced Upgrade Configuration:")
    print("=" * 60)
    
    # Select upgrade strategy
    strategies = {
        "1": ("big_bang", "Upgrade all devices at once (fastest, higher risk)"),
        "2": ("canary", "Phased rollout with configurable phases (safer, slower)"),
        "3": ("rrm", "Radio Resource Management aware upgrade (AP-only, intelligent)"),
        "4": ("serial", "One device at a time (safest, slowest)")
    }
    
    print("🎯 Select upgrade strategy:")
    for key, (strategy, description) in strategies.items():
        print(f"   [{key}] {strategy.upper()}: {description}")
    
    while True:
        try:
            strategy_choice = input("Select strategy (1-4, default=3 for rrm): ").strip() or "3"
            if strategy_choice in strategies:
                selected_strategy, strategy_desc = strategies[strategy_choice]
                print(f"✅ Selected strategy: {selected_strategy.upper()}")
                logging.info(f"User selected upgrade strategy: {selected_strategy}")
                break
            else:
                print("❌ Invalid selection. Please choose 1-4.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user.")
            logging.info("AP firmware upgrade cancelled during strategy selection")
            return
    
    # Advanced strategy-specific options
    upgrade_config = {
        "strategy": selected_strategy,
        "force": False,
        "enable_p2p": True,  # Default to enabled
        "max_failure_percentage": 5,
        "start_time": None,
        "canary_phases": [1, 10, 50, 100],
        "p2p_cluster_size": 10,
        "reboot": True  # APs auto-reboot, but explicit for clarity
    }
    
    # Strategy-specific configuration
    if selected_strategy == "canary":
        print(f"\n🔧 Canary Strategy Configuration:")
        
        # Custom phases
        use_custom_phases = input("Use custom canary phases? (y/N): ").strip().lower()
        if use_custom_phases in ['y', 'yes']:
            while True:
                try:
                    phases_input = input("Enter comma-separated percentages (e.g., 2,10,25,100): ").strip()
                    if phases_input:
                        phases = [int(x.strip()) for x in phases_input.split(',')]
                        if all(1 <= p <= 100 for p in phases) and phases[-1] == 100:
                            upgrade_config["canary_phases"] = phases
                            print(f"✅ Custom phases: {phases}")
                            break
                        else:
                            print("❌ Phases must be 1-100 and end with 100")
                    else:
                        break
                except ValueError:
                    print("❌ Invalid format. Use comma-separated numbers.")
        
        # Failure threshold
        try:
            failure_input = input(f"Max failure percentage per phase (default={upgrade_config['max_failure_percentage']}%): ").strip()
            if failure_input:
                failure_pct = int(failure_input)
                if 0 <= failure_pct <= 100:
                    upgrade_config["max_failure_percentage"] = failure_pct
                    print(f"✅ Max failures: {failure_pct}%")
        except ValueError:
            print("⚠️ Invalid input, using default failure threshold")
    
    elif selected_strategy == "rrm":
        print(f"\n🔧 RRM Strategy Configuration:")
        
        # RRM-specific options
        rrm_options = {
            "rrm_node_order": "fringe_to_center",
            "rrm_first_batch_percentage": 2,
            "rrm_max_batch_percentage": 10,
            "rrm_slow_ramp": True,
            "rrm_mesh_upgrade": "sequential"
        }
        
        # Node order selection
        node_orders = {
            "1": ("fringe_to_center", "Start from edge APs (recommended)"),
            "2": ("center_to_fringe", "Start from central APs")
        }
        
        print("Select RRM node order:")
        for key, (order, desc) in node_orders.items():
            print(f"   [{key}] {desc}")
        
        order_choice = input("Select order (1-2, default=1): ").strip() or "1"
        if order_choice in node_orders:
            rrm_options["rrm_node_order"] = node_orders[order_choice][0]
            print(f"✅ Node order: {node_orders[order_choice][1]}")
        
        # Batch size configuration
        try:
            first_batch = input(f"First batch percentage (default={rrm_options['rrm_first_batch_percentage']}%): ").strip()
            if first_batch:
                rrm_options["rrm_first_batch_percentage"] = int(first_batch)
            
            max_batch = input(f"Max batch percentage (default={rrm_options['rrm_max_batch_percentage']}%): ").strip()
            if max_batch:
                rrm_options["rrm_max_batch_percentage"] = int(max_batch)
        except ValueError:
            print("⚠️ Invalid input, using default batch sizes")
        
        upgrade_config.update(rrm_options)
    
    # P2P Configuration (all strategies)
    print(f"\n🔗 Peer-to-Peer (P2P) Configuration:")
    enable_p2p = input("Enable AP-to-AP firmware sharing? (Y/n): ").strip().lower()
    if enable_p2p not in ['n', 'no']:
        upgrade_config["enable_p2p"] = True
        print("✅ P2P enabled - APs will share firmware locally")
        
        try:
            cluster_size = input(f"P2P cluster size (default={upgrade_config['p2p_cluster_size']}): ").strip()
            if cluster_size:
                upgrade_config["p2p_cluster_size"] = int(cluster_size)
                print(f"✅ P2P cluster size: {upgrade_config['p2p_cluster_size']}")
        except ValueError:
            print("⚠️ Invalid input, using default cluster size")
    else:
        print("⚠️ P2P disabled - all firmware downloads from cloud")
    
    # Scheduling Options
    print(f"\n📅 Scheduling Options:")
    schedule_later = input("Schedule upgrade for later? (y/N): ").strip().lower()
    if schedule_later in ['y', 'yes']:
        while True:
            try:
                time_input = input("Enter start time (YYYY-MM-DD HH:MM or +minutes): ").strip()
                if time_input.startswith('+'):
                    # Relative time
                    minutes = int(time_input[1:])
                    start_time = int(time.time()) + (minutes * 60)
                    upgrade_config["start_time"] = start_time
                    scheduled_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M')
                    print(f"✅ Scheduled for: {scheduled_time}")
                    break
                else:
                    # Absolute time
                    dt = datetime.strptime(time_input, '%Y-%m-%d %H:%M')
                    start_time = int(dt.timestamp())
                    upgrade_config["start_time"] = start_time
                    print(f"✅ Scheduled for: {time_input}")
                    break
            except ValueError:
                print("❌ Invalid format. Use 'YYYY-MM-DD HH:MM' or '+minutes'")
                retry = input("Try again? (y/N): ").strip().lower()
                if retry not in ['y', 'yes']:
                    break
    
    # Force upgrade option
    force_upgrade = input("Force upgrade even if same version? (y/N): ").strip().lower()
    if force_upgrade in ['y', 'yes']:
        upgrade_config["force"] = True
        print("⚠️ Force upgrade enabled")
    
    # Display final configuration
    print(f"\n📋 Final Upgrade Configuration:")
    print("=" * 60)
    print(f"Strategy: {upgrade_config['strategy'].upper()}")
    if upgrade_config.get('start_time'):
        scheduled_time = datetime.fromtimestamp(upgrade_config['start_time']).strftime('%Y-%m-%d %H:%M')
        print(f"Scheduled: {scheduled_time}")
    else:
        print("Scheduled: Immediate")
    print(f"P2P Enabled: {upgrade_config['enable_p2p']}")
    if upgrade_config['enable_p2p']:
        print(f"P2P Cluster Size: {upgrade_config['p2p_cluster_size']}")
    print(f"Force Upgrade: {upgrade_config['force']}")
    print(f"Max Failure Rate: {upgrade_config['max_failure_percentage']}%")
    
    if upgrade_config['strategy'] == 'canary':
        print(f"Canary Phases: {upgrade_config['canary_phases']}%")
    elif upgrade_config['strategy'] == 'rrm':
        print(f"RRM Node Order: {upgrade_config.get('rrm_node_order', 'fringe_to_center')}")
        print(f"RRM First Batch: {upgrade_config.get('rrm_first_batch_percentage', 2)}%")
        print(f"RRM Max Batch: {upgrade_config.get('rrm_max_batch_percentage', 10)}%")
    
    # Step 7: Display upgrade plan and affected devices
    total_devices = sum(len(plan["devices"]) for plan in upgrade_plan.values())
    print(f"\n📋 Final Firmware Upgrade Plan:")
    print("=" * 60)
    
    if len(sites_to_upgrade) > 1:
        print(f"Bulk Upgrade Mode: {len(sites_to_upgrade)} sites")
        for site_info in sites_to_upgrade:
            site_count = sum(1 for plan in upgrade_plan.values() 
                           for device in plan["devices"] 
                           if device.get("_site_id") == site_info['id'])
            print(f"   • {site_info['name']}: {site_count} devices")
    else:
        print(f"Site: {sites_to_upgrade[0]['name']}")
    
    print(f"Total devices to upgrade: {total_devices}")
    print(f"Upgrade strategy: {upgrade_config['strategy'].upper()}")
    
    for model, plan in upgrade_plan.items():
        version = plan["version"]
        devices = plan["devices"]
        print(f"\n🔧 {model} → Firmware {version} ({len(devices)} devices):")
        
        if len(sites_to_upgrade) > 1:
            # Group devices by site for multi-site display
            devices_by_site = {}
            for device in devices:
                site_name = device.get("_site_name", "Unknown Site")
                if site_name not in devices_by_site:
                    devices_by_site[site_name] = []
                devices_by_site[site_name].append(device)
            
            for site_name, site_devices in devices_by_site.items():
                print(f"   📍 {site_name} ({len(site_devices)} devices):")
                for device in site_devices:
                    device_name = device.get("name", "Unnamed")
                    mac = device.get("mac", "Unknown")
                    device_id = device.get("id")
                    current_version = ap_versions.get(device_id, "Unknown")
                    print(f"      • {device_name} (MAC: {mac}) - Current: {current_version}")
        else:
            # Single site display
            for device in devices:
                device_name = device.get("name", "Unnamed")
                mac = device.get("mac", "Unknown")
                device_id = device.get("id")
                current_version = ap_versions.get(device_id, "Unknown")
                print(f"   • {device_name} (MAC: {mac}) - Current: {current_version}")
    
    # Step 8: Display warnings and get user confirmation
    warning_lines = [
        "🛑 CRITICAL WARNING - ADVANCED FIRMWARE UPGRADE OPERATION:",
        "• This action will UPGRADE FIRMWARE on Access Point devices",
        "• APs will REBOOT during the upgrade process",
        "• Wi-Fi connectivity will be TEMPORARILY LOST during upgrades", 
        "• Users will experience Wi-Fi service interruptions",
        "• Firmware upgrades can take 5-15 minutes per device",
        "• Failed upgrades may require manual recovery",
        "• This is a DISRUPTIVE network operation",
        "• Always ensure you have physical access to devices if recovery is needed",
        f"• Upgrade strategy: {upgrade_config['strategy'].upper()}",
        f"• Max failure tolerance: {upgrade_config['max_failure_percentage']}%",
        "• P2P enabled: " + ("Yes" if upgrade_config['enable_p2p'] else "No"),
        "• The script owner bears NO LIABILITY for any consequences",
        "• Proceed only if you understand and accept these risks"
    ]
    
    print("\n" + "⚠️" * 50)
    for line in warning_lines:
        print(line)
    print("⚠️" * 50)
    
    print(f"\n📊 Summary:")
    if len(sites_to_upgrade) > 1:
        print(f"   • Bulk upgrade across {len(sites_to_upgrade)} sites")
        sites_with_devices = len(set(device.get("_site_name") for plan in upgrade_plan.values() for device in plan["devices"]))
        print(f"   • Sites with devices to upgrade: {sites_with_devices}")
    else:
        print(f"   • Site: {sites_to_upgrade[0]['name']}")
    print(f"   • Total APs to upgrade: {total_devices}")
    print(f"   • Models affected: {len(upgrade_plan)}")
    print(f"   • Strategy: {upgrade_config['strategy'].upper()}")
    
    # Show target firmware versions for each model
    print(f"   • Target firmware versions:")
    for model, plan in upgrade_plan.items():
        version = plan["version"]
        device_count = len(plan["devices"])
        print(f"      - {model}: v{version} ({device_count} devices)")
    
    if upgrade_config.get('start_time'):
        scheduled_time = datetime.fromtimestamp(upgrade_config['start_time']).strftime('%Y-%m-%d %H:%M')
        print(f"   • Scheduled: {scheduled_time}")
    else:
        print(f"   • Scheduled: Immediate")
    
    # Get user confirmation with liability waiver
    print(f"\n🤔 Do you want to proceed with upgrading {total_devices} AP devices?")
    print("   Type 'UPGRADE' (all caps) to confirm, or anything else to cancel:")
    print("   By typing 'UPGRADE', you acknowledge and accept all risks and liability.")
    
    try:
        user_input = input(">>> ").strip()
        if user_input != "UPGRADE":
            print("❌ Advanced firmware upgrade operation cancelled by user.")
            logging.info("Advanced AP firmware upgrade operation cancelled by user input")
            return
        else:
            print("✅ User confirmed advanced firmware upgrade operation. Proceeding...")
            logging.info(f"🔥 LIABILITY WAIVER ACCEPTED: User confirmed advanced AP firmware upgrade for {total_devices} devices at site {site_name}")
            logging.info(f"User input: '{user_input}' - User accepts full responsibility for firmware upgrade risks")
            logging.info(f"Upgrade strategy: {upgrade_config['strategy']}, P2P: {upgrade_config['enable_p2p']}, Max failures: {upgrade_config['max_failure_percentage']}%")
            # Log detailed upgrade plan for audit trail
            plan_summary = []
            for model, plan in upgrade_plan.items():
                plan_summary.append(f"{model}→{plan['version']} ({len(plan['devices'])} devices)")
            logging.info(f"Upgrade plan: {'; '.join(plan_summary)}")
            
    except KeyboardInterrupt:
        print("\n❌ Firmware upgrade operation cancelled by user (Ctrl+C).")
        logging.info("AP firmware upgrade operation cancelled by user interrupt")
        return
    except Exception as e:
        print(f"❌ Error getting user input: {e}")
        logging.error(f"Error getting user input for upgrade confirmation: {e}")
        return
    
    # Step 9: Execute advanced firmware upgrades
    print("\n🚀 Starting advanced AP firmware upgrade operations...")
    print("=" * 60)
    logging.info("Starting firmware upgrade execution phase")
    logging.debug(f"Upgrade strategy: {upgrade_config['strategy']}, P2P: {upgrade_config['enable_p2p']}, Max failures: {upgrade_config['max_failure_percentage']}%")
    
    results = []
    successful_upgrades = 0
    failed_upgrades = 0
    upgrade_ids = []  # Track multiple upgrade IDs for multi-site
    
    # Organize devices by site for execution
    logging.debug("Organizing devices by site for execution")
    devices_by_site = {}
    for model, plan in upgrade_plan.items():
        version = plan["version"]
        devices = plan["devices"]
        logging.debug(f"Processing {len(devices)} devices for model {model} → firmware {version}")
        
        for device in devices:
            site_id = device.get("_site_id")
            site_name = device.get("_site_name")
            
            if site_id not in devices_by_site:
                logging.debug(f"Creating new site entry for {site_name} (ID: {site_id})")
                devices_by_site[site_id] = {
                    'name': site_name,
                    'devices': [],
                    'models': {}
                }
            
            devices_by_site[site_id]['devices'].append(device)
            
            # Track model/version per site
            if model not in devices_by_site[site_id]['models']:
                devices_by_site[site_id]['models'][model] = {
                    'version': version,
                    'devices': []
                }
            devices_by_site[site_id]['models'][model]['devices'].append(device)
    
    logging.debug(f"Device organization complete: {len(devices_by_site)} sites")
    for site_id, site_data in devices_by_site.items():
        logging.debug(f"  Site {site_data['name']}: {len(site_data['devices'])} devices, {len(site_data['models'])} models")
    
    total_sites_to_upgrade = len(devices_by_site)
    total_devices = sum(len(site_data['devices']) for site_data in devices_by_site.values())
    logging.debug(f"Upgrade execution will process {total_devices} devices across {total_sites_to_upgrade} sites")
    
    print(f"\n🔄 Executing upgrades across {total_sites_to_upgrade} site(s) with {total_devices} devices...")
    
    for site_index, (site_id, site_data) in enumerate(devices_by_site.items(), 1):
        site_name = site_data['name']
        site_devices = site_data['devices']
        site_models = site_data['models']
        
        logging.debug(f"Starting upgrade execution for site {site_index}/{total_sites_to_upgrade}: {site_name}")
        print(f"\n   📍 Site {site_index}/{total_sites_to_upgrade}: {site_name} ({len(site_devices)} devices)")
        print(f"   Strategy: {upgrade_config['strategy'].upper()}")
        print(f"   P2P Enabled: {upgrade_config['enable_p2p']}")
        
        try:
            # Prepare upgrade request for this site
            device_ids = [device.get("id") for device in site_devices if device.get("id")]
            
            # Check if all devices in this site use the same firmware version
            site_versions = set(model_info['version'] for model_info in site_models.values())
            
            if len(site_versions) == 1:
                # Single version for this site
                target_version = list(site_versions)[0]
                
                upgrade_body = {
                    "strategy": upgrade_config["strategy"],
                    "force": upgrade_config["force"],
                    "enable_p2p": upgrade_config["enable_p2p"],
                    "max_failure_percentage": upgrade_config["max_failure_percentage"],
                    "reboot": upgrade_config["reboot"],
                    "version": target_version,
                    "device_ids": device_ids
                }
                
                # Add P2P configuration
                if upgrade_config["enable_p2p"]:
                    upgrade_body["p2p_cluster_size"] = upgrade_config["p2p_cluster_size"]
                
                # Add strategy-specific options
                if upgrade_config["strategy"] == "canary":
                    upgrade_body["canary_phases"] = upgrade_config["canary_phases"]
                elif upgrade_config["strategy"] == "rrm":
                    for key in ["rrm_node_order", "rrm_first_batch_percentage", "rrm_max_batch_percentage", "rrm_slow_ramp", "rrm_mesh_upgrade"]:
                        if key in upgrade_config:
                            upgrade_body[key] = upgrade_config[key]
                
                # Add scheduling
                if upgrade_config.get("start_time"):
                    upgrade_body["start_time"] = upgrade_config["start_time"]
                
                logging.debug(f"Prepared upgrade body for site {site_name}: {upgrade_body}")
                print(f"      📡 Upgrading all devices to version {target_version}...")
                logging.info(f"Initiating upgrade for site {site_name} with {len(device_ids)} devices to version {target_version}")
                
                logging.debug(f"Calling upgradeSiteDevices API for site {site_id}")
                resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(
                    apisession,
                    site_id,
                    body=upgrade_body
                )
                logging.debug(f"upgradeSiteDevices API call completed for site {site_name}")
                
                # Handle response
                upgrade_id = None
                if hasattr(resp, "data") and resp.data:
                    logging.debug(f"Upgrade response data: {resp.data}")
                    if isinstance(resp.data, dict) and "upgrade_id" in resp.data:
                        upgrade_id = resp.data["upgrade_id"]
                        upgrade_ids.append(upgrade_id)
                        logging.debug(f"Upgrade ID captured: {upgrade_id}")
                        print(f"      ✅ Upgrade initiated - ID: {upgrade_id}")
                    else:
                        logging.debug(f"Upgrade initiated without specific upgrade ID")
                        print(f"      ✅ Upgrade command sent successfully")
                else:
                    logging.warning(f"Upgrade response missing data for site {site_name}")
                
                successful_upgrades += len(site_devices)
                logging.info(f"✅ Site {site_name} upgrade initiated for {len(site_devices)} devices")
                
            else:
                # Multiple versions for this site - separate calls per model
                print(f"      🔧 Multiple firmware versions for site - executing per model...")
                
                for model, model_info in site_models.items():
                    model_version = model_info['version']
                    model_devices = model_info['devices']
                    model_device_ids = [device.get("id") for device in model_devices if device.get("id")]
                    
                    print(f"         • {model}: {len(model_devices)} devices → v{model_version}")
                    
                    model_upgrade_body = {
                        "strategy": upgrade_config["strategy"],
                        "force": upgrade_config["force"],
                        "enable_p2p": upgrade_config["enable_p2p"],
                        "max_failure_percentage": upgrade_config["max_failure_percentage"],
                        "reboot": upgrade_config["reboot"],
                        "version": model_version,
                        "device_ids": model_device_ids
                    }
                    
                    # Add P2P and strategy configs
                    if upgrade_config["enable_p2p"]:
                        model_upgrade_body["p2p_cluster_size"] = upgrade_config["p2p_cluster_size"]
                    if upgrade_config["strategy"] == "canary":
                        model_upgrade_body["canary_phases"] = upgrade_config["canary_phases"]
                    elif upgrade_config["strategy"] == "rrm":
                        for key in ["rrm_node_order", "rrm_first_batch_percentage", "rrm_max_batch_percentage", "rrm_slow_ramp", "rrm_mesh_upgrade"]:
                            if key in upgrade_config:
                                model_upgrade_body[key] = upgrade_config[key]
                    if upgrade_config.get("start_time"):
                        model_upgrade_body["start_time"] = upgrade_config["start_time"]
                    
                    logging.debug(f"Prepared per-model upgrade body for {model}: {model_upgrade_body}")
                    logging.debug(f"Calling upgradeSiteDevices API for {model} devices in site {site_name}")
                    model_resp = mistapi.api.v1.sites.devices.upgradeSiteDevices(
                        apisession,
                        site_id,
                        body=model_upgrade_body
                    )
                    logging.debug(f"Per-model upgradeSiteDevices API call completed for {model}")
                    
                    # Handle model upgrade response
                    if hasattr(model_resp, "data") and model_resp.data and isinstance(model_resp.data, dict):
                        logging.debug(f"Per-model upgrade response data for {model}: {model_resp.data}")
                        if "upgrade_id" in model_resp.data:
                            model_upgrade_id = model_resp.data["upgrade_id"]
                            upgrade_ids.append(model_upgrade_id)
                            logging.debug(f"Per-model upgrade ID captured for {model}: {model_upgrade_id}")
                            print(f"            ✅ {model} upgrade initiated - ID: {model_upgrade_id}")
                        else:
                            logging.debug(f"Per-model upgrade initiated for {model} without specific upgrade ID")
                            print(f"            ✅ {model} upgrade command sent")
                    else:
                        logging.warning(f"Per-model upgrade response missing data for {model} in site {site_name}")
                    
                    successful_upgrades += len(model_devices)
            
            # Log each device for audit trail
            for device in site_devices:
                device_name = device.get("name", "Unnamed")
                device_mac = device.get("mac", "Unknown")
                device_id = device.get("id", "Unknown")
                device_model = device.get("model", "Unknown")
                current_version = ap_versions.get(device_id, "Unknown")
                
                # Find target version for this device
                target_version = "Unknown"
                for model, plan in upgrade_plan.items():
                    if device in plan["devices"]:
                        target_version = plan["version"]
                        break
                
                results.append({
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": device_id,
                    "Device Name": device_name,
                    "Device MAC": device_mac,
                    "Model": device_model,
                    "Current Version": current_version,
                    "Target Version": target_version,
                    "Strategy": upgrade_config["strategy"],
                    "P2P Enabled": upgrade_config["enable_p2p"],
                    "Max Failure %": upgrade_config["max_failure_percentage"],
                    "Force Upgrade": upgrade_config["force"],
                    "Upgrade ID": upgrade_id or "Multiple",
                    "Status": "Advanced Upgrade Initiated",
                    "Timestamp": datetime.now(timezone.utc).isoformat()
                })
                
        except Exception as e:
            error_status = f"ERROR: {e}"
            print(f"      ❌ Failed to initiate upgrade for site {site_name}: {e}")
            logging.error(f"❌ Failed to initiate upgrade for site {site_name}: {e}")
            failed_upgrades += len(site_devices)
            
            # Log failed devices
            for device in site_devices:
                device_name = device.get("name", "Unnamed")
                device_mac = device.get("mac", "Unknown")
                device_id = device.get("id", "Unknown")
                device_model = device.get("model", "Unknown")
                current_version = ap_versions.get(device_id, "Unknown")
                
                # Find target version for this device
                target_version = "Unknown"
                for model, plan in upgrade_plan.items():
                    if device in plan["devices"]:
                        target_version = plan["version"]
                        break
                
                results.append({
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": device_id,
                    "Device Name": device_name,
                    "Device MAC": device_mac,
                    "Model": device_model,
                    "Current Version": current_version,
                    "Target Version": target_version,
                    "Strategy": upgrade_config["strategy"],
                    "P2P Enabled": upgrade_config["enable_p2p"],
                    "Max Failure %": upgrade_config["max_failure_percentage"],
                    "Force Upgrade": upgrade_config["force"],
                    "Upgrade ID": "Failed",
                    "Status": error_status,
                    "Timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    # Step 10: Configure site auto-upgrade settings
    logging.debug(f"Starting auto-upgrade configuration for site {site_name} (ID: {site_id})")
    print(f"\n⚙️ Configuring site auto-upgrade settings...")
    
    # Collect unique versions from upgrade plan
    target_versions = set(plan["version"] for plan in upgrade_plan.values())
    logging.debug(f"Collected target versions from upgrade plan: {target_versions}")
    
    if len(target_versions) == 1:
        # Single version - configure auto-upgrade for the site
        target_version = list(target_versions)[0]
        logging.debug(f"Single target version detected: {target_version}")
        
        auto_upgrade_prompt = input(f"Configure site auto-upgrade settings? (Y/n): ").strip().lower()
        logging.debug(f"User auto-upgrade configuration choice: '{auto_upgrade_prompt}'")
        if auto_upgrade_prompt not in ['n', 'no']:
            try:
                logging.debug(f"Proceeding with auto-upgrade configuration for site {site_name}")
                print(f"   🔧 Configuring site auto-upgrade settings...")
                
                # Get current site settings to check existing auto-upgrade configuration
                logging.debug(f"Retrieving current auto-upgrade settings for site {site_name}")
                current_auto_upgrade = None
                current_settings = {}
                try:
                    current_settings_resp = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)
                    logging.debug(f"API call getSiteSetting completed for site {site_id}")
                    current_settings = current_settings_resp.data if hasattr(current_settings_resp, 'data') else {}
                    current_auto_upgrade = current_settings.get("auto_upgrade", {}) if isinstance(current_settings, dict) else {}
                    
                    logging.debug(f"Current auto-upgrade settings retrieved: {current_auto_upgrade}")
                    
                    # Display current auto-upgrade settings if they exist
                    if current_auto_upgrade and current_auto_upgrade.get("enabled"):
                        logging.debug(f"Auto-upgrade currently enabled for site {site_name}")
                        print(f"   📋 Current auto-upgrade settings:")
                        print(f"      • Enabled: Yes")
                        print(f"      • Version: {current_auto_upgrade.get('version', 'Not set')}")
                        print(f"      • Time of day: {current_auto_upgrade.get('time_of_day', 'Not set')}")
                        day_of_week = current_auto_upgrade.get('day_of_week')
                        if day_of_week:
                            print(f"      • Day of week: {day_of_week}")
                        else:
                            print(f"      • Day of week: Every day")
                    else:
                        logging.debug(f"Auto-upgrade currently disabled or not configured for site {site_name}")
                        print(f"   📋 Current auto-upgrade: Disabled or not configured")
                        
                except Exception as e:
                    logging.warning(f"Could not retrieve current site settings: {e}")
                    print(f"   ⚠️ Could not retrieve current settings: {e}")
                
                # Auto-upgrade configuration options
                logging.debug(f"Presenting auto-upgrade configuration options for target version {target_version}")
                print(f"\n   ⚙️ Auto-upgrade configuration options:")
                print(f"      [1] Enable auto-upgrade to version {target_version}")
                print(f"      [2] Disable auto-upgrade") 
                print(f"      [3] Skip auto-upgrade configuration")
                
                config_choice = input(f"   Select option (1-3, default=1): ").strip() or "1"
                logging.debug(f"User auto-upgrade configuration choice: '{config_choice}'")
                
                if config_choice == "2":
                    # Disable auto-upgrade
                    logging.debug(f"Configuring auto-upgrade to be disabled for site {site_name}")
                    new_auto_upgrade = {
                        "enabled": False
                    }
                    print(f"   ✅ Auto-upgrade will be disabled")
                elif config_choice == "3":
                    # Skip configuration
                    logging.debug(f"Skipping auto-upgrade configuration for site {site_name}")
                    print("   ⏭️ Skipping site auto-upgrade configuration")
                    logging.info("User chose to skip site auto-upgrade configuration")
                    # Continue without configuring auto-upgrade
                    pass
                else:
                    # Enable auto-upgrade (option 1 or fallback)
                    logging.debug(f"Enabling comprehensive auto-upgrade for site {site_name} with target version {target_version}")
                    print(f"   🔧 Configuring comprehensive auto-upgrade settings...")
                    print(f"   💡 This ensures all AP models get appropriate firmware automatically")
                    
                    # Build custom_versions dictionary starting with models from the upgrade plan
                    custom_versions = {}
                    models_in_upgrade_plan = set(upgrade_plan.keys())
                    logging.debug(f"Models in upgrade plan: {models_in_upgrade_plan}")
                    
                    # Get all models from the upgrade plan and set their target versions
                    for model, plan in upgrade_plan.items():
                        model_version = plan["version"]
                        custom_versions[model] = model_version
                        logging.debug(f"Setting custom version for {model}: {model_version}")
                        print(f"      ✅ {model}: {model_version} (from upgrade plan)")
                    
                    logging.debug(f"Starting AP model family analysis for comprehensive auto-upgrade coverage")
                    print(f"\n   🔍 Analyzing all available AP models for comprehensive auto-upgrade coverage...")
                    
                    # Get all available models from the firmware API
                    all_available_models = set()
                    model_version_ranges = {}
                    
                    if 'available_versions' in locals() and available_versions:
                        logging.debug(f"Processing available_versions data with {len(available_versions)} entries")
                        for version_info in available_versions:
                            if isinstance(version_info, dict):
                                # Try both "models" (plural) and "model" (singular) fields
                                models = version_info.get("models", [])
                                model = version_info.get("model")
                                version_num = version_info.get("version", "Unknown")
                                
                                target_models = models if models else ([model] if model else [])
                                
                                for target_model in target_models:
                                    if target_model:
                                        all_available_models.add(target_model)
                                        
                                        # Track version ranges for comprehensive coverage
                                        if target_model not in model_version_ranges:
                                            model_version_ranges[target_model] = []
                                        model_version_ranges[target_model].append(version_num)
                    
                    logging.debug(f"All available models discovered: {all_available_models}")
                    logging.debug(f"Model version ranges: {len(model_version_ranges)} models tracked")
                    
                    # Find models that are available but not in the current upgrade plan
                    models_not_in_plan = all_available_models - models_in_upgrade_plan
                    logging.debug(f"Models not in upgrade plan: {models_not_in_plan}")
                    
                    if models_not_in_plan:
                        logging.debug(f"Processing {len(models_not_in_plan)} additional AP models for auto-upgrade configuration")
                        print(f"\n   📋 Found {len(models_not_in_plan)} additional AP models available for auto-upgrade:")
                        
                        # Group models by their available firmware versions (AP families)
                        def get_version_signature(model_versions):
                            """Create a signature of available versions for grouping"""
                            return tuple(sorted(set(model_versions)))
                        
                        model_families = {}  # signature -> list of models
                        for model in models_not_in_plan:
                            if model in model_version_ranges:
                                signature = get_version_signature(model_version_ranges[model])
                                if signature not in model_families:
                                    model_families[signature] = []
                                model_families[signature].append(model)
                        
                        logging.debug(f"Created {len(model_families)} AP model families based on firmware version signatures")
                        
                        # Display grouped models
                        family_count = 0
                        for signature, models in model_families.items():
                            family_count += 1
                            logging.debug(f"Family {family_count}: {models} with {len(signature)} firmware versions")
                            if len(models) > 1:
                                print(f"      • AP Family {family_count}: {', '.join(sorted(models))} ({len(signature)} firmware versions)")
                            else:
                                print(f"      • {models[0]} ({len(signature)} firmware versions)")
                        
                        print(f"\n   🎯 Configure auto-upgrade for additional models:")
                        print(f"   Models with identical firmware versions are grouped together as families.")
                        print(f"   This ensures new APs of ANY model will auto-upgrade to appropriate firmware.")
                        
                        configure_additional = input(f"   Configure auto-upgrade for additional models? (Y/n): ").strip().lower()
                        logging.debug(f"User choice for additional model configuration: '{configure_additional}'")
                        
                        if configure_additional not in ['n', 'no']:
                            logging.debug(f"Proceeding with firmware version selection for {len(model_families)} model families")
                            print(f"\n   📦 Selecting firmware versions for additional model families...")
                            print(f"   Strategy: Highest version per major revision (e.g., highest 0.12.x, highest 0.14.x)")
                            
                            # Process each family group
                            for family_idx, (signature, models) in enumerate(model_families.items(), 1):
                                if not models:  # Skip empty groups
                                    logging.debug(f"Skipping empty family group {family_idx}")
                                    continue
                                    
                                logging.debug(f"Processing family {family_idx} with models: {models}")
                                
                                # Get firmware versions for this family (all models have the same versions)
                                representative_model = models[0]
                                if representative_model not in model_version_ranges:
                                    logging.warning(f"No firmware versions found for representative model {representative_model} in family {models}")
                                    print(f"      ⚠️ No firmware versions found for model family {models}")
                                    continue
                                
                                family_versions = model_version_ranges[representative_model]
                                logging.debug(f"Family {family_idx} has {len(family_versions)} firmware versions: {family_versions}")
                                
                                # Group versions by major revision
                                major_revisions = {}
                                for version in family_versions:
                                    try:
                                        # Extract major.minor (e.g., "0.12" from "0.12.27452")
                                        parts = version.split(".")
                                        if len(parts) >= 2:
                                            major_minor = f"{parts[0]}.{parts[1]}"
                                            if major_minor not in major_revisions:
                                                major_revisions[major_minor] = []
                                            major_revisions[major_minor].append(version)
                                    except:
                                        # Fallback for non-standard version formats
                                        major_minor = "other"
                                        if major_minor not in major_revisions:
                                            major_revisions[major_minor] = []
                                        major_revisions[major_minor].append(version)
                                
                                logging.debug(f"Family {family_idx} major revisions: {list(major_revisions.keys())}")
                                
                                # Find highest version for each major revision
                                highest_per_major = {}
                                for major_minor, versions in major_revisions.items():
                                    try:
                                        # Sort versions within this major revision
                                        sorted_versions = sorted(versions, key=lambda x: tuple(map(int, x.split("."))), reverse=True)
                                        highest_per_major[major_minor] = sorted_versions[0]
                                    except:
                                        # Fallback to string sorting
                                        sorted_versions = sorted(versions, reverse=True)
                                        highest_per_major[major_minor] = sorted_versions[0]
                                
                                logging.debug(f"Family {family_idx} highest versions per major: {highest_per_major}")
                                
                                # Display family information
                                if len(models) > 1:
                                    print(f"\n      🔧 AP Family {family_idx}: {', '.join(sorted(models))}")
                                    print(f"         These models share identical firmware version compatibility")
                                else:
                                    print(f"\n      🔧 Model: {models[0]}")
                                    
                                print(f"         Available major revisions with highest versions:")
                                
                                # Display options for this family
                                major_options = {}
                                for idx, (major_minor, highest_version) in enumerate(sorted(highest_per_major.items()), 1):
                                    print(f"            [{idx}] {major_minor}.x → {highest_version}")
                                    major_options[str(idx)] = highest_version
                                
                                print(f"            [s] Skip this family")
                                
                                # Get user selection for the entire family
                                while True:
                                    try:
                                        family_name = f"Family {family_idx}" if len(models) > 1 else models[0]
                                        user_choice = input(f"         Select firmware for {family_name} (1-{len(major_options)}, s): ").strip().lower()
                                        
                                        if user_choice == 's':
                                            print(f"         ⏭️ Skipping {family_name}")
                                            break
                                        elif user_choice in major_options:
                                            selected_version = major_options[user_choice]
                                            # Apply the selected version to all models in this family
                                            for model in models:
                                                custom_versions[model] = selected_version
                                            print(f"         ✅ {family_name} → firmware {selected_version}")
                                            print(f"            Applied to: {', '.join(sorted(models))}")
                                            break
                                        else:
                                            print(f"         ❌ Invalid selection. Please choose 1-{len(major_options)} or 's'.")
                                    except KeyboardInterrupt:
                                        print("\n         ❌ Configuration cancelled.")
                                        break
                    
                    # Validate that we have comprehensive model coverage
                    total_models_configured = len(custom_versions)
                    models_from_plan = len(models_in_upgrade_plan)
                    models_additionally_configured = total_models_configured - models_from_plan
                    
                    print(f"\n   ✅ Auto-upgrade coverage summary:")
                    print(f"      • Models from upgrade plan: {models_from_plan}")
                    print(f"      • Additional models configured: {models_additionally_configured}")
                    print(f"      • Total models configured: {total_models_configured}")
                    
                    if total_models_configured > 0:
                        print(f"\n   📋 Complete auto-upgrade model configuration:")
                        for model, version in sorted(custom_versions.items()):
                            status = "from upgrade plan" if model in models_in_upgrade_plan else "additional coverage"
                            print(f"      • {model} → firmware {version} ({status})")

                    new_auto_upgrade = {
                        "enabled": True,
                        "version": "custom",  # Use "custom" to indicate custom_versions are in use
                        "custom_versions": custom_versions
                    }
                    
                    # Time scheduling configuration
                    print(f"\n   ⏰ Auto-upgrade time scheduling:")
                    
                    # Check if user wants to maintain current time settings or change them
                    if current_auto_upgrade and current_auto_upgrade.get("time_of_day"):
                        current_time = current_auto_upgrade.get("time_of_day")
                        current_day = current_auto_upgrade.get("day_of_week")
                        
                        if current_day:
                            current_schedule = f"{current_time} on {current_day}"
                        else:
                            current_schedule = f"{current_time} every day"
                        
                        maintain_time = input(f"   Keep current schedule ({current_schedule})? (Y/n): ").strip().lower()
                        
                        if maintain_time not in ['n', 'no']:
                            # Maintain current time settings
                            new_auto_upgrade["time_of_day"] = current_time
                            if current_day:
                                new_auto_upgrade["day_of_week"] = current_day
                            print(f"   ✅ Maintaining current schedule: {current_schedule}")
                        else:
                            # Configure new time settings
                            print(f"   🕐 Configure new auto-upgrade schedule:")
                            new_auto_upgrade.update(get_auto_upgrade_time_settings())
                    else:
                        # No current time settings, get new ones
                        print(f"   🕐 Configure auto-upgrade schedule:")
                        new_auto_upgrade.update(get_auto_upgrade_time_settings())
                
                # Only proceed with site settings update if user didn't choose to skip
                if config_choice != "3":
                    # Prepare final site settings update
                    logging.debug(f"Preparing auto-upgrade settings update for site {site_name}")
                    site_settings_body = {
                        "auto_upgrade": new_auto_upgrade
                    }
                    logging.debug(f"Auto-upgrade configuration to apply: {new_auto_upgrade}")
                    
                    # Merge with existing settings to preserve other configurations
                    if isinstance(current_settings, dict):
                        logging.debug(f"Merging with existing site settings to preserve other configurations")
                        current_settings.update(site_settings_body)
                        site_settings_body = current_settings
                    
                    # Update site settings
                    logging.debug(f"Calling updateSiteSettings API for site {site_id}")
                    settings_resp = mistapi.api.v1.sites.setting.updateSiteSettings(
                        apisession,
                        site_id,
                        body=site_settings_body
                    )
                    logging.debug(f"updateSiteSettings API call completed for site {site_name}")
                    
                    if new_auto_upgrade.get("enabled", False):
                        logging.info(f"Site auto-upgrade configured successfully for {site_name}")
                        print(f"   ✅ Site auto-upgrade configured successfully")
                        custom_versions = new_auto_upgrade.get("custom_versions", {})
                        if custom_versions:
                            logging.debug(f"Auto-upgrade configured with {len(custom_versions)} custom model versions")
                            print(f"   📋 New/replacement APs will auto-upgrade per model:")
                            for model, version in custom_versions.items():
                                print(f"      • {model}: {version}")
                            
                            # Log with model details
                            version_summary = ", ".join([f"{m}:{v}" for m, v in custom_versions.items()])
                            logging.info(f"Site auto-upgrade configured: site={site_id}, custom_versions={version_summary}")
                        else:
                            logging.debug(f"Auto-upgrade configured with standard version {target_version}")
                            print(f"   📋 New/replacement APs will auto-upgrade to configured version")
                            logging.info(f"Site auto-upgrade configured: site={site_id}")
                    else:
                        logging.info(f"Site auto-upgrade disabled for {site_name}")
                        print(f"   ✅ Site auto-upgrade disabled successfully")
                        print(f"   📋 New/replacement APs will NOT auto-upgrade")
                        logging.info(f"Site auto-upgrade disabled: site={site_id}")
                    
                    # Add to results for audit trail
                    if new_auto_upgrade.get("enabled", False):
                        # Auto-upgrade is enabled - set appropriate values
                        custom_versions = new_auto_upgrade.get("custom_versions", {})
                        if custom_versions:
                            version_summary = ", ".join([f"{m}:{v}" for m, v in custom_versions.items()])
                            target_version_display = f"Custom: {version_summary}"
                            status_display = "Site Auto-Upgrade Configured (Custom Versions)"
                        else:
                            target_version_display = target_version
                            status_display = "Site Auto-Upgrade Configured"
                    else:
                        # Auto-upgrade is disabled
                        target_version_display = "DISABLED"
                        status_display = "Site Auto-Upgrade Disabled"
                    
                    auto_upgrade_result = {
                        "Site ID": site_id,
                        "Site Name": site_name,
                        "Device ID": "SITE_CONFIG",
                        "Device Name": "Auto-Upgrade Setting",
                        "Device MAC": "N/A",
                        "Model": "Site Configuration",
                        "Current Version": "N/A",
                        "Target Version": target_version_display,
                        "Strategy": upgrade_config["strategy"],
                        "P2P Enabled": upgrade_config["enable_p2p"],
                        "Max Failure %": upgrade_config["max_failure_percentage"],
                        "Force Upgrade": upgrade_config["force"],
                        "Upgrade ID": "SITE_AUTO_UPGRADE",
                        "Status": status_display,
                        "Timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    results.append(auto_upgrade_result)
                
            except Exception as e:
                error_msg = f"Failed to configure site auto-upgrade: {e}"
                print(f"   ❌ {error_msg}")
                logging.error(f"❌ {error_msg}")
                
                # Add failure to results
                auto_upgrade_result = {
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": "SITE_CONFIG",
                    "Device Name": "Auto-Upgrade Setting",
                    "Device MAC": "N/A",
                    "Model": "Site Configuration",
                    "Current Version": "N/A",
                    "Target Version": "ERROR",
                    "Strategy": upgrade_config["strategy"],
                    "P2P Enabled": upgrade_config["enable_p2p"],
                    "Max Failure %": upgrade_config["max_failure_percentage"],
                    "Force Upgrade": upgrade_config["force"],
                    "Upgrade ID": "SITE_AUTO_UPGRADE",
                    "Status": f"ERROR: {e}",
                    "Timestamp": datetime.now(timezone.utc).isoformat()
                }
                results.append(auto_upgrade_result)
        else:
            print("   ⏭️ Skipping site auto-upgrade configuration")
            logging.info("User chose to skip site auto-upgrade configuration")
    
    else:
        # Multiple versions - need careful auto-upgrade configuration
        print(f"   ⚠️ Multiple firmware versions in upgrade plan:")
        for version in sorted(target_versions):
            models_with_version = [model for model, plan in upgrade_plan.items() if plan["version"] == version]
            print(f"      • Version {version}: {', '.join(models_with_version)}")
        
        print(f"\n   🔍 Auto-Upgrade Configuration for Mixed-Model Environment:")
        print(f"   Site auto-upgrade must handle different AP models with different firmware capabilities.")
        
        # Analyze what models exist in the upgrade plan
        all_models_in_plan = set(upgrade_plan.keys())
        print(f"\n   📋 AP Models in this upgrade plan: {', '.join(sorted(all_models_in_plan))}")
        
        # Provide enhanced options for mixed-model auto-upgrade
        print(f"\n   ⚙️ Auto-upgrade options for mixed-model environment:")
        print(f"      [1] Configure custom versions per model (RECOMMENDED)")
        print(f"         • Each AP model gets its optimal firmware version")
        print(f"         • New APs will auto-upgrade to model-appropriate firmware")
        print(f"         • Handles model compatibility constraints automatically")
        print(f"      [2] Disable auto-upgrade")
        print(f"         • Manual firmware management required for new APs")
        print(f"         • Prevents version conflicts but requires more maintenance")
        print(f"      [3] Skip auto-upgrade configuration")
        print(f"         • Leave current auto-upgrade settings unchanged")
        
        auto_upgrade_choice = input("   Select auto-upgrade option (1-3, default=1): ").strip() or "1"
        
        try:
            if auto_upgrade_choice == "3":
                print("   ⏭️ Skipping site auto-upgrade configuration")
                logging.info("User chose to skip site auto-upgrade configuration for multi-version upgrade")
                
            elif auto_upgrade_choice == "2":
                # Disable auto-upgrade
                print(f"   🔧 Disabling site auto-upgrade...")
                
                # Configure auto-upgrade disabled
                site_settings_body = {
                    "auto_upgrade": {
                        "enabled": False
                    }
                }
                
                # Get and merge current settings
                try:
                    current_settings_resp = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)
                    current_settings = current_settings_resp.data if hasattr(current_settings_resp, 'data') else {}
                    if isinstance(current_settings, dict):
                        current_settings.update(site_settings_body)
                        site_settings_body = current_settings
                except Exception as e:
                    logging.warning(f"Could not retrieve current site settings: {e}")
                
                settings_resp = mistapi.api.v1.sites.setting.updateSiteSettings(
                    apisession,
                    site_id,
                    body=site_settings_body
                )
                
                print(f"   ✅ Site auto-upgrade disabled successfully")
                print(f"   📋 New/replacement APs will NOT auto-upgrade")
                print(f"   💡 Manual firmware management will be required for new devices")
                logging.info(f"Site auto-upgrade disabled: site={site_id} (user selected disable from multi-version upgrade)")
                
                # Add to results
                auto_upgrade_result = {
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": "SITE_CONFIG",
                    "Device Name": "Auto-Upgrade Setting",
                    "Device MAC": "N/A",
                    "Model": "Site Configuration",
                    "Current Version": "N/A",
                    "Target Version": "DISABLED",
                    "Strategy": upgrade_config["strategy"],
                    "P2P Enabled": upgrade_config["enable_p2p"],
                    "Max Failure %": upgrade_config["max_failure_percentage"],
                    "Force Upgrade": upgrade_config["force"],
                    "Upgrade ID": "SITE_AUTO_UPGRADE",
                    "Status": "Site Auto-Upgrade Disabled (Mixed-Model Protection)",
                    "Timestamp": datetime.now(timezone.utc).isoformat()
                }
                results.append(auto_upgrade_result)
                
            else:
                # Option 1 (default): Configure custom versions per model
                print(f"   🔧 Configuring model-specific auto-upgrade versions...")
                print(f"   💡 This ensures each AP model gets compatible firmware automatically")
                
                # Build custom_versions dictionary starting with models from the upgrade plan
                custom_versions = {}
                models_in_upgrade_plan = set(upgrade_plan.keys())
                
                for model, plan in upgrade_plan.items():
                    model_version = plan["version"]
                    custom_versions[model] = model_version
                    print(f"      ✅ {model} → firmware {model_version} (from upgrade plan)")
                
                print(f"\n   🔍 Analyzing all available AP models for comprehensive auto-upgrade coverage...")
                
                # Get all available models from the firmware API
                all_available_models = set()
                model_version_ranges = {}
                
                if 'available_versions' in locals() and available_versions:
                    for version_info in available_versions:
                        if isinstance(version_info, dict):
                            # Try both "models" (plural) and "model" (singular) fields
                            models = version_info.get("models", [])
                            model = version_info.get("model")
                            version_num = version_info.get("version", "Unknown")
                            
                            target_models = models if models else ([model] if model else [])
                            
                            for target_model in target_models:
                                if target_model:
                                    all_available_models.add(target_model)
                                    
                                    # Track version ranges for comprehensive coverage
                                    if target_model not in model_version_ranges:
                                        model_version_ranges[target_model] = []
                                    model_version_ranges[target_model].append(version_num)
                
                # Find models that are available but not in the current upgrade plan
                models_not_in_plan = all_available_models - models_in_upgrade_plan
                
                if models_not_in_plan:
                    print(f"\n   📋 Found {len(models_not_in_plan)} additional AP models available for auto-upgrade:")
                    
                    # Group models by their available firmware versions (AP families)
                    def get_version_signature(model_versions):
                        """Create a signature of available versions for grouping"""
                        return tuple(sorted(set(model_versions)))
                    
                    model_families = {}  # signature -> list of models
                    for model in models_not_in_plan:
                        if model in model_version_ranges:
                            signature = get_version_signature(model_version_ranges[model])
                            if signature not in model_families:
                                model_families[signature] = []
                            model_families[signature].append(model)
                    
                    # Display grouped models
                    family_count = 0
                    for signature, models in model_families.items():
                        family_count += 1
                        if len(models) > 1:
                            print(f"      • AP Family {family_count}: {', '.join(sorted(models))} ({len(signature)} firmware versions)")
                        else:
                            print(f"      • {models[0]} ({len(signature)} firmware versions)")
                    
                    print(f"\n   🎯 Configure auto-upgrade for additional models:")
                    print(f"   Models with identical firmware versions are grouped together as families.")
                    print(f"   This ensures new APs of ANY model will auto-upgrade to appropriate firmware.")
                    
                    configure_additional = input(f"   Configure auto-upgrade for additional models? (Y/n): ").strip().lower()
                    
                    if configure_additional not in ['n', 'no']:
                        print(f"\n   📦 Selecting firmware versions for additional model families...")
                        print(f"   Strategy: Highest version per major revision (e.g., highest 0.12.x, highest 0.14.x)")
                        
                        # Process each family group
                        for family_idx, (signature, models) in enumerate(model_families.items(), 1):
                            if not models:  # Skip empty groups
                                continue
                                
                            # Get firmware versions for this family (all models have the same versions)
                            representative_model = models[0]
                            if representative_model not in model_version_ranges:
                                print(f"      ⚠️ No firmware versions found for model family {models}")
                                continue
                            
                            family_versions = model_version_ranges[representative_model]
                            
                            # Group versions by major revision
                            major_revisions = {}
                            for version in family_versions:
                                try:
                                    # Extract major.minor (e.g., "0.12" from "0.12.27452")
                                    parts = version.split(".")
                                    if len(parts) >= 2:
                                        major_minor = f"{parts[0]}.{parts[1]}"
                                        if major_minor not in major_revisions:
                                            major_revisions[major_minor] = []
                                        major_revisions[major_minor].append(version)
                                except:
                                    # Fallback for non-standard version formats
                                    major_minor = "other"
                                    if major_minor not in major_revisions:
                                        major_revisions[major_minor] = []
                                    major_revisions[major_minor].append(version)
                            
                            # Find highest version for each major revision
                            highest_per_major = {}
                            for major_minor, versions in major_revisions.items():
                                try:
                                    # Sort versions within this major revision
                                    sorted_versions = sorted(versions, key=lambda x: tuple(map(int, x.split("."))), reverse=True)
                                    highest_per_major[major_minor] = sorted_versions[0]
                                except:
                                    # Fallback to string sorting
                                    sorted_versions = sorted(versions, reverse=True)
                                    highest_per_major[major_minor] = sorted_versions[0]
                            
                            # Display family information
                            if len(models) > 1:
                                print(f"\n      🔧 AP Family {family_idx}: {', '.join(sorted(models))}")
                                print(f"         These models share identical firmware version compatibility")
                            else:
                                print(f"\n      🔧 Model: {models[0]}")
                                
                            print(f"         Available major revisions with highest versions:")
                            
                            # Display options for this family
                            major_options = {}
                            for idx, (major_minor, highest_version) in enumerate(sorted(highest_per_major.items()), 1):
                                print(f"            [{idx}] {major_minor}.x → {highest_version}")
                                major_options[str(idx)] = highest_version
                            
                            print(f"            [s] Skip this family")
                            
                            # Get user selection for the entire family
                            while True:
                                try:
                                    family_name = f"Family {family_idx}" if len(models) > 1 else models[0]
                                    user_choice = input(f"         Select firmware for {family_name} (1-{len(major_options)}, s): ").strip().lower()
                                    
                                    if user_choice == 's':
                                        print(f"         ⏭️ Skipping {family_name}")
                                        break
                                    elif user_choice in major_options:
                                        selected_version = major_options[user_choice]
                                        # Apply the selected version to all models in this family
                                        for model in models:
                                            custom_versions[model] = selected_version
                                        print(f"         ✅ {family_name} → firmware {selected_version}")
                                        print(f"            Applied to: {', '.join(sorted(models))}")
                                        break
                                    else:
                                        print(f"         ❌ Invalid selection. Please choose 1-{len(major_options)} or 's'.")
                                except KeyboardInterrupt:
                                    print("\n         ❌ Configuration cancelled.")
                                    break
                
                # Validate that we have comprehensive model coverage
                total_models_configured = len(custom_versions)
                models_from_plan = len(models_in_upgrade_plan)
                models_additionally_configured = total_models_configured - models_from_plan
                
                print(f"\n   ✅ Auto-upgrade coverage summary:")
                print(f"      • Models from upgrade plan: {models_from_plan}")
                print(f"      • Additional models configured: {models_additionally_configured}")
                print(f"      • Total models configured: {total_models_configured}")
                
                if total_models_configured > 0:
                    print(f"\n   📋 Complete auto-upgrade model configuration:")
                    for model, version in sorted(custom_versions.items()):
                        status = "from upgrade plan" if model in models_in_upgrade_plan else "additional coverage"
                        print(f"      • {model} → firmware {version} ({status})")
                
                # Configure auto-upgrade with comprehensive model-specific versions
                new_auto_upgrade = {
                    "enabled": True,
                    "version": "custom",  # Use "custom" to indicate custom_versions are in use
                    "custom_versions": custom_versions
                }
                
                # Time scheduling configuration for comprehensive auto-upgrade
                print(f"\n   ⏰ Auto-upgrade time scheduling:")
                print(f"   Configure when new APs should automatically upgrade their firmware.")
                
                # Get time settings (reuse existing function)
                time_settings = get_auto_upgrade_time_settings()
                new_auto_upgrade.update(time_settings)
                
                # Prepare final site settings update
                site_settings_body = {
                    "auto_upgrade": new_auto_upgrade
                }
                
                # Get and merge current settings to preserve other configurations
                try:
                    current_settings_resp = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)
                    current_settings = current_settings_resp.data if hasattr(current_settings_resp, 'data') else {}
                    if isinstance(current_settings, dict):
                        current_settings.update(site_settings_body)
                        site_settings_body = current_settings
                except Exception as e:
                    logging.warning(f"Could not retrieve current site settings for merge: {e}")
                
                # Update site settings
                settings_resp = mistapi.api.v1.sites.setting.updateSiteSettings(
                    apisession,
                    site_id,
                    body=site_settings_body
                )
                
                print(f"   ✅ Site auto-upgrade configured with model-specific versions")
                print(f"   📋 New APs will auto-upgrade to model-appropriate firmware:")
                
                # Show the configured versions
                for model, version in custom_versions.items():
                    print(f"      • New {model} APs → firmware {version}")
                
                # Show time schedule
                time_of_day = new_auto_upgrade.get("time_of_day", "02:00")
                day_of_week = new_auto_upgrade.get("day_of_week")
                if day_of_week:
                    schedule_text = f"every {day_of_week} at {time_of_day}"
                else:
                    schedule_text = f"daily at {time_of_day}"
                    
                print(f"   ⏰ Schedule: {schedule_text}")
                print(f"   🛡️ Model compatibility: Protected - each model gets appropriate firmware")
                
                logging.info(f"Site auto-upgrade configured with custom versions: {custom_versions}")
                logging.info(f"Auto-upgrade schedule: {schedule_text}")
                
                # Build version summary for results
                version_summary = ", ".join([f"{m}:{v}" for m, v in custom_versions.items()])
                
                # Add to results
                auto_upgrade_result = {
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Device ID": "SITE_CONFIG",
                    "Device Name": "Auto-Upgrade Setting",
                    "Device MAC": "N/A",
                    "Model": "Site Configuration",
                    "Current Version": "N/A",
                    "Target Version": f"Custom: {version_summary}",
                    "Strategy": upgrade_config["strategy"],
                    "P2P Enabled": upgrade_config["enable_p2p"],
                    "Max Failure %": upgrade_config["max_failure_percentage"],
                    "Force Upgrade": upgrade_config["force"],
                    "Upgrade ID": "SITE_AUTO_UPGRADE",
                    "Status": "Site Auto-Upgrade Configured (Model-Specific Versions)",
                    "Timestamp": datetime.now(timezone.utc).isoformat()
                }
                results.append(auto_upgrade_result)
                
        except Exception as e:
            print(f"   ❌ Error during auto-upgrade configuration: {e}")
            logging.error(f"Error during auto-upgrade configuration: {e}")

    # Step 11: Offer to check upgrade status
    if successful_upgrades > 0:
        print(f"\n✅ Firmware upgrade{'s' if successful_upgrades > 1 else ''} initiated successfully!")
        print(f"   � {successful_upgrades} upgrade{'s' if successful_upgrades > 1 else ''} started across {len(devices_by_site)} site{'s' if len(devices_by_site) > 1 else ''}")
        
        if upgrade_ids:
            logging.info(f"Upgrade monitoring - {len(upgrade_ids)} upgrade(s) initiated across {len(devices_by_site)} site(s)")
            
            # Store upgrade IDs to file for later retrieval by option 60
            try:
                upgrade_tracking_file = "ActiveUpgrades.json"
                upgrade_tracking_data = []
                
                # Load existing data if file exists
                if os.path.exists(upgrade_tracking_file):
                    try:
                        with open(upgrade_tracking_file, 'r', encoding='utf-8') as f:
                            upgrade_tracking_data = json.load(f)
                    except:
                        upgrade_tracking_data = []
                
                # Add new upgrade records with detailed model tracking
                timestamp = datetime.now(timezone.utc).isoformat()
                for upgrade_id in upgrade_ids:
                    # Find which site this upgrade belongs to by matching with results
                    matching_sites = []
                    upgrade_models = {}
                    total_devices_for_upgrade = 0
                    
                    # Search through results to find devices with this upgrade_id
                    for result in results:
                        result_upgrade_id = result.get("Upgrade ID")
                        if result_upgrade_id == upgrade_id or (result_upgrade_id == "Multiple" and len(upgrade_ids) == 1):
                            site_id = result["Site ID"]
                            site_name = result["Site Name"]
                            model = result["Model"]
                            target_version = result["Target Version"]
                            
                            # Track site info
                            site_key = f"{site_id}|{site_name}"
                            if site_key not in matching_sites:
                                matching_sites.append(site_key)
                            
                            # Track model/version combinations
                            if model not in upgrade_models:
                                upgrade_models[model] = {
                                    'version': target_version,
                                    'device_count': 0
                                }
                            upgrade_models[model]['device_count'] += 1
                            total_devices_for_upgrade += 1
                    
                    # Use first matching site, or fallback to first site from devices_by_site
                    if matching_sites:
                        site_parts = matching_sites[0].split("|", 1)
                        upgrade_site_id = site_parts[0]
                        upgrade_site_name = site_parts[1] if len(site_parts) > 1 else "Unknown"
                    else:
                        # Fallback to first site
                        first_site_id = next(iter(devices_by_site.keys()))
                        upgrade_site_id = first_site_id
                        upgrade_site_name = devices_by_site[first_site_id]['name']
                    
                    # Determine upgrade type for better tracking
                    upgrade_type = "mixed_model" if len(upgrade_models) > 1 else "single_model"
                    version_summary = None
                    
                    if upgrade_type == "single_model":
                        # Single model - use the version directly
                        model_name = next(iter(upgrade_models.keys()))
                        version_summary = f"{model_name} → {upgrade_models[model_name]['version']}"
                    else:
                        # Multiple models - create summary
                        model_summaries = []
                        for model, info in upgrade_models.items():
                            model_summaries.append(f"{model}:{info['version']}")
                        version_summary = ", ".join(model_summaries)
                    
                    upgrade_record = {
                        'upgrade_id': upgrade_id,
                        'site_id': upgrade_site_id,
                        'site_name': upgrade_site_name,
                        'org_id': org_id,
                        'strategy': upgrade_config['strategy'],
                        'initiated_timestamp': timestamp,
                        'total_devices': total_devices_for_upgrade or sum(len(plan["devices"]) for plan in upgrade_plan.values()),
                        'upgrade_type': upgrade_type,
                        'version_summary': version_summary,
                        'models_and_versions': {model: info['version'] for model, info in upgrade_models.items()} or {model: plan["version"] for model, plan in upgrade_plan.items()},
                        'device_counts_by_model': {model: info['device_count'] for model, info in upgrade_models.items()},
                        'p2p_enabled': upgrade_config.get('enable_p2p', False),
                        'max_failure_percentage': upgrade_config.get('max_failure_percentage', 5),
                        'status': 'initiated'
                    }
                    upgrade_tracking_data.append(upgrade_record)
                
                # Clean up old records (older than 7 days)
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
                upgrade_tracking_data = [
                    record for record in upgrade_tracking_data
                    if datetime.fromisoformat(record.get('initiated_timestamp', '1970-01-01T00:00:00+00:00')) > cutoff_time
                ]
                
                # Save updated data
                with open(upgrade_tracking_file, 'w', encoding='utf-8') as f:
                    json.dump(upgrade_tracking_data, f, indent=2, ensure_ascii=False)
                
                print(f"   💾 Upgrade tracking data saved to {upgrade_tracking_file}")
                logging.info(f"Saved {len(upgrade_ids)} upgrade IDs to tracking file {upgrade_tracking_file}")
                
            except Exception as e:
                print(f"   ⚠️ Warning: Failed to save upgrade tracking data: {e}")
                logging.warning(f"Failed to save upgrade tracking data: {e}")
        
        # Offer to check upgrade status now
        print(f"\n� Reminder: You can monitor upgrade progress using menu option 60")
        print(f"   🔍 Option 60: Check current firmware upgrade status across organization")
        
        try:
            check_now = input(f"\n❓ Would you like to check the upgrade status now? (y/n): ").strip().lower()
            if check_now in ['y', 'yes']:
                print(f"\n� Checking upgrade status...")
                check_firmware_upgrade_status()
            else:
                print(f"   ℹ️ You can check upgrade status anytime using menu option 60")
        except (EOFError, KeyboardInterrupt):
            print(f"\n   ℹ️ You can check upgrade status anytime using menu option 60")
    
    # Step 12: Write results to CSV
    try:
        results_filename = f"AdvancedAPFirmwareUpgrade_{site_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(results_filename, "w", newline='', encoding="utf-8") as f:
            if results:
                fieldnames = ["Site ID", "Site Name", "Device ID", "Device Name", "Device MAC", 
                            "Model", "Current Version", "Target Version", "Strategy", "P2P Enabled",
                            "Max Failure %", "Force Upgrade", "Upgrade ID", "Status", "Timestamp"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        print(f"\n📊 Advanced Firmware Upgrade Operation Completed!")
        print(f"   ✅ Successful upgrades initiated: {successful_upgrades} devices")
        print(f"   ❌ Failed upgrade attempts: {failed_upgrades} devices")
        print(f"   📝 Detailed results logged to: {results_filename}")
        print(f"   🎯 Strategy used: {upgrade_config['strategy'].upper()}")
        
        # Show mixed-model upgrade summary if applicable
        unique_versions_used = set()
        models_upgraded = set()
        for result in results:
            if result.get("Status") != "ERROR":
                unique_versions_used.add(result.get("Target Version", "Unknown"))
                models_upgraded.add(result.get("Model", "Unknown"))
        
        if len(unique_versions_used) > 1:
            print(f"   🔧 Mixed-Model Upgrade: {len(models_upgraded)} models, {len(unique_versions_used)} firmware versions")
            for model in sorted(models_upgraded):
                # Find the version for this model
                model_version = "Unknown"
                for result in results:
                    if result.get("Model") == model and result.get("Status") != "ERROR":
                        model_version = result.get("Target Version", "Unknown")
                        break
                model_device_count = sum(1 for r in results if r.get("Model") == model and r.get("Status") != "ERROR")
                print(f"      • {model}: {model_device_count} devices → firmware {model_version}")
            print(f"   💡 This is normal behavior when different AP models support different firmware ranges")
        else:
            single_version = list(unique_versions_used)[0] if unique_versions_used else "Unknown"
            print(f"   📦 Unified Upgrade: All {len(models_upgraded)} model(s) upgrading to firmware {single_version}")
        
        if upgrade_id:
            print(f"   🆔 Primary Upgrade ID: {upgrade_id}")
        
        print(f"\n💡 Important Notes:")
        print(f"   • Upgrades will continue in the background")
        print(f"   • Monitor device status in Mist portal or API")
        print(f"   • Strategy '{upgrade_config['strategy']}' controls rollout pace")
        if upgrade_config['enable_p2p']:
            print(f"   • P2P enabled - APs will share firmware locally")
        print(f"   • APs will reboot during upgrade process")
        print(f"   • Full upgrade process may take 5-15 minutes per device")
        if upgrade_config['strategy'] in ['canary', 'rrm']:
            print(f"   • Phased rollout will continue automatically based on strategy")
        if upgrade_config.get('start_time'):
            scheduled_time = datetime.fromtimestamp(upgrade_config['start_time']).strftime('%Y-%m-%d %H:%M')
            print(f"   • Upgrade scheduled for: {scheduled_time}")
        
        # Check if auto-upgrade was configured or disabled
        auto_upgrade_configured = any(r.get("Device ID") == "SITE_CONFIG" and "Configured" in r.get("Status", "") for r in results)
        auto_upgrade_disabled = any(r.get("Device ID") == "SITE_CONFIG" and "Disabled" in r.get("Status", "") for r in results)
        
        if auto_upgrade_configured:
            print(f"   • Site auto-upgrade configured - new APs will auto-upgrade")
        elif auto_upgrade_disabled:
            print(f"   • Site auto-upgrade disabled - new APs will NOT auto-upgrade")
        
        logging.info(f"✅ Advanced AP firmware upgrade results written to {results_filename} ({len(results)} entries)")
        logging.info(f"Advanced firmware upgrade summary: {successful_upgrades} successful, {failed_upgrades} failed, strategy: {upgrade_config['strategy']}")
        
    except Exception as e:
        logging.error(f"❌ Failed to write results to CSV: {e}")
        print(f"❌ Failed to write results to CSV: {e}")


menu_actions = {
    # ==============================
    # � READ-ONLY OPERATIONS
    # ==============================
    
    # 🗂️ Setup & Core Logs
    "1": (export_open_org_alarms_to_csv, "Export all organization alarms from the past day"),
    "2": (export_recent_device_events_to_csv, "Export all device events from the past 24 hours"),
    "3": (lambda: export_audit_logs_to_csv(full_history=False), "Export audit logs for the organization (last 24 hours)"),

    # 📚 Event & Alarm Definitions
    "4": (export_nac_event_definitions_to_csv, "Export NAC (Network Access Control) event definitions"),
    "5": (export_client_event_definitions_to_csv, "Export client event definitions"),
    "6": (export_device_event_definitions_to_csv, "Export device event definitions"),
    "7": (export_mist_edge_event_definitions_to_csv, "Export Mist Edge event definitions"),
    "8": (export_other_device_event_definitions_to_csv, "Export other device event definitions"),
    "9": (export_system_event_definitions_to_csv, "Export system event definitions"),
    "10": (export_alarm_definitions_to_csv, "Export alarm definitions with severity and field info"),

    # 🏢 Organization-Level Exports
    "11": (export_all_sites_to_csv, "Export a list of all sites in the organization"),
    "12": (export_device_inventory_to_csv, "Export the full inventory of devices in the organization"),
    "13": (export_device_stats_to_csv, "Export statistics for all devices in the organization"),
    "14": (export_device_port_stats_to_csv, "Export port-level statistics for switches and gateways"),
    "15": (export_vpn_peer_stats_to_csv, "Export VPN peer path statistics for the organization"),

    # 🌐 Gateway & Site-Wide Exports
    "16": (export_gateway_synthetic_tests_to_csv, "Export synthetic test results for all gateways"),
    "17": (export_all_devices_to_csv, "Export a list of all devices in the organization"),
    "18": (export_site_settings_to_csv, "Export configuration settings for all sites"),
    "19": (export_gateway_test_results_by_site_to_csv, "Export all synthetic test results (including speed tests) for gateways"),

    # 🗺️ Location-Enriched Exports
    "20": (export_sites_with_location_to_csv, "Export a list of sites with location and timezone info"),
    "21": (export_gateways_with_site_info_to_csv, "Export a list of gateways with associated site and address info"),
    "22": (export_devices_with_site_info_to_csv, "Export a list of all devices with associated site and address info"),
    "23": (lambda: (export_current_guest_users_to_csv(), export_historical_guest_users_to_csv()),"Export all current guest users and last 7 days of historical guests to CSV"),
    "24": (export_switch_vc_stats_to_csv, "Export all switch virtual chassis (VC/stacking) stats to CSV"),
    "25": (export_combined_inventory_with_site_info, "Export combined inventory with site and address info by calendar week"),
    "26": (export_gateway_templates_to_csv, "Export gateway templates from the organization"),
    "27": (export_all_sites_list_to_csv, "Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)"),
    "28": (lambda fast=False: export_gateways_with_wan_overrides_to_csv(fast=fast), "Find gateway ports overridden from template (outliers for compliance correction)"),
    
    # 🏢 Site-Specific Data Exports
    "29": (export_site_port_stats_to_csv, "Export port statistics for a selected site"),
    "30": (export_site_clients_to_csv, "Export client statistics for a selected site"),
    "31": (export_site_devices_to_csv, "Export device list for a selected site"),
    "32": (export_site_device_stats_to_csv, "Export device statistics for a selected site"),
    "33": (export_site_device_virtual_chassis_to_csv, "Export virtual chassis information for a selected switch device"),
    "34": (export_site_wifi_clients_to_csv, "Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV"),
    
    # 📋 Organization Template Exports
    "35": (export_organization_templates_to_csv, "Export all organization templates (gateway, network, RF, site, AP)"),
    "36": (export_org_network_templates_to_csv, "Export network template information for the organization"),
    "37": (export_org_rf_templates_to_csv, "Export RF template information for the organization"),
    "38": (export_org_ap_templates_to_csv, "Export AP template information for the organization"),
    "39": (export_org_switch_templates_to_csv, "Export switch template information for the organization"),
    
    # 📊 Organization Statistics & Analytics  
    "40": (export_org_wireless_clients_to_csv, "Export wireless client statistics for the organization"),
    "41": (export_org_wired_clients_to_csv, "Export wired client statistics for the organization"),
    
    # 🔒 Security & Monitoring
    "42": (export_org_security_events_to_csv, "Export security events for the organization"),
    "43": (export_org_rogue_clients_to_csv, "Export rogue client detections for the organization"),
    "44": (export_org_rogue_aps_to_csv, "Export rogue AP detections for the organization"),
    
    # ⚙️ Configuration & Management (Read-Only)
    "45": (export_org_licenses_to_csv, "Export license information for the organization"),
    "46": (export_org_psks_to_csv, "Export PSK (Pre-Shared Key) information for the organization"),
    "47": (export_org_webhooks_to_csv, "Export webhook configuration for the organization"),
    "48": (export_org_wlans_to_csv, "Export WLAN configuration for the organization"),
    "49": (export_site_wlans_to_csv, "Export WLAN configuration for a selected site"),
    "50": (export_site_beacons_to_csv, "Export beacon information for a selected site"),
    "51": (export_site_maps_to_csv, "Export map information for a selected site"),
    "52": (export_site_zones_to_csv, "Export zone information for a selected site"),
    "53": (export_site_insights_to_csv, "Export insights information for a selected site"),
    
    # 👥 Organization Management (Read-Only)
    "54": (export_org_api_tokens_to_csv, "Export API token information for the organization"),
    "55": (export_org_admins_to_csv, "Export administrator information for the organization"),
    "56": (export_org_msp_to_csv, "Export MSP (Managed Service Provider) information for the organization"),
    "57": (export_org_sso_to_csv, "Export SSO (Single Sign-On) information for the organization"),
    "58": (export_org_usage_to_csv, "Export license usage information for the organization"),
    "59": (export_org_mx_edges_to_csv, "Export MX Edge information for the organization"),
    
    # � Status & Monitoring
    "60": (check_firmware_upgrade_status, "Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV"),
    "61": (compare_inventory_with_csv, "Compare inventory data with external CSV file and show zip code mismatches"),
    "62": (poll_marvis_actions, "Interactive Marvis (VNA) AI troubleshooting - guided client, device, and network analysis"),
    
    # � Work In Progress Features (Read-Only)
    "63": (export_all_org_device_events_52w_to_csv, "WIP Export all org device events from the last 52 weeks"),
    "64": (lambda: export_audit_logs_to_csv(full_history=True, duration="52w"), "WIP Export ALL audit logs for the organization (last 52 weeks)"),
    "65": (export_gateway_device_configs_to_csv, "WIP Export configuration details for all gateway devices across all sites"),
    
    
    # ==============================
    # ⚠️ UNSAFE/INTERACTIVE OPERATIONS
    # ==============================
    
    # 🎛️ Site Selection & Interactive Tools
    "70": (prompt_and_log_site_selection, "Select a site (used by other functions)"),
    "71": (interactive_display_site_inventory, "View device inventory for a selected site"),
    "72": (interactive_display_device_stats, "View statistics for a selected device at a site"),
    "73": (interactive_display_device_tests, "View synthetic test stats for a selected gateway device"),
    "74": (interactive_display_device_config, "View configuration details for a selected device"),
    
    # 🔄 Continuous Operations & Monitoring
    "75": (lambda debug=False: loop_refresh_core_datasets(delay=None, debug=debug), "Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt'"),
    "76": (continuous_data_collection_loop, "Run continuous data collection loop (5 core API calls with rate limiting)"),
    
    # 🛠️ File Processing & Support Operations
    "77": (process_and_merge_csv_for_sfp_address, "Process and merge CSV files of SFP Module locations into a single CSV file"),
    "78": (generate_support_package, "Generate support package for each site"),
    
    # � CLI & WebSocket Operations
    "79": (launch_cli_shell, "Interactively execute a CLI command on a gateway or switch (exit with ~)"),
    "80": (run_arp_via_websocket, "Run ARP command on an AP and receive output via WebSocket"),

    # ⚡ DESTRUCTIVE OPERATIONS - USE WITH EXTREME CAUTION
    "90": (bulk_upgrade_ap_firmware_by_site, "🔥 DESTRUCTIVE: Advanced bulk AP firmware upgrade with multiple strategies (big_bang, canary, rrm, serial), P2P sharing, scheduling, and progress monitoring"),
    "91": (reboot_devices_by_gateway_template_list, "🔥 DESTRUCTIVE: Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results"),
    "92": (convert_virtual_chassis_to_virtual_mac, "🔥 DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive selection)(WIP)"),
    "93": (convert_virtual_chassis_by_site_list, "🔥 DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation)"),
    "94": (check_virtual_chassis_conversion_status, "Check virtual chassis to virtual MAC conversion status for all switches"),
    
    # ==============================
    # 📡 POST API OPERATIONS - Device Commands (Starting at 100)
    # ==============================
    
    # 🏓 Device Network Operations removed (options 100, 101)
}

def run_systematic_test():
    """
    Run systematic test of all safe menu options.
    
    This function cycles through all menu options that are safe for automated testing:
    - Only GET operations (no POST/PUT/DELETE)
    - No interactive functions requiring user input
    - No websocket operations
    - No reboot or destructive operations
    - No continuous loops
    
    Unsafe operations are skipped with explanatory messages.
    
    Returns:
        bool: True if all tests passed, False if any failed
    """
    start_time = time.time()
    print("🧪 Starting systematic test of MistHelper menu options...")
    print("⚠️  Note: This will skip interactive, websocket, POST, and destructive operations")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define unsafe menu options that should be skipped during testing
    unsafe_options = {
        # Site-specific operations requiring site selection
        "29": "Requires site selection",
        "30": "Requires site selection", 
        "31": "Requires site selection",
        "32": "Requires site selection",
        "33": "Requires site and device selection",
        "34": "Requires site selection",
        "49": "Requires site selection",
        "50": "Requires site selection", 
        "51": "Requires site selection",
        "52": "Requires site selection",
        "53": "Requires site selection",
        
        # WIP (Work in Progress) - may be unstable
        "63": "WIP (Work in Progress) - may be unstable", 
        "64": "WIP (Work in Progress) - may be unstable",
        "65": "WIP (Work in Progress) - may be unstable",
        
        # Interactive operations
        "70": "Interactive site selection",
        "71": "Interactive site inventory browser",
        "72": "Interactive device stats viewer", 
        "73": "Interactive device tests viewer",
        "74": "Interactive device config viewer",
        
        # Continuous operations
        "75": "Continuous loop operation",
        "76": "Continuous data collection loop",
        
        # File processing and support operations
        "77": "File processing operation - potentially resource intensive",
        "78": "Support package generation - potentially resource intensive",
        
        # CLI and WebSocket operations
        "79": "Interactive CLI shell session",
        "80": "WebSocket operation",
        "81": "Shell command execution via WebSocket",
        "82": "Shell command execution via WebSocket", 
        "83": "Shell command execution via WebSocket",
        
        # DESTRUCTIVE operations - absolutely skip
        "90": "DESTRUCTIVE: AP firmware upgrade operation",
        "91": "DESTRUCTIVE: Device reboot operation", 
        "92": "DESTRUCTIVE: Virtual chassis conversion - WIP",
        "93": "DESTRUCTIVE: Virtual chassis conversion - bulk operation"
    }
    
    # Get all available menu options
    all_options = sorted(menu_actions.keys(), key=lambda x: float(x.replace('a', '.1')))
    safe_options = [opt for opt in all_options if opt not in unsafe_options]
    
    print(f"📊 Found {len(all_options)} total menu options")
    print(f"✅ {len(safe_options)} safe options will be tested")
    print(f"⚠️  {len(unsafe_options)} unsafe options will be skipped")
    print()
    
    # Show which options will be skipped and why
    print("🚫 Skipping unsafe operations:")
    for opt in sorted(unsafe_options.keys(), key=lambda x: float(x.replace('a', '.1'))):
        if opt in menu_actions:
            _, description = menu_actions[opt]
            reason = unsafe_options[opt]
            print(f"   {opt:2}: {description[:60]}... (Reason: {reason})")
    print()
    
    # Test safe options
    print("🧪 Testing safe operations:")
    success_count = 0
    error_count = 0
    
    global org_id
    if not org_id:
        org_id = get_cached_or_prompted_org_id()
    
    for i, option in enumerate(safe_options, 1):
        func, description = menu_actions[option]
        print(f"   [{i:2}/{len(safe_options)}] Testing option {option:2}: {description[:60]}...")
        
        try:
            # Execute the function
            logging.info(f"SYSTEMATIC_TEST: Starting test of menu option {option}: {description}")
            func()
            print(f"   ✅ Option {option} completed successfully")
            success_count += 1
            logging.info(f"SYSTEMATIC_TEST: Successfully completed menu option {option}")
            
        except Exception as e:
            print(f"   ❌ Option {option} failed: {str(e)[:100]}...")
            error_count += 1
            logging.error(f"SYSTEMATIC_TEST: Failed menu option {option}: {e}")
            
        # Small delay between tests to be respectful to the API
        time.sleep(1)
    
    # Summary
    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print("🧪 Systematic Test Summary:")
    print(f"   ✅ Successful operations: {success_count}")
    print(f"   ❌ Failed operations: {error_count}")
    print(f"   🚫 Skipped unsafe operations: {len(unsafe_options)}")
    print(f"   📊 Total coverage: {success_count}/{len(all_options)} ({success_count/len(all_options)*100:.1f}%)")
    print(f"   ⏱️  Total execution time: {total_time:.2f} seconds")
    print(f"   📄 Detailed logs in: script.log")
    
    if error_count == 0:
        print("   🎉 All tested operations completed successfully!")
        logging.info(f"SYSTEMATIC_TEST: All {success_count} tested operations completed successfully in {total_time:.2f}s")
        return True
    else:
        print(f"   ⚠️  {error_count} operations failed - check logs for details")
        logging.warning(f"SYSTEMATIC_TEST: {error_count} operations failed out of {len(safe_options)} tested")
        return False

def main():
    """Main entry point for MistHelper CLI application."""
    logging.debug("ENTRY: main()")
    
    # --- CLI Argument Parsing ---
    parser = argparse.ArgumentParser(description="MistHelper CLI Interface")
    parser.add_argument("-O", "--org", help="Organization ID")
    parser.add_argument("-M", "--menu", help="Menu option number to execute")
    parser.add_argument("-S", "--site", help="Human-readable site name")
    parser.add_argument("-D", "--device", help="Human-readable device name")
    parser.add_argument("-P", "--port", help="Port ID")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (includes detailed table data in logs)")
    parser.add_argument("--delay", type=int, help="Fixed delay between loop iterations (in seconds). If omitted, delay is dynamic.")
    parser.add_argument("--fast", action="store_true", help="Enable fast mode with multithreading (bypasses rate limiting)")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check on startup for faster script initialization")
    parser.add_argument("--output-format", choices=["csv", "sqlite"], default="csv", 
                       help="Output format: 'csv' for CSV files (default) or 'sqlite' for hybrid database with natural primary keys")
    parser.add_argument("--test", action="store_true", help="Run systematic test of all safe menu options (GET operations only, no interactive/websocket/POST operations)")
    args = parser.parse_args()
    
    # Set global output format based on CLI argument
    global OUTPUT_FORMAT
    OUTPUT_FORMAT = args.output_format
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.info(f"Output format set to: {OUTPUT_FORMAT} at {timestamp}")
    
    # Enable debug logging if --debug flag is provided
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled via --debug flag")
    
    # Handle systematic testing mode
    if args.test:
        logging.info("SYSTEMATIC_TEST: Starting systematic test mode")
        print("🧪 Systematic test mode activated")
        print("📋 Dependency checks were skipped for faster testing")
        success = run_systematic_test()
        logging.info(f"SYSTEMATIC_TEST: Test mode completed with success={success}")
        sys.exit(0 if success else 1)
    
    logging.debug(f"Parsed CLI arguments: org={args.org}, menu={args.menu}, site={args.site}, device={args.device}, port={args.port}, debug={args.debug}, delay={args.delay}, fast={args.fast}, skip_deps={args.skip_deps}, output_format={args.output_format}, test={args.test}")

    global org_id
    if len(sys.argv) > 1:
        logging.info("CLI arguments detected, running in non-interactive mode.")
        if args.org:
            org_id = args.org
            logging.info(f"Using org_id from CLI argument: {org_id}")
        else:
            org_id = get_cached_or_prompted_org_id()

        site_id = None
        if args.site:
            logging.info(f"Resolving site name '{args.site}' to site_id...")
            response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_lookup = {site["name"]: site["id"] for site in sites}
            site_id = site_lookup.get(args.site)
            if not site_id:
                logging.error(f"❌ Site name '{args.site}' not found.")
                print(f"❌ Site name '{args.site}' not found.")
                sys.exit(1)
            else:
                logging.info(f"Resolved site name '{args.site}' to site_id '{site_id}'.")

        device_id = None
        if args.device and site_id:
            logging.info(f"Resolving device name '{args.device}' at site_id '{site_id}'...")
            response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id)
            devices = mistapi.get_all(response=response, mist_session=apisession)
            device_lookup = {dev["name"]: dev["id"] for dev in devices}
            device_id = device_lookup.get(args.device)
            if not device_id:
                logging.error(f"❌ Device name '{args.device}' not found at site '{args.site}'.")
                print(f"❌ Device name '{args.device}' not found at site '{args.site}'.")
                sys.exit(1)
            else:
                logging.info(f"Resolved device name '{args.device}' to device_id '{device_id}'.")

        if args.menu in menu_actions:
            func, _ = menu_actions[args.menu]
            logging.info(f"Executing menu action '{args.menu}'.")
            func_args = {
                "site_id": site_id,
                "device_id": device_id,
                "port": args.port,
                "org_id": org_id,
                "debug": args.debug,
                "delay": args.delay,
                "fast": args.fast
            }
            sig = inspect.signature(func)
            accepted_args = {k: v for k, v in func_args.items() if k in sig.parameters and v is not None}
            func(**accepted_args)
        else:
            logging.error(f"❌ Invalid menu option: {args.menu}")
            print(f"❌ Invalid menu option: {args.menu}")
            sys.exit(1)

        logging.info("CLI execution complete. Exiting.")
        logging.debug("EXIT: main() - CLI success")
        sys.exit(0)

    # --- Interactive Menu Fallback ---
    logging.info("No CLI arguments detected, running in interactive menu mode.")
    print("\nAvailable Options:")
    for key, (func, description) in menu_actions.items():
        print(f"{key}: {description}")
    iwant = input("\nEnter your selection number now: ").strip()
    selected = menu_actions.get(iwant)
    if selected:
        func, _ = selected
        logging.info(f"User selected menu option '{iwant}'. Executing associated function.")
        try:
            func()
            logging.info("Interactive menu execution complete.")
            logging.debug("EXIT: main() - interactive success")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error executing menu option '{iwant}': {e}")
            logging.debug("EXIT: main() - interactive error")
            sys.exit(1)
    else:
        logging.error(f"Invalid selection '{iwant}' entered by user.")
        print("Invalid selection. Please try again.")
        logging.debug("EXIT: main() - invalid selection")
        sys.exit(1)

if __name__ == "__main__":
    try:
        logging.info("=== MistHelper application starting ===")
        main()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user (Ctrl+C)")
        logging.debug("EXIT: __main__ - user interrupt")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logging.error(f"Unhandled exception in main application: {e}")
        logging.debug("EXIT: __main__ - unhandled exception")
        sys.exit(1)
    finally:
        logging.info("=== MistHelper application ending ===")