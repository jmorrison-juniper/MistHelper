"""Interactive Mist session login and MSP/org selection flow."""

from __future__ import annotations

import getpass
import logging
from collections.abc import Callable
from typing import Any


class InteractiveSessionManager:
    """Manage interactive session login and MSP/org selection outside MistHelper.py."""

    def __init__(
        self,
        state: dict[str, Any],
        safe_input: Callable[..., str],
        detect_msp_privileges: Callable[[], list[dict[str, Any]]],
        select_org_from_session: Callable[[], None],
    ) -> None:
        """Initialize manager with shared mutable state and injected dependencies."""
        self.state = state
        self.safe_input = safe_input
        self.detect_msp_privileges = detect_msp_privileges
        self.select_org_from_session = select_org_from_session

    @staticmethod
    def _mist_clouds() -> dict[str, tuple[str, str]]:
        """Return selectable Mist cloud endpoints for interactive login."""
        return {
            "1": ("Global 01", "api.mist.com"),
            "2": ("Global 02", "api.gc1.mist.com"),
            "3": ("Global 03", "api.ac2.mist.com"),
            "4": ("Global 04", "api.gc2.mist.com"),
            "5": ("Global 05", "api.gc4.mist.com"),
            "6": ("EMEA 01", "api.eu.mist.com"),
            "7": ("EMEA 02", "api.gc3.mist.com"),
            "8": ("EMEA 03", "api.ac6.mist.com"),
            "9": ("EMEA 04", "api.gc6.mist.com"),
            "10": ("APAC 01", "api.ac5.mist.com"),
            "11": ("APAC 03", "api.gc7.mist.com"),
        }

    def initialize_mist_session_interactive(self) -> bool:
        """Initialize Mist API session using interactive login flow."""
        mistapi_module = self.state.get("mistapi")
        if mistapi_module is None:
            try:
                import mistapi as mistapi_fallback

                mistapi_module = mistapi_fallback
                self.state["mistapi"] = mistapi_module
            except ImportError as import_error:
                logging.error("Cannot import mistapi: %s", import_error)
                print("X Failed to import mistapi library")
                return False

        print("")
        print("=" * 60)
        print("  INTERACTIVE MIST API LOGIN")
        print("=" * 60)
        print("")
        print("  This authentication method uses session/cookie-based login,")
        print("  which can access MSP-level APIs (unlike org-scoped API tokens).")
        print("")

        clouds = self._mist_clouds()
        print("  Available Mist Clouds:")
        for key, (name, host) in clouds.items():
            print(f"    {key:>2}. {name:<12} ({host})")
        print("")

        try:
            cloud_choice = self.safe_input(
                "  Select cloud (1-11, or press Enter for Global 01): ",
                context="interactive_login",
            ).strip()
        except SystemExit:
            return False

        if cloud_choice == "" or cloud_choice not in clouds:
            cloud_choice = "1"

        cloud_name, host = clouds[cloud_choice]
        print(f"  Using cloud: {cloud_name} ({host})")
        print("")

        try:
            email = self.safe_input("  Email: ", context="interactive_login").strip()
        except SystemExit:
            return False

        if not email:
            print("X Email is required")
            return False

        try:
            password = getpass.getpass("  Password: ")
        except EOFError:
            logging.info("EOF during password entry - session disconnected")
            return False
        except Exception as password_error:
            logging.error("Failed to read password: %s", password_error)
            print(f"X Failed to read password: {password_error}")
            return False

        if not password:
            print("X Password is required")
            return False

        print("")
        print("  Authenticating...")

        try:
            logging.debug("Interactive login - host: %s", host)
            logging.debug("Interactive login - email: %s", email)
            logging.debug("Interactive login - password length: %s", len(password) if password else 0)

            print("  Creating API session...")
            apisession = mistapi_module.APISession(
                email=email,
                password=password,
                host=host,
                console_log_level=20,
                show_cli_notif=False,
            )

            if apisession is None:
                logging.error("APISession constructor returned None")
                print("  X Failed to create API session")
                return False

            if apisession._apitoken:
                logging.debug(
                    "Clearing API token to force email/password login (had %s token(s))",
                    len(apisession._apitoken),
                )
                apisession._apitoken = []
                apisession._apitoken_index = -1

            print("  Sending login request...")
            login_result = apisession.login_with_return()

            error_data = login_result.get("error", {}) if login_result else {}
            two_factor_required = False
            if isinstance(error_data, dict) and error_data.get("two_factor_required"):
                two_factor_required = True
            elif login_result and login_result.get("two_factor_required"):
                two_factor_required = True

            if two_factor_required:
                print("")
                print("  Two-factor authentication required.")
                try:
                    two_factor_code = self.safe_input("  Enter 2FA code: ", context="interactive_login").strip()
                except SystemExit:
                    self.state["apisession"] = None
                    return False

                if not two_factor_code:
                    print("  X 2FA code is required")
                    self.state["apisession"] = None
                    return False

                print("  Sending 2FA verification...")
                login_result = apisession.login_with_return(two_factor=two_factor_code)

            if not login_result or not login_result.get("authenticated", False):
                error_field = login_result.get("error", "Unknown error") if login_result else "No response"
                if isinstance(error_field, dict):
                    error_message = error_field.get("detail", str(error_field))
                else:
                    error_message = str(error_field)
                print(f"  X Authentication failed: {error_message}")
                logging.error("Interactive login failed: %s", error_message)
                self.state["apisession"] = None
                return False

            self.state["apisession"] = apisession
            print("")
            print("  + Login successful!")
            logging.info("Interactive login successful for %s to %s", email, host)

            try:
                from src.auth.session_timeout import configure_session_timeout

                configure_session_timeout(apisession)
            except Exception:
                pass

            print("  Checking for MSP privileges...")
            detected = self.detect_msp_privileges()
            if detected:
                self.state["msp_privileges"] = detected
                print(f"  + MSP access detected: {len(detected)} MSP(s) available")
                for msp in detected:
                    print(f"    - {msp['msp_name']} (role: {msp['role']})")
            else:
                print("  - No MSP privileges detected (org-level access only)")

            print("")
            return True

        except ConnectionError as connection_error:
            print(f"  X Connection failed: {connection_error}")
            logging.error("Interactive login connection error: %s", connection_error)
            self.state["apisession"] = None
            return False

        except ValueError as value_error:
            error_message = str(value_error).lower()
            if "token" in error_message or "401" in error_message:
                print("  X Invalid API token or credentials")
            else:
                print(f"  X Authentication error: {value_error}")
            logging.error("Interactive login value error: %s", value_error)
            self.state["apisession"] = None
            return False

        except Exception as login_error:
            error_message = str(login_error)
            if "invalid" in error_message.lower() or "credential" in error_message.lower():
                print("  X Invalid email or password")
            elif "two_factor" in error_message.lower() or "2fa" in error_message.lower():
                print("  X Two-factor authentication failed")
            elif "401" in error_message:
                print("  X Invalid email or password (authentication failed)")
            else:
                print(f"  X Login failed: {login_error}")
            logging.error("Interactive login failed: %s", login_error)
            self.state["apisession"] = None
            return False

    def select_msp_and_org(self) -> None:
        """Select MSP then organization and update state in-place."""
        msp_privileges = self.state.get("msp_privileges", [])
        apisession = self.state.get("apisession")

        logging.debug("Entering select_msp_and_org() - %s MSP(s) available", len(msp_privileges))
        print("")
        print("=" * 60)
        print("  SELECT MSP AND ORGANIZATION")
        print("=" * 60)
        print("")

        if not msp_privileges:
            self.select_org_from_session()
            return

        chosen_msp = None
        if len(msp_privileges) == 1:
            chosen_msp = msp_privileges[0]
            print(f"  Using MSP: {chosen_msp['msp_name']} (only one available)")
        else:
            print("  Available MSPs:")
            for index, msp in enumerate(msp_privileges, start=1):
                msp_name = msp.get("msp_name", "Unknown")
                msp_role = msp.get("role", "unknown")
                print(f"    {index}. {msp_name} (role: {msp_role})")
            print("")

            try:
                choice = self.safe_input("  Select MSP (number, or Enter to skip): ", context="msp_select").strip()
                if choice == "":
                    print("  Skipping MSP selection - using direct org access")
                    self.select_org_from_session()
                    return
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(msp_privileges):
                    chosen_msp = msp_privileges[choice_index]
                else:
                    print("  X Invalid selection - skipping MSP selection")
                    self.select_org_from_session()
                    return
            except (ValueError, SystemExit):
                print("  X Invalid input - skipping MSP selection")
                self.select_org_from_session()
                return

        self.state["selected_msp"] = chosen_msp
        msp_id = chosen_msp["msp_id"]
        msp_name = chosen_msp.get("msp_name", "Unknown")

        print(f"  + Selected MSP: {msp_name}")
        print(f"  Fetching organizations under {msp_name}...")

        if apisession is None:
            print("  X API session not initialized")
            logging.error("API session not initialized when selecting MSP org")
            return

        try:
            mistapi_module = self.state.get("mistapi")
            if mistapi_module is None:
                import mistapi as mistapi_fallback

                mistapi_module = mistapi_fallback
                self.state["mistapi"] = mistapi_module

            response = mistapi_module.api.v1.msps.orgs.listMspOrgs(apisession, msp_id)
            if not response or not hasattr(response, "data"):
                print("  X Failed to retrieve MSP organizations")
                return

            orgs_data = response.data
            if not isinstance(orgs_data, list):
                orgs_data = [orgs_data] if orgs_data else []
            if not orgs_data:
                print("  No organizations found under this MSP")
                return

            orgs_data = sorted(orgs_data, key=lambda org: org.get("name", "").lower())
            print(f"  Found {len(orgs_data)} organization(s):")
            print("")

            page_size = 20
            current_page = 0
            total_pages = (len(orgs_data) + page_size - 1) // page_size

            while True:
                start_index = current_page * page_size
                end_index = min(start_index + page_size, len(orgs_data))
                for org_index in range(start_index, end_index):
                    org = orgs_data[org_index]
                    org_name = org.get("name", "Unknown")
                    org_id_preview = org.get("id", "N/A")[:8]
                    print(f"    {org_index + 1:>3}. {org_name} ({org_id_preview}...)")

                print("")
                if total_pages > 1:
                    print(f"  Page {current_page + 1}/{total_pages}")
                    print("  Enter number to select, 'n' for next page, 'p' for previous, 'q' to skip")
                else:
                    print("  Enter number to select, or 'q' to skip")

                try:
                    choice = self.safe_input("  Selection: ", context="org_select").strip().lower()
                except SystemExit:
                    return

                if choice in {"", "q"}:
                    print("  Skipping org selection")
                    return
                if choice == "n" and current_page < total_pages - 1:
                    current_page += 1
                    continue
                if choice == "p" and current_page > 0:
                    current_page -= 1
                    continue

                try:
                    choice_index = int(choice) - 1
                except ValueError:
                    print("  X Invalid input - try again")
                    continue

                if 0 <= choice_index < len(orgs_data):
                    selected_org = orgs_data[choice_index]
                    selected_org_id = selected_org.get("id")
                    selected_org_name = selected_org.get("name", "Unknown")
                    self.state["org_id"] = selected_org_id
                    print("")
                    print(f"  + Selected organization: {selected_org_name}")
                    print(f"  + Organization ID: {selected_org_id}")
                    logging.info(
                        "User selected org: %s (%s) under MSP: %s",
                        selected_org_name,
                        selected_org_id,
                        msp_name,
                    )
                    return

                print("  X Invalid number - try again")

        except Exception as org_error:
            print(f"  X Error fetching MSP organizations: {org_error}")
            logging.error("Failed to fetch MSP organizations: %s", org_error)
