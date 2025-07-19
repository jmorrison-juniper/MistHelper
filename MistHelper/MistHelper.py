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
DATABASE_PATH = os.path.join("data", "mist_data.db")  # Path to SQLite database file

def check_and_generate_csv(file_name, generate_function, freshness_minutes=None):
    """
    Checks if a CSV file exists and is fresh (modified within the last `freshness_minutes`).
    If not, it runs the `generate_function` to regenerate the file.
    freshness_minutes is now settable via the .env file as CSV_FRESHNESS_MINUTES.
    """
    logging.debug(f"ENTRY: check_and_generate_csv(file_name={file_name}, generate_function={generate_function.__name__}, freshness_minutes={freshness_minutes})")
    
    if freshness_minutes is None:
        freshness_minutes = CSV_FRESHNESS_MINUTES
        
    # Check if the file already exists
    if os.path.exists(file_name):
        try:
            # Get the last modified time of the file
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_name))
            logging.debug(f"File I/O: Successfully read modification time for {file_name}: {file_mtime}")
            
            # Check if the file is still fresh
            if datetime.now() - file_mtime < timedelta(minutes=freshness_minutes):
                # Log that the cached file is being used
                logging.info(f"✅ Using cached {file_name} (fresh)")
                logging.debug(f"EXIT: check_and_generate_csv - using cached file")
                return
            else:
                # Log that the file is stale and will be regenerated
                logging.info(f"♻️ {file_name} is older than {freshness_minutes} minutes. Regenerating...")
        except OSError as e:
            logging.error(f"File I/O: Failed to read modification time for {file_name}: {e}")
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
    except Exception as e:
        logging.error(f"Failed to generate {file_name} using {generate_function.__name__}: {e}")
        logging.debug(f"EXIT: check_and_generate_csv - generation failed")
        raise

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
    if not os.path.exists('OrgDevicePortStats.csv'):
        print("⚠️ OrgDevicePortStats.csv not found. Generating it now...")
        logging.info("OrgDevicePortStats.csv not found. Generating it now...")
        export_device_port_stats_to_csv()

    if not os.path.exists('AllDevicesWithSiteInfo.csv'):
        print("⚠️ AllDevicesWithSiteInfo.csv not found. Generating it now...")
        logging.info("AllDevicesWithSiteInfo.csv not found. Generating it now...")
        export_devices_with_site_info_to_csv()

    try:
        # Load site and device info, keyed by MAC address
        logging.debug("File I/O: Reading AllDevicesWithSiteInfo.csv")
        with open('AllDevicesWithSiteInfo.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            site_info = {
                row['mac']: {
                    'site_name': row.get('site_name', ''),
                    'site_address': row.get('site_address', ''),
                    'device_name': row.get('name', '')
                } for row in reader
            }
        logging.info(f"File I/O: Successfully loaded {len(site_info)} device entries from AllDevicesWithSiteInfo.csv")

        # Merge with port stats, skipping rows with blank/null transceiver model
        merged_data = []
        logging.debug("File I/O: Reading OrgDevicePortStats.csv")
        with open('OrgDevicePortStats.csv', mode='r', encoding='utf-8') as file:
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

        # Write output to new CSV
        output_file = 'MergedTransceiverData.csv'
        logging.debug(f"File I/O: Writing merged data to {output_file}")
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = [
                'site_name', 'site_address', 'device_name', 'port_id',
                'transceiver_part_number', 'transceiver_model', 'transceiver_serial_number'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_data)

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
    """
    logging.debug(f"ENTRY: write_dict_list_to_csv(data_rows={len(data) if data else 0}, csv_file={csv_file})")
    
    if not data:
        logging.warning(f"No data provided to write to {csv_file}")
        logging.debug(f"EXIT: write_dict_list_to_csv - no data to write")
        return
        
    logging.debug(f"Preparing to write {len(data)} rows to {csv_file}...")
    data = escape_multiline_strings_for_csv(data)
    fields = get_all_unique_dict_keys(data)
    logging.debug(f"CSV fields determined: {fields}")

    try:
        logging.debug(f"File I/O: Attempting to open {csv_file} for writing")
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            logging.debug(f"File I/O: Successfully wrote CSV header to {csv_file}")
            
            for idx, row in enumerate(data):
                writer.writerow({field: row.get(field, "") for field in fields})
                if idx < 3:  # Log the first few rows for debugging
                    logging.debug(f"Row {idx} written: {row}")
                    
        logging.info(f"File I/O: Successfully wrote {len(data)} rows to {csv_file}")
        logging.debug(f"EXIT: write_dict_list_to_csv - success")
        
    except PermissionError as e:
        logging.error(f"File I/O: Permission denied when writing to {csv_file}: {e}")
        print(f"❌ Cannot write to {csv_file}. Is it open in another program?")
        logging.debug(f"EXIT: write_dict_list_to_csv - permission error")
        raise
    except OSError as e:
        logging.error(f"File I/O: OS error when writing to {csv_file}: {e}")
        logging.debug(f"EXIT: write_dict_list_to_csv - OS error")
        raise
    except Exception as e:
        logging.error(f"File I/O: Unexpected error when writing to {csv_file}: {e}")
        logging.debug(f"EXIT: write_dict_list_to_csv - unexpected error")
        raise


def write_dict_list_to_sqlite_database_inside_container(data, table_name):
    """
    Writes a list of dictionaries to a SQLite database table inside the container.
    Follows NASA/JPL coding standards with comprehensive logging and error handling.
    
    Args:
        data (list): List of dictionaries containing the data to write
        table_name (str): Name of the database table to write to
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Entry logging with input validation
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.debug(f"ENTRY: write_dict_list_to_sqlite_database_inside_container(data_rows={len(data) if data else 0}, table_name={table_name}) at {timestamp}")
    
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
        
    # Sanitize table name to prevent SQL injection (following safety-critical standards)
    import re
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
    if not table_name or table_name[0].isdigit():
        table_name = f"table_{table_name}"
        
    logging.debug(f"Processing {len(data)} rows for table {table_name} at {timestamp}")
    
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
    
    # Process data to handle CSV-specific formatting (escape multiline strings)
    try:
        processed_data = escape_multiline_strings_for_csv(data)
        logging.debug(f"Successfully processed data for SQLite compatibility at {timestamp}")
    except Exception as e:
        logging.error(f"Failed to process data: {e} at {timestamp}")
        logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - data processing failed")
        return False
    
    # Get all unique fields for table schema
    try:
        fields = get_all_unique_dict_keys(processed_data)
        if not fields:
            logging.error(f"No fields found in data for table {table_name} at {timestamp}")
            logging.debug(f"EXIT: write_dict_list_to_sqlite_database_inside_container - no fields")
            return False
        logging.debug(f"Database fields determined: {fields} at {timestamp}")
    except Exception as e:
        logging.error(f"Failed to determine fields: {e} at {timestamp}")
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
        
        # Create table with all fields as TEXT (following safety-critical principle: simple, predictable)
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT"
        for field in fields:
            # Rename fields that conflict with our built-in columns to preserve data
            if field.lower() == 'id':
                safe_field = 'api_id'  # Preserve API ID as 'api_id'
                logging.debug(f"Renaming field '{field}' to 'api_id' to preserve data while avoiding conflict")
            elif field.lower() == 'timestamp':
                safe_field = 'api_timestamp'  # Preserve API timestamp as 'api_timestamp'
                logging.debug(f"Renaming field '{field}' to 'api_timestamp' to preserve data while avoiding conflict")
            else:
                # Sanitize field names for SQL safety
                safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
            create_table_sql += f", {safe_field} TEXT"
        create_table_sql += ")"
        
        cursor.execute(create_table_sql)
        logging.debug(f"Table {table_name} created/verified at {timestamp}")
        
        # Clear existing data in table (replace mode for consistency with CSV behavior)
        cursor.execute(f"DELETE FROM {table_name}")
        logging.debug(f"Cleared existing data from table {table_name} at {timestamp}")
        
        # Insert data rows
        insert_timestamp = datetime.now(timezone.utc).isoformat()
        for idx, row in enumerate(processed_data):
            try:
                # Prepare values for insertion
                values = [insert_timestamp]  # Add timestamp as first column
                field_values = []
                safe_fields = ["timestamp"]
                
                for field in fields:
                    # Rename fields that conflict with our built-in columns to preserve data
                    if field.lower() == 'id':
                        safe_field = 'api_id'  # Preserve API ID as 'api_id'
                    elif field.lower() == 'timestamp':
                        safe_field = 'api_timestamp'  # Preserve API timestamp as 'api_timestamp'
                    else:
                        safe_field = re.sub(r'[^a-zA-Z0-9_]', '_', str(field))
                    
                    value = row.get(field, "")
                    # Convert value to string for TEXT storage
                    if value is None:
                        value = ""
                    else:
                        value = str(value)
                    values.append(value)
                    safe_fields.append(safe_field)
                
                # Create parameterized query for safety
                placeholders = ", ".join(["?"] * len(values))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(safe_fields)}) VALUES ({placeholders})"
                
                cursor.execute(insert_sql, values)
                
                # Log first few rows for debugging
                if idx < 3:
                    logging.debug(f"Row {idx} inserted into {table_name} at {timestamp}")
                    
            except Exception as e:
                logging.error(f"Failed to insert row {idx} into {table_name}: {e} at {timestamp}")
                # Continue with other rows rather than failing completely
                continue
        
        # Commit transaction
        connection.commit()
        logging.info(f"Successfully wrote {len(processed_data)} rows to table {table_name} in database {DATABASE_PATH} at {timestamp}")
        
        # Verify data was written
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
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


def write_data_with_format_selection(data, filename_or_table, format_override=None):
    """
    Writes data to either CSV or SQLite database based on global OUTPUT_FORMAT or override.
    Follows NASA/JPL coding standards with comprehensive logging.
    
    Args:
        data (list): List of dictionaries containing the data to write
        filename_or_table (str): CSV filename or database table name
        format_override (str): Optional override for output format ("csv" or "sqlite")
    
    Returns:
        bool: True if successful, False otherwise
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.debug(f"ENTRY: write_data_with_format_selection(data_rows={len(data) if data else 0}, filename_or_table={filename_or_table}, format_override={format_override}) at {timestamp}")
    
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
            
            logging.info(f"Writing {len(data)} rows to SQLite table: {table_name} at {timestamp}")
            result = write_dict_list_to_sqlite_database_inside_container(data, table_name)
            logging.debug(f"EXIT: write_data_with_format_selection - SQLite {'success' if result else 'failed'}")
            return result
            
    except Exception as e:
        logging.error(f"Failed to write data to {filename_or_table} in {output_format} format: {e} at {timestamp}")
        logging.debug(f"EXIT: write_data_with_format_selection - exception")
        return False


def save_data_to_output(data, filename):
    """
    Wrapper function to replace write_dict_list_to_csv calls.
    Routes to appropriate output format based on global OUTPUT_FORMAT setting.
    
    Args:
        data (list): List of dictionaries containing the data to write
        filename (str): CSV filename or database table name
    """
    return write_data_with_format_selection(data, filename)

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
                    save_data_to_output(rawdata, filename)
                    logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows).")
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

        # Write processed data to CSV
        save_data_to_output(data, filename)
        logging.info(f"Data written to {filename} ({len(data)} rows).")

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
            save_data_to_output(rawdata, filename)
            logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows).")
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

    # Load the site list from CSV
    with open(csv_file, mode='r', encoding='utf-8') as file:
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
            api_call=mistapi.api.v1.orgs.aptemplates.listOrgApTemplates,
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
        with open("SiteList.csv", mode="r", encoding="utf-8") as f:
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
        with open("SiteList.csv", mode="r", encoding="utf-8") as f:
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
        with open("SiteList.csv", mode="r", encoding="utf-8") as f:
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
            response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="gateway")
            devices = mistapi.get_all(response=response, mist_session=apisession)
            logging.info(f"[INFO] Found {len(devices)} gateway devices at site {site_id}.")
            for device in tqdm(devices, desc=f"Site {site_id}", unit="device", leave=False):
                device_id = device.get("id")
                device_name = device.get("name", "")
                try:
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
    if os.path.exists('AllGatewayTestResults.csv'):
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
    with open(filename, mode='r', encoding='utf-8') as file:
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
    Polls Marvis actions for the organization, filters for open actions, and writes them to a CSV.
    Adds logging and comments for traceability.
    """
    logging.info("🔍 Polling Marvis Actions...")
    print("🔍 Polling Marvis Actions...")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id} for Marvis actions polling.")

    # Call the Mist API to get Marvis actions
    response = mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(apisession, org_id)
    rawdata = mistapi.get_all(response=response, mist_session=apisession)
    logging.info(f"Fetched {len(rawdata)} Marvis actions from API.")

    # Filter only open actions (state == "open")
    open_actions = [action for action in rawdata if action.get("state") == "open"]
    logging.info(f"Filtered {len(open_actions)} open Marvis actions.")

    # Flatten and clean the data for CSV compatibility
    data = flatten_nested_fields_in_list(open_actions)
    data = escape_multiline_strings_for_csv(data)
    logging.debug("Flattened and sanitized open Marvis actions for CSV.")

    # Write to CSV
    save_data_to_output(data, "OpenMarvisActions.csv")
    logging.info(f"✅ {len(open_actions)} open Marvis actions written to OpenMarvisActions.csv")
    print(f"✅ {len(open_actions)} open Marvis actions written to OpenMarvisActions.csv")

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
    with open("OrgInventory.csv", mode="r", encoding="utf-8") as file:
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
        device_id = prompt_select_device_id_from_inventory(site_id, device_type=device_type)
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

def run_shell_command_and_log(command, log_filename, csv_output=None, description="Running shell command"):
    logging.info(f"Launching shell to run: {description}")
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
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write("".join(output_lines))
        print(f"✅ Output saved to {log_filename}")

        if csv_output:
            extract_json_from_ws_log_to_csv(log_file=log_filename, output_csv=csv_output)

    except Exception as e:
        print(f"❌ Error during shell session: {e}")

def extract_json_from_ws_log_to_csv(log_file, output_csv):
    """
    Cleans a WebSocket log file, extracts the first valid JSON object,
    and writes it to a CSV file.
    """
    import re
    import json

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove null characters and non-printable characters
        cleaned = ''.join(c for c in content if c.isprintable())

        # Remove known shell prompts and noise
        cleaned = re.sub(r"{master:.*?}\s*", "", cleaned)
        cleaned = re.sub(r"mist@\S+>\s*", "", cleaned)

        # Try to extract the first valid JSON object
        json_candidates = re.findall(r"{.*}", cleaned, re.DOTALL)
        json_data = None

        for candidate in json_candidates:
            try:
                json_data = json.loads(candidate)
                break  # Stop at the first valid JSON
            except json.JSONDecodeError:
                continue

        if not json_data:
            print("⚠️ No valid JSON block found in log.")
            return

        # Flatten and write to CSV
        flattened = flatten_nested_fields_in_list([json_data])
        save_data_to_output(flattened, output_csv)
        print(f"✅ Extracted JSON written to {output_csv}")

    except Exception as e:
        print(f"❌ Failed to clean {log_file}: {e}")

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
        with open("FilteredGatewayPortConfigs.csv", "w", newline="", encoding="utf-8") as f:
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
        with open("SiteList.csv", mode="r", encoding="utf-8") as f:
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
    with open("AllDevicesWithSiteInfo.csv", mode="r", encoding="utf-8") as f:
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
    with open("AllSiteGatewayConfigs.csv", encoding="utf-8") as f:
        configs = list(csv.DictReader(f))
    with open("SiteList_ListAPI.csv", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))
    with open("OrgGatewayTemplates.csv", encoding="utf-8") as f:
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
        # Still create empty CSV file
        output_file = "GatewayOverriddenPorts.csv"
        fieldnames = [
            "gateway_device_name", "site_name", "template_name", "port_name", "port_description",
            "port_status", "port_admin_status", "port_gateway_ip", "port_ip_address", "port_netmask",
            "port_config_type", "port_usage", "overridden_from_template",
            "device_id", "site_id", "template_id"
        ]
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
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
    fieldnames = [
        "gateway_device_name",
        "site_name", 
        "template_name",
        "port_name",
        "port_description",
        "port_status",
        "port_admin_status", 
        "port_gateway_ip",
        "port_ip_address",
        "port_netmask",
        "port_config_type",
        "port_usage",
        "overridden_from_template",
        "device_id",
        "site_id",
        "template_id"
    ]
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(overridden_port_info)

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
    Presents a list of switches that are virtual chassis, lets the user select one,
    and calls the Mist API to convert the device to a virtual MAC.
    """
    # Ensure OrgInventory.csv is fresh
    check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)

    # Load OrgInventory.csv and filter for switches with a non-empty id 
    with open("OrgInventory.csv", mode="r", encoding="utf-8") as file:
        reader = list(csv.DictReader(file))
        switches = [
            row for row in reader
            if row.get("type") == "switch" and row.get("id", "").strip()
        ]

    if not switches:
        print("No virtual chassis switches found in OrgInventory.csv.")
        logging.warning("No virtual chassis switches found in OrgInventory.csv.")
        return

    # Display indexed list to user
    print("\nAvailable Virtual Chassis Switches:")
    index_to_device = {}
    name_to_device = {}
    for idx, sw in enumerate(switches):
        print(f"[{idx}] {sw.get('name', ''):20} MAC: {sw.get('mac', ''):17} Model: {sw.get('model', ''):10} Serial: {sw.get('serial', ''):15} ID: {sw.get('id', '')}")
        index_to_device[idx] = sw
        name_to_device[sw.get("name", "")] = sw

    user_input = input("\nEnter the index or switch name to convert to virtual MAC: ").strip()

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

    site_id = selected.get("site_id")
    device_id = selected.get("id")
    if not site_id or not device_id:
        print("❌ Missing site_id or device_id for selected switch.")
        logging.warning("Missing site_id or device_id for selected switch.")
        return

    print(f"Converting switch '{selected.get('name', '')}' (device_id: {device_id}) at site_id: {site_id} to virtual MAC...")
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
            print("✅ Conversion to virtual MAC triggered.")
            logging.info(f"Conversion to virtual MAC triggered for device {device_id} at site {site_id}. Response: {getattr(resp, 'data', '')}")
    except Exception as e:
        print(f"❌ Failed to convert to virtual MAC: {e}")
        logging.error(f"Failed to convert to virtual MAC: {e}")

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
        with open("SiteList.csv", mode="r", encoding="utf-8") as f:
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
            with open("SiteWiFiClients.CSV", "w", newline="", encoding="utf-8") as f:
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
    if not os.path.exists("GatewayTemplateRebootList.CSV"):
        logging.error("❌ GatewayTemplateRebootList.CSV not found.")
        print("❌ GatewayTemplateRebootList.CSV not found. Please create this file with template names to reboot.")
        return

    # Step 2: Ensure required CSVs are fresh
    check_and_generate_csv("OrgDevices.csv", export_all_devices_to_csv)
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    check_and_generate_csv("OrgGatewayTemplates.csv", export_gateway_templates_to_csv)
    check_and_generate_csv("AllSiteGatewayConfigs.csv", lambda: export_gateway_device_configs_to_csv(fast=True))

    # Step 3: Load template name to ID mapping from OrgGatewayTemplates.csv
    template_name_to_id = {}
    try:
        with open("OrgGatewayTemplates.csv", encoding="utf-8") as f:
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
        with open("GatewayTemplateRebootList.CSV", encoding="utf-8") as f:
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
        with open("SiteList.csv", encoding="utf-8") as f:
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
        with open("AllSiteGatewayConfigs.csv", encoding="utf-8") as f:
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
            with open("AllSiteGatewayConfigs.csv", encoding="utf-8") as f:
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
    print(f"Found {len(reboot_targets)} gateway devices to reboot:")
    for target in reboot_targets:
        print(f"  - {target['device_name']} (ID: {target['device_id']})")

    # Step 8: Reboot each device and log results
    results = []
    for device in reboot_targets:
        status = ""
        try:
            logging.info(f"Rebooting device '{device['device_name']}' (ID: {device['device_id']})")
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
            logging.info(f"✅ Reboot command sent for '{device['device_name']}': {status}")
        except Exception as e:
            status = f"ERROR: {e}"
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

    # Step 9: Write results to CSV
    try:
        with open("GatewayTemplateRebootResults.CSV", "w", newline='', encoding="utf-8") as f:
            fieldnames = ["Template ID", "Template Name", "Device ID", "Device Name", "Site ID", "Site Name", "Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logging.info(f"✅ Reboot results written to GatewayTemplateRebootResults.CSV ({len(results)} entries)")
        print(f"✅ Reboot results written to GatewayTemplateRebootResults.CSV ({len(results)} entries)")
    except Exception as e:
        logging.error(f"❌ Failed to write results to CSV: {e}")
        print(f"❌ Failed to write results to CSV: {e}")

menu_actions = {
    # 🗂️ Setup & Core Logs
    "0": (prompt_and_log_site_selection, "Select a site (used by other functions)"),
    "1": (export_open_org_alarms_to_csv, "Export all organization alarms from the past day"),
    "2": (export_recent_device_events_to_csv, "Export all device events from the past 24 hours"),
    "2a": (export_all_org_device_events_52w_to_csv, "WIP Export all org device events from the last 52 weeks"),
    "3": (lambda: export_audit_logs_to_csv(full_history=False), "Export audit logs for the organization (last 24 hours)"),
    "3a": (lambda: export_audit_logs_to_csv(full_history=True, duration="52w"), "WIP Export ALL audit logs for the organization (last 52 weeks)"),

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

    # 🧭 Interactive Site/Device Exploration
    "16": (interactive_display_site_inventory, "View device inventory for a selected site"),
    "17": (interactive_display_device_stats, "View statistics for a selected device at a site"),
    "18": (interactive_display_device_tests, "View synthetic test stats for a selected gateway device"),
    "19": (interactive_display_device_config, "View configuration details for a selected device"),

    # 🌐 Gateway & Site-Wide Exports
    "20": (export_gateway_synthetic_tests_to_csv, "Export synthetic test results for all gateways"),
    "21": (export_all_devices_to_csv, "Export a list of all devices in the organization"),
    "22": (export_site_settings_to_csv, "Export configuration settings for all sites"),
    "23": (export_gateway_device_configs_to_csv, "WIP Export configuration details for all gateway devices across all sites"),
    "24": (export_gateway_test_results_by_site_to_csv, "Export all synthetic test results (including speed tests) for gateways"),

    # 🗺️ Location-Enriched Exports
    "25": (export_sites_with_location_to_csv, "Export a list of sites with location and timezone info"),
    "26": (export_gateways_with_site_info_to_csv, "Export a list of gateways with associated site and address info"),
    "27": (export_devices_with_site_info_to_csv, "Export a list of all devices with associated site and address info"),
    "28": (process_and_merge_csv_for_sfp_address, "Process and merge CSV files of SFP Module locations into a single CSV file"),
    "29": (generate_support_package, "Generate support package for each site"),
    "30": (poll_marvis_actions, "Poll Marvis actions and export open actions to CSV"),
    "31": (lambda: (export_current_guest_users_to_csv(), export_historical_guest_users_to_csv()),"Export all current guest users and last 7 days of historical guests to CSV"),
    "32": (export_switch_vc_stats_to_csv, "Export all switch virtual chassis (VC/stacking) stats to CSV"),
    "33": (launch_cli_shell, "Interactively execute a CLI command on a gateway or switch (exit with ~)"),
    "34": (run_arp_via_websocket, "Run ARP command on an AP and receive output via WebSocket"),
    "35": (lambda debug=False: loop_refresh_core_datasets(delay=None, debug=debug), "Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt'"),
    "38": (lambda: run_shell_command_and_log(command="show route 0.0.0.0 | display json | no-more\nDONE!",log_filename="ws_def_route.log",csv_output="RouteDefault.csv",description="Show default route"), "Run 'show route 0.0.0.0' on a selected device via shell session"),
    "39": (lambda: run_shell_command_and_log(command="show dhcp-security binding | display json | no-more\nDONE!",log_filename="ws_dhcp.log",csv_output="DhcpSecurityBindings.csv",description="Show DHCP security bindings"), "Run 'show dhcp-security binding' on a selected device via shell session"),
    "40": (lambda: run_shell_command_and_log(command="show vlans | display json | no-more\nDONE! ",log_filename="ws_vlans.log",csv_output="Vlans.csv",description="Show VLANs"), "Run 'show vlans' on a selected device via shell session"),
    "41": (export_combined_inventory_with_site_info, "Export combined inventory with site and address info by calendar week"),
    "42": (export_gateway_templates_to_csv, "Export gateway templates from the organization"),
    "43": (export_all_sites_list_to_csv, "Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)"),
    "44": (lambda fast=False: export_gateways_with_wan_overrides_to_csv(fast=fast), "Find gateway ports overridden from template (outliers for compliance correction)"),
    "45": (convert_virtual_chassis_to_virtual_mac, "Convert a virtual chassis switch to virtual MAC (interactive selection)(WIP)"),
    "46": (reboot_devices_by_gateway_template_list, "Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results"),
    "47": (export_site_wifi_clients_to_csv, "Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV"),
    
    # 🏢 Site-Specific Data Exports
    "48": (export_site_port_stats_to_csv, "Export port statistics for a selected site"),
    "49": (export_site_clients_to_csv, "Export client statistics for a selected site"),
    "50": (export_site_devices_to_csv, "Export device list for a selected site"),
    "51": (export_site_device_stats_to_csv, "Export device statistics for a selected site"),
    "52": (export_site_device_virtual_chassis_to_csv, "Export virtual chassis information for a selected switch device"),
    
    # 📋 Organization Template Exports
    "53": (export_organization_templates_to_csv, "Export all organization templates (gateway, network, RF, site, AP)"),
    
    # 📊 Organization Statistics & Analytics  
    "54": (export_org_wireless_clients_to_csv, "Export wireless client statistics for the organization"),
    "55": (export_org_wired_clients_to_csv, "Export wired client statistics for the organization"),
    
    # 🔒 Security & Monitoring
    "56": (export_org_security_events_to_csv, "Export security events for the organization"),
    "57": (export_org_rogue_clients_to_csv, "Export rogue client detections for the organization"),
    "58": (export_org_rogue_aps_to_csv, "Export rogue AP detections for the organization"),
    
    # ⚙️ Configuration & Management
    "59": (export_org_licenses_to_csv, "Export license information for the organization"),
    "60": (export_org_psks_to_csv, "Export PSK (Pre-Shared Key) information for the organization"),
    "61": (export_org_webhooks_to_csv, "Export webhook configuration for the organization"),
    "62": (export_org_wlans_to_csv, "Export WLAN configuration for the organization"),
    "63": (export_site_wlans_to_csv, "Export WLAN configuration for a selected site"),
    "64": (export_site_beacons_to_csv, "Export beacon information for a selected site"),
    "65": (export_site_maps_to_csv, "Export map information for a selected site"),
    "66": (export_site_zones_to_csv, "Export zone information for a selected site"),
    "67": (export_site_insights_to_csv, "Export insights information for a selected site"),
    
    # 👥 Organization Management
    "68": (export_org_api_tokens_to_csv, "Export API token information for the organization"),
    "69": (export_org_admins_to_csv, "Export administrator information for the organization"),
    "70": (export_org_msp_to_csv, "Export MSP (Managed Service Provider) information for the organization"),
    "71": (export_org_sso_to_csv, "Export SSO (Single Sign-On) information for the organization"),
    "72": (export_org_usage_to_csv, "Export license usage information for the organization"),
    "73": (export_org_mx_edges_to_csv, "Export MX Edge information for the organization"),
    
    # 🔄 Continuous Data Collection
    "74": (continuous_data_collection_loop, "Run continuous data collection loop (5 core API calls with rate limiting)"),
    
    # 📋 Additional Template Exports
    "75": (export_org_network_templates_to_csv, "Export network template information for the organization"),
    "76": (export_org_rf_templates_to_csv, "Export RF template information for the organization"),
    "77": (export_org_ap_templates_to_csv, "Export AP template information for the organization"),
    "78": (export_org_switch_templates_to_csv, "Export switch template information for the organization")
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
        "0": "Interactive site selection",
        "2a": "WIP (Work in Progress) - may be unstable", 
        "3a": "WIP (Work in Progress) - may be unstable",
        "16": "Interactive site inventory browser",
        "17": "Interactive device stats viewer", 
        "18": "Interactive device tests viewer",
        "19": "Interactive device config viewer",
        "23": "WIP (Work in Progress) - may be unstable",
        "29": "Support package generation - potentially resource intensive",
        "30": "Marvis polling - continuous operation",
        "31": "Contains lambda with multiple functions",
        "33": "Interactive CLI shell session",
        "34": "WebSocket operation",
        "35": "Continuous loop operation",
        "38": "Shell command execution via WebSocket",
        "39": "Shell command execution via WebSocket", 
        "40": "Shell command execution via WebSocket",
        "44": "WIP (Work in Progress) - may be unstable",
        "45": "Interactive virtual chassis conversion - WIP",
        "46": "Device reboot operation - destructive",
        "47": "Requires site selection",
        "48": "Requires site selection",
        "49": "Requires site selection", 
        "50": "Requires site selection",
        "51": "Requires site selection",
        "52": "Requires site and device selection",
        "63": "Requires site selection",
        "64": "Requires site selection", 
        "65": "Requires site selection",
        "66": "Requires site selection",
        "67": "Requires site selection",
        "68": "Requires site selection",
        "69": "Requires site selection",
        "70": "Requires site selection",
        "78": "Continuous data collection loop"
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
                       help="Output format: 'csv' for CSV files (default) or 'sqlite' for embedded database")
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