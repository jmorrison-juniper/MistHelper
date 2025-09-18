#!/usr/bin/env python3
"""
MistHelper - Comprehensive Juniper Mist API Data Export Tool
A powerful utility for extracting and analyzing data from Juniper Mist cloud environments.
"""

# ============================================================================
# GLOBAL DEPENDENCY MANAGEMENT AND IMPORT SYSTEM
# ============================================================================
import sys
import time
import socket
import argparse
import getpass
import logging
import logging.handlers
import os
import re
import ipaddress
import multiprocessing
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from threading import Lock
from typing import Tuple, Optional
import paramiko
from paramiko import SSHClient, AutoAddPolicy
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import time

# Standard library imports for static analysis
import csv
import json
import sqlite3
import datetime
from datetime import timezone, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import ast
import math
import shutil
import glob
import traceback
import argparse
import re
import difflib
import unicodedata
from collections import defaultdict
import inspect

# Third-party imports for static analysis (with fallbacks)
try:
    from prettytable import PrettyTable
except ImportError:
    PrettyTable = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import websocket
except ImportError:
    websocket = None

try:
    from difflib import SequenceMatcher
except ImportError:
    SequenceMatcher = None

# Import mistapi later through GlobalImportManager for better dependency management
mistapi = None

# tqdm will be properly imported by GlobalImportManager
# This fallback will be overridden by the real tqdm import
def tqdm(iterable, *args, **kwargs):
    """Fallback tqdm function - will be replaced by real tqdm after import initialization."""
    return iterable

try:
    import requests
except ImportError:
    requests = None

try:
    import urllib3
except ImportError:
    urllib3 = None

try:
    import pyte
except ImportError:
    pyte = None

# Optional imports with fallbacks
try:
    from scourgify import normalize_address_record
except ImportError:
    normalize_address_record = None

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

# Keyboard listener functionality has been removed for simplicity
listen_keyboard = None
stop_listening = None

def listen_keyboard(*args, **kwargs):
    """Keyboard listener has been removed - this is a no-op fallback."""
    logging.info("Keyboard listener functionality has been removed")
    return None
    def stop_listening():
        pass

# ============================================================================
# CENTRALIZED PAGINATION DEFAULTS
# ============================================================================
# Several legacy code paths relied on the mistapi client's implicit default page
# size (commonly 100). That caused excessive paging (e.g., 10x HTTP calls for
# 1000-item datasets). We unify a single configurable default via environment
# variable MIST_PAGE_LIMIT (clamped to 1..1000). All new/updated listOrgSites /
# getOrgInventory calls should pass limit=DEFAULT_API_PAGE_LIMIT or use the
# helper wrappers below to ensure consistency and simpler tuning.
try:
    _raw_page_limit_env = os.environ.get("MIST_PAGE_LIMIT", "1000").strip()
    _parsed_limit = int(_raw_page_limit_env)
except Exception:
    _parsed_limit = 1000

DEFAULT_API_PAGE_LIMIT = max(1, min(_parsed_limit, 1000))
if _parsed_limit != DEFAULT_API_PAGE_LIMIT:
    logging.warning(
        f"MIST_PAGE_LIMIT value {_parsed_limit} adjusted to {DEFAULT_API_PAGE_LIMIT} (valid range 1..1000)"
    )

logging.info(f"API Page Size Configuration Active: DEFAULT_API_PAGE_LIMIT={DEFAULT_API_PAGE_LIMIT}")

def fetch_all_sites_with_limit(org_id):
    """Fetch all sites with unified pagination.

    SECURITY: Read-only; no sensitive data logged.
    """
    resp = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)
    return mistapi.get_all(response=resp, mist_session=apisession)

def fetch_all_inventory_with_limit(org_id):
    """Fetch full org inventory with unified pagination.

    SECURITY: Read-only; no secrets in inventory object fields.
    """
    resp = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)
    return mistapi.get_all(response=resp, mist_session=apisession)

# Early dotenv import for configuration loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
    load_dotenv()
except ImportError:
    DOTENV_AVAILABLE = False
    # Manual .env loading fallback when python-dotenv is not available
    def load_dotenv():
        """Fallback .env loader when python-dotenv package is not installed."""
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except FileNotFoundError:
            logging.debug("No .env file found")
        except Exception as e:
            logging.debug(f"Error loading .env file: {e}")
    load_dotenv()

class GlobalImportManager:
    """
    Centralized import and dependency management system for MistHelper.
    
    This class handles:
    - UV-based package installation and upgrades
    - Centralized import management
    - Dependency verification and auto-installation
    - Graceful handling of optional dependencies
    - Performance optimization through early imports
    """
    
    def __init__(self):
        """Initialize the import manager with configuration from environment variables."""
        # Configuration from .env file
        # For local development: UV enabled, auto-upgrades enabled
        # For containers: These are overridden by environment variables
        self.auto_upgrade_uv = os.getenv("AUTO_UPGRADE_UV", "true").lower() == "true"  # Default to true for local UV usage
        self.auto_upgrade_dependencies = os.getenv("AUTO_UPGRADE_DEPENDENCIES", "true").lower() == "true"  # Default to true for local development
        self.upgrade_check_timeout = int(os.getenv("UPGRADE_CHECK_TIMEOUT", "30"))  # Shorter timeout
        self.csv_freshness_minutes = int(os.getenv("CSV_FRESHNESS_MINUTES", "15"))
        # Only check for UV updates once per day by default
        self.uv_update_check_hours = int(os.getenv("UV_UPDATE_CHECK_HOURS", "24"))
        # Option to completely disable UV checking (useful for containers)
        self.disable_uv_check = os.getenv("DISABLE_UV_CHECK", "false").lower() == "true"
        # Option to completely disable auto-installation (useful for containers)
        self.disable_auto_install = os.getenv("DISABLE_AUTO_INSTALL", "false").lower() == "true"
        
        # Dependency tracking
        self.required_packages = {}
        self.optional_packages = {}
        self.failed_imports = []
        self.installed_packages = []
        
        # Import storage for global access
        self.imports = {}
        
        # UV availability cache to avoid repeated checks
        self._uv_available = None
        self._uv_checked = False
        self._last_uv_update_check = None  # Track when we last checked for UV updates
        
        # Import name mappings for cases where package name != import name
        self.import_name_mappings = {
            'websocket-client': 'websocket',      # websocket-client package provides websocket module
            'python-dotenv': 'dotenv',            # python-dotenv package provides dotenv module
            'usaddress-scourgify': 'scourgify',   # usaddress-scourgify package provides scourgify module
            'pillow': 'PIL',                      # Pillow package provides PIL module
            'beautifulsoup4': 'bs4',              # beautifulsoup4 package provides bs4 module
            'pyyaml': 'yaml',                     # PyYAML package provides yaml module
            'python-dateutil': 'dateutil',       # python-dateutil package provides dateutil module
            'msgpack-python': 'msgpack',          # msgpack-python package provides msgpack module
        }
        
        # Special import handlers for complex cases
        self.special_import_handlers = {
            'concurrent.futures': self._import_concurrent_futures,
            'datetime': self._import_datetime,
            'tqdm': self._import_tqdm,
        }
        
        # Initialize logging early
        self._setup_logging()
        
        # Detect virtual environment for better package management
        self._detect_virtual_environment()
        
        # Define all required and optional packages
        self._define_package_requirements()
        
    def _detect_virtual_environment(self):
        """Detect if we're running in a virtual environment and log info."""
        self.in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if self.in_venv:
            venv_path = getattr(sys, 'prefix', 'unknown')
            logging.info(f"Running in virtual environment: {venv_path}")
            logging.info(f"Python executable: {sys.executable}")
        else:
            logging.info("Running in system Python environment")
            logging.info(f"Python executable: {sys.executable}")
        
    def _setup_logging(self):
        """Setup basic logging configuration with environment-specific levels."""
        # Get console and file log levels from environment (default to INFO if not set)
        console_log_level = int(os.environ.get('CONSOLE_LOG_LEVEL', logging.INFO))
        file_log_level = int(os.environ.get('LOGGING_LOG_LEVEL', logging.INFO))
        
        # Create console handler with environment-specified level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_log_level)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Create file handler with environment-specified level
        file_handler = logging.FileHandler('script.log')
        file_handler.setLevel(file_log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Configure root logger to capture all messages, handlers will filter
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[file_handler, console_handler],
            force=True  # Override any existing configuration
        )
        
    def _define_package_requirements(self):
        """Define all required and optional package dependencies."""
        # Required packages (core functionality)
        self.required_packages = {
            # Core API and networking
            'mistapi': 'mistapi>=0.3.0',
            'requests': 'requests>=2.28.0',
            'websocket-client': 'websocket-client>=1.4.0',
            
            # CLI and user interface
            'prettytable': 'prettytable>=3.5.0',
            'tqdm': 'tqdm>=4.64.0',
            
            # Data processing
            'numpy': 'numpy>=1.24.0',
            'python-dotenv': 'python-dotenv>=1.0.0',
            
            # SSH and direct device connections  
            'paramiko': 'paramiko>=2.9.0',  # More compatible version for SSH
            
            # Standard library modules (no installation needed)
            'argparse': None,  # Built-in
            'csv': None,       # Built-in
            'json': None,      # Built-in
            'sqlite3': None,   # Built-in
            'time': None,      # Built-in
            'datetime': None,  # Built-in
            'threading': None, # Built-in
            'concurrent.futures': None,  # Built-in
            'inspect': None,   # Built-in
            'http.client': None,  # Built-in
            're': None,        # Built-in
            'difflib': None,   # Built-in
            'unicodedata': None,  # Built-in
            'collections': None,  # Built-in
            'ast': None,       # Built-in
            'math': None,      # Built-in
            'shutil': None,    # Built-in
            'glob': None,      # Built-in
            'traceback': None, # Built-in
            'collections': None,  # Built-in
            'glob': None,      # Built-in
            'traceback': None, # Built-in
        }
        
        # Optional packages (enhanced functionality)
        optional_packages_raw = {
            'sshkeyboard': 'sshkeyboard>=2.3.0',  # Interactive operations
            'pyte': 'pyte>=0.8.0',                # Terminal emulation
            'usaddress-scourgify': 'usaddress-scourgify>=0.6.0',  # Address parsing
            'rapidfuzz': 'rapidfuzz>=3.8.0',     # Fuzzy string matching
            'urllib3': 'urllib3>=1.26.0',        # Enhanced HTTP
            # Note: pynput and pexpect removed for simplicity and container compatibility
        }
        # Filter out None values (platform-incompatible packages)
        self.optional_packages = {k: v for k, v in optional_packages_raw.items() if v is not None}
        
    def check_uv_installation(self) -> bool:
        """Check if UV package manager is installed and accessible (cached)."""
        # If UV checking is disabled, return False immediately
        if self.disable_uv_check:
            return False
            
        # Return cached result if already checked
        if self._uv_checked:
            return self._uv_available
            
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logging.info(f"UV package manager found: {result.stdout.strip()}")
                self._uv_available = True
            else:
                logging.warning("UV package manager not found or not working properly")
                self._uv_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logging.warning(f"UV package manager check failed: {e}")
            self._uv_available = False
            
        # Cache the result
        self._uv_checked = True
        return self._uv_available
            
    def install_uv(self) -> bool:
        """Install UV package manager if not present."""
        if not self.auto_upgrade_uv:
            logging.info("Auto-upgrade of UV is disabled in configuration")
            return False
            
        logging.info("Attempting to install UV package manager...")
        try:
            # Try installing UV using pip as fallback
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], 
                                  capture_output=True, text=True, timeout=self.upgrade_check_timeout)
            if result.returncode == 0:
                logging.info("UV package manager installed successfully via pip")
                return True
            else:
                logging.error(f"Failed to install UV via pip: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logging.error(f"Failed to install UV package manager: {e}")
            return False
            
    def upgrade_uv(self) -> bool:
        """Upgrade UV package manager to latest version (only if needed)."""
        if not self.auto_upgrade_uv:
            return True
        
        # Check if we've recently checked for updates
        now = time.time()
        if self._last_uv_update_check:
            hours_since_last_check = (now - self._last_uv_update_check) / 3600
            if hours_since_last_check < self.uv_update_check_hours:
                logging.debug(f"UV update check skipped (last check {hours_since_last_check:.1f} hours ago, threshold: {self.uv_update_check_hours} hours)")
                return True
            
        try:
            logging.info("Checking for UV package manager updates...")
            # First try UV self-update (for standalone installations)
            result = subprocess.run(['uv', 'self', 'update'], 
                                  capture_output=True, text=True, timeout=self.upgrade_check_timeout)
            
            # Update the last check time regardless of result
            self._last_uv_update_check = now
            
            if result.returncode == 0:
                logging.info("UV package manager updated successfully")
                return True
            else:
                # If self-update fails, try pip upgrade (for pip-installed UV)
                if "Self-update is only available for uv binaries installed via the standalone installation scripts" in result.stderr:
                    logging.info("UV was installed via pip, attempting pip upgrade...")
                    pip_result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'uv'], 
                                              capture_output=True, text=True, timeout=self.upgrade_check_timeout)
                    if pip_result.returncode == 0:
                        logging.info("UV package manager updated successfully via pip")
                        return True
                    else:
                        logging.warning(f"Failed to upgrade UV via pip: {pip_result.stderr}")
                        return True  # Non-critical failure
                else:
                    logging.warning(f"UV self-update returned non-zero: {result.stderr}")
                    return True  # Non-critical failure
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            # Still update the last check time to avoid repeated failures
            self._last_uv_update_check = now
            logging.warning(f"UV self-update failed: {e}")
            return True  # Non-critical failure
            
    def install_package_with_uv(self, package_spec: str) -> bool:
        """Install a package using UV package manager with fast resolution and virtual environment awareness."""
        try:
            logging.debug(f"Installing package with UV: {package_spec}")
            
            # Check if we're in a virtual environment and prefer venv's UV if available
            uv_cmd = 'uv'
            if hasattr(self, 'in_venv') and self.in_venv:
                # Try to use UV from the virtual environment first
                venv_uv = os.path.join(os.path.dirname(sys.executable), 'uv.exe')
                if os.path.exists(venv_uv):
                    uv_cmd = venv_uv
                    logging.debug(f"Using venv UV: {venv_uv}")
                
                # Use UV with the current Python environment
                cmd = [uv_cmd, 'pip', 'install', '--python', sys.executable, '--no-build-isolation', package_spec]
            else:
                # Use UV with default behavior
                cmd = [uv_cmd, 'pip', 'install', '--no-build-isolation', package_spec]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.upgrade_check_timeout)
            if result.returncode == 0:
                logging.info(f"Successfully installed {package_spec} with UV")
                return True
            else:
                # Try without --no-build-isolation if it failed
                logging.debug(f"UV install failed with --no-build-isolation, retrying without it")
                if hasattr(self, 'in_venv') and self.in_venv:
                    cmd = [uv_cmd, 'pip', 'install', '--python', sys.executable, package_spec]
                else:
                    cmd = [uv_cmd, 'pip', 'install', package_spec]
                    
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.upgrade_check_timeout)
                if result.returncode == 0:
                    logging.info(f"Successfully installed {package_spec} with UV (fallback)")
                    return True
                else:
                    logging.warning(f"UV install failed for {package_spec}: {result.stderr}")
                    return False
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logging.warning(f"Failed to install {package_spec} with UV: {e}")
            return False
            
    def install_package_with_pip(self, package_spec: str) -> bool:
        """Install a package using pip as fallback with virtual environment awareness."""
        try:
            logging.info(f"Installing package with pip: {package_spec}")
            # Always use the current Python executable to ensure installation in the right environment
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package_spec], 
                                  capture_output=True, text=True, timeout=self.upgrade_check_timeout)
            if result.returncode == 0:
                logging.info(f"Successfully installed {package_spec} with pip")
                return True
            else:
                logging.error(f"Failed to install {package_spec} with pip: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logging.error(f"Failed to install {package_spec} with pip: {e}")
            return False
            
    def should_check_uv_update(self) -> bool:
        """Check if we should check for UV updates based on time since last check."""
        if not self.auto_upgrade_uv:
            return False
            
        if self._last_uv_update_check is None:
            return True
            
        time_since_check = time.time() - self._last_uv_update_check
        hours_since_check = time_since_check / 3600
        return hours_since_check >= self.uv_update_check_hours
    
    def check_uv_needs_update(self) -> bool:
        """Check if UV actually needs an update by comparing versions."""
        try:
            # Get current UV version
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
                
            # For now, we'll assume UV is up to date since checking remote version is complex
            # In a production environment, you might want to implement version comparison
            logging.debug("UV version check complete - assuming current version is adequate")
            return False
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
        """Check if a package is already installed."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def upgrade_all_dependencies(self) -> bool:
        """Install missing dependencies and upgrade existing ones."""
        if not self.auto_upgrade_dependencies:
            logging.info("Auto-upgrade of dependencies is disabled in configuration")
            return True
            
        # Collect package specs, filtering out built-in modules
        packages_to_process = []
        for pkg_name, pkg_spec in {**self.required_packages, **self.optional_packages}.items():
            if pkg_spec is not None:  # Skip built-in modules
                packages_to_process.append((pkg_name, pkg_spec))
                
        if not packages_to_process:
            logging.info("No packages to process")
            return True
        
        logging.info(f"Processing {len(packages_to_process)} packages...")
        
        # Process packages individually for better error handling
        uv_available = self.check_uv_installation()
        if uv_available:
            logging.info("Using UV package manager for installations")
        else:
            logging.info("Using pip for package installations (UV not available)")
            
        success_count = 0
        
        for pkg_name, pkg_spec in packages_to_process:
            # Extract base package name from spec (e.g., "requests>=2.28.0" -> "requests")
            base_name = pkg_spec.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
            
            try:
                # Try UV first if available
                if uv_available:
                    if self.install_package_with_uv(pkg_spec):
                        success_count += 1
                        continue
                
                # Fallback to pip
                if self.install_package_with_pip(pkg_spec):
                    success_count += 1
                else:
                    logging.warning(f"Failed to install/upgrade {pkg_spec}")
                    
            except Exception as e:
                logging.warning(f"Error processing package {pkg_spec}: {e}")
        
        logging.info(f"Successfully processed {success_count}/{len(packages_to_process)} packages")
        return success_count > 0
    
    def _import_concurrent_futures(self):
        """Special handler for concurrent.futures import."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        return type('ConcurrentFutures', (), {
            'ThreadPoolExecutor': ThreadPoolExecutor,
            'as_completed': as_completed
        })()
    
    def _import_datetime(self):
        """Special handler for datetime import."""
        # Import the actual datetime module for module-level access
        import datetime as dt_module
        from datetime import datetime, timezone, timedelta
        
        # The code expects 'datetime' to refer to the datetime class, not the module
        # But we also need module-level access. Create a special object that behaves like both.
        class DateTimeHandler:
            def __init__(self):
                # Make this object callable like datetime class
                self.now = datetime.now
                self.fromtimestamp = datetime.fromtimestamp
                self.strptime = datetime.strptime
                self.utcnow = datetime.utcnow
                # Add module attributes
                self.datetime = datetime
                self.timezone = timezone
                self.timedelta = timedelta
                # Add module for UTC access
                self.timezone = timezone
                
            def __call__(self, *args, **kwargs):
                # Allow calling like datetime()
                return datetime(*args, **kwargs)
                
        return DateTimeHandler()
    
    def _import_tqdm(self):
        """Special handler for tqdm import to ensure proper functionality."""
        try:
            from tqdm import tqdm
            logging.debug("Successfully imported tqdm from package")
            return tqdm
        except ImportError:
            logging.warning("tqdm package not available, using fallback")
            # Return the fallback function if tqdm is not available
            def tqdm_fallback(iterable, *args, **kwargs):
                """Fallback when tqdm package is not available."""
                desc = kwargs.get('desc', 'Processing')
                unit = kwargs.get('unit', 'item')
                if hasattr(iterable, '__len__'):
                    total = len(iterable)
                    logging.info(f"{desc}: {total} {unit}s to process")
                else:
                    logging.info(f"{desc}: processing {unit}s...")
                return iterable
            return tqdm_fallback
    
    def _check_and_upgrade_package(self, module_name: str, package_spec: str) -> bool:
        """Check if a package needs upgrading and upgrade it if necessary."""
        if not package_spec:
            return True  # Built-in modules don't need upgrading
            
        try:
            # Extract package name from spec
            package_name = package_spec.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
            
            # Check current version
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logging.debug(f"Package {package_name} not found, skipping upgrade check")
                return True
                
            # Parse current version from pip show output
            current_version = None
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    current_version = line.split(':', 1)[1].strip()
                    break
                    
            if current_version:
                logging.debug(f"Current version of {package_name}: {current_version}")
                
                # Try to upgrade the package
                logging.info(f"  Checking for updates to {package_name}...")
                
                # Use UV if available, otherwise pip
                if self.check_uv_installation():
                    # Check if we're in a virtual environment and prefer venv's UV if available
                    uv_cmd = 'uv'
                    if hasattr(self, 'in_venv') and self.in_venv:
                        # Try to use UV from the virtual environment first
                        venv_uv = os.path.join(os.path.dirname(sys.executable), 'uv.exe')
                        if os.path.exists(venv_uv):
                            uv_cmd = venv_uv
                        upgrade_cmd = [uv_cmd, 'pip', 'install', '--python', sys.executable, '--upgrade', package_spec]
                    else:
                        upgrade_cmd = [uv_cmd, 'pip', 'install', '--upgrade', package_spec]
                else:
                    upgrade_cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', package_spec]
                
                upgrade_result = subprocess.run(upgrade_cmd, capture_output=True, text=True, timeout=self.upgrade_check_timeout)
                
                if upgrade_result.returncode == 0:
                    # Check if version actually changed
                    new_result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                                              capture_output=True, text=True, timeout=10)
                    
                    new_version = None
                    for line in new_result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            new_version = line.split(':', 1)[1].strip()
                            break
                    
                    if new_version and new_version != current_version:
                        logging.info(f"  [OK] {package_name}: Upgraded from {current_version} to {new_version}")
                        return True
                    else:
                        logging.debug(f"  [OK] {package_name}: Already up to date ({current_version})")
                        return True
                else:
                    logging.debug(f"  [WARN] {package_name}: Upgrade check failed: {upgrade_result.stderr}")
                    return True  # Non-critical failure
            
            return True
            
        except Exception as e:
            logging.debug(f"Error checking/upgrading {module_name}: {e}")
            return True  # Non-critical failure
    
    def _get_actual_import_name(self, module_name: str) -> str:
        """Get the actual import name for a given module name, handling mappings."""
        return self.import_name_mappings.get(module_name, module_name)
            
    def import_module_safely(self, module_name: str, package_spec: Optional[str] = None, 
                           required: bool = True, skip_deps: bool = False, skip_upgrade: bool = True) -> Optional[Any]:
        """
        Safely import a module with automatic installation and upgrade checking if needed.
        
        Args:
            module_name: Name of the module to import
            package_spec: Package specification for installation (e.g., 'requests>=2.28.0')
            required: Whether this is a required dependency
            skip_deps: Whether to skip dependency checking and installation
            skip_upgrade: Whether to skip upgrade checking (default True for faster imports)
            
        Returns:
            The imported module or None if import failed
        """
        try:
            # Check if we have a special handler for this module
            if module_name in self.special_import_handlers:
                module = self.special_import_handlers[module_name]()
            else:
                # Use mapping to get actual import name
                actual_import_name = self._get_actual_import_name(module_name)
                module = __import__(actual_import_name)
                
            self.imports[module_name] = module
            logging.debug(f"Successfully imported {module_name}")
            
            # Check if we should upgrade existing packages (only if auto-upgrade is enabled and not skipping)
            if package_spec and self.auto_upgrade_dependencies and not skip_deps and not skip_upgrade:
                self._check_and_upgrade_package(module_name, package_spec)
            
            return module
            
        except ImportError as e:
            logging.warning(f"Failed to import {module_name}: {e}")
            
            # Attempt to install if package spec is provided and auto-installation is enabled
            if package_spec and self.auto_upgrade_dependencies and not skip_deps and not self.disable_auto_install:
                logging.info(f"Attempting to install missing dependency: {package_spec}")
                
                # Try installing the package
                installed = False
                
                # Try UV first if available (using cached check)
                if self.check_uv_installation():
                    logging.debug(f"Trying UV installation for {package_spec}")
                    installed = self.install_package_with_uv(package_spec)
                
                # Fallback to pip if UV failed or not available
                if not installed:
                    logging.debug(f"Trying pip installation for {package_spec}")
                    installed = self.install_package_with_pip(package_spec)
                    
                if installed:
                    # Clear import caches to allow fresh import
                    import importlib
                    importlib.invalidate_caches()
                    
                    # Remove any cached failed imports
                    actual_import_name = self._get_actual_import_name(module_name)
                    modules_to_clear = [actual_import_name, module_name]
                    for mod_name in modules_to_clear:
                        if mod_name in sys.modules:
                            del sys.modules[mod_name]
                            logging.debug(f"Cleared cached module: {mod_name}")
                    
                    # Wait a moment for installation to complete
                    time.sleep(0.5)
                    
                    # Retry import after installation
                    try:
                        if module_name in self.special_import_handlers:
                            module = self.special_import_handlers[module_name]()
                        else:
                            actual_import_name = self._get_actual_import_name(module_name)
                            module = __import__(actual_import_name)
                            
                        self.imports[module_name] = module
                        self.installed_packages.append(package_spec)
                        logging.info(f"Successfully imported {module_name} after installation")
                        return module
                        
                    except ImportError as retry_e:
                        logging.error(f"Import still failed after installation for {module_name}: {retry_e}")
                        # For optional packages, this is not critical
                        if not required:
                            logging.info(f"Optional package {module_name} installation succeeded but import failed - likely needs system restart or different Python session")
                else:
                    logging.error(f"Failed to install {package_spec}")
                        
            # Handle failure
            if required:
                self.failed_imports.append(module_name)
                logging.error(f"Required dependency {module_name} could not be imported or installed")
            else:
                logging.warning(f"Optional dependency {module_name} not available")
                
            return None
            
    def _import_packages_concurrently(self, packages_dict, required=True, skip_deps=False, max_workers=4):
        """
        Import packages concurrently for faster dependency resolution.
        
        Args:
            packages_dict: Dictionary of package_name: package_spec
            required: Whether these are required (True) or optional (False) packages
            skip_deps: Whether to skip dependency installation
            max_workers: Maximum number of concurrent workers
        """
        import concurrent.futures
        import threading
        
        # Thread-safe logging
        log_lock = threading.Lock()
        
        def import_single_package(package_info):
            module_name, package_spec = package_info
            package_type = "required" if required else "optional"
            
            with log_lock:
                logging.info(f"  Checking {package_type} dependency: {module_name} ({package_spec or 'built-in'})")
            
            result = self.import_module_safely(module_name, package_spec, required=required, skip_deps=skip_deps, skip_upgrade=True)
            
            with log_lock:
                if result:
                    logging.info(f"  [OK] {module_name}: Available")
                else:
                    if required:
                        logging.error(f"  [FAIL] {module_name}: Failed to import")
                    else:
                        logging.warning(f"  [WARN] {module_name}: Not available")
            
            return module_name, result
        
        # Split packages into built-in and external for better processing
        builtin_packages = {k: v for k, v in packages_dict.items() if v is None}
        external_packages = {k: v for k, v in packages_dict.items() if v is not None}
        
        # Process built-in packages first (fast, no network needed)
        for module_name, package_spec in builtin_packages.items():
            import_single_package((module_name, package_spec))
        
        # Process external packages concurrently
        if external_packages:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_package = {
                    executor.submit(import_single_package, item): item 
                    for item in external_packages.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_package):
                    package_info = future_to_package[future]
                    try:
                        module_name, result = future.result()
                    except Exception as exc:
                        with log_lock:
                            logging.error(f"Package {package_info[0]} import generated an exception: {exc}")
            
    def initialize_all_imports(self, skip_deps: bool = False) -> bool:
        """
        Initialize all imports and dependencies upfront.
        
        Args:
            skip_deps: Skip dependency checking and installation
            
        Returns:
            Tuple of (success: bool, global_assignments: dict)
        """
        # Check if already initialized to avoid duplicate work
        if hasattr(self, '_initialization_complete'):
            logging.debug("Import initialization already completed, returning cached results")
            return self._initialization_success, self._cached_global_assignments
            
        start_time = time.time()
        logging.info("Initializing global import management system...")
        
        if skip_deps:
            logging.info("Dependency checking and installation skipped (--skip-deps flag)")
        else:
            # Only check UV if auto-upgrade is enabled
            if self.auto_upgrade_uv:
                if not self.check_uv_installation():
                    self.install_uv()
                else:
                    self.upgrade_uv()
        
        # Import all required packages (this will install missing ones automatically)
        logging.info("Importing required dependencies...")
        
        # Use concurrent processing for faster dependency resolution
        if not skip_deps and len(self.required_packages) > 3:
            self._import_packages_concurrently(self.required_packages, required=True, skip_deps=skip_deps)
        else:
            # Sequential for smaller loads or when skipping deps
            for module_name, package_spec in self.required_packages.items():
                logging.info(f"  Checking required dependency: {module_name} ({package_spec or 'built-in'})")
                result = self.import_module_safely(module_name, package_spec, required=True, skip_deps=skip_deps, skip_upgrade=True)
                if result:
                    logging.info(f"  [OK] {module_name}: Available")
                else:
                    logging.error(f"  [FAIL] {module_name}: Failed to import")
            
        # Import optional packages
        logging.info("Importing optional dependencies...")
        if not skip_deps and len(self.optional_packages) > 3:
            self._import_packages_concurrently(self.optional_packages, required=False, skip_deps=skip_deps)
        else:
            # Sequential for smaller loads or when skipping deps
            for module_name, package_spec in self.optional_packages.items():
                logging.info(f"  Checking optional dependency: {module_name} ({package_spec or 'built-in'})")
                result = self.import_module_safely(module_name, package_spec, required=False, skip_deps=skip_deps, skip_upgrade=True)
                if result:
                    logging.info(f"  [OK] {module_name}: Available")
                else:
                    logging.warning(f"  [WARN] {module_name}: Not available")
            
        # Special imports for commonly used components
        self._import_special_modules()
        
        # Report results
        elapsed_time = time.time() - start_time
        total_required = len(self.required_packages)
        failed_required = len([p for p in self.failed_imports if p in self.required_packages])
        successful_required = total_required - failed_required
        optional_imported = len([p for p in self.imports.keys() if p in self.optional_packages])
        
        logging.info(f"Import initialization completed in {elapsed_time:.2f} seconds")
        logging.info(f"Required dependencies: {successful_required}/{total_required} successful")
        logging.info(f"Optional dependencies: {optional_imported}/{len(self.optional_packages)} available")
        
        if self.installed_packages:
            logging.info(f"Newly installed packages: {', '.join(self.installed_packages)}")
            
        if self.failed_imports:
            logging.error(f"Failed imports: {', '.join(self.failed_imports)}")
            
        # Make imported modules available globally
        global_assignments = self._get_global_assignments()
        
        # Cache results to avoid duplicate initialization
        success = len(self.failed_imports) == 0
        self._initialization_complete = True
        self._initialization_success = success
        self._cached_global_assignments = global_assignments
        
        # Return success status and global assignments
        return success, global_assignments
        
    def _get_global_assignments(self):
        """Get dictionary of global variable assignments for imported modules."""
        global_vars = {}
        
        # Add all imported modules to globals
        for module_name, module_obj in self.imports.items():
            # Add to global namespace
            global_vars[module_name] = module_obj
            
            # Handle special cases for commonly used attributes
            if module_name == 'datetime':
                global_vars['timezone'] = getattr(module_obj, 'timezone', None)
                global_vars['timedelta'] = getattr(module_obj, 'timedelta', None)
            elif module_name == 'concurrent.futures':
                global_vars['ThreadPoolExecutor'] = getattr(module_obj, 'ThreadPoolExecutor', None)
                global_vars['as_completed'] = getattr(module_obj, 'as_completed', None)
                global_vars['concurrent'] = module_obj  # For concurrent.futures references
            elif module_name == 'prettytable':
                global_vars['PrettyTable'] = getattr(module_obj, 'PrettyTable', None)
            elif module_name == 'numpy':
                global_vars['np'] = module_obj
            elif module_name == 'tqdm':
                # tqdm is used directly throughout the script
                global_vars['tqdm'] = module_obj
            elif module_name == 'collections':
                global_vars['defaultdict'] = getattr(module_obj, 'defaultdict', None)
            elif module_name == 'difflib':
                global_vars['SequenceMatcher'] = getattr(module_obj, 'SequenceMatcher', None)
            elif module_name == 'usaddress-scourgify':
                # Handle optional package - need to import the normalize function
                if module_obj:
                    try:
                        normalize_func = getattr(module_obj, 'normalize_address_record', None)
                        if normalize_func:
                            global_vars['normalize_address_record'] = normalize_func
                        else:
                            # Try importing directly from scourgify
                            from scourgify import normalize_address_record
                            global_vars['normalize_address_record'] = normalize_address_record
                    except (ImportError, AttributeError):
                        logging.debug("Could not import normalize_address_record from scourgify, using fallback")
            elif module_name == 'rapidfuzz':
                # Handle optional package - need to import the fuzz submodule
                if module_obj:
                    try:
                        fuzz_module = getattr(module_obj, 'fuzz', None)
                        if fuzz_module:
                            global_vars['fuzz'] = fuzz_module
                        else:
                            # Try importing fuzz directly from rapidfuzz
                            from rapidfuzz import fuzz
                            global_vars['fuzz'] = fuzz
                    except (ImportError, AttributeError):
                        logging.debug("Could not import fuzz from rapidfuzz, using fallback")
            # Note: pynput handling removed for simplicity
            elif module_name == 'mistapi':
                # Handle mistapi module - make it globally available
                if module_obj:
                    global_vars['mistapi'] = module_obj
                    logging.debug("Added mistapi to global namespace")
            elif module_name == 'paramiko':
                # Handle SSH client functionality
                if module_obj:
                    global_vars['paramiko'] = module_obj
                    logging.debug("Added paramiko to global namespace")
            # Note: pexpect handling removed for simplicity
            elif module_name == 'redexpect':
                # Handle cross-platform SSH automation
                if module_obj:
                    global_vars['redexpect'] = module_obj
                    logging.debug("Added redexpect to global namespace")
                        
        # Handle fallbacks for missing optional modules
        self._add_fallbacks_to_globals(global_vars)
        
        return global_vars
        
    def _make_modules_global(self):
        """Make all successfully imported modules available in the global namespace."""
        import builtins
        
        # Add all imported modules to globals
        for module_name, module_obj in self.imports.items():
            # Add to global namespace
            globals()[module_name] = module_obj
            
            # Handle special cases for commonly used attributes
            if module_name == 'datetime':
                globals()['timezone'] = getattr(module_obj, 'timezone', None)
                globals()['timedelta'] = getattr(module_obj, 'timedelta', None)
            elif module_name == 'concurrent.futures':
                globals()['ThreadPoolExecutor'] = getattr(module_obj, 'ThreadPoolExecutor', None)
                globals()['as_completed'] = getattr(module_obj, 'as_completed', None)
                globals()['concurrent'] = module_obj  # For concurrent.futures references
            elif module_name == 'prettytable':
                globals()['PrettyTable'] = getattr(module_obj, 'PrettyTable', None)
            elif module_name == 'numpy':
                globals()['np'] = module_obj
            elif module_name == 'tqdm':
                # tqdm is used directly throughout the script
                globals()['tqdm'] = module_obj
            elif module_name == 'collections':
                globals()['defaultdict'] = getattr(module_obj, 'defaultdict', None)
            elif module_name == 'difflib':
                globals()['SequenceMatcher'] = getattr(module_obj, 'SequenceMatcher', None)
            elif module_name == 'usaddress-scourgify':
                # Handle optional package - need to import the normalize function
                if module_obj:
                    try:
                        normalize_func = getattr(module_obj, 'normalize_address_record', None)
                        if normalize_func:
                            globals()['normalize_address_record'] = normalize_func
                        else:
                            # Try importing directly from scourgify
                            from scourgify import normalize_address_record
                            globals()['normalize_address_record'] = normalize_address_record
                    except (ImportError, AttributeError):
                        logging.debug("Could not import normalize_address_record from scourgify, using fallback")
            elif module_name == 'rapidfuzz':
                # Handle optional package - need to import the fuzz submodule
                if module_obj:
                    try:
                        fuzz_module = getattr(module_obj, 'fuzz', None)
                        if fuzz_module:
                            globals()['fuzz'] = fuzz_module
                        else:
                            # Try importing fuzz directly from rapidfuzz
                            from rapidfuzz import fuzz
                            globals()['fuzz'] = fuzz
                    except (ImportError, AttributeError):
                        logging.debug("Could not import fuzz from rapidfuzz, using fallback")
            # Note: pynput handling removed for simplicity
                        
        # Handle fallbacks for missing optional modules
        self._setup_fallbacks()
                        
        logging.debug("Successfully made imported modules available globally")
        
    def _add_fallbacks_to_globals(self, global_vars):
        """Add fallbacks for optional modules that failed to import."""
        # If scourgify not available, provide a fallback
        if 'normalize_address_record' not in global_vars or global_vars['normalize_address_record'] is None:
            def normalize_address_record_fallback(address_string):
                """Fallback function when scourgify is not available."""
                logging.debug("Using fallback address normalization (scourgify not available)")
                return {
                    'address_line_1': address_string,
                    'city': '',
                    'state': '', 
                    'zip': '',
                    'country': ''
                }
            global_vars['normalize_address_record'] = normalize_address_record_fallback
            
        # If rapidfuzz not available, provide fallback
        if 'fuzz' not in global_vars or global_vars['fuzz'] is None:
            class FuzzFallback:
                """Fallback class when rapidfuzz is not available."""
                @staticmethod
                def token_sort_ratio(str1, str2):
                    """Fallback using difflib SequenceMatcher."""
                    if global_vars.get('difflib'):
                        return int(global_vars['difflib'].SequenceMatcher(None, str1, str2).ratio() * 100)
                    return 0
            global_vars['fuzz'] = FuzzFallback()
            
        # Keyboard listener functionality has been removed for simplicity
        # No fallback needed since the feature is no longer supported
        
        # Add SSH connection fallbacks
        if 'paramiko' not in global_vars or global_vars['paramiko'] is None:
            class SSHFallback:
                """Fallback class when paramiko is not available."""
                @staticmethod
                def SSHClient():
                    raise ImportError("SSH functionality requires 'paramiko' package. Install with: pip install paramiko")
            global_vars['paramiko'] = SSHFallback()
            
        # pexpect functionality has been removed for simplicity
        # SSH automation should use paramiko directly
        
        if 'redexpect' not in global_vars or global_vars['redexpect'] is None:
            class RedexpectFallback:
                """Fallback class when redexpect is not available."""
                @staticmethod
                def spawn(*args, **kwargs):
                    raise ImportError("Cross-platform SSH automation requires 'redexpect' package. Install with: pip install redexpect")
            global_vars['redexpect'] = RedexpectFallback()
        
    def _import_special_modules(self):
        """Import special modules with custom handling."""
        # Import mistapi with its sub-modules only if base mistapi is available
        if 'mistapi' in self.imports:
            try:
                mistapi = self.imports['mistapi']
                # Import commonly used mistapi modules without forcing sub-module structure
                try:
                    # These imports may not be available in all mistapi versions
                    # Import them dynamically to avoid hard dependencies on specific structure
                    globals()['mistapi'] = mistapi
                    # Also ensure it's in the module's global namespace
                    import sys
                    sys.modules[__name__].mistapi = mistapi
                    logging.debug("Successfully imported mistapi main module")
                    # Verify the api module is accessible
                    if hasattr(mistapi, 'api') and hasattr(mistapi.api, 'v1'):
                        logging.debug("mistapi.api.v1 module structure confirmed")
                    else:
                        logging.warning("mistapi.api.v1 structure not found - this may cause API call failures")
                except Exception as sub_e:
                    logging.debug(f"Note: mistapi sub-modules handled dynamically: {sub_e}")
            except Exception as e:
                logging.warning(f"Error accessing mistapi: {e}")
        else:
            logging.debug("mistapi not imported, skipping sub-module imports")
            
        # Import websocket if available
        if 'websocket-client' in self.imports:
            logging.debug("websocket-client available for WebSocket operations")
        else:
            logging.debug("websocket-client not available - WebSocket operations will be disabled")
            
    def get_import(self, module_name: str) -> Optional[Any]:
        """Get an imported module by name."""
        return self.imports.get(module_name)
        
    def is_available(self, module_name: str) -> bool:
        """Check if a module is available."""
        return module_name in self.imports
        
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration values."""
        return {
            'auto_upgrade_uv': self.auto_upgrade_uv,
            'auto_upgrade_dependencies': self.auto_upgrade_dependencies,
            'upgrade_check_timeout': self.upgrade_check_timeout,
            'csv_freshness_minutes': self.csv_freshness_minutes,
            'uv_update_check_hours': self.uv_update_check_hours,
        }

# ============================================================================
# GLOBAL CONSTANTS
# ============================================================================

# File paths for configuration and data
tuning_data_file = "tuning_data.json"

# API usage tracking cache
_api_usage_cache = {
    "timestamp": 0,
    "used": 0,
    "limit": 5000,
    "last_updated": 0,
    "perceived_requests": 0,
    "initialized": False 
}

# ============================================================================
# GLOBAL IMPORT MANAGER INITIALIZATION
# ============================================================================

# Create global import manager instance
import_manager = GlobalImportManager()

# Initialize imports immediately (unless deferred by CLI flags)
# Test mode and skip-deps both defer initialization to main() for better control
_initialize_imports_now = True

# Check for test mode or skip-deps from command line
if '--test' in sys.argv or '--skip-deps' in sys.argv:
    _initialize_imports_now = False
    if '--test' in sys.argv and '--skip-deps' not in sys.argv:
        logging.info("Deferring import initialization for test mode (dependencies will still be checked)")
    elif '--skip-deps' in sys.argv:
        logging.info("Deferring import initialization due to --skip-deps flag")
    else:
        logging.info("Deferring import initialization due to CLI flags")

if _initialize_imports_now:
    # Initialize all imports upfront for faster runtime performance
    success, global_assignments = import_manager.initialize_all_imports()
    
    # Apply global assignments to module namespace
    if global_assignments:
        for var_name, var_value in global_assignments.items():
            globals()[var_name] = var_value
            # Special handling for tqdm to ensure it overrides the fallback
            if var_name == 'tqdm' and var_value is not None:
                logging.info(f"Successfully imported real tqdm: {type(var_value)}")
        logging.debug(f"Applied {len(global_assignments)} global variable assignments")
        
        # Verify tqdm was properly imported
        if 'tqdm' in global_assignments:
            logging.info(f"tqdm is available in global namespace: {type(globals().get('tqdm'))}")
        else:
            logging.warning("tqdm was not found in global assignments - progress bars will not be functional")
    
    if not success:
        logging.warning("Some required imports failed - functionality may be limited")
else:
    # Deferred initialization - will be done in main()
    success, global_assignments = False, {}

# ============================================================================
# TEST MODE GLOBALS & DYNAMIC LOOKBACK HELPER
# ============================================================================
# Central flag for test mode (available early so helper functions outside main can use it)
IS_TEST_MODE = '--test' in sys.argv

def get_dynamic_lookback_hours(default_hours: int = 24, test_hours: int = 1) -> int:
    """Return lookback hours adjusted for test mode.

    In normal operation we retain the full 24 hour (or caller provided) window.
    When the global --test flag is present, we shrink the lookback to 1 hour to:
      - Minimize API payload sizes / speed up systematic tests
      - Still exercise recent-data code paths
    The value is intentionally conservative (1h) to avoid missing fresh events while
    keeping runtime low. If a caller passes a different default_hours (e.g., 12),
    that value will be honored outside test mode.

    Parameters
    ----------
    default_hours : int
        Standard lookback window (typically 24).
    test_hours : int
        Reduced lookback for test mode (default 1 hour).

    Returns
    -------
    int
        Hours to use for lookback calculations.
    """
    try:
        if IS_TEST_MODE:
            # Boundaries & safety: never return less than 1 hour
            if test_hours < 1:
                return 1
            return test_hours
        if default_hours < 1:
            return 1
        return default_hours
    except Exception as e:
        logging.debug(f"get_dynamic_lookback_hours fallback due to error: {e}")
        return test_hours if IS_TEST_MODE else default_hours

def log_dynamic_lookback(context: str, hours: int):
    """Helper to produce a consistent log line when dynamic lookback applies."""
    if IS_TEST_MODE:
        logging.info(f"[TEST MODE] Using reduced lookback window of {hours}h for {context} (normally 24h)")
    else:
        logging.debug(f"Using standard lookback window of {hours}h for {context}")

# ============================================================================
# IMPORT STATUS AND HELPER FUNCTIONS
# ============================================================================

def get_import_status():
    """Get status of all imports for debugging."""
    return {
        'required_packages': import_manager.required_packages,
        'optional_packages': import_manager.optional_packages,
        'failed_imports': import_manager.failed_imports,
        'successful_imports': list(import_manager.imports.keys()),
        'installed_packages': import_manager.installed_packages
    }

def ensure_tqdm_available():
    """Ensure tqdm is available and properly imported."""
    global tqdm
    
    # Check if tqdm is properly imported (not our fallback)
    if hasattr(tqdm, '__module__') and tqdm.__module__ == 'tqdm':
        logging.debug("tqdm is properly imported and available")
        return True
    
    # Try to get tqdm from the import manager
    tqdm_from_manager = import_manager.get_import('tqdm')
    if tqdm_from_manager:
        tqdm = tqdm_from_manager
        logging.info("Retrieved tqdm from import manager")
        return True
    
    # Try importing tqdm directly
    try:
        from tqdm import tqdm as real_tqdm
        tqdm = real_tqdm
        logging.info("Successfully imported tqdm directly")
        return True
    except ImportError:
        logging.warning("tqdm package is not available - progress bars will be disabled")
        return False

def clean_unicode_for_logging(message):
    """Clean Unicode characters from log messages to prevent encoding errors on Windows."""
    if isinstance(message, str):
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            'OK': '[OK]',
            'FAIL': '[FAIL]',
            'WARN': '[WARN]',
            '*': '*',
            '-': '-',
            '-': '-',
            '—': '-',
            ''': "'",
            ''': "'",
            '"': '"',
            '"': '"',
        }
        for unicode_char, ascii_replacement in replacements.items():
            message = message.replace(unicode_char, ascii_replacement)
        
        # Remove any remaining non-ASCII characters
        message = message.encode('ascii', 'replace').decode('ascii')
    return message

def safe_print(message):
    """Print message with Unicode characters cleaned for Windows compatibility."""
    print(clean_unicode_for_logging(str(message)))

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Configuration variables from .env (with defaults) - now managed by import manager
config = import_manager.get_configuration()
CSV_FRESHNESS_MINUTES = config['csv_freshness_minutes']
AUTO_UPGRADE_UV = config['auto_upgrade_uv']
AUTO_UPGRADE_DEPENDENCIES = config['auto_upgrade_dependencies']
UPGRADE_CHECK_TIMEOUT = config['upgrade_check_timeout']

# Fast Mode Configuration from .env
FAST_MODE_MAX_RETRIES = int(os.getenv("FAST_MODE_MAX_RETRIES", "3"))
FAST_MODE_RETRY_DELAY = float(os.getenv("FAST_MODE_RETRY_DELAY", "0.5"))

org_id=None

# Additional Fast Mode Configuration from .env (continuing from earlier definitions)
FAST_MODE_BACKOFF_MULTIPLIER = float(os.getenv("FAST_MODE_BACKOFF_MULTIPLIER", "1.5"))
FAST_MODE_DEVICES_PER_THREAD = int(os.getenv("FAST_MODE_DEVICES_PER_THREAD", "10"))
FAST_MODE_RETRY_THREADS = int(os.getenv("FAST_MODE_RETRY_THREADS", "4"))
FAST_MODE_RETRY_MAX_RETRIES = int(os.getenv("FAST_MODE_RETRY_MAX_RETRIES", "2"))
FAST_MODE_SEQUENTIAL_MAX_RETRIES = int(os.getenv("FAST_MODE_SEQUENTIAL_MAX_RETRIES", "1"))
FAST_MODE_FALLBACK_THREADS = int(os.getenv("FAST_MODE_FALLBACK_THREADS", "8"))
FAST_MODE_MAX_CONCURRENT_CONNECTIONS = int(os.getenv("FAST_MODE_MAX_CONCURRENT_CONNECTIONS", "8"))
FAST_MODE_USE_CONNECTION_AWARE_THREADING = os.getenv("FAST_MODE_USE_CONNECTION_AWARE_THREADING", "true").lower() == "true"

# Global configuration for output format (CSV or SQLite)
# Default to CSV for general use, can be overridden by CLI flag
OUTPUT_FORMAT = "csv"  # Valid values: "csv", "sqlite"
DATABASE_PATH = os.path.join("data", "mist_data.db")  # Path to hybrid SQLite database with natural primary keys

# ============================================================================
# GLOBAL SESSION INITIALIZATION
# ============================================================================

# Initialize Mist API session (will be set up after authentication)
apisession = None

def initialize_mist_session():
    """Initialize the Mist API session with authentication.

    Strategy:
      1. Try APISession with env_file (legacy behavior).
      2. If that fails, normalize token(s) from MIST_APITOKEN / MIST_API_TOKEN and try APISession with each via 'apitoken='.
      3. Fallback to mistapi.Session() if available.
      4. If all fail, return False (do NOT create placeholder that lacks required methods).

    SECURITY: Tokens are only logged in redacted preview at DEBUG level.
    """
    global apisession
    if apisession:
        return True

    host = os.getenv('MIST_HOST', 'api.mist.com')
    raw_token_env = os.getenv('MIST_APITOKEN') or os.getenv('MIST_API_TOKEN')
    if raw_token_env:
        tokens = [t.strip() for t in re.split(r'[\n,]+', raw_token_env) if t.strip()]
    else:
        tokens = []
    if tokens:
        redacted_preview = ','.join([(t[:4] + '...' + t[-4:]) if len(t) >= 8 else '***' for t in tokens])
        logging.debug(f"Token(s) discovered for initialization (redacted): {redacted_preview}")
    else:
        logging.debug("No tokens discovered in environment; will rely on env_file or mistapi.Session fallback")

    # Dynamically interrogate APISession signature to avoid wrong parameter names
    apisession_cls = getattr(mistapi, 'APISession', None) if mistapi else None
    tried_variants = []
    if apisession_cls:
        try:
            sig_params = list(inspect.signature(apisession_cls).parameters.keys())
            logging.debug(f"mistapi.APISession accepted parameters: {sig_params}")
        except Exception:
            sig_params = []
    else:
        sig_params = []

    # Candidate constructors to attempt (ordered)
    attempts = []
    if apisession_cls:
        # 1. env_file only if supported
        if 'env_file' in sig_params:
            attempts.append({'env_file': '.env'})
        # 2. Direct tokens (iterate) with potential parameter names
        token_param_names = [n for n in ['apitoken', 'api_token', 'token'] if n in sig_params]
        if tokens and token_param_names:
            for idx, tk in enumerate(tokens, start=1):
                for pname in token_param_names:
                    base_kwargs = {pname: tk}
                    if 'host' in sig_params:
                        base_kwargs['host'] = host
                    attempts.append(base_kwargs)
        # 3. Host only (unauthenticated) if allowed (rare but safe to record)
        if 'host' in sig_params and not tokens:
            attempts.append({'host': host})

    # Execute attempts
    successful_method = None
    for i, kwargs in enumerate(attempts, start=1):
        try:
            tried_variants.append(kwargs)
            apisession = apisession_cls(**kwargs)
            successful_method = kwargs
            logging.info(f"Mist API session initialized with mistapi.APISession using kwargs={list(kwargs.keys())}")
            break
        except Exception as e:
            logging.warning(f"APISession attempt {i}/{len(attempts)} failed kwargs={kwargs}: {e}")
            apisession = None

    # Fallback to mistapi.Session if APISession failed
    if not apisession and mistapi and hasattr(mistapi, 'Session'):
        try:
            apisession = mistapi.Session()
            successful_method = {'fallback': 'mistapi.Session'}
            logging.info("Mist API session initialized with mistapi.Session fallback")
        except Exception as e:
            logging.error(f"mistapi.Session fallback failed: {e}")
            apisession = None

    if not apisession:
        logging.error("All Mist API session initialization attempts failed. Variants tried:")
        for variant in tried_variants:
            logging.error(f"  - {variant}")
        return False

    # Validate that required request method exists (mist_get is used by code)
    if not hasattr(apisession, 'mist_get'):
        # Some versions expose 'get' instead; we can wrap it for compatibility
        if hasattr(apisession, 'get') and callable(getattr(apisession, 'get')):
            def _mist_get_wrapper(*args, **kwargs):  # pragma: no cover (simple adapter)
                return apisession.get(*args, **kwargs)
            setattr(apisession, 'mist_get', _mist_get_wrapper)
            logging.info("Added mist_get wrapper around underlying get() method for compatibility")
        else:
            logging.error("Initialized session lacks 'mist_get' or 'get' methods required for API calls")
            return False

    # Enhanced token validation - only warn if no authentication method was used
    token_attr = next((a for a in ("apitoken", "api_token", "token") if hasattr(apisession, a)), None)
    has_readable_token = token_attr and getattr(apisession, token_attr)
    used_env_file = successful_method and 'env_file' in successful_method
    used_direct_token = successful_method and any(param in successful_method for param in ['apitoken', 'api_token', 'token'])
    used_fallback_session = successful_method and 'fallback' in successful_method
    
    # Only warn if no authentication method appears to be configured
    if not (has_readable_token or used_env_file or used_direct_token or used_fallback_session):
        logging.warning("Session established but no authentication method detected; API calls may fail if authentication required")
        logging.warning("To fix this: 1) Copy documentation/sample.env to .env, 2) Set MIST_APITOKEN to your Mist API token")
        logging.warning("Get your API token from: https://manage.mist.com/admin/apitoken")
    elif used_env_file:
        logging.debug("Session initialized using env_file - authentication configured via .env file")
    elif used_direct_token:
        logging.debug("Session initialized using direct token parameter - authentication configured")
    elif has_readable_token:
        logging.debug("Session has readable token attribute - authentication appears configured")

    return True

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
    'listSiteDevicesStats': {
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
                logging.info(f"! Using cached {file_name} (fresh)")
                logging.debug(f"EXIT: check_and_generate_csv - using cached file")
                return True
            else:
                # Log that the file is stale and will be regenerated
                logging.info(f"* {file_name} is older than {freshness_minutes} minutes. Regenerating...")
        except OSError as e:
            logging.error(f"File I/O: Failed to read modification time for {full_file_path}: {e}")
            logging.info(f"* {file_name} exists but cannot read metadata. Regenerating...")
    else:
        # Log that the file does not exist and will be generated
        logging.info(f"* {file_name} not found. Generating...")

    # Call the function to generate the file
    logging.info(f"* Running {generate_function.__name__} to generate {file_name}...")
    try:
        generate_function()
        logging.info(f"! {file_name} generated or refreshed.")
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
    DataExporter.save_data_to_output(data, filename)

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
    DataExporter.save_data_to_output(stats, filename)

    # Display the data in a table
    display_dict_list_as_pretty_table(stats)

class SFPTransceiverDataProcessor:
    """Process and correlate SFP / transceiver data with site & device context.

    RATIONALE:
        This logic was previously a standalone function (`process_and_merge_csv_for_sfp_address`).
        It is only invoked by menu option 77 and has no tight coupling with most runtime state.
        Encapsulating it in a class improves hierarchy and opens the door for future extensions
        (e.g., JSON export, filtering, unit tests) without growing the monolithic global scope.

    SECURITY:
        Operates only on locally generated CSV artifacts inside the controlled `data/` directory.
        No external network or credential usage. Filenames are static and not user-injected.
    """

    OUTPUT_FILENAME = 'MergedTransceiverData.csv'

    @staticmethod
    def merge_transceiver_data():
        """Generate a merged transceiver CSV linking port optics to site + device context.

        Steps:
            1. Ensure prerequisite CSVs exist (generate if missing):
               - OrgDevicePortStats.csv
               - AllDevicesWithSiteInfo.csv
            2. Load device/site context keyed by MAC.
            3. Filter port stats to rows containing a non-empty transceiver model.
            4. Write merged result to `MergedTransceiverData.csv` via DataExporter.
        """
        logging.debug("ENTRY: SFPTransceiverDataProcessor.merge_transceiver_data()")

        org_port_stats_path = get_csv_file_path('OrgDevicePortStats.csv')
        devices_with_site_info_path = get_csv_file_path('AllDevicesWithSiteInfo.csv')

        # Generate prerequisites if absent (idempotent behavior matches prior function)
        if not os.path.exists(org_port_stats_path):
            print("* OrgDevicePortStats.csv not found. Generating it now...")
            logging.info("OrgDevicePortStats.csv missing; invoking export_device_port_stats_to_csv()")
            export_device_port_stats_to_csv()

        if not os.path.exists(devices_with_site_info_path):
            print("* AllDevicesWithSiteInfo.csv not found. Generating it now...")
            logging.info("AllDevicesWithSiteInfo.csv missing; invoking export_devices_with_site_info_to_csv()")
            export_devices_with_site_info_to_csv()

        try:
            # Load context keyed by MAC
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
            logging.info(f"Loaded {len(site_info)} device entries from {devices_with_site_info_path}")

            merged_data = []
            total_rows = 0
            candidate_rows = 0  # rows having a non-empty transceiver model (may or may not map to a known device MAC)
            matched_rows = 0    # rows contributing to merged output
            unique_devices_with_transceivers: set[str] = set()

            logging.debug(f"File I/O: Reading {org_port_stats_path}")
            with open(org_port_stats_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    total_rows += 1
                    mac = row.get('mac')
                    transceiver_model = row.get('xcvr_model', '').strip()

                    if transceiver_model:
                        candidate_rows += 1

                    if mac in site_info and transceiver_model:
                        matched_rows += 1
                        unique_devices_with_transceivers.add(mac)
                        merged_data.append({
                            'site_name': site_info[mac]['site_name'],
                            'site_address': site_info[mac]['site_address'],
                            'device_name': site_info[mac]['device_name'],
                            'port_id': row.get('port_id', ''),
                            'transceiver_part_number': row.get('xcvr_part_number', ''),
                            'transceiver_model': transceiver_model,
                            'transceiver_serial_number': row.get('xcvr_serial', '')
                        })

            if matched_rows == 0:
                # Downgraded severity explanation lives here; DataExporter currently emits a WARNING when given 0 rows.
                logging.info(
                    "Processed port stats; no matching transceivers found. total_rows=%d candidate_rows=%d known_devices=%d. "
                    "This can be normal if the inventory currently has no optics populated.",
                    total_rows, candidate_rows, len(site_info)
                )
            else:
                logging.info(
                    "Processed port stats; %d ports with transceivers found (total_rows=%d candidate_rows=%d unique_devices=%d)",
                    matched_rows, total_rows, candidate_rows, len(unique_devices_with_transceivers)
                )

            DataExporter.save_data_to_output(merged_data, SFPTransceiverDataProcessor.OUTPUT_FILENAME)
            logging.info(f"Wrote {len(merged_data)} rows to {SFPTransceiverDataProcessor.OUTPUT_FILENAME}")
            print(f"! Merged data written to {SFPTransceiverDataProcessor.OUTPUT_FILENAME}")
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - success")
        except FileNotFoundError as e:
            logging.error(f"File I/O: Required CSV file not found: {e}")
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - file not found")
            raise
        except csv.Error as e:
            logging.error(f"File I/O: CSV processing error: {e}")
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - CSV error")
            raise
        except Exception as e:
            logging.error(f"File I/O: Unexpected error during transceiver merge: {e}")
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - unexpected error")
            raise


    # NOTE: Legacy function name `process_and_merge_csv_for_sfp_address` removed; menu now invokes class method directly.

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
        error_msg = f"! site_id is None in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    if isinstance(site_id, str) and site_id.strip() == "":
        error_msg = f"! site_id is empty string in {function_name}. Cannot make API call."
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
        error_msg = f"! device_id is None in {function_name}. Cannot make API call."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    if isinstance(device_id, str) and device_id.strip() == "":
        error_msg = f"! device_id is empty string in {function_name}. Cannot make API call."
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

def get_cached_or_prompted_org_id():
    """
    Get organization ID from various sources in order of preference:
    1. Global variable
    2. Environment variable
    3. .env file
    4. Interactive prompt
    """
    global org_id
    # 1. Check global variable
    if org_id:
        logging.info(f"! Using org_id from global variable: {org_id}")
        return org_id
    # 2. Check environment variable (set by dotenv or OS)
    org_id_env = os.environ.get("org_id") or os.environ.get("ORG_ID")
    if org_id_env:
        org_id = org_id_env
        logging.info(f"! Loaded org_id from environment: {org_id}")
        return org_id
    # 3. Fallback: Try to load from .env manually (rarely needed)
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("org_id="):
                    org_id = line.strip().split("=", 1)[1].strip().strip('"')
        if org_id:
            logging.info(f"! Loaded org_id from .env: {org_id}")
            return org_id
    except FileNotFoundError:
        logging.warning("! .env file not found.")
    # 4. Prompt if still not set
    logging.info("* No org_id found in .env or CLI. Prompting user...")
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
        # Skip entries that are not dictionaries (defensive programming)
        if not isinstance(entry, dict):
            logging.debug(f"Skipping non-dictionary entry: {type(entry).__name__} - {entry}")
            continue
            
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
        print(f"! Cannot write to {csv_file_path}. Is it open in another program?")
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


class DataExporter:
    """
    Handles data export operations for CSV and SQLite output formats.
    Centralizes all data saving logic that was previously scattered across functions.
    Uses static methods to avoid unnecessary object instantiation.
    """
    
    @staticmethod
    def save_data_to_output(data, filename, api_function_name=None):
        """
        Save data to the specified format (CSV or SQLite).
        This replaces the save_data_to_output function with identical signature.
        
        Args:
            data (list): List of dictionaries containing the data to write
            filename (str): CSV filename or database table name  
            api_function_name (str, optional): Name of the API function for SQLite strategy selection
            
        Returns:
            bool: True if successful, False otherwise
        """
        return write_data_with_format_selection(data, filename, api_function_name=api_function_name)
    
    @staticmethod
    def export_with_processing(data, filename, sort_key=None, api_function_name=None):
        """
        Export data with standard processing (flatten, escape, sort).
        Common pattern used throughout the codebase.
        
        Args:
            data (list): Raw data from API
            filename (str): Output filename
            sort_key (str, optional): Key to sort by
            api_function_name (str, optional): API function name for strategy
            
        Returns:
            int: Number of records processed
        """
        if not data:
            logging.warning(f"No data to export for {filename}")
            return 0
            
        # Filter to dict entries only (defensive)
        processed_data = [entry for entry in data if isinstance(entry, dict)]
        
        # Sort if requested
        if sort_key:
            processed_data = sorted(processed_data, key=lambda x: x.get(sort_key, ""))
            logging.debug(f"Data sorted by key: {sort_key}")
        
        # Apply standard processing
        processed_data = flatten_nested_fields_in_list(processed_data)
        processed_data = escape_multiline_strings_for_csv(processed_data)
        
        # Save the processed data
        success = DataExporter.save_data_to_output(processed_data, filename, api_function_name)
        
        if success:
            logging.info(f"Exported {len(processed_data)} records to {filename}")
            return len(processed_data)
        else:
            logging.error(f"Failed to export data to {filename}")
            return 0


def save_data_to_output(data, filename, api_function_name=None):
    """
    Wrapper function to replace write_dict_list_to_csv calls.
    Routes to appropriate output format based on global OUTPUT_FORMAT setting.
    
    Args:
        data (list): List of dictionaries containing the data to write
        filename (str): CSV filename or database table name
        api_function_name (str, optional): Name of the API function for SQLite strategy selection
    """
    return DataExporter.save_data_to_output(data, filename, api_function_name)

def fetch_and_display_api_data(title, api_call, filename, sort_key=None, display_fields=None, **kwargs):
    """
    Fetches data using the provided API call, processes it (flattening, sorting, escaping),
    writes it to a CSV file, and displays it in a PrettyTable. Adds detailed logging.
    Handles API rate limiting (HTTP 429) by saving partial results and exiting gracefully.
    """

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
            print(f"! Exception occurred during API call: {e}")
            # Handle HTTP 429 (rate limit exceeded)
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code == 429:
                logging.warning("API rate limit (HTTP 429) reached. Saving partial results and exiting.")
                if rawdata:
                    DataExporter.save_data_to_output(rawdata, filename, api_function_name=api_call.__name__)
                    logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows) using {api_call.__name__} strategy.")
                logging.debug(f"EXIT: fetch_and_display_api_data - rate limited")
                return
            else:
                logging.debug(f"EXIT: fetch_and_display_api_data - API error")
                raise

        if rawdata is None:
            logging.warning(f"! No data returned from API for {title}. Skipping.")
            logging.debug(f"EXIT: fetch_and_display_api_data - no data")
            return

        logging.info(f"Fetched {len(rawdata)} raw records from API.")

        # Process and export data using DataExporter
        record_count = DataExporter.export_with_processing(rawdata, filename, sort_key=sort_key, api_function_name=api_call.__name__)
        print(f"! {len(rawdata)} records exported to {filename}")
        
        # Get processed data for display (reprocess for table display)
        data = [entry for entry in rawdata if isinstance(entry, dict)]
        if sort_key:
            data = sorted(data, key=lambda x: x.get(sort_key, ""))
        data = flatten_nested_fields_in_list(data)
        data = escape_multiline_strings_for_csv(data)
        
        # Determine all unique fields for table display
        fields = get_all_unique_dict_keys(data)
        logging.debug(f"Unique fields for table: {fields}")

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
        logging.error(f"! Error during data fetch for {title}: {e}")
        # Always save whatever data was collected so far
        if rawdata:
            DataExporter.save_data_to_output(rawdata, filename, api_function_name=api_call.__name__)
            logging.info(f"Partial results saved to {filename} ({len(rawdata)} rows) using {api_call.__name__} strategy.")
        logging.debug(f"EXIT: fetch_and_display_api_data - error")
        raise

def execute_with_connection_pool_management(work_items, worker_function, batch_description="items", retry_function=None):
    """
    Execute a list of work items using connection pool management and configurable threading.
    
    This is a reusable helper that any function can use to benefit from:
    - Connection-aware vs CPU-aware threading
    - Semaphore-based connection limiting 
    - Configurable batch processing
    - Automatic retry handling
    - Progress tracking
    
    Args:
        work_items: List of items to process
        worker_function: Function to call for each item. Should accept (item, connection_semaphore) parameters
        batch_description: Description for progress tracking (e.g., "devices", "sites")
        retry_function: Optional function to call for retry logic. Should accept (failed_items, connection_semaphore) parameters
        
    Returns:
        Tuple of (successful_results, failed_items)
    """
    
    if not work_items:
        logging.info(f"* No {batch_description} to process.")
        return [], []
        
    logging.info(f"* Processing {len(work_items)} {batch_description} with connection pool management...")
    
    # Determine threading strategy from environment variables
    if FAST_MODE_USE_CONNECTION_AWARE_THREADING:
        # Connection-aware threading: limit threads to connection pool capacity
        max_threads = FAST_MODE_MAX_CONCURRENT_CONNECTIONS
        threading_mode = "connection-aware"
        logging.info(f"! Connection-aware threading: Using {max_threads} threads (respects connection pool limit)")
    else:
        # CPU-aware threading: use maximum CPU threads available
        max_threads = os.cpu_count() or FAST_MODE_FALLBACK_THREADS
        threading_mode = "CPU-aware"
        logging.info(f"! CPU-aware threading: Using {max_threads} threads (maximum CPU utilization)")
    
    # Create a semaphore to limit concurrent API connections
    connection_semaphore = threading.Semaphore(FAST_MODE_MAX_CONCURRENT_CONNECTIONS)
    logging.info(f"* Connection pool protection: Maximum {FAST_MODE_MAX_CONCURRENT_CONNECTIONS} concurrent API calls")
    
    # Calculate optimal batch size using configurable devices per thread
    devices_per_thread = FAST_MODE_DEVICES_PER_THREAD
    batch_size = max_threads * devices_per_thread
    successful_results = []
    failed_items = []
    
    # Process items in batches
    for i in range(0, len(work_items), batch_size):
        try:
            batch = work_items[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(work_items) + batch_size - 1) // batch_size
            logging.info(f"! Processing batch {batch_number}/{total_batches} ({len(batch)} {batch_description}, ~{len(batch)/max_threads:.0f} per thread)")
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit batch tasks with connection semaphore
                future_to_item = {
                    executor.submit(worker_function, item, connection_semaphore): item 
                    for item in batch
                }
                batch_desc = f"Batch {batch_number}/{total_batches}"
                # Strategy: optionally avoid as_completed entirely using wait loop for stability
                use_wait_loop = True  # Default to True after repeated environment anomalies
                first_result_logged = False
                if use_wait_loop:
                    pending = set(future_to_item.keys())
                    pbar_total = len(pending)
                    with tqdm(total=pbar_total, desc=batch_desc, unit=batch_description.rstrip('s')) as pbar:
                        while pending:
                            done, pending = wait(pending, return_when=FIRST_COMPLETED)
                            for future in done:
                                item = future_to_item[future]
                                try:
                                    result = future.result()
                                    if result:
                                        successful_results.append(result)
                                        if not first_result_logged:
                                            logging.debug(f"! First future result type: {type(result)}")
                                            first_result_logged = True
                                    else:
                                        failed_items.append(item)
                                except Exception as e:
                                    logging.error(f"! Future exception for {batch_description.rstrip('s')} {item}: {e}")
                                    failed_items.append(item)
                                finally:
                                    try:
                                        pbar.update(1)
                                    except Exception as upd_err:
                                        logging.error(f"! Progress bar update failed: {upd_err}")
                else:
                    # Retained fallback path (not expected to be used now)
                    for future in as_completed(future_to_item):
                        item = future_to_item[future]
                        try:
                            result = future.result()
                            if result:
                                successful_results.append(result)
                            else:
                                failed_items.append(item)
                        except Exception as e:
                            logging.error(f"! Future exception for {batch_description.rstrip('s')} {item}: {e}")
                            failed_items.append(item)
        except Exception as batch_exc:
            # Log detailed context about the batch to aid debugging (e.g., dict+float arithmetic errors outside futures)
            logging.error(f"! Batch-level exception in execute_with_connection_pool_management: {batch_exc}")
            logging.error(f"! Batch context: i={i}, batch_size={batch_size}, max_threads={max_threads}, threading_mode={threading_mode}")
            try:
                import traceback as _tb2
                formatted = ''.join(_tb2.format_exception(type(batch_exc), batch_exc, batch_exc.__traceback__))
                for line in formatted.rstrip().splitlines():
                    logging.error(line)
            except Exception as trace_log_err:
                logging.error(f"! Failed to log batch exception traceback: {trace_log_err}")
            # Re-raise to allow outer handlers / global excepthook to capture as well
            raise
    
    # Handle retries if retry function is provided
    if failed_items and retry_function:
        logging.info(f"! Retrying {len(failed_items)} failed {batch_description}...")
        retry_results, still_failed = retry_function(failed_items, connection_semaphore)
        successful_results.extend(retry_results)
        failed_items = still_failed
    
    logging.info(f"! Processed {len(successful_results)} {batch_description} successfully, {len(failed_items)} failed")
    return successful_results, failed_items

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
    DataExporter.save_data_to_output(inventory, csv_filename)
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
            logging.error(" Invalid index.")
            return None

    # Try name selection
    if user_input in name_to_device:
        device_id = name_to_device[user_input].get("id")
        logging.info(f"User selected device by name: {user_input} (device_id: {device_id})")
        return device_id

    logging.error(" Device not found by name or index.")
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
    DataExporter.save_data_to_output(inventory, csv_filename)
    logging.info(f"Device inventory written to {csv_filename} ({len(inventory)} rows)")

    # Prepare PrettyTable for display
    table = PrettyTable()
    table.field_names = fields

    # Attempt to sort the table by 'model' if present
    if "model" in fields:
        try:
            table.sortby = "model"
        except Exception as e:
            logging.warning(f"! Could not sort table by 'model': {e}")

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
            print(f"! Selected site: {index_to_site[idx].get('name')} (ID: {site_id})")
            logging.info(f"User selected site by index: {idx} (site_id: {site_id})")
            return site_id
        else:
            print(" Invalid index.")
            logging.warning(f"Invalid site index entered: {idx}")
            return None

    # Try name selection
    if user_input in name_to_site:
        site_id = name_to_site[user_input].get("id")
        print(f"! Selected site: {user_input} (ID: {site_id})")
        logging.info(f"User selected site by name: {user_input} (site_id: {site_id})")
        return site_id

    print(" Site not found by name or index.")
    logging.warning(f"Site not found by name or index: {user_input}")
    return None

def prompt_and_log_site_selection():
    """
    Prompts the user to select a site from the CSV list and logs the selection.
    """
    logging.info("Prompting user to select a site from SiteList.csv...")
    site_id = prompt_select_site_id_from_csv()
    if site_id:
        logging.info(f"! Selected site ID: {site_id}")
        # You can store or use the selected site_id as needed here
    else:
        logging.error(" No site selected. User may have entered an invalid value or cancelled the prompt.")

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
            logging.warning(f"! No data returned from API for {data_type} at site {site_name}. Skipping.")
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
        DataExporter.save_data_to_output(data, filename)
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
        logging.error(f"! Error during site {data_type} export for {site_name}: {e}")
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
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("open org alarms export", hours)
    logging.info(f"Starting search for all open org alarms in the past {hours} hours...")
    
    try:
        fetch_and_display_api_data(
            title="Search all Org Alarms:",
            api_call=mistapi.api.v1.orgs.alarms.searchOrgAlarms,
            filename="OrgAlarms.csv",
            limit=1000,
            duration=f"{hours}h",
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
    # Dynamic lookback window (24h normal / 1h test by default)
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("recent device events export", hours)
    # Use explicit duration parameter rather than start/end to avoid mistapi defaulting to duration=1d
    # If we provided only start/end previously, the library still appended duration=1d in the request.
    # Explicitly passing duration ensures correct reduced window in test mode.
    duration_param = f"{hours}h"
    response = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
        apisession,
        org_id,
        device_type="all",
        limit=1000,
        duration=duration_param
    )
    # Retrieve all paginated results
    rawdata = mistapi.get_all(response=response, mist_session=apisession)
    events = rawdata
    logging.info(f"Fetched {len(events)} device events from the past {hours} hours (duration={duration_param}).")
    # Write the events to a CSV file
    DataExporter.save_data_to_output(events, "OrgDeviceEvents.csv")
    logging.info(f"Device events written to OrgDeviceEvents.csv ({len(events)} rows).")
    print(f"! {len(events)} device events exported to OrgDeviceEvents.csv")
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
    DataExporter.save_data_to_output(events, "OrgDeviceEvents_52w.csv")
    logging.info(" All org device events (52w) exported to OrgDeviceEvents_52w.csv.")

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
            # Caller explicitly provided duration; honor it.
            kwargs["duration"] = duration
            logging.info(f"Exporting audit logs for duration: {duration}")
        elif not full_history:
            # Use dynamic hour window and pass duration directly to avoid mistapi auto-appending duration=1d
            hours = get_dynamic_lookback_hours(24, 1)
            log_dynamic_lookback("audit logs export", hours)
            kwargs["duration"] = f"{hours}h"
            logging.info(f"Exporting only last {hours} hours of audit logs (duration={hours}h).")
        else:
            kwargs["start"] = 0
            logging.info("Exporting full audit log history (start=0).")

        # Call the API and fetch all pages
        logging.debug(f"Making API call with parameters: {kwargs}")
        response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(apisession, org_id, **kwargs)
        rawdata = mistapi.get_all(response=response, mist_session=apisession)

        if not rawdata:
            logging.warning(" No audit logs returned from API.")
            logging.debug("EXIT: export_audit_logs_to_csv - no data")
            return

        # Flatten and sanitize for CSV
        data = flatten_nested_fields_in_list(rawdata)
        data = escape_multiline_strings_for_csv(data)
        DataExporter.save_data_to_output(data, "OrgAuditLogs.csv")
        print(f"! {len(data)} audit logs exported to OrgAuditLogs.csv")
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
        logging.info(f"! Using cached {output_file} (already exists)")
        print(f"! Using cached {output_file} (already exists)")
        return

    logging.info("Fetching all sites using the 'list' sites API endpoint...")
    print("Fetching all sites using the 'list' sites API endpoint...")
    org_id = get_cached_or_prompted_org_id()
    sites = fetch_all_sites_with_limit(org_id)
    if not sites:
        logging.warning(" No sites returned from API.")
        print(" No sites returned from API.")
        return
    # Flatten and sanitize for CSV
    sites = flatten_nested_fields_in_list(sites)
    sites = escape_multiline_strings_for_csv(sites)
    DataExporter.save_data_to_output(sites, output_file)
    logging.info(f"! Sites exported to {output_file}")
    print(f"! Sites exported to {output_file}")

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

def export_device_stats_to_csv(fast: bool = False):
    """Export statistics for all devices in the organization to `OrgDeviceStats.csv`.

    Fast Mode Behavior:
        - If `fast` is True and a fresh CSV (mtime < CSV_FRESHNESS_MINUTES) exists, skip API call (cache hit).
        - Falls back to normal fetch otherwise (no change to data semantics).
    SECURITY: Read-only operation; safe to cache.
    """
    output_file = "OrgDeviceStats.csv"
    if fast and os.path.exists(output_file):
        try:
            mtime = os.path.getmtime(output_file)
            age_minutes = (time.time() - mtime) / 60.0
            if age_minutes < CSV_FRESHNESS_MINUTES:
                logging.info(f" Fast mode cache hit: {output_file} is fresh ({age_minutes:.1f}m < {CSV_FRESHNESS_MINUTES}m); skipping fetch.")
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")
                return
        except Exception as e:  # pragma: no cover - defensive
            logging.debug(f"Fast mode freshness check failed for {output_file}: {e}")
    logging.info("Starting export of organization device statistics...")
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("org device statistics export", hours)
    fetch_and_display_api_data(
        title="Org Device Stats:",
        api_call=mistapi.api.v1.orgs.stats.listOrgDevicesStats,
        filename=output_file,
        sort_key="type",
        type="all",
        duration=f"{hours}h",
        limit=1000
    )

def export_device_port_stats_to_csv(fast: bool = False):
    """Export port-level statistics for all switches and gateways to `OrgDevicePortStats.csv`.

    Fast Mode Behavior:
        - Skips API call if recent CSV exists (freshness based on `CSV_FRESHNESS_MINUTES`).
        - Otherwise identical behavior.
    SECURITY: Read-only aggregation; caching is safe.
    """
    output_file = "OrgDevicePortStats.csv"
    if fast and os.path.exists(output_file):
        try:
            mtime = os.path.getmtime(output_file)
            age_minutes = (time.time() - mtime) / 60.0
            if age_minutes < CSV_FRESHNESS_MINUTES:
                logging.info(f" Fast mode cache hit: {output_file} is fresh ({age_minutes:.1f}m < {CSV_FRESHNESS_MINUTES}m); skipping fetch.")
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")
                return
        except Exception as e:  # pragma: no cover
            logging.debug(f"Fast mode freshness check failed for {output_file}: {e}")
    logging.info("Starting export of organization device port statistics...")
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("org device port statistics export", hours)
    fetch_and_display_api_data(
        title="Org Device Port Stats:",
        api_call=mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
        filename=output_file,
        sort_key="mac",
        duration=f"{hours}h",
        limit=1000
    )

def export_vpn_peer_stats_to_csv(fast: bool = False):
    """Export VPN peer path statistics to `OrgVPNPeerStats.csv`.

    Fast Mode Behavior:
        - Skip API call on fresh cache (age < `CSV_FRESHNESS_MINUTES`).
        - Normal fetch otherwise.
    SECURITY: Read-only; safe to cache.
    """
    output_file = "OrgVPNPeerStats.csv"
    if fast and os.path.exists(output_file):
        try:
            mtime = os.path.getmtime(output_file)
            age_minutes = (time.time() - mtime) / 60.0
            if age_minutes < CSV_FRESHNESS_MINUTES:
                logging.info(f" Fast mode cache hit: {output_file} is fresh ({age_minutes:.1f}m < {CSV_FRESHNESS_MINUTES}m); skipping fetch.")
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")
                return
        except Exception as e:  # pragma: no cover
            logging.debug(f"Fast mode freshness check failed for {output_file}: {e}")
    logging.info("Starting export of organization VPN peer path statistics...")
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("org vpn peer path statistics export", hours)
    fetch_and_display_api_data(
        title="Org VPN Peer Stats:",
        api_call=mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
        filename=output_file,
        sort_key="mac",
        duration=f"{hours}h",
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
    print("Export Virtual Chassis Information:")
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
            DataExporter.save_data_to_output(sanitized, filename)
            
            logging.info(f"! Virtual chassis information exported to {filename}")
            
            # Display summary
            if sanitized:
                print(f"\n!! Virtual Chassis Summary for {device_name}:")
                print(f"   * Records exported: {len(sanitized)}")
                if 'members' in sanitized[0]:
                    print(f"   * VC members: {sanitized[0].get('members', 'N/A')}")
                if 'preprovisioned' in sanitized[0]:
                    print(f"   * Preprovisioned: {sanitized[0].get('preprovisioned', 'N/A')}")
                print(f"   * Data saved to: {filename}")
        else:
            logging.warning(f"! No virtual chassis data returned for device {device_name}")
            print(f"! No virtual chassis data found for device {device_name}")
            
    except Exception as e:
        logging.error(f"! Failed to export virtual chassis information: {e}")
        print(f"! Failed to export virtual chassis information: {e}")

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
    
    logging.info(" Organization templates export completed")

def export_site_clients_to_csv():
    """
    Export client statistics for a specific site to SiteClients.csv.
    Prompts user to select a site and exports connected client information.
    """
    print("Site Client Statistics:")
    logging.info("Starting export of site client statistics...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    sites = fetch_all_sites_with_limit(org_id)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting client statistics for site: {site_name}")
    
    # Fetch site client stats directly
    try:
        response = mistapi.api.v1.sites.stats.searchSiteClientStats(apisession, site_id, limit=1000)
        rawdata = mistapi.get_all(response=response, mist_session=apisession)
        
        if rawdata:
            # Process and save data
            flattened_data = flatten_nested_fields_in_list(rawdata)
            sanitized_data = escape_multiline_strings_for_csv(flattened_data)
            filename = f"SiteClients_{site_name.replace(' ', '_')}.csv"
            DataExporter.save_data_to_output(sanitized_data, filename)
            print(f"! {len(rawdata)} client records exported to {filename}")
        else:
            print("! No client data found for this site")
    except Exception as e:
        logging.error(f"Error fetching client stats for site {site_name}: {e}")
        print(f"! Error fetching client data: {e}")

def export_site_devices_to_csv():
    """
    Export device list for a specific site to SiteDevices.csv.
    Prompts user to select a site and exports device information.
    """
    print("Site Device List:")
    logging.info("Starting export of site device list...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    sites = fetch_all_sites_with_limit(org_id)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting device list for site: {site_name}")
    
    # Fetch site devices directly
    try:
        response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all")
        rawdata = getattr(response, 'data', [])
        
        if rawdata:
            # Process and save data
            flattened_data = flatten_nested_fields_in_list(rawdata)
            sanitized_data = escape_multiline_strings_for_csv(flattened_data)
            filename = f"SiteDevices_{site_name.replace(' ', '_')}.csv"
            DataExporter.save_data_to_output(sanitized_data, filename)
            print(f"! {len(rawdata)} devices exported to {filename}")
        else:
            print("! No devices found for this site")
    except Exception as e:
        logging.error(f"Error fetching devices for site {site_name}: {e}")
        print(f"! Error fetching device data: {e}")

def export_site_device_stats_to_csv():
    """
    Export device statistics for a specific site to SiteDeviceStats.csv.
    Prompts user to select a site and exports device statistics.
    """
    print("Site Device Statistics:")
    logging.info("Starting export of site device statistics...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for display
    sites = fetch_all_sites_with_limit(org_id)
    site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    
    logging.info(f"Exporting device statistics for site: {site_name}")
    
    # Fetch site device stats directly
    try:
        response = mistapi.api.v1.sites.stats.listSiteDevicesStats(apisession, site_id, type="all", limit=1000)
        rawdata = mistapi.get_all(response=response, mist_session=apisession)
        
        if rawdata:
            # Process and save data
            flattened_data = flatten_nested_fields_in_list(rawdata)
            sanitized_data = escape_multiline_strings_for_csv(flattened_data)
            filename = f"SiteDeviceStats_{site_name.replace(' ', '_')}.csv"
            DataExporter.save_data_to_output(sanitized_data, filename)
            print(f"! {len(rawdata)} device stats exported to {filename}")
        else:
            print("! No device statistics found for this site")
    except Exception as e:
        logging.error(f"Error fetching device stats for site {site_name}: {e}")
        print(f"! Error fetching device statistics: {e}")

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
    """Export security policies (OrgSecurityPolicies.csv), security intelligence profiles (OrgSecIntelProfiles.csv), and site rogue data (OrgRogueData.csv)."""
    print("Export Organization Security Data:")
    logging.info("Starting export of organization security policies, intelligence profiles, and rogue data...")
    org_id = get_cached_or_prompted_org_id()

    # 1. Security Policies
    policies = []
    try:
        logging.info("Fetching organization security policies (secpolicies)...")
        resp = mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies(apisession, org_id, limit=1000)
        policies = mistapi.get_all(response=resp, mist_session=apisession) or []
        logging.debug(f"Security policies fetched: {len(policies)}")
    except Exception as e:
        logging.warning(f"Failed to fetch security policies: {e}")
    if policies:
        processed = flatten_nested_fields_in_list(policies)
        processed = escape_multiline_strings_for_csv(processed)
        DataExporter.save_data_to_output(processed, "OrgSecurityPolicies.csv")
        print(f"! {len(processed)} security policies exported to OrgSecurityPolicies.csv")
        logging.info(f"Exported {len(processed)} security policies to OrgSecurityPolicies.csv")
    else:
        print("! 0 security policies exported to OrgSecurityPolicies.csv (no policies found)")
        logging.warning("No data to export for OrgSecurityPolicies.csv (zero policies returned).")
        DataExporter.save_data_to_output([], "OrgSecurityPolicies.csv")

    # 2. Security Intelligence Profiles (use available endpoint)
    secintel_profiles = []
    try:
        logging.info("Fetching organization security intelligence profiles...")
        resp_secintel = mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles(apisession, org_id)
        secintel_profiles = mistapi.get_all(response=resp_secintel, mist_session=apisession) or []
        logging.debug(f"Security intelligence profiles fetched: {len(secintel_profiles)}")
    except Exception as e:
        logging.warning(f"Failed to fetch security intelligence profiles: {e}")
    if secintel_profiles:
        processed_si = flatten_nested_fields_in_list(secintel_profiles)
        processed_si = escape_multiline_strings_for_csv(processed_si)
        DataExporter.save_data_to_output(processed_si, "OrgSecIntelProfiles.csv")
        print(f"! {len(processed_si)} security intelligence profiles exported to OrgSecIntelProfiles.csv")
        logging.info(f"Exported {len(processed_si)} security intelligence profiles to OrgSecIntelProfiles.csv")
    else:
        print("! 0 security intelligence profiles exported to OrgSecIntelProfiles.csv (no profiles found)")
        logging.warning("No data to export for OrgSecIntelProfiles.csv (zero profiles returned).")
        DataExporter.save_data_to_output([], "OrgSecIntelProfiles.csv")

    # 3. Rogue Events (site-level via insights)
    logging.info("Fetching rogue APs and clients from all sites via insights...")
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    all_rogue_aps = []
    all_rogue_clients = []
    try:
        site_list_path = get_csv_file_path("SiteList.csv")
        with open(site_list_path, mode="r", encoding="utf-8") as f:
            sites = list(csv.DictReader(f))
        for site in tqdm(sites, desc="Sites", unit="site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unknown Site")
            if not site_id:
                continue
            try:
                # Get rogue APs
                response_aps = mistapi.api.v1.sites.insights.listSiteRogueAPs(apisession, site_id, duration="7d", limit=1000)
                site_rogue_aps = mistapi.get_all(response=response_aps, mist_session=apisession) or []
                for ap in site_rogue_aps:
                    ap["site_id"] = site_id
                    ap["site_name"] = site_name
                    ap["rogue_type"] = "AP"
                all_rogue_aps.extend(site_rogue_aps)
                
                # Get rogue clients  
                response_clients = mistapi.api.v1.sites.insights.listSiteRogueClients(apisession, site_id, duration="7d", limit=1000)
                site_rogue_clients = mistapi.get_all(response=response_clients, mist_session=apisession) or []
                for client in site_rogue_clients:
                    client["site_id"] = site_id
                    client["site_name"] = site_name
                    client["rogue_type"] = "Client"
                all_rogue_clients.extend(site_rogue_clients)
                
                logging.info(f"! Fetched {len(site_rogue_aps)} rogue APs and {len(site_rogue_clients)} rogue clients from site: {site_name}")
            except Exception as e:
                logging.warning(f"! Failed to fetch rogue data from site {site_name}: {e}")
                continue
            time.sleep(0.2)
    except Exception as e:
        logging.error(f"Failed to process sites for rogue data: {e}")

    # Combine all rogue data
    all_rogue_data = all_rogue_aps + all_rogue_clients

    if all_rogue_data:
        processed_r = flatten_nested_fields_in_list(all_rogue_data)
        processed_r = escape_multiline_strings_for_csv(processed_r)
        DataExporter.save_data_to_output(processed_r, "OrgRogueData.csv")
        print(f"! {len(processed_r)} rogue devices exported to OrgRogueData.csv")
        logging.info(f"Exported {len(processed_r)} rogue devices to OrgRogueData.csv")
    else:
        print("! 0 rogue devices exported to OrgRogueData.csv (no rogue devices found)")
        logging.info("No rogue devices found across all sites (OrgRogueData.csv written empty).")
        DataExporter.save_data_to_output([], "OrgRogueData.csv")

    print("Security data export completed (3 files generated)")
    logging.info("Completed security policies, intelligence profiles, and rogue data export aggregate.")

# ==============================
# INSIGHTS API FUNCTIONS - Organization & Site Analytics
# ==============================

def export_org_sle_metrics_to_csv():
    """Export organization-wide SLE (Service Level Experience) metrics to OrgSLEMetrics.csv."""
    print("Export Organization SLE Metrics:")
    logging.info("Starting export of organization SLE metrics...")
    org_id = get_cached_or_prompted_org_id()
    
    # Use the actual SLE service categories supported by the Mist platform
    # These are the core service level experience domains
    sle_categories = [
        "wifi",               # WiFi/wireless SLE metrics - CONFIRMED WORKING
        "wan",                # WAN connectivity SLE metrics - CONFIRMED WORKING  
        "wired",              # Wired network SLE metrics - CONFIRMED WORKING
    ]
    
    # Try to get organization-level SLE data using specialized SLE metrics
    # Based on what actually worked in option 83, try SLE-specific aggregation metrics
    org_sle_specialized_metrics = [
        "summary",            # Org summary SLE data - from const insights
        "sites-sle",          # Sites SLE aggregation - from const insights  
        "worst-sites-by-sle", # Worst performing sites SLE analysis
    ]
    
    all_sle_data = []
    metrics_retrieved = 0
    metrics_failed = 0
    
    print(f"! Retrieving organization SLE data using {len(sle_categories)} service categories...")
    print(f"! Also attempting {len(org_sle_specialized_metrics)} specialized SLE aggregation metrics...")
    
    try:
        # First, try using the specialized SLE aggregation metrics with getOrgSle
        for metric in org_sle_specialized_metrics:
            try:
                logging.debug(f"Attempting to retrieve specialized SLE metric: {metric}")
                
                # For metrics that analyze sites by SLE, use getOrgSitesSle instead of getOrgSle
                if "worst-sites" in metric or "sites-sle" in metric:
                    # These metrics require site-level SLE data analysis
                    for sle_category in sle_categories:
                        try:
                            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(
                                apisession, 
                                org_id, 
                                sle=sle_category,
                                duration="7d",
                                limit=1000
                            )
                            sites_sle_data = mistapi.get_all(response=response, mist_session=apisession) or []
                            
                            if sites_sle_data:
                                # Create an aggregated metric result from sites data
                                aggregated_result = {
                                    'sle_metric_type': f"{metric}_{sle_category}",
                                    'org_id': org_id,
                                    'sle_category': sle_category,
                                    'data_source': 'org_sites_sle_aggregated',
                                    'total_sites': len(sites_sle_data),
                                    'sites_analyzed': sites_sle_data,
                                    'metric_name': metric
                                }
                                
                                # For worst-sites metrics, we could add analysis here
                                if "worst-sites" in metric:
                                    aggregated_result['analysis_type'] = 'worst_sites_identification'
                                
                                all_sle_data.append(aggregated_result)
                                metrics_retrieved += 1
                                logging.debug(f"Successfully retrieved sites SLE data for metric analysis: {metric} with SLE: {sle_category} ({len(sites_sle_data)} sites)")
                            else:
                                logging.debug(f"No sites SLE data available for metric: {metric} with SLE: {sle_category}")
                        except Exception as sites_error:
                            logging.debug(f"Failed to get sites SLE data for metric '{metric}' with SLE '{sle_category}': {sites_error}")
                            continue
                else:
                    # For other metrics, call getOrgSle directly
                    response = mistapi.api.v1.orgs.insights.getOrgSle(
                        apisession, 
                        org_id, 
                        metric,
                        duration="7d"
                    )
                    sle_data = getattr(response, 'data', response) or {}
                    
                    if sle_data:
                        sle_data['sle_metric_type'] = metric
                        sle_data['org_id'] = org_id
                        sle_data['data_source'] = 'org_sle_specialized'
                        all_sle_data.append(sle_data)
                        metrics_retrieved += 1
                        logging.debug(f"Successfully retrieved specialized SLE data for metric: {metric}")
                    else:
                        logging.debug(f"No data available for specialized SLE metric: {metric}")
                        metrics_failed += 1
                    
            except Exception as metric_error:
                metrics_failed += 1
                logging.debug(f"Failed to get specialized SLE data for metric '{metric}': {metric_error}")
                continue
        
        # Second, get aggregated SLE data for each service category using getOrgSitesSle 
        # but process it as organization-wide aggregated data
        for sle_category in sle_categories:
            try:
                logging.debug(f"Attempting to retrieve aggregated SLE data for category: {sle_category}")
                response = mistapi.api.v1.orgs.insights.getOrgSitesSle(
                    apisession, 
                    org_id, 
                    sle=sle_category, 
                    duration="7d", 
                    limit=1000
                )
                sites_sle_data = mistapi.get_all(response=response, mist_session=apisession) or []
                
                if sites_sle_data:
                    # Create an organization-level aggregation from sites data
                    org_aggregated = {
                        'sle_category': sle_category,
                        'org_id': org_id,
                        'data_source': 'org_aggregated_from_sites',
                        'total_sites': len(sites_sle_data),
                        'sites_data': sites_sle_data  # Include detailed sites for analysis
                    }
                    
                    # Calculate organization-level aggregations if possible
                    if sites_sle_data:
                        # Add summary statistics
                        org_aggregated['summary_calculated'] = True
                        
                    all_sle_data.append(org_aggregated)
                    metrics_retrieved += 1
                    logging.debug(f"Successfully aggregated SLE data for {len(sites_sle_data)} sites in category: {sle_category}")
                else:
                    logging.debug(f"No sites SLE data available for category: {sle_category}")
                    metrics_failed += 1
                    
            except Exception as category_error:
                metrics_failed += 1
                logging.debug(f"Failed to get SLE data for category '{sle_category}': {category_error}")
                continue
        
        # Report results
        print(f"! SLE data retrieval completed: {metrics_retrieved} successful, {metrics_failed} failed")
        logging.info(f"Org SLE data: {metrics_retrieved} retrieved successfully, {metrics_failed} failed")
        
        if all_sle_data:
            # Flatten and process the data for CSV export
            processed = flatten_nested_fields_in_list(all_sle_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, "OrgSLEMetrics.csv")
            print(f"! {metrics_retrieved} organization SLE data sources exported to OrgSLEMetrics.csv")
            logging.info(f"Exported {len(processed)} org SLE data points from {metrics_retrieved} sources to OrgSLEMetrics.csv")
        else:
            print("! 0 organization SLE metrics exported to OrgSLEMetrics.csv (no data available)")
            logging.warning("No org SLE data available - all sources failed or returned empty")
            DataExporter.save_data_to_output([], "OrgSLEMetrics.csv")
            
    except Exception as e:
        print(f"! Error exporting organization SLE metrics: {e}")
        logging.error(f"Failed to export org SLE metrics: {e}")
        DataExporter.save_data_to_output([], "OrgSLEMetrics.csv")

def export_org_sites_sle_summary_to_csv():
    """Export SLE summary metrics for all sites in the organization to OrgSitesSLESummary.csv."""
    print("Export Organization Sites SLE Summary:")
    logging.info("Starting export of sites SLE summary...")
    org_id = get_cached_or_prompted_org_id()
    
    # SLE types to export
    sle_types = ["wifi", "wired", "wan"]
    all_sites_sle_data = []
    
    for sle_type in sle_types:
        try:
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(apisession, org_id, sle=sle_type, duration="7d", limit=1000)
            sites_sle_data = mistapi.get_all(response=response, mist_session=apisession) or []
            
            for site_data in sites_sle_data:
                # Add SLE type identifier to the data
                site_data['sle_type'] = sle_type
                all_sites_sle_data.append(site_data)
            
            logging.debug(f"Retrieved SLE data for {len(sites_sle_data)} sites with SLE type: {sle_type}")
        except Exception as e:
            logging.warning(f"Failed to get sites SLE data for type {sle_type}: {e}")
            continue
    
    if all_sites_sle_data:
        processed = flatten_nested_fields_in_list(all_sites_sle_data)
        processed = escape_multiline_strings_for_csv(processed)
        DataExporter.save_data_to_output(processed, "OrgSitesSLESummary.csv")
        print(f"! {len(processed)} sites SLE summary exported to OrgSitesSLESummary.csv")
        logging.info(f"Exported {len(processed)} sites SLE summary to OrgSitesSLESummary.csv")
    else:
        print("! 0 sites SLE summary exported to OrgSitesSLESummary.csv (no data available)")
        logging.warning("No sites SLE data available for organization")
        DataExporter.save_data_to_output([], "OrgSitesSLESummary.csv")

def export_site_insight_metrics_to_csv():
    """Export general insight metrics for a selected site to SiteInsightMetrics_[SiteName].csv."""
    print("Export Site Insight Metrics:")
    logging.info("Starting export of site insight metrics...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name or site_id)
    filename = f"SiteInsightMetrics_{sanitized_site_name}.csv"
    
    # First, refresh the available metrics from the API
    print("! Refreshing available insight metrics from Mist API...")
    export_const_insight_metrics_to_csv()
    
    # Get all metrics that support "site" scope
    site_metrics = get_insight_metrics_by_scope("site")
    
    if not site_metrics:
        print("! No metrics found for site scope. Check ConstInsightMetrics.csv file.")
        logging.error("No site-scope metrics found in const insight metrics")
        DataExporter.save_data_to_output([], filename)
        return
    
    all_insight_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(site_metrics)} different site insight metrics...")
    
    try:
        for metric in site_metrics:
            try:
                response = mistapi.api.v1.sites.insights.getSiteInsightMetrics(apisession, site_id, metric)
                insight_data = getattr(response, 'data', response) or {}
                
                if insight_data:
                    # Add metric type identifier to each data point
                    insight_data['metric_type'] = metric
                    insight_data['site_id'] = site_id
                    insight_data['site_name'] = site_name
                    all_insight_data.append(insight_data)
                    metrics_retrieved += 1
                    logging.debug(f"Retrieved site insight data for metric: {metric}")
                else:
                    logging.debug(f"No data available for metric: {metric}")
            except Exception as e:
                logging.debug(f"Failed to get site insight data for metric {metric}: {e}")
                continue
        
        if all_insight_data:
            processed = flatten_nested_fields_in_list(all_insight_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} site insight metrics exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} site insight metrics for {site_name} to {filename}")
        else:
            print(f"! 0 insight metrics exported to {filename} (no data available)")
            logging.warning(f"No insight data available for site {site_name}")
            DataExporter.save_data_to_output([], filename)
    except Exception as e:
        print(f"! Error exporting site insight metrics: {e}")
        logging.error(f"Failed to export site insight metrics for {site_name}: {e}")
        DataExporter.save_data_to_output([], filename)

def export_site_client_insights_to_csv():
    """Export client-specific insight metrics for a selected site to SiteClientInsights_[SiteName].csv."""
    print("Export Site Client Insights:")
    logging.info("Starting export of site client insights...")
    
    # First, refresh the available metrics from the API
    print("! Refreshing available insight metrics from Mist API...")
    export_const_insight_metrics_to_csv()
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get site name for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name or site_id)
    
    # Get available clients for the site to help user selection
    try:
        response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(apisession, site_id)
        clients = mistapi.get_all(response=response, mist_session=apisession) or []
        
        if clients:
            print(f"\n! Found {len(clients)} clients at site {site_name}")
            print("Recent clients (showing first 5):")
            for i, client in enumerate(clients[:5]):
                mac = client.get('mac', 'Unknown')
                hostname = client.get('hostname', 'Unknown')
                last_seen = client.get('last_seen', 'Unknown')
                print(f"  [{i}] MAC: {mac}, Hostname: {hostname}, Last seen: {last_seen}")
        else:
            print(f"! No clients found at site {site_name}")
    except Exception as e:
        logging.warning(f"Could not retrieve client list: {e}")
        clients = []
    
    # Prompt for client MAC address
    print("\nEnter client MAC address or index number (or press Enter to skip):")
    client_input = input("Client MAC/Index: ").strip()
    
    if not client_input:
        print("! No client input provided. Skipping client insights export.")
        return
    
    # Check if input is a numeric index
    client_mac = None
    if client_input.isdigit():
        try:
            index = int(client_input)
            if 0 <= index < len(clients):
                client_mac = clients[index].get('mac', '')
                print(f"! Selected client by index: {client_mac}")
            else:
                print(f"! Invalid index {index}. Must be between 0 and {len(clients)-1}")
                return
        except (ValueError, IndexError):
            print(f"! Invalid index: {client_input}")
            return
    else:
        # Treat as MAC address
        client_mac = client_input
    
    if not client_mac:
        print("! Could not determine client MAC address.")
        return
    
    filename = f"SiteClientInsights_{sanitized_site_name}_{client_mac.replace(':', '')}.csv"
    
    # Get all metrics that support "client" scope
    client_metrics = get_insight_metrics_by_scope("client")
    
    if not client_metrics:
        print("! No metrics found for client scope. Check ConstInsightMetrics.csv file.")
        logging.error("No client-scope metrics found in const insight metrics")
        DataExporter.save_data_to_output([], filename)
        return
    
    all_client_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(client_metrics)} different client insight metrics for {client_mac}...")
    
    try:
        for metric in client_metrics:
            try:
                response = mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient(apisession, site_id, client_mac, metric)
                client_insight_data = getattr(response, 'data', response) or {}
                
                if client_insight_data:
                    # Add metric type identifier to each data point
                    client_insight_data['metric_type'] = metric
                    client_insight_data['site_id'] = site_id
                    client_insight_data['site_name'] = site_name
                    client_insight_data['client_mac'] = client_mac
                    all_client_data.append(client_insight_data)
                    metrics_retrieved += 1
                    logging.debug(f"Retrieved client insight data for metric: {metric}")
                else:
                    logging.debug(f"No data available for client metric: {metric}")
            except Exception as e:
                logging.debug(f"Failed to get client insight data for metric {metric}: {e}")
                continue
        
        if all_client_data:
            processed = flatten_nested_fields_in_list(all_client_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} client insight metrics exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} client insight metrics for {client_mac} at {site_name} to {filename}")
        else:
            print(f"! 0 client insights exported to {filename} (no data available)")
            logging.warning(f"No client insight data available for {client_mac} at {site_name}")
            DataExporter.save_data_to_output([], filename)
    except Exception as e:
        print(f"! Error exporting client insights: {e}")
        logging.error(f"Failed to export client insights for {client_mac} at {site_name}: {e}")
        DataExporter.save_data_to_output([], filename)

def export_site_device_insights_to_csv():
    """Export device-specific insight metrics for a selected site to SiteDeviceInsights_[SiteName].csv."""
    print("Export Site Device Insights:")
    logging.info("Starting export of site device insights...")
    
    # First, refresh the available metrics from the API
    print("! Refreshing available insight metrics from Mist API...")
    export_const_insight_metrics_to_csv()
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        logging.error("No site selected. Exiting.")
        return
    
    # Get device selection
    device_id = prompt_device_selection(site_id)
    if not device_id:
        logging.error("No device selected. Exiting.")
        return
    
    # Get site and device names for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    try:
        response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all")
        devices = mistapi.get_all(response=response, mist_session=apisession)
        device = next((dev for dev in devices if dev["id"] == device_id), None)
        device_name = device["name"] if device else device_id
        device_mac = device["mac"] if device else None
    except:
        device_name = device_id
        device_mac = None
    
    if not device_mac:
        print(f"! Error: Could not find MAC address for device {device_name}")
        logging.error(f"Could not find MAC address for device {device_id}")
        return
    
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name or site_id)
    sanitized_device_name = EnhancedSSHRunner.sanitize_filename(device_name or device_id)
    filename = f"SiteDeviceInsights_{sanitized_site_name}_{sanitized_device_name}.csv"
    
    # Get all metrics that support "device" scope
    device_metrics = get_insight_metrics_by_scope("device")
    
    if not device_metrics:
        print("! No metrics found for device scope. Check ConstInsightMetrics.csv file.")
        logging.error("No device-scope metrics found in const insight metrics")
        DataExporter.save_data_to_output([], filename)
        return
    
    all_device_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(device_metrics)} different device insight metrics for {device_name}...")
    
    try:
        for metric in device_metrics:
            try:
                response = mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(apisession, site_id, metric, device_mac)
                device_insight_data = getattr(response, 'data', response) or {}
                
                if device_insight_data:
                    # Add metric type identifier to each data point
                    device_insight_data['metric_type'] = metric
                    device_insight_data['site_id'] = site_id
                    device_insight_data['site_name'] = site_name
                    device_insight_data['device_id'] = device_id
                    device_insight_data['device_name'] = device_name
                    device_insight_data['device_mac'] = device_mac
                    all_device_data.append(device_insight_data)
                    metrics_retrieved += 1
                    logging.debug(f"Retrieved device insight data for metric: {metric}")
                else:
                    logging.debug(f"No data available for device metric: {metric}")
            except Exception as e:
                logging.debug(f"Failed to get device insight data for metric {metric}: {e}")
                continue
        
        if all_device_data:
            processed = flatten_nested_fields_in_list(all_device_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} device insight metrics exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} device insight metrics for {device_name} at {site_name} to {filename}")
        else:
            print(f"! 0 device insights exported to {filename} (no data available)")
            logging.warning(f"No device insight data available for {device_name} at {site_name}")
            DataExporter.save_data_to_output([], filename)
    except Exception as e:
        print(f"! Error exporting device insights: {e}")
        logging.error(f"Failed to export device insights for {device_name} at {site_name}: {e}")
        DataExporter.save_data_to_output([], filename)

def export_all_const_definitions_to_csv():
    """Export all available const definitions from the Mist API to individual CSV files.
    
    Implements fully dynamic discovery and smart caching:
    - Automatically discovers all available const endpoints from mistapi library using introspection
    - Dynamically inspects each const module to find the correct function names
    - Checks if each Const{EndpointName}.csv exists and is fresh (< 24 hours old)
    - If fresh file exists, skips API call for that endpoint
    - If file is missing or stale (>= 24 hours old), fetches fresh data from API
    - Creates comprehensive const definition files for all available endpoints
    """
    import os
    import time
    import importlib
    import inspect
    import pkgutil
    from datetime import datetime, timedelta
    
    print("Export All Available Const Definitions (Dynamic Discovery):")
    logging.info("Starting comprehensive dynamic export of all const definitions...")
    
    cache_max_age_hours = 24  # Consider file stale after 24 hours
    
    try:
        # Dynamically discover all const modules in mistapi.api.v1.const
        import mistapi.api.v1.const as const_package
        
        discovered_endpoints = {}
        
        print("! Dynamically discovering const endpoints from mistapi library...")
        logging.info("Starting dynamic discovery of const endpoints")
        
        # Walk through all submodules in the const package
        for importer, modname, ispkg in pkgutil.iter_modules(const_package.__path__, const_package.__name__ + "."):
            if not ispkg:  # Only process non-package modules
                try:
                    # Extract just the endpoint name (last part after the dots)
                    endpoint_name = modname.split('.')[-1]
                    
                    # Skip if this looks like a private module
                    if endpoint_name.startswith('_'):
                        continue
                    
                    print(f"  ! Inspecting const module: {endpoint_name}")
                    
                    # Import the module dynamically
                    module = importlib.import_module(modname)
                    
                    # Find all callable functions in the module that look like API calls
                    functions = []
                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj) and not name.startswith('_'):
                            # Check if function takes a mist_session parameter (API call signature)
                            sig = inspect.signature(obj)
                            param_names = list(sig.parameters.keys())
                            if ('mist_session' in param_names or 'apisession' in param_names) and len(param_names) >= 1:
                                functions.append(name)
                                logging.debug(f"Found potential API function in {endpoint_name}: {name}{sig}")
                    
                    if functions:
                        # For const endpoints, we typically want the "list" function
                        # Priority order: list*, get*, then first available
                        api_function = None
                        for func_name in functions:
                            if func_name.lower().startswith('list'):
                                api_function = func_name
                                break
                        
                        if not api_function:
                            for func_name in functions:
                                if func_name.lower().startswith('get'):
                                    api_function = func_name
                                    break
                        
                        if not api_function and functions:
                            api_function = functions[0]  # Use first available function
                        
                        if api_function:
                            # Create filename based on endpoint name with proper title casing
                            # Convert snake_case to TitleCase properly
                            parts = endpoint_name.split('_')
                            title_name = ''.join(word.capitalize() for word in parts)
                            filename = f"Const{title_name}.csv"
                            description = f"{endpoint_name.replace('_', ' ').title()} Definitions"
                            
                            # Check if this function requires additional parameters beyond mist_session
                            sig = inspect.signature(getattr(module, api_function))
                            required_params = [p for p in sig.parameters.values() 
                                             if p.default == inspect.Parameter.empty and p.name not in ['mist_session', 'apisession']]
                            
                            if required_params:
                                # Handle special cases that need additional parameters
                                param_names = [p.name for p in required_params]
                                
                                if endpoint_name == 'default_gateway_config' and 'model' in param_names:
                                    # Special handling for gateway config - call for all models
                                    print(f"    ! Found special endpoint {api_function}() requiring 'model' parameter")
                                    print(f"    ! Will call for all available gateway models -> {filename}")
                                    discovered_endpoints[endpoint_name] = {
                                        'module': module,
                                        'function': api_function,
                                        'filename': filename,
                                        'description': description,
                                        'modname': modname,
                                        'special_handling': 'all_models'
                                    }
                                elif endpoint_name == 'states' and 'country_code' in param_names:
                                    # Special handling for states - call for all countries
                                    print(f"    ! Found special endpoint {api_function}() requiring 'country_code' parameter")
                                    print(f"    ! Will call for all available countries -> {filename}")
                                    discovered_endpoints[endpoint_name] = {
                                        'module': module,
                                        'function': api_function,
                                        'filename': filename,
                                        'description': description,
                                        'modname': modname,
                                        'special_handling': 'all_countries'
                                    }
                                else:
                                    # Skip functions that require other additional parameters we can't provide
                                    print(f"    ! Skipping {api_function}() - requires additional parameters: {param_names}")
                                    logging.info(f"Skipping {endpoint_name}.{api_function}() - requires parameters: {param_names}")
                                    continue
                            else:
                                # Standard endpoint with no extra parameters required
                                discovered_endpoints[endpoint_name] = {
                                    'module': module,
                                    'function': api_function,
                                    'filename': filename,
                                    'description': description,
                                    'modname': modname,
                                    'special_handling': None
                                }
                            
                            print(f"    ! Found API function: {api_function}() -> {filename}")
                            logging.debug(f"Discovered {endpoint_name}: {api_function}() -> {filename}")
                        else:
                            print(f"    ! No suitable API functions found in {endpoint_name}")
                            logging.warning(f"No API functions with mist_session parameter found in {endpoint_name}")
                    else:
                        print(f"    ! No API functions found in {endpoint_name}")
                        logging.warning(f"No functions found in {endpoint_name}")
                        
                except Exception as e:
                    print(f"    ! Error inspecting {endpoint_name}: {e}")
                    logging.error(f"Error inspecting const module {endpoint_name}: {e}")
                    continue
        
        if not discovered_endpoints:
            print("! No const endpoints discovered from mistapi library")
            logging.error("Dynamic discovery found no const endpoints")
            return
        
        print(f"! Successfully discovered {len(discovered_endpoints)} const endpoints dynamically")
        logging.info(f"Dynamic discovery completed: {len(discovered_endpoints)} endpoints found")
        
        endpoints_processed = 0
        endpoints_skipped_fresh = 0
        endpoints_updated = 0
        endpoints_failed = 0
        
        # Process each discovered const endpoint individually
        for endpoint_name, endpoint_config in discovered_endpoints.items():
            try:
                filename = endpoint_config['filename']
                description = endpoint_config['description']
                module = endpoint_config['module']
                function_name = endpoint_config['function']
                
                print(f"\n! Processing {description} ({endpoint_name})...")
                
                # Check if file exists and determine its freshness
                file_path = os.path.join('data', filename)
                file_exists = os.path.exists(file_path)
                file_is_fresh = False
                
                if file_exists:
                    try:
                        file_mtime = os.path.getmtime(file_path)
                        file_age_hours = (time.time() - file_mtime) / 3600
                        file_is_fresh = file_age_hours < cache_max_age_hours
                        
                        file_timestamp = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        if file_is_fresh:
                            print(f"  ! Found fresh {filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
                            print(f"  ! Skipping API call - using cached data (cache valid for {cache_max_age_hours}h)")
                            logging.info(f"Using cached {endpoint_name} file (age: {file_age_hours:.1f}h)")
                            endpoints_skipped_fresh += 1
                            endpoints_processed += 1
                            continue  # Skip to next endpoint - file is fresh enough
                        else:
                            print(f"  ! Found stale {filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
                            print(f"  ! File is older than {cache_max_age_hours}h threshold - fetching fresh data from API...")
                            logging.info(f"Refreshing stale {endpoint_name} file (age: {file_age_hours:.1f}h)")
                    except Exception as e:
                        print(f"  ! Error checking file timestamp: {e}")
                        logging.warning(f"Could not check {endpoint_name} file timestamp, will fetch fresh data: {e}")
                        file_is_fresh = False
                else:
                    print(f"  ! {filename} not found - fetching fresh data from API...")
                    logging.info(f"{filename} not found, fetching from API")
                
                # Only reach this point if file is missing or stale - fetch fresh data
                try:
                    print(f"  ! Requesting fresh {description.lower()} from Mist API using {function_name}()...")
                    
                    # Handle special endpoints that require additional parameters
                    special_handling = endpoint_config.get('special_handling')
                    
                    if special_handling == 'all_models':
                        # Handle default_gateway_config - call for all available gateway models
                        print(f"  ! Special handling: Calling {function_name}() for all available gateway models...")
                        
                        # First get the list of gateway models from device_models
                        try:
                            device_models_module = importlib.import_module('mistapi.api.v1.const.device_models')
                            device_models_function = getattr(device_models_module, 'listDeviceModels')
                            models_response = device_models_function(apisession)
                            device_models_data = getattr(models_response, 'data', models_response) or {}
                            
                            # Filter for gateway models only (NOT switches)
                            gateway_models = []
                            if isinstance(device_models_data, dict):
                                # Handle dictionary format
                                for model_name, model_details in device_models_data.items():
                                    if isinstance(model_details, dict):
                                        model_type = model_details.get('type', '').lower()
                                        if model_type == 'gateway':
                                            gateway_models.append(model_name)
                            elif isinstance(device_models_data, list):
                                # Handle list format
                                for model_item in device_models_data:
                                    if isinstance(model_item, dict):
                                        model_name = model_item.get('model', model_item.get('name', ''))
                                        model_type = model_item.get('type', '').lower()
                                        if model_name and model_type == 'gateway':
                                            gateway_models.append(model_name)
                                        
                            if not gateway_models:
                                # Fallback to common gateway models only (not switches)
                                gateway_models = ['SRX300', 'SRX320', 'SRX320-POE', 'SRX340', 'SRX345', 'SRX380']
                                print(f"    ! Using fallback gateway models: {len(gateway_models)} models")
                            else:
                                print(f"    ! Discovered {len(gateway_models)} gateway models from device definitions")
                            
                            # Call the function for each gateway model
                            all_gateway_configs = []
                            successful_models = 0
                            failed_models = 0
                            
                            for model in gateway_models:
                                try:
                                    api_function = getattr(module, function_name)
                                    model_response = api_function(apisession, model=model)
                                    model_data = getattr(model_response, 'data', model_response) or {}
                                    
                                    if model_data:
                                        # Add model identifier to each record
                                        if isinstance(model_data, dict):
                                            model_record = {'model': model}
                                            model_record.update(model_data)
                                            all_gateway_configs.append(model_record)
                                        elif isinstance(model_data, list):
                                            for item in model_data:
                                                if isinstance(item, dict):
                                                    item['model'] = model
                                                all_gateway_configs.extend(model_data)
                                        else:
                                            all_gateway_configs.append({'model': model, 'config': str(model_data)})
                                        successful_models += 1
                                except Exception as model_error:
                                    logging.warning(f"Failed to get gateway config for model {model}: {model_error}")
                                    failed_models += 1
                                    continue
                            
                            const_data = all_gateway_configs
                            print(f"    ! Successfully retrieved configs for {successful_models} models, {failed_models} failed")
                            
                        except Exception as e:
                            print(f"    ! Error getting gateway models list: {e}")
                            logging.error(f"Failed to get gateway models for {endpoint_name}: {e}")
                            const_data = {}
                            
                    elif special_handling == 'all_countries':
                        # Handle states - call for all available countries
                        print(f"  ! Special handling: Calling {function_name}() for all available countries...")
                        
                        # First get the list of countries
                        try:
                            countries_module = importlib.import_module('mistapi.api.v1.const.countries')
                            countries_function = getattr(countries_module, 'listCountryCodes')
                            countries_response = countries_function(apisession)
                            countries_data = getattr(countries_response, 'data', countries_response) or {}
                            
                            # Extract country codes
                            country_codes = []
                            if isinstance(countries_data, dict):
                                country_codes = list(countries_data.keys())
                            elif isinstance(countries_data, list):
                                for item in countries_data:
                                    if isinstance(item, dict) and 'code' in item:
                                        country_codes.append(item['code'])
                                    elif isinstance(item, dict) and 'name' in item:
                                        # Extract code from name or use first 2 chars
                                        code = item.get('alpha2', item.get('code', item['name'][:2].upper()))
                                        country_codes.append(code)
                            
                            if not country_codes:
                                # Fallback to major countries if we can't get the full list
                                country_codes = ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'JP', 'CN', 'IN', 'BR']
                                print(f"    ! Using fallback country codes: {len(country_codes)} countries")
                            else:
                                print(f"    ! Discovered {len(country_codes)} country codes from country definitions")
                            
                            # Call the function for each country
                            all_states = []
                            successful_countries = 0
                            failed_countries = 0
                            
                            for country_code in country_codes:
                                try:
                                    api_function = getattr(module, function_name)
                                    country_response = api_function(apisession, country_code=country_code)
                                    country_data = getattr(country_response, 'data', country_response) or {}
                                    
                                    if country_data:
                                        # Add country identifier to each record
                                        if isinstance(country_data, dict):
                                            for state_code, state_data in country_data.items():
                                                if isinstance(state_data, dict):
                                                    state_record = {'country_code': country_code, 'state_code': state_code}
                                                    state_record.update(state_data)
                                                    all_states.append(state_record)
                                                else:
                                                    all_states.append({
                                                        'country_code': country_code, 
                                                        'state_code': state_code, 
                                                        'state_name': str(state_data)
                                                    })
                                        elif isinstance(country_data, list):
                                            for item in country_data:
                                                if isinstance(item, dict):
                                                    item['country_code'] = country_code
                                                all_states.extend(country_data)
                                        successful_countries += 1
                                except Exception as country_error:
                                    logging.warning(f"Failed to get states for country {country_code}: {country_error}")
                                    failed_countries += 1
                                    continue
                            
                            const_data = all_states
                            print(f"    ! Successfully retrieved states for {successful_countries} countries, {failed_countries} failed")
                            
                        except Exception as e:
                            print(f"    ! Error getting countries list: {e}")
                            logging.error(f"Failed to get countries for {endpoint_name}: {e}")
                            const_data = {}
                    else:
                        # Standard endpoint - call normally
                        api_function = getattr(module, function_name)
                        response = api_function(apisession)
                        const_data = getattr(response, 'data', response) or {}
                    
                    if const_data:
                        # Handle different data structures returned by different endpoints
                        if isinstance(const_data, dict):
                            # Convert dictionary to list of records for CSV processing
                            if endpoint_name == 'insight_metrics':
                                # Special handling for insight metrics with complex nested structure
                                data_list = []
                                for metric_name, metric_details in const_data.items():
                                    # Flatten the metric details into a single row
                                    metric_row = {
                                        'metric_name': metric_name,
                                        'description': metric_details.get('description', ''),
                                        'type': metric_details.get('type', ''),
                                        'unit': metric_details.get('unit', ''),
                                        'scopes': ', '.join(metric_details.get('scopes', [])),
                                        'report_scopes': ', '.join(metric_details.get('report_scopes', [])),
                                    }
                                    
                                    # Add interval information if available
                                    intervals = metric_details.get('intervals', {})
                                    if intervals:
                                        interval_info = []
                                        for interval_name, interval_data in intervals.items():
                                            interval_str = f"{interval_name}({interval_data.get('interval', 'N/A')}s, max_age:{interval_data.get('max_age', 'N/A')}s)"
                                            interval_info.append(interval_str)
                                        metric_row['intervals'] = '; '.join(interval_info)
                                    else:
                                        metric_row['intervals'] = ''
                                    
                                    # Add report interval information if available
                                    report_intervals = metric_details.get('report_intervals', {})
                                    if report_intervals:
                                        report_interval_info = []
                                        for interval_name, interval_data in report_intervals.items():
                                            interval_str = f"{interval_name}({interval_data.get('interval', 'N/A')}s)"
                                            report_interval_info.append(interval_str)
                                        metric_row['report_intervals'] = '; '.join(report_interval_info)
                                    else:
                                        metric_row['report_intervals'] = ''
                                    
                                    data_list.append(metric_row)
                            else:
                                # Standard dictionary to list conversion for other endpoints
                                data_list = []
                                for key, value in const_data.items():
                                    if isinstance(value, dict):
                                        # Flatten nested dictionary
                                        row = {'name': key}
                                        row.update(value)
                                        data_list.append(row)
                                    else:
                                        # Simple key-value pair
                                        data_list.append({'name': key, 'value': str(value)})
                        elif isinstance(const_data, list):
                            # Data is already a list - use directly
                            data_list = const_data
                        else:
                            # Single item, convert to list
                            data_list = [const_data] if const_data else []
                        
                        # Process and save the data
                        processed = escape_multiline_strings_for_csv(data_list)
                        DataExporter.save_data_to_output(processed, filename)
                        print(f"  ! {len(processed)} {description.lower()} exported to {filename}")
                        logging.info(f"Exported {len(processed)} fresh {description.lower()} to {filename}")
                        endpoints_updated += 1
                    else:
                        print(f"  ! 0 {description.lower()} exported to {filename} (no data available)")
                        logging.warning(f"No {description.lower()} data available from {endpoint_name} endpoint")
                        DataExporter.save_data_to_output([], filename)
                        endpoints_updated += 1
                        
                except Exception as e:
                    print(f"  ! Error exporting {description.lower()}: {e}")
                    logging.error(f"Failed to export {description.lower()} from {endpoint_name}: {e}")
                    DataExporter.save_data_to_output([], filename)
                    endpoints_failed += 1
                    
                endpoints_processed += 1
                
            except Exception as e:
                print(f"! Critical error processing {endpoint_name}: {e}")
                logging.error(f"Critical error processing {endpoint_name}: {e}")
                endpoints_failed += 1
                endpoints_processed += 1
        
        # Summary report
        print(f"\n! Dynamic Const Export Summary:")
        print(f"  ! Total endpoints discovered: {len(discovered_endpoints)}")
        print(f"  ! Total endpoints processed: {endpoints_processed}")
        print(f"  ! Fresh files skipped: {endpoints_skipped_fresh}")
        print(f"  ! Files updated/created: {endpoints_updated}")
        print(f"  ! Failed endpoints: {endpoints_failed}")
        logging.info(f"Dynamic const export completed: {len(discovered_endpoints)} discovered, {endpoints_processed} processed, {endpoints_skipped_fresh} skipped (fresh), {endpoints_updated} updated, {endpoints_failed} failed")
        
    except Exception as e:
        print(f"! Critical error during dynamic const discovery: {e}")
        logging.error(f"Critical error during dynamic const discovery: {e}")


def export_const_insight_metrics_to_csv():
    """Legacy function maintained for backward compatibility.
    
    This function now calls the comprehensive dynamic export_all_const_definitions_to_csv()
    but still provides individual insight metrics functionality for existing code.
    """
    print("Export Available Insight Metrics (Legacy Mode):")
    print("! Note: This function now uses the dynamic comprehensive const export system")
    print("! For best results, consider using Menu 82: Export All Const Definitions")
    logging.info("Legacy const insight metrics export called - using dynamic comprehensive system")
    
    # Call the comprehensive function which will handle insight metrics along with all others
    export_all_const_definitions_to_csv()
    
    # Provide specific feedback about insight metrics
    import os
    insight_metrics_file = os.path.join('data', 'ConstInsightMetrics.csv')
    if os.path.exists(insight_metrics_file):
        print("! ConstInsightMetrics.csv is available in the dynamic export results")
    else:
        print("! Warning: ConstInsightMetrics.csv was not created during dynamic export")

def get_insight_metrics_by_scope(target_scope):
    """
    Read ConstInsightMetrics.csv and return metrics that support the specified scope.
    
    Args:
        target_scope (str): The scope to filter by (e.g., 'site', 'client', 'device', 'ap')
        
    Returns:
        list: List of metric names that support the target scope
    """
    import csv
    import os
    
    csv_path = os.path.join('data', 'ConstInsightMetrics.csv')
    metrics_for_scope = []
    
    try:
        if not os.path.exists(csv_path):
            logging.warning(f"ConstInsightMetrics.csv not found at {csv_path}")
            return []
            
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                scopes = row.get('scopes', '')
                metric_name = row.get('metric_name', '')
                
                # Skip rows with empty metric names
                if not metric_name:
                    continue
                    
                # Check if target scope is in the scopes list
                if scopes and target_scope in scopes:
                    metrics_for_scope.append(metric_name)
                    
        logging.debug(f"Found {len(metrics_for_scope)} metrics for scope '{target_scope}': {metrics_for_scope}")
        return metrics_for_scope
        
    except Exception as e:
        logging.error(f"Error reading ConstInsightMetrics.csv: {e}")
        return []

def export_org_insight_metrics_to_csv():
    """Export organization-wide insight metrics to OrgInsightMetrics.csv."""
    print("Export Organization Insight Metrics:")
    logging.info("Starting export of organization insight metrics...")
    
    # First, refresh the available metrics from the API
    print("! Refreshing available insight metrics from Mist API...")
    export_const_insight_metrics_to_csv()
    
    # Get all metrics that support "org" scope
    org_metrics = get_insight_metrics_by_scope("org")
    
    if not org_metrics:
        print("! No metrics found for org scope. Check ConstInsightMetrics.csv file.")
        logging.error("No org-scope metrics found in const insight metrics")
        DataExporter.save_data_to_output([], "OrgInsightMetrics.csv")
        return
    
    org_id = get_cached_or_prompted_org_id()
    filename = "OrgInsightMetrics.csv"
    
    all_insight_data = []
    metrics_retrieved = 0
    metrics_failed = 0
    
    print(f"! Retrieving {len(org_metrics)} different organization insight metrics...")
    print("! Processing each metric individually with proper error handling...")
    
    try:
        # Iterate through each org-scoped metric and retrieve it individually
        for metric in org_metrics:
            try:
                logging.debug(f"Attempting to retrieve org insight metric: {metric}")
                
                # For metrics that analyze sites, use getOrgSitesSle instead of getOrgSle
                if "worst-sites" in metric or metric in ["sites-sle", "sites-sle-filtered"]:
                    # These metrics require site-level SLE data analysis
                    sle_categories = ["wifi", "wan", "wired"]
                    
                    for sle_category in sle_categories:
                        try:
                            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(
                                apisession, 
                                org_id, 
                                sle=sle_category,
                                duration="7d",
                                limit=1000
                            )
                            sites_data = mistapi.get_all(response=response, mist_session=apisession) or []
                            
                            if sites_data:
                                # Create an aggregated insight result from sites data
                                insight_result = {
                                    'metric_type': f"{metric}_{sle_category}",
                                    'org_id': org_id,
                                    'sle_category': sle_category,
                                    'data_source': 'sites_sle_analysis',
                                    'total_sites': len(sites_data),
                                    'sites_data': sites_data,
                                    'original_metric': metric
                                }
                                
                                all_insight_data.append(insight_result)
                                metrics_retrieved += 1
                                logging.debug(f"Successfully retrieved sites data for insight metric: {metric} with SLE: {sle_category} ({len(sites_data)} sites)")
                            else:
                                logging.debug(f"No sites data available for insight metric: {metric} with SLE: {sle_category}")
                        except Exception as sites_error:
                            logging.debug(f"Failed to get sites data for insight metric '{metric}' with SLE '{sle_category}': {sites_error}")
                            continue
                else:
                    # For other metrics, use getOrgSle directly
                    response = mistapi.api.v1.orgs.insights.getOrgSle(
                        apisession, 
                        org_id, 
                        metric,
                        duration="7d"
                    )
                    insight_data = getattr(response, 'data', response) or {}
                    
                    if insight_data:
                        # Add metric type identifier to each data point
                        insight_data['metric_type'] = metric
                        insight_data['org_id'] = org_id
                        all_insight_data.append(insight_data)
                        metrics_retrieved += 1
                        logging.debug(f"Successfully retrieved org insight data for metric: {metric}")
                    else:
                        logging.debug(f"No data available for org metric: {metric}")
                        metrics_failed += 1
                    
            except Exception as metric_error:
                metrics_failed += 1
                logging.debug(f"Failed to get org insight data for metric '{metric}': {metric_error}")
                # Continue with next metric instead of failing entirely
                continue
        
        # Also try getOrgSitesSle for sites summary data 
        try:
            logging.debug("Attempting to retrieve org sites SLE summary")
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(apisession, org_id, duration="7d", limit=100)
            sites_data = mistapi.get_all(response=response, mist_session=apisession) or []
            if sites_data:
                for item in sites_data:
                    item['metric_type'] = 'org_sites_sle_summary'
                    item['org_id'] = org_id
                    all_insight_data.append(item)
                metrics_retrieved += 1
                logging.debug(f"Successfully retrieved org sites SLE data for {len(sites_data)} sites")
        except Exception as sites_error:
            metrics_failed += 1
            logging.debug(f"Failed to get org sites SLE summary: {sites_error}")
        
        # Report results
        print(f"! Metric retrieval completed: {metrics_retrieved} successful, {metrics_failed} failed")
        logging.info(f"Org insight metrics: {metrics_retrieved} retrieved successfully, {metrics_failed} failed")
        
        if all_insight_data:
            # Flatten and process the data for CSV export
            processed = flatten_nested_fields_in_list(all_insight_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} organization insight metrics exported to {filename}")
            logging.info(f"Exported {len(processed)} org insight data points from {metrics_retrieved} metrics to {filename}")
        else:
            print(f"! 0 organization insight metrics exported to {filename} (no data available)")
            logging.warning("No org insight data available - all metrics failed or returned empty")
            DataExporter.save_data_to_output([], filename)
            
    except Exception as e:
        print(f"! Error exporting organization insight metrics: {e}")
        logging.error(f"Failed to export org insight metrics: {e}")
        DataExporter.save_data_to_output([], filename)

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
                logging.info(f"! Fetched {len(clients)} rogue clients from site: {site_name}")
                
            except Exception as e:
                logging.warning(f"! Failed to fetch rogue clients from site {site_name}: {e}")
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
        DataExporter.save_data_to_output(sanitized, "OrgRogueClients")
        logging.info(f"! {len(all_rogue_clients)} rogue clients exported to OrgRogueClients")
        print(f"! {len(all_rogue_clients)} rogue clients exported to OrgRogueClients")
    else:
        logging.info("No rogue clients found across all sites")
        print(" No rogue clients detected across all sites")

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
                logging.info(f"! Fetched {len(aps)} rogue APs from site: {site_name}")
                
            except Exception as e:
                logging.warning(f"! Failed to fetch rogue APs from site {site_name}: {e}")
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
        DataExporter.save_data_to_output(sanitized, "OrgRogueAPs")
        logging.info(f"! {len(all_rogue_aps)} rogue APs exported to OrgRogueAPs")
        print(f"! {len(all_rogue_aps)} rogue APs exported to OrgRogueAPs")
    else:
        logging.info("No rogue APs found across all sites")
        print(" No rogue APs detected across all sites")

def export_org_licenses_to_csv():
    """Export organization license entitlements to OrgLicenses.csv using the canonical list endpoint.

    Rationale: Per user directive, remove multi-endpoint fallback / probing logic. We use the
    detailed list endpoint only. If it returns zero records we log and still emit an empty file.
    """
    logging.info("Starting export of organization licenses (canonical endpoint)...")
    filename = "OrgLicenses.csv"
    org_id = get_cached_or_prompted_org_id()

    try:
        # Canonical endpoint: listOrgLicenses (paginated). We deliberately do NOT call the summary endpoint.
        list_func = getattr(mistapi.api.v1.orgs.licenses, 'listOrgLicenses', None)
        if list_func is None:
            # Library wrapper absent – this is a version compatibility shim, not an alternate data source.
            logging.debug("listOrgLicenses wrapper not present in mistapi library; performing direct GET /licenses")
            raw_url = f"/api/v1/orgs/{org_id}/licenses"
            response = apisession.mist_get(raw_url)
            raw_items = getattr(response, 'data', response) or []
        else:
            response = list_func(apisession, org_id, limit=1000)
            raw_items = mistapi.get_all(response=response, mist_session=apisession) or []

        if not isinstance(raw_items, list):
            # Defensive normalization: if API ever returns a dict, convert to single-element list.
            logging.debug("License endpoint returned non-list payload; normalizing to list")
            raw_items = [raw_items]

        if not raw_items:
            logging.info("No license records returned from canonical endpoint; writing empty OrgLicenses.csv")
            DataExporter.save_data_to_output([], filename)
            return

        processed = flatten_nested_fields_in_list(raw_items)
        processed = escape_multiline_strings_for_csv(processed)
        DataExporter.save_data_to_output(processed, filename)
        logging.info(f"Exported {len(processed)} license records to {filename}.")
    except Exception as e:
        logging.error(f"Failed to export licenses: {e}")
        # Emit an empty file to keep test harness consistent, then re-raise for visibility
        try:
            DataExporter.save_data_to_output([], filename)
        except Exception:
            pass
        raise

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
    
    logging.info(" License usage data exported to OrgUsage")
    print(" License usage data exported to OrgUsage")

def export_org_msp_to_csv():
    """Export MSP (Managed Service Provider) information for the organization to OrgMsp.csv."""
    logging.warning(" MSP data is available only at MSP level, not organization level")
    print(" MSP data is available only at MSP level, not organization level")
    print(" To access MSP data, use the Mist API MSP endpoints directly:")
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
    """Export AP device profiles (templates) to OrgApTemplates.csv via canonical filtered endpoint.

    Single call only (type='ap'). If zero returned we write an empty file without secondary probing.
    """
    print("Export Organization AP Templates:")
    logging.info("Starting export of organization AP templates (canonical deviceprofiles type=ap)...")
    org_id = get_cached_or_prompted_org_id()
    filename = "OrgApTemplates.csv"
    try:
        response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(apisession, org_id, type="ap", limit=1000)
        ap_profiles = mistapi.get_all(response=response, mist_session=apisession) or []
        if not ap_profiles:
            print("! 0 AP templates exported to OrgApTemplates.csv (no templates found)")
            logging.info("No AP templates returned from canonical endpoint; writing empty OrgApTemplates.csv")
            DataExporter.save_data_to_output([], filename)
            return
        processed = flatten_nested_fields_in_list(ap_profiles)
        processed = escape_multiline_strings_for_csv(processed)
        DataExporter.save_data_to_output(processed, filename)
        print(f"! {len(processed)} AP templates exported to {filename}")
        logging.info(f"Exported {len(processed)} AP templates to {filename}.")
    except Exception as e:
        logging.error(f"Failed to export AP templates: {e}")
        try:
            DataExporter.save_data_to_output([], filename)
        except Exception:
            pass
        raise

def export_org_switch_templates_to_csv():
    """Export switch device profiles (templates) to OrgSwitchTemplates.csv via canonical filtered endpoint.

    Single call only (type='switch'). If zero returned we emit an empty file without retries.
    """
    print("Export Organization Switch Templates:")
    logging.info("Starting export of organization switch templates (canonical networktemplates)...")
    org_id = get_cached_or_prompted_org_id()
    filename = "OrgSwitchTemplates.csv"
    try:
        response = mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates(apisession, org_id, limit=1000)
        switch_profiles = mistapi.get_all(response=response, mist_session=apisession) or []
        if not switch_profiles:
            print("! 0 switch templates exported to OrgSwitchTemplates.csv (no templates found)")
            logging.info("No switch templates returned from canonical endpoint; writing empty OrgSwitchTemplates.csv")
            DataExporter.save_data_to_output([], filename)
            return
        processed = flatten_nested_fields_in_list(switch_profiles)
        processed = escape_multiline_strings_for_csv(processed)
        DataExporter.save_data_to_output(processed, filename)
        print(f"! {len(processed)} switch templates exported to {filename}")
        logging.info(f"Exported {len(processed)} switch templates to {filename}.")
    except Exception as e:
        logging.error(f"Failed to export switch templates: {e}")
        try:
            DataExporter.save_data_to_output([], filename)
        except Exception:
            pass
        raise

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
    print(" Starting continuous data collection loop...")
    print("   This will collect core organizational data every 5 seconds")
    print("   Press CTRL+C to stop or create 'stop_loop.txt' file")
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            print(f"\n  Loop iteration {loop_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check for stop file
            if os.path.exists("stop_loop.txt"):
                print(" Stop file detected. Ending continuous loop.")
                os.remove("stop_loop.txt")
                break
            
            try:
                # 1. Site list
                print("  Collecting site list...")
                export_all_sites_to_csv()
                time.sleep(0.75)  # Rate limiting
                
                # 2. Organization inventory
                print("  Collecting organization inventory...")
                export_device_inventory_to_csv()
                time.sleep(0.75)
                
                # 3. Organization device stats
                print("  Collecting organization device stats...")
                export_device_stats_to_csv()
                time.sleep(0.75)
                
                # 4. Organization device port stats
                print("  Collecting organization device port stats...")
                export_device_port_stats_to_csv()
                time.sleep(0.75)
                
                # 5. VPN peer path stats
                print("  Collecting VPN peer path stats...")
                export_vpn_peer_stats_to_csv()
                time.sleep(0.75)
                
                print(f"  Loop {loop_count} completed successfully")
                
            except KeyboardInterrupt:
                print("\n   Keyboard interrupt detected. Stopping loop...")
                break
            except Exception as e:
                logging.error(f"Error in continuous loop iteration {loop_count}: {e}")
                print(f"  Error in loop {loop_count}: {e}")
                print("  Continuing to next iteration...")
                time.sleep(5)  # Wait longer on error
                
    except KeyboardInterrupt:
        print("\n  Continuous data collection loop stopped by user.")
    except Exception as e:
        logging.error(f"Fatal error in continuous loop: {e}")
        print(f"! Fatal error in continuous loop: {e}")
    
    print(" Continuous data collection loop ended.")

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
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("org NAC events export", hours)
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents,
        data_type="nac events",
        sort_key="timestamp",
        duration=f"{hours}h"
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
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("org events export", hours)
    export_org_specific_data(
        api_call=mistapi.api.v1.orgs.events.searchOrgEvents,
        data_type="events",
        sort_key="timestamp",
        duration=f"{hours}h"
    )

# === Site-Level Functions ===

def export_site_system_events_to_csv():
    """Export system events for a specific site to SiteSystemEvents.csv."""
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("site system events export", hours)
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.events.searchSiteSystemEvents,
        data_type="system events",
        sort_key="timestamp",
        duration=f"{hours}h"
    )

def export_site_fast_roam_events_to_csv():
    """Export fast roam events for a specific site to SiteFastRoamEvents.csv."""
    hours = get_dynamic_lookback_hours(24, 1)
    log_dynamic_lookback("site fast roam events export", hours)
    export_site_specific_data(
        api_call=mistapi.api.v1.sites.events.searchSiteFastRoamEvents,
        data_type="fast roam events",
        sort_key="timestamp",
        duration=f"{hours}h"
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
    sites = fetch_all_sites_with_limit(org_id)

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
            logging.info(f"! Fetched config for site: {site_name} (ID: {site_id})")
        except Exception as e:
            logging.warning(f"! Failed to fetch config for {site_name} (ID: {site_id}): {e}")

    logging.info(f"Fetched settings for {len(all_configs)} sites.")
    return all_configs

def export_site_settings_to_csv():
    """
    Fetches and exports configuration settings for all sites in the organization to AllSiteConfigs.csv.
    Adds detailed logging at each step.
    """
    print("Site Configuration Settings:")
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
        DataExporter.save_data_to_output(data, "AllSiteConfigs.csv")
        print(f"! {len(data)} site configurations exported to AllSiteConfigs.csv")
        logging.info(" Site configs saved to AllSiteConfigs.csv")
    else:
        logging.warning(" No site configs found.")
        print("! No site configurations found.")

def export_gateway_synthetic_tests_to_csv(fast=False):
    """
    Collects and exports synthetic test stats for all gateways in the organization.
    Optimized to use cached inventory data and concurrent processing when fast=True.
    
    Args:
        fast (bool): If True, enables concurrent processing and uses cached inventory data
                    to minimize API calls.
    """
    # DEBUG: Log invocation context early so harness vs direct calls can be distinguished
    logging.debug(f"[DEBUG] export_gateway_synthetic_tests_to_csv invoked with fast={fast}")
    logging.info("[INFO] Collecting synthetic test stats for all gateways in the org...")
    if fast:
        logging.info(" Fast mode enabled: Using cached data and concurrent processing (synthetic tests)")
    
    org_id = get_cached_or_prompted_org_id()
    gateway_devices = get_gateway_devices_with_sites(apisession, org_id, fast=fast)
    all_stats = []

    if not gateway_devices:
        logging.warning("[WARN] No gateway devices found. Exiting export_gateway_synthetic_tests_to_csv.")
        return

    def fetch_synthetic_test_stats_with_retry(device_info, max_retries=None, retry_delay=None, connection_semaphore=None):
        """
        Fetch synthetic test stats for a single gateway device with retry logic and connection pool management.
        
        Args:
            device_info: Tuple of (site_id, device_id, device_name, site_name)
            max_retries: Maximum number of retry attempts (uses env var if None)
            retry_delay: Base delay between retries (uses env var if None)
            connection_semaphore: Semaphore to limit concurrent connections (optional)
        """
        # Use environment variables as defaults if not provided
        if max_retries is None:
            max_retries = FAST_MODE_MAX_RETRIES
        if retry_delay is None:
            retry_delay = FAST_MODE_RETRY_DELAY
            
        site_id, device_id, device_name, site_name = device_info
        
        for attempt in range(max_retries + 1):
            try:
                # Validate inputs before making API calls
                validate_site_id(site_id, "export_gateway_synthetic_tests_to_csv")
                validate_device_id(device_id, "export_gateway_synthetic_tests_to_csv")
                
                # Use semaphore to limit concurrent connections if provided
                if connection_semaphore:
                    with connection_semaphore:
                        stats = mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(apisession, site_id, device_id).data
                else:
                    stats = mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(apisession, site_id, device_id).data
                
                stats["site_id"] = site_id
                stats["site_name"] = site_name
                stats["device_id"] = device_id
                stats["device_name"] = device_name
                
                if attempt > 0:
                    logging.info(f"! Retry {attempt} successful for device {device_name} at site {site_name}")
                else:
                    logging.info(f"! Collected synthetic test stats for device {device_name} at site {site_name}")
                return stats
                
            except Exception as e:
                if attempt < max_retries:
                    # Fast mode: reduced backoff delay for quicker retries
                    backoff_delay = retry_delay * (FAST_MODE_BACKOFF_MULTIPLIER ** attempt)  # Configurable backoff
                    logging.warning(f"! Attempt {attempt + 1} failed for device {device_id} at site {site_id}: {e}")
                    logging.info(f"! Fast retry in {backoff_delay:.1f}s (attempt {attempt + 2}/{max_retries + 1})")
                    time.sleep(backoff_delay)
                else:
                    logging.error(f"! Final attempt failed for device {device_id} at site {site_id}: {e}")
                    return None
        
        return None

    if fast:
        # Concurrent processing mode with connection-aware threading + summary instrumentation
        start_time = time.time()

        # Define worker function for the connection pool helper
        def fetch_device_stats(device_info, connection_semaphore):
            """Worker function that fetches synthetic test stats for a single device."""
            return fetch_synthetic_test_stats_with_retry(device_info, connection_semaphore=connection_semaphore)

        # Define retry function for failed devices (unchanged logic, clearer logging prefix FAST)
        def retry_failed_devices(failed_devices, connection_semaphore):
            retry_results = []
            still_failed = []
            retry_threads = min(FAST_MODE_RETRY_THREADS, len(failed_devices), max(1, FAST_MODE_MAX_CONCURRENT_CONNECTIONS - 2))
            if retry_threads <= 0:
                logging.warning(" FAST MODE: No available threads for retry; skipping retries")
                return [], failed_devices
            with ThreadPoolExecutor(max_workers=retry_threads) as executor:
                retry_futures = {
                    executor.submit(fetch_synthetic_test_stats_with_retry, device_info, max_retries=FAST_MODE_RETRY_MAX_RETRIES, connection_semaphore=connection_semaphore): device_info
                    for device_info in failed_devices
                }
                for future in tqdm(as_completed(retry_futures), total=len(retry_futures), desc="Retrying Failed", unit="device"):
                    device_info = retry_futures[future]
                    try:
                        result = future.result()
                        if result:
                            retry_results.append(result)
                            logging.info(f" FAST RETRY OK: {device_info[2]}")
                        else:
                            still_failed.append(device_info)
                            logging.error(f" FAST RETRY FAIL: {device_info[2]}")
                    except Exception as e:
                        still_failed.append(device_info)
                        logging.error(f" FAST RETRY EXC: {device_info[2]} -> {e}")
            return retry_results, still_failed

        successful_results, failed_devices = execute_with_connection_pool_management(
            work_items=gateway_devices,
            worker_function=fetch_device_stats,
            batch_description="devices",
            retry_function=retry_failed_devices
        )

        duration = time.time() - start_time
        all_stats.extend(successful_results)
        logging.info(f" FAST MODE SUMMARY (synthetic tests): ok={len(successful_results)} fail={len(failed_devices)} total={len(gateway_devices)} elapsed={duration:.2f}s")
    else:
        # Sequential processing with rate limiting (original behavior)
        smoothed = None
        for device_info in tqdm(gateway_devices, desc="Gateway Devices", unit="device"):
            result = fetch_synthetic_test_stats_with_retry(device_info, max_retries=FAST_MODE_SEQUENTIAL_MAX_RETRIES)
            if result:
                all_stats.append(result)
            
            # Apply rate limiting only in non-fast mode
            smoothed, delay = get_rate_limited_delay(smoothed)
            logging.info(f"[INFO] Sleeping for {delay:.2f}s.")
            time.sleep(delay)

    if all_stats:
        filename = "AllGatewaySyntheticTests.csv"
        flattened = flatten_nested_fields_in_list(all_stats)
        sanitized = escape_multiline_strings_for_csv(flattened)
        DataExporter.save_data_to_output(sanitized, filename)
        print(f"! {len(all_stats)} gateway synthetic test results exported to {filename}")
        logging.info(f"! Synthetic test results saved to {filename} ({len(all_stats)} records).")
        logging.info(f"! API Optimization: Saved {len(gateway_devices)} listSiteDevices calls by using cached inventory")
    else:
        logging.warning(" No synthetic test results found. CSV not created.")
        print("! No synthetic test results found. CSV not created.")

def get_gateway_devices_with_sites(apisession, org_id, fast=False):
    """
    Efficiently fetches all gateway devices with their site information.
    Uses cached data when fast=True to minimize API calls.

    Args:
        apisession: The Mist API session object.
        org_id: The organization ID.
        fast (bool): If True, uses cached CSV data instead of making fresh API calls.

    Returns:
        List of tuples: (site_id, device_id, device_name, site_name) for each gateway device.
    """
    logging.info("[INFO] Fetching gateway devices with site information...")
    
    if fast:
        # Use cached data approach
        try:
            # Ensure required CSV files exist using caching
            check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)
            check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
            
            # Load inventory from cached CSV
            gateway_devices = []
            inventory_path = get_csv_file_path("OrgInventory.csv")
            with open(inventory_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                gateways = [row for row in reader if row.get("type") == "gateway" and row.get("site_id") and row.get("id")]
            
            # Load site names from cached CSV
            site_name_lookup = {}
            site_list_path = get_csv_file_path("SiteList.csv")
            with open(site_list_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                site_name_lookup = {row.get("id"): row.get("name", "Unknown Site") for row in reader}
            
            # Build device list with site names
            for device in gateways:
                site_id = device.get("site_id")
                device_id = device.get("id")
                device_name = device.get("name", "")
                site_name = site_name_lookup.get(site_id, "Unknown Site")
                gateway_devices.append((site_id, device_id, device_name, site_name))
            
            logging.info(f"! Fast mode: Loaded {len(gateway_devices)} gateway devices from cached data")
            return gateway_devices
            
        except Exception as e:
            logging.warning(f"! Fast mode failed, falling back to API calls: {e}")
            # Fall through to API mode
    
    # Original API-based approach
    logging.info("[INFO] Fetching org inventory to find gateway devices...")
    # Fetch the full org inventory (all devices)
    devices = fetch_all_inventory_with_limit(org_id)
    logging.info(f"[INFO] Retrieved {len(devices)} devices from org inventory.")
    
    # Get site names
    site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)
    sites = mistapi.get_all(response=site_response, mist_session=apisession)
    site_name_lookup = {site["id"]: site.get("name", "Unknown Site") for site in sites}
    
    # Filter for gateway devices and build tuples
    gateway_devices = []
    for device in devices:
        if device.get("type") == "gateway" and device.get("site_id") and device.get("id"):
            site_id = device.get("site_id")
            device_id = device.get("id")
            device_name = device.get("name", "")
            site_name = site_name_lookup.get(site_id, "Unknown Site")
            gateway_devices.append((site_id, device_id, device_name, site_name))
    
    logging.info(f"[INFO] Found {len(gateway_devices)} gateway devices across the organization.")
    return gateway_devices

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
    devices = fetch_all_inventory_with_limit(org_id)
    logging.info(f"[INFO] Retrieved {len(devices)} devices from org inventory.")

    # Collect unique site_ids for devices of type 'gateway'
    gateway_sites = {device["site_id"] for device in devices 
                     if device.get("type") == "gateway" 
                     and device.get("site_id") 
                     and str(device.get("site_id")).strip()}
    logging.info(f"[INFO] Found {len(gateway_sites)} sites with at least one gateway.")

    return list(gateway_sites)

def export_gateway_test_results_by_site_to_csv(fast: bool = False):
    """Export all synthetic test results (including speed tests) for all sites with gateways.

    When fast=True:
      * Uses cached inventory + site list CSVs (generates them if missing) to derive site IDs quickly.
      * Processes sites concurrently using the shared connection pool helper.
      * Skips per-site adaptive rate limiting delays (relies on pool throttling instead).

    Args:
        fast (bool): Enable cached data usage + concurrent site processing.
    """
    print("Gateway Synthetic Test Results:")
    logging.info("[INFO] Searching all test results (including speed tests) for sites with gateways...")
    if fast:
        logging.info(" Fast mode enabled: Using cached inventory/site data and concurrent site processing")

    org_id = get_cached_or_prompted_org_id()

    # Fast path: derive site IDs from cached CSVs to avoid full inventory refetch if possible
    site_ids = []
    if fast:
        try:
            # Ensure cached CSVs present
            check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)
            inventory_path = get_csv_file_path("OrgInventory.csv")
            with open(inventory_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Filter out None/empty site_ids and only include gateways
                site_ids = sorted({row.get("site_id") for row in reader 
                                 if row.get("type") == "gateway" and row.get("site_id") and row.get("site_id").strip()})
            logging.info(f"! Fast mode: Loaded {len(site_ids)} site_ids with gateways from cached inventory")
        except Exception as e:
            logging.warning(f"! Fast mode site derivation failed, falling back to API discovery: {e}")
            site_ids = []  # Force fallback

    if not site_ids:
        site_ids = get_site_ids_with_gateway_devices(apisession, org_id)

    if not site_ids:
        logging.warning(" No sites with gateways found.")
        return

    all_results = []

    def fetch_site_tests(site_id, connection_semaphore):
        """Worker to fetch all synthetic test results for one site (with optional semaphore)."""
        try:
            validate_site_id(site_id, "export_gateway_test_results_by_site_to_csv")
            if connection_semaphore:
                with connection_semaphore:
                    response = mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest(apisession, site_id)
            else:
                response = mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest(apisession, site_id)
            if not hasattr(response, "data"):
                logging.warning(f"! No data attribute in response for site {site_id}")
                return []
            results = response.data.get("results", []) if isinstance(response.data, dict) else []
            for r in results:
                r["site_id"] = site_id
            logging.info(f"[{site_id}] Retrieved {len(results)} test results.")
            return results
        except Exception as e:
            logging.warning(f"! Failed to fetch test results for site {site_id}: {e}")
            return []

    if fast:
        start_time = time.time()
        # Use generic connection pool executor (treat each site as a work item)
        # Reuse execute_with_connection_pool_management pattern by adapting worker signature
        def worker(site_id, connection_semaphore):
            return fetch_site_tests(site_id, connection_semaphore)

        successful_results, failed_sites = execute_with_connection_pool_management(
            work_items=site_ids,
            worker_function=worker,
            batch_description="sites"
        )
        # successful_results is a list of lists (each site's results); flatten
        flattened_results = []
        for site_list in successful_results:
            if isinstance(site_list, list):
                flattened_results.extend(site_list)
        all_results = flattened_results
        duration = time.time() - start_time
        logging.info(f" FAST MODE SUMMARY (site synthetic tests): ok_sites={len(successful_results)} fail_sites={len(failed_sites)} total_sites={len(site_ids)} records={len(all_results)} elapsed={duration:.2f}s")
    else:
        smoothed = None
        for site_id in tqdm(site_ids, desc="Sites", unit="site"):
            results = fetch_site_tests(site_id, connection_semaphore=None)
            if results:
                all_results.extend(results)
            smoothed, delay = get_rate_limited_delay(smoothed)
            time.sleep(delay)

    if all_results:
        filename = "AllGatewayTestResults.csv"
        flattened = flatten_nested_fields_in_list(all_results)
        sanitized = escape_multiline_strings_for_csv(flattened)
        DataExporter.save_data_to_output(sanitized, filename)
        print(f"! {len(all_results)} gateway test results exported to {filename}")
        logging.info(f"! All test results saved to {filename} ({len(all_results)} records).")
        if fast:
            logging.info(f"! API Optimization: Saved site-level repeat lookups by using cached inventory for site derivation")
    else:
        logging.warning(" No test results found. CSV not created.")
        print("! No gateway test results found. CSV not created.")

def export_gateway_device_stats_to_csv_with_freshness_check(fast=False):
    """
    Wrapper function that checks if AllGatewayDeviceStats.csv exists and is fresh before generating it.
    This ensures we don't unnecessarily regenerate data that's already current.
    """
    output_file = "AllGatewayDeviceStats.csv"
    
    # Check if file exists and is fresh
    if check_and_generate_csv(output_file, lambda: export_gateway_device_stats_to_csv(fast=fast)):
        logging.info(f"! {output_file} already exists and is fresh - using cached data")
    else:
        logging.info(f"! {output_file} was generated or refreshed")

def export_gateway_device_stats_to_csv(fast=False):
    """
    Collects and exports detailed device statistics for all gateways in the organization.
    Makes individual getSiteDeviceStats API calls for each gateway device.
    Optimized to use cached inventory data and concurrent processing when fast=True.
    
    Args:
        fast (bool): If True, enables concurrent processing and uses cached inventory data
                    to minimize API calls.
    """
    logging.info("[INFO] Collecting detailed device statistics for all gateways in the org...")
    if fast:
        logging.info(" Fast mode enabled: Using cached data and concurrent processing")
    
    org_id = get_cached_or_prompted_org_id()
    gateway_devices = get_gateway_devices_with_sites(apisession, org_id, fast=fast)
    all_stats = []

    if not gateway_devices:
        logging.warning("[WARN] No gateway devices found. Exiting export_gateway_device_stats_to_csv.")
        return

    def fetch_device_stats_with_retry(device_info, max_retries=None, retry_delay=None, connection_semaphore=None):
        """
        Fetch device statistics for a single gateway device with retry logic and connection pool management.
        
        Args:
            device_info: Tuple of (site_id, device_id, device_name, site_name)
            max_retries: Maximum number of retry attempts (uses env var if None)
            retry_delay: Base delay between retries (uses env var if None)
            connection_semaphore: Semaphore to limit concurrent connections (optional)
        """
        # Use environment variables as defaults if not provided
        if max_retries is None:
            max_retries = FAST_MODE_MAX_RETRIES
        if retry_delay is None:
            retry_delay = FAST_MODE_RETRY_DELAY
            
        site_id, device_id, device_name, site_name = device_info
        
        for attempt in range(max_retries + 1):
            try:
                # Validate inputs before making API calls
                validate_site_id(site_id, "export_gateway_device_stats_to_csv")
                validate_device_id(device_id, "export_gateway_device_stats_to_csv")
                
                # Use semaphore to limit concurrent connections if provided
                if connection_semaphore:
                    with connection_semaphore:
                        stats = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id).data
                else:
                    stats = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id).data
                
                # Add contextual information to the stats
                stats["site_id"] = site_id
                stats["site_name"] = site_name
                stats["device_id"] = device_id
                stats["device_name"] = device_name
                
                if attempt > 0:
                    logging.info(f"! Retry {attempt} successful for device {device_name} at site {site_name}")
                else:
                    logging.debug(f"! Collected device stats for gateway {device_name} at site {site_name}")
                return stats
                
            except Exception as e:
                if attempt < max_retries:
                    # Fast mode: reduced backoff delay for quicker retries
                    backoff_delay = retry_delay * (2 ** attempt) if not fast else retry_delay
                    logging.warning(f"! Attempt {attempt + 1} failed for device {device_name} at site {site_name}: {e}")
                    logging.info(f"! Retrying in {backoff_delay} seconds...")
                    time.sleep(backoff_delay)
                else:
                    logging.error(f"! Failed to fetch device stats for {device_name} at site {site_name} after {max_retries + 1} attempts: {e}")
                    # Return a minimal record with error information
                    return {
                        "site_id": site_id,
                        "site_name": site_name,
                        "device_id": device_id,
                        "device_name": device_name,
                        "error": str(e),
                        "status": "failed"
                    }

    # Process devices with appropriate threading based on fast mode
    if fast and len(gateway_devices) > 10:
        # Use concurrent processing for large numbers of devices
        logging.info(f"! Fast mode: Processing {len(gateway_devices)} gateway devices concurrently...")
        
        # Limit concurrent connections to prevent overwhelming the API
        max_workers = min(10, len(gateway_devices))  # Cap at 10 concurrent requests
        connection_semaphore = threading.Semaphore(max_workers)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    fetch_device_stats_with_retry, 
                    device_info, 
                    connection_semaphore=connection_semaphore
                ): device_info for device_info in gateway_devices
            }
            
            # Progress bar for concurrent processing
            for future in tqdm(concurrent.futures.as_completed(futures), 
                             total=len(futures), 
                             desc="Gateway Device Stats", 
                             unit="device"):
                device_info = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_stats.append(result)
                except Exception as e:
                    site_id, device_id, device_name, site_name = device_info
                    logging.error(f"! Concurrent processing failed for device {device_name} at site {site_name}: {e}")
    else:
        # Sequential processing for smaller datasets or normal mode
        logging.info(f"! Processing {len(gateway_devices)} gateway devices sequentially...")
        for i, device_info in enumerate(tqdm(gateway_devices, desc="Gateway Device Stats", unit="device"), 1):
            site_id, device_id, device_name, site_name = device_info
            logging.debug(f"! Processing device {i}/{len(gateway_devices)}: {device_name} at {site_name}")
            
            result = fetch_device_stats_with_retry(device_info)
            if result:
                all_stats.append(result)

    # Save results to CSV
    if all_stats:
        # Sanitize and flatten nested data structures
        sanitized = []
        for stats in all_stats:
            flat_record = flatten_dict_recursively(stats)
            sanitized.append(flat_record)
        
        filename = "AllGatewayDeviceStats.csv"
        DataExporter.save_data_to_output(sanitized, filename)
        logging.info(f"! Gateway device statistics saved to {filename} ({len(all_stats)} records).")
        logging.info(f"! API Optimization: Collected detailed stats for {len(gateway_devices)} gateways")
        
        # Log summary of successful vs failed requests
        successful_requests = len([s for s in all_stats if s.get("status") != "failed"])
        failed_requests = len(all_stats) - successful_requests
        if failed_requests > 0:
            logging.warning(f"! {failed_requests} requests failed out of {len(all_stats)} total")
        else:
            logging.info(f"! All {successful_requests} requests completed successfully")
    else:
        logging.warning(" No gateway device statistics found. CSV not created.")

def export_gateways_with_wan_port_conflicts_to_csv():
    """
    Checks if AllGatewayDeviceStats.csv exists and is fresh. If not, generates it.
    Then exports a filtered CSV showing gateways that have IP address conflicts WITHIN the same device:
    - Same IP address assigned to multiple WAN ports (0/0/0, 0/0/1, 0/0/2)
    
    Note: Next hop gateway conflicts are not checked since this data is not available in the CSV.
    """
    logging.info(" Starting WAN port IP conflict analysis for individual gateway devices...")
    
    # Check if AllGatewayDeviceStats.csv exists and is fresh using existing helper
    stats_file = "AllGatewayDeviceStats.csv"
    
    check_and_generate_csv(stats_file, lambda: export_gateway_device_stats_to_csv(fast=True))
    
    # Load the gateway device stats using CSV reader
    stats_path = get_csv_file_path(stats_file)
    try:
        gateway_data = []
        with open(stats_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            gateway_data = list(reader)
        
        logging.info(f"! Loaded {len(gateway_data)} gateway device records for analysis")
    except Exception as e:
        logging.error(f"! Failed to load {stats_file}: {e}")
        print(f"! Failed to load {stats_file}: {e}")
        return
    
    # Define WAN port columns to analyze
    wan_ports = ['0/0/0', '0/0/1', '0/0/2'] 
    ip_columns = [f'if_stat_ge-{port}_ips' for port in wan_ports]
    
    # Find gateways with internal WAN port IP conflicts
    logging.info(" Analyzing individual gateways for internal WAN port IP conflicts...")
    
    conflicts_found = []
    
    for i, row in enumerate(gateway_data):
        device_name = row.get('device_name', row.get('name', f"Device_{i}"))
        site_name = row.get('site_name', 'Unknown Site')
        
        # Collect IP addresses for this device's WAN ports
        device_ips = {}  # {ip: [port1, port2, ...]}
        
        # Collect IP addresses from WAN ports
        for col in ip_columns:
            if col in row and row[col] and str(row[col]).strip():
                ip_value = str(row[col]).strip()
                if ip_value not in ['', 'nan', 'None', 'null']:
                    port = col.replace('if_stat_ge-', '').replace('_ips', '')
                    
                    if ip_value not in device_ips:
                        device_ips[ip_value] = []
                    device_ips[ip_value].append(port)
        
        # Check for IP conflicts within this gateway (same IP on multiple ports)
        ip_conflicts = []
        for ip, ports in device_ips.items():
            if len(ports) > 1:
                ip_conflicts.append({
                    'type': 'IP Address Conflict',
                    'value': ip,
                    'ports': ports,
                    'port_count': len(ports)
                })
                logging.warning(f"! IP conflict in {device_name}: {ip} assigned to ports {', '.join(ports)}")
        
        # If this gateway has IP conflicts, add simplified records for each conflicted port
        if ip_conflicts:
            # Add records for IP conflicts - one line per conflicted port
            for conflict in ip_conflicts:
                for port in conflict['ports']:
                    conflicts_found.append({
                        'device_name': device_name,
                        'site_name': site_name,
                        'port_name': f"ge-{port}",
                        'port_ip': conflict['value'],
                        'conflict_type': 'IP Address Conflict',
                        'conflict_with_ports': ', '.join([p for p in conflict['ports'] if p != port])
                    })
    
    # Export results
    if conflicts_found:
        output_file = "GatewayWANPortConflicts.csv"
        
        # Sort by device name and port name
        conflicts_found.sort(key=lambda x: (x.get('device_name', ''), x.get('port_name', '')))
        
        # Save to CSV using existing helper
        DataExporter.save_data_to_output(conflicts_found, output_file)
        
        logging.info(f"! WAN port IP conflicts exported to {output_file} ({len(conflicts_found)} conflicted port records)")
        print(f"! WAN port IP conflicts exported to {output_file} ({len(conflicts_found)} conflicted port records)")
        
        # Display summary
        unique_gateways = set()
        ip_conflict_ports = len(conflicts_found)
        
        for record in conflicts_found:
            unique_gateways.add(record.get('device_name', 'Unknown'))
        
        logging.info(f"! Summary: {len(unique_gateways)} gateways with IP conflicts ({ip_conflict_ports} conflicted ports)")
        print(f"! Summary: {len(unique_gateways)} gateways with IP conflicts ({ip_conflict_ports} conflicted ports)")
        
        # Show sample of conflicted ports
        print(f"\n  Sample WAN Port IP Conflicts Found:")
        for i, record in enumerate(conflicts_found[:10], 1):
            print(f"{i:2d}. {record.get('device_name', 'Unknown')} ({record.get('site_name', 'Unknown Site')})")
            print(f"    Port {record.get('port_name', 'Unknown')} has IP {record.get('port_ip', 'Unknown')}")
            print(f"    Conflicts with port(s): {record.get('conflict_with_ports', 'Unknown')}")
            print()
        
        if len(conflicts_found) > 10:
            print(f"... and {len(conflicts_found) - 10} more conflicted ports")
        
    else:
        logging.info(" No internal WAN port IP conflicts found - all gateways have unique IP addresses per WAN port")
        print(" No internal WAN port IP conflicts found - all gateways have unique IP addresses per WAN port")
        print(" This indicates healthy WAN port configurations with no duplicate IP assignments within individual gateways")

def export_sites_with_location_to_csv():
    """
    Export a list of sites with all available fields to SitesWithLocations.csv.
    """
    print("Sites with Location and Timezone Info:")
    logging.info("Listing Sites with Full Info:")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"Using org_id: {org_id} for site location export.")

    # Fetch all sites using unified page size helper
    sites = fetch_all_sites_with_limit(org_id)
    logging.info(f"Fetched {len(sites)} sites from the organization.")

    # Flatten and sanitize all site data
    flattened_sites = flatten_nested_fields_in_list(sites)
    sanitized_sites = escape_multiline_strings_for_csv(flattened_sites)

    # Write to CSV
    DataExporter.save_data_to_output(sanitized_sites, "SitesWithLocations.csv")
    print(f"! {len(sanitized_sites)} sites exported to SitesWithLocations.csv")
    logging.info(" Full site data written to SitesWithLocations.csv")

def export_gateways_with_site_info_to_csv():
    """
    Fetches all gateway devices in the organization, enriches them with site and address info,
    and exports the result to GatewaysWithSiteInfo.csv. Also logs and displays a summary table.
    """
    print("Gateways with Site and Address Info:")
    logging.info("Fetching Gateways with Site Info...")
    org_id = get_cached_or_prompted_org_id()

    # Fetch site list and build a lookup dictionary for site info
    sites = fetch_all_sites_with_limit(org_id)
    site_lookup = {
        site["id"]: {
            "name": site.get("name", ""),
            "address": site.get("address", "")
        } for site in sites
    }
    logging.debug(f"Loaded {len(site_lookup)} sites for lookup.")

    # Fetch org inventory (all devices)
    inventory = fetch_all_inventory_with_limit(org_id)
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
    DataExporter.save_data_to_output(gateways, "GatewaysWithSiteInfo.csv")
    print(f"! {len(gateways)} gateways exported to GatewaysWithSiteInfo.csv")
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

def export_devices_with_site_info_to_csv(fast=False):
    """
    Fetches all devices in the organization, enriches them with site and address info,
    and exports the result to AllDevicesWithSiteInfo.csv. Also logs and displays a summary table.
    
    Args:
        fast (bool): If True, enables optimized processing mode with enhanced caching
                    and concurrent site lookups where applicable.
    """
    print("All Devices with Site and Address Info:")
    logging.info("Fetching All Devices with Site Info...")  # Log start of function
    if fast:
        logging.info(" Fast mode enabled for devices with site info export")
    
    org_id = get_cached_or_prompted_org_id()

    # Ensure required CSV files are available, using caching where possible
    if fast:
        # Use cached data when fast mode is enabled
        check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
        check_and_generate_csv("OrgInventory.csv", export_device_inventory_to_csv)
        
        # Load from cached CSV files instead of making API calls
        site_lookup = {}
        try:
            site_list_path = get_csv_file_path("SiteList.csv")
            with open(site_list_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                site_lookup = {
                    row["id"]: {
                        "name": row.get("name", ""),
                        "address": row.get("address", "")
                    } for row in reader
                }
            logging.debug(f"Loaded {len(site_lookup)} sites from cached SiteList.csv")
        except Exception as e:
            logging.warning(f"Failed to load from cached SiteList.csv, falling back to API: {e}")
            # Fallback to API if cached data fails
            sites = fetch_all_sites_with_limit(org_id)
            site_lookup = {
                site["id"]: {
                    "name": site.get("name", ""),
                    "address": site.get("address", "")
                } for site in sites
            }
            logging.debug(f"Loaded {len(site_lookup)} sites from API fallback")

        # Load inventory from cached CSV
        inventory = []
        try:
            inventory_path = get_csv_file_path("OrgInventory.csv")
            with open(inventory_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                inventory = list(reader)
            logging.debug(f"Loaded {len(inventory)} devices from cached OrgInventory.csv")
        except Exception as e:
            logging.warning(f"Failed to load from cached OrgInventory.csv, falling back to API: {e}")
            # Fallback to API if cached data fails
            inventory = fetch_all_inventory_with_limit(org_id)
            logging.debug(f"Loaded {len(inventory)} devices from API fallback")
    else:
        # Original behavior: fetch directly from API
        # Fetch all sites and build a lookup dictionary for site info
        sites = fetch_all_sites_with_limit(org_id)
        site_lookup = {
            site["id"]: {
                "name": site.get("name", ""),
                "address": site.get("address", "")
            } for site in sites
        }
        logging.debug(f"Loaded {len(site_lookup)} sites for lookup.")

        # Fetch org inventory (all devices)
        inventory = fetch_all_inventory_with_limit(org_id)
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
    DataExporter.save_data_to_output(enriched_devices, "AllDevicesWithSiteInfo.csv")
    print(f"! {len(enriched_devices)} devices exported to AllDevicesWithSiteInfo.csv")
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
        logging.warning(" AllGatewayTestResults.csv not found. Skipping speedtest data.")
        speedtest_data = {}

    # Create a support package for each site with alarms or events
    for site_id, site_info in site_data.items():
        # Only generate support package if there are alarms or events for the site
        if not alarms_data.get(site_id) and not events_data.get(site_id):
            logging.info(f"Skipping site {site_id} � no alarms or events.")
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

    logging.info(" Support packages generated for applicable sites.")
    logging.info(" Support packages generated for all sites!")

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
    logging.info(" Starting Marvis (VNA) troubleshooting workflow...")
    logging.debug("MARVIS DEBUG: Entering poll_marvis_actions() function")
    print(" Starting Marvis (VNA - Virtual Network Assistant) Troubleshooting")
    print("=" * 65)
    print()
    
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id} for Marvis troubleshooting")
    logging.debug(f"MARVIS DEBUG: Session state - authenticated: {apisession is not None}")

    print(" Marvis AI Troubleshooting Options:")
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
        print(" Invalid option selected.")
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
    print("\n  Client Selection")
    print("=" * 30)
    
    # If no site_id provided, decide between site-specific or org-wide search
    if not site_id:
        scope_choice = input("Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ").strip().lower()
        if scope_choice == 's':
            site_id = prompt_site_selection()
            if not site_id:
                print(" No site selected.")
                return None, None, None
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        all_clients = []
        
        if site_id:
            # Site-specific client search
            print(f"! Searching for clients in selected site...")
            
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
            print(f"! Searching for clients across organization...")
            
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
            print(" No clients found.")
            return None, None, None
        
        # Sort clients by hostname, then MAC
        all_clients = sorted(all_clients, key=lambda x: (x.get('hostname', ''), x.get('mac', '')))
        
        # Prepare table for selection
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
            print(" Loading site information...")
            sites = fetch_all_sites_with_limit(org_id)
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
            status = "??" if client.get('connected', True) else "??"
            if 'last_seen' in client:
                last_seen = client.get('last_seen', 0)
                current_time = int(time.time())
                if current_time - last_seen > 300:  # More than 5 minutes ago
                    status = "??"
            
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
        
        print(f"\n  Found {len(all_clients)} clients:")
        print(table)
        
        # Show summary statistics
        wireless_count = sum(1 for c in all_clients if c.get('client_type') == 'wireless')
        wired_count = sum(1 for c in all_clients if c.get('client_type') == 'wired')
        print(f"\n  Summary: {wireless_count} wireless, {wired_count} wired clients")
        
        # Show legend
        print("\n  = Online  = Recently seen  = Offline")
        print("---" * 20)
        
        # Get user selection
        try:
            max_index = len(all_clients) - 1
            user_input = input(f"\n  Enter client index (0-{max_index}) or 'q' to quit: ").strip()
                
            if user_input.lower() in ['q', 'quit', 'exit']:
                print(" Exiting client selection...")
                return None, None, None
                
            idx = int(user_input)
            if 0 <= idx <= max_index:
                selected_client = index_to_client[idx]
                client_mac = selected_client.get('mac')
                client_type = selected_client.get('client_type', 'unknown')
                client_site_id = selected_client.get('site_id', site_id)
                hostname = selected_client.get('hostname', selected_client.get('name', 'Unknown'))
                
                print(f"\n Selected client:")
                print(f"   Name: {hostname}")
                print(f"   MAC: {client_mac}")
                print(f"   Type: {client_type}")
                if client_site_id and client_site_id in sites_cache:
                    print(f"   Site: {sites_cache[client_site_id]}")
                
                logging.info(f"User selected client: MAC={client_mac}, type={client_type}, site={client_site_id}")
                return client_mac, client_type, client_site_id
            else:
                print(f"! Invalid index. Please enter a number between 0 and {max_index}.")
                return None, None, None
                
        except ValueError:
            print(" Please enter a valid number or 'q' to quit.")
            return None, None, None
            
    except Exception as e:
        logging.error(f"Error during client selection: {e}")
        print(f"! Error searching for clients: {e}")
        return None, None, None

def troubleshoot_client_connectivity():
    """
    Troubleshoot client connectivity issues using Marvis AI.
    Uses guided client selection instead of manual MAC address entry.
    """
    print("\n  Client Connectivity Troubleshooting")
    print("=" * 50)
    
    # Use guided client selection
    client_mac, client_type, site_id = prompt_client_selection()
    if not client_mac:
        print(" No client selected. Returning to main menu.")
        return
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        print(f"! Running Marvis AI analysis for client {client_mac}...")
        print(f"   Client Type: {client_type}")
        if site_id:
            print(f"   Site ID: {site_id}")
        
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
            print(" Marvis AI analysis completed!")
            print(f"! Analysis results available.")
            
            # Save results to CSV with optimized formatting
            data = format_marvis_data_for_csv(response.data, "client")
            
            filename = f"MarvisInsights_Client_{client_mac.replace(':', '')}_{client_type}.csv"
            DataExporter.save_data_to_output(data, filename)
            print(f"! Results saved to {filename}")
            
            # Display summary
            if isinstance(response.data, dict):
                if 'results' in response.data:
                    print("\n  Marvis Analysis Summary:")
                    for result in response.data.get('results', []):
                        print(f"  � {result.get('description', 'Analysis result')}")
                        if result.get('action'):
                            print(f"    Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    print("\n  Marvis Insights:")
                    insights = response.data.get('insights', [])
                    for insight in insights:
                        print(f"  � {insight.get('description', insight)}")
                else:
                    print(f"\n  Analysis Data: {len(data)} items processed")
        else:
            print(" No specific connectivity issues found for this client.")
            print(" This could indicate the client is functioning normally.")
            
    except Exception as e:
        logging.error(f"Failed to troubleshoot client {client_mac}: {e}")
        print(f"! Failed to troubleshoot client: {e}")
        print(" This may indicate:")
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
    print("\n  Device Performance Troubleshooting")
    print("=" * 50)
    
    # Get site selection first
    site_id = prompt_site_selection()
    if not site_id:
        print(" No site selected.")
        logging.debug("MARVIS DEBUG: No site selected for device troubleshooting")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected site_id: {site_id}")
    
    # Get device selection
    device_id = prompt_device_selection(site_id)
    if not device_id:
        print(" No device selected.")
        logging.debug("MARVIS DEBUG: No device selected")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected device_id: {device_id}")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id}")
    
    try:
        # Get device MAC address from device ID
        print(f"! Looking up device details...")
        logging.debug(f"MARVIS DEBUG: About to get device details for device_id: {device_id} in site: {site_id}")
        
        device_response = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
        logging.debug(f"MARVIS DEBUG: Device lookup response status: {device_response.status if hasattr(device_response, 'status') else 'unknown'}")
        
        if not device_response.data:
            print(" Could not retrieve device details.")
            logging.debug("MARVIS DEBUG: Device response data is None")
            return
            
        logging.debug(f"MARVIS DEBUG: Device data keys: {list(device_response.data.keys()) if isinstance(device_response.data, dict) else 'not a dict'}")
        
        device_mac = device_response.data.get('mac')
        device_name = device_response.data.get('name', 'Unknown Device')
        
        logging.debug(f"MARVIS DEBUG: Device MAC: {device_mac}")
        logging.debug(f"MARVIS DEBUG: Device name: {device_name}")
        
        if not device_mac:
            print(" Could not determine device MAC address.")
            logging.debug("MARVIS DEBUG: Device MAC is None or empty")
            return
        
        print(f"! Running Marvis AI performance analysis...")
        print(f"   Device: {device_name} ({device_mac})")
        print(f"   Site ID: {site_id}")
        
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
            
            print(" Marvis AI device analysis completed!")
            
            # Save results to CSV with optimized formatting
            data = format_marvis_data_for_csv(response.data, "device")
            logging.debug(f"MARVIS DEBUG: Formatted device data length: {len(data) if data else 0}")
            
            filename = f"MarvisInsights_Device_{device_mac.replace(':', '')}_{device_name.replace(' ', '_')}.csv"
            DataExporter.save_data_to_output(data, filename)
            print(f"! Results saved to {filename}")
            
            # Display summary if available
            if isinstance(response.data, dict):
                if 'results' in response.data:
                    results = response.data.get('results', [])
                    logging.debug(f"MARVIS DEBUG: Found {len(results)} device results")
                    print("\n  Device Performance Analysis:")
                    for result in results:
                        print(f"  � {result.get('description', 'Analysis result')}")
                        if result.get('action'):
                            print(f"    Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    print("\n  Marvis Device Insights:")
                    insights = response.data.get('insights', [])
                    logging.debug(f"MARVIS DEBUG: Found {len(insights)} device insights")
                    for insight in insights:
                        print(f"  � {insight.get('description', insight)}")
                else:
                    logging.debug("MARVIS DEBUG: No results or insights in device response")
                    print(f"\n  Analysis Data: {len(data)} items processed")
            
        else:
            logging.debug("MARVIS DEBUG: Device response data is None or empty")
            print(" No performance issues detected for this device.")
            print(" This could indicate the device is operating within normal parameters.")
            
    except Exception as e:
        logging.error(f"MARVIS DEBUG: Exception in troubleshoot_device_performance: {e}")
        logging.error(f"MARVIS DEBUG: Exception type: {type(e)}")
        logging.error(f"MARVIS DEBUG: Exception traceback: ", exc_info=True)
        print(f"! Failed to troubleshoot device: {e}")
        print(" This may indicate:")
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
    print("\n  Network Connectivity Troubleshooting")
    print("=" * 50)
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        print(" No site selected.")
        logging.debug("MARVIS DEBUG: No site selected, exiting network troubleshooting")
        return
    
    logging.debug(f"MARVIS DEBUG: Selected site_id: {site_id}")
    org_id = get_cached_or_prompted_org_id()
    logging.debug(f"MARVIS DEBUG: Using org_id: {org_id}")
    
    try:
        print(f"! Running Marvis AI network analysis...")
        print(f"   Analyzing site-level connectivity")
        print(f"   Site ID: {site_id}")
        
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
            
            print(" Marvis AI network analysis completed!")
            
            # Save results to CSV with optimized formatting
            logging.debug("MARVIS DEBUG: About to format data for CSV")
            data = format_marvis_data_for_csv(response.data, "network")
            logging.debug(f"MARVIS DEBUG: Formatted data length: {len(data) if data else 0}")
            logging.debug(f"MARVIS DEBUG: Formatted data sample: {data[:1] if data else 'empty'}")
            
            filename = f"MarvisInsights_Network_{site_id}.csv"
            DataExporter.save_data_to_output(data, filename)
            print(f"! Results saved to {filename}")
            logging.debug(f"MARVIS DEBUG: Saved data to {filename}")
            
            # Display summary if available
            if isinstance(response.data, dict):
                logging.debug("MARVIS DEBUG: Response data is a dict, checking for results/insights")
                if 'results' in response.data:
                    results = response.data.get('results', [])
                    logging.debug(f"MARVIS DEBUG: Found 'results' key with {len(results)} items")
                    print("\n  Network Connectivity Analysis:")
                    for idx, result in enumerate(results):
                        logging.debug(f"MARVIS DEBUG: Processing result {idx}: {result}")
                        description = result.get('description', 'Analysis result') if isinstance(result, dict) else str(result)
                        print(f"  � {description}")
                        if isinstance(result, dict) and result.get('action'):
                            print(f"    Recommended Action: {result['action']}")
                elif 'insights' in response.data:
                    insights = response.data.get('insights', [])
                    logging.debug(f"MARVIS DEBUG: Found 'insights' key with {len(insights)} items")
                    print("\n  Marvis Network Insights:")
                    for idx, insight in enumerate(insights):
                        logging.debug(f"MARVIS DEBUG: Processing insight {idx}: {insight}")
                        description = insight.get('description', insight) if isinstance(insight, dict) else str(insight)
                        print(f"  � {description}")
                else:
                    logging.debug("MARVIS DEBUG: No 'results' or 'insights' keys found in response data")
                    logging.debug(f"MARVIS DEBUG: Available keys in response: {list(response.data.keys())}")
                    print(f"\n  Analysis Data: {len(data)} items processed")
                    if response.data:
                        print(f"! Raw response keys: {list(response.data.keys())}")
                        # Show some raw data for debugging
                        for key, value in list(response.data.items())[:5]:
                            print(f"   {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                logging.debug(f"MARVIS DEBUG: Response data is not a dict, type: {type(response.data)}")
                print(f"\n  Raw response: {str(response.data)[:200]}{'...' if len(str(response.data)) > 200 else ''}")
            
        else:
            logging.debug("MARVIS DEBUG: Response data is None or empty")
            print(" No network connectivity issues detected for this site.")
            print(" This indicates the network is operating within normal parameters.")
            
    except Exception as e:
        logging.error(f"MARVIS DEBUG: Exception in troubleshoot_network_connectivity: {e}")
        logging.error(f"MARVIS DEBUG: Exception type: {type(e)}")
        logging.error(f"MARVIS DEBUG: Exception traceback: ", exc_info=True)
        print(f"! Failed to troubleshoot network: {e}")
        print(" This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - The site has no devices or insufficient data for analysis")
        print("   - Insufficient permissions for network troubleshooting")
    
    logging.debug("MARVIS DEBUG: Exiting troubleshoot_network_connectivity()")

def view_marvis_insights():
    """
    View available Marvis (VNA) insights and capabilities for the organization.
    This provides information about Marvis availability and organizational insights.
    """
    print("\n  Marvis (VNA) Insights & Capabilities")
    print("=" * 50)
    
    org_id = get_cached_or_prompted_org_id()
    
    try:
        print(" Checking Marvis availability and organizational insights...")
        
        # Try to get organization info to check Marvis capabilities
        org_response = mistapi.api.v1.orgs.orgs.getOrg(apisession, org_id)
        
        if org_response.data:
            org_info = org_response.data
            print(f"! Organization: {org_info.get('name', 'Unknown')}")
            
            # Check for Marvis-related features
            features = org_info.get('features', [])
            marvis_features = [f for f in features if any(keyword in f.lower() for keyword in ['marvis', 'vna', 'insight'])]
            
            if marvis_features:
                print("\n  Marvis/VNA Features Available:")
                for feature in marvis_features:
                    print(f"  � {feature}")
            else:
                print("\n  No specific Marvis/VNA features detected in organization settings.")
            
            # Try to get organization-level insights if available
            try:
                print("\n Attempting to retrieve organization-level insights...")
                
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
                                print(f"\n  {endpoint_name}:")
                                for insight in insights_data[:5]:  # Show first 5 insights
                                    description = insight.get('description', insight.get('type', insight.get('name', str(insight))))
                                    print(f"  � {description}")
                                
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
                                DataExporter.save_data_to_output(formatted_insights, filename)
                                print(f"  Full insights saved to {filename}")
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
                    print("\n  No organization-level insights currently available.")
                
            except Exception as e:
                logging.warning(f"Could not retrieve organization insights: {e}")
                print(f"! Could not retrieve insights: {e}")
            
            print("\n  Marvis (VNA - Virtual Network Assistant) Usage Guide:")
            print("   Targeted Troubleshooting:")
            print("     � Use client troubleshooting for specific device connectivity issues")
            print("     � Use device troubleshooting for AP, switch, or gateway performance")
            print("     � Use network troubleshooting for site-wide connectivity analysis")
            print()
            print("   Requirements:")
            print("     � Marvis must be enabled for your organization")
            print("     � Devices must be actively managed and reporting data")
            print("     � Sufficient data history for meaningful analysis")
            print()
            print("   Best Practices:")
            print("     � Run troubleshooting when issues are actively occurring")
            print("     � Provide specific timeframes when prompted")
            print("     � Review saved CSV files for detailed analysis results")
            
        else:
            print(" Could not retrieve organization information.")
            
    except Exception as e:
        logging.error(f"Failed to get Marvis insights: {e}")
        print(f"! Failed to get Marvis insights: {e}")
        print(" This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - Insufficient permissions to view organization details")
        print("   - API connectivity issues")
        print("   - Organization may not have Marvis licensing")
        print()
        print(" Contact your Mist administrator to:")
        print("   � Verify Marvis/VNA licensing and enablement")
        print("   � Confirm user permissions for AI troubleshooting")
        print("   � Check organization feature settings")

def export_current_guest_users_to_csv():
    """
    Export all current guest users in the org to OrgCurrentGuests.csv
    """
    print("Current and Historical Guest Users:")
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
    DataExporter.save_data_to_output(guests, "OrgCurrentGuests.csv")
    print(f"! {len(guests)} current guest users exported to OrgCurrentGuests.csv")
    logging.info(" Current guests exported to OrgCurrentGuests.csv")  # Log completion

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
    DataExporter.save_data_to_output(guests, "OrgHistoricalGuests.csv")
    print(f"! {len(guests)} historical guest users exported to OrgHistoricalGuests.csv")
    logging.info(" Historical guests exported to OrgHistoricalGuests.csv")  # Log completion

def export_switch_vc_stats_to_csv():
    """
    Export virtual chassis stats (including stacking cable info) for all switches in the org.
    """
    print("Switch Virtual Chassis Statistics:")
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
    DataExporter.save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv")
    print(f"! {len(all_vc_stats)} switch VC stats exported to OrgSwitchVCStats.csv")
    logging.info(f"! Switch VC stats exported to OrgSwitchVCStats.csv ({len(all_vc_stats)} records).")
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
            print(" No site selected.")
            return None, None

    if not device_id:
        device_id = prompt_select_device_id_from_inventory(site_id, device_type="all")
        if not device_id:
            print(" No device selected.")
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
        print(f"! Failed to create shell session: {e}")
        return None

def run_interactive_shell(shell_url, debug=False):
    if debug:
        websocket.enableTrace(True)

    print(" Connecting to WebSocket shell...")
    ws = websocket.create_connection(shell_url)
    print(" Connected.")

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
        logging.error(f"! WebSocket error: {error}")

    def on_open(ws):
        logging.info(" WebSocket opened. Subscribing...")
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
            logging.info(" Idle timeout reached. Closing WebSocket.")
            ws.close()
            break

    if ws.keep_running:
        logging.warning(" Timeout waiting for ARP output.")
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
    logging.info(" WebSocket closed.")
    if output_lines:
        compiled_output = "\n".join(output_lines)
        _save_output_to_file(compiled_output)
        export_arp_output_to_csv("arp_output_raw.txt")


        print("\n  ARP Output Received:\n")
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
            logging.info(f"! Compiled ARP Output:\n{compiled_output}")
            logging.debug("\n" + table.get_string())
        else:
            print(f"! ARP output received with {len(parsed_rows)} rows.")
    else:
        print(" No ARP output received for this session.")
        logging.warning(" No ARP output received for this session.")

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

        print(f"! Saved {len(dataset1)} rows to {csv1}")
        print(f"! Saved {len(dataset2)} rows to {csv2}")

    except Exception as e:
        print(f"! Failed to export ARP output to CSV: {e}")

def _save_output_to_file(compiled_output, filename="arp_output_raw.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(compiled_output)
        logging.info(f"! ARP output saved to {filename}")
    except Exception as e:
        logging.error(f"! Failed to save ARP output to file: {e}")

def trigger_arp_command(mist_host, mist_apitoken, site_id, device_id):
    url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"
    headers = {'Authorization': f'Token {mist_apitoken}'}
    response = requests.post(url, headers=headers, json={})

    if response.status_code == 200:
        session_id = response.json().get("session")
        print(f"! ARP command triggered. Session ID: {session_id}")
        return session_id
    else:
        print(f"! Failed to trigger ARP command: {response.status_code}")
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
        print(" Mist host or API token not found in session or environment.")
        return

    print(" Subscribing to WebSocket stream...")
    session_id = trigger_arp_command(mist_host, mist_apitoken, site_id, device_id)
    if session_id:
        listen_for_command_output(mist_host.replace("api.", "api-ws."), mist_apitoken, site_id, device_id, session_id)

def loop_refresh_core_datasets(delay=None, debug=False):
    """
    Continuously refreshes core datasets with optional dynamic delay based on API usage.
    If delay is None, it will be calculated dynamically to avoid exceeding API limits.
    Loop can be stopped gracefully by creating a file named 'stop_loop.txt'.
    """
    logging.info(" Starting continuous data refresh loop...")
    smoothed = None  # Initialize smoothed delay tracker
    get_cached_or_prompted_org_id()  # Ensure org_id is loaded from .env if not already

    try:
        while True:
            if os.path.exists("stop_loop.txt"):
                logging.info(" Stop signal detected (stop_loop.txt). Exiting loop.")
                break

            export_all_sites_to_csv()
            export_device_inventory_to_csv()
            export_device_stats_to_csv()
            export_device_port_stats_to_csv()
            export_vpn_peer_stats_to_csv()
            logging.info(" All datasets refreshed.")

            # Determine delay
            if delay is not None:
                actual_delay = delay
            else:
                smoothed, actual_delay = get_rate_limited_delay(smoothed)

            logging.info(f"! Sleeping for {actual_delay:.2f} seconds...")
            time.sleep(actual_delay)

    except KeyboardInterrupt:
        logging.info(" Loop interrupted by user (Ctrl+C). Exiting gracefully.")

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
        logging.error(" Could not create shell session.")
        return

    try:
        ws = websocket.create_connection(shell_url)
        print(" Connected to shell session.")
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
        print(" WebSocket output saved to ws.log")

    except Exception as e:
        print(f"! Error during shell session: {e}")

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
    logging.info(" Gateway templates exported to OrgGatewayTemplates.csv.")

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
        logging.error(" Could not create shell session.")
        return

    try:
        ws = websocket.create_connection(shell_url)
        print(" Connected to shell session.")
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
        print(" DHCP security binding output saved to ws_dhcp.log")

    except Exception as e:
        print(f"! Error during shell session: {e}")

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
        logging.error("!! Could not create shell session.")
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
        logging.warning(" No device configs found.")
        return

    # Flatten and sanitize the data
    flattened = flatten_nested_fields_in_list(data)
    sanitized = escape_multiline_strings_for_csv(flattened)

    # Write full dataset to CSV
    DataExporter.save_data_to_output(sanitized, "AllSiteGatewayConfigs.csv")
    logging.info(" Device configs saved to AllSiteGatewayConfigs.csv")

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
        logging.warning(" No rows matched the port config filter. FilteredGatewayPortConfigs.csv will be empty.")
        filtered_csv_path = get_csv_file_path("FilteredGatewayPortConfigs.csv")
        with open(filtered_csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("No matching data found.\n")
    else:
        if debug:
            logging.debug(f"Sample filtered row: {filtered_rows[0]}")
        DataExporter.save_data_to_output(filtered_rows, "FilteredGatewayPortConfigs.csv")
        logging.info(" Filtered gateway port configs saved to FilteredGatewayPortConfigs.csv")

def fetch_gateway_device_configs_from_api(apisession, org_id, fast=False, max_workers=None):
    """
    Fetches configuration details for all gateway devices in the org using org inventory.
    If `fast` is True, fetches each device config concurrently using connection pool management.
    
    Args:
        apisession: Authenticated Mist API session.
        org_id: Organization ID.
        fast (bool): If True, enables high-concurrency mode with connection pool management.
        max_workers (int): Optional override for number of concurrent threads.
    
    Returns:
        List of device configuration dictionaries.
    """
    logging.info("Fetching org inventory to find gateway devices...")
    try:
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)
        inventory = mistapi.get_all(response=response, mist_session=apisession)
    except Exception as e:
        logging.error(f"! Failed to fetch org inventory: {e}")
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
        logging.warning(f"! Failed to load SiteList.csv for site names: {e}")

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

    def fetch_config(work_item, connection_semaphore):
        """Fetch configuration for a single device with retry logic."""
        site_id, device_id, site_name = work_item
        
        with connection_semaphore:  # Limit concurrent connections
            try:
                logging.debug(f"Fetching config for {device_id} ({site_name})")
                response = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
                config = getattr(response, "data", {})
                if config:
                    # Add site metadata for enrichment
                    config["site_name"] = site_name
                    config["site_id"] = site_id
                    logging.debug(f"! Config fetched for {device_id}")
                    return config
                else:
                    logging.warning(f"! Empty config for device {device_id}")
            except Exception as e:
                logging.error(f"! Failed to fetch config for device {device_id}: {e}")
                return None

    def retry_fetch_config(failed_items, connection_semaphore):
        """Retry wrapper for device config fetching."""
        max_retries = int(os.getenv('FAST_MODE_SEQUENTIAL_MAX_RETRIES', '1'))
        retry_results = []
        
        for work_item in failed_items:
            site_id, device_id, site_name = work_item
            
            for attempt in range(max_retries + 1):
                result = fetch_config(work_item, connection_semaphore)
                if result is not None:
                    retry_results.append(result)
                    break
                if attempt < max_retries:
                    delay = 0.5 * (1.5 ** attempt)  # Exponential backoff
                    logging.debug(f"Retrying device {device_id} in {delay:.2f}s (attempt {attempt + 2}/{max_retries + 1})")
                    time.sleep(delay)
            else:
                logging.warning(f"! Failed to fetch config for device {device_id} after {max_retries + 1} attempts")
        
        return retry_results

    # Use connection pool management helper if fast mode is enabled
    if fast:
        successful_results, failed_items = execute_with_connection_pool_management(
            work_items=work_items,
            worker_function=fetch_config,
            batch_description="gateway device configs",
            retry_function=retry_fetch_config
        )
        all_device_configs = successful_results
    else:
        # Sequential processing for non-fast mode
        all_device_configs = []
        # Create a dummy semaphore for sequential processing
        dummy_semaphore = threading.Semaphore(1)
        
        for work_item in tqdm(work_items, desc="Fetching Configs", unit="device"):
            result = fetch_config(work_item, dummy_semaphore)
            if result is not None:
                all_device_configs.append(result)

    # Filter out None results
    all_device_configs = [config for config in all_device_configs if config is not None]
    
    logging.info(f"! Completed fetching {len(all_device_configs)} gateway device configs.")
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
            logging.info(" Hour boundary crossed. Resetting integral.")
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
    print("Combined Inventory with Site Info by Calendar Week:")

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
            logging.warning(f"! Skipping device due to error: {e}")

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

    # Count the total weekly files created
    total_weeks = len(weekly_data)
    total_devices = len(site_configs)
    print(f"! {total_weeks} weekly CSV files created in CombinedInventory_ByWeek/ folder ({total_devices} total devices processed)")
    print(f"! Summary report exported to CombinedInventory_ByWeek/CombinedInventory_Summary.csv")

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

def normalize_state_name(state_str):
    """
    Normalizes state names and abbreviations to a consistent format.
    Converts both full state names and abbreviations to lowercase abbreviations.
    """
    if not state_str:
        return ""
    
    # Convert to lowercase and strip
    state = state_str.lower().strip()
    
    # State name to abbreviation mapping
    state_mapping = {
        # Full names to abbreviations
        'alabama': 'al', 'alaska': 'ak', 'arizona': 'az', 'arkansas': 'ar', 'california': 'ca',
        'colorado': 'co', 'connecticut': 'ct', 'delaware': 'de', 'florida': 'fl', 'georgia': 'ga',
        'hawaii': 'hi', 'idaho': 'id', 'illinois': 'il', 'indiana': 'in', 'iowa': 'ia',
        'kansas': 'ks', 'kentucky': 'ky', 'louisiana': 'la', 'maine': 'me', 'maryland': 'md',
        'massachusetts': 'ma', 'michigan': 'mi', 'minnesota': 'mn', 'mississippi': 'ms', 'missouri': 'mo',
        'montana': 'mt', 'nebraska': 'ne', 'nevada': 'nv', 'new hampshire': 'nh', 'new jersey': 'nj',
        'new mexico': 'nm', 'new york': 'ny', 'north carolina': 'nc', 'north dakota': 'nd', 'ohio': 'oh',
        'oklahoma': 'ok', 'oregon': 'or', 'pennsylvania': 'pa', 'rhode island': 'ri', 'south carolina': 'sc',
        'south dakota': 'sd', 'tennessee': 'tn', 'texas': 'tx', 'utah': 'ut', 'vermont': 'vt',
        'virginia': 'va', 'washington': 'wa', 'west virginia': 'wv', 'wisconsin': 'wi', 'wyoming': 'wy',
        'district of columbia': 'dc',
        
        # Abbreviations to themselves (normalized to lowercase)
        'al': 'al', 'ak': 'ak', 'az': 'az', 'ar': 'ar', 'ca': 'ca', 'co': 'co', 'ct': 'ct',
        'de': 'de', 'fl': 'fl', 'ga': 'ga', 'hi': 'hi', 'id': 'id', 'il': 'il', 'in': 'in',
        'ia': 'ia', 'ks': 'ks', 'ky': 'ky', 'la': 'la', 'me': 'me', 'md': 'md', 'ma': 'ma',
        'mi': 'mi', 'mn': 'mn', 'ms': 'ms', 'mo': 'mo', 'mt': 'mt', 'ne': 'ne', 'nv': 'nv',
        'nh': 'nh', 'nj': 'nj', 'nm': 'nm', 'ny': 'ny', 'nc': 'nc', 'nd': 'nd', 'oh': 'oh',
        'ok': 'ok', 'or': 'or', 'pa': 'pa', 'ri': 'ri', 'sc': 'sc', 'sd': 'sd', 'tn': 'tn',
        'tx': 'tx', 'ut': 'ut', 'vt': 'vt', 'va': 'va', 'wa': 'wa', 'wv': 'wv', 'wi': 'wi',
        'wy': 'wy', 'dc': 'dc'
    }
    
    return state_mapping.get(state, state)

def validate_addresses_with_nominatim(mist_address, comparison_address, timeout=5, debug=False, skip_ssl_verify=False, org_name=None, mist_duplicates=None, ref_duplicates=None, site_name=None):
    """
    Validate both address sets against Nominatim (OpenStreetMap) geocoding API
    to determine which is more accurate/complete.
    
    Args:
        mist_address (dict): Mist address data
        comparison_address (dict): Comparison CSV address data  
        timeout (int): HTTP request timeout in seconds
        debug (bool): If True, enables detailed debug logging for API requests and responses
        org_name (str): Organization name for intelligent tiebreaking
        mist_duplicates (dict): Dictionary of duplicate Mist addresses {addr_key: [site_names]}
        ref_duplicates (dict): Dictionary of duplicate reference addresses {addr_key: [site_names]}
        site_name (str): Current site name being processed
        
    Returns:
        dict: {
            'mist_validation': {'valid': bool, 'confidence': float, 'lat': float, 'lon': float},
            'comparison_validation': {'valid': bool, 'confidence': float, 'lat': float, 'lon': float},
            'recommendation': str  # 'mist', 'comparison', or 'uncertain'
        }
    """
    
    # Suppress SSL warnings if skip_ssl_verify is enabled
    if skip_ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        if debug:
            logging.warning("SSL certificate verification disabled - urllib3 warnings suppressed")
    
    if debug:
        logging.debug("ENTRY: validate_addresses_with_nominatim()")
        logging.debug(f"  mist_address: {mist_address}")
        logging.debug(f"  comparison_address: {comparison_address}")
        logging.debug(f"  timeout: {timeout}")
        logging.debug(f"  skip_ssl_verify: {skip_ssl_verify}")
    
    def geocode_address(address_dict, address_source="unknown"):
        """Geocode a single address using Nominatim"""
        try:
            # Build address string
            address_parts = []
            if address_dict.get('address'):
                address_parts.append(address_dict['address'])
            if address_dict.get('city'):
                address_parts.append(address_dict['city'])
            if address_dict.get('state'):
                address_parts.append(address_dict['state'])
            if address_dict.get('zip'):
                address_parts.append(address_dict['zip'])
                
            if not address_parts:
                if debug:
                    logging.debug(f"GEOCODE [{address_source}]: No address parts available")
                return {'valid': False, 'confidence': 0.0, 'lat': None, 'lon': None, 'error': 'Empty address'}
            
            address_string = ', '.join(address_parts)
            if debug:
                logging.debug(f"GEOCODE [{address_source}]: Built address string: '{address_string}'")
            
            # Nominatim API call (respect 1 req/sec limit)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'format': 'json',
                'q': address_string,
                'limit': 1,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'MistHelper/1.0 (address validation)'
            }
            
            if debug:
                logging.debug(f"GEOCODE [{address_source}]: Making API request to {url}")
                logging.debug(f"GEOCODE [{address_source}]: Request params: {params}")
                logging.debug(f"GEOCODE [{address_source}]: Request headers: {headers}")
                if skip_ssl_verify:
                    logging.warning(f"GEOCODE [{address_source}]: SSL certificate verification DISABLED for this request")
            
            # Configure SSL verification based on parameter
            verify_ssl = not skip_ssl_verify
            if skip_ssl_verify and debug:
                logging.debug(f"GEOCODE [{address_source}]: SSL verification bypassed (verify={verify_ssl})")
            
            # Retry logic for timeout errors
            max_retries = 2
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries + 1):
                try:
                    # Increase timeout for better reliability
                    actual_timeout = timeout + (attempt * 5)  # Increase timeout on retries
                    if debug and attempt > 0:
                        logging.debug(f"GEOCODE [{address_source}]: Retry attempt {attempt} with timeout {actual_timeout}s")
                    
                    response = requests.get(url, params=params, headers=headers, timeout=actual_timeout, verify=verify_ssl)
                    
                    if debug:
                        logging.debug(f"GEOCODE [{address_source}]: Response status: {response.status_code}")
                        logging.debug(f"GEOCODE [{address_source}]: Response headers: {dict(response.headers)}")
                        logging.debug(f"GEOCODE [{address_source}]: Response content length: {len(response.content)} bytes")
                    
                    # If we get here, the request succeeded, break out of retry loop
                    break
                    
                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as timeout_error:
                    if attempt < max_retries:
                        if debug:
                            logging.debug(f"GEOCODE [{address_source}]: Timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Final retry failed, raise the timeout error
                        if debug:
                            logging.debug(f"GEOCODE [{address_source}]: All retry attempts failed due to timeout")
                        raise timeout_error
                except Exception as e:
                    # Non-timeout errors should not be retried
                    raise e
            
            if response.status_code == 200:
                results = response.json()
                if debug:
                    logging.debug(f"GEOCODE [{address_source}]: Response JSON: {results}")
                
                if results:
                    result = results[0]
                    
                    # Calculate confidence from multiple Nominatim fields
                    confidence = 0.0
                    importance = float(result.get('importance', 0.0))
                    
                    if debug:
                        logging.debug(f"GEOCODE [{address_source}]: Raw importance from Nominatim: {importance}")
                        logging.debug(f"GEOCODE [{address_source}]: Available result fields: {list(result.keys())}")
                    
                    # Use importance if available and meaningful, otherwise calculate from match quality
                    if importance > 0.01:  # Only use importance if it's above a minimal threshold
                        confidence = min(1.0, importance * 2.0)  # Scale importance up as it's often small
                        if debug:
                            logging.debug(f"GEOCODE [{address_source}]: Using scaled importance: {confidence:.3f}")
                    else:
                        # Calculate confidence based on address components matched and result quality
                        display_name = result.get('display_name', '').lower()
                        address_string_lower = address_string.lower()
                        
                        if debug:
                            logging.debug(f"GEOCODE [{address_source}]: Calculating custom confidence")
                            logging.debug(f"GEOCODE [{address_source}]: Address string: '{address_string_lower}'")
                            logging.debug(f"GEOCODE [{address_source}]: Display name: '{display_name}'")
                        
                        # Count matching components with partial matching
                        match_score = 0.0
                        total_components = len(address_parts)
                        
                        for part in address_parts:
                            part_clean = part.lower().strip()
                            if len(part_clean) > 2:  # Only check meaningful parts
                                # Full match gets full point
                                if part_clean in display_name:
                                    match_score += 1.0
                                    if debug:
                                        logging.debug(f"GEOCODE [{address_source}]: Full match for '{part_clean}'")
                                # Partial match gets partial point
                                elif any(word in display_name for word in part_clean.split() if len(word) > 2):
                                    match_score += 0.5
                                    if debug:
                                        logging.debug(f"GEOCODE [{address_source}]: Partial match for '{part_clean}'")
                        
                        # Base confidence from component matching
                        component_conf = match_score / total_components if total_components > 0 else 0.0
                        
                        # Quality indicators from Nominatim result
                        quality_boost = 0.0
                        
                        # Place type quality boost
                        place_type = result.get('type', '').lower()
                        place_class = result.get('class', '').lower()
                        
                        if place_type in ['house', 'building', 'commercial', 'office', 'retail', 'shop']:
                            quality_boost += 0.3
                        elif place_type in ['residential', 'industrial', 'public']:
                            quality_boost += 0.2
                        elif place_class in ['building', 'place', 'amenity']:
                            quality_boost += 0.1
                            
                        # Address detail quality (more specific = higher confidence)
                        if result.get('address', {}):
                            address_details = result.get('address', {})
                            detail_count = len([v for v in address_details.values() if v])
                            if detail_count >= 5:  # Street, city, state, postcode, country
                                quality_boost += 0.2
                            elif detail_count >= 3:
                                quality_boost += 0.1
                        
                        # Combine component matching with quality indicators
                        confidence = min(1.0, component_conf + quality_boost)
                        
                        if debug:
                            logging.debug(f"GEOCODE [{address_source}]: Component confidence: {component_conf:.3f}")
                            logging.debug(f"GEOCODE [{address_source}]: Quality boost: {quality_boost:.3f}")
                            logging.debug(f"GEOCODE [{address_source}]: Place type: '{place_type}', Class: '{place_class}'")
                            logging.debug(f"GEOCODE [{address_source}]: Final confidence: {confidence:.3f}")
                    
                    geocode_result = {
                        'valid': True,
                        'confidence': confidence,
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result.get('display_name', ''),
                        'place_type': result.get('type', ''),
                        'place_class': result.get('class', ''),
                        'address_details': result.get('address', {}),
                        'error': None
                    }
                    if debug:
                        logging.debug(f"GEOCODE [{address_source}]: SUCCESS - confidence: {confidence:.3f}, lat: {result['lat']}, lon: {result['lon']}")
                        logging.debug(f"GEOCODE [{address_source}]: Display name: {result.get('display_name', '')}")
                        logging.debug(f"GEOCODE [{address_source}]: Place type: {result.get('type', '')}")
                    return geocode_result
                else:
                    if debug:
                        logging.debug(f"GEOCODE [{address_source}]: No results found in API response")
                    return {'valid': False, 'confidence': 0.0, 'lat': None, 'lon': None, 'error': 'No results found'}
            else:
                if debug:
                    logging.debug(f"GEOCODE [{address_source}]: HTTP error {response.status_code}")
                    logging.debug(f"GEOCODE [{address_source}]: Response content: {response.content[:200]}...")
                return {'valid': False, 'confidence': 0.0, 'lat': None, 'lon': None, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            if debug:
                logging.debug(f"GEOCODE [{address_source}]: Exception occurred: {str(e)}")
                logging.debug(f"GEOCODE [{address_source}]: Full traceback: {traceback.format_exc()}")
            return {'valid': False, 'confidence': 0.0, 'lat': None, 'lon': None, 'error': str(e)}
    
    # Validate both addresses (with rate limiting)
    if debug:
        logging.debug("Starting mist address validation...")
    mist_result = geocode_address(mist_address, "MIST")
    
    if debug:
        logging.debug("Applying rate limiting delay (1.1 seconds)...")
    time.sleep(1.1)  # Respect Nominatim 1 req/sec limit
    
    if debug:
        logging.debug("Starting comparison address validation...")
    comparison_result = geocode_address(comparison_address, "COMPARISON")
    
    if debug:
        logging.debug(f"Mist validation result: {mist_result}")
        logging.debug(f"Comparison validation result: {comparison_result}")
    
    # Determine recommendation based on validation results
    recommendation = 'uncertain'
    recommendation_reason = "Unknown"
    
    if mist_result['valid'] and not comparison_result['valid']:
        recommendation = 'mist'
        recommendation_reason = f"Only Mist address is valid (confidence: {mist_result['confidence']:.3f})"
        if debug:
            logging.debug("Recommendation: MIST (only mist address is valid)")
    elif comparison_result['valid'] and not mist_result['valid']:
        recommendation = 'comparison'
        recommendation_reason = f"Only reference address is valid (confidence: {comparison_result['confidence']:.3f})"
        if debug:
            logging.debug("Recommendation: COMPARISON (only comparison address is valid)")
    elif mist_result['valid'] and comparison_result['valid']:
        # Both addresses are valid - need intelligent tiebreaker logic
        if debug:
            logging.debug("TIEBREAKER: Both addresses validated successfully, applying tiebreaker logic")
        
        # Check for duplicate address disqualification first
        mist_is_duplicate = False
        ref_is_duplicate = False
        
        if mist_duplicates and site_name:
            # Create address key for Mist address
            mist_addr_key = f"{mist_address['address'].lower()}|{mist_address['city'].lower()}|{mist_address['state'].lower()}|{mist_address['zip']}"
            mist_is_duplicate = mist_addr_key in mist_duplicates
            if debug and mist_is_duplicate:
                logging.debug(f"TIEBREAKER: Mist address is duplicate - shared by sites: {mist_duplicates[mist_addr_key]}")
        
        if ref_duplicates and site_name:
            # Create address key for reference address
            ref_addr_key = f"{comparison_address['address'].lower()}|{comparison_address['city'].lower()}|{comparison_address['state'].lower()}|{comparison_address['zip']}"
            ref_is_duplicate = ref_addr_key in ref_duplicates
            if debug and ref_is_duplicate:
                logging.debug(f"TIEBREAKER: Reference address is duplicate - shared by sites: {ref_duplicates[ref_addr_key]}")
        
        # Apply duplicate disqualification logic
        if mist_is_duplicate and ref_is_duplicate:
            recommendation = 'uncertain' 
            recommendation_reason = "  Both addresses are duplicates (shared between multiple sites) - manual review required"
            if debug:
                logging.debug("TIEBREAKER: Both addresses are duplicates - flagging as uncertain")
        elif mist_is_duplicate and not ref_is_duplicate:
            recommendation = 'comparison'
            recommendation_reason = "Mist address is duplicate (shared between sites), using reference address"
            if debug:
                logging.debug("TIEBREAKER: Mist address is duplicate, recommending reference")
        elif ref_is_duplicate and not mist_is_duplicate:
            recommendation = 'mist'
            recommendation_reason = "Reference address is duplicate (shared between sites), using Mist address"
            if debug:
                logging.debug("TIEBREAKER: Reference address is duplicate, recommending Mist")
        else:
            # No duplicates detected, proceed with standard tiebreaker logic
            # Both valid - compare confidence scores
            if mist_result['confidence'] > comparison_result['confidence'] * 1.1:  # 10% threshold
                recommendation = 'mist'
                recommendation_reason = f"Mist address has higher confidence ({mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})"
                if debug:
                    logging.debug(f"Recommendation: MIST (higher confidence: {mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})")
            elif comparison_result['confidence'] > mist_result['confidence'] * 1.1:
                recommendation = 'comparison'
                recommendation_reason = f"Reference address has higher confidence ({comparison_result['confidence']:.3f} vs {mist_result['confidence']:.3f})"
                if debug:
                    logging.debug(f"Recommendation: COMPARISON (higher confidence: {comparison_result['confidence']:.3f} vs {mist_result['confidence']:.3f})")
            else:
                # Confidence scores are too close - use intelligent tiebreaker
                recommendation = 'uncertain'
                recommendation_reason = f"Both addresses have similar confidence ({mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})"
                
                if org_name and debug:
                    logging.debug(f"Both addresses valid with similar confidence - applying organization name tiebreaker with org: '{org_name}'")
                
                # Intelligent tiebreaker using organization name and business context
                if org_name:
                    # Normalize organization name for comparison
                    normalized_org = NameNormalizationUtils.normalize_business_name(org_name)
                    
                    # Extract business names from validated address display names
                    mist_display = mist_result.get('display_name', '').lower()
                    comp_display = comparison_result.get('display_name', '').lower()
                    
                    # Calculate organization name similarity with each address
                    mist_org_similarity = NameNormalizationUtils.calculate_org_name_similarity(normalized_org, mist_display)
                    comp_org_similarity = NameNormalizationUtils.calculate_org_name_similarity(normalized_org, comp_display)
                    
                    if debug:
                        logging.debug(f"Organization name similarity scores: Mist={mist_org_similarity:.3f}, Comparison={comp_org_similarity:.3f}")
                    
                    # If there's a clear winner based on organization name similarity
                    if mist_org_similarity > comp_org_similarity + 0.1:  # 10% threshold
                        recommendation = 'mist'
                        recommendation_reason = f"Mist address better matches organization '{org_name}' (similarity: {mist_org_similarity:.3f} vs {comp_org_similarity:.3f})"
                        if debug:
                            logging.debug(f"Recommendation: MIST (organization name match: {mist_org_similarity:.3f} vs {comp_org_similarity:.3f})")
                    elif comp_org_similarity > mist_org_similarity + 0.1:
                        recommendation = 'comparison'
                        recommendation_reason = f"Reference address better matches organization '{org_name}' (similarity: {comp_org_similarity:.3f} vs {mist_org_similarity:.3f})"
                        if debug:
                            logging.debug(f"Recommendation: COMPARISON (organization name match: {comp_org_similarity:.3f} vs {mist_org_similarity:.3f})")
                    else:
                        # Still too close - apply business context rules
                        business_recommendation = apply_business_context_rules(mist_result, comparison_result, debug)
                        if business_recommendation == 'mist':
                            recommendation = 'mist'
                            recommendation_reason = f"Mist address appears more business-appropriate (type: {mist_result.get('place_type', 'unknown')})"
                        elif business_recommendation == 'comparison':
                            recommendation = 'comparison'
                            recommendation_reason = f"Reference address appears more business-appropriate (type: {comparison_result.get('place_type', 'unknown')})"
                        else:
                            recommendation = 'uncertain'
                            recommendation_reason = f"All tiebreakers inconclusive - similar confidence ({mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})"
                            if debug:
                                logging.debug(f"Recommendation: UNCERTAIN (all tiebreakers inconclusive - confidence: {mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})")
                else:
                    # No org name available - apply business context rules only
                    business_recommendation = apply_business_context_rules(mist_result, comparison_result, debug)
                    if business_recommendation == 'mist':
                        recommendation = 'mist'
                        recommendation_reason = f"Mist address appears more business-appropriate (type: {mist_result.get('place_type', 'unknown')})"
                    elif business_recommendation == 'comparison':
                        recommendation = 'comparison'
                        recommendation_reason = f"Reference address appears more business-appropriate (type: {comparison_result.get('place_type', 'unknown')})"
                    else:
                        recommendation = 'uncertain'
                        recommendation_reason = f"Confidence scores too close and no clear business preference ({mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})"
                        if debug:
                            logging.debug(f"Recommendation: UNCERTAIN (confidence scores too close: {mist_result['confidence']:.3f} vs {comparison_result['confidence']:.3f})")
    else:
        recommendation = 'uncertain'
        recommendation_reason = "Both addresses failed validation"
        if debug:
            logging.debug("Recommendation: UNCERTAIN (both addresses failed validation)")
    
    final_result = {
        'mist_validation': mist_result,
        'comparison_validation': comparison_result,
        'recommendation': recommendation,
        'recommendation_reason': recommendation_reason
    }
    
    if debug:
        logging.debug(f"EXIT: validate_addresses_with_nominatim() - returning: {final_result}")
    
    return final_result

class NameNormalizationUtils:
    """General name & token normalization helpers (business, org, and generic strings).

    EVOLUTION:
        Derived from earlier AddressBusinessNameUtils which wrapped two former free functions.
        Generalized to support broader name cleaning (future: contact names, model families, etc.).

    FEATURES:
        * Business suffix stripping
        * Generic punctuation stripping & whitespace collapsing
        * Alias methods maintained for backward compatibility
        * Token extraction utility for future semantic similarity modules

    SECURITY: Pure string transformations; no I/O or external calls.
    """

    BUSINESS_SUFFIX_PATTERNS = [
        r'\binc\.?$', r'\bincorporated$', r'\bllc\.?$', r'\bcorp\.?$', r'\bcorporation$',
        r'\bltd\.?$', r'\blimited$', r'\bco\.?$', r'\bcompany$', r'\benterprise$',
        r'\benterprises$', r'\bgroup$', r'\bholdings$', r'\bassociates$', r'\bpartners$',
        r'\b& co\.?$', r'\b&co\.?$'
    ]

    @staticmethod
    def normalize_business_name(business_name: str) -> str:
        if not business_name:
            return ""
        normalized = business_name.lower().strip()
        for suffix in NameNormalizationUtils.BUSINESS_SUFFIX_PATTERNS:
            normalized = re.sub(suffix, '', normalized).strip()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    @staticmethod
    def normalize_generic(name: str) -> str:
        """Lightweight generic normalization (lower, trim, collapse whitespace)."""
        if not name:
            return ""
        cleaned = unicodedata.normalize('NFKD', str(name)).casefold().strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned

    @staticmethod
    def extract_tokens(name: str) -> list:
        """Return lowercase alphanumeric tokens for fuzzy pipelines."""
        if not name:
            return []
        return re.findall(r'[a-z0-9]+', NameNormalizationUtils.normalize_generic(name))

    @staticmethod
    def calculate_org_name_similarity(org_name: str, address_display: str) -> float:
        if not org_name or not address_display:
            return 0.0
        org_words = set(org_name.split())
        address_words = set(re.findall(r'\b\w+\b', address_display.lower()))
        exact_matches = len(org_words.intersection(address_words))
        word_similarity = (exact_matches / len(org_words)) if org_words else 0.0
        string_similarity = SequenceMatcher(None, org_name, address_display).ratio()
        combined_similarity = (word_similarity * 0.7) + (string_similarity * 0.3)
        return min(1.0, combined_similarity)

# Backward-compatible alias (in case any external automation referenced the old class name)
AddressBusinessNameUtils = NameNormalizationUtils

def apply_business_context_rules(mist_result, comparison_result, debug=False):
    """
    Apply business context rules when both addresses are valid but confidence scores are similar.
    Returns 'mist', 'comparison', or 'uncertain'.
    """
    # Business address type preferences based on place_type
    business_place_types = ['commercial', 'office', 'retail', 'building', 'shop', 'store']
    residential_place_types = ['house', 'residential', 'apartment']
    
    mist_place = mist_result.get('place_type', '').lower()
    comp_place = comparison_result.get('place_type', '').lower()
    
    if debug:
        logging.debug(f"Business context analysis: Mist place_type='{mist_place}', Comparison place_type='{comp_place}'")
    
    # Prefer business/commercial addresses over residential
    mist_is_business = any(biz_type in mist_place for biz_type in business_place_types)
    comp_is_business = any(biz_type in comp_place for biz_type in business_place_types)
    
    mist_is_residential = any(res_type in mist_place for res_type in residential_place_types)
    comp_is_residential = any(res_type in comp_place for res_type in residential_place_types)
    
    if mist_is_business and comp_is_residential:
        if debug:
            logging.debug("Business context rule: Preferring Mist (business over residential)")
        return 'mist'
    elif comp_is_business and mist_is_residential:
        if debug:
            logging.debug("Business context rule: Preferring Comparison (business over residential)")
        return 'comparison'
    
    # If both are business or both are residential, check confidence again with lower threshold
    confidence_diff = abs(mist_result['confidence'] - comparison_result['confidence'])
    if confidence_diff > 0.05:  # 5% threshold for final decision
        if mist_result['confidence'] > comparison_result['confidence']:
            if debug:
                logging.debug(f"Business context rule: Preferring Mist (slightly higher confidence: {mist_result['confidence']:.3f})")
            return 'mist'
        else:
            if debug:
                logging.debug(f"Business context rule: Preferring Comparison (slightly higher confidence: {comparison_result['confidence']:.3f})")
            return 'comparison'
    
    if debug:
        logging.debug("Business context rules inconclusive")
    return 'uncertain'

def normalize_address_string(address_str):
    """
    Normalizes an address string for comparison by:
    - Converting to lowercase
    - Removing extra whitespace
    - Standardizing common abbreviations
    - Removing punctuation
    - Unicode normalization for diacritics
    """
    
    if not address_str:
        return ""
    
    # Unicode normalization (NFKD) and casefold for robust comparison
    normalized = unicodedata.normalize('NFKD', address_str)
    normalized = normalized.casefold().strip()
    
    # Remove extra whitespace and collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Common address abbreviations standardization
    abbreviations = {
        r'\bstreet\b': 'st',
        r'\bst\b': 'st',
        r'\bavenue\b': 'ave',
        r'\bave\b': 'ave',
        r'\bboulevard\b': 'blvd',
        r'\bblvd\b': 'blvd',
        r'\bbuilding\b': 'bldg',
        r'\bbuilding\b': 'bldg',
        r'\bsuite\b': 'ste',
        r'\bsuite\b': 'ste',
        r'\bnorth\b': 'n',
        r'\bsouth\b': 's',
        r'\beast\b': 'e',
        r'\bwest\b': 'w',
        r'\bdrive\b': 'dr',
        r'\bdr\b': 'dr',
        r'\broad\b': 'rd',
        r'\brd\b': 'rd',
        r'\blane\b': 'ln',
        r'\bln\b': 'ln',
        r'\bcourt\b': 'ct',
        r'\bct\b': 'ct',
        r'\bplace\b': 'pl',
        r'\bpl\b': 'pl',
        r'\bparkway\b': 'pkwy',
        r'\bpkwy\b': 'pkwy',
        r'\bhighway\b': 'hwy',
        r'\bhwy\b': 'hwy',
    }
    
    for full_form, abbrev in abbreviations.items():
        normalized = re.sub(full_form, abbrev, normalized)
    
    # Remove punctuation and extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = ' '.join(normalized.split())
    
    return normalized

def parse_address_components(address_string, debug=False):
    """
    Parse address components with defensive parsing and robust heuristics.
    
    Handles:
    - Defensive parsing with length checks
    - "Unknown" address detection  
    - Puerto Rico US territory mapping
    - Right-to-left parsing (country, zip, city, street)
    - Unicode normalization
    - Graceful error handling
    
    Args:
        address_string (str): Raw address string
        debug (bool): Enable debug logging
        
    Returns:
        dict: {
            'address': str,
            'city': str, 
            'state': str,
            'zip': str,
            'country': str,
            'is_parseable': bool,
            'parse_reason': str,
            'original': str
        }
    """
    
    if debug:
        logging.debug(f"PARSE_ADDRESS: Input: '{address_string}'")
    
    # Initialize default result
    result = {
        'address': None,
        'city': None,
        'state': None,
        'zip': None,
        'country': None,
        'is_parseable': False,
        'parse_reason': 'unparsed',
        'original': address_string or ""
    }
    
    # Handle empty or None input
    if not address_string or not str(address_string).strip():
        result['parse_reason'] = 'empty_input'
        if debug:
            logging.debug("PARSE_ADDRESS: Empty input")
        return result
    
    # Handle "Unknown" addresses
    cleaned_input = str(address_string).strip()
    if cleaned_input.lower() in ['unknown', 'n/a', 'na', 'none', 'null', '']:
        result['parse_reason'] = 'unknown_address'
        if debug:
            logging.debug("PARSE_ADDRESS: Unknown address detected")
        return result
    
    try:
        # Unicode normalization and defensive cleaning
        normalized = unicodedata.normalize('NFKD', cleaned_input)
        
        # Trim whitespace, collapse repeated commas, remove empty tokens
        parts = [part.strip() for part in normalized.split(',')]
        parts = [part for part in parts if part]  # Remove empty parts
        
        if not parts:
            result['parse_reason'] = 'no_parts_after_cleaning'
            if debug:
                logging.debug("PARSE_ADDRESS: No parts after cleaning")
            return result
        
        if debug:
            logging.debug(f"PARSE_ADDRESS: Cleaned parts: {parts}")
        
        # Parse from right to left (country, postal/ZIP, city, street)
        
        # Step 1: Detect country (last token if recognizable)
        country = None
        remaining_parts = parts[:]
        
        if len(remaining_parts) > 0:
            last_part = remaining_parts[-1].strip().lower()
            
            # Country detection patterns
            if last_part in ['usa', 'united states', 'united states of america', 'us']:
                country = 'US'
                remaining_parts = remaining_parts[:-1]
            elif last_part in ['puerto rico', 'pr']:
                country = 'US'  # Puerto Rico is US territory
                remaining_parts = remaining_parts[:-1]
            elif len(last_part) == 2 and last_part.isalpha():
                # Assume 2-letter country code
                country = last_part.upper()
                remaining_parts = remaining_parts[:-1]
        
        # Step 2: Detect ZIP/postal code (numeric patterns)
        zip_code = None
        if len(remaining_parts) > 0:
            last_part = remaining_parts[-1].strip()
            
            # US ZIP pattern: 5 digits or 5+4 format
            if re.match(r'^\d{5}(-?\d{4})?$', last_part):
                zip_code = last_part
                remaining_parts = remaining_parts[:-1]
                # If no country detected but ZIP found, assume US
                if not country:
                    country = 'US'
        
        # Step 3: Handle Puerto Rico special case
        state = None
        if len(remaining_parts) > 0:
            last_part = remaining_parts[-1].strip().lower()
            
            # Check for Puerto Rico in various positions
            if last_part == 'puerto rico':
                state = 'PR'
                country = 'US'
                remaining_parts = remaining_parts[:-1]
            elif country == 'US' and last_part == 'pr':
                state = 'PR'
                remaining_parts = remaining_parts[:-1]
            elif len(last_part) <= 2 and last_part.isalpha():
                # Assume state abbreviation
                state = last_part.upper()
                remaining_parts = remaining_parts[:-1]
            elif len(remaining_parts) > 1:
                # Check if it's a full state name
                state_normalized = normalize_state_name(last_part)
                if state_normalized:
                    state = state_normalized.upper()
                    remaining_parts = remaining_parts[:-1]
        
        # Step 4: Detect city (next remaining part from right)
        city = None
        if len(remaining_parts) > 0:
            city = remaining_parts[-1].strip()
            remaining_parts = remaining_parts[:-1]
        
        # Step 5: Everything else is street address
        address = None
        if remaining_parts:
            address = ', '.join(remaining_parts).strip()
        
        # Populate result
        result.update({
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'country': country,
            'is_parseable': True,
            'parse_reason': 'success'
        })
        
        if debug:
            logging.debug(f"PARSE_ADDRESS: Parsed result: {result}")
        
        return result
        
    except Exception as e:
        result['parse_reason'] = f'exception: {str(e)}'
        if debug:
            logging.warning(f"PARSE_ADDRESS: Exception during parsing: {e}")
        return result

def enhanced_usaddress_parse(address_string, debug=False):
    """
    Enhanced address parsing using usaddress-scourgify for US addresses.
    Falls back to heuristic parsing for non-US or failed cases.
    
    Args:
        address_string (str): Raw address string
        debug (bool): Enable debug logging
        
    Returns:
        dict: Same format as parse_address_components
    """
    try:
        
        if debug:
            logging.debug(f"USADDRESS_PARSE: Attempting usaddress parsing for: '{address_string}'")
        
        # Try usaddress-scourgify first
        try:
            parsed = normalize_address_record(address_string)
            
            result = {
                'address': parsed.get('address_line_1', ''),
                'city': parsed.get('city', ''),
                'state': parsed.get('state', ''),
                'zip': parsed.get('postal_code', ''),
                'country': 'US',  # usaddress is US-focused
                'is_parseable': True,
                'parse_reason': 'usaddress_success',
                'original': address_string or ""
            }
            
            # Handle address_line_2 if present
            if parsed.get('address_line_2'):
                # Combine address lines with space
                address_parts = [parsed.get('address_line_1', ''), parsed.get('address_line_2', '')]
                result['address'] = ' '.join(part for part in address_parts if part)
            
            if debug:
                logging.debug(f"USADDRESS_PARSE: Success: {result}")
            
            return result
            
        except Exception as usaddress_error:
            if debug:
                logging.debug(f"USADDRESS_PARSE: Failed with: {usaddress_error}")
            
            # Fall back to heuristic parsing
            return parse_address_components(address_string, debug=debug)
    
    except ImportError:
        if debug:
            logging.debug("USADDRESS_PARSE: usaddress-scourgify not available, using heuristic parsing")
        return parse_address_components(address_string, debug=debug)

def calculate_string_similarity(str1, str2):
    """
    Calculate similarity percentage between two strings using RapidFuzz for better performance.
    Falls back to difflib if RapidFuzz is not available.
    
    Returns a percentage from 0-100.
    """
    if not str1 and not str2:
        return 100.0  # Both empty, consider perfect match
    if not str1 or not str2:
        return 0.0    # One empty, one not, no match
    
    # Normalize both strings
    norm_str1 = normalize_address_string(str1)
    norm_str2 = normalize_address_string(str2)
    
    try:
        # Try RapidFuzz for better performance and accuracy
        
        # Use token-based similarity for better address matching
        similarity = fuzz.token_sort_ratio(norm_str1, norm_str2) / 100.0
        return similarity * 100
        
    except ImportError:
        # Fall back to difflib
        similarity = difflib.SequenceMatcher(None, norm_str1, norm_str2).ratio()
        return similarity * 100

def check_address_should_skip(comparison_address, skip_addresses, debug=False):
    """
    Check if a comparison address should be automatically skipped (treating Mist address as correct).
    
    Args:
        comparison_address (dict): Address from comparison CSV to check
        skip_addresses (list): List of addresses to skip from AddressSkip.csv
        debug (bool): Enable debug logging
        
    Returns:
        tuple: (should_skip: bool, skip_reason: str)
    """
    if not skip_addresses:
        return False, ""
    
    # Normalize comparison address fields for matching
    comp_addr = str(comparison_address.get('address', '')).strip().upper()
    comp_city = str(comparison_address.get('city', '')).strip().upper()
    comp_state = str(comparison_address.get('state', '')).strip().upper()
    comp_zip = str(comparison_address.get('zip', '')).strip().upper()
    
    for skip_entry in skip_addresses:
        skip_addr = str(skip_entry.get('Skip_Address', '')).strip().upper()
        skip_city = str(skip_entry.get('Skip_City', '')).strip().upper()
        skip_state = str(skip_entry.get('Skip_State', '')).strip().upper()
        skip_zip = str(skip_entry.get('Skip_Zip', '')).strip().upper()
        skip_reason = skip_entry.get('Reason', 'Address in skip list')
        
        # Check for exact matches (case-insensitive)
        if (comp_addr == skip_addr and 
            comp_city == skip_city and 
            comp_state == skip_state and 
            comp_zip == skip_zip):
            
            if debug:
                logging.debug(f"ADDRESS_SKIP: Found exact match - {comp_addr}, {comp_city}, {comp_state}, {comp_zip}")
            return True, skip_reason
            
        # Check for partial matches (any field matches and others are empty in skip list)
        partial_match = False
        matching_fields = 0
        
        if skip_addr and comp_addr == skip_addr:
            partial_match = True
            matching_fields += 1
        if skip_city and comp_city == skip_city:
            partial_match = True
            matching_fields += 1
        if skip_state and comp_state == skip_state:
            partial_match = True
            matching_fields += 1
        if skip_zip and comp_zip == skip_zip:
            partial_match = True
            matching_fields += 1
            
        # For wildcard patterns: require at least 3 empty fields AND only 1 matching field
        # For specific addresses: require at least 2 matching fields
        empty_fields = sum([1 for f in [skip_addr, skip_city, skip_state, skip_zip] if not f])
        populated_fields = 4 - empty_fields
        
        if partial_match:
            # Wildcard pattern (mostly empty fields): require exactly 1 match
            if empty_fields >= 3 and matching_fields == 1:
                if debug:
                    logging.debug(f"ADDRESS_SKIP: Found wildcard match - {comp_addr}, {comp_city}, {comp_state}, {comp_zip}")
                return True, skip_reason
            # Specific address pattern: require at least 50% field match
            elif populated_fields >= 2 and matching_fields >= max(2, populated_fields // 2):
                if debug:
                    logging.debug(f"ADDRESS_SKIP: Found specific address match - {comp_addr}, {comp_city}, {comp_state}, {comp_zip}")
                return True, skip_reason
    
    return False, ""

def enhanced_compare_addresses_with_threshold(mist_address, comparison_address, threshold, debug=False):
    """
    Enhanced address comparison with robust parsing and better similarity metrics.
    
    Args:
        mist_address (dict): Dictionary with keys: address, city, state, zip, country
        comparison_address (dict): Dictionary with keys: address, city, state, zip, country  
        threshold (float): Minimum similarity percentage required to be considered a match
        debug (bool): Enable debug logging
        
    Returns:
        dict: {
            'overall_similarity': float,
            'is_match': bool,
            'field_similarities': {
                'address': float,
                'city': float, 
                'state': float,
                'zip': float
            },
            'failed_fields': list,
            'parse_status': dict  # New: parsing status for both addresses
        }
    """
    # Field weights for overall similarity calculation
    field_weights = {
        'address': 0.4,    # Street address is most important
        'city': 0.3,       # City is very important
        'state': 0.2,      # State is important
        'zip': 0.1         # Zip is least weighted since we already have zip comparison
    }
    
    field_similarities = {}
    failed_fields = []
    parse_status = {
        'mist_parseable': True,
        'comparison_parseable': True,
        'mist_reason': 'valid',
        'comparison_reason': 'valid'
    }
    
    if debug:
        logging.debug(f"ENHANCED_COMPARE: Mist address: {mist_address}")
        logging.debug(f"ENHANCED_COMPARE: Comparison address: {comparison_address}")
    
    # Check for unparseable addresses
    for field in field_weights.keys():
        mist_value = mist_address.get(field, "")
        comp_value = comparison_address.get(field, "")
        
        # Check if either address appears to be unparseable
        if str(mist_value).strip().lower() in ['unknown', 'n/a', 'na', 'none', 'null', '']:
            parse_status['mist_parseable'] = False
            parse_status['mist_reason'] = 'unknown_address'
        
        if str(comp_value).strip().lower() in ['unknown', 'n/a', 'na', 'none', 'null', '']:
            parse_status['comparison_parseable'] = False
            parse_status['comparison_reason'] = 'unknown_address'
    
    # If either address is unparseable, return early with low similarity
    if not parse_status['mist_parseable'] or not parse_status['comparison_parseable']:
        if debug:
            logging.debug(f"ENHANCED_COMPARE: Unparseable address detected: {parse_status}")
        
        return {
            'overall_similarity': 0.0,
            'is_match': False,
            'field_similarities': {field: 0.0 for field in field_weights.keys()},
            'failed_fields': list(field_weights.keys()),
            'parse_status': parse_status
        }
    
    # Compare address fields using enhanced similarity
    for field, weight in field_weights.items():
        mist_value = str(mist_address.get(field, "")).strip()
        comp_value = str(comparison_address.get(field, "")).strip()
        
        if field == 'zip':
            # Use normalized zip comparison
            mist_norm = normalize_zip_code(mist_value)
            comp_norm = normalize_zip_code(comp_value)
            similarity = 100.0 if mist_norm == comp_norm and mist_norm else 0.0
        elif field == 'state':
            # Use normalized state comparison (handles abbreviations vs full names)
            mist_norm = normalize_state_name(mist_value)
            comp_norm = normalize_state_name(comp_value)
            similarity = 100.0 if mist_norm == comp_norm and mist_norm else 0.0
        else:
            # Use enhanced string similarity for address and city fields
            similarity = calculate_string_similarity(mist_value, comp_value)
        
        field_similarities[field] = similarity
        
        # Use a more forgiving threshold for individual fields (75% of the overall threshold)
        field_threshold = threshold * 0.75
        if similarity < field_threshold:
            failed_fields.append(field)
        
        if debug:
            logging.debug(f"ENHANCED_COMPARE: {field} similarity: {similarity:.1f}% (threshold: {field_threshold:.1f}%)")
    
    # Calculate weighted overall similarity
    overall_similarity = sum(field_similarities[field] * field_weights[field] 
                           for field in field_weights.keys())
    
    is_match = overall_similarity >= threshold
    
    result = {
        'overall_similarity': overall_similarity,
        'is_match': is_match,
        'field_similarities': field_similarities,
        'failed_fields': failed_fields,
        'parse_status': parse_status
    }
    
    if debug:
        logging.debug(f"ENHANCED_COMPARE: Result: {result}")
    
    return result

def compare_addresses_with_threshold(mist_address, comparison_address, threshold):
    """
    Compare two address dictionaries and return overall similarity percentage and field-by-field breakdown.
    
    Args:
        mist_address (dict): Dictionary with keys: address, city, state, zip, country
        comparison_address (dict): Dictionary with keys: address, city, state, zip, country  
        threshold (float): Minimum similarity percentage required to be considered a match
        
    Returns:
        dict: {
            'overall_similarity': float,
            'is_match': bool,
            'field_similarities': {
                'address': float,
                'city': float, 
                'state': float,
                'zip': float
            },
            'failed_fields': list
        }
    """
    # Field weights for overall similarity calculation
    field_weights = {
        'address': 0.4,    # Street address is most important
        'city': 0.3,       # City is very important
        'state': 0.2,      # State is important
        'zip': 0.1         # Zip is least weighted since we already have zip comparison
    }
    
    field_similarities = {}
    failed_fields = []
    
    # Compare address fields (ignore country as requested)
    for field, weight in field_weights.items():
        mist_value = mist_address.get(field, "").strip()
        comp_value = comparison_address.get(field, "").strip()
        
        if field == 'zip':
            # Use normalized zip comparison
            mist_norm = normalize_zip_code(mist_value)
            comp_norm = normalize_zip_code(comp_value)
            similarity = 100.0 if mist_norm == comp_norm else 0.0
        elif field == 'state':
            # Use normalized state comparison (handles abbreviations vs full names)
            mist_norm = normalize_state_name(mist_value)
            comp_norm = normalize_state_name(comp_value)
            similarity = 100.0 if mist_norm == comp_norm else 0.0
        else:
            # Use string similarity for address and city fields
            similarity = calculate_string_similarity(mist_value, comp_value)
        
        field_similarities[field] = similarity
        
        if similarity < threshold:
            failed_fields.append(field)
    
    # Calculate weighted overall similarity
    overall_similarity = sum(field_similarities[field] * field_weights[field] 
                           for field in field_weights.keys())
    
    is_match = overall_similarity >= threshold
    
    return {
        'overall_similarity': overall_similarity,
        'is_match': is_match,
        'field_similarities': field_similarities,
        'failed_fields': failed_fields
    }

class AddressComparisonCounters:
    """Track comprehensive metrics for address comparison operations."""
    
    def __init__(self):
        self.total_devices = 0
        self.devices_enriched = 0
        self.devices_skipped = 0
        self.parse_failures = 0
        self.comparison_failures = 0
        self.validation_attempts = 0
        self.validation_successes = 0
        self.validation_failures = 0
        self.mismatches_found = 0
        self.perfect_matches = 0
        self.auto_corrections = 0  # New counter for automatically corrected addresses
        self.parse_failure_reasons = {}
        self.start_time = None
        self.end_time = None
    
    def start_timing(self):
        self.start_time = time.time()
    
    def end_timing(self):
        self.end_time = time.time()
    
    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def increment_parse_failure(self, reason):
        self.parse_failures += 1
        self.parse_failure_reasons[reason] = self.parse_failure_reasons.get(reason, 0) + 1
    
    def log_summary(self):
        """Log comprehensive summary of the comparison operation."""
        duration = self.get_duration()
        
        logging.info("=== ADDRESS COMPARISON SUMMARY ===")
        logging.info(f"Total devices processed: {self.total_devices}")
        logging.info(f"Devices enriched with site info: {self.devices_enriched}")
        logging.info(f"Devices skipped (not in comparison CSV): {self.devices_skipped}")
        logging.info(f"Parse failures: {self.parse_failures}")
        logging.info(f"Address mismatches found: {self.mismatches_found}")
        logging.info(f"Perfect matches: {self.perfect_matches}")
        logging.info(f"Auto-corrections applied: {self.auto_corrections}")
        
        if self.validation_attempts > 0:
            success_rate = (self.validation_successes / self.validation_attempts) * 100
            logging.info(f"External validation attempts: {self.validation_attempts}")
            logging.info(f"External validation successes: {self.validation_successes} ({success_rate:.1f}%)")
            logging.info(f"External validation failures: {self.validation_failures}")
        
        if self.parse_failure_reasons:
            logging.info("Parse failure breakdown:")
            for reason, count in self.parse_failure_reasons.items():
                logging.info(f"  {reason}: {count}")
        
        if duration > 0:
            logging.info(f"Total operation duration: {duration:.2f} seconds")
            devices_per_second = self.total_devices / duration if duration > 0 else 0
            logging.info(f"Processing rate: {devices_per_second:.2f} devices/second")

def create_address_parse_failures_csv(parse_failures, filename="AddressParseFailures.csv"):
    """
    Create a CSV file documenting address parsing failures.
    
    Args:
        parse_failures (list): List of parse failure records
        filename (str): Output filename
    """
    if not parse_failures:
        logging.info("No address parsing failures to document.")
        return
    
    try:
        output_path = get_csv_file_path(filename)
        
        with open(output_path, "w", newline='', encoding="utf-8") as f:
            fieldnames = [
                'site_id', 'site_name', 'device_id', 'device_serial', 'device_name',
                'original_address', 'parsed_tokens', 'failure_reason', 'timestamp'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for failure in parse_failures:
                writer.writerow(failure)
        
        logging.info(f"Address parsing failures documented in: {filename} ({len(parse_failures)} records)")
        print(f"! Address parsing failures documented in: {filename} ({len(parse_failures)} records)")
        
    except Exception as e:
        logging.error(f"Failed to create address parse failures CSV: {e}")
        print(f"! Failed to create address parse failures CSV: {e}")

def get_device_identifier(device, warn_on_missing=False):
    """
    Get the best available identifier for a device with fallback logic.
    
    Args:
        device (dict): Device record
        warn_on_missing (bool): Whether to log a warning on first missing name
        
    Returns:
        str: Device identifier (name, serial, or device_id)
    """
    # Try name first
    name = device.get("name", "").strip()
    if name:
        return name
    
    # Fall back to serial
    serial = device.get("serial", "").strip()
    if serial:
        if warn_on_missing:
            logging.warning(f"Device {serial} missing name field, using serial as identifier")
        return serial
    
    # Fall back to device_id
    device_id = device.get("id", "").strip()
    if device_id:
        if warn_on_missing:
            logging.warning(f"Device {device_id} missing name and serial, using device_id as identifier")
        return device_id
    
    # Last resort
    if warn_on_missing:
        logging.warning("Device found with no name, serial, or id - using 'UNKNOWN'")
    return "UNKNOWN"

def compare_inventory_with_csv(fast=False, address_check=False, debug=False, skip_ssl_verify=True):
    """
    Compares combined inventory data with site info against a user-selected CSV file.
    Shows items where addresses don't meet the configured similarity threshold.
    Skips items that aren't in the comparison CSV file.
    Uses configurable ADDRESS_MATCH_THRESHOLD from .env file for fuzzy address matching.
    
    Enhanced with:
    - Hardened address parsing with defensive error handling
    - Comprehensive metrics and counters
    - Parse failure artifact generation
    - Improved logging and observability
    - Better handling of "Unknown" addresses
    - Unicode normalization and fuzzy matching improvements
    
    Args:
        fast (bool): If True, enables optimized data generation mode using cached data
                    and concurrent processing where applicable.
        address_check (bool): If True, enables external address validation using Nominatim API.
                             Overrides ENABLE_ADDRESS_VALIDATION setting from .env file.
        debug (bool): If True, enables detailed debug logging for API requests and responses.
        skip_ssl_verify (bool): If True, skips SSL certificate verification for external APIs.
    """
    # Initialize counters for comprehensive tracking
    counters = AddressComparisonCounters()
    counters.start_timing()
    parse_failures = []  # Track parsing failures for artifact generation

    # Load environment variables
    load_dotenv()
    END_CUSTOMER_NAME = os.getenv("END_CUSTOMER_NAME")
    END_CUSTOMER_ACCOUNT_ID = os.getenv("END_CUSTOMER_ACCOUNT_ID")
    
    # Get configurable address match threshold (default: 75%)
    ADDRESS_MATCH_THRESHOLD = float(os.getenv("ADDRESS_MATCH_THRESHOLD", "75"))

    print("* Data Integrity Analysis: Comparing Mist vs Comparison CSV addresses...")
    print(f"* Using address similarity threshold: {ADDRESS_MATCH_THRESHOLD}% (conflicts below this will be flagged)")
    print(f"* Enhanced features: defensive parsing, Unicode normalization, fuzzy matching")
    if fast:
        print("* Fast mode enabled: Using optimized data generation and caching")
    if debug:
        print(" Debug mode enabled: Detailed comparison logging active")
        logging.debug("ENTRY: compare_inventory_with_csv()")
        logging.debug(f"  Parameters: fast={fast}, address_check={address_check}, debug={debug}")
        logging.debug(f"  ADDRESS_MATCH_THRESHOLD={ADDRESS_MATCH_THRESHOLD}")
    
    # Check if address validation is enabled
    address_validation_enabled = address_check or os.getenv("ENABLE_ADDRESS_VALIDATION", "false").lower() == "true"
    
    if address_validation_enabled:
        source = "--address-check flag" if address_check else ".env file"
        print(f"! External address validation enabled via {source}")
        print(f"   Address conflicts will be validated using Nominatim API")
        if debug:
            logging.debug(f"Address validation enabled via {source}")
    else:
        print("  External address validation disabled")
        print("   Use --address-check flag or set ENABLE_ADDRESS_VALIDATION=true in .env to enable intelligent address recommendations")
        if debug:
            logging.debug("Address validation disabled")
    
    # Use efficient caching instead of always regenerating fresh data
    check_and_generate_csv("AllDevicesWithSiteInfo.csv", lambda: export_devices_with_site_info_to_csv(fast=fast))

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
        print(" No CSV files found in the data directory for comparison.")
        print(f"   Please place comparison CSV files in the '{data_dir}' folder.")
        logging.error("No CSV files found for comparison in data directory.")
        return

    # Present CSV files to user for selection
    print("\n  Available CSV files for comparison:")
    print("=" * 60)
    for idx, csv_file in enumerate(csv_files):
        print(f"[{idx}] {csv_file}")
    
    try:
        user_input = input(f"\nEnter the index (0-{len(csv_files)-1}) of the CSV file to compare against: ").strip()
        selected_index = int(user_input)
        
        if selected_index < 0 or selected_index >= len(csv_files):
            print(" Invalid index selected.")
            logging.error(f"Invalid CSV file index selected: {selected_index}")
            return
            
        comparison_file = csv_files[selected_index]
        print(f"! Selected comparison file: {comparison_file}")
        logging.info(f"User selected comparison file: {comparison_file}")
        
    except ValueError:
        print(" Invalid input. Please enter a numeric index.")
        logging.error("Invalid numeric input for CSV file selection.")
        return
    except KeyboardInterrupt:
        print("\n Operation cancelled by user.")
        logging.info("CSV comparison operation cancelled by user.")
        return

    # Load the comparison CSV file
    try:
        comparison_file_path = get_csv_file_path(comparison_file)
        with open(comparison_file_path, mode="r", encoding="utf-8") as f:
            comparison_data = list(csv.DictReader(f))
    except Exception as e:
        print(f"! Error reading comparison file {comparison_file}: {e}")
        logging.error(f"Error reading comparison file {comparison_file}: {e}")
        return

    print(f"! Loaded {len(site_configs)} devices from AllDevicesWithSiteInfo.csv")
    print(f"! Loaded {len(comparison_data)} records from {comparison_file}")

    # Load the address skip list for automatic corrections
    skip_addresses = []
    skip_file_path = get_csv_file_path("AddressSkip.csv")
    try:
        with open(skip_file_path, mode="r", encoding="utf-8") as f:
            skip_data = list(csv.DictReader(f))
            skip_addresses = skip_data
        print(f"! Loaded {len(skip_addresses)} skip addresses from AddressSkip.csv")
        if debug:
            logging.debug(f"Loaded {len(skip_addresses)} addresses to skip from AddressSkip.csv")
    except FileNotFoundError:
        print("  AddressSkip.csv not found - no addresses will be automatically skipped")
        if debug:
            logging.debug("AddressSkip.csv not found - continuing without skip list")
    except Exception as e:
        print(f"!  Error loading AddressSkip.csv: {e}")
        logging.warning(f"Error loading AddressSkip.csv: {e}")

    # Create lookup dictionaries for comparison data
    # Try common field names for serial number and zip code
    comparison_serials = {}
    comparison_zip_lookup = {}
    
    # Detect field names in comparison CSV
    if not comparison_data:
        print(" Comparison CSV file is empty.")
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
        print(" Could not find serial number field in comparison CSV.")
        print("   Looked for fields containing: 'serial', 'sn', 'system serial'")
        print(f"   Available fields: {list(comparison_headers)}")
        logging.error(f"Serial field not found in {comparison_file}. Available fields: {list(comparison_headers)}")
        return
        
    if not zip_field:
        print(" Could not find zip code field in comparison CSV.")
        print("   Looked for fields containing: 'zip', 'postal', 'zip code', 'postal code'")
        print(f"   Available fields: {list(comparison_headers)}")
        logging.error(f"Zip field not found in {comparison_file}. Available fields: {list(comparison_headers)}")
        return

    print(f"! Using serial field: '{serial_field}'")
    print(f"! Using zip field: '{zip_field}'")
    if address_field:
        print(f"! Using address field: '{address_field}'")
    if city_field:
        print(f"! Using city field: '{city_field}'")
    if state_field:
        print(f"! Using state field: '{state_field}'")
    if country_field:
        print(f"! Using country field: '{country_field}'")

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

    print(f"! Built comparison lookup with {len(comparison_serials)} serial numbers")
    
    # Show validation count if address validation is enabled
    if address_validation_enabled:
        validation_count = len([d for d in site_configs if d.get('serial', '').strip() in comparison_serials])
        print(f"! Will validate {validation_count} address conflicts using Nominatim API")

    # Duplicate address detection between sites
    print("\n  Checking for duplicate addresses between sites...")
    
    # Get unique address per site for Mist data
    mist_site_addresses = {}  # site_name -> address_key
    for device in site_configs:
        site_name = device.get("site_name", "")
        if not site_name or site_name in mist_site_addresses:
            continue  # Skip if already processed this site
            
        mist_address = {
            'address': device.get("street", "").strip(),
            'city': device.get("city", "").strip(),
            'state': device.get("state", "").strip(),
            'zip': device.get("zip_code", "").strip()
        }
        
        # Skip empty addresses
        if not any([mist_address['address'], mist_address['city'], mist_address['state'], mist_address['zip']]):
            continue
        
        # Create normalized address key
        address_key = f"{mist_address['address'].lower()}|{mist_address['city'].lower()}|{mist_address['state'].lower()}|{mist_address['zip']}"
        mist_site_addresses[site_name] = {
            'address_key': address_key,
            'address': mist_address
        }
    
    # Find duplicate addresses between Mist sites
    mist_address_to_sites = {}  # address_key -> [list of site names]
    for site_name, addr_data in mist_site_addresses.items():
        address_key = addr_data['address_key']
        if address_key not in mist_address_to_sites:
            mist_address_to_sites[address_key] = []
        mist_address_to_sites[address_key].append(site_name)
    
    mist_duplicates = {addr_key: sites for addr_key, sites in mist_address_to_sites.items() if len(sites) > 1}
    
    # Get unique address per site for reference data
    ref_site_addresses = {}  # site_name -> address_key
    for device in site_configs:
        device_serial = device.get("serial", "").strip()
        site_name = device.get("site_name", "")
        
        if not site_name or site_name in ref_site_addresses or device_serial not in comparison_address_lookup:
            continue  # Skip if already processed this site or no reference data
            
        ref_data = comparison_address_lookup[device_serial]
        ref_address = {
            'address': ref_data.get("Address", "").strip(),
            'city': ref_data.get("City", "").strip(),
            'state': ref_data.get("State", "").strip(),
            'zip': ref_data.get("Zip", "").strip()
        }
        
        # Skip empty addresses
        if not any([ref_address['address'], ref_address['city'], ref_address['state'], ref_address['zip']]):
            continue
        
        # Create normalized address key
        address_key = f"{ref_address['address'].lower()}|{ref_address['city'].lower()}|{ref_address['state'].lower()}|{ref_address['zip']}"
        ref_site_addresses[site_name] = {
            'address_key': address_key,
            'address': ref_address
        }
    
    # Find duplicate addresses between reference sites
    ref_address_to_sites = {}  # address_key -> [list of site names]
    for site_name, addr_data in ref_site_addresses.items():
        address_key = addr_data['address_key']
        if address_key not in ref_address_to_sites:
            ref_address_to_sites[address_key] = []
        ref_address_to_sites[address_key].append(site_name)
    
    ref_duplicates = {addr_key: sites for addr_key, sites in ref_address_to_sites.items() if len(sites) > 1}
    
    # Report results
    if mist_duplicates:
        print("    Mist sites sharing the same address:")
        for addr_key, sites in mist_duplicates.items():
            # Get the actual address for display
            sample_site = sites[0]
            addr = mist_site_addresses[sample_site]['address']
            print(f"        Address: {addr['address']}, {addr['city']}, {addr['state']} {addr['zip']}")
            print(f"        Sites ({len(sites)}): {', '.join(sites)}")
    
    if ref_duplicates:
        print("    Reference sites sharing the same address:")
        for addr_key, sites in ref_duplicates.items():
            # Get the actual address for display
            sample_site = sites[0]
            addr = ref_site_addresses[sample_site]['address']
            print(f"        Address: {addr['address']}, {addr['city']}, {addr['state']} {addr['zip']}")
            print(f"        Sites ({len(sites)}): {', '.join(sites)}")
    
    # Summary
    if not mist_duplicates and not ref_duplicates:
        print("    No duplicate addresses found between sites")
    else:
        print(f"     Found {len(mist_duplicates)} Mist address duplications affecting {sum(len(sites) for sites in mist_duplicates.values())} sites")
        print(f"     Found {len(ref_duplicates)} reference address duplications affecting {sum(len(sites) for sites in ref_duplicates.values())} sites")
        if debug:
            logging.info(f"DUPLICATE_CHECK: Found {len(mist_duplicates)} Mist duplicates and {len(ref_duplicates)} reference duplicates between sites")

    # Process device data and find address mismatches using configurable threshold
    # IMPROVED ORDER OF OPERATIONS:
    # 1. Fix both addresses first (normalize, parse, clean up)  
    # 2. Remove duplicates (addresses that are the same after normalization)
    # 3. Remove addresses in skip file (known problematic addresses)
    # 4. Then validate remaining conflicts with external API
    
    mismatched_items = []
    diff_report_items = []
    skipped_count = 0
    validation_count = 0
    devices_needing_validation = []  # Will be populated after filtering
    
    print(f"\n  Processing {len(site_configs)} total devices with improved order of operations...")
    print(" Step 1: Parsing and normalizing all addresses...")
    
    # Step 1: Process all devices, fix addresses, and identify initial mismatches
    all_conflicts = []  # Store all conflicts before filtering
    counters.total_devices = len(site_configs)
    first_missing_name_warned = False
    
    for device in tqdm(site_configs, desc="Step 1: Parsing Addresses", unit="device"):
        device_serial = device.get("serial", "").strip()
        device_identifier = get_device_identifier(device, warn_on_missing=not first_missing_name_warned)
        
        if not first_missing_name_warned and device_identifier != device.get("name", "").strip():
            first_missing_name_warned = True
        
        # Skip if device serial not in comparison file
        if device_serial not in comparison_serials:
            counters.devices_skipped += 1
            if debug:
                logging.debug(f"DEVICE_SKIP [{device_serial}]: Not found in comparison CSV (available: {len(comparison_serials)} serials)")
            continue
        
        counters.devices_enriched += 1
        
        # Enhanced address parsing with error handling
        try:
            # Parse Mist address with enhanced parsing
            mist_address_raw = device.get("site_address", "").strip()
            if not mist_address_raw:
                # Fall back to component parsing if no combined address
                mist_address = {
                    'address': device.get("street", "").strip(),
                    'city': device.get("city", "").strip(),
                    'state': device.get("state", "").strip(),
                    'zip': device.get("zip_code", "").strip()
                }
            else:
                # Use enhanced parsing for combined address
                parsed_mist = enhanced_usaddress_parse(mist_address_raw, debug=debug)
                if not parsed_mist['is_parseable']:
                    # Document parsing failure
                    failure_record = {
                        'site_id': device.get("site_id", ""),
                        'site_name': device.get("site_name", ""),
                        'device_id': device.get("id", ""),
                        'device_serial': device_serial,
                        'device_name': device_identifier,
                        'original_address': mist_address_raw,
                        'parsed_tokens': str(mist_address_raw.split(',')),
                        'failure_reason': parsed_mist['parse_reason'],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    parse_failures.append(failure_record)
                    counters.increment_parse_failure(parsed_mist['parse_reason'])
                    
                    # Fall back to component parsing
                    mist_address = {
                        'address': device.get("street", "").strip(),
                        'city': device.get("city", "").strip(),
                        'state': device.get("state", "").strip(),
                        'zip': device.get("zip_code", "").strip()
                    }
                else:
                    mist_address = {
                        'address': parsed_mist.get('address') or "",
                        'city': parsed_mist.get('city') or "",
                        'state': parsed_mist.get('state') or "",
                        'zip': parsed_mist.get('zip') or ""
                    }
            
            # Parse comparison address
            comparison_address_data = comparison_address_lookup.get(device_serial, {})
            
            # Additional safety check: if no comparison data found, skip this device
            if not comparison_address_data or not any(comparison_address_data.values()):
                counters.devices_skipped += 1
                if debug:
                    logging.debug(f"DEVICE_SKIP [{device_serial}]: No comparison address data found")
                continue
            
            comparison_address_raw = f"{comparison_address_data.get('Address', '')}, {comparison_address_data.get('City', '')}, {comparison_address_data.get('State', '')}, {comparison_address_data.get('Zip', '')}".strip(", ")
            
            if comparison_address_raw and comparison_address_raw != "   ":
                parsed_comp = enhanced_usaddress_parse(comparison_address_raw, debug=debug)
                if not parsed_comp['is_parseable']:
                    # Document parsing failure for comparison address
                    failure_record = {
                        'site_id': 'COMPARISON_CSV',
                        'site_name': 'COMPARISON_CSV', 
                        'device_id': device_serial,
                        'device_serial': device_serial,
                        'device_name': device_identifier,
                        'original_address': comparison_address_raw,
                        'parsed_tokens': str(comparison_address_raw.split(',')),
                        'failure_reason': parsed_comp['parse_reason'],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    parse_failures.append(failure_record)
                    counters.increment_parse_failure(f"comparison_{parsed_comp['parse_reason']}")
            
            comparison_address = {
                'address': comparison_address_data.get("Address", "").strip(),
                'city': comparison_address_data.get("City", "").strip(),
                'state': comparison_address_data.get("State", "").strip(),
                'zip': comparison_address_data.get("Zip", "").strip()
            }
            
            # Validate that we have meaningful comparison data
            if not any([comparison_address['address'], comparison_address['city'], comparison_address['state'], comparison_address['zip']]):
                counters.devices_skipped += 1
                if debug:
                    logging.debug(f"DEVICE_SKIP [{device_serial}]: Empty comparison address data")
                continue
            
            if debug:
                logging.debug(f"DEVICE_COMPARISON [{device_serial}]: Mist address: {mist_address}")
                logging.debug(f"DEVICE_COMPARISON [{device_serial}]: Comparison address: {comparison_address}")
            
            # Enhanced address comparison with defensive parsing
            comparison_result = enhanced_compare_addresses_with_threshold(
                mist_address, comparison_address, ADDRESS_MATCH_THRESHOLD, debug=debug
            )
            
            if debug:
                logging.debug(f"DEVICE_COMPARISON [{device_serial}]: Enhanced similarity result: {comparison_result}")
            
            # Track match/mismatch statistics
            if comparison_result['is_match']:
                counters.perfect_matches += 1
            else:
                counters.mismatches_found += 1
                # Store conflict for further filtering
                all_conflicts.append({
                    'device': device,
                    'device_serial': device_serial,
                    'device_identifier': device_identifier,
                    'mist_address': mist_address,
                    'comparison_address': comparison_address,
                    'comparison_result': comparison_result
                })
                
        except Exception as device_error:
            logging.warning(f"! Error processing device {device_serial}: {device_error}")
            counters.comparison_failures += 1
            
            # Document this as a parse failure
            failure_record = {
                'site_id': device.get("site_id", ""),
                'site_name': device.get("site_name", ""),
                'device_id': device.get("id", ""),
                'device_serial': device_serial,
                'device_name': device_identifier if 'device_identifier' in locals() else device_serial,
                'original_address': str(device.get("site_address", "")),
                'parsed_tokens': 'N/A',
                'failure_reason': f'device_processing_error: {str(device_error)}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            parse_failures.append(failure_record)
            counters.increment_parse_failure('device_processing_error')

    print(f"! Step 1 Complete: Found {len(all_conflicts)} address conflicts from {counters.devices_enriched} analyzed devices")
    
    # Step 2: Remove duplicate addresses (after normalization) 
    print(" Step 2: Removing duplicate addresses...")
    unique_conflicts = []
    seen_addresses = set()
    
    for conflict in all_conflicts:
        # Create normalized address key for deduplication
        mist_addr = conflict['mist_address']
        comp_addr = conflict['comparison_address']
        address_key = f"{mist_addr['address'].lower().strip()}|{mist_addr['city'].lower().strip()}|{mist_addr['state'].lower().strip()}|{mist_addr['zip'].strip()}" + \
                     f"||{comp_addr['address'].lower().strip()}|{comp_addr['city'].lower().strip()}|{comp_addr['state'].lower().strip()}|{comp_addr['zip'].strip()}"
        
        if address_key not in seen_addresses:
            seen_addresses.add(address_key)
            unique_conflicts.append(conflict)
        else:
            if debug:
                logging.debug(f"DUPLICATE_REMOVED [{conflict['device_serial']}]: Address pair already seen")
    
    duplicates_removed = len(all_conflicts) - len(unique_conflicts)
    print(f"! Step 2 Complete: Removed {duplicates_removed} duplicate address pairs, {len(unique_conflicts)} unique conflicts remain")
    
    # Step 3: Remove addresses in skip file
    print(" Step 3: Applying address skip filters...")
    filtered_conflicts = []
    
    for conflict in unique_conflicts:
        comparison_address = conflict['comparison_address']
        device_serial = conflict['device_serial']
        
        # Check if comparison address should be automatically skipped
        should_skip, skip_reason = check_address_should_skip(comparison_address, skip_addresses, debug=debug)
        
        if should_skip:
            # Automatically treat as a match (Mist address is correct)
            counters.perfect_matches += 1
            counters.auto_corrections += 1
            
            if debug:
                logging.debug(f"ADDRESS_SKIP [{device_serial}]: Skipped comparison address due to: {skip_reason}")
            
            print(f"    Auto-corrected: {device_serial} (Skip reason: {skip_reason})")
        else:
            filtered_conflicts.append(conflict)
    
    skip_filtered = len(unique_conflicts) - len(filtered_conflicts)
    print(f"! Step 3 Complete: Removed {skip_filtered} addresses via skip filters, {len(filtered_conflicts)} conflicts require analysis")
    
    # Step 4: Prepare for external validation (only if enabled)
    if address_validation_enabled and filtered_conflicts:
        devices_needing_validation = [(c['device'], c['device_serial'], c['mist_address'], c['comparison_address']) for c in filtered_conflicts]
        total_validations = len(devices_needing_validation)
        print(f"\n  Step 4: External address validation enabled - {total_validations} remaining conflicts need validation")
        print(" This may take several minutes due to API rate limiting (1 request/second)...")
        if debug:
            logging.debug(f"ADDRESS_VALIDATION: {total_validations} devices require external validation after filtering")
    elif not address_validation_enabled and filtered_conflicts:
        # Process conflicts without validation
        print(f"\n  Step 4: Processing {len(filtered_conflicts)} conflicts without external validation...")
        for conflict in filtered_conflicts:
            device = conflict['device'] 
            device_serial = conflict['device_serial']
            comparison_result = conflict['comparison_result']
            mist_address = conflict['mist_address']
            comparison_address = conflict['comparison_address']
            
            # Generate mismatch records
            try:
                created_time = int(device.get("created_time", 0))
                created_date = datetime.fromtimestamp(created_time, tz=timezone.utc)
                year, week, _ = created_date.isocalendar()
                week_key = f"{year}_Week_{week:02d}"

                # Determine primary mismatch type based on failed fields
                failed_fields = comparison_result['failed_fields']
                if 'zip' in failed_fields and len(failed_fields) == 1:
                    mismatch_type = "Zip Code Mismatch"
                elif 'address' in failed_fields:
                    mismatch_type = "Address Mismatch"
                elif 'city' in failed_fields:
                    mismatch_type = "City Mismatch"
                elif 'state' in failed_fields:
                    mismatch_type = "State Mismatch"
                else:
                    mismatch_type = "Multi-field Address Mismatch"

                # Enhanced mismatch item with parse status
                mismatched_item = {
                    "Week": week_key,
                    "Full Site": device.get("site_name", ""),
                    "System Serial Number": device_serial,
                    "System Model Number": device.get("model", ""),
                    "End Customer Name": END_CUSTOMER_NAME,
                    "Address Line 1": mist_address['address'],
                    "Address Line 2": "",
                    "City": mist_address['city'],
                    "State": mist_address['state'],
                    "Current Zip Code": mist_address['zip'],
                    "Current Zip Normalized": normalize_zip_code(mist_address['zip']),
                    "Comparison Zip Code": comparison_address['zip'],
                    "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                    "Mismatch Type": mismatch_type,
                    "Overall Similarity": f"{comparison_result['overall_similarity']:.1f}%",
                    "Address Similarity": f"{comparison_result['field_similarities']['address']:.1f}%",
                    "City Similarity": f"{comparison_result['field_similarities']['city']:.1f}%",
                    "State Similarity": f"{comparison_result['field_similarities']['state']:.1f}%",
                    "Zip Similarity": f"{comparison_result['field_similarities']['zip']:.1f}%",
                    "Failed Fields": ', '.join(failed_fields),
                    # Enhanced fields
                    "Mist_Parse_Status": comparison_result['parse_status']['mist_parseable'],
                    "Comparison_Parse_Status": comparison_result['parse_status']['comparison_parseable'],
                    "Parse_Issues": f"Mist: {comparison_result['parse_status']['mist_reason']}, Comp: {comparison_result['parse_status']['comparison_reason']}",
                    # Address validation results (No validation in basic mode)
                    "Mist_Validation_Status": 'N/A',
                    "Mist_Confidence": 'N/A',
                    "Comparison_Validation_Status": 'N/A',
                    "Comparison_Confidence": 'N/A',
                    "Validation_Recommendation": 'N/A'
                }
                mismatched_items.append(mismatched_item)

                # Enhanced diff report item with parse status
                diff_item = {
                    "Week": week_key,
                    "Full Site": device.get("site_name", ""),
                    "System Serial Number": device_serial,
                    "System Model Number": device.get("model", ""),
                    "End Customer Name": END_CUSTOMER_NAME,
                    "Mist_Address_Line_1": mist_address['address'],
                    "Mist_City": mist_address['city'],
                    "Mist_State": mist_address['state'],
                    "Mist_Zip_Code": mist_address['zip'],
                    "Mist_Zip_Normalized": normalize_zip_code(mist_address['zip']),
                    "Comparison_Address": comparison_address['address'],
                    "Comparison_City": comparison_address['city'],
                    "Comparison_State": comparison_address['state'],
                    "Comparison_Zip_Code": comparison_address['zip'],
                    "Comparison_Zip_Normalized": normalize_zip_code(comparison_address['zip']),
                    "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                    "Mismatch Type": mismatch_type,
                    "Overall Similarity": f"{comparison_result['overall_similarity']:.1f}%",
                    "Address Similarity": f"{comparison_result['field_similarities']['address']:.1f}%",
                    "City Similarity": f"{comparison_result['field_similarities']['city']:.1f}%",
                    "State Similarity": f"{comparison_result['field_similarities']['state']:.1f}%",
                    "Zip Similarity": f"{comparison_result['field_similarities']['zip']:.1f}%",
                    "Failed Fields": ', '.join(failed_fields),
                    # Enhanced fields
                    "Mist_Parse_Status": comparison_result['parse_status']['mist_parseable'],
                    "Comparison_Parse_Status": comparison_result['parse_status']['comparison_parseable'],
                    "Parse_Issues": f"Mist: {comparison_result['parse_status']['mist_reason']}, Comp: {comparison_result['parse_status']['comparison_reason']}",
                    # Address validation results (No validation in basic mode)
                    "Mist_Validation_Status": 'N/A',
                    "Mist_Confidence": 'N/A',
                    "Comparison_Validation_Status": 'N/A',
                    "Comparison_Confidence": 'N/A',
                    "Validation_Recommendation": 'N/A'
                }
                diff_report_items.append(diff_item)
                
            except Exception as mismatch_error:
                logging.warning(f"! Error processing mismatch for device {device_serial}: {mismatch_error}")
                counters.comparison_failures += 1
    
    # Step 4 (continued): Process devices that need validation with proper progress bar
    if address_validation_enabled and devices_needing_validation:
        # Get organization name for intelligent tiebreaker logic
        org_name = None
        try:
            if debug:
                logging.debug("Fetching organization information for tiebreaker logic...")
            org_response = mistapi.api.v1.orgs.orgs.getOrg(apisession, org_id)
            if org_response.status_code == 200:
                org_data = org_response.data
                org_name = org_data.get('name', '').strip()
                if debug:
                    logging.debug(f"Organization name retrieved: '{org_name}'")
            else:
                if debug:
                    logging.warning(f"Failed to retrieve organization info: HTTP {org_response.status_code}")
        except Exception as e:
            if debug:
                logging.warning(f"Could not retrieve organization name for tiebreaker: {e}")
        
        validation_count = 0
        for device, device_serial, mist_address, comparison_address in tqdm(devices_needing_validation, desc="Step 4: Validating Addresses", unit="device"):
            validation_count += 1
            if debug:
                logging.debug(f"DEVICE_VALIDATION [{device_serial}]: Starting validation process")
                logging.debug(f"DEVICE_VALIDATION [{device_serial}]: Mist address: {mist_address}")
                logging.debug(f"DEVICE_VALIDATION [{device_serial}]: Comparison address: {comparison_address}")
            
            # Find the corresponding conflict for this device
            conflict = next((c for c in filtered_conflicts if c['device_serial'] == device_serial), None)
            if not conflict:
                logging.warning(f"Could not find conflict data for device {device_serial}")
                continue
                
            comparison_result = conflict['comparison_result']
            
            if debug:
                logging.debug(f"DEVICE_VALIDATION [{device_serial}]: Similarity result: {comparison_result}")
            
            # Perform external address validation
            validation_result = None
            ADDRESS_VALIDATION_TIMEOUT = int(os.getenv("ADDRESS_VALIDATION_TIMEOUT", "10"))
            
            try:
                # Create formatted address strings for logging
                mist_addr_str = f"{mist_address['address']}, {mist_address['city']}, {mist_address['state']} {mist_address['zip']}".replace(", , ", ", ").strip(", ")
                comp_addr_str = f"{comparison_address['address']}, {comparison_address['city']}, {comparison_address['state']} {comparison_address['zip']}".replace(", , ", ", ").strip(", ")
                
                print(f"! [{validation_count}/{total_validations}] Validating {device_serial}...")
                print(f"    Mist:       {mist_addr_str}")
                print(f"    Reference:  {comp_addr_str}")
                
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Starting validation")
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Mist address: {mist_addr_str}")
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Comparison address: {comp_addr_str}")
                
                validation_result = validate_addresses_with_nominatim(
                    mist_address, comparison_address, ADDRESS_VALIDATION_TIMEOUT, debug=debug, skip_ssl_verify=skip_ssl_verify, org_name=org_name,
                    mist_duplicates=mist_duplicates, ref_duplicates=ref_duplicates, site_name=device.get("site_name", "")
                )
                
                # Format results for display
                mist_status = " Valid" if validation_result['mist_validation']['valid'] else " Invalid"
                comp_status = " Valid" if validation_result['comparison_validation']['valid'] else " Invalid"
                
                mist_conf = f"{validation_result['mist_validation']['confidence']:.3f}" if validation_result['mist_validation']['valid'] else "N/A"
                comp_conf = f"{validation_result['comparison_validation']['confidence']:.3f}" if validation_result['comparison_validation']['valid'] else "N/A"
                
                recommendation_icon = {"mist": " Mist", "comparison": " Reference", "uncertain": " Uncertain"}
                recommendation_display = recommendation_icon.get(validation_result['recommendation'], validation_result['recommendation'])
                recommendation_reason = validation_result.get('recommendation_reason', 'No reason provided')
                
                print(f"    Results:    Mist: {mist_status} (conf: {mist_conf}) | Reference: {comp_status} (conf: {comp_conf})")
                print(f"    Recommendation: {recommendation_display}")
                if validation_result['recommendation'] != 'uncertain' or 'inconclusive' not in recommendation_reason.lower():
                    print(f"    Reason: {recommendation_reason}")
                
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Mist validation - valid: {validation_result['mist_validation']['valid']}, confidence: {mist_conf}")
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Comparison validation - valid: {validation_result['comparison_validation']['valid']}, confidence: {comp_conf}")
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Final recommendation: {validation_result['recommendation']}")
                logging.info(f"ADDRESS_VALIDATION [{device_serial}]: Recommendation reason: {recommendation_reason}")
                
            except Exception as e:
                print(f"    Validation failed: {str(e)}")
                logging.warning(f"ADDRESS_VALIDATION [{device_serial}]: Validation failed: {e}")
                if debug:
                    logging.debug(f"ADDRESS_VALIDATION [{device_serial}]: Full exception traceback: {traceback.format_exc()}")
                validation_result = None
            
            # Process mismatch logic for this device
            if not comparison_result['is_match']:
                try:
                    created_time = int(device.get("created_time", 0))
                    created_date = datetime.fromtimestamp(created_time, tz=timezone.utc)
                    year, week, _ = created_date.isocalendar()
                    week_key = f"{year}_Week_{week:02d}"

                    # Determine primary mismatch type based on failed fields
                    failed_fields = comparison_result['failed_fields']
                    if 'zip' in failed_fields and len(failed_fields) == 1:
                        mismatch_type = "Zip Code Mismatch"
                    elif 'address' in failed_fields:
                        mismatch_type = "Address Mismatch"
                    elif 'city' in failed_fields:
                        mismatch_type = "City Mismatch"
                    elif 'state' in failed_fields:
                        mismatch_type = "State Mismatch"
                    else:
                        mismatch_type = "Multi-field Address Mismatch"

                    # Standard mismatch item (enhanced format)
                    mismatched_item = {
                        "Week": week_key,
                        "Full Site": device.get("site_name", ""),
                        "System Serial Number": device_serial,
                        "System Model Number": device.get("model", ""),
                        "End Customer Name": END_CUSTOMER_NAME,
                        "Address Line 1": mist_address['address'],
                        "Address Line 2": "",
                        "City": mist_address['city'],
                        "State": mist_address['state'],
                        "Current Zip Code": mist_address['zip'],
                        "Current Zip Normalized": normalize_zip_code(mist_address['zip']),
                        "Comparison Zip Code": comparison_address['zip'],
                        "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                        "Mismatch Type": mismatch_type,
                        "Overall Similarity": f"{comparison_result['overall_similarity']:.1f}%",
                        "Address Similarity": f"{comparison_result['field_similarities']['address']:.1f}%",
                        "City Similarity": f"{comparison_result['field_similarities']['city']:.1f}%",
                        "State Similarity": f"{comparison_result['field_similarities']['state']:.1f}%",
                        "Zip Similarity": f"{comparison_result['field_similarities']['zip']:.1f}%",
                        "Failed Fields": ', '.join(failed_fields),
                        # Address validation results (if enabled)
                        "Mist_Validation_Status": validation_result['mist_validation']['valid'] if validation_result else 'N/A',
                        "Mist_Confidence": f"{validation_result['mist_validation']['confidence']:.3f}" if validation_result and validation_result['mist_validation']['valid'] else 'N/A',
                        "Comparison_Validation_Status": validation_result['comparison_validation']['valid'] if validation_result else 'N/A',
                        "Comparison_Confidence": f"{validation_result['comparison_validation']['confidence']:.3f}" if validation_result and validation_result['comparison_validation']['valid'] else 'N/A',
                        "Validation_Recommendation": validation_result['recommendation'] if validation_result else 'N/A'
                    }
                    mismatched_items.append(mismatched_item)

                    # Diff report item (showing both address sets with similarity scores)
                    diff_item = {
                        "Week": week_key,
                        "Full Site": device.get("site_name", ""),
                        "System Serial Number": device_serial,
                        "System Model Number": device.get("model", ""),
                        "End Customer Name": END_CUSTOMER_NAME,
                        "Mist_Address_Line_1": mist_address['address'],
                        "Mist_City": mist_address['city'],
                        "Mist_State": mist_address['state'],
                        "Mist_Zip_Code": mist_address['zip'],
                        "Mist_Zip_Normalized": normalize_zip_code(mist_address['zip']),
                        "Comparison_Address": comparison_address['address'],
                        "Comparison_City": comparison_address['city'],
                        "Comparison_State": comparison_address['state'],
                        "Comparison_Zip_Code": comparison_address['zip'],
                        "Comparison_Zip_Normalized": normalize_zip_code(comparison_address['zip']),
                        "End Customer Account ID": END_CUSTOMER_ACCOUNT_ID,
                        "Mismatch Type": mismatch_type,
                        "Overall Similarity": f"{comparison_result['overall_similarity']:.1f}%",
                        "Address Similarity": f"{comparison_result['field_similarities']['address']:.1f}%",
                        "City Similarity": f"{comparison_result['field_similarities']['city']:.1f}%",
                        "State Similarity": f"{comparison_result['field_similarities']['state']:.1f}%", 
                        "Zip Similarity": f"{comparison_result['field_similarities']['zip']:.1f}%",
                        "Failed Fields": ', '.join(failed_fields),
                        # Address validation results (if enabled)
                        "Mist_Validation_Status": validation_result['mist_validation']['valid'] if validation_result else 'N/A',
                        "Mist_Confidence": f"{validation_result['mist_validation']['confidence']:.3f}" if validation_result and validation_result['mist_validation']['valid'] else 'N/A',
                        "Comparison_Validation_Status": validation_result['comparison_validation']['valid'] if validation_result else 'N/A',
                        "Comparison_Confidence": f"{validation_result['comparison_validation']['confidence']:.3f}" if validation_result and validation_result['comparison_validation']['valid'] else 'N/A',
                        "Validation_Recommendation": validation_result['recommendation'] if validation_result else 'N/A'
                    }
                    diff_report_items.append(diff_item)
                except Exception as e:
                    logging.warning(f"! Skipping device due to error: {e}")
    
    else:
        # Skip external validation section since it's already handled above in the improved order of operations
        pass

    # End timing and generate artifacts
    counters.end_timing()
    
    # Create parse failures artifact if there were any
    if parse_failures:
        create_address_parse_failures_csv(parse_failures)
    
    # Enhanced results display
    print(f"\n  Data Integrity Analysis Results:")
    print(f"   Total devices analyzed: {counters.total_devices}")
    print(f"   Devices with comparison data: {counters.devices_enriched}")
    print(f"    Devices excluded (not in comparison CSV): {counters.devices_skipped}")
    print(f"   Address conflicts found: {counters.mismatches_found}")
    print(f"   Consistent addresses: {counters.perfect_matches}")
    print(f"   Auto-skipped addresses: {counters.auto_corrections}")
    print(f"   Parse failures: {counters.parse_failures}")
    
    if counters.mismatches_found > 0:
        conflict_rate = (counters.mismatches_found / counters.devices_enriched) * 100
        print(f"   Conflict rate: {conflict_rate:.1f}% of analyzed devices have address discrepancies")
    
    if counters.parse_failures > 0:
        print(f"   Parse failure breakdown:")
        for reason, count in counters.parse_failure_reasons.items():
            print(f"      - {reason}: {count}")
    
    processing_rate = counters.total_devices / counters.get_duration() if counters.get_duration() > 0 else 0
    print(f"    Processing rate: {processing_rate:.1f} devices/second")

    # Log comprehensive summary
    counters.log_summary()

    if mismatched_items:
        print(f"\n  Data Integrity Conflicts (address discrepancies requiring review):")
        print("=" * 130)
        for idx, item in enumerate(mismatched_items[:10]):  # Show first 10
            mist_addr = f"{item.get('Mist_Address_Line_1', '')}, {item.get('Mist_City', '')}, {item.get('Mist_State', '')}"
            comp_addr = f"{item.get('Comparison_Address', '')}, {item.get('Comparison_City', '')}, {item.get('Comparison_State', '')}"
            print(f"[{idx+1:2}] Serial: {item['System Serial Number']:<15}")
            print(f"     Mist:       {mist_addr}")
            print(f"     Reference:  {comp_addr}")
            print(f"     Similarity: {item['Overall Similarity']:<6} | Type: {item['Mismatch Type']}")
            if address_validation_enabled and item.get('Validation_Recommendation', 'N/A') != 'N/A':
                print(f"     Recommendation: {item['Validation_Recommendation']}")
            print()
        
        if len(mismatched_items) > 10:
            print(f"   ... and {len(mismatched_items) - 10} more conflicts (see CSV report for complete list)")
            
        # Always save to CSV (no prompting)
        if mismatched_items:
            base_filename = comparison_file.replace('.csv', '')
            
            # Save comprehensive address comparison report with both address sets
            output_file = f"AddressMismatches_vs_{base_filename}.csv"
            fieldnames = [
                "Week", "Full Site", "System Serial Number", "System Model Number", 
                "End Customer Name", "Mist_Address_Line_1", "Mist_City", "Mist_State",
                "Mist_Zip_Code", "Mist_Zip_Normalized", "Comparison_Address", "Comparison_City", 
                "Comparison_State", "Comparison_Zip_Code", "Comparison_Zip_Normalized",
                "End Customer Account ID", "Mismatch Type", "Overall Similarity",
                "Address Similarity", "City Similarity", "State Similarity", "Zip Similarity", "Failed Fields",
                "Mist_Parse_Status", "Comparison_Parse_Status", "Parse_Issues",
                "Mist_Validation_Status", "Mist_Confidence", "Comparison_Validation_Status", "Comparison_Confidence", 
                "Validation_Recommendation"
            ]
            
            with open(output_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(diff_report_items)
            
            print(f"! Data integrity report saved to: {output_file}")
            print(f"! Location: {get_csv_file_path(output_file)}")
            print(f"\n  Data Integrity Summary:")
            print(f"   Found {len(diff_report_items)} address conflicts requiring review")
            if address_validation_enabled:
                print(f"   External validation recommendations included")
                print(f"   Check 'Validation_Recommendation' column for guidance")
            else:
                print(f"    No external validation performed")
                print(f"   Run with --address-check for intelligent recommendations")
            
            logging.info(f"Saved {len(diff_report_items)} address conflicts to {output_file}")
    else:
        total_good_addresses = counters.perfect_matches + counters.auto_corrections
        print(f"! Data integrity check complete! All {total_good_addresses} addresses are consistent.")
        print(f"   No conflicts found between Mist and comparison data")
        if counters.auto_corrections > 0:
            print(f"   {counters.auto_corrections} addresses auto-skipped via AddressSkip.csv")

def export_gateway_templates_to_csv():
    """
    Fetches all gateway templates for the organization and exports them to OrgGatewayTemplates.csv.
    """
    print("Gateway Templates:")
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
    DataExporter.save_data_to_output(templates, "OrgGatewayTemplates.csv")
    print(f"! {len(templates)} gateway templates exported to OrgGatewayTemplates.csv")
    logging.info(" Gateway templates exported to OrgGatewayTemplates.csv")

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
    print("Gateway Ports Overridden from Template (Compliance Outliers):")
    logging.info(" Identifying gateway ports with template overrides (outliers for compliance correction)...")

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
    logging.info(" First pass: Identifying devices with port overrides...")
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

    logging.info(f"! Found {len(devices_with_overrides)} devices with port overrides out of {len(configs)} total gateway devices")
    
    if not devices_with_overrides:
        logging.info(" No template overrides found - all gateways are compliant with their assigned templates!")
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
        print(f"! Gateway override report written to {output_file}")
        print(" No template overrides found - all gateways are compliant with their assigned templates!")
        return

    # OPTIMIZATION: Second pass - fetch device configs and stats only for devices with overrides
    logging.info(f"! Second pass: Fetching device configs and stats for {len(devices_with_overrides)} devices with overrides...")
    
    if fast and len(devices_with_overrides) > 5:  # Use connection pool management for fast mode with 5+ devices
        logging.info(" Using fast mode with connection pool management for device data fetching...")
        
        # Define worker function for fetching device configs and stats
        def fetch_device_data(device_info, connection_semaphore):
            """Worker function that fetches config and stats for a single device."""
            device_id = device_info[0]
            device_data = device_info[1]
            device_name = device_data["device_name"]
            site_id = device_data["site_id"]
            
            # Acquire connection semaphore before making API calls
            with connection_semaphore:
                port_configs = {}
                interface_stats = {}
                
                # Fetch live device info from getSiteDevice API for current config
                try:
                    resp = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
                    device_config_data = getattr(resp, "data", {})
                    port_configs = device_config_data.get("port_config", {})
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

                return (device_id, port_configs, interface_stats)
        
        # Prepare work items for the helper
        work_items = list(devices_with_overrides.items())
        
        # Use the reusable connection pool management helper
        successful_results, failed_devices = execute_with_connection_pool_management(
            work_items=work_items,
            worker_function=fetch_device_data,
            batch_description="override devices",
            retry_function=None  # No retry for this use case
        )
        
        # Build device_data_cache from successful results
        device_data_cache = {}
        for device_id, port_configs, interface_stats in successful_results:
            device_data_cache[device_id] = (port_configs, interface_stats)
        
        # Handle failed devices (fallback to empty configs)
        for failed_item in failed_devices:
            device_id = failed_item[0]
            device_data_cache[device_id] = ({}, {})
        
        logging.info(f"! Fast mode: Fetched data for {len(successful_results)}/{len(work_items)} devices with connection pool protection")
        
    else:
        # Regular sequential processing for non-fast mode or small datasets
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
    logging.info(" Third pass: Processing overridden ports with live data...")
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
    DataExporter.save_data_to_output(overridden_port_info, output_file)

    # Calculate summary statistics
    total_gateways_processed = len(configs)
    devices_with_overrides_count = len(devices_with_overrides) if 'devices_with_overrides' in locals() else 0
    if overridden_port_info:
        gateways_with_overrides = len(set(entry["device_id"] for entry in overridden_port_info))
    else:
        gateways_with_overrides = 0
    total_overridden_ports = len(overridden_port_info)

    logging.info(f"! Gateway override report written to {output_file} with {total_overridden_ports} overridden ports from {gateways_with_overrides} gateway devices.")
    logging.info(f"! API Optimization: Made device config/stats calls for only {devices_with_overrides_count} devices instead of all {total_gateways_processed} devices")
    print(f"! Gateway override report written to {output_file}")
    print(f"! Found {total_overridden_ports} overridden ports across {gateways_with_overrides} of {total_gateways_processed} gateway devices")
    print(f"! API Optimization: Only fetched live data for {devices_with_overrides_count} devices with overrides (saved {total_gateways_processed - devices_with_overrides_count} unnecessary API calls)")
    print(f"! Target ports analyzed: {', '.join(target_ports)}")
    print(f"! These are outliers that may need correction to match template configuration")
    
    if total_overridden_ports == 0:
        print(" No template overrides found - all gateways are compliant with their assigned templates!")

def convert_virtual_chassis_to_virtual_mac():
    """
    Presents a list of sites first, then shows switches that are virtual chassis at the selected site,
    lets the user select one, and calls the Mist API to convert the device to a virtual MAC.
    """
    print("\n  DESTRUCTIVE: Virtual Chassis to Virtual MAC Conversion")
    print("=" * 60)
    
    # First, prompt for site selection
    site_id = prompt_site_selection()
    if not site_id:
        print(" No site selected.")
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
    
    print(f"\n  Selected Site: {site_name} ({site_id})")
    
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
        print(f"! No virtual chassis switches found at site '{site_name}'.")
        print(" Virtual chassis switches must have a device ID assigned.")
        logging.warning(f"No virtual chassis switches found at site {site_id}.")
        return

    # Display indexed list to user
    print(f"\n  Available Virtual Chassis Switches at '{site_name}':")
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
        print(" Switch not found by index or name.")
        logging.warning(f"Switch not found: {user_input}")
        return

    device_id = selected.get("id")
    if not device_id:
        print(" Missing device_id for selected switch.")
        logging.warning("Missing device_id for selected switch.")
        return

    # Confirmation prompt for destructive operation
    print(f"\n   DESTRUCTIVE OPERATION WARNING ")
    print(f"You are about to convert switch '{selected.get('name', '')}' to virtual MAC.")
    print(f"Site: {site_name}")
    print(f"Device ID: {device_id}")
    print(f"MAC: {selected.get('mac', '')}")
    print(f"This operation cannot be undone!")
    
    confirm = input("\nType 'CONVERT' to proceed or anything else to cancel: ").strip()
    if confirm != "CONVERT":
        print(" Operation cancelled.")
        return

    print(f"! Converting switch '{selected.get('name', '')}' (device_id: {device_id}) at site '{site_name}' to virtual MAC...")
    try:
        # Call the Mist API to convert to virtual MAC
        resp = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(apisession, site_id, device_id)
        # Show the result to the user, including error details if present
        if hasattr(resp, "status_code") and resp.status_code >= 400:
            print(f"! Conversion failed (HTTP {resp.status_code}): {getattr(resp, 'data', '')}")
            logging.error(f"Conversion to virtual MAC failed for device {device_id} at site {site_id}. Response: {getattr(resp, 'data', '')}")
        elif isinstance(getattr(resp, "data", None), dict) and "detail" in resp.data:
            print(f"! Conversion failed: {resp.data['detail']}")
            logging.error(f"Conversion to virtual MAC failed for device {device_id} at site_id {site_id}. Detail: {resp.data['detail']}")
        else:
            print(" Conversion to virtual MAC triggered successfully!")
            print(" Check the device status in the Mist UI to monitor progress.")
            logging.info(f"Conversion to virtual MAC triggered for device {device_id} at site {site_id}. Response: {getattr(resp, 'data', '')}")
    except Exception as e:
        print(f"! Failed to convert to virtual MAC: {e}")
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
        print(f"! File '{csv_file}' not found.")
        print(f"   Please create this file at: {csv_file_path}")
        print("   This file should contain site names (one per line, no header).")
        
        # Offer to create a basic file
        user_input = input("   Would you like to create an empty file to get started? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            try:
                template_path = create_missing_csv_template("VCConvert.CSV")
                print(f"! Empty file created at: {template_path}")
                print("   Please edit the file to add your site names and run the script again.")
            except Exception as e:
                print(f"! Failed to create file: {e}")
        
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
        print(f"! Error reading {csv_file}: {e}")
        logging.error(f"Error reading VCConvert.CSV: {e}")
        return

    if not site_names:
        print(f"! No site names found in {csv_file}.")
        logging.warning("No site names found in VCConvert.CSV.")
        return

    print(f"! Loaded {len(site_names)} site names from {csv_file}:")
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
        print(f"! Error reading SiteList.csv: {e}")
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
        print(f"! Warning: The following sites were not found in the organization:")
        for site in missing_sites:
            print(f"   - {site}")

    if not target_site_ids:
        print(" No valid sites found. Exiting.")
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
        print(f"! Error reading OrgInventory.csv: {e}")
        logging.error(f"Error reading OrgInventory.csv: {e}")
        return

    if not switches_to_convert:
        print(" No virtual chassis switches found in the specified sites.")
        logging.warning("No virtual chassis switches found in target sites.")
        return

    # Display switches that will be converted
    print(f"\n  Found {len(switches_to_convert)} virtual chassis switches to convert:")
    print("=" * 100)
    for idx, switch in enumerate(switches_to_convert):
        print(f"[{idx+1:2}] Site: {switch.get('site_name', ''):25} | "
              f"Name: {switch.get('name', ''):20} | "
              f"MAC: {switch.get('mac', ''):17} | "
              f"Model: {switch.get('model', ''):12} | "
              f"Serial: {switch.get('serial', '')}")

    # Ask for user confirmation
    print(f"\n  This will convert {len(switches_to_convert)} virtual chassis switches to virtual MAC.")
    print(" This operation cannot be undone easily.")
    
    confirm = input("\n  Do you want to proceed with the conversion? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print(" Conversion cancelled by user.")
        logging.info("Virtual chassis conversion cancelled by user.")
        return

    # Proceed with conversions
    print(f"\n  Starting conversion of {len(switches_to_convert)} switches...")
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
                print(f"! Conversion failed (HTTP {resp.status_code}): {getattr(resp, 'data', '')}")
                logging.error(f"Conversion failed for {switch_name} at {site_name}. HTTP {resp.status_code}: {getattr(resp, 'data', '')}")
                failed_conversions += 1
            elif isinstance(getattr(resp, "data", None), dict) and "detail" in resp.data:
                print(f"! Conversion failed: {resp.data['detail']}")
                logging.error(f"Conversion failed for {switch_name} at {site_name}. Detail: {resp.data['detail']}")
                failed_conversions += 1
            else:
                print(f"! Conversion triggered successfully.")
                logging.info(f"Conversion triggered for {switch_name} at {site_name}. Response: {getattr(resp, 'data', '')}")
                successful_conversions += 1
                
        except Exception as e:
            print(f"! Exception during conversion: {e}")
            logging.error(f"Exception during conversion of {switch_name} at {site_name}: {e}")
            failed_conversions += 1

    # Summary
    print(f"\n  Conversion Summary:")
    print(f"   Successful conversions: {successful_conversions}")
    print(f"   Failed conversions: {failed_conversions}")
    print(f"   Total switches processed: {len(switches_to_convert)}")
    
    if successful_conversions > 0:
        print(f"\n  Note: Successful conversions may take a few minutes to complete.")
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
    print("\n  Virtual Chassis to Virtual MAC Conversion Status Check")
    print("=" * 70)
    print(" Checking all switches for virtual chassis conversion status...")
    print(" Converted switches have vc_mac starting with '020003'")
    
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
        print(f"! Error reading OrgInventory.csv: {e}")
        logging.error(f"Error reading OrgInventory.csv: {e}")
        return
    
    if not switches_with_vc_mac:
        print(" No switches with vc_mac found in the organization.")
        print(" Only virtual chassis switches have vc_mac assigned.")
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
    
    print(f"\n  Virtual Chassis Conversion Status Summary:")
    print(f"   Total virtual chassis switches: {total_switches}")
    print(f"   Converted to virtual MAC: {converted_count}")
    print(f"   Not converted: {not_converted_count}")
    
    if converted_count > 0:
        print(f"\n Converted Switches (vc_mac starts with '020003'):")
        for switch in converted_switches[:10]:  # Show first 10
            print(f"   � {switch.get('name', 'Unnamed'):20} | Site: {switch.get('site_name', ''):25} | vc_mac: {switch.get('vc_mac', '')[:8]}...")
        if len(converted_switches) > 10:
            print(f"   ... and {len(converted_switches) - 10} more")
    
    if not_converted_count > 0:
        print(f"\n Not Converted Switches (vc_mac does NOT start with '020003'):")
        for switch in not_converted_switches[:10]:  # Show first 10
            print(f"   � {switch.get('name', 'Unnamed'):20} | Site: {switch.get('site_name', ''):25} | vc_mac: {switch.get('vc_mac', '')[:8]}...")
        if len(not_converted_switches) > 10:
            print(f"   ... and {len(not_converted_switches) - 10} more")
    
    # Export to CSV
    try:
        # Flatten any nested fields for CSV export
        flattened_switches = flatten_nested_fields_in_list(all_switches)
        sanitized_switches = escape_multiline_strings_for_csv(flattened_switches)
        
        # Save to CSV
        filename = "VirtualChassisConversionStatus.csv"
        DataExporter.save_data_to_output(sanitized_switches, filename)
        
        print(f"\n  Results exported to: {filename}")
        print(f"   Location: {get_csv_file_path(filename)}")
        
        # Log results
        logging.info(f"Virtual chassis conversion status check completed:")
        logging.info(f"  Total switches: {total_switches}")
        logging.info(f"  Converted: {converted_count}")
        logging.info(f"  Not converted: {not_converted_count}")
        logging.info(f"  Results exported to {filename}")
        
    except Exception as e:
        print(f"! Error exporting results: {e}")
        logging.error(f"Error exporting conversion status results: {e}")
    
    print(f"\n  Usage Notes:")
    print(f"   � Use option 92 to convert individual switches")
    print(f"   � Use option 93 for bulk conversion by site list")
    print(f"   � Virtual chassis switches without '020003' vc_mac prefix can be converted")

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
    print("Export Site WiFi Clients:")
    logging.info("Starting export of site WiFi clients...")
    
    # Ensure required CSVs are fresh
    check_and_generate_csv("SiteList.csv", export_all_sites_to_csv)
    
    # Get site_id if not provided
    if not site_id:
        site_id = prompt_select_site_id_from_csv("SiteList.csv")
        if not site_id:
            logging.error(" No site selected.")
            print(" No site selected.")
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
        logging.warning(f"! Failed to load site name from SiteList.csv: {e}")
    
    logging.info(f"Fetching WiFi clients for site: {site_name} (ID: {site_id})")
    print(f"! Fetching WiFi clients for site: {site_name}")
    
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
            logging.warning(" No WiFi clients or sessions found at this site.")
            print(" No WiFi clients or sessions found at this site.")
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
            logging.warning(" No data to export after processing.")
            print(" No data to export after processing.")
            return
        
        # Flatten and sanitize the data for CSV
        flattened = flatten_nested_fields_in_list(enriched_clients)
        sanitized = escape_multiline_strings_for_csv(flattened)
        
        # Write to CSV
        DataExporter.save_data_to_output(sanitized, "SiteWiFiClients.CSV")
        
        client_count = len(clients) if clients else 0
        session_count = len(sessions) if sessions else 0
        total_records = len(enriched_clients)
        
        logging.info(f"! WiFi data exported to SiteWiFiClients.CSV ({client_count} clients, {session_count} sessions, {total_records} total records)")
        print(f"! WiFi data exported to SiteWiFiClients.CSV")
        print(f"   {client_count} current clients, {session_count} sessions, {total_records} total records from {site_name}")
        
    except Exception as e:
        logging.error(f"! Failed to fetch WiFi data for site {site_id}: {e}")
        print(f"! Failed to fetch WiFi data: {e}")

def reboot_devices_by_gateway_template_list():
    """
    Reboots all devices associated with branch templates listed in GatewayTemplateRebootList.CSV.
    Logs the result of each reboot command to GatewayTemplateRebootResults.CSV.
    """

    logging.info("[46] Starting reboot_devices_by_gateway_template_list")

    # Step 1: Check if the reboot list file exists
    reboot_list_path = get_csv_file_path("GatewayTemplateRebootList.CSV")
    if not os.path.exists(reboot_list_path):
        logging.error(" GatewayTemplateRebootList.CSV not found.")
        print(" GatewayTemplateRebootList.CSV not found.")
        print(f"   Please create this file at: {reboot_list_path}")
        print("   This file should contain template names to reboot, one per line.")
        
        # Offer to create a basic file
        user_input = input("   Would you like to create an empty file to get started? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            try:
                template_path = create_missing_csv_template("GatewayTemplateRebootList.CSV")
                print(f"! Empty file created at: {template_path}")
                print("   Please edit the file to add your template names and run the script again.")
            except Exception as e:
                print(f"! Failed to create file: {e}")
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
        logging.error(f"! Failed to load gateway templates: {e}")
        print(f"! Failed to load gateway templates: {e}")
        return

    if not template_name_to_id:
        logging.warning(" No gateway templates found in OrgGatewayTemplates.csv")
        print(" No gateway templates found in OrgGatewayTemplates.csv")
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
        logging.error(f"! Failed to load reboot template list: {e}")
        print(f"! Failed to load reboot template list: {e}")
        return

    # Step 5: Map template names to IDs and show matches/mismatches
    reboot_template_ids = set()
    for name in reboot_template_names:
        if name in template_name_to_id:
            reboot_template_ids.add(template_name_to_id[name])
            logging.info(f"! Found template '{name}' with ID '{template_name_to_id[name]}'")
        else:
            logging.warning(f"! Template '{name}' not found in OrgGatewayTemplates.csv")
            print(f"! Template '{name}' not found in available templates")

    if not reboot_template_ids:
        logging.error(" No matching template IDs found for reboot")
        print(" No matching template IDs found for reboot")
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
        logging.error(f"! Failed to load site list: {e}")
        print(f"! Failed to load site list: {e}")
        return

    if not sites_using_templates:
        logging.warning(" No sites found using the specified gateway templates")
        print(" No sites found using the specified gateway templates")
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
        logging.error(f"! Failed to load gateway configs: {e}")
        print(f"! Failed to load gateway configs: {e}")
        return

    if not reboot_targets:
        logging.warning(" No gateway devices found in sites using the specified templates")
        print(" No gateway devices found in sites using the specified templates")
        
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
    print(" DEVICE REBOOT CONFIRMATION REQUIRED ")
    print("=" * 100)
    print(f"\n  The following {len(reboot_targets)} gateway devices will be REBOOTED:")
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
        print(f"\n  Template: {template_name}")
        print(f"   {len(devices)} devices affected:")
        for device in devices:
            print(f"      � {device['device_name']} (ID: {device['device_id']}) at site '{device['site_name']}'")
    
    # Display critical warnings in a cleaner format
    warning_lines = [
        " CRITICAL WARNING - READ CAREFULLY:",
        "� This action will REBOOT network gateway devices",
        "� Network connectivity will be TEMPORARILY LOST during reboot",
        "� Users may experience service interruptions",
        "� Remote sites may become inaccessible during reboot",
        "� This is a DISRUPTIVE network operation",
        "� Ensure you have alternative access methods if needed",
        "� The script owner bears NO LIABILITY for any consequences",
        "� Proceed only if you understand and accept these risks"
    ]
    
    print("\n" + "??" * 50)
    for line in warning_lines:
        print(line)
    print("??" * 50)
    
    print(f"\n  Summary:")
    print(f"   � Total devices to reboot: {len(reboot_targets)}")
    print(f"   � Templates involved: {len(devices_by_template)}")
    print(f"   � Sites affected: {len(set(target['site_name'] for target in reboot_targets))}")
    
    # Get user confirmation with liability waiver
    print(f"\n  Do you want to proceed with rebooting {len(reboot_targets)} gateway devices?")
    print("   Type 'REBOOT' (all caps) to confirm, or anything else to cancel:")
    print("   By typing 'REBOOT', you acknowledge and accept all risks and liability.")
    
    try:
        user_input = input(">>> ").strip()
        if user_input != "REBOOT":
            print(" Reboot operation cancelled by user.")
            logging.info("Gateway reboot operation cancelled by user input")
            return
        else:
            print(" User confirmed reboot operation. Proceeding...")
            logging.info(f"! LIABILITY WAIVER ACCEPTED: User confirmed gateway reboot operation for {len(reboot_targets)} devices")
            logging.info(f"User input: '{user_input}' - User accepts full responsibility and liability for network disruption")
            # Log detailed device list for audit trail
            device_list = [f"{d['device_name']} ({d['device_id']}) at {d['site_name']}" for d in reboot_targets]
            logging.info(f"Devices to be rebooted: {device_list}")
    except KeyboardInterrupt:
        print("\n Reboot operation cancelled by user (Ctrl+C).")
        logging.info("Gateway reboot operation cancelled by user interrupt")
        return
    except Exception as e:
        print(f"! Error getting user input: {e}")
        logging.error(f"Error getting user input for reboot confirmation: {e}")
        return

    print("\n  Starting device reboot operations...")
    print("=" * 50)

    # Step 9: Reboot each device and log results
    results = []
    for device in reboot_targets:
        status = ""
        try:
            logging.info(f"Rebooting device '{device['device_name']}' (ID: {device['device_id']})")
            print(f"! Rebooting {device['device_name']} at {device['site_name']}...")
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
            print(f"   Reboot command sent successfully")
            logging.info(f"! Reboot command sent for '{device['device_name']}': {status}")
        except Exception as e:
            status = f"ERROR: {e}"
            print(f"   Failed to send reboot command: {e}")
            logging.error(f"! Failed to reboot '{device['device_name']}': {e}")

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
        
        print(f"\n  Operation completed!")
        print(f"   Reboot commands sent to {len(results)} devices")
        print(f"   Results logged to GatewayTemplateRebootResults.CSV")
        logging.info(f"! Reboot results written to GatewayTemplateRebootResults.CSV ({len(results)} entries)")
    except Exception as e:
        logging.error(f"! Failed to write results to CSV: {e}")
        print(f"! Failed to write results to CSV: {e}")


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
    
    print(" Firmware Upgrade Status Check")
    print("=" * 60)
    
    # Step 1: Choose scope (organization-wide or specific site)
    print("\n  Select status check scope:")
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
                print(" Invalid selection. Please choose 1-4.")
                logging.debug(f"Invalid scope selection: {scope_choice}")
        except KeyboardInterrupt:
            print("\n Operation cancelled by user.")
            return
    
    site_filter = None
    if scope_choice == '2':
        # Get specific site selection
        logging.debug("User selected specific site mode")
        site_filter = prompt_site_selection()
        if not site_filter:
            print(" No site selected. Exiting.")
            logging.warning("No site selected in specific site mode")
            return
        logging.debug(f"Selected site filter: {site_filter}")
    
    # Step 2: Fetch device statistics to get current firmware status
    print(f"\n  Fetching device statistics...")
    logging.debug(f"Fetching device statistics with scope: {scope_choice}, site_filter: {site_filter}")
    all_device_stats = []
    upgrade_results = []
    
    try:
        if site_filter:
            # Single site mode
            print(f"   Fetching stats for selected site...")
            logging.debug(f"Fetching stats for single site: {site_filter}")
            stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                apisession, 
                site_filter,
                limit=1000
            )
            site_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
            all_device_stats.extend(site_stats)
            
            print(f"   Retrieved stats for {len(site_stats)} devices at selected site")
            logging.info(f"Retrieved stats for {len(site_stats)} devices at site {site_filter}")
        else:
            # Organization-wide mode
            print(f"   Fetching organization-wide device statistics...")
            logging.debug(f"Fetching organization-wide stats for org: {org_id}")
            stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
                apisession, 
                org_id,
                limit=1000
            )
            org_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
            all_device_stats.extend(org_stats)
            
            print(f"   Retrieved stats for {len(org_stats)} devices organization-wide")
            logging.info(f"Retrieved stats for {len(org_stats)} devices organization-wide")
            
    except Exception as e:
        print(f"! Failed to fetch device statistics: {e}")
        logging.error(f"Failed to fetch device statistics: {e}")
        return
    
    if not all_device_stats:
        print(" No device statistics found.")
        return
    
    # Step 3: Process device firmware status
    print(f"\n  Analyzing firmware status for {len(all_device_stats)} devices...")
    
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
    print(f"   Fetching site information for device enrichment...")
    try:
        all_sites = fetch_all_sites_with_limit(org_id)
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
    print(f"\n  Firmware Status Summary:")
    print(f"   � Total devices analyzed: {firmware_status_summary['total_devices']}")
    print(f"   � Devices with upgrade info: {firmware_status_summary['devices_with_fwupdate']}")
    print(f"   � Upgrades in progress: {firmware_status_summary['upgrade_in_progress']}")
    print(f"   � Upgrades completed: {firmware_status_summary['upgrade_completed']}")
    print(f"   � Upgrades failed: {firmware_status_summary['upgrade_failed']}")
    print(f"   � Unknown status: {firmware_status_summary['upgrade_unknown']}")
    
    if firmware_status_summary['devices_by_status']:
        print(f"\n  Status Distribution:")
        for status, count in sorted(firmware_status_summary['devices_by_status'].items()):
            print(f"   � {status}: {count} devices")
    
    print(f"\n  Version Distribution:")
    sorted_versions = sorted(firmware_status_summary['devices_by_version'].items(), 
                           key=lambda x: x[1], reverse=True)
    for version, count in sorted_versions[:10]:  # Show top 10 versions
        print(f"   � {version}: {count} devices")
    if len(sorted_versions) > 10:
        print(f"   ... and {len(sorted_versions) - 10} more versions")
    
    print(f"\n  Model Distribution:")
    sorted_models = sorted(firmware_status_summary['devices_by_model'].items(), 
                          key=lambda x: x[1], reverse=True)
    for model, count in sorted_models[:10]:  # Show top 10 models
        print(f"   � {model}: {count} devices")
    if len(sorted_models) > 10:
        print(f"   ... and {len(sorted_models) - 10} more models")
    
    # Step 5: Check for active upgrade operations
    print(f"\n  Checking for active upgrade operations...")
    active_upgrades = []
    
    # Check stored upgrade IDs from option 90
    upgrade_tracking_file = "ActiveUpgrades.json"
    stored_upgrades = []
    
    if os.path.exists(upgrade_tracking_file):
        try:
            with open(upgrade_tracking_file, 'r', encoding='utf-8') as f:
                stored_upgrades = json.load(f)
            
            if stored_upgrades:
                print(f"   Found {len(stored_upgrades)} stored upgrade operations from ActiveUpgrades.json")
                
                # Filter to current org_id
                org_upgrades = [u for u in stored_upgrades if u.get('org_id') == org_id]
                if org_upgrades:
                    print(f"   {len(org_upgrades)} upgrades match current organization")
                    
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
                                    
                                    print(f"      Upgrade {upgrade_id[:8]}... at site '{site_name}': Status = {status}")
                                    
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
                                    print(f"      Upgrade {upgrade_id[:8]}... at site '{site_name}': No longer active or not found")
                                    
                            except Exception as e:
                                print(f"      Failed to check upgrade {upgrade_id[:8]}... at site '{site_name}': {e}")
                                logging.warning(f"Failed to check stored upgrade {upgrade_id}: {e}")
                else:
                    print(f"   No stored upgrades match current organization ID")
        except Exception as e:
            print(f"   Failed to read stored upgrade tracking data: {e}")
            logging.warning(f"Failed to read stored upgrade tracking: {e}")
    else:
        print(f"   No stored upgrade tracking file found (ActiveUpgrades.json)")
    
    # Check organization audit logs for recent upgrade events
    try:
        print(f"   Searching organization audit logs for recent upgrade events...")
        
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
                print(f"      Found {len(upgrade_events)} upgrade-related audit events in last 24 hours")
                
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
                    
                    print(f"         � {event_time} | {admin_name} | {site_name}: {message}")
            else:
                print(f"      No upgrade-related events found in recent audit logs")
        else:
            print(f"      No audit logs retrieved for the last 24 hours")
            
    except Exception as e:
        print(f"   Failed to search organization audit logs: {e}")
        logging.warning(f"Failed to search org audit logs for upgrades: {e}")
    
    # Check organization-level device events for upgrade activity
    try:
        print(f"   Searching organization device events for upgrade activity...")
        
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
            print(f"      Found {len(device_events)} device upgrade events in last 24 hours")
            
            # Group events by type
            events_by_type = {}
            for event in device_events:
                event_type = event.get('type', 'Unknown')
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                events_by_type[event_type].append(event)
            
            for event_type, type_events in events_by_type.items():
                print(f"         � {event_type}: {len(type_events)} events")
                
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
            print(f"      No device upgrade events found in last 24 hours")
            
    except Exception as e:
        print(f"   Failed to search device upgrade events: {e}")
        logging.warning(f"Failed to search device upgrade events: {e}")
    
    # Check organization-level upgrades if not filtering by site (legacy approach)
    if not site_filter and not active_upgrades:
        try:
            print(f"   Note: Organization-level upgrade tracking requires specific upgrade IDs")
            print(f"        � Use the stored upgrade tracking above for ongoing operations")
            print(f"        � Or check individual sites below for comprehensive status")
        except Exception as e:
            logging.warning(f"Failed to check org-level upgrades: {e}")
    
    # Check site-level upgrades
    sites_to_check = [site_filter] if site_filter else list(site_lookup.keys())
    
    for site_id in sites_to_check[:5]:  # Limit to first 5 sites for performance
        try:
            site_name = site_lookup.get(site_id, 'Unknown')
            print(f"   Checking site '{site_name}' for active upgrades...")
            
            upgrades_resp = mistapi.api.v1.sites.devices.listSiteDeviceUpgrades(apisession, site_id)
            site_upgrades = mistapi.get_all(response=upgrades_resp, mist_session=apisession)
            
            if site_upgrades:
                print(f"      Found {len(site_upgrades)} upgrade operations")
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
                print(f"      No upgrade operations found")
                
        except Exception as e:
            print(f"      Failed to check upgrades for site {site_id}: {e}")
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
            DataExporter.save_data_to_output(upgrade_results, device_status_file)
            print(f"\n[SUCCESS] Device firmware status exported to: data/{device_status_file}")
            print(f"   [DATA] {len(upgrade_results)} device records exported")
            logging.info(f"Exported {len(upgrade_results)} device firmware status records to data/{device_status_file}")
            
        except Exception as e:
            print(f"! Failed to export device status: {e}")
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
            
            print(f"! Active upgrade operations exported to: {upgrade_ops_file}")
            print(f"   {len(active_upgrades)} upgrade operations exported")
            logging.info(f"Exported {len(active_upgrades)} active upgrade operations to {upgrade_ops_file}")
            
        except Exception as e:
            print(f"! Failed to export upgrade operations: {e}")
            logging.error(f"Failed to export upgrade operations: {e}")
    
    # Step 7: Summary and recommendations
    print(f"\n  Summary and Recommendations:")
    
    if firmware_status_summary['upgrade_failed'] > 0:
        print(f"   {firmware_status_summary['upgrade_failed']} devices have failed upgrades")
        print(f"   Check failed devices for retry eligibility or manual intervention")
    
    if firmware_status_summary['upgrade_in_progress'] > 0:
        print(f"   {firmware_status_summary['upgrade_in_progress']} devices currently upgrading")
        print(f"   Monitor progress and avoid disrupting these devices")
    
    if len(firmware_status_summary['devices_by_version']) > 3:
        print(f"   Multiple firmware versions detected ({len(firmware_status_summary['devices_by_version'])} different versions)")
        print(f"   Consider standardizing on a consistent firmware version")
    
    if active_upgrades:
        print(f"   {len(active_upgrades)} active upgrade operations found")
        print(f"   Monitor upgrade progress in exported CSV files")
    else:
        print(f"   No active upgrade operations detected")
    
    print(f"\n  Status check complete. Check exported CSV files for detailed analysis.")
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
            print(f"   Enter upgrade time (24-hour format, e.g., 02:00, 14:30):")
            time_input = input("   Time of day (default=02:00): ").strip() or "02:00"
            
            # Validate time format
            try:
                # Try to parse the time to validate format
                datetime.strptime(time_input, "%H:%M")
                time_settings["time_of_day"] = time_input
                print(f"   Upgrade time set to: {time_input}")
                break
            except ValueError:
                print(f"   Invalid time format. Please use HH:MM (24-hour format)")
                
        except KeyboardInterrupt:
            print("\n   Time configuration cancelled")
            time_settings["time_of_day"] = "02:00"  # Default fallback
            break
    
    # Day of week configuration
    print(f"\n   Select upgrade schedule:")
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
            
            print(f"   Select day of week:")
            for key, (day_value, day_name) in days.items():
                print(f"      [{key}] {day_name}")
            
            day_choice = input("   Select day (1-7): ").strip()
            if day_choice in days:
                day_value, day_name = days[day_choice]
                time_settings["day_of_week"] = day_value
                print(f"   Upgrade day set to: {day_name}")
            else:
                print(f"   Invalid selection, defaulting to every day")
                # Don't set day_of_week (None means every day)
        else:
            # Every day (don't set day_of_week)
            print(f"   Upgrade schedule: Every day at {time_settings.get('time_of_day', '02:00')}")
            
    except KeyboardInterrupt:
        print("\n   Schedule configuration cancelled, defaulting to every day")
    
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
        print(f"! Found {bulk_upgrade_file} - Loading sites for bulk upgrade...")
        logging.info(f"Found {bulk_upgrade_file} file, proceeding with bulk site upgrade")
        logging.debug(f"Bulk upgrade file path: {os.path.abspath(bulk_upgrade_file_path)}")
        
        # First, get all sites in the organization for reverse lookup
        print(f"   Fetching organization sites for name-to-ID lookup...")
        logging.debug("Fetching organization sites for name-to-ID mapping")
        try:
            all_org_sites = fetch_all_sites_with_limit(org_id)
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
            print(f"! Failed to fetch organization sites: {e}")
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
                print(f"! No site names found in {bulk_upgrade_file}")
                logging.error(f"No site names found in {bulk_upgrade_file}")
                return
            
            print(f"   Read {len(site_names)} site names from file")
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
                print(f"   Warning: {len(missing_sites)} site(s) not found in organization:")
                for missing_site in missing_sites:
                    print(f"      � '{missing_site}'")
                print(f"   Available sites in organization:")
                available_names = sorted(site_name_to_id.keys())
                for name in available_names[:10]:  # Show first 10 as examples
                    print(f"      � '{name}'")
                if len(available_names) > 10:
                    print(f"      ... and {len(available_names) - 10} more")
                    
            if not sites_to_upgrade:
                print(f"! No valid sites found - none of the names in {bulk_upgrade_file} match organization sites")
                logging.error(f"No valid sites found in {bulk_upgrade_file}")
                return
            
            print(f"! Successfully resolved {len(sites_to_upgrade)} site(s) for bulk upgrade:")
            for site in sites_to_upgrade:
                print(f"   � {site['name']} (ID: {site['id']})")
            
            logging.info(f"Resolved {len(sites_to_upgrade)} sites for bulk upgrade from {bulk_upgrade_file}")
            
        except Exception as e:
            print(f"! Failed to read {bulk_upgrade_file}: {e}")
            logging.error(f"Failed to read {bulk_upgrade_file}: {e}")
            return
    else:
        print(f"! {bulk_upgrade_file} not found - Single site mode")
        print(f"   To enable bulk upgrade mode, create '{bulk_upgrade_file}' in the data/ folder")
        print(f"   File format: one site name per line (no header)")
        logging.info(f"{bulk_upgrade_file} not found, proceeding with single site selection")
        
        # Single site selection (existing behavior)
        site_id = prompt_site_selection()
        if not site_id:
            logging.error("No site selected. Exiting.")
            print(" No site selected. Exiting.")
            return
        
        # Get site name for display
        try:
            sites = fetch_all_sites_with_limit(org_id)
            site_name = next((site["name"] for site in sites if site.get("id") == site_id), site_id)
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
    
    print(f"\n  Fetching APs across {len(sites_to_upgrade)} site(s)...")
    logging.debug(f"Starting AP discovery across {len(sites_to_upgrade)} sites")
    
    for site_info in sites_to_upgrade:
        site_id = site_info['id']
        site_name = site_info['name']
        
        try:
            print(f"   Fetching APs at site '{site_name}'...")
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
                
                print(f"      Found {len(site_aps)} APs at '{site_name}'")
                logging.info(f"Found {len(site_aps)} APs at site {site_name} (ID: {site_id})")
                logging.debug(f"AP models at {site_name}: {list(set(ap.get('model', 'Unknown') for ap in site_aps))}")
            else:
                print(f"      No APs found at site '{site_name}'")
                logging.warning(f"No APs found at site {site_name} (ID: {site_id})")
                all_sites_aps[site_id] = {
                    'name': site_name,
                    'aps': [],
                    'count': 0
                }
                
        except Exception as e:
            print(f"      Failed to fetch APs for site '{site_name}': {e}")
            logging.error(f"Failed to fetch APs for site {site_id} ({site_name}): {e}")
            all_sites_aps[site_id] = {
                'name': site_name,
                'aps': [],
                'count': 0,
                'error': str(e)
            }
    
    if not all_aps:
        print(" No APs found across any selected sites.")
        logging.warning("No APs found across any selected sites")
        return
    
    total_aps = len(all_aps)
    sites_with_aps = len([s for s in all_sites_aps.values() if s['count'] > 0])
    
    print(f"\n  AP Discovery Summary:")
    print(f"   � Total APs found: {total_aps}")
    print(f"   � Sites with APs: {sites_with_aps}/{len(sites_to_upgrade)}")
    
    for site_id, site_data in all_sites_aps.items():
        site_name = site_data['name']
        ap_count = site_data['count']
        if 'error' in site_data:
            print(f"   � {site_name}: {ap_count} APs (Error: {site_data['error']})")
        else:
            print(f"   � {site_name}: {ap_count} APs")
    
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
    
    print(f"\n  Getting current firmware versions from device statistics...")
    
    # For multi-site upgrades, we need to fetch stats per site
    all_ap_stats = []
    stats_lookup = {}
    
    for site_id, site_data in all_sites_aps.items():
        if site_data['count'] == 0:
            continue  # Skip sites with no APs
            
        site_name = site_data['name']
        site_aps = site_data['aps']
        
        print(f"   Fetching device statistics for {len(site_aps)} APs at '{site_name}'...")
        
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
            print(f"   Failed to fetch stats for site '{site_name}': {e}")
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
        print(f"   No device statistics retrieved - falling back to individual calls")
    
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
    
    print(f"   Retrieved {bulk_stats_count} device versions via bulk API call")
    if individual_calls_needed > 0:
        print(f"   {individual_calls_needed} devices required individual calls")
    
    logging.info(f"API optimization: {bulk_stats_count} versions from bulk call, {individual_calls_needed} individual calls needed")
    
    print(f"\n  AP Models found across {len(sites_to_upgrade)} site(s):")
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
            print(f"   � {model}: {len(devices)} devices (Current versions: {versions_text})")
        else:
            print(f"   � {model}: {len(devices)} devices (Current versions: Unknown)")
            
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
                print(f"      {site_name} ({len(site_devices)} devices):")
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
    print(f"\n  Fetching available firmware versions...")
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
        print(f"! Failed to fetch available firmware versions: {e}")
        return
    
    # Step 5: Let user select firmware version for each model
    upgrade_plan = {}
    print(f"\n  Firmware Version Selection:")
    print("=" * 60)
    
    # Show current version summary across all APs
    print(f"! Current Firmware Status Summary:")
    all_current_versions = {}
    for model, devices in aps_by_model.items():
        for device in devices:
            device_id = device.get("id")
            version = ap_versions.get(device_id, "Unknown")
            
            if version not in all_current_versions:
                all_current_versions[version] = []
            all_current_versions[version].append(f"{device.get('name', 'Unnamed')} ({model})")
    
    for version, device_list in sorted(all_current_versions.items(), reverse=True):
        print(f"   Version {version}: {len(device_list)} devices")
        for device_info in device_list:
            print(f"      � {device_info}")
    print()
    
    # Show summary of what was found
    if available_versions:
        total_raw_versions = len(available_versions) if isinstance(available_versions, list) else 0
        print(f"! Found {total_raw_versions} firmware entries from API")
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
            print(f"!  Models without specific firmware versions: {', '.join(sorted(missing_models))}")
        
        # Analyze version compatibility across models using API data
        if len(matching_models) > 1:
            print(f"\n  Version Compatibility Analysis (API-based):")
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
                
                print(f"   Cross-compatible versions (work with multiple models):")
                for version, compatible_models in sorted_by_compatibility[:10]:  # Show top 10
                    model_list = ", ".join(sorted(compatible_models))
                    coverage = f"{len(compatible_models)}/{len(matching_models)}"
                    if len(compatible_models) == len(matching_models):
                        print(f"      {version}: ALL models ({model_list}) - UNIVERSAL")
                    elif len(compatible_models) >= len(matching_models) * 0.7:  # 70%+ coverage
                        print(f"      {version}: {coverage} models ({model_list}) - HIGH COMPATIBILITY")
                    else:
                        print(f"      {version}: {coverage} models ({model_list})")
                
                # Highlight universal versions
                universal_versions = [v for v, models in version_compatibility.items() if len(models) == len(matching_models)]
                if universal_versions:
                    sorted_universal = sorted(universal_versions, key=lambda x: tuple(map(int, x.split("."))) if x.replace(".", "").isdigit() else (0,), reverse=True)
                    print(f"\n   UNIVERSAL versions (compatible with ALL {len(matching_models)} models):")
                    print(f"      {', '.join(sorted_universal[:5])}{' ...' if len(sorted_universal) > 5 else ''}")
                    print(f"   Recommendation: Use universal version for simplified management")
                    logging.info(f"Found {len(universal_versions)} universal versions across all models")
                else:
                    print(f"\n    NO universal versions found - mixed-version upgrade required")
                    print(f"   Recommendation: Select optimal version per model based on compatibility matrix above")
                    logging.warning("No universal firmware versions found across all AP models")
            else:
                print(f"    NO cross-compatible versions found - each model has unique firmware options")
                logging.warning("No cross-compatible versions found between models")
            
            # Show model-specific version counts for context
            print(f"\n   Model-specific firmware availability:")
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
                    
                    print(f"      � {model}: {len(versions)} versions ({range_text})")
        
        elif len(matching_models) == 1:
            model = list(matching_models)[0]
            print(f"\n  Single model environment: {model}")
            if model in model_version_ranges:
                versions = model_version_ranges[model]
                print(f"   {len(versions)} firmware versions available for {model}")
            else:
                print(f"    No specific firmware versions found for {model}")
    
    
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
            print(f"!  No firmware versions found for model '{model}' - skipping {len(devices)} devices")
            print(f"   (This model may not have specific firmware versions listed, or no updates available)")
            logging.warning(f"No firmware versions found for model {model} - checked {len(raw_model_versions)} entries before deduplication")
            continue
        
        logging.debug(f"Model {model}: Found {len(raw_model_versions)} raw entries, {len(model_versions)} unique versions after deduplication")
        
        print(f"\n  Model: {model} ({len(devices)} devices)")
        
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
                    print(f"   Note: Different models may support different version ranges")
        
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
                print(f"   UNIVERSAL versions work with all models: {', '.join(universal_versions[:3])}")
            else:
                high_compat_versions = [v for v, models in cross_compatibility.items() if len(models) >= len(other_models) * 0.7]
                if high_compat_versions:
                    print(f"   HIGH COMPATIBILITY versions work with most models: {', '.join(high_compat_versions[:3])}")
        
        print()  # Add blank line for readability
        
        # Get user selection
        while True:
            try:
                user_input = input(f"Select firmware version for {model} (0-{len(model_versions)-1}, or 's' to skip): ").strip().lower()
                
                if user_input == 's':
                    print(f"!  Skipping firmware upgrade for {model}")
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
                    print(f"! Selected version {version_num} for {model}{notes_text}")
                    logging.info(f"User selected firmware version {version_num} for model {model} (recommended: {is_recommended}, current: {is_current})")
                    break
                else:
                    print(f"! Invalid selection. Please enter a number between 0 and {len(model_versions)-1}, or 's' to skip.")
                    
            except ValueError:
                print(" Invalid input. Please enter a number or 's' to skip.")
            except KeyboardInterrupt:
                print("\n Operation cancelled by user.")
                logging.info("Bulk AP firmware upgrade cancelled by user interrupt")
                return
    
    if not upgrade_plan:
        print(" No firmware upgrades selected. Exiting.")
        logging.info("No firmware upgrades selected by user")
        return
    
    # Step 5.5: Upgrade Plan Summary and Compatibility Validation
    print(f"\n  Upgrade Plan Summary:")
    print("=" * 60)
    
    total_devices_to_upgrade = 0
    selected_versions = set()
    models_in_plan = list(upgrade_plan.keys())
    
    for model, plan_info in upgrade_plan.items():
        version = plan_info["version"]
        device_count = len(plan_info["devices"])
        total_devices_to_upgrade += device_count
        selected_versions.add(version)
        
        print(f"   {model}: {device_count} devices firmware {version}")
    
    print(f"\n  Summary:")
    print(f"   � Total models: {len(upgrade_plan)}")
    print(f"   � Total devices: {total_devices_to_upgrade}")
    print(f"   � Firmware versions: {len(selected_versions)}")
    
    # Highlight coordination considerations for mixed-version upgrades
    if len(selected_versions) > 1:
        sorted_versions = sorted(selected_versions, key=lambda x: tuple(map(int, x.split("."))) if x.replace(".", "").isdigit() else (0,), reverse=True)
        print(f"\n   Multi-Version Upgrade Detected:")
        print(f"   Versions selected: {', '.join(sorted_versions)}")
        
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
                print(f"   Analysis: Version(s) {', '.join(could_be_universal)} could work with ALL models")
                print(f"   Consider: You chose model-specific versions despite universal options available")
                print(f"      This may be optimal for performance/features per model")
            else:
                print(f"   Analysis: No single version compatible with all selected models")
                print(f"   Multi-version upgrade is necessary due to model firmware constraints")
        
        print(f"\n   Coordination considerations:")
        print(f"      � Each model will upgrade to its optimal version")
        print(f"      � Network features may vary between firmware versions")
        print(f"      � Monitor compatibility for shared network functions")
        print(f"      � Consider upgrade timing to minimize impact")
        
        logging.info(f"Multi-version upgrade plan: {len(selected_versions)} different versions across {len(models_in_plan)} models")
        
        # Ask user for confirmation on mixed-version upgrade
        print(f"\n  Proceed with multi-version upgrade plan?")
        confirm_mixed = input("   Continue? (y/n, default=y): ").strip().lower() or "y"
        if confirm_mixed not in ['y', 'yes']:
            print(" Mixed-version upgrade cancelled by user.")
            logging.info("Mixed-version upgrade cancelled by user")
            return
        else:
            print(" Multi-version upgrade plan confirmed.")
    else:
        single_version = list(selected_versions)[0]
        print(f"\n Single-Version Upgrade:")
        print(f"   All {len(models_in_plan)} model(s) will upgrade to firmware {single_version}")
        
        # Analyze if this version is truly universal or if users just happened to select the same version
        if len(models_in_plan) > 1 and 'model_version_ranges' in locals():
            universal_compatibility = True
            for model in models_in_plan:
                if model not in model_version_ranges or single_version not in model_version_ranges[model]:
                    universal_compatibility = False
                    break
            
            if universal_compatibility:
                print(f"   Excellent choice: {single_version} is UNIVERSAL (compatible with all models)")
                print(f"   Unified firmware version simplifies management and ensures feature consistency")
            else:
                print(f"    Note: Selected version may not be verified as compatible with all models")
                print(f"   Proceed with caution and monitor compatibility during upgrade")
        else:
            print(f"   Consistent firmware version across all AP models")
        
        logging.info(f"Single-version upgrade plan: all models upgrading to {single_version}")
    
    print(f"\n  Ready to proceed with advanced configuration...")
    logging.info(f"Upgrade plan validated: {total_devices_to_upgrade} devices across {len(models_in_plan)} models")
    
    # Step 6: Advanced Configuration Options
    print(f"\n  Advanced Upgrade Configuration:")
    print("=" * 60)
    
    # Select upgrade strategy
    strategies = {
        "1": ("big_bang", "Upgrade all devices at once (fastest, higher risk)"),
        "2": ("canary", "Phased rollout with configurable phases (safer, slower)"),
        "3": ("rrm", "Radio Resource Management aware upgrade (AP-only, intelligent)"),
        "4": ("serial", "One device at a time (safest, slowest)")
    }
    
    print(" Select upgrade strategy:")
    for key, (strategy, description) in strategies.items():
        print(f"   [{key}] {strategy.upper()}: {description}")
    
    while True:
        try:
            strategy_choice = input("Select strategy (1-4, default=3 for rrm): ").strip() or "3"
            if strategy_choice in strategies:
                selected_strategy, strategy_desc = strategies[strategy_choice]
                print(f"! Selected strategy: {selected_strategy.upper()}")
                logging.info(f"User selected upgrade strategy: {selected_strategy}")
                break
            else:
                print(" Invalid selection. Please choose 1-4.")
        except KeyboardInterrupt:
            print("\n Operation cancelled by user.")
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
        print(f"\n  Canary Strategy Configuration:")
        
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
                            print(f"! Custom phases: {phases}")
                            break
                        else:
                            print(" Phases must be 1-100 and end with 100")
                    else:
                        break
                except ValueError:
                    print(" Invalid format. Use comma-separated numbers.")
        
        # Failure threshold
        try:
            failure_input = input(f"Max failure percentage per phase (default={upgrade_config['max_failure_percentage']}%): ").strip()
            if failure_input:
                failure_pct = int(failure_input)
                if 0 <= failure_pct <= 100:
                    upgrade_config["max_failure_percentage"] = failure_pct
                    print(f"! Max failures: {failure_pct}%")
        except ValueError:
            print(" Invalid input, using default failure threshold")
    
    elif selected_strategy == "rrm":
        print(f"\n  RRM Strategy Configuration:")
        
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
            print(f"! Node order: {node_orders[order_choice][1]}")
        
        # Batch size configuration
        try:
            first_batch = input(f"First batch percentage (default={rrm_options['rrm_first_batch_percentage']}%): ").strip()
            if first_batch:
                rrm_options["rrm_first_batch_percentage"] = int(first_batch)
            
            max_batch = input(f"Max batch percentage (default={rrm_options['rrm_max_batch_percentage']}%): ").strip()
            if max_batch:
                rrm_options["rrm_max_batch_percentage"] = int(max_batch)
        except ValueError:
            print(" Invalid input, using default batch sizes")
        
        upgrade_config.update(rrm_options)
    
    # P2P Configuration (all strategies)
    print(f"\n  Peer-to-Peer (P2P) Configuration:")
    enable_p2p = input("Enable AP-to-AP firmware sharing? (Y/n): ").strip().lower()
    if enable_p2p not in ['n', 'no']:
        upgrade_config["enable_p2p"] = True
        print(" P2P enabled - APs will share firmware locally")
        
        try:
            cluster_size = input(f"P2P cluster size (default={upgrade_config['p2p_cluster_size']}): ").strip()
            if cluster_size:
                upgrade_config["p2p_cluster_size"] = int(cluster_size)
                print(f"! P2P cluster size: {upgrade_config['p2p_cluster_size']}")
        except ValueError:
            print(" Invalid input, using default cluster size")
    else:
        print(" P2P disabled - all firmware downloads from cloud")
    
    # Scheduling Options
    print(f"\n  Scheduling Options:")
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
                    print(f"! Scheduled for: {scheduled_time}")
                    break
                else:
                    # Absolute time
                    dt = datetime.strptime(time_input, '%Y-%m-%d %H:%M')
                    start_time = int(dt.timestamp())
                    upgrade_config["start_time"] = start_time
                    print(f"! Scheduled for: {time_input}")
                    break
            except ValueError:
                print(" Invalid format. Use 'YYYY-MM-DD HH:MM' or '+minutes'")
                retry = input("Try again? (y/N): ").strip().lower()
                if retry not in ['y', 'yes']:
                    break
    
    # Force upgrade option
    force_upgrade = input("Force upgrade even if same version? (y/N): ").strip().lower()
    if force_upgrade in ['y', 'yes']:
        upgrade_config["force"] = True
        print(" Force upgrade enabled")
    
    # Display final configuration
    print(f"\n  Final Upgrade Configuration:")
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
    print(f"\n  Final Firmware Upgrade Plan:")
    print("=" * 60)
    
    if len(sites_to_upgrade) > 1:
        print(f"Bulk Upgrade Mode: {len(sites_to_upgrade)} sites")
        for site_info in sites_to_upgrade:
            site_count = sum(1 for plan in upgrade_plan.values() 
                           for device in plan["devices"] 
                           if device.get("_site_id") == site_info['id'])
            print(f"   � {site_info['name']}: {site_count} devices")
    else:
        print(f"Site: {sites_to_upgrade[0]['name']}")
    
    print(f"Total devices to upgrade: {total_devices}")
    print(f"Upgrade strategy: {upgrade_config['strategy'].upper()}")
    
    for model, plan in upgrade_plan.items():
        version = plan["version"]
        devices = plan["devices"]
        print(f"\n  {model} Firmware {version} ({len(devices)} devices):")
        
        if len(sites_to_upgrade) > 1:
            # Group devices by site for multi-site display
            devices_by_site = {}
            for device in devices:
                site_name = device.get("_site_name", "Unknown Site")
                if site_name not in devices_by_site:
                    devices_by_site[site_name] = []
                devices_by_site[site_name].append(device)
            
            for site_name, site_devices in devices_by_site.items():
                print(f"   {site_name} ({len(site_devices)} devices):")
                for device in site_devices:
                    device_name = device.get("name", "Unnamed")
                    mac = device.get("mac", "Unknown")
                    device_id = device.get("id")
                    current_version = ap_versions.get(device_id, "Unknown")
                    print(f"      � {device_name} (MAC: {mac}) - Current: {current_version}")
        else:
            # Single site display
            for device in devices:
                device_name = device.get("name", "Unnamed")
                mac = device.get("mac", "Unknown")
                device_id = device.get("id")
                current_version = ap_versions.get(device_id, "Unknown")
                print(f"   � {device_name} (MAC: {mac}) - Current: {current_version}")
    
    # Step 8: Display warnings and get user confirmation
    warning_lines = [
        " CRITICAL WARNING - ADVANCED FIRMWARE UPGRADE OPERATION:",
        "� This action will UPGRADE FIRMWARE on Access Point devices",
        "� APs will REBOOT during the upgrade process",
        "� Wi-Fi connectivity will be TEMPORARILY LOST during upgrades", 
        "� Users will experience Wi-Fi service interruptions",
        "� Firmware upgrades can take 5-15 minutes per device",
        "� Failed upgrades may require manual recovery",
        "� This is a DISRUPTIVE network operation",
        "� Always ensure you have physical access to devices if recovery is needed",
        f"� Upgrade strategy: {upgrade_config['strategy'].upper()}",
        f"� Max failure tolerance: {upgrade_config['max_failure_percentage']}%",
        "� P2P enabled: " + ("Yes" if upgrade_config['enable_p2p'] else "No"),
        "� The script owner bears NO LIABILITY for any consequences",
        "� Proceed only if you understand and accept these risks"
    ]
    
    print("\n" + "??" * 50)
    for line in warning_lines:
        print(line)
    print("??" * 50)
    
    print(f"\n  Summary:")
    if len(sites_to_upgrade) > 1:
        print(f"   � Bulk upgrade across {len(sites_to_upgrade)} sites")
        sites_with_devices = len(set(device.get("_site_name") for plan in upgrade_plan.values() for device in plan["devices"]))
        print(f"   � Sites with devices to upgrade: {sites_with_devices}")
    else:
        print(f"   � Site: {sites_to_upgrade[0]['name']}")
    print(f"   � Total APs to upgrade: {total_devices}")
    print(f"   � Models affected: {len(upgrade_plan)}")
    print(f"   � Strategy: {upgrade_config['strategy'].upper()}")
    
    # Show target firmware versions for each model
    print(f"   � Target firmware versions:")
    for model, plan in upgrade_plan.items():
        version = plan["version"]
        device_count = len(plan["devices"])
        print(f"      - {model}: v{version} ({device_count} devices)")
    
    if upgrade_config.get('start_time'):
        scheduled_time = datetime.fromtimestamp(upgrade_config['start_time']).strftime('%Y-%m-%d %H:%M')
        print(f"   � Scheduled: {scheduled_time}")
    else:
        print(f"   � Scheduled: Immediate")
    
    # Get user confirmation with liability waiver
    print(f"\n  Do you want to proceed with upgrading {total_devices} AP devices?")
    print("   Type 'UPGRADE' (all caps) to confirm, or anything else to cancel:")
    print("   By typing 'UPGRADE', you acknowledge and accept all risks and liability.")
    
    try:
        user_input = input(">>> ").strip()
        if user_input != "UPGRADE":
            print(" Advanced firmware upgrade operation cancelled by user.")
            logging.info("Advanced AP firmware upgrade operation cancelled by user input")
            return
        else:
            print(" User confirmed advanced firmware upgrade operation. Proceeding...")
            logging.info(f"! LIABILITY WAIVER ACCEPTED: User confirmed advanced AP firmware upgrade for {total_devices} devices at site {site_name}")
            logging.info(f"User input: '{user_input}' - User accepts full responsibility for firmware upgrade risks")
            logging.info(f"Upgrade strategy: {upgrade_config['strategy']}, P2P: {upgrade_config['enable_p2p']}, Max failures: {upgrade_config['max_failure_percentage']}%")
            # Log detailed upgrade plan for audit trail
            plan_summary = []
            for model, plan in upgrade_plan.items():
                plan_summary.append(f"{model}?{plan['version']} ({len(plan['devices'])} devices)")
            logging.info(f"Upgrade plan: {'; '.join(plan_summary)}")
            
    except KeyboardInterrupt:
        print("\n Firmware upgrade operation cancelled by user (Ctrl+C).")
        logging.info("AP firmware upgrade operation cancelled by user interrupt")
        return
    except Exception as e:
        print(f"! Error getting user input: {e}")
        logging.error(f"Error getting user input for upgrade confirmation: {e}")
        return
    
    # Step 9: Execute advanced firmware upgrades
    print("\n  Starting advanced AP firmware upgrade operations...")
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
        logging.debug(f"Processing {len(devices)} devices for model {model} firmware {version}")
        
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
    
    print(f"\n  Executing upgrades across {total_sites_to_upgrade} site(s) with {total_devices} devices...")
    
    for site_index, (site_id, site_data) in enumerate(devices_by_site.items(), 1):
        site_name = site_data['name']
        site_devices = site_data['devices']
        site_models = site_data['models']
        
        logging.debug(f"Starting upgrade execution for site {site_index}/{total_sites_to_upgrade}: {site_name}")
        print(f"\n   Site {site_index}/{total_sites_to_upgrade}: {site_name} ({len(site_devices)} devices)")
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
                print(f"      Upgrading all devices to version {target_version}...")
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
                        print(f"      Upgrade initiated - ID: {upgrade_id}")
                    else:
                        logging.debug(f"Upgrade initiated without specific upgrade ID")
                        print(f"      Upgrade command sent successfully")
                else:
                    logging.warning(f"Upgrade response missing data for site {site_name}")
                
                successful_upgrades += len(site_devices)
                logging.info(f"! Site {site_name} upgrade initiated for {len(site_devices)} devices")
                
            else:
                # Multiple versions for this site - separate calls per model
                print(f"      Multiple firmware versions for site - executing per model...")
                
                for model, model_info in site_models.items():
                    model_version = model_info['version']
                    model_devices = model_info['devices']
                    model_device_ids = [device.get("id") for device in model_devices if device.get("id")]
                    
                    print(f"         � {model}: {len(model_devices)} devices v{model_version}")
                    
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
                            print(f"            {model} upgrade initiated - ID: {model_upgrade_id}")
                        else:
                            logging.debug(f"Per-model upgrade initiated for {model} without specific upgrade ID")
                            print(f"            {model} upgrade command sent")
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
            print(f"      Failed to initiate upgrade for site {site_name}: {e}")
            logging.error(f"! Failed to initiate upgrade for site {site_name}: {e}")
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
    print(f"\n  Configuring site auto-upgrade settings...")
    
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
                print(f"   Configuring site auto-upgrade settings...")
                
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
                        print(f"   Current auto-upgrade settings:")
                        print(f"      � Enabled: Yes")
                        print(f"      � Version: {current_auto_upgrade.get('version', 'Not set')}")
                        print(f"      � Time of day: {current_auto_upgrade.get('time_of_day', 'Not set')}")
                        day_of_week = current_auto_upgrade.get('day_of_week')
                        if day_of_week:
                            print(f"      � Day of week: {day_of_week}")
                        else:
                            print(f"      � Day of week: Every day")
                    else:
                        logging.debug(f"Auto-upgrade currently disabled or not configured for site {site_name}")
                        print(f"   Current auto-upgrade: Disabled or not configured")
                        
                except Exception as e:
                    logging.warning(f"Could not retrieve current site settings: {e}")
                    print(f"   Could not retrieve current settings: {e}")
                
                # Auto-upgrade configuration options
                logging.debug(f"Presenting auto-upgrade configuration options for target version {target_version}")
                print(f"\n   Auto-upgrade configuration options:")
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
                    print(f"   Auto-upgrade will be disabled")
                elif config_choice == "3":
                    # Skip configuration
                    logging.debug(f"Skipping auto-upgrade configuration for site {site_name}")
                    print("   Skipping site auto-upgrade configuration")
                    logging.info("User chose to skip site auto-upgrade configuration")
                    # Continue without configuring auto-upgrade
                    pass
                else:
                    # Enable auto-upgrade (option 1 or fallback)
                    logging.debug(f"Enabling comprehensive auto-upgrade for site {site_name} with target version {target_version}")
                    print(f"   Configuring comprehensive auto-upgrade settings...")
                    print(f"   This ensures all AP models get appropriate firmware automatically")
                    
                    # Build custom_versions dictionary starting with models from the upgrade plan
                    custom_versions = {}
                    models_in_upgrade_plan = set(upgrade_plan.keys())
                    logging.debug(f"Models in upgrade plan: {models_in_upgrade_plan}")
                    
                    # Get all models from the upgrade plan and set their target versions
                    for model, plan in upgrade_plan.items():
                        model_version = plan["version"]
                        custom_versions[model] = model_version
                        logging.debug(f"Setting custom version for {model}: {model_version}")
                        print(f"      {model}: {model_version} (from upgrade plan)")
                    
                    logging.debug(f"Starting AP model family analysis for comprehensive auto-upgrade coverage")
                    print(f"\n   Analyzing all available AP models for comprehensive auto-upgrade coverage...")
                    
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
                        print(f"\n   Found {len(models_not_in_plan)} additional AP models available for auto-upgrade:")
                        
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
                                print(f"      � AP Family {family_count}: {', '.join(sorted(models))} ({len(signature)} firmware versions)")
                            else:
                                print(f"      � {models[0]} ({len(signature)} firmware versions)")
                        
                        print(f"\n   Configure auto-upgrade for additional models:")
                        print(f"   Models with identical firmware versions are grouped together as families.")
                        print(f"   This ensures new APs of ANY model will auto-upgrade to appropriate firmware.")
                        
                        configure_additional = input(f"   Configure auto-upgrade for additional models? (Y/n): ").strip().lower()
                        logging.debug(f"User choice for additional model configuration: '{configure_additional}'")
                        
                        if configure_additional not in ['n', 'no']:
                            logging.debug(f"Proceeding with firmware version selection for {len(model_families)} model families")
                            print(f"\n   Selecting firmware versions for additional model families...")
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
                                    print(f"      No firmware versions found for model family {models}")
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
                                    print(f"\n      AP Family {family_idx}: {', '.join(sorted(models))}")
                                    print(f"         These models share identical firmware version compatibility")
                                else:
                                    print(f"\n      Model: {models[0]}")
                                    
                                print(f"         Available major revisions with highest versions:")
                                
                                # Display options for this family
                                major_options = {}
                                for idx, (major_minor, highest_version) in enumerate(sorted(highest_per_major.items()), 1):
                                    print(f"            [{idx}] {major_minor}.x {highest_version}")
                                    major_options[str(idx)] = highest_version
                                
                                print(f"            [s] Skip this family")
                                
                                # Get user selection for the entire family
                                while True:
                                    try:
                                        family_name = f"Family {family_idx}" if len(models) > 1 else models[0]
                                        user_choice = input(f"         Select firmware for {family_name} (1-{len(major_options)}, s): ").strip().lower()
                                        
                                        if user_choice == 's':
                                            print(f"         Skipping {family_name}")
                                            break
                                        elif user_choice in major_options:
                                            selected_version = major_options[user_choice]
                                            # Apply the selected version to all models in this family
                                            for model in models:
                                                custom_versions[model] = selected_version
                                            print(f"         {family_name} firmware {selected_version}")
                                            print(f"            Applied to: {', '.join(sorted(models))}")
                                            break
                                        else:
                                            print(f"         Invalid selection. Please choose 1-{len(major_options)} or 's'.")
                                    except KeyboardInterrupt:
                                        print("\n         Configuration cancelled.")
                                        break
                    
                    # Validate that we have comprehensive model coverage
                    total_models_configured = len(custom_versions)
                    models_from_plan = len(models_in_upgrade_plan)
                    models_additionally_configured = total_models_configured - models_from_plan
                    
                    print(f"\n   Auto-upgrade coverage summary:")
                    print(f"      � Models from upgrade plan: {models_from_plan}")
                    print(f"      � Additional models configured: {models_additionally_configured}")
                    print(f"      � Total models configured: {total_models_configured}")
                    
                    if total_models_configured > 0:
                        print(f"\n   Complete auto-upgrade model configuration:")
                        for model, version in sorted(custom_versions.items()):
                            status = "from upgrade plan" if model in models_in_upgrade_plan else "additional coverage"
                            print(f"      � {model} firmware {version} ({status})")

                    new_auto_upgrade = {
                        "enabled": True,
                        "version": "custom",  # Use "custom" to indicate custom_versions are in use
                        "custom_versions": custom_versions
                    }
                    
                    # Time scheduling configuration
                    print(f"\n   Auto-upgrade time scheduling:")
                    
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
                            print(f"   Maintaining current schedule: {current_schedule}")
                        else:
                            # Configure new time settings
                            print(f"   Configure new auto-upgrade schedule:")
                            new_auto_upgrade.update(get_auto_upgrade_time_settings())
                    else:
                        # No current time settings, get new ones
                        print(f"   Configure auto-upgrade schedule:")
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
                        print(f"   Site auto-upgrade configured successfully")
                        custom_versions = new_auto_upgrade.get("custom_versions", {})
                        if custom_versions:
                            logging.debug(f"Auto-upgrade configured with {len(custom_versions)} custom model versions")
                            print(f"   New/replacement APs will auto-upgrade per model:")
                            for model, version in custom_versions.items():
                                print(f"      � {model}: {version}")
                            
                            # Log with model details
                            version_summary = ", ".join([f"{m}:{v}" for m, v in custom_versions.items()])
                            logging.info(f"Site auto-upgrade configured: site={site_id}, custom_versions={version_summary}")
                        else:
                            logging.debug(f"Auto-upgrade configured with standard version {target_version}")
                            print(f"   New/replacement APs will auto-upgrade to configured version")
                            logging.info(f"Site auto-upgrade configured: site={site_id}")
                    else:
                        logging.info(f"Site auto-upgrade disabled for {site_name}")
                        print(f"   Site auto-upgrade disabled successfully")
                        print(f"   New/replacement APs will NOT auto-upgrade")
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
                print(f"   {error_msg}")
                logging.error(f"! {error_msg}")
                
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
            print("   Skipping site auto-upgrade configuration")
            logging.info("User chose to skip site auto-upgrade configuration")
    
    else:
        # Multiple versions - need careful auto-upgrade configuration
        print(f"   Multiple firmware versions in upgrade plan:")
        for version in sorted(target_versions):
            models_with_version = [model for model, plan in upgrade_plan.items() if plan["version"] == version]
            print(f"      � Version {version}: {', '.join(models_with_version)}")
        
        print(f"\n   Auto-Upgrade Configuration for Mixed-Model Environment:")
        print(f"   Site auto-upgrade must handle different AP models with different firmware capabilities.")
        
        # Analyze what models exist in the upgrade plan
        all_models_in_plan = set(upgrade_plan.keys())
        print(f"\n   AP Models in this upgrade plan: {', '.join(sorted(all_models_in_plan))}")
        
        # Provide enhanced options for mixed-model auto-upgrade
        print(f"\n   Auto-upgrade options for mixed-model environment:")
        print(f"      [1] Configure custom versions per model (RECOMMENDED)")
        print(f"         � Each AP model gets its optimal firmware version")
        print(f"         � New APs will auto-upgrade to model-appropriate firmware")
        print(f"         � Handles model compatibility constraints automatically")
        print(f"      [2] Disable auto-upgrade")
        print(f"         � Manual firmware management required for new APs")
        print(f"         � Prevents version conflicts but requires more maintenance")
        print(f"      [3] Skip auto-upgrade configuration")
        print(f"         � Leave current auto-upgrade settings unchanged")
        
        auto_upgrade_choice = input("   Select auto-upgrade option (1-3, default=1): ").strip() or "1"
        
        try:
            if auto_upgrade_choice == "3":
                print("   Skipping site auto-upgrade configuration")
                logging.info("User chose to skip site auto-upgrade configuration for multi-version upgrade")
                
            elif auto_upgrade_choice == "2":
                # Disable auto-upgrade
                print(f"   Disabling site auto-upgrade...")
                
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
                
                print(f"   Site auto-upgrade disabled successfully")
                print(f"   New/replacement APs will NOT auto-upgrade")
                print(f"   Manual firmware management will be required for new devices")
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
                print(f"   Configuring model-specific auto-upgrade versions...")
                print(f"   This ensures each AP model gets compatible firmware automatically")
                
                # Build custom_versions dictionary starting with models from the upgrade plan
                custom_versions = {}
                models_in_upgrade_plan = set(upgrade_plan.keys())
                
                for model, plan in upgrade_plan.items():
                    model_version = plan["version"]
                    custom_versions[model] = model_version
                    print(f"      {model} firmware {model_version} (from upgrade plan)")
                
                print(f"\n   Analyzing all available AP models for comprehensive auto-upgrade coverage...")
                
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
                    print(f"\n   Found {len(models_not_in_plan)} additional AP models available for auto-upgrade:")
                    
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
                            print(f"      � AP Family {family_count}: {', '.join(sorted(models))} ({len(signature)} firmware versions)")
                        else:
                            print(f"      � {models[0]} ({len(signature)} firmware versions)")
                    
                    print(f"\n   Configure auto-upgrade for additional models:")
                    print(f"   Models with identical firmware versions are grouped together as families.")
                    print(f"   This ensures new APs of ANY model will auto-upgrade to appropriate firmware.")
                    
                    configure_additional = input(f"   Configure auto-upgrade for additional models? (Y/n): ").strip().lower()
                    
                    if configure_additional not in ['n', 'no']:
                        print(f"\n   Selecting firmware versions for additional model families...")
                        print(f"   Strategy: Highest version per major revision (e.g., highest 0.12.x, highest 0.14.x)")
                        
                        # Process each family group
                        for family_idx, (signature, models) in enumerate(model_families.items(), 1):
                            if not models:  # Skip empty groups
                                continue
                                
                            # Get firmware versions for this family (all models have the same versions)
                            representative_model = models[0]
                            if representative_model not in model_version_ranges:
                                print(f"      No firmware versions found for model family {models}")
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
                                print(f"\n      AP Family {family_idx}: {', '.join(sorted(models))}")
                                print(f"         These models share identical firmware version compatibility")
                            else:
                                print(f"\n      Model: {models[0]}")
                                
                            print(f"         Available major revisions with highest versions:")
                            
                            # Display options for this family
                            major_options = {}
                            for idx, (major_minor, highest_version) in enumerate(sorted(highest_per_major.items()), 1):
                                print(f"            [{idx}] {major_minor}.x {highest_version}")
                                major_options[str(idx)] = highest_version
                            
                            print(f"            [s] Skip this family")
                            
                            # Get user selection for the entire family
                            while True:
                                try:
                                    family_name = f"Family {family_idx}" if len(models) > 1 else models[0]
                                    user_choice = input(f"         Select firmware for {family_name} (1-{len(major_options)}, s): ").strip().lower()
                                    
                                    if user_choice == 's':
                                        print(f"         Skipping {family_name}")
                                        break
                                    elif user_choice in major_options:
                                        selected_version = major_options[user_choice]
                                        # Apply the selected version to all models in this family
                                        for model in models:
                                            custom_versions[model] = selected_version
                                        print(f"         {family_name} firmware {selected_version}")
                                        print(f"            Applied to: {', '.join(sorted(models))}")
                                        break
                                    else:
                                        print(f"         Invalid selection. Please choose 1-{len(major_options)} or 's'.")
                                except KeyboardInterrupt:
                                    print("\n         Configuration cancelled.")
                                    break
                
                # Validate that we have comprehensive model coverage
                total_models_configured = len(custom_versions)
                models_from_plan = len(models_in_upgrade_plan)
                models_additionally_configured = total_models_configured - models_from_plan
                
                print(f"\n   Auto-upgrade coverage summary:")
                print(f"      � Models from upgrade plan: {models_from_plan}")
                print(f"      � Additional models configured: {models_additionally_configured}")
                print(f"      � Total models configured: {total_models_configured}")
                
                if total_models_configured > 0:
                    print(f"\n   Complete auto-upgrade model configuration:")
                    for model, version in sorted(custom_versions.items()):
                        status = "from upgrade plan" if model in models_in_upgrade_plan else "additional coverage"
                        print(f"      � {model} firmware {version} ({status})")
                
                # Configure auto-upgrade with comprehensive model-specific versions
                new_auto_upgrade = {
                    "enabled": True,
                    "version": "custom",  # Use "custom" to indicate custom_versions are in use
                    "custom_versions": custom_versions
                }
                
                # Time scheduling configuration for comprehensive auto-upgrade
                print(f"\n   Auto-upgrade time scheduling:")
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
                
                print(f"   Site auto-upgrade configured with model-specific versions")
                print(f"   New APs will auto-upgrade to model-appropriate firmware:")
                
                # Show the configured versions
                for model, version in custom_versions.items():
                    print(f"      � New {model} APs firmware {version}")
                
                # Show time schedule
                time_of_day = new_auto_upgrade.get("time_of_day", "02:00")
                day_of_week = new_auto_upgrade.get("day_of_week")
                if day_of_week:
                    schedule_text = f"every {day_of_week} at {time_of_day}"
                else:
                    schedule_text = f"daily at {time_of_day}"
                    
                print(f"   Schedule: {schedule_text}")
                print(f"   + Model compatibility: Protected - each model gets appropriate firmware")
                
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
            print(f"   Error during auto-upgrade configuration: {e}")
            logging.error(f"Error during auto-upgrade configuration: {e}")

    # Step 11: Offer to check upgrade status
    if successful_upgrades > 0:
        print(f"\n Firmware upgrade{'s' if successful_upgrades > 1 else ''} initiated successfully!")
        print(f"   {successful_upgrades} upgrade{'s' if successful_upgrades > 1 else ''} started across {len(devices_by_site)} site{'s' if len(devices_by_site) > 1 else ''}")
        
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
                        version_summary = f"{model_name} {upgrade_models[model_name]['version']}"
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
                
                print(f"   Upgrade tracking data saved to {upgrade_tracking_file}")
                logging.info(f"Saved {len(upgrade_ids)} upgrade IDs to tracking file {upgrade_tracking_file}")
                
            except Exception as e:
                print(f"   Warning: Failed to save upgrade tracking data: {e}")
                logging.warning(f"Failed to save upgrade tracking data: {e}")
        
        # Offer to check upgrade status now
        print(f"\n Reminder: You can monitor upgrade progress using menu option 60")
        print(f"   Option 60: Check current firmware upgrade status across organization")
        
        try:
            check_now = input(f"\n Would you like to check the upgrade status now? (y/n): ").strip().lower()
            if check_now in ['y', 'yes']:
                print(f"\n Checking upgrade status...")
                check_firmware_upgrade_status()
            else:
                print(f"   You can check upgrade status anytime using menu option 60")
        except (EOFError, KeyboardInterrupt):
            print(f"\n   You can check upgrade status anytime using menu option 60")
    
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
        
        print(f"\n  Advanced Firmware Upgrade Operation Completed!")
        print(f"   Successful upgrades initiated: {successful_upgrades} devices")
        print(f"   Failed upgrade attempts: {failed_upgrades} devices")
        print(f"   Detailed results logged to: {results_filename}")
        print(f"   Strategy used: {upgrade_config['strategy'].upper()}")
        
        # Show mixed-model upgrade summary if applicable
        unique_versions_used = set()
        models_upgraded = set()
        for result in results:
            if result.get("Status") != "ERROR":
                unique_versions_used.add(result.get("Target Version", "Unknown"))
                models_upgraded.add(result.get("Model", "Unknown"))
        
        if len(unique_versions_used) > 1:
            print(f"   Mixed-Model Upgrade: {len(models_upgraded)} models, {len(unique_versions_used)} firmware versions")
            for model in sorted(models_upgraded):
                # Find the version for this model
                model_version = "Unknown"
                for result in results:
                    if result.get("Model") == model and result.get("Status") != "ERROR":
                        model_version = result.get("Target Version", "Unknown")
                        break
                model_device_count = sum(1 for r in results if r.get("Model") == model and r.get("Status") != "ERROR")
                print(f"      � {model}: {model_device_count} devices firmware {model_version}")
            print(f"   This is normal behavior when different AP models support different firmware ranges")
        else:
            single_version = list(unique_versions_used)[0] if unique_versions_used else "Unknown"
            print(f"   Unified Upgrade: All {len(models_upgraded)} model(s) upgrading to firmware {single_version}")
        
        if upgrade_id:
            print(f"   Primary Upgrade ID: {upgrade_id}")
        
        print(f"\n  Important Notes:")
        print(f"   � Upgrades will continue in the background")
        print(f"   � Monitor device status in Mist portal or API")
        print(f"   � Strategy '{upgrade_config['strategy']}' controls rollout pace")
        if upgrade_config['enable_p2p']:
            print(f"   � P2P enabled - APs will share firmware locally")
        print(f"   � APs will reboot during upgrade process")
        print(f"   � Full upgrade process may take 5-15 minutes per device")
        if upgrade_config['strategy'] in ['canary', 'rrm']:
            print(f"   � Phased rollout will continue automatically based on strategy")
        if upgrade_config.get('start_time'):
            scheduled_time = datetime.fromtimestamp(upgrade_config['start_time']).strftime('%Y-%m-%d %H:%M')
            print(f"   � Upgrade scheduled for: {scheduled_time}")
        
        # Check if auto-upgrade was configured or disabled
        auto_upgrade_configured = any(r.get("Device ID") == "SITE_CONFIG" and "Configured" in r.get("Status", "") for r in results)
        auto_upgrade_disabled = any(r.get("Device ID") == "SITE_CONFIG" and "Disabled" in r.get("Status", "") for r in results)
        
        if auto_upgrade_configured:
            print(f"   � Site auto-upgrade configured - new APs will auto-upgrade")
        elif auto_upgrade_disabled:
            print(f"   � Site auto-upgrade disabled - new APs will NOT auto-upgrade")
        
        logging.info(f"! Advanced AP firmware upgrade results written to {results_filename} ({len(results)} entries)")
        logging.info(f"Advanced firmware upgrade summary: {successful_upgrades} successful, {failed_upgrades} failed, strategy: {upgrade_config['strategy']}")
        
    except Exception as e:
        logging.error(f"! Failed to write results to CSV: {e}")
        print(f"! Failed to write results to CSV: {e}")


def get_potential_anomaly_metrics():
    """Parse ConstInsightMetrics.csv to dynamically discover potential anomaly metrics.
    
    Returns metrics that are:
    1. Site-scoped (have 'site' in scopes field)
    2. Specifically related to anomaly detection (based on strict keyword matching)
    3. More likely to be supported by the anomaly API endpoint
    """
    potential_metrics = []
    
    try:
        # Ensure we have the latest const insight metrics
        check_and_generate_csv("ConstInsightMetrics.csv", export_all_const_definitions_to_csv)
        
        const_metrics_path = get_csv_file_path("ConstInsightMetrics.csv")
        
        # Stricter anomaly-related keywords focused on actual anomaly metrics
        anomaly_keywords = [
            "roam", "availability", "coverage", "capacity", "connect", 
            "success", "failure", "uptime"
        ]
        
        # Metrics that we know work well with the anomaly endpoint
        priority_metrics = [
            "client-roam-band5", "client-roam-band24", "ap-availability",
            "successful-connect", "time-to-connect", "client-coverage-band5", 
            "client-coverage-band24", "client-capacity-band5", "client-capacity-band24"
        ]
        
        with open(const_metrics_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                metric_name = row.get("metric_name", "").strip()
                scopes = row.get("scopes", "").lower()
                description = row.get("description", "").lower()
                
                # Prioritize known working metrics
                if metric_name in priority_metrics and "site" in scopes:
                    potential_metrics.append({
                        "metric_name": metric_name,
                        "description": row.get("description", ""),
                        "scopes": row.get("scopes", ""),
                        "type": row.get("type", ""),
                        "priority": True
                    })
                # Then add others that match our stricter criteria
                elif ("site" in scopes and 
                      any(keyword in description or keyword in metric_name.lower() 
                          for keyword in anomaly_keywords) and
                      metric_name not in priority_metrics):
                    
                    # Skip metrics that are clearly not anomaly-focused
                    if any(skip in metric_name.lower() or skip in description 
                           for skip in ["top-", "num_", "bytes", "rate", "latency", "{ctype}", "call-", "app-", "wan-", "minis-"]):
                        continue
                        
                    potential_metrics.append({
                        "metric_name": metric_name,
                        "description": row.get("description", ""),
                        "scopes": row.get("scopes", ""),
                        "type": row.get("type", ""),
                        "priority": False
                    })
        
        # Sort by priority (known working metrics first)
        potential_metrics.sort(key=lambda x: (not x.get("priority", False), x["metric_name"]))
                    
        logging.info(f"Discovered {len(potential_metrics)} potential anomaly metrics from ConstInsightMetrics.csv")
        return potential_metrics
        
    except Exception as e:
        logging.warning(f"Failed to parse ConstInsightMetrics.csv for anomaly metrics: {e}")
        # Fallback to known working metrics
        return [
            {"metric_name": "client-roam-band5", "description": "5GHz roaming anomalies", "priority": True},
            {"metric_name": "client-roam-band24", "description": "2.4GHz roaming anomalies", "priority": True},
            {"metric_name": "ap-availability", "description": "AP availability anomalies", "priority": True}
        ]


def export_site_anomaly_metrics_to_csv():
    """Export comprehensive anomaly events for a selected site to SiteAnomalyEvents_[SiteName].csv.
    
    Dynamically discovers potential anomaly metrics from ConstInsightMetrics.csv and uses 
    GET /api/v1/sites/:site_id/anomaly/:metric endpoint to retrieve anomaly events
    for all site-scoped metrics related to anomaly detection (capacity, coverage, roaming, 
    client connectivity, AP availability, etc.).
    """
    print("Export Site Anomaly Events:")
    logging.info("Starting export of site anomaly events...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        print("! No site selected. Exiting.")
        return
    
    # Get site name for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    # Clean site name for filename
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name)
    filename = f"SiteAnomalyEvents_{sanitized_site_name}.csv"
    
    # Dynamically discover potential anomaly metrics from ConstInsightMetrics.csv
    print("! Discovering potential anomaly metrics from Mist API definitions...")
    potential_metrics = get_potential_anomaly_metrics()
    
    # Extract just the metric names for API calls
    site_anomaly_metrics = [metric["metric_name"] for metric in potential_metrics]
    
    # Log discovered metrics
    print(f"! Found {len(site_anomaly_metrics)} potential anomaly metrics:")
    for metric_info in potential_metrics:
        print(f"  - {metric_info['metric_name']}: {metric_info['description'][:60]}...")
    
    if not site_anomaly_metrics:
        print("! No potential anomaly metrics found. Please check ConstInsightMetrics.csv availability.")
        return
    
    all_anomaly_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(site_anomaly_metrics)} different site anomaly events...")
    
    # Temporarily suppress mistapi error logging to keep console clean
    mistapi_loggers = ['apirequest', 'apiresponse', 'mistapi', 'mistapi.apirequest', 'mistapi.apiresponse']
    original_levels = {}
    for logger_name in mistapi_loggers:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.CRITICAL)  # Suppress ERROR logs temporarily
    
    try:
        for metric in site_anomaly_metrics:
            try:
                # Call the site anomaly API endpoint
                response = mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents(
                    apisession, 
                    site_id, 
                    metric
                )
                anomaly_data = getattr(response, 'data', response) or {}
                
                if anomaly_data:
                    # Add metric type identifier to each data point
                    anomaly_data['metric_type'] = metric
                    anomaly_data['site_id'] = site_id
                    anomaly_data['site_name'] = site_name
                    anomaly_data['data_type'] = 'site_anomaly_events'
                    all_anomaly_data.append(anomaly_data)
                    metrics_retrieved += 1
                    print(f"✓ Retrieved {metric} anomaly events")
                    logging.debug(f"Successfully retrieved {metric} anomaly events for site {site_id}")
                else:
                    print(f"! No {metric} anomaly events available")
                    logging.info(f"No {metric} anomaly events available for site {site_id}")
            except Exception as metric_error:
                print(f"! Error retrieving {metric} anomaly events: {metric_error}")
                logging.warning(f"Error retrieving {metric} anomaly events for site {site_id}: {metric_error}")
        
        # Process and save all collected anomaly data
        if all_anomaly_data:
            processed = flatten_nested_fields_in_list(all_anomaly_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} site anomaly event types exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} site anomaly event types for {site_name} to {filename}")
        else:
            print(f"! 0 anomaly events exported to {filename} (no data available)")
            logging.warning(f"No anomaly events available for site {site_name}")
            DataExporter.save_data_to_output([], filename)
            
    except Exception as e:
        print(f"! Error exporting site anomaly events: {e}")
        logging.error(f"Failed to export site anomaly events for {site_name}: {e}")
    finally:
        # Restore original logging levels
        for logger_name, original_level in original_levels.items():
            logging.getLogger(logger_name).setLevel(original_level)


def export_site_device_anomaly_to_csv():
    """Export device-specific anomaly events for a selected device to SiteDeviceAnomalyEvents_[SiteName]_[DeviceName].csv.
    
    Uses GET /api/v1/sites/:site_id/anomaly/:metric/device/:device_id endpoint to retrieve device anomaly events.
    """
    print("Export Site Device Anomaly Events:")
    logging.info("Starting export of site device anomaly events...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        print("! No site selected. Exiting.")
        return
    
    # Get site name for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    # Get device selection
    device_selection = prompt_device_selection(site_id)
    if not device_selection:
        print("! No device selected. Exiting.")
        return
    
    device_mac = device_selection[0]
    device_name = device_selection[1]
    
    # Clean names for filename
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name)
    sanitized_device_name = EnhancedSSHRunner.sanitize_filename(device_name)
    filename = f"SiteDeviceAnomalyEvents_{sanitized_site_name}_{sanitized_device_name}.csv"
    
    # Define device-specific anomaly metrics
    device_anomaly_metrics = [
        "ap_availability",
        "throughput",
        "capacity"
    ]
    
    all_device_anomaly_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(device_anomaly_metrics)} different device anomaly events for {device_name}...")
    
    # Temporarily suppress mistapi error logging to keep console clean
    mistapi_loggers = ['apirequest', 'apiresponse', 'mistapi', 'mistapi.apirequest', 'mistapi.apiresponse']
    original_levels = {}
    for logger_name in mistapi_loggers:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.CRITICAL)  # Suppress ERROR logs temporarily
    
    try:
        for metric in device_anomaly_metrics:
            try:
                # Call the site device anomaly API endpoint
                response = mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForDevice(
                    apisession, 
                    site_id, 
                    metric, 
                    device_mac
                )
                device_anomaly_data = getattr(response, 'data', response) or {}
                
                if device_anomaly_data:
                    # Add metadata
                    device_anomaly_data['metric_type'] = metric
                    device_anomaly_data['site_id'] = site_id
                    device_anomaly_data['site_name'] = site_name
                    device_anomaly_data['device_mac'] = device_mac
                    device_anomaly_data['device_name'] = device_name
                    device_anomaly_data['data_type'] = 'device_anomaly_events'
                    all_device_anomaly_data.append(device_anomaly_data)
                    metrics_retrieved += 1
                    print(f"✓ Retrieved {metric} device anomaly data")
                    logging.debug(f"Successfully retrieved {metric} device anomaly data for {device_mac}")
                else:
                    print(f"! No {metric} device anomaly data available")
                    logging.info(f"No {metric} device anomaly data available for {device_mac}")
            except Exception as metric_error:
                print(f"! Error retrieving {metric} device anomaly data: {metric_error}")
                logging.warning(f"Error retrieving {metric} device anomaly data for {device_mac}: {metric_error}")
        
        # Process and save all collected device anomaly data
        if all_device_anomaly_data:
            processed = flatten_nested_fields_in_list(all_device_anomaly_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} device anomaly event types exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} device anomaly event types for {device_name} to {filename}")
        else:
            print(f"! 0 device anomaly events exported to {filename} (no data available)")
            logging.warning(f"No device anomaly events available for {device_name}")
            DataExporter.save_data_to_output([], filename)
            
    except Exception as e:
        print(f"! Error exporting device anomaly events: {e}")
        logging.error(f"Failed to export device anomaly events for {device_name}: {e}")
    finally:
        # Restore original logging levels
        for logger_name, original_level in original_levels.items():
            logging.getLogger(logger_name).setLevel(original_level)
        logging.error(f"Failed to export device anomaly events for {device_name}: {e}")


def export_site_client_anomaly_to_csv():
    """Export client-specific anomaly events for a selected client to SiteClientAnomalyEvents_[SiteName]_[ClientMAC].csv.
    
    Uses GET /api/v1/sites/:site_id/anomaly/:metric/client/:client_mac endpoint to retrieve client anomaly events
    including connection success rates, band-specific roaming performance, and throughput issues.
    """
    print("Export Site Client Anomaly Events:")
    logging.info("Starting export of site client anomaly events...")
    
    # Get site selection
    site_id = prompt_site_selection()
    if not site_id:
        print("! No site selected. Exiting.")
        return
    
    # Get site name for filename
    try:
        response = mistapi.api.v1.sites.listSites(apisession, site_id)
        sites = mistapi.get_all(response=response, mist_session=apisession)
        site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
    except:
        site_name = site_id
    
    # Use the guided client selection function with the site_id
    client_mac, client_type, selected_site_id = prompt_client_selection(site_id)
    if not client_mac:
        print("! No client selected. Exiting.")
        return
    
    # Get hostname from the client MAC (we'll need to look it up)
    client_hostname = "Unknown"
    try:
        # Search for the client to get hostname
        response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(apisession, site_id, limit=100, duration="1d")
        clients = getattr(response, 'data', response) or []
        
        for client in clients:
            if client.get('mac') == client_mac:
                client_hostname = client.get('hostname', client.get('name', 'Unknown'))
                break
                
    except Exception as e:
        logging.warning(f"Could not retrieve client hostname for {client_mac}: {e}")
        client_hostname = client_mac  # Fallback to MAC address 
    
    # Clean names for filename
    sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name)
    filename = f"SiteClientAnomalyEvents_{sanitized_site_name}_{client_mac.replace(':', '')}.csv"
    
    # Define client-specific anomaly metrics (verified working metrics)
    client_anomaly_metrics = [
        "successful_connect",    # Note: uses underscore, not hyphen for client endpoint
        "roaming",              # Client roaming issues  
        "throughput"            # Client throughput anomalies
    ]
    
    all_client_anomaly_data = []
    metrics_retrieved = 0
    
    print(f"! Retrieving {len(client_anomaly_metrics)} different client anomaly events for {client_mac} ({client_hostname})...")
    
    # Temporarily suppress mistapi error logging to keep console clean
    mistapi_loggers = ['apirequest', 'apiresponse', 'mistapi', 'mistapi.apirequest', 'mistapi.apiresponse']
    original_levels = {}
    for logger_name in mistapi_loggers:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.CRITICAL)  # Suppress ERROR logs temporarily
    
    try:
        for metric in client_anomaly_metrics:
            try:
                # Call the site client anomaly API endpoint
                response = mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForClient(
                    apisession, 
                    site_id, 
                    client_mac, 
                    metric
                )
                client_anomaly_data = getattr(response, 'data', response) or {}
                
                if client_anomaly_data:
                    # Add metadata
                    client_anomaly_data['metric_type'] = metric
                    client_anomaly_data['site_id'] = site_id
                    client_anomaly_data['site_name'] = site_name
                    client_anomaly_data['client_mac'] = client_mac
                    client_anomaly_data['client_hostname'] = client_hostname
                    client_anomaly_data['data_type'] = 'client_anomaly_events'
                    all_client_anomaly_data.append(client_anomaly_data)
                    metrics_retrieved += 1
                    print(f"✓ Retrieved {metric} client anomaly data")
                    logging.debug(f"Successfully retrieved {metric} client anomaly data for {client_mac}")
                else:
                    print(f"! No {metric} client anomaly data available")
                    logging.info(f"No {metric} client anomaly data available for {client_mac}")
            except Exception as metric_error:
                print(f"! Error retrieving {metric} client anomaly data: {metric_error}")
                logging.warning(f"Error retrieving {metric} client anomaly data for {client_mac}: {metric_error}")
        
        # Process and save all collected client anomaly data
        if all_client_anomaly_data:
            processed = flatten_nested_fields_in_list(all_client_anomaly_data)
            processed = escape_multiline_strings_for_csv(processed)
            DataExporter.save_data_to_output(processed, filename)
            print(f"! {metrics_retrieved} client anomaly event types exported to {filename}")
            logging.info(f"Exported {metrics_retrieved} client anomaly event types for {client_mac} to {filename}")
        else:
            print(f"! 0 client anomaly events exported to {filename} (no data available)")
            logging.warning(f"No client anomaly events available for {client_mac}")
            DataExporter.save_data_to_output([], filename)
            
    except Exception as e:
        print(f"! Error exporting client anomaly events: {e}")
        logging.error(f"Failed to export client anomaly events for {client_mac}: {e}")
    finally:
        # Restore original logging levels
        for logger_name, original_level in original_levels.items():
            logging.getLogger(logger_name).setLevel(original_level)


def ssh_runner_main():
    """SSH Runner entry point - delegates to class-based application logic"""
    try:
        # Create argument parser
        parser = EnhancedSSHRunner.create_argument_parser()
        
        # Parse arguments
        args = parser.parse_args()
        
        # Run the application
        ssh_main_success = EnhancedSSHRunner.run_application(args)
        
        # If application returns False and it's likely due to missing parameters, show help
        if not ssh_main_success:
            # Check if we have the basic requirements that would indicate help is needed
            if not any([args.hostname, args.interactive]):
                parser.print_help()
        
        # Exit with appropriate code
        sys.exit(0 if ssh_main_success else 1)
        
    except argparse.ArgumentTypeError as e:
        print(f"❌ Invalid argument: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


def ssh_runner_interactive():
    """SSH Runner wrapper for menu system integration - runs with auto-detection"""
    try:
        print("\n🚀 Enhanced SSH Command Runner")
        print("=" * 60)
        
        # Create a mock args object that enables auto-detection behavior
        class MockArgs:
            def __init__(self):
                self.interactive = False  # Set to False to enable auto-detection
                self.hostname = None      # Will be auto-detected from .env
                self.username = None      # Will be auto-detected from .env
                self.password = None      # Will be auto-detected from .env
                self.command = None       # Will be auto-detected from CSV
                self.port = 22
                self.timeout = 30
                self.shell = True
                self.no_shell = False
                self.no_env = False       # Enable .env file loading
                self.log_level = 'INFO'
                self.debug = False
                self.max_threads = None
                self.secure = False
        
        # Run the SSH runner with auto-detection
        args = MockArgs()
        ssh_runner_success = EnhancedSSHRunner.run_application(args)
        
        if ssh_runner_success:
            print("\n✅ SSH runner completed successfully")
        else:
            print("\n❌ SSH runner completed with errors")
            
        return ssh_runner_success
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"SSH Runner error: {e}", exc_info=True)
        return False


menu_actions = {
    # ==============================
    # READ-ONLY OPERATIONS
    # ==============================
    
    # > Setup & Core Logs
    "1": (export_open_org_alarms_to_csv, "Export all organization alarms from the past day"),
    "2": (export_recent_device_events_to_csv, "Export all device events from the past 24 hours"),
    "3": (lambda: export_audit_logs_to_csv(full_history=False), "Export audit logs for the organization (last 24 hours)"),

    # Organization-Level Exports
    "11": (export_all_sites_to_csv, "Export a list of all sites in the organization"),
    "12": (export_device_inventory_to_csv, "Export the full inventory of devices in the organization"),
    "13": (export_device_stats_to_csv, "Export statistics for all devices in the organization"),
    "14": (export_device_port_stats_to_csv, "Export port-level statistics for switches and gateways"),
    "15": (export_vpn_peer_stats_to_csv, "Export VPN peer path statistics for the organization"),

    # Gateway & Site-Wide Exports
    # Direct reference (removed lambda) so systematic test harness can introspect 'fast' parameter
    "16": (export_gateway_synthetic_tests_to_csv, "Export synthetic test results for all gateways"),
    "17": (export_all_devices_to_csv, "Export a list of all devices in the organization"),
    "18": (export_site_settings_to_csv, "Export configuration settings for all sites"),
    "19": (export_gateway_test_results_by_site_to_csv, "Export all synthetic test results (including speed tests) for gateways"),

    # > Location-Enriched Exports
    "20": (export_sites_with_location_to_csv, "Export a list of sites with location and timezone info"),
    "21": (export_gateways_with_site_info_to_csv, "Export a list of gateways with associated site and address info"),
    "22": (export_devices_with_site_info_to_csv, "Export a list of all devices with associated site and address info"),
    "23": (lambda: (export_current_guest_users_to_csv(), export_historical_guest_users_to_csv()),"Export all current guest users and last 7 days of historical guests to CSV"),
    "24": (export_switch_vc_stats_to_csv, "Export all switch virtual chassis (VC/stacking) stats to CSV"),
    "25": (export_combined_inventory_with_site_info, "Export combined inventory with site and address info by calendar week"),
    "26": (export_gateway_templates_to_csv, "Export gateway templates from the organization"),
    "27": (export_all_sites_list_to_csv, "Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)"),
    "28": (lambda fast=False: export_gateways_with_wan_overrides_to_csv(fast=fast), "Find gateway ports overridden from template (outliers for compliance correction)"),
    
    # Site-Specific Data Exports
    "29": (export_site_port_stats_to_csv, "Export port statistics for a selected site"),
    "30": (export_site_clients_to_csv, "Export client statistics for a selected site"),
    "31": (export_site_devices_to_csv, "Export device list for a selected site"),
    "32": (export_site_device_stats_to_csv, "Export device statistics for a selected site"),
    "33": (export_site_device_virtual_chassis_to_csv, "Export virtual chassis information for a selected switch device"),
    "34": (export_site_wifi_clients_to_csv, "Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV"),
    
    # Organization Template Exports
    "35": (export_organization_templates_to_csv, "Export all organization templates (gateway, network, RF, site, AP)"),
    "36": (export_org_network_templates_to_csv, "Export network template information for the organization"),
    "37": (export_org_rf_templates_to_csv, "Export RF template information for the organization"),
    "38": (export_org_ap_templates_to_csv, "Export AP template information for the organization"),
    "39": (export_org_switch_templates_to_csv, "Export switch template information for the organization"),
    
    # Organization Statistics & Analytics  
    "40": (export_org_wireless_clients_to_csv, "Export wireless client statistics for the organization"),
    "41": (export_org_wired_clients_to_csv, "Export wired client statistics for the organization"),
    
    # Security & Monitoring
    "42": (export_org_security_events_to_csv, "Export security events for the organization"),
    "43": (export_org_rogue_clients_to_csv, "Export rogue client detections for the organization"),
    "44": (export_org_rogue_aps_to_csv, "Export rogue AP detections for the organization"),
    
    # Configuration & Management (Read-Only)
    "45": (export_org_licenses_to_csv, "Export license information for the organization"),
    "46": (export_org_psks_to_csv, "Export PSK (Pre-Shared Key) information for the organization"),
    "47": (export_org_webhooks_to_csv, "Export webhook configuration for the organization"),
    "48": (export_org_wlans_to_csv, "Export WLAN configuration for the organization"),
    "49": (export_site_wlans_to_csv, "Export WLAN configuration for a selected site"),
    "50": (export_site_beacons_to_csv, "Export beacon information for a selected site"),
    "51": (export_site_maps_to_csv, "Export map information for a selected site"),
    "52": (export_site_zones_to_csv, "Export zone information for a selected site"),
    "53": (export_site_insights_to_csv, "Export insights information for a selected site"),
    
    # Organization Management (Read-Only)
    "54": (export_org_api_tokens_to_csv, "Export API token information for the organization"),
    "55": (export_org_admins_to_csv, "Export administrator information for the organization"),
    "56": (export_org_msp_to_csv, "Export MSP (Managed Service Provider) information for the organization"),
    "57": (export_org_sso_to_csv, "Export SSO (Single Sign-On) information for the organization"),
    "58": (export_org_usage_to_csv, "Export license usage information for the organization"),
    "59": (export_org_mx_edges_to_csv, "Export MX Edge information for the organization"),
    
    # Status & Monitoring
    "60": (check_firmware_upgrade_status, "Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV"),
    "61": (lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: compare_inventory_with_csv(fast=fast, address_check=address_check, debug=debug, skip_ssl_verify=skip_ssl_verify), "Compare inventory data with external CSV file using configurable address similarity threshold (ADDRESS_MATCH_THRESHOLD in .env)"),
    "62": (poll_marvis_actions, "Interactive Marvis (VNA) AI troubleshooting - guided client, device, and network analysis"),
    
    # Work In Progress Features (Read-Only)
    "63": (export_all_org_device_events_52w_to_csv, "WIP Export all org device events from the last 52 weeks"),
    "64": (lambda: export_audit_logs_to_csv(full_history=True, duration="52w"), "WIP Export ALL audit logs for the organization (last 52 weeks)"),
    "65": (export_gateway_device_configs_to_csv, "WIP Export configuration details for all gateway devices across all sites"),
    
    
    # ==============================
    # UNSAFE/INTERACTIVE OPERATIONS
    # ==============================
    
    # > Site Selection & Interactive Tools
    "70": (prompt_and_log_site_selection, "Select a site (used by other functions)"),
    "71": (interactive_display_site_inventory, "View device inventory for a selected site"),
    "72": (interactive_display_device_stats, "View statistics for a selected device at a site"),
    "73": (interactive_display_device_tests, "View synthetic test stats for a selected gateway device"),
    "74": (interactive_display_device_config, "View configuration details for a selected device"),
    
    # > Continuous Operations & Monitoring
    "75": (lambda debug=False: loop_refresh_core_datasets(delay=None, debug=debug), "Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt'"),
    "76": (continuous_data_collection_loop, "Run continuous data collection loop (5 core API calls with rate limiting)"),
    
    # > File Processing & Support Operations
    "77": (SFPTransceiverDataProcessor.merge_transceiver_data, "Process and merge CSV files of SFP Module locations into a single CSV file"),
    "78": (generate_support_package, "Generate support package for each site"),
    
    # > CLI & WebSocket Operations
    "79": (launch_cli_shell, "Interactively execute a CLI command on a gateway or switch (exit with ~)"),
    "80": (run_arp_via_websocket, "Run ARP command on an AP and receive output via WebSocket"),

    # ! DESTRUCTIVE OPERATIONS - USE WITH EXTREME CAUTION
    "90": (bulk_upgrade_ap_firmware_by_site, " DESTRUCTIVE: Advanced bulk AP firmware upgrade with multiple strategies (big_bang, canary, rrm, serial), P2P sharing, scheduling, and progress monitoring"),
    "91": (reboot_devices_by_gateway_template_list, " DESTRUCTIVE: Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results"),
    "92": (convert_virtual_chassis_to_virtual_mac, " DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive selection)(WIP)"),
    "93": (convert_virtual_chassis_by_site_list, " DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation)"),
    "94": (check_virtual_chassis_conversion_status, "Check virtual chassis to virtual MAC conversion status for all switches"),
    "95": (lambda fast=False: export_gateway_device_stats_to_csv_with_freshness_check(fast=fast), "Export detailed device statistics for all gateways (with freshness check)"),
    "96": (export_gateways_with_wan_port_conflicts_to_csv, "Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2)"),
    "97": (ssh_runner_interactive, "Enhanced SSH Command Runner - Execute commands on remote network devices via SSH"),

    # ==============================
    # INSIGHTS API OPERATIONS - Organization & Site Analytics
    # ==============================
    "66": (export_org_sle_metrics_to_csv, "Export Organization SLE Metrics (Service Level Experience)"),
    "67": (export_org_sites_sle_summary_to_csv, "Export SLE summary metrics for all sites in the organization"),
    "68": (export_site_insight_metrics_to_csv, "Export general insight metrics for a selected site"),
    "69": (export_site_client_insights_to_csv, "Export client-specific insight metrics for a selected site"),
    "81": (export_site_device_insights_to_csv, "Export device-specific insight metrics for a selected site"),
    "82": (export_all_const_definitions_to_csv, "Export all available const definitions from the Mist API (comprehensive endpoint coverage)"),
    "83": (export_org_insight_metrics_to_csv, "Export Organization Insight Metrics (comprehensive operational insights)"),
    "84": (export_site_anomaly_metrics_to_csv, "Export Site Anomaly Events (dynamic discovery of all anomaly-related metrics from Mist API)"),
    "85": (export_site_device_anomaly_to_csv, "Export Site Device Anomaly Events (device-specific anomaly detection)"),
    "86": (export_site_client_anomaly_to_csv, "Export Site Client Anomaly Events (client-specific anomaly detection: connectivity, roaming, throughput)"),

    # ==============================
    # POST API OPERATIONS - Device Commands (Starting at 100)
    # ==============================
    
    # Device Network Operations removed (options 100, 101)
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
    print(" Starting systematic test of MistHelper menu options...")
    print("  Note: This will skip interactive, websocket, POST, and destructive operations")
    print(f"! Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define unsafe menu options that should be skipped during testing
    unsafe_options = {
        # Resource-intensive operations that consistently fail or take excessive time
        "14": "Port-level statistics - extremely resource intensive (8+ hours, often fails)",
        "18": "Site configurations - hits API rate limits after 7+ hours",
        
        # Interactive operations requiring user input
        "60": "Firmware upgrade status - requires interactive scope selection",
        "61": "CSV comparison - requires interactive file selection",
        "62": "Marvis troubleshooting - requires interactive option selection",
        
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
        
        # Site-specific operations requiring site selection
        "68": "Requires site selection",
        "69": "Requires site selection",
        "84": "Requires site selection",
        "85": "Requires site and device selection", 
        "86": "Requires site and client selection", 
        
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
        
        # DESTRUCTIVE operations - absolutely skip
        "90": "DESTRUCTIVE: AP firmware upgrade operation",
        "91": "DESTRUCTIVE: Device reboot operation", 
        "92": "DESTRUCTIVE: Virtual chassis conversion - WIP",
        "93": "DESTRUCTIVE: Virtual chassis conversion - bulk operation"
    }
    
    # Get all available menu options
    all_options = sorted(menu_actions.keys(), key=lambda x: float(x.replace('a', '.1')))
    
    # Define optimized test order based on execution time analysis (shortest to longest)
    # This ordering minimizes total test time by running quick tests first
    optimized_test_order = [
        # Fast tests (~0.6-3.5 seconds)
        "3",   # Audit Logs (~0.6s)
        "17",  # All Devices List (~3s)
        "11",  # All Sites List (~3.5s)
        
        # Medium tests (~18-30 seconds)
        "12",  # Device Inventory (~18s)
        "66",  # Organization SLE Metrics (new)
        "67",  # Organization Sites SLE Summary (new)
        "1",   # Organization Alarms (~30s)
        
        # Slower tests (~1-5 minutes)
        "13",  # Device Stats (~97s)
        "15",  # VPN Peer Stats (~257s)
        
        # Slow tests (~8+ minutes)
        "2",   # Device Events (~485s)
        "16",  # Gateway Synthetic Tests (~1115s)
        
        # Note: Options 14 (Port-level Statistics) and 18 (Site Configurations) 
        # have been moved to unsafe_options due to excessive resource consumption
    ]
    
    # Create optimized safe options list, preserving any additional options not in the predefined order
    safe_options_set = set(opt for opt in all_options if opt not in unsafe_options)
    safe_options = []
    
    # Add options in optimized order first
    for opt in optimized_test_order:
        if opt in safe_options_set:
            safe_options.append(opt)
            safe_options_set.remove(opt)
    
    # Add any remaining safe options at the end (for future additions)
    safe_options.extend(sorted(safe_options_set, key=lambda x: float(x.replace('a', '.1'))))
    
    print(f"! Found {len(all_options)} total menu options")
    print(f"! {len(safe_options)} safe options will be tested")
    print(f"!  {len(unsafe_options)} unsafe options will be skipped")
    print()
    
    # Show which options will be skipped and why
    print(" Skipping unsafe operations:")
    for opt in sorted(unsafe_options.keys(), key=lambda x: float(x.replace('a', '.1'))):
        if opt in menu_actions:
            _, description = menu_actions[opt]
            reason = unsafe_options[opt]
            print(f"   {opt:2}: {description[:60]}... (Reason: {reason})")
    print()
    
    # Test safe options
    print(" Testing safe operations:")
    success_count = 0
    error_count = 0
    
    global org_id
    if not org_id:
        org_id = get_cached_or_prompted_org_id()
    
    for i, option in enumerate(safe_options, 1):
        func, description = menu_actions[option]
        print(f"   [{i:2}/{len(safe_options)}] Testing option {option:2}: {description[:60]}...")
        # Determine if fast mode is globally enabled and if function supports it
        fast_enabled = False
        try:
            fast_enabled = bool(globals().get('FAST_MODE_ENABLED', False))
        except Exception:
            fast_enabled = False

        # Defensive fallback: if global not set but original CLI args indicate fast, force enable
        if not fast_enabled:
            cli_args = globals().get('args') if 'args' in globals() else None
            try:
                if cli_args and getattr(cli_args, 'fast', False):
                    fast_enabled = True
                    logging.debug(f"SYSTEMATIC_TEST: Forcing fast_enabled=True for option {option} based on CLI args.fast")
            except Exception:
                pass

        # Introspect signature to see if 'fast' is accepted
        supports_fast = False
        try:
            sig = inspect.signature(func)
            supports_fast = 'fast' in sig.parameters
        except Exception:
            supports_fast = False

        # Log harness invocation detail
        logging.info(
            f"SYSTEMATIC_TEST: INVOKE option={option} fast_supported={supports_fast} fast_enabled={fast_enabled} test_mode=True description='{description}'"
        )

        # Build kwargs dynamically
        invoke_kwargs = {}
        if supports_fast and fast_enabled:
            invoke_kwargs['fast'] = True
        try:
            logging.info(f"SYSTEMATIC_TEST: Starting test of menu option {option} (fast_applied={invoke_kwargs.get('fast', False)})")
            func(**invoke_kwargs)
            print(f"   [SUCCESS] Option {option} completed successfully")
            success_count += 1
            logging.info(f"SYSTEMATIC_TEST: Successfully completed menu option {option}")
        except Exception as e:
            print(f"   [FAILED]  Option {option} failed: {str(e)[:100]}...")
            error_count += 1
            logging.error(f"SYSTEMATIC_TEST: Failed menu option {option}: {e}")
            
        # Small delay between tests to be respectful to the API
        time.sleep(1)
    
    # Summary
    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print(" Systematic Test Summary:")
    print(f"   Successful operations: {success_count}")
    print(f"   Failed operations: {error_count}")
    print(f"   Skipped unsafe operations: {len(unsafe_options)}")
    print(f"   Total coverage: {success_count}/{len(all_options)} ({success_count/len(all_options)*100:.1f}%)")
    print(f"    Total execution time: {total_time:.2f} seconds")
    print(f"   Detailed logs in: script.log")
    
    if error_count == 0:
        print("   All tested operations completed successfully!")
        logging.info(f"SYSTEMATIC_TEST: All {success_count} tested operations completed successfully in {total_time:.2f}s")
        return True
    else:
        print(f"    {error_count} operations failed - check logs for details")
        logging.warning(f"SYSTEMATIC_TEST: {error_count} operations failed out of {len(safe_options)} tested")
        return False


class EnhancedSSHRunner:
    """Advanced SSH connection and command execution handler with comprehensive validation"""
    
    def __init__(self, timeout: int = 30, logger: logging.Logger = None):
        """
        Initialize SSH runner
        
        Args:
            timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout
        self.client = None
        self.logger = logger or logging.getLogger('ssh_runner_v2')
        self.logger.debug(f"EnhancedSSHRunner initialized with timeout={timeout}")
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """
        Validate hostname or IP address format
        
        Args:
            hostname: Hostname or IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not hostname or not isinstance(hostname, str):
            return False
        
        # Check length limits
        if len(hostname) > 253:  # RFC 1035 limit
            return False
        
        # Try to parse as IP address first
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass
        
        # Validate as hostname (RFC 1123 compliant)
        if len(hostname) > 253:
            return False
        
        # Remove trailing dot if present
        hostname = hostname.rstrip('.')
        
        # Check overall format
        hostname_pattern = re.compile(
            r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        )
        
        return bool(hostname_pattern.match(hostname))
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """
        Validate port number is in valid range
        
        Args:
            port: Port number to validate
            
        Returns:
            bool: True if valid (1-65535), False otherwise
        """
        return isinstance(port, int) and 1 <= port <= 65535
    
    @staticmethod
    def validate_timeout(timeout: int) -> bool:
        """
        Validate timeout value is reasonable
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            bool: True if valid (1-3600), False otherwise
        """
        return isinstance(timeout, int) and 1 <= timeout <= 3600
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate SSH username format
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        
        # Length check (typical Unix limit is 32 chars)
        if len(username) > 32 or len(username) < 1:
            return False
        
        # Basic character validation (alphanumeric, underscore, hyphen, dot)
        username_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        return bool(username_pattern.match(username))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:
            return "unknown"
        
        # Remove or replace dangerous characters
        # Keep only alphanumeric, underscore, hyphen, and dot
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Remove leading/trailing dots and dashes
        sanitized = sanitized.strip('.-')
        
        # Ensure filename isn't empty after sanitization
        if not sanitized:
            sanitized = "sanitized_host"
        
        # Limit length to prevent filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        # Prevent reserved filenames on Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if sanitized.upper() in reserved_names:
            sanitized = f"host_{sanitized}"
        
        return sanitized
    
    @staticmethod
    def validate_command(command: str) -> bool:
        """
        Basic validation for SSH commands
        
        Args:
            command: Command to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not command or not isinstance(command, str):
            return False
        
        # Length check (reasonable command length limit)
        if len(command) > 1000:
            return False
        
        # Check for null bytes (can cause issues in some contexts)
        if '\x00' in command:
            return False
        
        return True
    
    @staticmethod
    def validate_thread_count(thread_count: int, max_hosts: int) -> int:
        """
        Validate and adjust thread count to reasonable limits
        
        Args:
            thread_count: Requested thread count
            max_hosts: Maximum number of hosts
            
        Returns:
            int: Validated thread count
        """
        if not isinstance(thread_count, int) or thread_count <= 0:
            return min(max_hosts, multiprocessing.cpu_count())
        
        # Limit to reasonable maximum (don't overwhelm system)
        max_reasonable_threads = min(50, max_hosts * 2)
        return min(thread_count, max_reasonable_threads, max_hosts)
    
    @staticmethod
    def parse_host_list(hosts_str: str) -> list:
        """
        Parse comma-separated host list from .env file with validation
        
        Args:
            hosts_str: String containing comma-separated hosts (e.g., '192.168.1.1,192.168.1.2')
            
        Returns:
            list: List of validated hostnames/IPs
        """
        if not hosts_str or not isinstance(hosts_str, str):
            return []
        
        # Length check to prevent DoS
        if len(hosts_str) > 10000:  # Reasonable limit for host list
            print("⚠️  Host list too long, truncating to first 10000 characters")
            hosts_str = hosts_str[:10000]
        
        # Split by comma and validate each host
        hosts = []
        invalid_hosts = []
        
        for host in hosts_str.split(','):
            host = host.strip()
            if not host:  # Skip empty entries
                continue
                
            # Validate hostname/IP format
            if EnhancedSSHRunner.validate_hostname(host):
                hosts.append(host)
            else:
                invalid_hosts.append(host)
        
        # Warn about invalid hosts
        if invalid_hosts:
            print(f"⚠️  Skipping {len(invalid_hosts)} invalid hosts: {', '.join(invalid_hosts[:5])}")
            if len(invalid_hosts) > 5:
                print(f"    ... and {len(invalid_hosts) - 5} more")
        
        # Limit total number of hosts to prevent resource exhaustion
        max_hosts = 100  # Reasonable limit
        if len(hosts) > max_hosts:
            print(f"⚠️  Too many hosts ({len(hosts)}), limiting to first {max_hosts}")
            hosts = hosts[:max_hosts]
        
        return hosts
    
    @staticmethod
    def parse_command_list(commands_str: str) -> list:
        """
        Parse comma-separated command list from .env file with validation
        
        Args:
            commands_str: String containing comma-separated commands (e.g., 'show ver,show route' or '"show ver","show route"')
            
        Returns:
            list: List of validated commands
        """
        if not commands_str or not isinstance(commands_str, str):
            return []
        
        # Length check to prevent DoS
        if len(commands_str) > 50000:  # Reasonable limit for command string
            print("⚠️  Command list too long, truncating to first 50000 characters")
            commands_str = commands_str[:50000]
        
        # Remove outer quotes if present
        commands_str = commands_str.strip('\'"')
        
        # Split by comma and validate each command
        commands = []
        invalid_commands = []
        
        for cmd in commands_str.split(','):
            # Remove quotes and whitespace
            clean_cmd = cmd.strip().strip('\'"').strip()
            
            if not clean_cmd:  # Skip empty commands
                continue
            
            # Validate command
            if EnhancedSSHRunner.validate_command(clean_cmd):
                commands.append(clean_cmd)
            else:
                invalid_commands.append(clean_cmd[:50] + "..." if len(clean_cmd) > 50 else clean_cmd)
        
        # Warn about invalid commands
        if invalid_commands:
            print(f"⚠️  Skipping {len(invalid_commands)} invalid commands: {', '.join(invalid_commands[:3])}")
            if len(invalid_commands) > 3:
                print(f"    ... and {len(invalid_commands) - 3} more")
        
        # Limit total number of commands to prevent resource exhaustion
        max_commands = 50  # Reasonable limit
        if len(commands) > max_commands:
            print(f"⚠️  Too many commands ({len(commands)}), limiting to first {max_commands}")
            commands = commands[:max_commands]
        
        return commands
    
    @staticmethod
    def load_commands_from_csv(csv_file_path: str = "data/SSH_COMMANDS.CSV") -> list:
        """
        Load SSH commands from a CSV file as fallback when .env has no commands.
        
        Expected CSV format:
        - First column: command
        - Optional second column: description/comment (ignored)
        - Lines starting with # are treated as comments and ignored
        - Empty lines are ignored
        
        Example CSV content:
        # Network device commands
        show version
        show interfaces,Interface status
        show route,Routing table
        
        Args:
            csv_file_path (str): Path to the CSV file (default: data/SSH_COMMANDS.CSV)
            
        Returns:
            list: List of validated commands loaded from the CSV file
        """
        import csv
        
        commands = []
        
        if not os.path.exists(csv_file_path):
            # Legacy fallback: check previous root location if default data path missing
            if csv_file_path.startswith("data/"):
                legacy_path = csv_file_path.replace("data/", "")
                if os.path.exists(legacy_path):
                    try:
                        print(f"ℹ️  Using legacy SSH commands file at {legacy_path}; move it to data/ for consistency.")
                        csv_file_path = legacy_path
                    except Exception:
                        return commands
                else:
                    return commands
            else:
                return commands
            
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Use simple comma delimiter instead of trying to detect dialect
                # This is more reliable for simple CSV files with comments
                reader = csv.reader(csvfile, delimiter=',')
                invalid_commands = []
                
                for row_num, row in enumerate(reader, 1):
                    if not row:  # Skip empty rows
                        continue
                        
                    # Skip comment lines (lines starting with #)
                    first_cell = str(row[0]).strip()
                    if first_cell.startswith('#') or not first_cell:
                        continue
                    
                    # Get the command (first column)
                    command = first_cell
                    
                    # Validate the command
                    if EnhancedSSHRunner.validate_command(command):
                        commands.append(command)
                    else:
                        invalid_cmd = command[:50] + "..." if len(command) > 50 else command
                        invalid_commands.append(f"line {row_num}: {invalid_cmd}")
                
                # Warn about invalid commands
                if invalid_commands:
                    print(f"⚠️  Skipping {len(invalid_commands)} invalid commands from {csv_file_path}:")
                    for invalid_cmd in invalid_commands[:3]:  # Show first 3
                        print(f"    {invalid_cmd}")
                    if len(invalid_commands) > 3:
                        print(f"    ... and {len(invalid_commands) - 3} more")
                
                # Limit total number of commands to prevent resource exhaustion
                max_commands = 50  # Reasonable limit
                if len(commands) > max_commands:
                    print(f"⚠️  Too many commands in {csv_file_path} ({len(commands)}), limiting to first {max_commands}")
                    commands = commands[:max_commands]
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not read {csv_file_path}: {e}")
            return []
            
        return commands
    
    def create_secure_log_file(self, hostname: str) -> tuple:
        """
        Create a secure per-host log file with proper sanitization
        
        Args:
            hostname: Original hostname
            
        Returns:
            tuple: (log_file_path, write_function)
        """
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = self.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            self.logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                self.logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                self.logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    self.logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                self.logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        return host_log_file, write_to_host_log
    
    def connect(self, hostname: str, username: str, password: str, port: int = 22) -> bool:
        """
        Establish SSH connection to remote host with input validation
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            port: SSH port (default 22)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Validate inputs before attempting connection
        if not self.validate_hostname(hostname):
            error_msg = f"Invalid hostname format: {hostname}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not self.validate_username(username):
            error_msg = f"Invalid username format: {username}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not self.validate_port(port):
            error_msg = f"Invalid port number: {port} (must be 1-65535)"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not password:
            error_msg = "Password cannot be empty"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        try:
            self.logger.info(f"Attempting SSH connection to {hostname}:{port} as {username}")
            print(f"🔌 Connecting to {hostname}:{port} as {username}...")
            
            # Create SSH client
            self.client = SSHClient()
            # Load existing host keys if available
            self.client.load_system_host_keys()  
            try:
                self.client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except FileNotFoundError:
                # known_hosts file doesn't exist yet - that's fine
                pass
            
            # For internal networks: Auto-accept new host keys
            # NOTE: Only use this for trusted internal networks, not internet-facing connections
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.logger.debug("SSH client created with AutoAddPolicy for internal network use")
            
            # Attempt connection
            connection_start = time.time()
            self.logger.debug(f"Initiating SSH connection with timeout={self.timeout}s")
            self.client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            connection_time = time.time() - connection_start
            self.logger.debug(f"SSH connection established in {connection_time:.2f} seconds")
            
            self.logger.info(f"Successfully connected to {hostname} in {connection_time:.2f} seconds")
            print(f"✅ Successfully connected to {hostname}")
            return True
            
        except socket.gaierror as e:
            error_msg = f"DNS Resolution Error for {hostname}: {e}"
            self.logger.error(error_msg)
            print(f"❌ DNS Resolution Error: {e}")
            return False
        except socket.timeout:
            error_msg = f"Connection timeout to {hostname}:{port} after {self.timeout} seconds"
            self.logger.error(error_msg)
            print(f"❌ Connection timeout after {self.timeout} seconds")
            return False
        except paramiko.AuthenticationException as e:
            error_msg = f"Authentication failed for {username}@{hostname}: {e}"
            self.logger.error(error_msg)
            print("❌ Authentication failed - check username and password")
            return False
        except paramiko.SSHException as e:
            error_msg = f"SSH Error connecting to {hostname}: {e}"
            self.logger.error(error_msg)
            print(f"❌ SSH Error: {e}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error connecting to {hostname}: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            print(f"❌ Unexpected error: {e}")
            return False
    
    def execute_command(self, command: str, use_shell: bool = False, hostname: str = "unknown") -> Tuple[bool, str, str]:
        """
        Execute command on remote host
        
        Args:
            command: Command to execute
            use_shell: Use interactive shell instead of exec_command (better for network devices)
            hostname: Hostname for display purposes
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:
            error_msg = "No active SSH connection"
            self.logger.error(error_msg)
            return False, "", error_msg
        
        try:
            self.logger.debug(f"Executing command: '{command}' (shell_mode={use_shell})")
            self.logger.debug(f"Command execution method: {'shell' if use_shell else 'direct'}")
            
            command_start = time.time()
            
            if use_shell:
                # Use interactive shell for network devices
                self.logger.debug("Using shell-based execution for network device compatibility")
                return self._execute_with_shell(command, command_start, hostname)
            else:
                # Use direct exec_command (try with PTY first for network devices)
                self.logger.debug("Using direct exec_command execution")
                return self._execute_direct(command, command_start, hostname)
                
        except socket.timeout:
            error_msg = f"Command execution timeout after {self.timeout} seconds"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def _execute_direct(self, command: str, start_time: float, hostname: str = 'unknown') -> Tuple[bool, str, str]:
        """Execute command using exec_command with PTY support"""
        try:
            # Try with PTY first (better for network devices)
            self.logger.debug("Attempting exec_command with get_pty=True")
            stdin, stdout, stderr = self.client.exec_command(
                command, 
                timeout=self.timeout, 
                get_pty=True
            )
            
            # Get output
            stdout_output = stdout.read().decode('utf-8', errors='ignore')
            stderr_output = stderr.read().decode('utf-8', errors='ignore')
            exit_status = stdout.channel.recv_exit_status()
            command_time = time.time() - start_time
            
            self.logger.debug(f"Command completed in {command_time:.2f} seconds with exit status: {exit_status}")
            # Escape newlines and special characters for clean logging
            stdout_sample = stdout_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            self.logger.debug(f"STDOUT ({len(stdout_output)} chars): {stdout_sample}{'...' if len(stdout_output) > 200 else ''}")
            
            if stderr_output:
                stderr_sample = stderr_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                self.logger.warning(f"STDERR ({len(stderr_output)} chars): {stderr_sample}{'...' if len(stderr_output) > 200 else ''}")
            
            print(f"📊 [{hostname}] Command completed with exit status: {exit_status}")
            return exit_status == 0, stdout_output, stderr_output
            
        except Exception as e:
            # If PTY fails, try without PTY
            self.logger.warning(f"exec_command with PTY failed: {e}, trying without PTY")
            try:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
                stdout_output = stdout.read().decode('utf-8', errors='ignore')
                stderr_output = stderr.read().decode('utf-8', errors='ignore')
                exit_status = stdout.channel.recv_exit_status()
                command_time = time.time() - start_time
                
                self.logger.debug(f"Command completed (no PTY) in {command_time:.2f} seconds with exit status: {exit_status}")
                print(f"📊 [{hostname}] Command completed with exit status: {exit_status}")
                return exit_status == 0, stdout_output, stderr_output
            except Exception as e2:
                self.logger.error(f"Both PTY and non-PTY exec_command failed: {e2}")
                raise e2
    
    def _execute_with_shell(self, command: str, start_time: float, hostname: str = 'unknown') -> Tuple[bool, str, str]:
        """Execute command using interactive shell with device type detection"""
        try:
            self.logger.debug("Using interactive shell mode")
            
            # Start interactive shell
            shell = self.client.invoke_shell(term='vt100', width=120, height=24)
            shell.settimeout(self.timeout)
            
            # Wait for initial prompt
            max_wait = 3  # Maximum wait time
            wait_increment = 0.2
            total_wait = 0
            initial_sample = "(no initial data)"
            
            while total_wait < max_wait:
                time.sleep(wait_increment)
                total_wait += wait_increment
                if shell.recv_ready():
                    initial_output = shell.recv(4096).decode('utf-8', errors='ignore')
                    # Escape newlines and special characters for clean logging
                    initial_sample = initial_output[:100].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    self.logger.debug(f"Initial shell output: {initial_sample}...")
                    break
            
            # Send command with improved buffering
            try:
                command_with_newline = command + '\n'
                shell.send(command_with_newline)
                time.sleep(0.1)  # Small delay to ensure command is sent completely
                self.logger.debug(f"Sent command to shell: {command}")
            except Exception as e:
                self.logger.warning(f"Error sending command: {e}")
                return False, "", f"Failed to send command: {e}"
            
            # Wait for command execution with adaptive timing
            max_cmd_wait = 6  # Increased maximum command wait time
            cmd_wait = 0
            
            while cmd_wait < max_cmd_wait:
                time.sleep(wait_increment)
                cmd_wait += wait_increment
                if shell.recv_ready():
                    break            # Collect output with universal timing-based approach
            output = ""
            last_data_time = time.time()
            no_data_timeout = 3.0  # Universal timeout - wait 3 seconds after no new data
            max_total_wait = 120  # Universal maximum wait time (2 minutes) for any command
            
            max_output_size = 100 * 1024 * 1024  # 100MB limit - higher since we now drain properly
            chunk_count = 0
            
            try:
                while (time.time() - start_time) < max_total_wait:
                    current_duration = time.time() - start_time
                    
                    # Hard timeout detection - if we've been running too long, force completion
                    if current_duration > 90:  # 90 second hard timeout
                        print(f"⏰ [{hostname}] HANG DETECTED: Command running for {current_duration:.0f}s, forcing completion")
                        self.logger.warning(f"Command hang detected after {current_duration:.0f}s, forcing completion: {command}")
                        output += f"\n\n[COMMAND TIMEOUT - Forced completion after {current_duration:.0f}s]\n"
                        break
                    
                    # Progress messages for long-running commands
                    if current_duration > 30:  # Show progress after 30 seconds
                        if chunk_count % 150 == 0:  # Every 150 chunks after 30 seconds
                            print(f"⏱️ [{hostname}] Long-running command... {current_duration:.0f}s elapsed (Ctrl+C to interrupt)")
                    
                    if shell.recv_ready():
                        chunk = shell.recv(131072).decode('utf-8', errors='ignore')  # Even larger buffer (128KB) for efficiency
                        output += chunk
                        last_data_time = time.time()  # Reset timer when we get data
                        chunk_count += 1
                        
                        # Log progress every 100 chunks for very large outputs
                        if chunk_count % 100 == 0:
                            output_mb = len(output) / (1024 * 1024)
                            self.logger.debug(f"Receiving data... {chunk_count} chunks, {output_mb:.1f}MB")
                            # Print progress for user feedback on large outputs
                            if output_mb > 5:
                                print(f"📥 [{hostname}] Receiving large output... {output_mb:.1f}MB (Press Ctrl+C to interrupt)")
                        
                        # Check output size limit - but keep draining to prevent blocking
                        if len(output) > max_output_size:
                            self.logger.warning(f"Output size limit ({max_output_size // (1024*1024)}MB) reached, draining remaining data...")
                            output += f"\n\n[OUTPUT TRUNCATED - Size limit of {max_output_size // (1024*1024)}MB reached]\n"
                            print(f"📋 [{hostname}] Output truncated at {max_output_size // (1024*1024)}MB, draining remaining data...")
                            
                            # Continue draining data without storing it to prevent device blocking
                            drain_start = time.time()
                            max_drain_time = 30  # Maximum 30 seconds to drain
                            drained_chunks = 0
                            
                            while (time.time() - drain_start) < max_drain_time:
                                if shell.recv_ready():
                                    shell.recv(262144)  # Large drain buffer (256KB) for maximum efficiency
                                    drained_chunks += 1
                                    last_data_time = time.time()  # Reset timeout
                                    
                                    # Show drain progress
                                    if drained_chunks % 100 == 0:
                                        drain_duration = time.time() - drain_start
                                        print(f"🚰 [{hostname}] Draining excess data... {drain_duration:.0f}s ({drained_chunks} chunks discarded)")
                                        
                                else:
                                    # Check if we've waited long enough since last data
                                    if (time.time() - last_data_time) >= no_data_timeout:
                                        break  # No new data, device finished
                                    time.sleep(0.05)
                            
                            drain_duration = time.time() - drain_start
                            print(f"✅ [{hostname}] Data drain completed in {drain_duration:.1f}s ({drained_chunks} chunks discarded)")
                            break
                        
                        time.sleep(0.01)  # Very small delay for maximum throughput
                    else:
                        # Check if we've waited long enough since last data
                        if (time.time() - last_data_time) >= no_data_timeout:
                            break  # No new data for timeout period, command likely complete
                        time.sleep(0.05)  # Small sleep when no data available
                    
            except KeyboardInterrupt:
                print(f"\n💥 [{hostname}] Ctrl+C detected! Interrupting command: {command}")
                self.logger.warning(f"Command interrupted by user: {command}")
                output += f"\n\n[COMMAND INTERRUPTED BY USER - Ctrl+C pressed during data collection]\n"
                # Don't return here, continue with cleanup and return what we have
            
            # Log command completion status
            command_duration = time.time() - start_time
            output_size_mb = len(output) / (1024 * 1024)
            if output_size_mb > 1:
                self.logger.info(f"Command data collection completed after {command_duration:.2f}s, output size: {output_size_mb:.2f}MB ({chunk_count} chunks)")
            else:
                self.logger.debug(f"Command data collection completed after {command_duration:.2f}s, output size: {len(output)} bytes ({chunk_count} chunks)")
            
            # Fast cleanup - especially important after truncation
            cleanup_start = time.time()
            max_cleanup_time = 2.0  # Maximum 2 seconds for cleanup to prevent hangs
            
            try:
                shell.send('exit\n')
                shell.send('\n')  # Extra newline to ensure command completion
                
                # Quick cleanup collection with timeout
                cleanup_timeout = time.time() + max_cleanup_time
                while time.time() < cleanup_timeout:
                    if shell.recv_ready():
                        try:
                            shell.recv(4096)  # Drain any remaining output quickly
                            time.sleep(0.1)
                        except:
                            break
                    else:
                        time.sleep(0.1)
                        break  # No more data, exit quickly
                        
            except KeyboardInterrupt:
                print(f"💥 [{hostname}] Ctrl+C during cleanup - forcing shell close")
                self.logger.warning("Command cleanup interrupted by user")
            except Exception as e:
                self.logger.debug(f"Warning during cleanup: {e}")
            
            cleanup_duration = time.time() - cleanup_start
            if cleanup_duration > 1.0:
                self.logger.debug(f"Cleanup took {cleanup_duration:.2f}s")
            
            # Force close shell to prevent hangs
            try:
                shell.close()
            except Exception as e:
                self.logger.debug(f"Warning during shell close: {e}")
            command_time = time.time() - start_time
            
            # Enhanced output cleaning to remove shell artifacts and prompts
            lines = output.split('\n')
            cleaned_lines = []
            skip_command = False
            command_found = False
            
            # Common shell prompts and artifacts to filter out
            shell_artifacts = [
                'exit', 'logout', 'Connection to', 'Last login:',
                'Welcome to', 'Match except:', '---(more)---',
                'No next tag', 'press RETURN', 'Invalid command:', 'xit',
                'vyos@vyos:~$', 'Connection closed'
            ]
            
            # Shell prompt patterns (more comprehensive)
            shell_prompt_patterns = [
                r'.*[$#>]\s*$',  # Basic prompts ending with $, #, or >
                r'vyos@.*[$#>]\s*$',  # VyOS prompts
                r'.*@.*:.*[$#>]\s*$',  # Standard user@host:path$ prompts
                r'{master:\d+}',  # Juniper master mode prompts
                r'^\s*$',  # Empty lines (remove excessive whitespace)
                r':+.*\[.*\d+;\d+.*H.*',  # ANSI cursor positioning sequences
                r'^:.*press RETURN.*',  # Pager "press RETURN" prompts
                r'^>vyos@.*\$ xit$',  # VyOS shell prompt with truncated exit
                r'^vyos@.*:~\$.*xit$',  # VyOS shell cleanup with xit
                r'^Invalid command: \[xit\]$',  # VyOS invalid xit command error
                r'^.*Connection to .* closed\.$',  # Connection closed messages
                r'^\s*xit\s*$'  # Standalone truncated exit commands
            ]
            
            import re
            
            for line in lines:
                original_line = line
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip command echo (first occurrence of the command)
                if not command_found and command.strip() in line:
                    command_found = True
                    continue
                
                # Skip shell artifacts
                should_skip = False
                for artifact in shell_artifacts:
                    if artifact.lower() in line.lower():
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Skip shell prompts using regex patterns
                is_prompt = False
                for pattern in shell_prompt_patterns:
                    if re.match(pattern, line):
                        is_prompt = True
                        break
                
                if is_prompt:
                    continue
                
                # Enhanced cleaning for terminal control sequences and VyOS artifacts
                clean_line = re.sub(r'\x1b\[[0-9;]*[mK]', '', line)  # ANSI escape codes
                clean_line = re.sub(r'\x1b\[\?[0-9]+[hl]', '', clean_line)  # ANSI mode changes
                clean_line = re.sub(r'\x1b\[[0-9]+;[0-9]+H', '', clean_line)  # ANSI cursor positioning
                clean_line = re.sub(r':\s*$', '', clean_line)  # Remove trailing colons from pager prompts
                clean_line = clean_line.replace('\r', '').replace('\x08', '').strip()  # Remove carriage returns and backspaces
                
                # Skip VyOS-specific shell artifacts
                vyos_artifacts = [
                    r'^\s*xit\s*$',
                    r'^Invalid command: \[xit\]$',
                    r'^vyos@.*:~\$',
                    r'^Connection.*closed\.$'
                ]
                
                skip_vyos_artifact = False
                for artifact_pattern in vyos_artifacts:
                    if re.match(artifact_pattern, clean_line):
                        skip_vyos_artifact = True
                        break
                
                # Only add non-empty cleaned lines that aren't VyOS artifacts
                if clean_line and not skip_vyos_artifact:
                    cleaned_lines.append(clean_line)
            
            cleaned_output = '\n'.join(cleaned_lines).strip()
            
            self.logger.debug(f"Shell command completed in {command_time:.2f} seconds")
            # Only log output sample for smaller outputs to avoid log spam
            if len(cleaned_output) < 10000:  # Only log sample for outputs under 10KB
                output_sample = cleaned_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                self.logger.debug(f"Shell output ({len(cleaned_output)} chars): {output_sample}{'...' if len(cleaned_output) > 200 else ''}")
            else:
                self.logger.debug(f"Shell output: {len(cleaned_output)} characters (large output, sample not logged)")
            
            # Universal success detection - simple and reliable
            command_success = len(cleaned_output) > 0
            
            # More intelligent error detection - only flag real command errors
            # Skip error detection for shell cleanup artifacts
            error_patterns = [
                "command not found", "syntax error",
                "permission denied", "authentication failed",
                "connection refused", "host unreachable", "network unreachable",
                "no such file or directory"
            ]
            
            # Exclude patterns that are likely shell cleanup artifacts
            shell_cleanup_indicators = [
                "invalid command: [xit]",
                "unknown command: xit",
                "invalid command: exit",
                "connection to .* closed"
            ]
            
            output_lower = cleaned_output.lower()
            
            # Check for shell cleanup indicators first - if found, don't treat as error
            is_shell_cleanup = False
            for cleanup_pattern in shell_cleanup_indicators:
                if cleanup_pattern in output_lower:
                    is_shell_cleanup = True
                    self.logger.debug(f"Shell cleanup artifact detected, ignoring: {cleanup_pattern}")
                    break
            
            # Only check for real errors if this isn't shell cleanup
            if not is_shell_cleanup:
                for pattern in error_patterns:
                    if pattern in output_lower:
                        command_success = False
                        self.logger.warning(f"Command error detected: {pattern}")
                        break
            
            self.logger.debug(f"Command success determination: success={command_success}, output_length={len(cleaned_output)}")
            print(f"📊 [{hostname}] Command completed in {command_time:.2f} seconds")
            return command_success, cleaned_output, ""
            
        except Exception as e:
            error_msg = f"Shell execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.logger.debug("Closing SSH connection")
            self.client.close()
            self.client = None
            print("🔌 SSH connection closed")
        else:
            self.logger.debug("No SSH connection to close")
    
    @staticmethod
    def load_ssh_config_from_env(env_file: str = ".env") -> dict:
        """
        Load SSH configuration from .env file with comprehensive validation
        
        Args:
            env_file: Path to the .env file (default: ".env")
            
        Returns:
            dict: SSH configuration with keys: hosts, username, password, commands
        """
        config = {
            'hosts': [],
            'username': None, 
            'password': None,
            'commands': []
        }
        
        # Validate env_file path to prevent directory traversal
        if not env_file or '..' in env_file or env_file.startswith('/') or '\\' in env_file:
            print(f"⚠️  Invalid .env file path: {env_file}")
            return config
        
        if not os.path.exists(env_file):
            return config
        
        # Check file size to prevent DoS
        try:
            file_size = os.path.getsize(env_file)
            if file_size > 1024 * 1024:  # 1MB limit
                print(f"⚠️  .env file too large ({file_size} bytes), skipping")
                return config
        except OSError as e:
            print(f"⚠️  Cannot access .env file: {e}")
            return config
        
        if DOTENV_AVAILABLE:
            # Use python-dotenv for proper parsing
            try:
                load_dotenv(env_file)
                ssh_host = os.getenv('SSH_HOST')
                if ssh_host:
                    config['hosts'] = EnhancedSSHRunner.parse_host_list(ssh_host)
                
                # Validate username
                username = os.getenv('SSH_USER')
                if username and EnhancedSSHRunner.validate_username(username):
                    config['username'] = username
                elif username:
                    print(f"⚠️  Invalid username format in .env file: {username}")
                
                config['password'] = os.getenv('SSH_PASSWORD')
                
                # Parse SSH_COMMANDS
                ssh_commands = os.getenv('SSH_COMMANDS')
                if ssh_commands:
                    config['commands'] = EnhancedSSHRunner.parse_command_list(ssh_commands)
            except Exception as e:
                print(f"⚠️  Error loading .env with python-dotenv: {e}")
        else:
            # Basic manual parsing for .env files with enhanced validation
            try:
                with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = 0
                    for line in f:
                        line_count += 1
                        
                        # Prevent processing too many lines
                        if line_count > 1000:
                            print("⚠️  .env file has too many lines, stopping at 1000")
                            break
                        
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Skip lines without equals sign
                        if '=' not in line:
                            continue
                        
                        # Handle multiple = signs correctly
                        parts = line.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Process known keys with validation
                        if key == 'SSH_HOST':
                            config['hosts'] = EnhancedSSHRunner.parse_host_list(value)
                        elif key == 'SSH_USER':
                            if EnhancedSSHRunner.validate_username(value):
                                config['username'] = value
                            else:
                                print(f"⚠️  Invalid username format in .env file: {value}")
                        elif key == 'SSH_PASSWORD':
                            config['password'] = value
                        elif key == 'SSH_COMMANDS':
                            config['commands'] = EnhancedSSHRunner.parse_command_list(value)
                            
            except UnicodeDecodeError as e:
                print(f"⚠️  .env file encoding error: {e}")
            except IOError as e:
                print(f"⚠️  Error reading {env_file}: {e}")
            except Exception as e:
                print(f"⚠️  Unexpected error reading {env_file}: {e}")
        
        return config
    
    @staticmethod
    def setup_logging(log_level: str = 'INFO') -> logging.Logger:
        """
        Setup comprehensive logging configuration with syslog-style levels
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Unified logging: use root handlers (script.log + console) only
        logger = logging.getLogger('ssh_runner_v2')
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        # Remove any prior dedicated handlers so we don't duplicate output
        for h in list(logger.handlers):
            logger.removeHandler(h)
        # Ensure messages bubble to root configuration
        logger.propagate = True
        # Emit initialization message (will land in script.log)
        if log_level.upper() == 'DEBUG':
            logger.debug("Enhanced SSH Runner v2 logging initialized (root handlers)")
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized (root handlers)")
        return logger
    
    @staticmethod
    def run_multiple_ssh_commands(hostname: str, username: str, password: str, commands: list, 
                                 port: int = 22, timeout: int = 30, use_shell: bool = False) -> bool:
        """
        Connect via SSH and execute multiple commands sequentially
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            commands: List of commands to execute
            port: SSH port (default 22)
            timeout: Connection timeout
            use_shell: Use interactive shell mode (better for network devices)
            
        Returns:
            bool: True if all commands successful, False otherwise
        """
        # Get the already-configured logger
        logger = logging.getLogger('ssh_runner_v2')
        logger.debug(f"Starting SSH multi-command execution: {hostname}:{port} - {len(commands)} commands (shell={use_shell})")
        logger.debug(f"Commands to execute: {commands}")
        
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"🌐 [{hostname}] Logging to: {host_log_file}")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        overall_success = True
        
        # Initialize host log with header
        header = f"""
{'='*80}
SSH Session Log for Host: {hostname}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Commands to execute: {len(commands)}
{'='*80}"""
        write_to_host_log(header)
        
        try:
            # Connect once for all commands
            if not runner.connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"❌ {error_msg}")
                return False
            
            logger.debug(f"SSH connected to {hostname}, executing {len(commands)} commands")
            connection_msg = f"\n🚀 Executing {len(commands)} commands sequentially..."
            write_to_host_log(connection_msg)
            
            # Execute each command with keyboard interrupt handling
            for i, command in enumerate(commands, 1):
                try:
                    separator = f"\n{'='*60}"
                    command_header = f"📝 Command {i}/{len(commands)}: {command}"
                    separator_line = '='*60
                    
                    write_to_host_log(separator)
                    write_to_host_log(command_header)
                    write_to_host_log(separator_line)
                    
                    print(f"⚡ [{hostname}] Executing command: {command}")
                    success, stdout, stderr = runner.execute_command(command, use_shell=use_shell, hostname=hostname)
                    
                    if stdout:
                        write_to_host_log("📤 OUTPUT:")
                        write_to_host_log(stdout)
                    
                    if stderr:
                        write_to_host_log("📤 ERRORS:")
                        write_to_host_log(stderr)
                    
                    if success:
                        logger.debug(f"[{hostname}] Command {i}/{len(commands)} completed: {command}")
                        success_msg = f"✅ Command {i} executed successfully"
                        write_to_host_log(success_msg)
                    else:
                        logger.warning(f"[{hostname}] Command {i}/{len(commands)} failed: {command[:50]}...")
                        failure_msg = f"❌ Command {i} failed"
                        write_to_host_log(failure_msg)
                        overall_success = False
                    
                    # Small delay between commands for network devices
                    if i < len(commands):
                        time.sleep(0.5)
                        
                except KeyboardInterrupt:
                    print(f"\n💥 [{hostname}] Ctrl+C detected! Skipping remaining commands...")
                    interrupt_msg = f"\n❌ Command {i} interrupted by user (Ctrl+C)\n⏭️ Skipping remaining {len(commands) - i} commands"
                    write_to_host_log(interrupt_msg)
                    logger.warning(f"[{hostname}] Command execution interrupted by user at command {i}/{len(commands)}")
                    overall_success = False
                    break
            
            final_separator = f"\n{'='*60}"
            write_to_host_log(final_separator)
            
            if overall_success:
                logger.info(f"[{hostname}] All {len(commands)} commands completed successfully")
                final_msg = "✅ All commands executed successfully"
                write_to_host_log(final_msg)
            else:
                logger.warning(f"[{hostname}] Some commands failed during execution")
                final_msg = "⚠️  Some commands failed - check output above"
                write_to_host_log(final_msg)
            
            return overall_success
            
        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error during multi-command execution: {type(e).__name__}: {e}", exc_info=True)
            error_msg = f"❌ Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner.disconnect()
            logger.debug(f"[{hostname}] SSH multi-command session completed")
            
            # Write session footer to host log with safer success check
            try:
                # Ensure we have a valid overall_success value
                final_success = locals().get('overall_success', False)
                if not isinstance(final_success, bool):
                    logger.warning(f"Overall success value is not boolean: {type(final_success)} = {final_success}")
                    final_success = False
                    
                footer = f"""
{'='*80}
SSH Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'SUCCESS' if final_success else 'FAILED'}
Log file: {host_log_file}
{'='*80}"""
                write_to_host_log(footer)
            except Exception as e:
                logger.error(f"Error in multi-command footer generation: {type(e).__name__}: {e}")
                # Write minimal footer
                try:
                    simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    write_to_host_log(simple_footer)
                except Exception as e2:
                    logger.error(f"Even simple multi-command footer failed: {e2}")
    
    @staticmethod
    def run_ssh_command(hostname: str, username: str, password: str, command: str, 
                       port: int = 22, timeout: int = 30, use_shell: bool = False) -> bool:
        """
        Connect via SSH and execute a command
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            command: Command to execute
            port: SSH port (default 22)
            timeout: Connection timeout
            use_shell: Use interactive shell mode (better for network devices)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the already-configured logger
        logger = logging.getLogger('ssh_runner_v2')
        logger.debug(f"Starting SSH command execution: {hostname}:{port} - '{command}' (shell={use_shell})")
        logger.debug(f"Single command details: timeout={timeout}, use_shell={use_shell}")
        
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"🌐 [{hostname}] Logging to: {host_log_file}")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        
        # Initialize host log with header
        header = f"""
{'='*80}
SSH Single Command Log for Host: {hostname}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Command: {command}
{'='*80}"""
        write_to_host_log(header)
        
        try:
            # Connect
            if not runner.connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"❌ {error_msg}")
                return False
            
            logger.debug(f"SSH connected to {hostname}, executing single command")
            
            # Execute command
            single_cmd_success, stdout, stderr = runner.execute_command(command, use_shell=use_shell, hostname=hostname)
            
            # Display results
            separator = "\n" + "=" * 60
            output_header = "📋 COMMAND OUTPUT"
            separator_line = "=" * 60
            
            write_to_host_log(separator)
            write_to_host_log(output_header)
            write_to_host_log(separator_line)
            
            if stdout:
                write_to_host_log("📤 STDOUT:")
                write_to_host_log(stdout)
            
            if stderr:
                write_to_host_log("📤 STDERR:")
                write_to_host_log(stderr)
            
            if not stdout and not stderr:
                write_to_host_log("📝 No output returned")
            
            write_to_host_log(separator_line)
            
            if single_cmd_success:
                logger.info(f"[{hostname}] Command completed successfully")
                success_msg = "✅ Command executed successfully"
                write_to_host_log(success_msg)
            else:
                logger.warning(f"[{hostname}] Command failed: {command[:50]}...")
                failure_msg = "❌ Command execution failed or returned non-zero exit status"
                write_to_host_log(failure_msg)
                    
            return single_cmd_success
            
        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error during SSH command execution: {type(e).__name__}: {e}", exc_info=True)
            error_msg = f"❌ Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner.disconnect()
            logger.debug(f"[{hostname}] SSH single command session completed")
            
            # Write session footer to host log with safer success check
            try:
                # Ensure we have a valid success value
                final_success = locals().get('single_cmd_success', False)
                if not isinstance(final_success, bool):
                    logger.warning(f"Success value is not boolean: {type(final_success)} = {final_success}")
                    final_success = False
                    
                footer = f"""
{'='*80}
SSH Single Command Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'SUCCESS' if final_success else 'FAILED'}
Log file: {host_log_file}
{'='*80}"""
                write_to_host_log(footer)
            except Exception as e:
                logger.error(f"Error in footer generation: {type(e).__name__}: {e}")
                # Write minimal footer
                try:
                    simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    write_to_host_log(simple_footer)
                except Exception as e2:
                    logger.error(f"Even simple footer failed: {e2}")
    
    @staticmethod
    def run_ssh_command_on_host(hostname: str, username: str, password: str, commands: list, 
                               port: int = 22, timeout: int = 30, use_shell: bool = True) -> tuple:
        """
        Run SSH commands on a single host (for multi-threading)
        
        Args:
            hostname: IP address or hostname
            username: SSH username  
            password: SSH password
            commands: List of commands to execute
            port: SSH port
            timeout: Connection timeout
            use_shell: Whether to use shell mode
            
        Returns:
            tuple: (hostname, success, results_summary)
        """
        # Use the unified SSH runner logger (propagates to script.log)
        logger = logging.getLogger('ssh_runner_v2')

        try:
            logger.debug(f"[{hostname}] Starting SSH session...")

            if len(commands) == 1:
                # Single command
                host_success = EnhancedSSHRunner.run_ssh_command(hostname, username, password, commands[0], port, timeout, use_shell)
                return (hostname, host_success, f"Single command: {commands[0]}")
            else:
                # Multiple commands
                host_success = EnhancedSSHRunner.run_multiple_ssh_commands(hostname, username, password, commands, port, timeout, use_shell)
                return (hostname, host_success, f"{len(commands)} commands executed")

        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
            return (hostname, False, f"Error: {e}")
    
    @staticmethod
    def run_ssh_commands_multi_host(hosts: list, username: str, password: str, commands: list,
                                   port: int = 22, timeout: int = 30, use_shell: bool = True,
                                   max_threads: int = 5) -> dict:
        """
        Run SSH commands on multiple hosts concurrently using threading

        Args:
            hosts: List of hostnames/IPs
            username: SSH username
            password: SSH password  
            commands: List of commands to execute on each host
            port: SSH port
            timeout: Connection timeout
            use_shell: Whether to use shell mode
            max_threads: Maximum number of concurrent threads

        Returns:
            dict: Results summary with success/failure counts per host
        """
        logger = logging.getLogger('ssh_runner_v2')
        # Debug diagnostic for mysterious dict+float TypeError
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[TRACE] Enter run_ssh_commands_multi_host(hosts={hosts}, username={username}, port={port}, timeout={timeout}, use_shell={use_shell}, max_threads={max_threads})")
            logger.debug(f"[TRACE] Types: hosts={type(hosts)}, username={type(username)}, password={'***' if password else None}, commands={type(commands)}, timeout={type(timeout)}")
        
        print(f"\n🚀 Starting SSH execution on {len(hosts)} hosts ({max_threads} threads)")
        logger.info(f"Multi-host SSH execution: {len(hosts)} hosts, {len(commands)} commands, {max_threads} threads")
        logger.debug(f"Target hosts: {hosts}")
        logger.debug(f"Commands: {commands}")
        logger.debug(f"Connection parameters: port={port}, timeout={timeout}, use_shell={use_shell}")
        
        ssh_execution_results = {}
        successful_hosts = []
        failed_hosts = []
        
        # Use ThreadPoolExecutor for thread management
        with ThreadPoolExecutor(max_workers=max_threads, thread_name_prefix="SSH") as executor:
            # Submit all host tasks
            future_to_host = {
                executor.submit(EnhancedSSHRunner.run_ssh_command_on_host, host, username, password, commands, 
                               port, timeout, use_shell): host 
                for host in hosts
            }
            
            # Process completed tasks (custom loop to avoid as_completed timeout TypeError)
            try:
                import concurrent.futures as _cf
                pending = set(future_to_host.keys())
                iteration = 0
                while pending:
                    iteration += 1
                    done, pending = _cf.wait(pending, return_when=_cf.FIRST_COMPLETED)
                    for future in done:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"[TRACE] wait loop iteration={iteration} future_done={future.done()} future={future}")
                        try:
                            hostname, host_success, summary = future.result()
                        except Exception as fut_e:
                            logger.error(f"[TRACE] Future exception: {type(fut_e).__name__}: {fut_e}", exc_info=True)
                            hostname = future_to_host.get(future, 'unknown')
                            host_success = False
                            summary = f"Error: {fut_e}"
                        ssh_execution_results[hostname] = {
                            'success': host_success,
                            'summary': summary
                        }
                        if host_success:
                            successful_hosts.append(hostname)
                            logger.debug(f"[{hostname}] Completed successfully: {summary}")
                        else:
                            failed_hosts.append(hostname)
                            logger.error(f"[{hostname}] Failed: {summary}")
            except Exception as loop_e:
                logger.error(f"[TRACE] Multi-host wait loop failure: {type(loop_e).__name__}: {loop_e}", exc_info=True)
                # Fallback: mark any remaining hosts as failed
                for future, host in future_to_host.items():
                    if host not in ssh_execution_results:
                        ssh_execution_results[host] = {'success': False, 'summary': f'Loop failure: {loop_e}'}
                        failed_hosts.append(host)
        
        # Summary report
        print(f"\n{'='*60}")
        print(f"📊 EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total hosts: {len(hosts)}")
        print(f"Successful: {len(successful_hosts)} ✅")
        print(f"Failed: {len(failed_hosts)} ❌")
        print(f"Per-host logs: per-host-logs/ssh_output_<hostname>_<timestamp>.log")
        
        if successful_hosts:
            print(f"\n✅ Successful hosts: {', '.join(successful_hosts)}")
        
        if failed_hosts:
            print(f"\n❌ Failed hosts: {', '.join(failed_hosts)}")
        
        logger.info(f"Multi-host execution completed: {len(successful_hosts)}/{len(hosts)} successful")
        
        return {
            'total': len(hosts),
            'successful': len(successful_hosts),
            'failed': len(failed_hosts),
            'successful_hosts': successful_hosts,
            'failed_hosts': failed_hosts,
            'results': ssh_execution_results
        }
    
    @staticmethod
    def run_application(args):
        """Main application logic - handles all the SSH runner functionality"""
        # Determine logging level (--debug flag overrides --log-level)
        log_level = 'DEBUG' if args.debug else args.log_level
        
        # Setup logging with specified level
        logger = EnhancedSSHRunner.setup_logging(log_level)

        # Optional line-level tracing (only when debug enabled) to capture exact failing line
        tracer_installed = False
        previous_tracer = None
        if logger.isEnabledFor(logging.DEBUG):
            try:
                import sys, inspect
                runner_file = __file__
                # Rough bounds: limit tracing to lines inside this file within the class region to reduce noise
                CLASS_START = 14300  # approximate lower bound (keep generous)
                CLASS_END = 16600    # approximate upper bound
                def _ssh_line_tracer(frame, event, arg):
                    if event == 'line':
                        try:
                            if frame.f_code.co_filename == runner_file and CLASS_START <= frame.f_lineno <= CLASS_END:
                                logger.debug(f"[LINE] {frame.f_code.co_name}:{frame.f_lineno}")
                        except Exception:
                            pass
                    return _ssh_line_tracer
                previous_tracer = sys.gettrace()
                sys.settrace(_ssh_line_tracer)
                tracer_installed = True
                logger.debug("[TRACE] Line-level tracer installed for EnhancedSSHRunner region")
            except Exception as _trace_e:
                logger.debug(f"[TRACE] Failed to install line tracer: {_trace_e}")
        
        # Interactive mode
        if args.interactive:
            return EnhancedSSHRunner.interactive_mode()
        
        # Determine if we should use .env file (default behavior unless --no-env is specified)
        use_env = not args.no_env
        
        # Try to load .env configuration
        env_config = {}
        if use_env:
            logger.info("Loading SSH credentials from .env file (default behavior)")
            env_config = EnhancedSSHRunner.load_ssh_config_from_env()
            if any([env_config.get('hosts'), env_config['username'], env_config['password']]):
                host_count = len(env_config.get('hosts', []))
                hosts_str = ', '.join(env_config.get('hosts', [])) if host_count <= 3 else f"{host_count} hosts"
                logger.info(f"Found .env credentials - Hosts: {hosts_str}, User: {env_config['username']}, Commands: {len(env_config['commands'])}")
        
        # Determine final connection parameters (command line overrides .env)
        final_hosts = []
        if args.hostname:
            final_hosts = [args.hostname]  # Single host from command line
        elif env_config.get('hosts'):
            final_hosts = env_config['hosts']  # Multiple hosts from .env
        
        final_username = args.username or env_config.get('username') 
        final_password = env_config.get('password')  # Only from .env, never from command line
        
        # Handle secure password input if needed
        if not final_password and not args.secure:
            if final_username and final_hosts:
                host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
                final_password = getpass.getpass(f"🔒 Enter password for {final_username}@{host_display}: ")
            else:
                print("❌ Password required but not provided")
                return False
        elif args.secure and not final_password:
            host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
            final_password = getpass.getpass(f"🔒 Enter password for {final_username}@{host_display}: ")
        # SECURITY: Password argument removed - this code block is no longer needed
        
        # Validate final parameters
        validated_hosts = []
        invalid_hosts = []
        
        for host in final_hosts:
            if EnhancedSSHRunner.validate_hostname(host):
                validated_hosts.append(host)
            else:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            print(f"❌ Invalid hosts detected: {', '.join(invalid_hosts)}")
            if not validated_hosts:
                print("❌ No valid hosts remaining")
                return False
            else:
                print(f"⚠️  Proceeding with {len(validated_hosts)} valid hosts")
                final_hosts = validated_hosts
        
        # Validate username
        if final_username and not EnhancedSSHRunner.validate_username(final_username):
            print(f"❌ Invalid username format: {final_username}")
            return False
        
        # Check if we have minimum required parameters
        if not all([final_hosts, final_username, final_password]):
            missing = []
            if not final_hosts: missing.append("hostname/SSH_HOST")
            if not final_username: missing.append("username/SSH_USER") 
            if not final_password: missing.append("password/SSH_PASSWORD")
            
            print(f"❌ Error: Missing required parameters: {', '.join(missing)}")
            if use_env:
                print("💡 Add these to your .env file or provide as command line arguments")
                print("💡 Use --no-env flag to disable .env file loading")
            else:
                print("💡 Provide as command line arguments or remove --no-env flag to use .env file")
                # Since we can't access the parser here, we'll let the caller handle help display
            return False
        
        # Determine commands to execute
        commands_to_run = []
        
        # Priority 1: Command line argument
        if args.command:
            commands_to_run = [args.command]
            logger.info(f"Using command from command line: {args.command}")
        # Priority 2: SSH_COMMANDS from .env file
        elif use_env and env_config.get('commands'):
            commands_to_run = env_config['commands']
            logger.info(f"Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
    # Priority 3: data/SSH_COMMANDS.CSV file as fallback
        elif not args.command:
            csv_commands = EnhancedSSHRunner.load_commands_from_csv()
            if csv_commands:
                commands_to_run = csv_commands
                logger.info(f"Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                print(f"💡 Loaded {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV")
        # Priority 4: Interactive input
        else:
            # Check what command sources are available
            env_commands = env_config.get('commands', []) if use_env else []
            csv_commands = EnhancedSSHRunner.load_commands_from_csv() if not commands_to_run else []
            
            if env_commands and csv_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(env_commands)} commands from .env, or 'csv' for {len(csv_commands)} commands from CSV): ").strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"💡 Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                elif command.lower() == 'csv':
                    commands_to_run = csv_commands
                    print(f"💡 Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif env_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(env_commands)} commands from .env): ").strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"💡 Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif csv_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(csv_commands)} commands from data/SSH_COMMANDS.CSV): ").strip()
                if not command:
                    commands_to_run = csv_commands
                    print(f"💡 Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            else:
                command = input("⚡ Enter command to execute: ").strip()
                if not command:
                    print("❌ No commands specified")
                    return False
                commands_to_run = [command]
        
        # Validate commands
        validated_commands = []
        invalid_commands = []
        
        for cmd in commands_to_run:
            if EnhancedSSHRunner.validate_command(cmd):
                validated_commands.append(cmd)
            else:
                invalid_cmd = cmd[:50] + "..." if len(cmd) > 50 else cmd
                invalid_commands.append(invalid_cmd)
        
        if invalid_commands:
            print(f"❌ Invalid commands detected: {', '.join(invalid_commands)}")
            if not validated_commands:
                print("❌ No valid commands remaining")
                return False
            else:
                print(f"⚠️  Proceeding with {len(validated_commands)} valid commands")
                commands_to_run = validated_commands
        
        if not commands_to_run:
            print("❌ No commands to execute")
            return False
        
        # Determine shell mode (default is True unless --no-shell is specified)
        use_shell_mode = args.shell and not args.no_shell
        
        # Execute SSH commands
        try:
            if len(final_hosts) == 1:
                # Single host execution
                hostname = final_hosts[0]
                if len(commands_to_run) == 1:
                    # Single command on single host
                    ssh_success = EnhancedSSHRunner.run_ssh_command(
                        hostname,
                        final_username,
                        final_password,
                        commands_to_run[0],
                        args.port,
                        args.timeout,
                        use_shell_mode
                    )
                else:
                    # Multiple commands on single host
                    ssh_success = EnhancedSSHRunner.run_multiple_ssh_commands(
                        hostname,
                        final_username,
                        final_password,
                        commands_to_run,
                        args.port,
                        args.timeout,
                        use_shell_mode
                    )
                
                return ssh_success
                
            else:
                # Multiple host execution (multi-threaded)
                default_threads = multiprocessing.cpu_count()
                requested_threads = args.max_threads or default_threads
                max_threads = EnhancedSSHRunner.validate_thread_count(requested_threads, len(final_hosts))
                
                if max_threads != requested_threads:
                    print(f"⚠️  Adjusted thread count from {requested_threads} to {max_threads}")
                
                ssh_results = EnhancedSSHRunner.run_ssh_commands_multi_host(
                    final_hosts,
                    final_username,
                    final_password,
                    commands_to_run,
                    args.port,
                    args.timeout,
                    use_shell_mode,
                    max_threads
                )
                
                # Return success if all hosts succeeded
                return ssh_results['failed'] == 0
            
        except KeyboardInterrupt:
            print("\n🛑 Operation cancelled by user")
            return False
        except Exception as e:
            # Enhanced diagnostic logging for elusive dict+float TypeError
            logger.error("Fatal error during SSH runner execution", exc_info=True)
            try:
                logger.debug(f"[DIAG] Type of exception object: {type(e)}")
            except Exception:
                pass
            print(f"❌ Fatal error: {e}")
            return False
        finally:
            if tracer_installed:
                try:
                    import sys
                    sys.settrace(previous_tracer)
                    logger.debug("[TRACE] Line-level tracer removed")
                except Exception as _trace_cleanup_e:
                    logger.debug(f"[TRACE] Failed to remove line tracer: {_trace_cleanup_e}")

    @staticmethod
    def create_argument_parser():
        """Create and configure the argument parser"""
        parser = argparse.ArgumentParser(
            description="Enhanced SSH Command Runner v2 - Execute commands on remote hosts via SSH",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    # Default: Uses .env file and shell mode (recommended)
    python ssh_runner_v2.py
    
    # Override with specific command (still uses shell mode by default)
    python ssh_runner_v2.py "show version"
    
    # Manual SSH connection (uses secure password prompt)
    python ssh_runner_v2.py 192.168.1.1 vyos --secure "show version"
    
    # Use exec_command mode instead of shell mode  
    python ssh_runner_v2.py --no-shell "ls -la"
    
    # Multi-host with custom thread count
    python ssh_runner_v2.py --max-threads 10
    
    # Interactive mode
    python ssh_runner_v2.py --interactive
    
    # Disable .env loading and use exec_command mode with secure password
    python ssh_runner_v2.py --no-env --no-shell --secure 192.168.1.1 vyos "show version"

.env file format (SECURITY: Keep this file private and out of version control):
    SSH_HOST=192.168.1.1,192.168.1.2,192.168.1.3
    SSH_USER=vyos
    SSH_PASSWORD=your_password
    SSH_COMMANDS=show version,show interfaces,show route
    
SECURITY NOTES:
    - Never commit .env files containing passwords to version control
    - Use secure password prompts (--secure flag) when possible
    - Consider using SSH keys instead of passwords for better security
    - Add .env to your .gitignore file
            """
        )
        
        # Interactive mode
        parser.add_argument("--interactive", "-i", action="store_true",
                           help="Run in interactive mode")
        
        # .env file mode controls
        parser.add_argument("--no-env", action="store_true",
                           help="Disable automatic .env file loading (use manual credentials)")
        
        # Connection parameters
        parser.add_argument("hostname", nargs="?", help="Hostname or IP address (overrides SSH_HOST)")
        parser.add_argument("username", nargs="?", help="SSH username (overrides SSH_USER)") 
        parser.add_argument("password", nargs="?", help="SSH password (overrides SSH_PASSWORD)")
        parser.add_argument("command", nargs="?", help="Command to execute (overrides SSH_COMMANDS)")
        
        # Optional parameters with validation
        def validate_port_arg(value):
            ivalue = int(value)
            if not EnhancedSSHRunner.validate_port(ivalue):
                raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got {ivalue}")
            return ivalue
        
        def validate_timeout_arg(value):
            ivalue = int(value)
            if not EnhancedSSHRunner.validate_timeout(ivalue):
                raise argparse.ArgumentTypeError(f"Timeout must be between 1 and 3600 seconds, got {ivalue}")
            return ivalue
        
        def validate_threads_arg(value):
            ivalue = int(value)
            if ivalue <= 0 or ivalue > 100:
                raise argparse.ArgumentTypeError(f"Thread count must be between 1 and 100, got {ivalue}")
            return ivalue
        
        parser.add_argument("--port", "-p", type=validate_port_arg, default=22,
                           help="SSH port (default: 22)")
        parser.add_argument("--timeout", "-t", type=validate_timeout_arg, default=30,
                           help="Connection timeout in seconds (default: 30)")
        parser.add_argument("--secure", "-s", action="store_true",
                           help="Prompt for password securely instead of command line")
        parser.add_argument("--shell", action="store_true", default=True,
                           help="Use interactive shell mode (default, recommended for network devices)")
        parser.add_argument("--no-shell", action="store_true",
                           help="Disable shell mode and use exec_command instead")
        parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                           default='INFO', help="Set logging level (default: INFO)")
        parser.add_argument("--debug", "-d", action="store_true",
                           help="Enable debug logging (equivalent to --log-level DEBUG)")
        parser.add_argument("--max-threads", type=validate_threads_arg, default=None,
                           help=f"Maximum threads for multi-host execution (default: {multiprocessing.cpu_count()} cores)")
        
        return parser

    @staticmethod
    def interactive_mode():
        """Interactive mode for SSH command execution with input validation"""
        print("🖥️  Enhanced SSH Command Runner v2 - Interactive Mode")
        print("=" * 60)
        
        # Get connection details with validation
        while True:
            hostname = input("🌐 Enter hostname or IP address: ").strip()
            if not hostname:
                print("❌ Hostname is required")
                continue
            if not EnhancedSSHRunner.validate_hostname(hostname):
                print("❌ Invalid hostname or IP address format")
                continue
            break
        
        while True:
            username = input("👤 Enter username: ").strip()
            if not username:
                print("❌ Username is required")
                continue
            if not EnhancedSSHRunner.validate_username(username):
                print("❌ Invalid username format (alphanumeric, underscore, hyphen, dot only)")
                continue
            break
        
        password = getpass.getpass("🔒 Enter password: ")
        if not password:
            print("❌ Password is required")
            return False
        
        # Optional settings with validation
        while True:
            try:
                port_input = input("🔌 Enter SSH port (default 22): ").strip()
                if not port_input:
                    port = 22
                    break
                port = int(port_input)
                if not EnhancedSSHRunner.validate_port(port):
                    print("❌ Port must be between 1 and 65535")
                    continue
                break
            except ValueError:
                print("❌ Port must be a valid number")
        
        while True:
            try:
                timeout_input = input("⏱️  Enter timeout in seconds (default 30): ").strip()
                if not timeout_input:
                    timeout = 30
                    break
                timeout = int(timeout_input)
                if not EnhancedSSHRunner.validate_timeout(timeout):
                    print("❌ Timeout must be between 1 and 3600 seconds")
                    continue
                break
            except ValueError:
                print("❌ Timeout must be a valid number")
        
        # Execution mode
        shell_mode = input("🐚 Use interactive shell mode? (y/N - recommended for network devices): ").strip().lower()
        use_shell = shell_mode in ['y', 'yes', 'true', '1']
        
        # Get command with validation
        while True:
            command = input("⚡ Enter command to execute: ").strip()
            if not command:
                print("❌ Command is required")
                continue
            if not EnhancedSSHRunner.validate_command(command):
                print("❌ Invalid command (too long or contains null bytes)")
                continue
            break
        
        print(f"\n🚀 Starting SSH session (shell_mode={use_shell})...")
        
        # Execute
        return EnhancedSSHRunner.run_ssh_command(hostname, username, password, command, port, timeout, use_shell)



def main():
    """Main entry point for MistHelper CLI application."""
    logging.debug("ENTRY: main()")
    
    # Handle deferred import initialization if needed (only once)
    global success, global_assignments
    if not success and not global_assignments and not hasattr(import_manager, '_deferred_init_done'):
        logging.info("Initializing deferred imports at application start...")
        success, global_assignments = import_manager.initialize_all_imports()
        import_manager._deferred_init_done = True  # Mark as completed
        
        # Apply global assignments to module namespace
        if global_assignments:
            for var_name, var_value in global_assignments.items():
                globals()[var_name] = var_value
                # Special handling for tqdm to ensure it overrides the fallback
                if var_name == 'tqdm' and var_value is not None:
                    logging.info(f"Successfully imported real tqdm in deferred mode: {type(var_value)}")
            logging.debug(f"Applied {len(global_assignments)} global variable assignments")
            
            # Verify tqdm was properly imported
            if 'tqdm' in global_assignments:
                logging.info(f"tqdm is available in global namespace: {type(globals().get('tqdm'))}")
            else:
                logging.warning("tqdm was not found in global assignments - progress bars will not be functional")
        
        if not success:
            logging.warning("Some required imports failed - functionality may be limited")
    elif hasattr(import_manager, '_deferred_init_done'):
        logging.debug("Deferred imports already initialized, skipping duplicate initialization")
    
    # Ensure tqdm is properly available
    ensure_tqdm_available()
    
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
    parser.add_argument("--address-check", action="store_true", help="Enable external address validation using Nominatim API for address comparison operations")
    parser.add_argument("--skip-ssl-verify", action="store_true", help="Skip SSL certificate verification for external API calls (use with caution - for corporate networks only)")
    args = parser.parse_args()

    # ------------------------------------------------------------------------
    # Establish global FAST_MODE_ENABLED flag for systematic test harness
    # The harness inspects globals()['FAST_MODE_ENABLED']; previously this was
    # never set, causing fast mode to be ignored inside run_systematic_test.
    # SECURITY: Read-only flag derived solely from CLI input; no external input.
    # ------------------------------------------------------------------------
    try:
        global FAST_MODE_ENABLED
        FAST_MODE_ENABLED = bool(args.fast)
    except Exception:
        # Fail-safe: ensure symbol exists even if something unexpected happens
        FAST_MODE_ENABLED = False

    # ------------------------------------------------------------------------
    # FAST MODE STARTUP BANNER (Feature A)
    # Enumerate functions that currently accept fast= so operators know scope.
    # This is intentionally static (no reflection over globals()) for safety & clarity.
    # ------------------------------------------------------------------------
    if args.fast:
        fast_capable = [
            "export_gateway_synthetic_tests_to_csv",
            "get_gateway_devices_with_sites",
            "export_gateway_device_stats_to_csv_with_freshness_check",
            "export_gateway_device_stats_to_csv",
            "export_gateway_test_results_by_site_to_csv",
            "export_devices_with_site_info_to_csv",
            "export_gateway_device_configs_to_csv",
            "fetch_gateway_device_configs_from_api",
            "compare_inventory_with_csv",
            "export_gateways_with_wan_overrides_to_csv",
            # Newly added fast-capable stats exporters:
            "export_device_stats_to_csv",
            "export_device_port_stats_to_csv",
            "export_vpn_peer_stats_to_csv",
        ]
        logging.info("FAST MODE ACTIVE: Enabling caching/concurrency shortcuts for: " + ", ".join(fast_capable))
        print("* Fast mode active (caching/concurrency). Functions optimized:")
        for name in fast_capable:
            print(f"  - {name}")
    
    # ============================================================================
    # DEPENDENCY MANAGEMENT - Initialize imports if not already done
    # ============================================================================
    if not _initialize_imports_now and not hasattr(import_manager, '_deferred_init_done'):
        # If imports were deferred, initialize them now with proper skip behavior
        if not args.skip_deps:
            logging.info("Initializing deferred dependencies with full checking...")
            success, global_assignments = import_manager.initialize_all_imports(skip_deps=False)
            import_manager._deferred_init_done = True  # Mark as completed
            
            # Apply global assignments
            if global_assignments:
                for var_name, var_value in global_assignments.items():
                    globals()[var_name] = var_value
                logging.debug(f"Applied {len(global_assignments)} global variable assignments")
            
            if not success and not args.test:
                logging.error("Critical dependencies missing. Exiting.")
                print("!! Critical dependencies missing. Use --skip-deps to bypass or install missing packages.")
                sys.exit(1)
        else:
            logging.info("Dependency initialization skipped due to --skip-deps flag")
            # Still need to initialize the basic imports for core functionality
            success, global_assignments = import_manager.initialize_all_imports(skip_deps=True)
            import_manager._deferred_init_done = True  # Mark as completed
            
            # Apply global assignments even in skip mode
            if global_assignments:
                for var_name, var_value in global_assignments.items():
                    globals()[var_name] = var_value
                logging.debug(f"Applied {len(global_assignments)} global variable assignments in skip mode")
    elif hasattr(import_manager, '_deferred_init_done'):
        logging.debug("Dependencies already initialized, skipping duplicate initialization")
    
    # Initialize Mist API session after dependencies are available
    if not initialize_mist_session():
        logging.error("Failed to initialize Mist API session")
        print(" Failed to initialize Mist API session. Check your credentials.")
        sys.exit(1)
    
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
        print(">> Systematic test mode activated")
        if args.skip_deps:
            print(">> Dependency checks skipped due to --skip-deps flag")
        else:
            print(">> Running systematic test with full dependency verification")
        success = run_systematic_test()
        logging.info(f"SYSTEMATIC_TEST: Test mode completed with success={success}")
        sys.exit(0 if success else 1)
    
    logging.debug(f"Parsed CLI arguments: org={args.org}, menu={args.menu}, site={args.site}, device={args.device}, port={args.port}, debug={args.debug}, delay={args.delay}, fast={args.fast}, skip_deps={args.skip_deps}, output_format={args.output_format}, test={args.test}, address_check={args.address_check}")

    global org_id
    # Check if meaningful CLI arguments are provided (not just script name or flags-only)
    meaningful_cli_args = args.menu or args.org or args.site or args.device or args.port or args.test
    if meaningful_cli_args:
        logging.info("CLI arguments detected, running in non-interactive mode.")
        if args.org:
            org_id = args.org
            logging.info(f"Using org_id from CLI argument: {org_id}")
        else:
            org_id = get_cached_or_prompted_org_id()

        site_id = None
        if args.site:
            logging.info(f"Resolving site name '{args.site}' to site_id using unified pagination limit {DEFAULT_API_PAGE_LIMIT}...")
            sites = fetch_all_sites_with_limit(org_id)
            site_lookup = {site.get("name"): site.get("id") for site in sites if site.get("name") and site.get("id")}
            site_id = site_lookup.get(args.site)
            if not site_id:
                logging.error(f"! Site name '{args.site}' not found.")
                print(f"! Site name '{args.site}' not found.")
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
                logging.error(f"! Device name '{args.device}' not found at site '{args.site}'.")
                print(f"! Device name '{args.device}' not found at site '{args.site}'.")
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
                "fast": args.fast,
                "address_check": args.address_check,
                "skip_ssl_verify": args.skip_ssl_verify
            }
            sig = inspect.signature(func)
            accepted_args = {k: v for k, v in func_args.items() if k in sig.parameters and v is not None}
            func(**accepted_args)
        else:
            logging.error(f"! Invalid menu option: {args.menu}")
            print(f"! Invalid menu option: {args.menu}")
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
        # Single explicit banner for test mode to clarify reduced lookbacks
        try:
            if IS_TEST_MODE:
                logging.info("TEST MODE ACTIVE: Reducing default 24h lookback windows to 1h for eligible exports.")
        except NameError:
            # IS_TEST_MODE may not yet be defined if refactor order changes; ignore safely
            pass
        # Install a global exception hook early so we capture full tracebacks for unexpected issues
        def _global_excepthook(exc_type, exc_value, exc_traceback):
            try:
                import traceback as _tb
                if issubclass(exc_type, KeyboardInterrupt):
                    # Defer to default behavior for Ctrl+C
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                formatted = ''.join(_tb.format_exception(exc_type, exc_value, exc_traceback))
                logging.error("UNHANDLED TOP-LEVEL EXCEPTION TRACEBACK FOLLOWS")
                for line in formatted.rstrip().splitlines():
                    logging.error(line)
            except Exception as hook_err:
                logging.error(f"Exception in global excepthook: {hook_err}")
        try:
            import sys as _sys_mod
            _sys_mod.excepthook = _global_excepthook  # type: ignore[attr-defined]
        except Exception as hook_setup_err:
            logging.warning(f"Failed to install global excepthook: {hook_setup_err}")
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
